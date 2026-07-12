#!/data/data/com.termux/files/usr/bin/python3

import json
from pathlib import Path
from collections import defaultdict

BASE = Path.home() / "AIFT/registry"

GRAPH = BASE / "universal-symbol-graph.json"
OUTPUT = BASE / "code-intelligence-index.json"


def main():

    with open(GRAPH) as f:
        graph = json.load(f)


    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])


    repositories = defaultdict(list)
    symbols = defaultdict(list)
    files = defaultdict(list)
    dependencies = defaultdict(list)


    for node in nodes:

        node_id = node.get("id","")
        node_type = node.get("type","")
        data = node.get("data",{})


        if node_type == "repository":

            repositories[node_id]


        elif node_type in [
            "file",
            "source",
            "module"
        ]:

            repo = (
                data.get("repository")
                or data.get("repo")
                or "unknown"
            )

            files[repo].append(node_id)


        elif node_type in [
            "symbol",
            "function",
            "class",
            "export"
        ]:

            name = (
                data.get("name")
                or node_id
            )

            symbols[name].append({
                "id":node_id,
                "type":node_type,
                "data":data
            })


        else:

            if node_id:
                symbols[node_id].append({
                    "type":node_type
                })


    for edge in edges:

        if isinstance(edge,dict):

            source = (
                edge.get("source")
                or edge.get("from")
            )

            target = (
                edge.get("target")
                or edge.get("to")
            )

            relation = (
                edge.get("relation")
                or edge.get("type")
            )


            dependencies[source].append(
                {
                    "target":target,
                    "relation":relation
                }
            )


    result = {

        "engine":
            "Aetherion Code Intelligence v3.1",

        "statistics":{

            "nodes":
                len(nodes),

            "edges":
                len(edges),

            "repositories":
                len(repositories),

            "symbols":
                len(symbols),

            "files":
                len(files)

        },

        "repositories":
            repositories,

        "files":
            files,

        "symbols":
            symbols,

        "dependencies":
            dependencies

    }


    with open(
        OUTPUT,
        "w"
    ) as f:

        json.dump(
            result,
            f,
            indent=2
        )


    print("""
================================
 Aetherion Code Intelligence v3.1
================================
""")

    print(
        "Repositories:",
        len(repositories)
    )

    print(
        "Files:",
        len(files)
    )

    print(
        "Symbols:",
        len(symbols)
    )

    print(
        "Dependencies:",
        len(dependencies)
    )

    print()
    print("Saved:")
    print(OUTPUT)



if __name__=="__main__":
    main()
