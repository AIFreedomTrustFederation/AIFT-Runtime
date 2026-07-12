#!/data/data/com.termux/files/usr/bin/python3

import json
from pathlib import Path
from collections import defaultdict


HOME = Path.home()

SOURCE = HOME / "AIFT/registry/source-index.jsonl"
PYTHON = HOME / "AIFT/registry/python-symbol-index.jsonl"

OUTPUT = HOME / "AIFT/registry/symbol-knowledge-graph.json"


graph = {
    "nodes": [],
    "edges": []
}


nodes = {}
edges = []


def add_node(name, node_type, data=None):

    if name not in nodes:
        nodes[name] = {
            "id": name,
            "type": node_type,
            "data": data or {}
        }


def edge(a,b,relation):

    edges.append({
        "from":a,
        "to":b,
        "relation":relation
    })


# Load source index

with open(SOURCE) as f:

    for line in f:

        r=json.loads(line)

        file=r["path"]

        add_node(
            r["repository"],
            "repository"
        )

        add_node(
            file,
            "file",
            {
                "language":r["language"]
            }
        )


        edge(
            r["repository"],
            file,
            "contains"
        )


# Load python symbols

with open(PYTHON) as f:

    for line in f:

        r=json.loads(line)

        file=r["file"]

        symbols=r.get(
            "symbols",
            {}
        )


        for fn in symbols.get(
            "functions",
            []
        ):

            symbol=f"{file}:{fn}"

            add_node(
                symbol,
                "function"
            )

            edge(
                file,
                symbol,
                "defines"
            )


        for cls in symbols.get(
            "classes",
            []
        ):

            symbol=f"{file}:{cls}"

            add_node(
                symbol,
                "class"
            )

            edge(
                file,
                symbol,
                "defines"
            )


        for imp in symbols.get(
            "imports",
            []
        ):

            add_node(
                imp,
                "dependency"
            )

            edge(
                file,
                imp,
                "imports"
            )


graph["nodes"]=list(nodes.values())
graph["edges"]=edges


OUTPUT.write_text(
    json.dumps(
        graph,
        indent=2
    )
)


print("================================")
print(" Aetherion Symbol Knowledge Graph v1")
print("================================")
print()
print(
    "Nodes:",
    len(graph["nodes"])
)
print(
    "Edges:",
    len(graph["edges"])
)
print()
print(
    "Saved:",
    OUTPUT
)
