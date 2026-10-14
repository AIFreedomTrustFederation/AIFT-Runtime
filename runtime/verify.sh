#!/usr/bin/env bash
source "$HOME/AIFT/runtime/common.sh"

aift_verify_check() {
  local report="$1" label="$2"
  shift 2
  if "$@"; then
    printf '%s\n' "- PASS: $label" >> "$report"
  else
    printf '%s\n' "- FAIL: $label" >> "$report"
    return 1
  fi
}

aift_verify() {
  local report="$AIFT_REPORTS/verify-report.md"
  local original_dir="$PWD"
  local failures=0
  local paths p name task

  printf '# AIFT Verify Report\n\nGenerated: %s\n\n' \
    "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" > "$report"

  if ! paths="$(repo_paths)" || [[ -z "$paths" ]]; then
    printf '%s\n' '- FAIL: No repositories discovered (or discovery failed)' >> "$report"
    printf 'Verify failed: no repositories discovered. Report: %s\n' "$report" >&2
    return 1
  fi

  while IFS= read -r p; do
    [[ -n "$p" ]] || continue
    name="$(repo_name "$p")"
    printf '\n======================================\nVerifying %s\n======================================\n' "$name"
    printf '## %s\n\n' "$name" >> "$report"

    if ! cd "$p"; then
      printf '%s\n\n' '- FAIL: Cannot enter repository directory' >> "$report"
      failures=$((failures + 1))
      continue
    fi

    if [[ -f package.json ]]; then
      if ! command -v npm >/dev/null 2>&1; then
        printf '%s\n' '- FAIL: npm unavailable for Node project' >> "$report"
        failures=$((failures + 1))
      else
        for task in lint typecheck test build; do
          if ! aift_verify_check "$report" "npm run $task --if-present" npm run "$task" --if-present; then
            failures=$((failures + 1))
          fi
        done
      fi
    elif [[ -f Cargo.toml ]]; then
      if ! command -v cargo >/dev/null 2>&1; then
        printf '%s\n' '- FAIL: cargo unavailable for Rust project' >> "$report"
        failures=$((failures + 1))
      elif ! aift_verify_check "$report" 'cargo check' cargo check; then
        failures=$((failures + 1))
      fi
    elif [[ -f go.mod ]]; then
      if ! command -v go >/dev/null 2>&1; then
        printf '%s\n' '- FAIL: go unavailable for Go project' >> "$report"
        failures=$((failures + 1))
      elif ! aift_verify_check "$report" 'go test ./...' go test ./...; then
        failures=$((failures + 1))
      fi
    else
      if ! aift_verify_check "$report" 'git status --short (no build system detected)' git status --short; then
        failures=$((failures + 1))
      fi
    fi
    printf '\n' >> "$report"
    if ! cd "$original_dir"; then
      printf 'Verify failed: cannot restore working directory: %s\n' "$original_dir" >&2
      return 1
    fi
  done <<< "$paths"

  printf 'Failed checks: %d\n' "$failures" >> "$report"
  printf '\nVerify report written: %s (failed checks: %d)\n' "$report" "$failures"
  ((failures == 0))
}
