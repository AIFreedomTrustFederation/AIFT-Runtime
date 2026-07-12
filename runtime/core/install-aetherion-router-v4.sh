#!/data/data/com.termux/files/usr/bin/bash

ROOT="$HOME/AIFT"
REG="$ROOT/registry"
CORE="$ROOT/runtime/core"

mkdir -p "$REG" "$CORE"

echo "========================================"
echo " Aetherion Router v4 Installer"
echo " Hardened Cognitive Arbitration Layer"
echo "========================================"


# Initialize history
if [ ! -f "$REG/task-history.json" ]; then
    echo "[]" > "$REG/task-history.json"
fi


cat > "$CORE/aetherion-agent-router.sh" <<'ROUTER'
#!/data/data/com.termux/files/usr/bin/bash

ROOT="$HOME/AIFT"
REG="$ROOT/registry"

AGENTS="$REG/agent-map.json"
HISTORY="$REG/task-history.json"
LATEST="$REG/latest-routing.json"


echo "========================================"
echo " Aetherion Executive Router v4"
echo " Deterministic Arbitration Layer"
echo "========================================"


TASK="$*"


if [ -z "$TASK" ]; then
 echo "Usage: aeroute <task>"
 exit 1
fi


INTENT=$(echo "$TASK" \
 | tr '[:upper:]' '[:lower:]' \
 | sed 's/ /_/g')


echo
echo "TASK:"
echo "$TASK"

echo
echo "INTENT:"
echo "$INTENT"


MATCHES=$(jq \
 --arg intent "$INTENT" '

[
 .[] |
 . as $repo |

 .agents[] |

 {
   repository:$repo.repository,
   agent:.name,
   abilities:.abilities,

   score:
   (
    [
     .abilities[]
     |
     ascii_downcase
     |
     select(. == $intent)
    ]
    |
    length
   )
 }

 |
 select(.score > 0)

]

| sort_by(.score)
| reverse

' "$AGENTS")


if [ "$MATCHES" = "[]" ]; then

 echo
 echo "NO MATCH FOUND"

 exit 0

fi


echo "$MATCHES" > "$LATEST"


SELECTED=$(jq '.[0]' "$LATEST")


echo
echo "SELECTED AGENT:"
echo "$SELECTED" | jq


ENTRY=$(jq -n \
 --arg task "$TASK" \
 --slurpfile assignment "$LATEST" '

{
 timestamp:(now|todate),
 task:$task,
 assignment:$assignment[0][0],
 status:"assigned"
}

')


TEMP=$(mktemp)


jq \
 --argjson entry "$ENTRY" \
 '. + [$entry]' \
 "$HISTORY" > "$TEMP"


mv "$TEMP" "$HISTORY"


echo
echo "MEMORY UPDATED"
echo "$HISTORY"

echo
echo "EXECUTION READY"

ROUTER


chmod +x "$CORE/aetherion-agent-router.sh"


cat > "$CORE/aeroute" <<'CMD'
#!/data/data/com.termux/files/usr/bin/bash
$HOME/AIFT/runtime/core/aetherion-agent-router.sh "$@"
CMD


chmod +x "$CORE/aeroute"


cat > "$CORE/aetherion-status" <<'STATUS'
#!/data/data/com.termux/files/usr/bin/bash

ROOT="$HOME/AIFT"

echo "================================"
echo " Aetherion System Status"
echo "================================"

echo
echo "Registry:"
ls "$ROOT/registry"

echo
echo "Runtime:"
ls "$ROOT/runtime"

echo
echo "Last Route:"

cat "$ROOT/registry/latest-routing.json" 2>/dev/null || echo "No routing yet"

echo
echo "================================"
STATUS


chmod +x "$CORE/aetherion-status"


echo
echo "================================"
echo " Router v4 Installed"
echo
echo "Test:"
echo "$CORE/aeroute analyze code"
echo "$CORE/aeroute organize documents"
echo "$CORE/aetherion-status"
echo "================================"

