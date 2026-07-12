#!/data/data/com.termux/files/usr/bin/python3

import json
from pathlib import Path

GRAPH = Path.home() / "AIFT/registry/aetherion-knowledge-graph.json"


def load():
    with open(GRAPH) as f:
        return json.load(f)


def save(data):
    with open(GRAPH,"w") as f:
        json.dump(data,f,indent=2)


def main():

    graph=load()

    nodes={n["id"]:n for n in graph["nodes"]}

    new_nodes=[]
    new_edges=[]


    capabilities=set()


    for node in graph["nodes"]:

        for cap in node.get("metadata",{}).get("capabilities",[]):

            capabilities.add(cap)


    for cap in capabilities:

        cid="capability:"+cap

        if cid not in nodes:

            node={
                "id":cid,
                "type":"capability",
                "metadata":{
                    "name":cap
                }
            }

            new_nodes.append(node)
            nodes[cid]=node


    for node in graph["nodes"]:

        for cap in node.get("metadata",{}).get("capabilities",[]):

            new_edges.append({

                "source":node["id"],
                "relation":"IMPLEMENTS",
                "target":"capability:"+cap

            })


    graph["nodes"].extend(new_nodes)
    graph["edges"].extend(new_edges)

    graph["statistics"]["nodes"]=len(graph["nodes"])
    graph["statistics"]["relationships"]=len(graph["edges"])


    save(graph)

    print("================================")
    print(" Aetherion Capability Graph v4")
    print("================================")
    print()
    print("Capability Nodes Added:",len(new_nodes))
    print("Total Nodes:",len(graph["nodes"]))
    print("Total Edges:",len(graph["edges"]))


if __name__=="__main__":
    main()
