#!/usr/bin/env bash
source "$HOME/AIFT/runtime/common.sh"

aift_verify() {
  local report="$AIFT_REPORTS/verify-report.md"

  echo "# AIFT Verify Report" > "$report"
  echo >> "$report"
  echo "Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")" >> "$report"
  echo >> "$report"

  for p in $(repo_paths); do
    name="$(repo_name "$p")"

    echo
    echo "======================================"
    echo "Verifying $name"
    echo "======================================"

    cd "$p"
    echo "## $name" >> "$report"
    echo >> "$report"

    if [ -f package.json ] && command -v npm >/dev/null 2>&1; then
      npm run lint --if-present || true
      npm run typecheck --if-present || true
      npm run test --if-present || true
      npm run build --if-present || true
      echo "- Node checks attempted" >> "$report"
    elif [ -f Cargo.toml ] && command -v cargo >/dev/null 2>&1; then
      cargo check || true
      echo "- Cargo check attempted" >> "$report"
    elif [ -f go.mod ] && command -v go >/dev/null 2>&1; then
      go test ./... || true
      echo "- Go tests attempted" >> "$report"
    else
      git status --short || true
      echo "- No build system detected; git status checked" >> "$report"
    fi

    echo >> "$report"
  done

  echo
  echo "Verify report written: $report"
}
