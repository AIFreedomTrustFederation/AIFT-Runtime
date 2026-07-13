#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "========================================"
echo " AIFT Runtime Bootstrap"
echo "========================================"

echo
echo "[1/5] Checking Git LFS..."
if ! command -v git-lfs >/dev/null; then
    echo "ERROR: git-lfs is not installed."
    exit 1
fi

echo
echo "[2/5] Pulling LFS objects..."
git lfs install
git lfs pull

echo
echo "[3/5] Verifying model..."
MODEL="runtime/ai/models/aetherion.gguf"

if [ ! -f "$MODEL" ]; then
    echo "Model missing!"
    exit 1
fi

SIZE=$(du -h "$MODEL" | cut -f1)

echo "Found:"
echo "  $MODEL"
echo "  Size: $SIZE"

echo
echo "[4/5] Starting runtime..."

if [ -x runtime/ai/start.sh ]; then
    ./runtime/ai/start.sh
else
    echo "runtime/ai/start.sh not found."
fi

echo
echo "[5/5] Bootstrap complete."
