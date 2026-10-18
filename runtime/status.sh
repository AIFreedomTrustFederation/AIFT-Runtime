#!/usr/bin/env bash
source "$HOME/AIFT/runtime/common.sh"

aift_status() {
  local p
  while IFS= read -r p; do
    [[ -n "$p" ]] || continue
    echo
    echo "======================================"
    echo "$(repo_name "$p")"
    echo "======================================"
    echo "Branch: $(git_branch "$p")"
    echo "Commit: $(git_commit "$p")"
    echo "Changed files: $(git_changed_count "$p")"
    git -C "$p" status --short || true
  done < <(repo_paths)
}
