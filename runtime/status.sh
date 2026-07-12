#!/usr/bin/env bash
source "$HOME/AIFT/runtime/common.sh"

aift_status() {
  for p in $(repo_paths); do
    echo
    echo "======================================"
    echo "$(repo_name "$p")"
    echo "======================================"
    echo "Branch: $(git_branch "$p")"
    echo "Commit: $(git_commit "$p")"
    echo "Changed files: $(git_changed_count "$p")"
    cd "$p"
    git status --short || true
  done
}
