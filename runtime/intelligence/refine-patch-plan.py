#!/data/data/com.termux/files/usr/bin/python3

import json
from pathlib import Path
from collections import defaultdict


HOME = Path.home()

INPUT = HOME / "AIFT/registry/patch-plans/quantum-vault-orchestration.json"

OUTPUT = HOME / "AIFT/registry/patch-plans/quantum-vault-refined.json"


def normalize(target):

    if ":" in target:

        file, symbol = target.rsplit(":",1)

        return file, symbol

    return target, None



def score(path):

    score = 0

    if "server/services/quantum-vault" in path:
        score += 200

    elif "client/src/lib/quantum-vault" in path:
        score += 150

    elif "components/security" in path:
        score += 100

    elif "routes" in path:
        score += 75

    elif "fractalcoin" in path:
        score += 50

    return score



def main():

    data=json.loads(
        INPUT.read_text()
    )


    files=defaultdict(list)


    for phase,targets in data["phases"].items():

        for target in targets:

            file,symbol=normalize(target)

            if symbol:

                files[file].append(symbol)

            else:

                if file not in files:
                    files[file]=[]



    ranked=[]


    for file,symbols in files.items():

        ranked.append(
            {
                "file":file,
                "score":score(file),
                "symbols":sorted(
                    set(symbols)
                )
            }
        )


    ranked.sort(
        key=lambda x:x["score"],
        reverse=True
    )


    result={
        "task":
            "quantum wallet security",

        "files":
            ranked
    }


    OUTPUT.write_text(
        json.dumps(
            result,
            indent=2
        )
    )


    print("""
================================
 Aetherion Patch Intelligence v13.1
================================
""")

    print(
        "Files:",
        len(ranked)
    )


    for i,item in enumerate(ranked,1):

        print("\n",i)
        print(item["file"])
        print("Score:",item["score"])

        if item["symbols"]:

            print("Symbols:")

            for s in item["symbols"]:
                print(" -",s)


    print("\nSaved:")
    print(OUTPUT)



if __name__=="__main__":
    main()
