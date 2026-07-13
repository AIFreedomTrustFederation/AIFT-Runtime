#!/data/data/com.termux/files/usr/bin/bash

set +e

echo "========================================"
echo " Aetherion Repository Awareness Validation"
echo "========================================"

ROOT="$HOME/AIFT/AIFT-Runtime"

PASS=0
FAIL=0

check() {
NAME="$1"
CMD="$2"

if eval "$CMD" >/dev/null 2>&1; then
echo "✓ $NAME"
PASS=$((PASS+1))
else
echo "✗ $NAME"
FAIL=$((FAIL+1))
fi
}

echo
echo "[ Core Architecture ]"

check "Discovery engine" \
"test -f '$ROOT/runtime/core/aetherion-discover'"

check "Agent router" \
"test -f '$ROOT/runtime/core/aetherion-agent-router.sh'"


echo
echo "[ Intelligence Files ]"

check "Agent discovery" \
"test -f '$ROOT/runtime/intelligence/discover-agents.py'"

check "Task resolver" \
"test -f '$ROOT/runtime/intelligence/resolve-task-agent.py'"


echo
echo "[ Generated Registry Search ]"

REGISTRY=$(find "$ROOT" -type f \
\( -name "repo-intelligence.json" -o -name "repo-brain.json" -o -name "repos.json" \) \
2>/dev/null | head -20)

if [ -n "$REGISTRY" ]; then
echo "✓ Registry files found:"
echo "$REGISTRY"
PASS=$((PASS+1))
else
echo "✗ No generated repo intelligence files found"
FAIL=$((FAIL+1))
fi


echo
echo "[ Discovery Execution ]"

LOG="$HOME/aetherion-discovery-test.log"

python3 "$ROOT/runtime/core/aetherion-discover" \
>"$LOG" 2>&1

if grep -q "Repositories" "$LOG"; then
echo "✓ Discovery engine executed"
cat "$LOG"
PASS=$((PASS+1))
else
echo "✗ Discovery execution failed"
cat "$LOG"
FAIL=$((FAIL+1))
fi


echo
echo "[ Capability Layer ]"

CAPS=$(find "$HOME/AIFT" -name capabilities.json 2>/dev/null | wc -l)

if [ "$CAPS" -gt 0 ]; then
echo "✓ Capability files detected: $CAPS"
PASS=$((PASS+1))
else
echo "✗ No capability files detected"
FAIL=$((FAIL+1))
fi


echo
echo "[ Runtime ]"

check "Aetherion API" \
"curl -s --max-time 5 http://127.0.0.1:8080/v1/models >/dev/null"


echo
echo "========================================"
echo " RESULTS"
echo "========================================"

echo "PASSED: $PASS"
echo "FAILED: $FAIL"

if [ "$FAIL" -eq 0 ]; then
echo
echo "✓ AETHERION AWARENESS LAYER OPERATIONAL"
fi
