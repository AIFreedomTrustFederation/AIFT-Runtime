#!/data/data/com.termux/files/usr/bin/bash

ROOT="$HOME/AIFT"
REG="$ROOT/registry"

HISTORY="$REG/task-history.json"

echo "========================================"
echo " Aetherion Memory v5.1 Installer"
echo " Persistent Learning Layer"
echo "========================================"


# Backup current memory

if [ -f "$HISTORY" ]; then
    cp "$HISTORY" "$HISTORY.backup"
fi


# Normalize history schema

if ! jq empty "$HISTORY" >/dev/null 2>&1; then
    echo "[]" > "$HISTORY"
fi


jq '
map(
 {
   timestamp:
     (.timestamp // (now|todate)),

   task:
     (.task // "unknown"),

   repository:
     (.assignment.repository // .repository // "unknown"),

   agent:
     (.assignment.agent // .agent // "unknown"),

   abilities:
     (.assignment.abilities // .abilities // []),

   confidence:
     (.assignment.confidence // .confidence // 0),

   score:
     (.assignment.score // .score // 0),

   status:
     (.status // "assigned"),

   success:
     (.success // null),

   feedback:
     (.feedback // null)
 }
)
' "$HISTORY" > "$HISTORY.tmp"


mv "$HISTORY.tmp" "$HISTORY"


echo
echo "Memory normalized."

echo
echo "Current Memory:"
cat "$HISTORY" | jq .


echo
echo "========================================"
echo " Memory v5.1 Installed"
echo "========================================"

