#!/data/data/com.termux/files/usr/bin/bash

set -o pipefail

AI_HOME="$HOME/AIFT/runtime/ai"
LIVE_PID=""

if [ -f "$AI_HOME/aetherion.pid" ]; then
    PID=$(cat "$AI_HOME/aetherion.pid")

    if [[ "$PID" =~ ^[1-9][0-9]*$ ]] && kill -0 "$PID" 2>/dev/null; then
        LIVE_PID="$PID"
    fi
fi

# A live PID alone does not establish that the API is responding.
# A successful HTTP status is not enough: an unrelated service may return 200.
# Require a bounded, valid OpenAI-compatible model listing with an advertised ID.
if curl --fail --silent --max-time 5 http://127.0.0.1:8080/v1/models | python3 -c '
import json
import sys
raw = sys.stdin.buffer.read(65537)
if len(raw) > 65536:
    sys.exit(1)
try:
    payload = json.loads(raw)
except (ValueError, UnicodeError):
    sys.exit(1)
models = payload.get("data") if isinstance(payload, dict) else None
sys.exit(0 if isinstance(models, list) and any(
    isinstance(model, dict) and isinstance(model.get("id"), str) and model["id"].strip()
    for model in models
) else 1)
' 2>/dev/null; then
    echo "Aetherion ONLINE"
    if [ -n "$LIVE_PID" ]; then
        echo "PID: $LIVE_PID"
    fi
    echo "API responding on port 8080"
else
    echo "Aetherion OFFLINE"
fi
