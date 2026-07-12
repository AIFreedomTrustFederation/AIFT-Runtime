#!/data/data/com.termux/files/usr/bin/python3

import json
from pathlib import Path


HOME = Path.home()

FILES = [
    HOME / "AIFT/registry/source-index.jsonl",
    HOME / "AIFT/registry/python-symbol-index.jsonl",
    HOME / "AIFT/registry/typescript-symbol-index.jsonl"
]

OUTPUT = HOME / "AIFT/registry/universal-symbol-graph.json"


nodes = {}
edges = []


def add_node(name, kind, data=None):

    if name not in nodes:
        nodes[name] = {
            "id": name,
            "type": kind,
            "data": data or {}
        }


def add_edge(a,b,relation):

    edges.append({
        "from": a,
        "to": b,
        "relation": relation
    })


# Source files

with open(FILES[0]) as f:

    for line in f:

        r=json.loads(line)

        repo=r["repository"]
        file=r["path"]

        add_node(repo,"repository")

        add_node(
            file,
            "file",
            {
                "language":r.get("language")
            }
        )

        add_edge(
            repo,
            file,
            "contains"
        )



# Symbol indexes

for index in FILES[1:]:

    with open(index) as f:

        for line in f:

            r=json.loads(line)

            file=r["file"]

            add_node(
                file,
                "file"
            )

            symbols=r.get(
                "symbols",
                {}
            )


            for category, items in symbols.items():

                if not isinstance(items,list):
                    continue

                for item in items:

                    if not item:
                        continue

                    symbol=f"{file}:{item}"

                    add_node(
                        symbol,
                        category
                    )

                    add_edge(
                        file,
                        symbol,
                        "defines"
                    )


graph={
    "nodes":list(nodes.values()),
    "edges":edges
}


OUTPUT.write_text(
    json.dumps(
        graph,
        indent=2
    )
)


print("================================")
print(" Aetherion Universal Symbol Graph v2")
print("================================")
print()
print("Nodes:",len(graph["nodes"]))
print("Edges:",len(graph["edges"]))
print()
print("Saved:")
print(OUTPUT)
