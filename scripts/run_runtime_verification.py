#!/usr/bin/env python3
"""Run AIFT-Runtime source QA and emit commit-bound verification evidence."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "AIFreedomTrustFederation/AIFT-Runtime"


def command_result(command: list[str], root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)


def worktree_check(root: Path, expected_commit: str) -> dict:
    command = ["git", "status", "--porcelain", "--untracked-files=normal"]
    try:
        result = command_result(command, root)
        head = command_result(["git", "rev-parse", "HEAD"], root)
        code = (result.returncode or head.returncode or
                (1 if result.stdout or head.stdout.strip() != expected_commit else 0))
    except OSError:
        code = 127
    return {
        "id": "worktree",
        "command": "git status --porcelain --untracked-files=normal and git rev-parse HEAD (before and after)",
        "status": "passed" if code == 0 else "failed",
        "exit_code": code,
    }


def generate(root: Path, output: Path, environ: dict[str, str] | None = None) -> int:
    env = os.environ if environ is None else environ
    try:
        root = root.resolve()
        output = output.resolve()
        if output.is_relative_to(root):
            raise ValueError("verification output must be outside the repository checkout")
        result = command_result(["git", "rev-parse", "HEAD"], root)
        if result.returncode != 0:
            raise ValueError("cannot determine checkout commit")
        commit = result.stdout.strip()
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise ValueError("checkout commit is not a full lowercase Git SHA")
        if env.get("GITHUB_SHA") and env["GITHUB_SHA"] != commit:
            raise ValueError("GITHUB_SHA does not match the checked-out commit")
        if env.get("GITHUB_REPOSITORY") and env["GITHUB_REPOSITORY"] != REPOSITORY:
            raise ValueError("GITHUB_REPOSITORY does not match AIFT-Runtime")
        before = worktree_check(root, commit)
        try:
            qa = subprocess.run(["bash", "qa-local.sh"], cwd=root, check=False)
            qa_code = qa.returncode
        except OSError as error:
            print(f"runtime QA could not execute: {error}", file=sys.stderr)
            qa_code = 127
        after = worktree_check(root, commit)
        worktree_code = before["exit_code"] or after["exit_code"]
        source = "github-actions" if env.get("GITHUB_ACTIONS") == "true" else "local"
        run_id = env.get("GITHUB_RUN_ID", "")
        run_url = (f"https://github.com/{REPOSITORY}/actions/runs/{run_id}"
                   if source == "github-actions" and run_id.isdecimal() else None)
        checks = [
            {"id": "runtime_source", "command": "bash qa-local.sh",
             "status": "passed" if qa_code == 0 else "failed", "exit_code": qa_code},
            {**before, "status": "passed" if worktree_code == 0 else "failed",
             "exit_code": worktree_code},
        ]
        record = {
            "schema": "aift.verification.v1",
            "repository": REPOSITORY,
            "commit_sha": commit,
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source": {"type": source, "run_url": run_url},
            "checks": checks,
            "overall_status": "passed" if all(c["status"] == "passed" for c in checks) else "failed",
            "security": {"status": "not_checked", "reason": "Source QA is not a security assessment."},
            "dependencies": {"status": "not_checked", "reason": "Cross-repository dependencies are not exercised."},
            "deployment": {"status": "not_applicable", "reason": "No deployment occurs in this gate."},
            "limitations": [
                "Source QA checks syntax, JSON, Git LFS pointers and isolated unit tests, not live runtime health.",
                "No model inference, Termux integration, production deployment or cross-repository API is exercised.",
                "The JSON artifact is unsigned and is not a cryptographic attestation.",
                "Working-tree checks exclude ignored files and external runtime state.",
            ],
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Verification evidence: {output} ({record['overall_status']})")
        return 0 if record["overall_status"] == "passed" else 1
    except (OSError, ValueError) as error:
        print(f"verification evidence failed: {error}", file=sys.stderr)
        return 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    return generate(ROOT, args.output)


if __name__ == "__main__":
    sys.exit(main())
