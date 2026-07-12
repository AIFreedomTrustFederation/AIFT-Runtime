#!/data/data/com.termux/files/usr/bin/python3

import ast
import json
from pathlib import Path


INPUT = Path.home() / "AIFT/registry/source-index.jsonl"
OUTPUT = Path.home() / "AIFT/registry/python-symbol-index.jsonl"


def extract(path):

    result = {
        "functions": [],
        "classes": [],
        "imports": [],
        "exports": []
    }

    try:

        source = Path(path).read_text(
            errors="ignore"
        )

        tree = ast.parse(source)


        for node in ast.walk(tree):

            if isinstance(node, ast.FunctionDef):

                result["functions"].append(
                    node.name
                )


            elif isinstance(node, ast.ClassDef):

                result["classes"].append(
                    node.name
                )


            elif isinstance(node, ast.Import):

                for n in node.names:
                    result["imports"].append(
                        n.name
                    )


            elif isinstance(node, ast.ImportFrom):

                if node.module:

                    result["imports"].append(
                        node.module
                    )


        return result


    except Exception as e:

        return {
            "error":str(e)
        }



count = 0


with open(INPUT) as src, open(OUTPUT,"w") as out:

    for line in src:

        record=json.loads(line)


        if record["language"] != "python":
            continue


        symbols=extract(
            record["path"]
        )


        output={

            "repository":
                record["repository"],

            "file":
                record["path"],

            "symbols":
                symbols

        }


        out.write(
            json.dumps(output)
            + "\n"
        )


        count+=1


print("================================")
print(" Aetherion Python Symbol Engine v1")
print("================================")
print()
print("Python files analyzed:",count)
print("Output:")
print(OUTPUT)
