#!/data/data/com.termux/files/usr/bin/python3

import json
from pathlib import Path
from collections import defaultdict


ROOT = Path.home()

REPORT = ROOT / "AIFT/registry/impact-reports/quantum-vault-semantic.json"
OUTPUT = ROOT / "AIFT/registry/patch-plans/quantum-vault-orchestration.json"


def classify(target):

    if "server/services" in target:
        return 1

    if "client/src/lib/quantum-vault" in target:
        return 2

    if "components/security" in target:
        return 3

    if "routes" in target or "mysterion" in target:
        return 4

    return 5



def main():

    data=json.loads(
        REPORT.read_text()
    )

    nodes=data.get(
        "roots",
        []
    )

    if not nodes:
        nodes=data.get(
            "affected",
            []
        )


    phases=defaultdict(list)


    for node in nodes:

        target = node if isinstance(node,str) else node.get("target","")

        phases[classify(target)].append(
            target
        )


    plan={
        "task":"quantum wallet security",
        "phases":{}
    }


    for phase,items in sorted(phases.items()):

        plan["phases"][str(phase)] = items


    OUTPUT.parent.mkdir(
        exist_ok=True
    )

    OUTPUT.write_text(
        json.dumps(
            plan,
            indent=2
        )
    )


    print("""
================================
 Aetherion Patch Orchestrator v12
================================
""")

    print(
        "Saved:"
    )

    print(
        OUTPUT
    )

    for phase,items in sorted(phases.items()):

        print("\nPHASE",phase)

        for item in items:
            print(" -",item)



if __name__=="__main__":
    main()
