#!/data/data/com.termux/files/usr/bin/python3

import json
from pathlib import Path
from datetime import datetime, timezone

GRAPH = Path.home() / "AIFT/registry/aetherion-knowledge-graph.json"


def load():
    with open(GRAPH) as f:
        return json.load(f)


def enrich():

    graph = load()

    capability_map = {

        "blockchain": [
            "blockchain",
            "chain",
            "crypto",
            "coin"
        ],

        "artificial_intelligence": [
            "ai",
            "assistant",
            "agent",
            "model"
        ],

        "security": [
            "security",
            "quantum",
            "vault"
        ],

        "finance": [
            "coin",
            "wallet",
            "currency",
            "escrow"
        ],

        "identity": [
            "identity",
            "dynasty",
            "trust"
        ],

        "governance": [
            "governance",
            "federation"
        ]
    }


    for node in graph["nodes"]:

        text=node["id"].lower()

        node["metadata"]["capabilities"]=[]


        for cap,keywords in capability_map.items():

            for word in keywords:

                if word in text:

                    node["metadata"]["capabilities"].append(cap)
                    break


    graph["enriched_at"]=datetime.now(timezone.utc).isoformat()


    with open(GRAPH,"w") as f:
        json.dump(graph,f,indent=2)


    print("================================")
    print(" Aetherion Graph Enrichment v3")
    print("================================")
    print()
    print("Nodes enriched:",len(graph["nodes"]))
    print("Updated:",GRAPH)


if __name__=="__main__":
    enrich()
