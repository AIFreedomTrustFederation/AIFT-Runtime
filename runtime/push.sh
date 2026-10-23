#!/usr/bin/env bash
source "$HOME/AIFT/runtime/common.sh"

aift_push() {
  local report="$AIFT_REPORTS/push-report.md"
  local commit_msg="${AIFT_COMMIT_MSG:-chore: update AIFT federation runtime and repository metadata}"

  echo "# AIFT Push Report" > "$report"
  echo >> "$report"
  echo "Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")" >> "$report"
  echo >> "$report"
  echo "Commit message: \`$commit_msg\`" >> "$report"
  echo >> "$report"

  while IFS= read -r p; do
    name="$(repo_name "$p")"

    echo
    echo "======================================"
    echo "Pushing $name"
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

    if ! git pull --ff-only origin "$default_branch"; then
      echo "- $name: skipped, cannot fast-forward" >> "$report"
      echo "Cannot fast-forward. Skipping to avoid overwriting."
      continue
    fi

    # Missing optional paths must not abort staging of existing managed files.
    # Limit the subsequent commit to this same allowlist: an operator may have
    # unrelated changes staged in the index for a different purpose.
    local -a managed_paths=()
    local candidate
    for candidate in \
      FEDERATION.md aift.repo.json federation-os-bridge.sh commands \
      runtime registry intelligence reports manifests scripts aift-os.sh; do
      if [[ -e "$candidate" || -L "$candidate" ]] || \
        git ls-files --error-unmatch -- "$candidate" >/dev/null 2>&1; then
        managed_paths+=("$candidate")
      fi
    done

    if ((${#managed_paths[@]} == 0)); then
      echo "- $name: no managed paths" >> "$report"
      continue
    fi

    if ! git add -A -- "${managed_paths[@]}"; then
      echo "- $name: staging managed paths failed" >> "$report"
      continue
    fi

    if git diff --quiet HEAD -- "${managed_paths[@]}"; then
      echo "- $name: no managed changes" >> "$report"
      echo "No managed changes."
      continue
    fi


    git status --short

    if git commit --only -m "$commit_msg" -- "${managed_paths[@]}"; then
      if git push origin "$default_branch"; then
        echo "- $name: pushed to $default_branch" >> "$report"
        echo "✅ Pushed $name"
      else
        echo "- $name: push failed" >> "$report"
        echo "Push failed."
      fi
    else
      echo "- $name: commit failed" >> "$report"
      echo "Commit failed."
    fi
  done < <(repo_paths)

  echo
  echo "Push report written: $report"
}
