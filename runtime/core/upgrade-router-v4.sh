#!/data/data/com.termux/files/usr/bin/bash

ROOT="$HOME/AIFT"
REGISTRY="$ROOT/registry"
CORE="$ROOT/runtime/core"

AGENTS="$REGISTRY/agent-map.json"
HISTORY="$REGISTRY/task-history.json"

echo "========================================"
echo " Aetherion Executive Router v4"
echo " Deterministic Arbitration Layer"
echo "========================================"


TASK="$*"

if [ -z "$TASK" ]; then
 echo "Usage: aeroute <task>"
 exit 1
fi


if [ ! -f "$HISTORY" ]; then
 echo "[]" > "$HISTORY"
fi


NORMALIZED=$(echo "$TASK" \
| tr '[:upper:]' '[:lower:]' \
| sed 's/ /_/g')


case "$NORMALIZED" in

*code*)
 NORMALIZED="$NORMALIZED,analyze_code"
;;

*document*|*docs*)
 NORMALIZED="$NORMALIZED,organize_documents"
;;

*runtime*|*system*)
 NORMALIZED="$NORMALIZED,inspect_runtime"
;;

*build*)
 NORMALIZED="$NORMALIZED,manage_builds"
;;

*deploy*)
 NORMALIZED="$NORMALIZED,deploy_apps"
;;

esac


echo ""
echo "TASK:"
echo "$TASK"

echo ""
echo "INTENT:"
echo "$NORMALIZED"



MATCHES=$(jq \
--arg intent "$NORMALIZED" '

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
       ascii_downcase as $a
       |
       select(
          ($intent | contains($a))
       )
     ]
     |
     length
   ),

   priority:
   (
     if $repo.repository=="AIFT-Forge" then 100
     elif $repo.repository=="AIFT-OS" then 90
     elif $repo.repository=="AIFT-Genesis" then 80
     else 10
     end
   )
 }

 |

 select(.score > 0)

]

|

sort_by(
 [
  .score,
  .priority
 ]
)

|

reverse

' "$AGENTS")



if [ "$MATCHES" = "[]" ]; then
 echo ""
 echo "No matching agent."
 exit 0
fi


echo ""
echo "MATCHES:"
echo "$MATCHES" | jq



echo "$MATCHES" > "$REGISTRY/latest-routing.json"



jq \
--arg task "$TASK" \
--slurpfile assignment "$REGISTRY/latest-routing.json" '

. + [
 {
  timestamp:(now|todate),
  task:$task,
  assignment:$assignment[0][0],
  status:"assigned"
 }
]

' "$HISTORY" > "$HISTORY.tmp"



mv "$HISTORY.tmp" "$HISTORY"



echo ""
echo "MEMORY UPDATED"
echo "$HISTORY"

echo ""
echo "EXECUTION READY"

