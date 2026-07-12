#!/usr/bin/env python3

import json
import sys
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

BASE = Path.home() / "AIFT"

PLAN = BASE / "registry/patch-plans/quantum-vault-plan-v2.json"
REPORT_DIR = BASE / "registry/patch-execution"
BACKUP_DIR = BASE / "registry/patch-backups"

REPORT_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def run(cmd):
    try:
        return subprocess.check_output(
            cmd,
            shell=True,
            stderr=subprocess.STDOUT
        ).decode()
    except Exception as e:
        return str(e)


def load_plan():
    if not PLAN.exists():
        print("Missing plan:")
        print(PLAN)
        sys.exit(1)

    with open(PLAN) as f:
        return json.load(f)


def backup_file(path):
    src = BASE / "Aether_Coin_biozonecurrency" / path

    if src.exists():
        dest = BACKUP_DIR / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return str(dest)

    return None


def main():

    print("""
================================
 Aetherion Patch Executor v2
================================
""")

    task = sys.argv[1] if len(sys.argv) > 1 else "unknown"

    approved = "--approve" in sys.argv

    mode = "EXECUTION" if approved else "DRY RUN"

    print("TASK:")
    print(task)

    print()
    print("MODE:")
    print(mode)

    plan = load_plan()

    targets=[]

    # Support planner v2 schema
    if "phases" in plan:
        for phase in plan.get("phases", []):
            for target in phase.get("targets", []):
                targets.append(target)

    # Support patch_targets schema
    if "patch_targets" in plan:
        for item in plan.get("patch_targets", []):
            if isinstance(item, dict):
                if "file" in item:
                    targets.append(item["file"])
                elif "path" in item:
                    targets.append(item["path"])
            else:
                targets.append(item)

    # Support direct targets schema
    if "targets" in plan:
        for target in plan.get("targets", []):
            targets.append(target)

    normalized=[]

    for target in targets:
        if isinstance(target, dict):
            if "file" in target:
                normalized.append(target["file"])
            elif "path" in target:
                normalized.append(target["path"])
            elif "target" in target:
                normalized.append(target["target"])
        else:
            normalized.append(target)

    targets = list(dict.fromkeys(normalized))


    checkpoint = {
        "task": task,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "targets": targets,
        "git_status": run("git status --short")
    }


    checkpoint_file = REPORT_DIR / f"{task}-v2-checkpoint.json"

    with open(checkpoint_file,"w") as f:
        json.dump(checkpoint,f,indent=2)


    print()
    print("CHECKPOINT:")
    print(checkpoint_file)

    print()
    print("TARGET FILES:")
    print(len(targets))


    backups=[]

    for i,target in enumerate(targets,1):

        print()
        print(f"{i}. {target}")

        if approved:

            backup = backup_file(target)

            if backup:
                backups.append(backup)
                print(" Backup:")
                print(backup)

            print(" Status: READY FOR PATCH")


        else:
            print(" Status: ANALYSIS ONLY")


    report = {
        "task":task,
        "mode":mode,
        "approved":approved,
        "targets":targets,
        "backups":backups,
        "timestamp":datetime.now(timezone.utc).isoformat()
    }


    report_file = REPORT_DIR / f"{task}-v2-report.json"

    with open(report_file,"w") as f:
        json.dump(report,f,indent=2)


    print()
    print("REPORT:")
    print(report_file)


    if approved:
        print()
        print("NEXT:")
        print("Patch mutation engine required.")
        print("Backups created successfully.")

    else:
        print()
        print("Awaiting approval:")
        print("Run:")
        print(f"apatch-execute-v2 {task} --approve")


if __name__ == "__main__":
    main()
