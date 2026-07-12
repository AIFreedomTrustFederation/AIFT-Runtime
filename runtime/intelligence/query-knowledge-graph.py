#!/data/data/com.termux/files/usr/bin/python3

import json
import sys
from pathlib import Path

GRAPH = Path.home() / "AIFT/registry/aetherion-knowledge-graph.json"


def load():
    with open(GRAPH) as f:
        return json.load(f)


def find_node(term):
    term = term.lower()
    graph = load()

    return [
        n for n in graph["nodes"]
        if term in n["id"].lower()
        or term in n["type"].lower()
    ]


def connections(node_id):
    graph = load()

    output=[]

    for e in graph["edges"]:
        if e["source"] == node_id:
            output.append(
                ("OUT", e["relation"], e["target"])
            )

        if e["target"] == node_id:
            output.append(
                ("IN", e["relation"], e["source"])
            )

    return output


def classify(node):

    text=node["id"].lower()

    tags=[]

    if any(x in text for x in ["coin","token","wallet","currency"]):
        tags.append("finance")

    if any(x in text for x in ["ai","agent","model","intelligence"]):
        tags.append("artificial-intelligence")

    if any(x in text for x in ["governance","trust","federation"]):
        tags.append("governance")

    if any(x in text for x in ["blockchain","chain","crypto"]):
        tags.append("blockchain")

    if any(x in text for x in ["web","next","react"]):
        tags.append("application")

    return tags


def explain(node):

    print("\n==============================")
    print(node["id"])
    print("==============================")

    print("Type:")
    print(node["type"])

    print("\nSemantic Categories:")

    tags=classify(node)

    if tags:
        for t in tags:
            print(" -",t)
    else:
        print(" - unknown")


    print("\nConnections:")

    for direction,rel,target in connections(node["id"]):
        print(
            f" {direction} --{rel}--> {target}"
        )

    print()


def main():

    if len(sys.argv)<2:
        print("""
Aetherion Graph Intelligence v2

Usage:

agraph explain <node>
agraph depends <node>
agraph uses <technology>

""")
        return


    command=sys.argv[1]
    query=" ".join(sys.argv[2:])


    results=find_node(query)


    if not results:
        print("No graph matches.")
        return


    if command=="explain":

        for n in results:
            explain(n)


    elif command=="depends":

        for n in results:
            print("\n",n["id"])
            print("----------------")

            for direction,rel,target in connections(n["id"]):
                if direction=="OUT":
                    print(target)


    elif command=="uses":

        for n in results:
            print("\n",n["id"])
            print("----------------")

            for direction,rel,target in connections(n["id"]):
                if rel=="USES":
                    print(target)


if __name__=="__main__":
    main()
