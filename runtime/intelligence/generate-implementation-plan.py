#!/data/data/com.termux/files/usr/bin/python3

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

HOME = Path.home()

GRAPH = HOME / "AIFT/registry/aetherion-knowledge-graph.json"
AGENTS = HOME / "AIFT/registry/scored-agents.json"

OUTPUT_DIR = HOME / "AIFT/registry/execution-plans"


def load_json(path):
    with open(path) as f:
        return json.load(f)


def find_targets(capability, keywords):
    graph = load_json(GRAPH)

    matches = []

    for node in graph["nodes"]:

        text = json.dumps(node).lower()

        score = 0
        evidence = []

        for k in keywords:

            if k.lower() in text:
                score += 20
                evidence.append(k)

        if node["type"] in ["entrypoint", "repository"]:
            if score:
                matches.append({
                    "target": node["id"],
                    "type": node["type"],
                    "score": score,
                    "evidence": evidence
                })

    matches.sort(
        key=lambda x:x["score"],
        reverse=True
    )

    return matches[:10]


def generate_plan(agent, task):

    words = task.lower().split()

    targets = find_targets(
        agent,
        words
    )

    plan = {

        "created":
            datetime.now(timezone.utc).isoformat(),

        "agent":
            agent,

        "task":
            task,

        "analysis": {

            "primary_capability":
                agent,

            "target_count":
                len(targets)

        },

        "execution": {

            "operations":[

                {
                    "step":1,
                    "action":"analyze_existing_implementation"
                },

                {
                    "step":2,
                    "action":"resolve_dependencies"
                },

                {
                    "step":3,
                    "action":"generate_patch_plan"
                },

                {
                    "step":4,
                    "action":"run_validation"
                }

            ]

        },

        "targets":
            targets

    }

    return plan



def main():

    if len(sys.argv)<3:

        print("""
Aetherion Implementation Planner v10

Usage:

aimplan <agent> <task>

Example:

aimplan blockchain quantum wallet security
""")

        return


    agent=sys.argv[1]

    task=" ".join(sys.argv[2:])


    plan=generate_plan(
        agent,
        task
    )


    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


    filename = (
        task
        .replace(" ","-")
        .lower()
        +
        ".json"
    )


    output=OUTPUT_DIR / filename


    with open(output,"w") as f:
        json.dump(
            plan,
            f,
            indent=2
        )


    print("""
================================
 Aetherion Implementation Planner v10
================================
""")

    print("AGENT:")
    print(agent)

    print("\nTASK:")
    print(task)

    print("\nPLAN:")
    print(output)

    print("\nTARGETS:")

    for t in plan["targets"]:

        print("\n----------------")
        print(t["target"])
        print("Score:",t["score"])

        print("Evidence:")

        for e in t["evidence"]:
            print(" -",e)



if __name__=="__main__":
    main()

