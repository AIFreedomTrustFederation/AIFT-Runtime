#!/usr/bin/env bash
source "$HOME/AIFT/runtime/common.sh"
source "$HOME/AIFT/runtime/repo.sh"

aift_dashboard() {
  local out="$AIFT_REPORTS/federation-dashboard.md"

  {
    echo "# AIFT Federation Dashboard"
    echo
    echo "Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo
    echo "Workspace: \`$AIFT_WORKSPACE\`"
    echo
    for p in $(repo_paths); do
      echo "## $(repo_name "$p")"
      echo
      echo "- Branch: \`$(git_branch "$p")\`"
      echo "- Commit: \`$(git_commit "$p")\`"
      echo "- Changed files: \`$(git_changed_count "$p")\`"
      echo "- Language: \`$(detect_language "$p")\`"
      echo "- Runtime: \`$(detect_runtime "$p")\`"
      echo
    done
  } > "$out"

  echo "Dashboard written: $out"
}
