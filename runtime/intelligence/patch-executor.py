#!/usr/bin/env python3

import json
import sys
import subprocess
import shutil
from datetime import datetime, timezone
from pathlib import Path

BASE = Path.home() / "AIFT"

PLAN = BASE / "registry/patch-plans/quantum-vault-execution.json"
VALIDATION = BASE / "registry/patch-plans/quantum-vault-validation.json"

REPORT_DIR = BASE / "registry/patch-execution"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def run(cmd):
    try:
        return subprocess.check_output(
            cmd,
            shell=True,
            stderr=subprocess.STDOUT
        ).decode()
    except Exception as e:
        return str(e)


def main():

    print("""
================================
 Aetherion Patch Executor v1
================================
""")

    task = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    mode = "DRY RUN"

    print("TASK:")
    print(task)
    print()

    print("MODE:")
    print(mode)
    print()

    if not PLAN.exists():
        print("Missing patch plan:")
        print(PLAN)
        sys.exit(1)

    with open(PLAN) as f:
        plan = json.load(f)

    validation = {}

    if VALIDATION.exists():
        with open(VALIDATION) as f:
            validation = json.load(f)

    checkpoint = {
        "task": task,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "git_status": run("git status --short"),
        "files": plan.get("source_files", [])
    }

    checkpoint_file = REPORT_DIR / (
        task + "-checkpoint.json"
    )

    with open(checkpoint_file,"w") as f:
        json.dump(checkpoint,f,indent=2)


    print("CHECKPOINT:")
    print("created")
    print(checkpoint_file)
    print()

    targets=[]

    for phase in plan.get("phases",[]):
        for t in phase.get("targets",[]):
            targets.append(t)


    print("FILES:")
    print(len(targets))
    print()


    print("PROPOSED ACTIONS:")
    for i,t in enumerate(targets,1):
        print(
            str(i)+". Analyze / validate "
            + t
        )

    print()

    print("VALIDATION:")
    if validation:
        print("available")
    else:
        print("missing")

    print()

    print("MODIFICATION:")
    print("DISABLED")

    print()

    print("Awaiting approval")

    report = {
        "task":task,
        "mode":mode,
        "checkpoint":str(checkpoint_file),
        "targets":targets,
        "approved":False
    }

    report_file = REPORT_DIR / (
        task + "-dry-run.json"
    )

    with open(report_file,"w") as f:
        json.dump(report,f,indent=2)

    print()
    print("Saved:")
    print(report_file)


if __name__ == "__main__":
    main()
