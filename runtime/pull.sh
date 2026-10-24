#!/usr/bin/env bash
source "$HOME/AIFT/runtime/common.sh"

aift_pull() {
  local report="$AIFT_REPORTS/pull-report.md"
  local p name default_branch current_branch
  local failed=0

  echo "# AIFT Pull Report" > "$report"
  echo >> "$report"
  echo "Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")" >> "$report"
  echo >> "$report"

  while IFS= read -r p; do
    name="$(repo_name "$p")"

    echo
    echo "======================================"
    echo "Pulling $name"
    echo "======================================"

    cd "$p"
    git config --global --add safe.directory "$p" || true

    if ! git remote get-url origin >/dev/null 2>&1; then
      echo "- $name: no origin remote" >> "$report"
      echo "No origin remote. Skipping."
      continue
    fi

    default_branch="$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')"
    [ -z "$default_branch" ] && default_branch="main"

    # Never switch branches or carry unfinished work onto the default branch.
    # A workflow caller must resolve unsafe repositories before publishing.
    current_branch="$(git symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
    if [[ "$current_branch" != "$default_branch" ]]; then
      echo "- $name: skipped (current branch ${current_branch:-detached HEAD}; expected $default_branch)" >> "$report"
      failed=1
      continue
    fi

    if [[ -n "$(git status --porcelain)" ]]; then
      echo "- $name: skipped (uncommitted changes)" >> "$report"
      failed=1
      continue
    fi

    if ! git fetch origin "$default_branch"; then
      echo "- $name: fetch failed" >> "$report"
      failed=1
      continue
    fi

    if git pull --ff-only origin "$default_branch"; then
      echo "- $name: pulled $default_branch" >> "$report"
    else
      echo "- $name: pull failed / manual merge needed" >> "$report"
      failed=1
    fi
  done < <(repo_paths)

  echo
  echo "Pull report written: $report"
  return "$failed"
}
