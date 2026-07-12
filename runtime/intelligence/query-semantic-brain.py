#!/data/data/com.termux/files/usr/bin/python3

import json
import sys
from pathlib import Path

DB = Path.home() / "AIFT/registry/semantic-repo-brain.json"


def load():
    with open(DB) as f:
        return json.load(f)


def search(term):
    term = term.lower()
    results=[]

    for repo in load():
        blob=json.dumps(repo).lower()

        if term in blob:
            results.append(repo)

    return results


def display(repo):

    print("\n==============================")
    print(repo["name"])
    print("==============================")

    print("Path:")
    print(repo["path"])

    print("\nLanguage:")
    print(repo["language"])

    if repo["frameworks"]:
        print("\nFrameworks:")
        for f in repo["frameworks"]:
            print(" -",f)

    if repo["agents"]:
        print("\nAgents:")
        for a in repo["agents"]:
            print(" -",a)

    if repo["manifests"]:
        print("\nManifests:")
        for m in repo["manifests"][:10]:
            print(" -",m)

    print()


def main():

    if len(sys.argv)<2:
        print("""
Aetherion Semantic Brain Query

Usage:

abrain <search>

Examples:

abrain blockchain
abrain agents
abrain Next.js
abrain identity

""")
        return


    query=" ".join(sys.argv[1:])

    results=search(query)

    if not results:
        print("No semantic matches found.")
        return

    print(f"\nFound {len(results)} matches\n")

    for r in results:
        display(r)


if __name__=="__main__":
    main()
