#!/data/data/com.termux/files/usr/bin/python3

import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

HOME = Path.home()

REGISTRY = HOME / "AIFT/registry"
SEMANTIC = REGISTRY / "semantic-repo-brain.json"
OUTPUT = REGISTRY / "source-index.jsonl"

EXTENSIONS = {
    ".py":"python",
    ".go":"go",
    ".rs":"rust",
    ".js":"javascript",
    ".jsx":"javascript",
    ".ts":"typescript",
    ".tsx":"typescript",
    ".java":"java",
    ".c":"c",
    ".cpp":"cpp",
    ".cc":"cpp",
    ".h":"c",
    ".hpp":"cpp",
    ".json":"json",
    ".yaml":"yaml",
    ".yml":"yaml",
    ".toml":"toml",
    ".md":"markdown",
    ".sh":"shell"
}

SKIP = {
    ".git",
    "node_modules",
    ".next",
    ".vite",
    "dist",
    "build",
    "__pycache__",
    ".venv",
    "vendor",
    "target"
}


def sha256(path):
    h = hashlib.sha256()
    with open(path,"rb") as f:
        while True:
            b = f.read(65536)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def should_skip(path):
    for p in path.parts:
        if p in SKIP:
            return True
    return False


with open(SEMANTIC) as f:
    repos = json.load(f)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

count = 0

with open(OUTPUT,"w") as out:

    for repo in repos:

        root = Path(repo["path"])

        if not root.exists():
            continue

        for file in root.rglob("*"):

            if not file.is_file():
                continue

            if should_skip(file):
                continue

            ext = file.suffix.lower()

            if ext not in EXTENSIONS:
                continue

            stat = file.stat()

            record = {

                "repository": repo["name"],

                "path": str(file),

                "relative_path": str(file.relative_to(root)),

                "language": EXTENSIONS[ext],

                "extension": ext,

                "size": stat.st_size,

                "modified":
                    datetime.fromtimestamp(
                        stat.st_mtime,
                        timezone.utc
                    ).isoformat(),

                "sha256":
                    sha256(file),

                "imports": [],

                "exports": [],

                "symbols": []

            }

            out.write(json.dumps(record) + "\n")

            count += 1

print("================================")
print(" Aetherion Source Index v1")
print("================================")
print()
print("Indexed files:", count)
print("Output:")
print(OUTPUT)
