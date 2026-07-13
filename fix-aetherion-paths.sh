#!/data/data/com.termux/files/usr/bin/bash

set -e

echo "========================================"
echo " Aetherion Runtime Path Fix"
echo "========================================"

cd "$(dirname "$0")"

AI_DIR="$(pwd)/runtime/ai"

echo
echo "[1/5] Fixing start.sh..."

cat > runtime/ai/start.sh <<'SCRIPT'
#!/data/data/com.termux/files/usr/bin/bash

set -e

AI_HOME="$(cd "$(dirname "$0")" && pwd)"
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

chmod +x runtime/ai/start.sh


echo
echo "[2/5] Fixing optimize_aetherion.sh..."

sed -i 's|AI_HOME="\$HOME/AIFT/runtime/ai"|AI_HOME="$(cd "$(dirname "$0")" \&\& pwd)"|' runtime/ai/optimize_aetherion.sh || true

chmod +x runtime/ai/optimize_aetherion.sh


echo
echo "[3/5] Checking model..."

MODEL="$AI_DIR/models/aetherion.gguf"

if [ -f "$MODEL" ]; then
    echo "Model OK:"
    ls -lh "$MODEL"
else
    echo "ERROR: Model missing:"
    echo "$MODEL"
    exit 1
fi


echo
echo "[4/5] Stopping old Aetherion process..."

pkill llama-server 2>/dev/null || true
sleep 2


echo
echo "[5/5] Starting Aetherion..."

./runtime/ai/start.sh

sleep 5

echo
echo "========================================"
echo " Verification"
echo "========================================"

ps -ef | grep llama-server | grep -v grep || true

echo

curl -s http://127.0.0.1:8080/health || echo "Health endpoint unavailable"

echo
echo "========================================"
echo " Fix Complete"
echo "========================================"
