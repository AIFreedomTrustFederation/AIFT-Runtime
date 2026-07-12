#!/data/data/com.termux/files/usr/bin/bash

ROOT="$HOME/AIFT"
CORE="$ROOT/runtime/core"

ROUTER="$CORE/aetherion-agent-router.sh"

python - <<'PY'
from pathlib import Path

p = Path.home() / "AIFT/runtime/core/aetherion-agent-router.sh"

s = p.read_text()

s = s.replace(
") as $ability,",
") as $ability |"
)

s = s.replace(
") as $repo_info,",
") as $repo_info |"
)

s = s.replace(
") as $history_count,",
") as $history_count |"
)

s = s.replace(
"if [ \"$MATCHES\" = \"[]\" ]; then",
"if [ -z \"$MATCHES\" ] || [ \"$MATCHES\" = \"[]\" ]; then"
)

s = s.replace(
"ENTRY=$(jq -n \\",
"if ! echo \"$MATCHES\" | jq empty >/dev/null 2>&1; then\n echo \"ARBITRATION FAILED - MEMORY NOT UPDATED\"\n exit 1\nfi\n\nENTRY=$(jq -n \\"
)

p.write_text(s)

PY

chmod +x "$ROUTER"

echo "Router v6 patched."
