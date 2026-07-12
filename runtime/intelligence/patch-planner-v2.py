#!/usr/bin/env python3

import json
import sys
from pathlib import Path

BASE = Path.home() / "AIFT"

EXECUTION = BASE / "registry/patch-plans/quantum-vault-execution.json"
VALIDATION = BASE / "registry/patch-plans/quantum-vault-validation.json"

OUTPUT = BASE / "registry/patch-plans/quantum-vault-plan-v2.json"


def load(path):
    with open(path) as f:
        return json.load(f)


def main():

    print("""
================================
 Aetherion Patch Planner v2
================================
""")

    if not EXECUTION.exists():
        print("Missing execution plan")
        sys.exit(1)

    execution = load(EXECUTION)

    validation = {}

    if VALIDATION.exists():
        validation = load(VALIDATION)


    targets = []

    for phase in execution.get("phases", []):
        for target in phase.get("targets", []):
            targets.append({
                "target": target,
                "phase": phase.get("name"),
                "action": phase.get("action")
            })


    for item in targets:

        item["tests_required"] = [
            "typescript compile",
            "dependency import validation",
            "symbol export validation"
        ]

        item["rollback_required"] = True


    plan = {
        "engine": "Aetherion Patch Planner v2",
        "task": "quantum-vault",
        "strategy": "dependency-first",
        "approval_required": True,
        "targets": targets,
        "validation_source": str(VALIDATION)
    }


    with open(OUTPUT,"w") as f:
        json.dump(plan,f,indent=2)


    print("Generated:")
    print(OUTPUT)
    print()

    print("PATCH TARGETS:")
    for i,t in enumerate(targets,1):
        print(
            i,
            t["phase"],
            "-",
            t["target"]
        )


if __name__ == "__main__":
    main()
