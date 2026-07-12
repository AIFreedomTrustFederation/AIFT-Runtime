#!/data/data/com.termux/files/usr/bin/python3

import json
from pathlib import Path
from datetime import datetime, timezone

HOME = Path.home()

SOURCE = HOME / "AIFT/registry/semantic-repo-brain.json"
OUTPUT = HOME / "AIFT/registry/aetherion-knowledge-graph.json"


def load_brain():
    with open(SOURCE) as f:
        return json.load(f)


def add_node(nodes, node_id, node_type, metadata=None):
    if node_id not in nodes:
        nodes[node_id] = {
            "id": node_id,
            "type": node_type,
            "metadata": metadata or {}
        }


def add_edge(edges, source, relation, target):
    edges.append({
        "source": source,
        "relation": relation,
        "target": target
    })


def build_graph():

    repos = load_brain()

    nodes = {}
    edges = []

    for repo in repos:

        repo_id = repo["name"]

        add_node(
            nodes,
            repo_id,
            "repository",
            {
                "path": repo["path"],
                "language": repo["language"]
            }
        )

        if repo.get("frameworks"):
            for framework in repo["frameworks"]:

                add_node(
                    nodes,
                    framework,
                    "framework"
                )

                add_edge(
                    edges,
                    repo_id,
                    "USES",
                    framework
                )


        if repo.get("package_manager"):

            pm = repo["package_manager"]

            add_node(
                nodes,
                pm,
                "package_manager"
            )

            add_edge(
                edges,
                repo_id,
                "MANAGED_BY",
                pm
            )


        for manifest in repo.get("manifests", []):

            manifest_id = f"{repo_id}:{manifest}"

            add_node(
                nodes,
                manifest_id,
                "manifest",
                {
                    "file": manifest
                }
            )

            add_edge(
                edges,
                repo_id,
                "HAS_MANIFEST",
                manifest_id
            )


        for agent in repo.get("agents", []):

            agent_id = f"agent:{agent}"

            add_node(
                nodes,
                agent_id,
                "agent"
            )

            add_edge(
                edges,
                repo_id,
                "CONTAINS_AGENT",
                agent_id
            )


        for entry in repo.get("entrypoints", []):

            entry_id = f"{repo_id}:{entry}"

            add_node(
                nodes,
                entry_id,
                "entrypoint"
            )

            add_edge(
                edges,
                repo_id,
                "HAS_ENTRYPOINT",
                entry_id
            )


    graph = {
        "created": datetime.now(timezone.utc).isoformat(),
        "nodes": list(nodes.values()),
        "edges": edges,
        "statistics": {
            "repositories": len(repos),
            "nodes": len(nodes),
            "relationships": len(edges)
        }
    }


    with open(OUTPUT, "w") as f:
        json.dump(graph, f, indent=2)


    print("================================")
    print(" Aetherion Knowledge Graph v1")
    print("================================")
    print()
    print("Created:")
    print(OUTPUT)
    print()
    print("Repositories:", len(repos))
    print("Nodes:", len(nodes))
    print("Edges:", len(edges))


if __name__ == "__main__":
    build_graph()
