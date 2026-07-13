#!/data/data/com.termux/files/usr/bin/bash

set +e

echo "========================================"
echo " AIFT-Runtime Full Configuration Check"
echo "========================================"

ROOT="$(cd "$(dirname "$0")" && pwd)"
AI_DIR="$ROOT/runtime/ai"
MODEL="$AI_DIR/models/aetherion.gguf"
LLAMA="$HOME/Aetherion/llama.cpp/build/bin/llama-server"

PASS=0
FAIL=0

check() {
    if eval "$2"; then
        echo "✓ $1"
        PASS=$((PASS+1))
    else
        echo "✗ $1"
        FAIL=$((FAIL+1))
    fi
}

echo
echo "[ Repository ]"

check "Git repository exists" \
"test -d '$ROOT/.git'"

check "Remote origin configured" \
"git -C '$ROOT' remote get-url origin >/dev/null 2>&1"

check "Working tree clean" \
"test -z \"\$(git -C '$ROOT' status --porcelain)\""


echo
echo "[ Git LFS ]"

check "Git LFS installed" \
"command -v git-lfs >/dev/null"

check "Model tracked by LFS" \
"git -C '$ROOT' lfs ls-files | grep -q aetherion.gguf"


echo
echo "[ Model ]"

check "Model exists" \
"test -f '$MODEL'"

check "Model larger than 1GB" \
"test \$(stat -c%s '$MODEL' 2>/dev/null || echo 0) -gt 1000000000"


echo
echo "[ Runtime Files ]"

check "start.sh exists" \
"test -f '$AI_DIR/start.sh'"

check "start.sh executable" \
"test -x '$AI_DIR/start.sh'"

check "optimizer exists" \
"test -f '$AI_DIR/optimize_aetherion.sh'"

check "logs directory exists" \
"test -d '$AI_DIR/logs'"


echo
echo "[ Path Configuration ]"

check "start.sh uses portable path" \
"grep -q 'dirname.*0' '$AI_DIR/start.sh'"

check "No old AIFT runtime path" \
"! grep -q 'HOME/AIFT/runtime/ai' '$AI_DIR/start.sh'"


echo
echo "[ llama.cpp ]"

check "llama-server exists" \
"test -x '$LLAMA'"


echo
echo "[ Runtime Process ]"

check "Aetherion process running" \
"pgrep llama-server >/dev/null"


echo
echo "[ API ]"

check "API responding" \
"curl -s --max-time 5 http://127.0.0.1:8080 >/dev/null"


echo
echo "========================================"
echo " RESULTS"
echo "========================================"

echo "PASSED: $PASS"
echo "FAILED: $FAIL"

if [ "$FAIL" -eq 0 ]; then
    echo
    echo "✓ AETHERION RUNTIME FULLY CONFIGURED"
    exit 0
else
    echo
    echo "✗ Configuration issues detected"
    exit 1
fi
