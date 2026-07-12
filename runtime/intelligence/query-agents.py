#!/data/data/com.termux/files/usr/bin/python3

import json
import sys
from pathlib import Path

GRAPH = Path.home() / "AIFT/registry/aetherion-knowledge-graph.json"
AGENTS = Path.home() / "AIFT/registry/agent-capability-map.json"


def load(path):
    with open(path) as f:
        return json.load(f)


def find_capabilities(term):
    term = term.lower()
    graph = load(GRAPH)

    matches=[]

    for node in graph["nodes"]:
        text=json.dumps(node).lower()

        if term in text:
            matches.append(node)

    return matches


def query_agent(capability):

    data=load(AGENTS)

    print()
    print("================================")
    print(" Aetherion Agent Resolver")
    print("================================")
    print()

    found=False

    for agent in data["agents"]:

        if capability.lower() in [
            c.lower() for c in agent["capabilities"]
        ]:

            found=True

            print("Agent:")
            print(agent["name"])

            print()
            print("Capabilities:")

            for c in agent["capabilities"]:
                print(" -",c)

            print()
            print("Targets:")

            for t in agent["targets"]:
                print(" -",t)

            print()

    if not found:
        print("No agent mapped to capability:", capability)


def main():

    if len(sys.argv)<2:
        print("""
Usage:

aagent blockchain
aagent artificial-intelligence
aagent governance
""")
        return

    query=" ".join(sys.argv[1:])

    query_agent(query)


if __name__=="__main__":
    main()
