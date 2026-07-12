#!/usr/bin/env python3

import json
import sys
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

BASE = Path.home() / "AIFT"

PLAN = BASE / "registry/patch-plans/quantum-vault-plan-v2.json"
EXECUTION = BASE / "registry/patch-execution"
BACKUPS = BASE / "registry/patch-backups"

REPORT_DIR = EXECUTION / "mutation"
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


def load_plan():
    with open(PLAN) as f:
        return json.load(f)


def normalize_targets(plan):

    targets=[]

    # Planner v2 phases schema
    for phase in plan.get("phases",[]):

        phase_name = phase.get(
            "name",
            phase.get("phase","unknown")
        )

        for item in phase.get("targets",[]):

            if isinstance(item,dict):
                path = (
                    item.get("file")
                    or item.get("path")
                    or item.get("target")
                )
            else:
                path=item

            if path:
                targets.append({
                    "phase":phase_name,
                    "file":path
                })


    # Planner flattened patch_targets schema
    for item in plan.get("patch_targets",[]):

        if isinstance(item,dict):

            path = (
                item.get("file")
                or item.get("path")
                or item.get("target")
            )

            phase = (
                item.get("phase")
                or item.get("category")
                or "unknown"
            )

            if path:
                targets.append({
                    "phase":phase,
                    "file":path
                })


    # Direct targets schema
    for item in plan.get("targets",[]):

        if isinstance(item,dict):

            path = (
                item.get("file")
                or item.get("path")
            )

            phase = item.get(
                "phase",
                "unknown"
            )

            if path:
                targets.append({
                    "phase":phase,
                    "file":path
                })

        else:
            targets.append({
                "phase":"unknown",
                "file":item
            })


    return targets


def checkpoint(name,data):

    path = REPORT_DIR / name

    with open(path,"w") as f:
        json.dump(
            data,
            f,
            indent=2
        )

    return path


def main():

    print("""
================================
 Aetherion Patch Mutation Engine v1
================================
""")

    task = sys.argv[1] if len(sys.argv)>1 else "unknown"

    approve = "--approve" in sys.argv

    print("TASK:")
    print(task)

    print()

    if not approve:
        print("MODE:")
        print("SIMULATION")

    else:
        print("MODE:")
        print("CONTROLLED MUTATION")


    plan=load_plan()

    targets=normalize_targets(plan)


    state={
        "task":task,
        "timestamp":
            datetime.now(timezone.utc).isoformat(),
        "approved":approve,
        "targets":targets,
        "status":"initialized"
    }


    cp=checkpoint(
        task+"-mutation-start.json",
        state
    )


    print()
    print("CHECKPOINT:")
    print(cp)

    print()
    print("PHASES:")

    current=None

    for target in targets:

        if target["phase"] != current:

            current=target["phase"]

            print()
            print(
                "PHASE:",
                current
            )


        print(
            " -",
            target["file"]
        )


        if approve:

            print(
                "   Backup check:",
                "READY"
                if BACKUPS.exists()
                else "MISSING"
            )

            print(
                "   Mutation:",
                "QUEUED"
            )

        else:

            print(
                "   Mutation:",
                "DISABLED"
            )


    result={
        "task":task,
        "approved":approve,
        "mutation_status":
            "queued"
            if approve
            else "simulation",
        "targets":targets,
        "timestamp":
            datetime.now(timezone.utc).isoformat()
    }


    report=checkpoint(
        task+"-mutation-report.json",
        result
    )


    print()
    print("REPORT:")
    print(report)


    if approve:

        print()
        print("NEXT:")
        print(
            "Connect file transformer + test runner."
        )

    else:

        print()
        print(
            "Run with --approve for mutation queue."
        )


if __name__=="__main__":
    main()
