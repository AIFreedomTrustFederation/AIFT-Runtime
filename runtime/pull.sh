#!/usr/bin/env bash
source "$HOME/AIFT/runtime/common.sh"

aift_pull() {
  local report="$AIFT_REPORTS/pull-report.md"

  echo "# AIFT Pull Report" > "$report"
  echo >> "$report"
  echo "Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")" >> "$report"
  echo >> "$report"

  for p in $(repo_paths); do
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

    git fetch origin "$default_branch" || {
      echo "- $name: fetch failed" >> "$report"
      continue
    }

    git checkout "$default_branch" || git checkout -B "$default_branch" "origin/$default_branch"

    if git pull --ff-only origin "$default_branch"; then
      echo "- $name: pulled $default_branch" >> "$report"
    else
      echo "- $name: pull failed / manual merge needed" >> "$report"
    fi
  done

  echo
  echo "Pull report written: $report"
}
