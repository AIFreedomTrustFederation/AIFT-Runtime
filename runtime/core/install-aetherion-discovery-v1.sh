#!/data/data/com.termux/files/usr/bin/bash

ROOT="$HOME/AIFT"
REG="$ROOT/registry"
CORE="$ROOT/runtime/core"

mkdir -p "$REG"

echo "========================================"
echo " Aetherion Discovery Engine v1"
echo " System Self-Inventory Layer"
echo "========================================"


cat > "$CORE/aetherion-discover" <<'DISCOVER'
#!/data/data/com.termux/files/usr/bin/bash

ROOT="$HOME/AIFT"
REG="$ROOT/registry"

SYSTEM="$REG/system-map.json"
CAP="$REG/capability-graph.json"
DEP="$REG/dependency-map.json"
ARCH="$REG/architecture-map.json"
MISS="$REG/missing-capabilities.json"


echo "========================================"
echo " Aetherion Discovery Engine"
echo " Scanning System..."
echo "========================================"


python - <<'PY'

import os,json

ROOT=os.path.expanduser("~/AIFT")
REG=os.path.join(ROOT,"registry")

repos=[]

ignore={
".git",
"node_modules",
".next",
"dist",
"build"
}


for item in os.listdir(ROOT):

    path=os.path.join(ROOT,item)

    if not os.path.isdir(path):
        continue

    if item in ignore or item == "registry":
        continue

    info={
        "name":item,
        "path":path,
        "files":[],
        "languages":[],
        "frameworks":[],
        "package_managers":[],
        "capabilities":[]
    }


    for root,dirs,files in os.walk(path):

        dirs[:]=[
            d for d in dirs
            if d not in ignore
        ]

        for f in files:

            rel=os.path.relpath(
                os.path.join(root,f),
                path
            )

            info["files"].append(rel)


            if f=="package.json":
                info["package_managers"].append("npm")

            if f=="go.mod":
                info["package_managers"].append("go")

            if f=="requirements.txt":
                info["package_managers"].append("pip")

            if f.endswith(".go"):
                info["languages"].append("Go")

            if f.endswith(".py"):
                info["languages"].append("Python")

            if f.endswith(".js") or f.endswith(".ts"):
                info["languages"].append(
                    "JavaScript/TypeScript"
                )

            if f.endswith(".md"):
                info["capabilities"].append(
                    "documentation"
                )


    text=" ".join(info["files"]).lower()


    capability_rules={

        "code_generation":[
            "forge",
            "generator",
            "template"
        ],

        "web_application":[
            "next",
            "vite",
            "frontend"
        ],

        "blockchain":[
            "coin",
            "chain",
            "token"
        ],

        "documentation":[
            "book",
            "doc",
            "markdown"
        ],

        "infrastructure":[
            "docker",
            "server",
            "vps"
        ],

        "automation":[
            "workflow",
            "automation"
        ]
    }


    for cap,words in capability_rules.items():

        if any(w in text for w in words):
            info["capabilities"].append(cap)


    # remove duplicates

    for key in [
        "languages",
        "package_managers",
        "capabilities"
    ]:
        info[key]=sorted(list(set(info[key])))


    repos.append(info)


# The generated registry may not exist on a fresh AIFT workspace.
os.makedirs(REG, exist_ok=True)

def write_json_atomic(filename, value):
    """Publish one complete JSON file, leaving the previous version on failure.

    This is per-file atomicity, not a transaction across all five registry files.
    The temporary file lives on the destination filesystem for os.replace().
    """
    import stat
    import tempfile

    target = os.path.join(REG, filename)
    fd, temporary = tempfile.mkstemp(
        prefix=".aetherion-", suffix=".tmp", dir=REG
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(value, output, indent=2)
            output.flush()
            os.fsync(output.fileno())

        if os.path.exists(target):
            mode = stat.S_IMODE(os.stat(target).st_mode)
        else:
            # Match the permissions of a normal open(..., "w") under umask.
            mask = os.umask(0)
            os.umask(mask)
            mode = 0o666 & ~mask
        os.chmod(temporary, mode)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)



write_json_atomic("system-map.json", repos)


capabilities={}

for repo in repos:

    for c in repo["capabilities"]:

        capabilities.setdefault(
            c,
            []
        ).append(
            repo["name"]
        )


write_json_atomic("capability-graph.json", capabilities)


dependencies=[]

for repo in repos:

    dependencies.append({

        "repository":repo["name"],

        "dependencies":
            repo["package_managers"]

    })


write_json_atomic("dependency-map.json", dependencies)


architecture={

"repositories":
len(repos),

"agents":
"pending",

"capability_graph":
"generated",

"next_phase":
"planner"

}


write_json_atomic("architecture-map.json", architecture)


missing=[

"multi-agent planner",
"code synthesis engine",
"validation engine",
"deployment orchestration",
"agent collaboration graph"

]


write_json_atomic("missing-capabilities.json", missing)

# Publish a hash manifest LAST. A failed/interrupted multi-file refresh leaves
# the previous manifest behind, so consumers can detect mixed generations.
# This is detection, not a transaction or an authenticated attestation.
import hashlib
registry_files = (
    "system-map.json",
    "capability-graph.json",
    "dependency-map.json",
    "architecture-map.json",
    "missing-capabilities.json",
)
digests = {}
for filename in registry_files:
    digest = hashlib.sha256()
    with open(os.path.join(REG, filename), "rb") as source:
        for chunk in iter(lambda: source.read(65536), b""):
            digest.update(chunk)
    digests[filename] = digest.hexdigest()

generation_id = hashlib.sha256(
    json.dumps(digests, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()
write_json_atomic("registry-manifest.json", {
    "schema": "aift.runtime.discovery-registry.v1",
    "algorithm": "sha256",
    "generation_id": generation_id,
    "files": digests,
})


print()
print("Discovery Complete")
print()
print("Repositories:",len(repos))
print()
print("Generated:")
print("system-map.json")
print("capability-graph.json")
print("dependency-map.json")
print("architecture-map.json")
print("missing-capabilities.json")
print("registry-manifest.json")

PY

DISCOVER


chmod +x "$CORE/aetherion-discover"


echo
echo "========================================"
echo " Discovery Engine Installed"
echo
echo "Run:"
echo "$CORE/aetherion-discover"
echo "========================================"

