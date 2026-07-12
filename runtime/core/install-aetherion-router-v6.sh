#!/data/data/com.termux/files/usr/bin/bash

ROOT="$HOME/AIFT"
REG="$ROOT/registry"
CORE="$ROOT/runtime/core"

ROUTER="$CORE/aetherion-agent-router.sh"

echo "========================================"
echo " Aetherion Router v6 Installer"
echo " Graph Cognitive Arbitration"
echo "========================================"


cat > "$ROUTER" <<'ROUTER'
#!/data/data/com.termux/files/usr/bin/bash

ROOT="$HOME/AIFT"
REG="$ROOT/registry"

AGENTS="$REG/agent-map.json"
REPOS="$REG/repo-intelligence.json"
HISTORY="$REG/task-history.json"
BRAIN="$REG/repo-brain.json"
GRAPH="$REG/knowledge-graph.json"
LATEST="$REG/latest-routing.json"


echo "========================================"
echo " Aetherion Executive Router v6"
echo " Graph Cognitive Arbitration"
echo "========================================"


TASK="$*"

if [ -z "$TASK" ]; then
 echo "Usage: aeroute <task>"
 exit 1
fi


# Memory repair

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
 --slurpfile repos "$REPOS" \
 --slurpfile history "$HISTORY" '

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
 ]
 | length
 ) as $ability,


 (
 [
  $repos[0][]
  | select(.name == $repo.repository)
 ]
 | .[0]
 ) as $repo_info,


 (
 [
  $history[0][]
  | select(
      .repository == $repo.repository
      and
      .agent == $agent.name
    )
 ]
 | length
 ) as $history_count,


 {
   repository:$repo.repository,

   agent:$agent.name,

   abilities:$agent.abilities,


   intelligence:
   {
     repository_exists:
       (if $repo_info then 1 else 0 end),

     historical_runs:
       $history_count
   },


   confidence:
   (
     ($ability * 40)
     +
     ((if $repo_info then 30 else 0 end))
     +
     ($history_count * 10)
     +
     20
   ),

   score:$ability
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

 repository:
   $assignment[0][0].repository,

 agent:
   $assignment[0][0].agent,

 confidence:
   $assignment[0][0].confidence,

 status:"assigned",

 success:null,

 feedback:null
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

echo
echo "EXECUTION READY"

ROUTER


chmod +x "$ROUTER"


echo
echo "========================================"
echo " Router v6 Installed"
echo
echo "Test:"
echo "$CORE/aeroute analyze_code"
echo "$CORE/aeroute organize_documents"
echo "========================================"

