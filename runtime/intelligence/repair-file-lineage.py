#!/data/data/com.termux/files/usr/bin/python3

import json
from pathlib import Path
from collections import defaultdict

BASE = Path.home() / "AIFT/registry"

INPUT = BASE / "universal-symbol-graph.json"
OUTPUT = BASE / "code-intelligence-index.json"


def main():

    with open(INPUT) as f:
        graph=json.load(f)


    nodes=graph["nodes"]

    repo_files=defaultdict(set)
    symbol_count=0


    for node in nodes:

        node_id=node.get("id","")
        data=node.get("data",{})


        possible_path = (
            data.get("path")
            or data.get("file")
            or data.get("filepath")
            or ""
        )


        possible_repo = (
            data.get("repository")
            or data.get("repo")
            or ""
        )


        if possible_path:

            repo = possible_repo or "unknown"

            repo_files[repo].add(
                possible_path
            )


        # infer from IDs
        if ":" in node_id:

            parts=node_id.split(":",1)

            repo_files[parts[0]].add(
                parts[1]
            )


        if node.get("type") in [
            "symbol",
            "function",
            "class",
            "export"
        ]:
            symbol_count += 1



    with open(OUTPUT) as f:
        intelligence=json.load(f)


    intelligence["files"] = {
        k:list(v)
        for k,v in repo_files.items()
    }


    intelligence["statistics"]["files"] = sum(
        len(v)
        for v in repo_files.values()
    )


    with open(OUTPUT,"w") as f:
        json.dump(
            intelligence,
            f,
            indent=2
        )


    print("""
================================
 Aetherion File Lineage Repair v1
================================
""")

    print(
        "Files recovered:",
        intelligence["statistics"]["files"]
    )

    print(
        "Repositories:",
        len(repo_files)
    )

    print(
        "Symbols:",
        symbol_count
    )

    print()
    print("Updated:")
    print(OUTPUT)


if __name__=="__main__":
    main()
