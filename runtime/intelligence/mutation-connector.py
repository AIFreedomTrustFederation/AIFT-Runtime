#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

BASE = Path.home() / "AIFT"

PLAN = BASE / "registry/patch-plans/quantum-vault-plan-v2.json"

OUT = BASE / "registry/patch-execution/mutation"

OUT.mkdir(parents=True, exist_ok=True)


def main():

    task = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    approve = "--approve" in sys.argv

    print("""
================================
 Aetherion Mutation Connector v1
================================
""")

    print("TASK:")
    print(task)

    if not PLAN.exists():
        print("Missing plan")
        return

    with open(PLAN) as f:
        plan = json.load(f)


    queue = []

    for item in plan.get("targets", []):

        queue.append({
            "file": item["target"],
            "phase": item["phase"],
            "action": item["action"],
            "tests": item["tests_required"],
            "rollback": item["rollback_required"],
            "status": "queued"
        })


    report = {
        "engine": "Aetherion Mutation Connector v1",
        "task": task,
        "mode": "APPROVED" if approve else "SIMULATION",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mutation_queue": queue
    }


    outfile = OUT / (
        task + "-mutation-queue.json"
    )

    with open(outfile,"w") as f:
        json.dump(report,f,indent=2)


    print()
    print("QUEUE:")
    print(len(queue))

    print()
    print("REPORT:")
    print(outfile)

    if approve:
        print()
        print("NEXT:")
        print("Attach transformer engine.")
    else:
        print()
        print("Run:")
        print(
            "python3 mutation-connector.py "
            + task +
            " --approve"
        )


if __name__ == "__main__":
    main()
