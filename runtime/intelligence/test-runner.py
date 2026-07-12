#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

BASE = Path.home() / "AIFT"

REPORT_DIR = BASE / "registry/patch-execution/tests"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

TRANSFORM_DIR = (
    BASE /
    "registry/patch-execution/mutation/transformer"
)


def run_test(command):

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=BASE / "Aether_Coin_biozonecurrency",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=300
        )

        return {
            "command": command,
            "exit_code": result.returncode,
            "passed": result.returncode == 0,
            "output": result.stdout.decode(errors="ignore")[-2000:]
        }

    except Exception as e:

        return {
            "command": command,
            "passed": False,
            "error": str(e)
        }


def main():

    task = sys.argv[1] if len(sys.argv) > 1 else "unknown"

    print("""
================================
 Aetherion Test Runner v1
================================
""")

    print("TASK:")
    print(task)

    transform = (
        TRANSFORM_DIR /
        (task + "-transform-report.json")
    )

    if not transform.exists():
        print("Missing transformer report")
        return


    with open(transform) as f:
        data = json.load(f)


    print()
    print("TARGETS:")
    print(len(data["candidates"]))


    tests = []

    tests.append(
        run_test(
            "npm run check"
        )
    )

    tests.append(
        run_test(
            "npm run build"
        )
    )


    report = {

        "engine":
        "Aetherion Test Runner v1",

        "task":
        task,

        "timestamp":
        datetime.now(timezone.utc).isoformat(),

        "targets":
        data["candidates"],

        "tests":
        tests,

        "mutation_allowed":
        all(
            t.get("passed",False)
            for t in tests
        )
    }


    outfile = (
        REPORT_DIR /
        (task + "-test-report.json")
    )

    with open(outfile,"w") as f:
        json.dump(
            report,
            f,
            indent=2
        )


    print()
    print("REPORT:")
    print(outfile)

    print()

    if report["mutation_allowed"]:
        print("STATUS:")
        print("READY FOR MUTATION")
    else:
        print("STATUS:")
        print("BLOCKED - TEST FAILURE")


if __name__ == "__main__":
    main()
