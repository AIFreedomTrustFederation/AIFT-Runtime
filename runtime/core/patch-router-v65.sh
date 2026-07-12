#!/data/data/com.termux/files/usr/bin/bash

ROUTER="$HOME/AIFT/runtime/core/aetherion-agent-router.sh"

python - <<'PY'
from pathlib import Path

p=Path.home()/ "AIFT/runtime/core/aetherion-agent-router.sh"

s=p.read_text()

s=s.replace(
'HISTORY="$REG/task-history.json"',
'HISTORY="$REG/task-history.json"\nPROFILE="$REG/agent-performance.json"'
)

s=s.replace(
'--slurpfile history "$HISTORY"',
'--slurpfile history "$HISTORY" \\\n --slurpfile profile "$PROFILE"'
)

s=s.replace(
'''
"confidence":
   (
     ($ability * 40)
     +
     ((if $repo_info then 30 else 0 end))
     +
     ($history_count * 10)
     +
     20
   ),
''',
'''
"confidence":
   (
     ($ability * 40)
     +
     ((if $repo_info then 30 else 0 end))
     +
     ($history_count * 10)
     +
     (
       [
        $profile[0][$agent.name].reliability // 0
       ][0] * 20
     )
     +
     20
   ),
'''
)

p.write_text(s)
PY

chmod +x "$ROUTER"

echo "Router v6.5 patched."
