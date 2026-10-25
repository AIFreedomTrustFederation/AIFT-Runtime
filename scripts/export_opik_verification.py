#!/usr/bin/env python3
"""Prepare Opik trace kwargs from source-QA evidence, entirely offline."""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "AIFreedomTrustFederation/AIFT-Runtime"
CHECKS = ("runtime_source", "worktree")


def trace_kwargs(record):
    """Validate known evidence and allowlist fields; never copy arbitrary text."""
    if not isinstance(record, dict) or record.get("schema") != "aift.verification.v1":
        raise ValueError("expected aift.verification.v1 evidence")
    if record.get("repository") != REPOSITORY:
        raise ValueError("unexpected repository")
    commit = record.get("commit_sha")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("expected a full lowercase commit SHA")
    checks = record.get("checks")
    if not isinstance(checks, list) or len(checks) != len(CHECKS):
        raise ValueError("expected exactly the source and worktree checks")
    normalized = {}
    for check in checks:
        if not isinstance(check, dict):
            raise ValueError("invalid check")
        identifier = check.get("id")
        if not isinstance(identifier, str) or identifier not in CHECKS or identifier in normalized:
            raise ValueError("unknown or duplicate check")
        code = check.get("exit_code")
        if type(code) is not int:
            raise ValueError("exit_code must be an integer")
        status = "passed" if code == 0 else "failed"
        if check.get("status") != status:
            raise ValueError("check status contradicts exit code")
        normalized[identifier] = {"status": status, "exit_code": code}
    overall = "passed" if all(c["status"] == "passed" for c in normalized.values()) else "failed"
    if record.get("overall_status") != overall:
        raise ValueError("overall status contradicts checks")
    for key, status in (("security", "not_checked"), ("dependencies", "not_checked"),
                        ("deployment", "not_applicable")):
        if not isinstance(record.get(key), dict) or record[key].get("status") != status:
            raise ValueError(f"unexpected {key} assessment")
    return {
        "name": "aift-runtime-source-verification",
        "project_name": "aift-runtime-evaluation",
        "input": {"repository": REPOSITORY, "commit_sha": commit},
        "output": {"overall_status": overall,
                   "checks": {key: normalized[key] for key in CHECKS}},
        "metadata": {"evidence_schema": "aift.verification.v1",
                     "evidence_authenticated": False,
                     "scope": "source-qa-only",
                     "security": "not_checked", "dependencies": "not_checked",
                     "deployment": "not_applicable"},
        "tags": ["aift", "source-qa", "unsigned-evidence"],
        "feedback_scores": [{"name": "source_qa_passed",
                             "value": 1.0 if overall == "passed" else 0.0}],
    }


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        output = args.output.resolve()
        if output.is_relative_to(ROOT) or output == args.evidence.resolve():
            raise ValueError("output must be outside checkout and distinct from evidence")
        record = json.loads(args.evidence.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
        payload = trace_kwargs(record)
        # Exclusive creation avoids replacing existing evidence or following a symlink.
        with output.open("x", encoding="utf-8") as target:
            target.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        print("Offline trace prepared; nothing was sent to Opik.")
        return 0
    except (OSError, ValueError) as error:
        print(f"trace preparation failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
