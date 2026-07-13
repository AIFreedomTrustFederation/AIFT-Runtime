#!/data/data/com.termux/files/usr/bin/bash

echo "========== Runtime Health =========="

echo
echo "Git:"
git status -sb

echo
echo "Git LFS:"
git lfs ls-files

echo
echo "Model:"
ls -lh runtime/ai/models/

echo
echo "API:"
curl -s http://127.0.0.1:8080/health || echo "Runtime offline"

echo
echo "===================================="
