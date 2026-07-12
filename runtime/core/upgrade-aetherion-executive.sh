#!/data/data/com.termux/files/usr/bin/bash

ROOT="$HOME/AIFT"
REGISTRY="$ROOT/registry"
CORE="$ROOT/runtime/core"

mkdir -p "$REGISTRY"
mkdir -p "$CORE"

echo "========================================"
echo " Aetherion Executive Upgrade v2"
echo " Arbitration + Memory Layer"
echo "========================================"


########################################
# Agent Priority Database
########################################

cat > "$REGISTRY/agent-priority.json" <<'JSON'
{
 "AIFT-OS":10,
 "AIFT-Forge":10,
 "AIFT-Genesis":10,
 "VPS":8,
 "BookSmith-Federation-OS":7,
 "booksmith-ai":6,
 "capital-city-provisions":5,
 "tastycutz":5,
 "OpenMontage":5,
 "repo-brainstorm-backend-forge":4
}
JSON


########################################
# Task History Initialization
########################################

if [ ! -f "$REGISTRY/task-history.json" ]; then
echo "[]" > "$REGISTRY/task-history.json"
fi


########################################
# Executive Router v2
########################################

cat > "$CORE/aetherion-agent-router.sh" <<'SCRIPT'
#!/data/data/com.termux/files/usr/bin/bash


ROOT="$HOME/AIFT"
REGISTRY="$ROOT/registry"

AGENTS="$REGISTRY/agent-map.json"
PRIORITY="$REGISTRY/agent-priority.json"
HISTORY="$REGISTRY/task-history.json"


echo "========================================"
echo " Aetherion Executive Router v2"
echo " Arbitration Engine"
echo "========================================"


TASK="$*"


if [ -z "$TASK" ]; then
 echo "Usage:"
 echo "aeroute <task>"
 exit 1
fi


NORMALIZED=$(echo "$TASK" \
| tr '[:upper:]' '[:lower:]' \
| sed 's/ /_/g')


echo ""
echo "TASK:"
echo "$TASK"

echo ""
echo "NORMALIZED:"
echo "$NORMALIZED"


MATCHES=$(jq \
--arg TASK "$NORMALIZED" \
--argfile PRIORITY "$PRIORITY" '

[
 .[] |

 . as $repo |

 .agents[] |

 {
  repository:$repo.repository,
  agent:.name,
  abilities:.abilities,
  priority:
    ($PRIORITY[$repo.repository] // 1)
 }

 |

 select(
   [
    .abilities[]
    |
    ascii_downcase
   ]
   |
   any(
    contains($TASK)
   )
 )

 |

 .confidence =
 (
   (.priority / 10)
 )

]

|

sort_by(.priority)

|

reverse

' "$AGENTS")


if [ "$MATCHES" = "[]" ]; then

echo ""
echo "No matching agent found."

exit 0

fi


SELECTED=$(echo "$MATCHES" | jq '.[0]')


echo ""
echo "SELECTED AGENT:"
echo "$SELECTED" | jq


################################
# Memory Logging
################################


ENTRY=$(jq \
--arg task "$TASK" \
--argjson agent "$SELECTED" '

{
 timestamp:(now|todate),
 task:$task,
 assignment:$agent,
 status:"assigned"
}

')


TEMP=$(mktemp)

jq \
--argjson entry "$ENTRY" \
'. + [$entry]' \
"$HISTORY" > "$TEMP"

mv "$TEMP" "$HISTORY"


echo ""
echo "TASK RECORDED:"
echo "$HISTORY"

echo ""
echo "EXECUTION READY"

SCRIPT


chmod +x "$CORE/aetherion-agent-router.sh"


########################################
# Global Command Alias
########################################

cat > "$CORE/aeroute" <<'CMD'
#!/data/data/com.termux/files/usr/bin/bash

$HOME/AIFT/runtime/core/aetherion-agent-router.sh "$@"
CMD

chmod +x "$CORE/aeroute"


echo ""
echo "========================================"
echo " Upgrade Complete"
echo ""
echo "Test:"
echo "$CORE/aeroute analyze code"
echo "$CORE/aeroute inspect runtime"
echo "$CORE/aeroute organize documents"
echo "========================================"

