#!/data/data/com.termux/files/usr/bin/python3

import json
import sys
from pathlib import Path
from collections import defaultdict

HOME = Path.home()

GRAPH = HOME / "AIFT/registry/universal-symbol-graph.json"
OUTPUT_DIR = HOME / "AIFT/registry/impact-reports"

STOPWORDS = {
    "the","of","for","to","from","and","or","is","in",
    "a","an","this","that","with","as","on","by"
}


def load_graph():
    with open(GRAPH) as f:
        return json.load(f)


def normalize(text):
    return str(text).lower().replace("_","-").strip()


def meaningful(value):
    if not value:
        return False

    value = normalize(value)

    if value in STOPWORDS:
        return False

    if len(value) < 3:
        return False

    return True


def search_nodes(graph, query):

    query = normalize(query)

    matches=[]

    for node in graph.get("nodes",[]):

        nid = normalize(node.get("id",""))

        if query in nid:

            matches.append(node)

            continue


        data=node.get("data",{})

        for k,v in data.items():

            if query in normalize(v):
                matches.append(node)
                break

    return matches



def build_edges(graph):

    outgoing=defaultdict(list)

    for e in graph.get("edges",[]):

        src=e.get("source") or e.get("from")
        dst=e.get("target") or e.get("to")

        if src and dst:

            outgoing[src].append(dst)

    return outgoing



def walk(graph,start,depth=3):

    outgoing=build_edges(graph)

    visited=set()
    layers=[]

    current=[start]

    for level in range(depth):

        next_layer=[]

        for node in current:

            for child in outgoing.get(node,[]):

                if child not in visited:

                    visited.add(child)
                    next_layer.append(child)

        layers.append(next_layer)

        current=next_layer


    return layers



def classify(node):

    n=normalize(node)

    if any(x in n for x in [
        "security",
        "crypto",
        "vault",
        "wallet"
    ]):
        return "SECURITY"

    if any(x in n for x in [
        ".tsx",
        "component",
        "client"
    ]):
        return "UI"

    if any(x in n for x in [
        "server",
        "service",
        "route"
    ]):
        return "BACKEND"

    return "CODE"



def main():

    if len(sys.argv)<2:

        print("Usage:")
        print("aimpact semantic-term")
        return


    query=" ".join(sys.argv[1:])


    print("""
================================
 Aetherion Semantic Impact Engine v2
================================
""")


    graph=load_graph()


    roots=search_nodes(
        graph,
        query
    )


    if not roots:

        print("No semantic matches found")
        return


    report={

        "query":query,
        "roots":[],
        "impact":{
            "critical":[],
            "high":[],
            "medium":[]
        }

    }


    all_nodes=set()


    for root in roots:

        rid=root.get("id")

        report["roots"].append(rid)

        all_nodes.add(rid)


        layers=walk(
            graph,
            rid,
            3
        )


        for layer in layers:

            for item in layer:

                all_nodes.add(item)



    for node in all_nodes:

        category=classify(node)


        if category=="SECURITY":

            report["impact"]["critical"].append(node)

        elif category=="BACKEND":

            report["impact"]["high"].append(node)

        else:

            report["impact"]["medium"].append(node)



    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


    outfile=OUTPUT_DIR / (
        normalize(query)
        + "-semantic.json"
    )


    with open(outfile,"w") as f:

        json.dump(
            report,
            f,
            indent=2
        )


    print("QUERY:")
    print(query)

    print("\nROOTS:")

    for r in report["roots"]:
        print(" -",r)


    print("\nIMPACT:")

    for level,nodes in report["impact"].items():

        print("\n",level.upper())

        for n in nodes[:20]:
            print(" -",n)


    print("\nTotal affected nodes:",
          len(all_nodes))


    print("\nSaved:")
    print(outfile)



if __name__=="__main__":
    main()
