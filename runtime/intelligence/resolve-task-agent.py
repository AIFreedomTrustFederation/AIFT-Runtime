#!/data/data/com.termux/files/usr/bin/python3

import json
import sys
from pathlib import Path

HOME = Path.home()

AGENTS = HOME / "AIFT/registry/scored-agents.json"


STOPWORDS = {
    "to",
    "the",
    "a",
    "an",
    "add",
    "create",
    "build",
    "fix",
    "improve",
    "make"
}


CAPABILITY_WEIGHTS = {

    "blockchain": {
        "blockchain":50,
        "wallet":40,
        "quantum":35,
        "security":25,
        "token":25,
        "crypto":40
    },

    "artificial-intelligence": {
        "ai":40,
        "assistant":35,
        "model":30,
        "agent":30,
        "intelligence":30
    },

    "governance": {
        "trust":40,
        "federation":40,
        "governance":50
    },

    "frontend": {
        "frontend":40,
        "react":40,
        "vite":30,
        "next":30,
        "ui":25
    }

}


def load_agents():
    with open(AGENTS) as f:
        return json.load(f)["agents"]


def normalize(text):

    text=text.lower()

    for char in "-_":
        text=text.replace(char," ")

    return {
        x for x in text.split()
        if x not in STOPWORDS
    }


def score(task,agent):

    words=normalize(task)

    capability=agent["capability"]

    weights=CAPABILITY_WEIGHTS.get(
        capability,
        {}
    )

    confidence=0
    evidence=[]


    for word,value in weights.items():

        if word in words:
            confidence += value
            evidence.append(word)


    for target in agent.get("targets",[]):

        target_words=normalize(
            str(target)
        )

        matches=words.intersection(
            target_words
        )

        for m in matches:

            if m not in evidence:
                confidence += 5
                evidence.append(m)


    return confidence, evidence



def resolve(task):

    results=[]

    for agent in load_agents():

        confidence,evidence=score(
            task,
            agent
        )

        results.append({

            "agent":agent["agent"],
            "capability":agent["capability"],
            "confidence":confidence,
            "evidence":evidence,
            "targets":agent.get("targets",[])[:5]

        })


    return sorted(
        results,
        key=lambda x:x["confidence"],
        reverse=True
    )


def main():

    task=" ".join(sys.argv[1:])

    results=resolve(task)

    winner=results[0]


    print("""
================================
 Aetherion Task Arbitration v8.1
================================
""")

    print("TASK:")
    print(task)

    print("\nSELECTED AGENT:")
    print(winner["agent"])

    print("\nCAPABILITY:")
    print(winner["capability"])

    print("\nCONFIDENCE:")
    print(str(winner["confidence"])+"%")

    print("\nEVIDENCE:")
    for e in winner["evidence"]:
        print(" -",e)

    print("\nTARGETS:")
    for t in winner["targets"]:
        print(" -",t)


    print("\n--------------------------------")
    print("ALTERNATIVES:")

    for x in results[1:]:
        print(
            x["agent"],
            x["confidence"],
            "%"
        )


if __name__=="__main__":
    main()
