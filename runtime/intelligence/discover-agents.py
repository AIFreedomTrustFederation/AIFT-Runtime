#!/data/data/com.termux/files/usr/bin/python3

import json
from pathlib import Path
from datetime import datetime, timezone

GRAPH = Path.home() / "AIFT/registry/aetherion-knowledge-graph.json"
OUTPUT = Path.home() / "AIFT/registry/discovered-agents.json"


CAPABILITY_KEYWORDS = {
    "blockchain": [
        "blockchain",
        "wallet",
        "crypto"
    ],
    "artificial-intelligence": [
        "ai",
        "assistant",
        "intelligence"
    ],
    "governance": [
        "governance",
        "trust",
        "federation"
    ],
    "frontend": [
        "react",
        "next",
        "vite"
    ]
}


def load_graph():
    with open(GRAPH) as f:
        return json.load(f)


def discover():

    graph = load_graph()

    agents = []

    for capability, keywords in CAPABILITY_KEYWORDS.items():

        targets=[]

        for node in graph["nodes"]:

            text=json.dumps(node).lower()

            for keyword in keywords:

                if keyword in text:

                    targets.append(node["id"])
                    break


        if targets:

            agents.append({

                "name":
                capability.title()+"Agent",

                "capability":
                capability,

                "targets":
                list(set(targets))

            })


    output={

        "generated":
        datetime.now(timezone.utc).isoformat(),

        "agents":
        agents

    }


    with open(OUTPUT,"w") as f:
        json.dump(output,f,indent=2)


    print("================================")
    print(" Aetherion Autonomous Agents v6")
    print("================================")
    print()
    print("Agents discovered:",len(agents))
    print("Saved:",OUTPUT)


if __name__=="__main__":
    discover()
