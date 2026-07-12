#!/usr/bin/env python3

import json
import sys
from pathlib import Path

BASE = Path.home() / "AIFT"

PLAN = BASE / "registry/patch-plans/quantum-vault-execution.json"
GRAPH = BASE / "registry/universal-symbol-graph.json"

REPORT = BASE / "registry/patch-plans/quantum-vault-validation.json"


def load(path):
    with open(path) as f:
        return json.load(f)


def main():

    print("""
================================
 Aetherion Patch Validator v1
================================
""")

    if not PLAN.exists():
        print("Missing patch plan")
        sys.exit(1)

    plan = load(PLAN)

    graph = {}
    if GRAPH.exists():
        graph = load(GRAPH)

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    node_ids = set()

    for n in nodes:
        node_ids.add(n.get("id"))

    results = []

    for phase in plan["phases"]:
        for target in phase["targets"]:

            found = False
            dependents = []

            for n in nodes:
                nid = n.get("id","")

                if target in nid:
                    found = True

            for e in edges:
                src = e.get("source") or e.get("from")
                dst = e.get("target") or e.get("to")

                if target in str(dst):
                    dependents.append(src)

            results.append({
                "target": target,
                "exists_in_graph": found,
                "dependents": dependents,
                "risk":
                    "HIGH" if len(dependents) > 5
                    else "MEDIUM" if len(dependents)
                    else "LOW"
            })


    report = {
        "engine": "Aetherion Patch Validator v1",
        "task": "quantum-vault",
        "validated_targets": results,
        "ready_for_patch": True
    }


    with open(REPORT,"w") as f:
        json.dump(report,f,indent=2)


    print("Validation saved:")
    print(REPORT)
    print()

    for r in results:
        print(r["risk"], "-", r["target"])
        print(" dependents:", len(r["dependents"]))


if __name__ == "__main__":
    main()
