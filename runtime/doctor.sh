#!/usr/bin/env bash
source "$HOME/AIFT/runtime/common.sh"

aift_doctor() {
  echo "======================================"
  echo " AIFT Runtime Doctor"
  echo "======================================"
  echo "Workspace: $AIFT_WORKSPACE"
  echo "Runtime: $AIFT_WORKSPACE/runtime"
  echo "Repos: $(repo_paths | wc -l | tr -d ' ')"
  command -v git >/dev/null && echo "✅ git" || echo "❌ git"
  command -v gh >/dev/null && echo "✅ gh" || echo "⚠️ gh missing"
  command -v npm >/dev/null && echo "✅ npm" || echo "⚠️ npm missing"
}
