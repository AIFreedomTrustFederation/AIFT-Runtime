#!/usr/bin/env bash
set -euo pipefail

AIFT_WORKSPACE="${AIFT_WORKSPACE:-$HOME/AIFT}"
AIFT_REPORTS="$AIFT_WORKSPACE/reports"
AIFT_REGISTRY="$AIFT_WORKSPACE/registry"
AIFT_INTEL="$AIFT_WORKSPACE/intelligence"
AIFT_MANIFESTS="$AIFT_WORKSPACE/manifests"

mkdir -p "$AIFT_REPORTS" "$AIFT_REGISTRY" "$AIFT_INTEL" "$AIFT_MANIFESTS"

json_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\r//g; s/\t/ /g'
}

json_array_from_lines() {
  printf '['
  local first=1
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    [ "$first" = 0 ] && printf ','
    first=0
    printf '"%s"' "$(json_escape "$line")"
  done
  printf ']'
}

repo_paths() {
  find "$AIFT_WORKSPACE" -mindepth 1 -maxdepth 1 -type d | while read -r d; do
    name="$(basename "$d")"
    case "$name" in
      .github|runtime|registry|reports|intelligence|manifests|scripts) continue ;;
    esac
    # Linked Git worktrees have a .git file rather than a .git directory.
    # Validate the marker before including a repository in workspace operations.
    if [ -d "$d/.git" ] || [ -f "$d/.git" ]; then
      if git -C "$d" rev-parse --show-toplevel >/dev/null 2>&1; then
        printf '%s\n' "$d"
      fi
    fi
  done | sort
}

repo_name() {
  basename "$1"
}

git_branch() {
  cd "$1" && git branch --show-current 2>/dev/null || echo unknown
}

git_commit() {
  cd "$1" && git rev-parse --short HEAD 2>/dev/null || echo unknown
}

git_changed_count() {
  cd "$1" && git status --short 2>/dev/null | wc -l | tr -d ' '
}
