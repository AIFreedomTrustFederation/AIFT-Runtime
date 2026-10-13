#!/usr/bin/env bash
source "$HOME/AIFT/runtime/common.sh"

aift_verify() {
  local report="$AIFT_REPORTS/verify-report.md"
  local p name check failures=0 checked=0

  {
    printf '# AIFT Verify Report\n\n'
    printf 'Generated: %s\n\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  } > "$report" || return 1

  while IFS= read -r p; do
    [ -n "$p" ] || continue
    checked=$((checked + 1))
    name="$(repo_name "$p")"

    printf '\n======================================\nVerifying %s\n======================================\n' "$name"
    printf '## %s\n\n' "$name" >> "$report"

    if [ -f "$p/package.json" ]; then
      if ! command -v npm >/dev/null 2>&1; then
        printf '%s\n' '- FAIL: npm unavailable for Node project' >> "$report"
        failures=$((failures + 1))
      else
        for check in lint typecheck test build; do
          if (cd "$p" && npm run "$check" --if-present); then
            printf -- '- OK: npm run %s --if-present (missing scripts are skipped)\n' "$check" >> "$report"
          else
            printf -- '- FAIL: npm run %s --if-present\n' "$check" >> "$report"
            failures=$((failures + 1))
          fi
        done
      fi
    elif [ -f "$p/Cargo.toml" ]; then
      if command -v cargo >/dev/null 2>&1 && (cd "$p" && cargo check); then
        printf '%s\n' '- OK: cargo check' >> "$report"
      else
        printf '%s\n' '- FAIL: cargo check (or cargo unavailable)' >> "$report"
        failures=$((failures + 1))
      fi
    elif [ -f "$p/go.mod" ]; then
      if command -v go >/dev/null 2>&1 && (cd "$p" && go test ./...); then
        printf '%s\n' '- OK: go test ./...' >> "$report"
      else
        printf '%s\n' '- FAIL: go test ./... (or go unavailable)' >> "$report"
        failures=$((failures + 1))
      fi
    else
      if (cd "$p" && git status --short); then
        printf '%s\n' '- INFO: no recognized build system; git status checked (not a test)' >> "$report"
      else
        printf '%s\n' '- FAIL: git status' >> "$report"
        failures=$((failures + 1))
      fi
    fi
    printf '\n' >> "$report"
  done < <(repo_paths)

  if [ "$checked" -eq 0 ]; then
    printf '%s\n' '- FAIL: no repositories discovered' >> "$report"
    failures=$((failures + 1))
  fi
  printf 'Result: %s failure(s) across %s repository/repositories.\n' "$failures" "$checked" >> "$report"
  printf '\nVerify report written: %s\n' "$report"
  [ "$failures" -eq 0 ]
}
