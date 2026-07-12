#!/usr/bin/env bash
source "$HOME/AIFT/runtime/common.sh"

detect_language() {
  local p="$1"
  if [ -f "$p/package.json" ]; then echo "javascript-typescript"
  elif [ -f "$p/Cargo.toml" ]; then echo "rust"
  elif [ -f "$p/go.mod" ]; then echo "go"
  elif find "$p" -maxdepth 3 -name "*.py" | grep -q .; then echo "python"
  elif find "$p" -maxdepth 3 -name "*.sh" | grep -q .; then echo "shell"
  else echo "documents"; fi
}

detect_runtime() {
  local p="$1"
  local out=""
  [ -f "$p/package.json" ] && out="${out}node,"
  [ -f "$p/next.config.js" ] || [ -f "$p/next.config.mjs" ] || [ -f "$p/next.config.ts" ] && out="${out}nextjs,"
  [ -f "$p/vite.config.js" ] || [ -f "$p/vite.config.ts" ] && out="${out}vite,"
  [ -f "$p/Dockerfile" ] && out="${out}docker,"
  [ -z "$out" ] && out="none"
  echo "$out" | sed 's/,$//'
}
