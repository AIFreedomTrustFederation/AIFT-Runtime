#!/data/data/com.termux/files/usr/bin/bash

ROOT="$HOME/AIFT"
REG="$ROOT/registry"
CORE="$ROOT/runtime/core"

ROUTER="$CORE/aetherion-agent-router.sh"

echo "========================================"
echo " Aetherion Router v5 Installer"
echo " Cognitive Arbitration Engine"
echo "========================================"


cat > "$ROUTER" <<'ROUTER'
#!/data/data/com.termux/files/usr/bin/bash

ROOT="$HOME/AIFT"
REG="$ROOT/registry"

AGENTS="$REG/agent-map.json"
REPOS="$REG/repo-intelligence.json"
HISTORY="$REG/task-history.json"
LATEST="$REG/latest-routing.json"


echo "========================================"
echo " Aetherion Executive Router v5"
echo " Cognitive Arbitration Engine"
echo "========================================"


TASK="$*"

if [ -z "$TASK" ]; then
 echo "Usage: aeroute <task>"
 exit 1
fi


# repair memory if damaged

if ! jq empty "$HISTORY" >/dev/null 2>&1; then
 echo "[]" > "$HISTORY"
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
 --arg intent "$INTENT" \
 --slurpfile repos "$REPOS" '

[
 .[] |

 . as $repo |

 .agents[] |

 . as $agent |

 (
   [
    $agent.abilities[]
    | ascii_downcase
    | select(. == $intent)
   ] | length
 ) as $capability_score |


 (
   [
    $repos[0][]
    | select(.name == $repo.repository)
   ]
   | length
 ) as $repo_exists |


 {
   repository:$repo.repository,
   agent:$agent.name,
   abilities:$agent.abilities,

   confidence:
   (
      ($capability_score * 50)
      +
      ($repo_exists * 30)
      +
      20
   ),

   score:$capability_score
 }

 |

 select(.score > 0)

]

| sort_by(.confidence)
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
echo "$SELECTED" | jq .


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


chmod +x "$ROUTER"


echo
echo "========================================"
echo " Router v5 Installed"
echo
echo "Tests:"
echo "$CORE/aeroute analyze_code"
echo "$CORE/aeroute organize_documents"
echo "$CORE/aetherion-status"
echo "========================================"

