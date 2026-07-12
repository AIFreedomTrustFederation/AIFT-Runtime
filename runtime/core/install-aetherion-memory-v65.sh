#!/data/data/com.termux/files/usr/bin/bash

ROOT="$HOME/AIFT"
REG="$ROOT/registry"

HISTORY="$REG/task-history.json"
PROFILE="$REG/agent-performance.json"

echo "========================================"
echo " Aetherion Memory v6.5 Installer"
echo " Adaptive Learning Layer"
echo "========================================"


if ! jq empty "$HISTORY" >/dev/null 2>&1; then
    echo "[]" > "$HISTORY"
fi


if [ ! -f "$PROFILE" ]; then
cat > "$PROFILE" <<JSON
{}
JSON
fi


# Create performance model

jq '
reduce .[] as $task
(
 {};
 
 .[$task.agent] |=
 (
   . // {
     tasks:0,
     successes:0,
     failures:0,
     reliability:0
   }
 )
 
 |
 .[$task.agent].tasks += 1
 
 |
 if $task.success == true then
   .[$task.agent].successes += 1
 elif $task.success == false then
   .[$task.agent].failures += 1
 else .
 end
 
 |
 .[$task.agent].reliability =
 (
   if .[$task.agent].tasks > 0 then
     (.[$task.agent].successes / .[$task.agent].tasks)
   else
     0
   end
 )
)
' "$HISTORY" > "$PROFILE"


echo
echo "Agent Performance:"
cat "$PROFILE" | jq .


echo
echo "========================================"
echo " Memory v6.5 Installed"
echo "========================================"

