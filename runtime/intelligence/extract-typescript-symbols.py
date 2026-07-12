#!/data/data/com.termux/files/usr/bin/python3

import json
import re
from pathlib import Path


INPUT = Path.home() / "AIFT/registry/source-index.jsonl"
OUTPUT = Path.home() / "AIFT/registry/typescript-symbol-index.jsonl"


FUNCTION_PATTERNS = [
    r'function\s+([A-Za-z0-9_$]+)',
    r'const\s+([A-Za-z0-9_$]+)\s*=\s*\(',
    r'let\s+([A-Za-z0-9_$]+)\s*=\s*\(',
    r'export\s+function\s+([A-Za-z0-9_$]+)'
]

CLASS_PATTERNS = [
    r'class\s+([A-Za-z0-9_$]+)',
    r'interface\s+([A-Za-z0-9_$]+)',
    r'type\s+([A-Za-z0-9_$]+)'
]

IMPORT_PATTERNS = [
    r'import\s+.*?\s+from\s+[\'"](.+?)[\'"]',
    r'require\([\'"](.+?)[\'"]\)'
]

EXPORT_PATTERNS = [
    r'export\s+(?:default\s+)?(?:class|function|const|interface|type)?\s*([A-Za-z0-9_$]+)?'
]


def extract(path):

    result = {
        "functions": [],
        "classes": [],
        "interfaces": [],
        "types": [],
        "imports": [],
        "exports": []
    }

    try:

        source = Path(path).read_text(
            errors="ignore"
        )


        for pattern in FUNCTION_PATTERNS:
            result["functions"] += re.findall(
                pattern,
                source
            )


        for pattern in CLASS_PATTERNS:

            matches = re.findall(
                pattern,
                source
            )

            for item in matches:

                if item:

                    if "interface" in pattern:
                        result["interfaces"].append(item)

                    elif "type" in pattern:
                        result["types"].append(item)

                    else:
                        result["classes"].append(item)


        for pattern in IMPORT_PATTERNS:

            result["imports"] += re.findall(
                pattern,
                source
            )


        for pattern in EXPORT_PATTERNS:

            for item in re.findall(pattern, source):

                if item:
                    result["exports"].append(item)


        return result


    except Exception as e:

        return {
            "error": str(e)
        }



count = 0


with open(INPUT) as src, open(OUTPUT,"w") as out:

    for line in src:

        record=json.loads(line)

        if record.get("language") not in [
            "typescript",
            "javascript"
        ]:
            continue


        symbols = extract(
            record["path"]
        )


        out.write(
            json.dumps(
                {
                    "repository": record["repository"],
                    "file": record["path"],
                    "symbols": symbols
                }
            )
            + "\n"
        )


        count += 1



print("================================")
print(" Aetherion TypeScript Symbol Engine v1")
print("================================")
print()
print(
    "TS/JS files analyzed:",
    count
)
print(
    "Output:"
)
print(
    OUTPUT
)
