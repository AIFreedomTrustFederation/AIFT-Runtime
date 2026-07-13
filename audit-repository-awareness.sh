#!/data/data/com.termux/files/usr/bin/bash

set +e

echo "========================================"
echo " AIFT Repository Awareness Audit"
echo "========================================"

ROOT="$(cd "$(dirname "$0")" && pwd)"
BASE="$(dirname "$ROOT")"

PASS=0
FOUND=0

show() {
    echo "✓ $1"
    FOUND=$((FOUND+1))
}

check_file() {
    if [ -e "$1" ]; then
        show "$2"
    fi
}

echo
echo "[ Local Repository Discovery ]"

for repo in \
"AIFT-Runtime" \
"AIFT-OS" \
"AIFT-Forge" \
"AIFT-Genesis" \
"AI-Freedom-Trust" \
"AIFT"; do

    if [ -d "$BASE/$repo/.git" ]; then
        show "Found repository: $repo"
        echo "  Path: $BASE/$repo"
    fi
done


echo
echo "[ Git Remote Awareness ]"

for dir in "$BASE"/*; do
    if [ -d "$dir/.git" ]; then
        NAME=$(basename "$dir")
        REMOTE=$(git -C "$dir" remote get-url origin 2>/dev/null)

        if [ -n "$REMOTE" ]; then
            show "$NAME remote: $REMOTE"
        fi
    fi
done


echo
echo "[ AIFT Metadata ]"

for f in \
"aift.config.json" \
".aift/config.json" \
".aift/capabilities.json" \
"capabilities.json" \
"repos.json" \
"repositories.json" \
"agents.json"; do

    find "$BASE" -name "$f" 2>/dev/null | while read file; do
        show "Metadata found: $file"
    done
done


echo
echo "[ Router / Agent Awareness ]"

grep -R \
--exclude-dir=.git \
--exclude="*.gguf" \
--exclude="*.log" \
-E "AIFT-OS|AIFT-Forge|AIFT-Genesis|AIFT-Runtime|repository|repo|workspace" \
"$ROOT" 2>/dev/null | head -50


echo
echo "[ Existing Tools ]"

find "$ROOT" -type f \
\( -name "*.sh" -o -name "*.py" -o -name "*.js" \) \
2>/dev/null | while read file; do

    case "$file" in
        *router*|*agent*|*scan*|*discover*|*repo*)
            show "Awareness-related tool: $file"
            ;;
    esac

done


echo
echo "[ Repository Count ]"

COUNT=$(find "$BASE" -maxdepth 2 -type d -name .git | wc -l)

echo "Git repositories detected: $COUNT"


echo
echo "========================================"
echo " SUMMARY"
echo "========================================"

echo "Awareness indicators found: $FOUND"

if [ "$FOUND" -gt 0 ]; then
    echo "Repository awareness components already exist."
else
    echo "No repository awareness layer detected."
fi
