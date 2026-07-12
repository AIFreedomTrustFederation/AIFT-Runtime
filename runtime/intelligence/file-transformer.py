#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
import hashlib


BASE = Path.home() / "AIFT"

QUEUE_DIR = BASE / "registry/patch-execution/mutation"

OUT_DIR = QUEUE_DIR / "transformer"

OUT_DIR.mkdir(parents=True, exist_ok=True)


def fingerprint(path):

    p = BASE / "Aether_Coin_biozonecurrency" / path

    if not p.exists():
        return {
            "exists": False,
            "hash": None
        }

    data = p.read_bytes()

    return {
        "exists": True,
        "hash": hashlib.sha256(data).hexdigest(),
        "size": len(data)
    }


def main():

    task = sys.argv[1] if len(sys.argv) > 1 else "unknown"

    queue = QUEUE_DIR / (
        task + "-mutation-queue.json"
    )

    if not queue.exists():
        print("Missing mutation queue")
        return


    with open(queue) as f:
        data = json.load(f)


    print("""
================================
 Aetherion File Transformer v1
================================
""")

    print("TASK:")
    print(task)

    candidates=[]

    for item in data["mutation_queue"]:

        target=item["file"]

        candidates.append({
            "file": target,
            "phase": item["phase"],
            "action": item["action"],
            "before": fingerprint(target),
            "operation": "ANALYZE_ONLY",
            "patch_generated": False
        })


    report={
        "engine":"Aetherion File Transformer v1",
        "task":task,
        "timestamp":datetime.now(timezone.utc).isoformat(),
        "mode":"PRE_MUTATION",
        "candidates":candidates
    }


    outfile = OUT_DIR / (
        task + "-transform-report.json"
    )

    with open(outfile,"w") as f:
        json.dump(report,f,indent=2)


    print()
    print("FILES ANALYZED:")
    print(len(candidates))

    print()
    print("REPORT:")
    print(outfile)

    print()
    print("NEXT:")
    print("Attach test runner.")


if __name__=="__main__":
    main()
