#!/data/data/com.termux/files/usr/bin/python3

import json
import sys
from pathlib import Path

HOME=Path.home()

AGENTS=HOME/"AIFT/registry/scored-agents.json"
GRAPH=HOME/"AIFT/registry/aetherion-knowledge-graph.json"


def load_agents():
    with open(AGENTS) as f:
        return json.load(f)["agents"]


def load_graph():
    with open(GRAPH) as f:
        return json.load(f)


def normalize(text):
    return set(
        str(text)
        .lower()
        .replace("-"," ")
        .replace("_"," ")
        .replace("/"," ")
        .split()
    )


def rank_target(task,target):

    words=normalize(task)
    target_words=normalize(target)

    score=0
    evidence=[]

    for w in words:

        if w in target_words:
            score += 20
            evidence.append(w)

    # semantic boosts

    if "quantum" in words and "quantum" in target_words:
        score += 40

    if "wallet" in words and "wallet" in target_words:
        score += 40

    if "security" in words and (
        "security" in target_words
        or
        "vault" in target_words
    ):
        score += 30
        evidence.append("security")

    # Architecture weighting

    target_lower = target.lower()

    if "/src/" in target_lower:
        score += 25
        evidence.append("source-code")

    if "lib/" in target_lower or "features/" in target_lower:
        score += 25
        evidence.append("core-module")

    if "package.json" in target_lower:
        score -= 15
        evidence.append("manifest")

    if ".github" in target_lower:
        score -= 25
        evidence.append("automation")

    return score, list(set(evidence))


def plan(task,agent):

    ranked=[]

    for item in agent.get("targets",[]):

        target=item["target"] if isinstance(item,dict) else item

        score,evidence=rank_target(
            task,
            target
        )

        if score:

            ranked.append({

                "target":target,
                "score":score,
                "evidence":evidence

            })


    return sorted(
        ranked,
        key=lambda x:x["score"],
        reverse=True
    )[:10]


def main():

    if len(sys.argv)<3:
        print("Usage: aplan <Agent> <task>")
        return


    agent_name=sys.argv[1]
    task=" ".join(sys.argv[2:])


    agent=None

    for a in load_agents():
        if a["agent"]==agent_name:
            agent=a
            break


    if not agent:
        print("Agent not found")
        return


    results=plan(
        task,
        agent
    )


    print("""
================================
 Aetherion Execution Planner v9.1
================================
""")

    print("AGENT:")
    print(agent_name)

    print("\nTASK:")
    print(task)

    print("\nEXECUTION TARGETS:")

    for r in results:

        print("\n----------------")
        print(r["target"])
        print("Confidence:",r["score"])

        print("Evidence:")

        for e in r["evidence"]:
            print(" -",e)


    print("""
\nOPERATIONS:

[1] Analyze implementation
[2] Resolve dependencies
[3] Generate patch plan
[4] Run validation
""")


if __name__=="__main__":
    main()
