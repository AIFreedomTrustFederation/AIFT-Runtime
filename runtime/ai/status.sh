#!/data/data/com.termux/files/usr/bin/bash

AI_HOME="$HOME/AIFT/runtime/ai"
LIVE_PID=""

if [ -f "$AI_HOME/aetherion.pid" ]; then
    PID=$(cat "$AI_HOME/aetherion.pid")

    if [[ "$PID" =~ ^[1-9][0-9]*$ ]] && kill -0 "$PID" 2>/dev/null; then
        LIVE_PID="$PID"
    fi
fi

# A live PID alone does not establish that the API is responding.
if curl --fail --silent --max-time 5 http://127.0.0.1:8080/v1/models >/dev/null 2>&1; then
    echo "Aetherion ONLINE"
    if [ -n "$LIVE_PID" ]; then
        echo "PID: $LIVE_PID"
    fi
    echo "API responding on port 8080"
else
    echo "Aetherion OFFLINE"
fi
