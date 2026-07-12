#!/data/data/com.termux/files/usr/bin/bash

set -e

AI_HOME="$HOME/AIFT/runtime/ai"
START="$AI_HOME/start.sh"
LLAMA="$HOME/Aetherion/llama.cpp/build/bin/llama-server"

echo "=== Aetherion Optimization Script ==="

# Stop existing server
if pgrep llama-server >/dev/null; then
    echo "Stopping existing Aetherion..."
    pkill llama-server || true
    sleep 2
fi

# Backup current configuration
if [ -f "$START" ]; then
    cp "$START" "$START.backup.$(date +%s)"
    echo "Backup created."
fi

# Write optimized start script
cat > "$START" <<'SCRIPT'
#!/data/data/com.termux/files/usr/bin/bash

set -e

AI_HOME="$HOME/AIFT/runtime/ai"
LLAMA="$HOME/Aetherion/llama.cpp/build/bin/llama-server"
MODEL="$AI_HOME/models/aetherion.gguf"
LOG="$AI_HOME/logs/aetherion.log"

if [ ! -f "$MODEL" ]; then
    echo "ERROR: Missing model:"
    echo "$MODEL"
    exit 1
fi

echo "Starting optimized Aetherion..."

nohup "$LLAMA" \
-m "$MODEL" \
--host 127.0.0.1 \
--port 8080 \
--ctx-size 2048 \
--threads 6 \
--threads-batch 8 \
--batch-size 128 \
--ubatch-size 64 \
--flash-attn off \
--mlock \
> "$LOG" 2>&1 &

echo $! > "$AI_HOME/aetherion.pid"

echo "Aetherion ONLINE"
echo "PID: $(cat "$AI_HOME/aetherion.pid")"
echo "API: http://127.0.0.1:8080"
SCRIPT

chmod +x "$START"

# Create stop script
cat > "$AI_HOME/stop.sh" <<'STOP'
#!/data/data/com.termux/files/usr/bin/bash

pkill llama-server 2>/dev/null || true
echo "Aetherion stopped."
STOP

chmod +x "$AI_HOME/stop.sh"

# Create status script
cat > "$AI_HOME/status.sh" <<'STATUS'
#!/data/data/com.termux/files/usr/bin/bash

if pgrep llama-server >/dev/null; then
    echo "Aetherion ONLINE"
    ps -A | grep llama-server
else
    echo "Aetherion OFFLINE"
fi
STATUS

chmod +x "$AI_HOME/status.sh"

# Keep CPU awake
if command -v termux-wake-lock >/dev/null; then
    termux-wake-lock
    echo "Wake lock enabled."
fi

echo "Optimization complete."
echo "Starting Aetherion..."

"$START"
