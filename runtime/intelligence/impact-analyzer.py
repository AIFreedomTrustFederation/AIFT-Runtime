#!/data/data/com.termux/files/usr/bin/python3

import json
import sys
from pathlib import Path
from collections import defaultdict, deque

BASE = Path.home() / "AIFT/registry"

GRAPH_FILE = BASE / "universal-symbol-graph.json"
OUTPUT_DIR = BASE / "impact-reports"

OUTPUT_DIR.mkdir(exist_ok=True)


def load_graph():

    with open(GRAPH_FILE) as f:
        graph = json.load(f)

    nodes = {
        n.get("id"): n
        for n in graph.get("nodes", [])
        if n.get("id")
    }

    edges = defaultdict(list)
    reverse = defaultdict(list)

    for e in graph.get("edges", []):

        src = e.get("source") or e.get("from")
        dst = e.get("target") or e.get("to")

        if src and dst:
            relation = (
                e.get("relation")
                or e.get("type")
                or "connected"
            )

            edges[src].append(
                (dst, relation)
            )

            reverse[dst].append(
                (src, relation)
            )

    return nodes, edges, reverse


def find_matches(nodes, query):

    query = query.lower()

    results=[]

    for node_id,node in nodes.items():

        text=json.dumps(node).lower()

        if query in text:
            results.append(node_id)

    return results


def walk(start, graph, depth=3):

    visited=set()
    queue=deque()

    queue.append(
        (start,0)
    )

    while queue:

        current,d = queue.popleft()

        if current in visited:
            continue

        visited.add(current)

        if d < depth:

            for nxt,_ in graph[current]:
                queue.append(
                    (nxt,d+1)
                )

    return visited


def risk_score(count):

    if count > 100:
        return "CRITICAL"

    if count > 30:
        return "HIGH"

    if count > 10:
        return "MEDIUM"

    return "LOW"


def main():

    if len(sys.argv)<2:

        print(
            "Usage: aimpact <search-term>"
        )

        return


    query=" ".join(sys.argv[1:])


    nodes,edges,reverse=load_graph()


    matches=find_matches(
        nodes,
        query
    )


    print("""
================================
 Aetherion Impact Analyzer v1
================================
""")


    print("QUERY:")
    print(query)

    print()

    if not matches:

        print("No matching nodes found.")
        return


    affected=set()


    for m in matches:

        print("TARGET:")
        print(m)
        print()

        downstream=walk(
            m,
            edges
        )

        upstream=walk(
            m,
            reverse
        )

        affected |= downstream
        affected |= upstream


    print("--------------------------------")
    print("IMPACT SUMMARY")
    print("--------------------------------")

    print(
        "Matched nodes:",
        len(matches)
    )

    print(
        "Affected nodes:",
        len(affected)
    )

    print(
        "Risk:",
        risk_score(len(affected))
    )


    print()
    print("AFFECTED:")

    for item in list(affected)[:50]:

        print(
            " -",
            item
        )


    report={

        "query":query,

        "matched":matches,

        "affected":list(affected),

        "risk":
            risk_score(len(affected))

    }


    outfile = (
        OUTPUT_DIR /
        (
            query.replace(" ","-")
            +
            ".json"
        )
    )


    with open(outfile,"w") as f:

        json.dump(
            report,
            f,
            indent=2
        )


    print()
    print("Report:")
    print(outfile)


if __name__=="__main__":
    main()
