#!/data/data/com.termux/files/usr/bin/bash

AI_HOME="$HOME/AIFT/runtime/ai"

if [ -f "$AI_HOME/aetherion.pid" ]; then
    PID=$(cat "$AI_HOME/aetherion.pid")

    if kill -0 "$PID" 2>/dev/null; then
        echo "Aetherion ONLINE"
        echo "PID: $PID"
        echo "API: http://127.0.0.1:8080"
        exit 0
    fi
fi

if curl -s http://127.0.0.1:8080/v1/models >/dev/null; then
    echo "Aetherion ONLINE"
    echo "API responding on port 8080"
else
    echo "Aetherion OFFLINE"
fi
