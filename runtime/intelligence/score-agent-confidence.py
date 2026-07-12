#!/data/data/com.termux/files/usr/bin/python3

import json
from pathlib import Path
from datetime import datetime, timezone

GRAPH = Path.home() / "AIFT/registry/aetherion-knowledge-graph.json"
AGENTS = Path.home() / "AIFT/registry/discovered-agents.json"
OUTPUT = Path.home() / "AIFT/registry/scored-agents.json"


CAPABILITY_EVIDENCE = {

    "blockchain": {
        "high": [
            "blockchain",
            "wallet",
            "crypto",
            "token",
            "escrow",
            "quantum"
        ]
    },

    "artificial-intelligence": {
        "high": [
            "ai",
            "assistant",
            "intelligence",
            "agent",
            "model"
        ]
    },

    "governance": {
        "high": [
            "governance",
            "trust",
            "federation",
            "identity",
            "mission"
        ]
    },

    "frontend": {
        "high": [
            "react",
            "next",
            "vite",
            "web",
            "frontend"
        ]
    }
}


def load(path):
    with open(path) as f:
        return json.load(f)


def score_target(target, capability):

    text = target.lower()

    score = 0
    evidence = []

    keywords = CAPABILITY_EVIDENCE.get(
        capability,
        {}
    ).get(
        "high",
        []
    )

    for word in keywords:

        if word in text:

            score += 15
            evidence.append(word)


    if score > 100:
        score = 100


    return score, evidence


def build():

    agents = load(AGENTS)

    scored = []

    for agent in agents["agents"]:

        capability = agent["capability"]

        targets=[]

        for target in agent["targets"]:

            score, evidence = score_target(
                target,
                capability
            )

            if score:

                targets.append({

                    "target": target,

                    "confidence": score,

                    "evidence": evidence

                })


        targets.sort(
            key=lambda x:x["confidence"],
            reverse=True
        )


        scored.append({

            "agent": agent["name"],

            "capability": capability,

            "targets": targets

        })


    output={

        "generated":
        datetime.now(timezone.utc).isoformat(),

        "agents":
        scored

    }


    with open(OUTPUT,"w") as f:
        json.dump(
            output,
            f,
            indent=2
        )


    print("================================")
    print(" Aetherion Agent Confidence v7")
    print("================================")
    print()
    print("Agents scored:", len(scored))
    print("Saved:")
    print(OUTPUT)


if __name__=="__main__":
    build()
