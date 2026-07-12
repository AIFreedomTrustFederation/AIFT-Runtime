#!/data/data/com.termux/files/usr/bin/python3

import json
from pathlib import Path


HOME = Path.home()

INPUT = HOME / "AIFT/registry/universal-symbol-graph.json"

OUTPUT = HOME / "AIFT/registry/symbol-capability-graph.json"


CAPABILITY_RULES = {

    "blockchain": [
        "blockchain",
        "wallet",
        "transaction",
        "token",
        "crypto",
        "coin",
        "ledger",
        "vault",
        "signature",
        "quantum"
    ],

    "artificial-intelligence": [
        "ai",
        "agent",
        "model",
        "llm",
        "assistant",
        "embedding",
        "inference"
    ],

    "governance": [
        "trust",
        "federation",
        "governance",
        "policy",
        "manifest",
        "dao"
    ],

    "frontend": [
        "react",
        "component",
        "page",
        "vite",
        "next",
        "ui"
    ],

    "security": [
        "security",
        "encrypt",
        "decrypt",
        "auth",
        "permission",
        "credential"
    ]
}


graph=json.loads(
    INPUT.read_text()
)


nodes=graph["nodes"]
edges=graph["edges"]


new_nodes=[]
new_edges=[]


existing=set(
    n["id"]
    for n in nodes
)


def add_node(node):

    if node["id"] not in existing:

        nodes.append(node)
        existing.add(node["id"])



def add_edge(a,b,r):

    edges.append(
        {
            "from":a,
            "to":b,
            "relation":r
        }
    )



for node in list(nodes):

    text=node["id"].lower()

    for capability, keywords in CAPABILITY_RULES.items():

        matches=[]

        for word in keywords:

            if word in text:

                matches.append(word)


        if matches:

            cap=f"capability:{capability}"

            add_node(
                {
                    "id":cap,
                    "type":"capability",
                    "data":{
                        "category":capability
                    }
                }
            )


            add_edge(
                cap,
                node["id"],
                "IMPLEMENTS"
            )



OUTPUT.write_text(
    json.dumps(
        {
            "nodes":nodes,
            "edges":edges
        },
        indent=2
    )
)


print("================================")
print(" Aetherion Symbol Capability Mapper v1")
print("================================")
print()

print(
    "Nodes:",
    len(nodes)
)

print(
    "Edges:",
    len(edges)
)

print()

print(
    "Saved:"
)

print(
    OUTPUT
)
