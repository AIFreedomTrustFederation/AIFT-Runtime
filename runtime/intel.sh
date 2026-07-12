#!/usr/bin/env bash
source "$HOME/AIFT/runtime/common.sh"
source "$HOME/AIFT/runtime/repo.sh"

safe_find_json() {
  local p="$1"
  shift
  find "$p" -maxdepth 5 -type f "$@" \
    ! -path "*/.git/*" \
    ! -path "*/node_modules/*" \
    ! -path "*/.next/*" \
    ! -path "*/dist/*" \
    ! -path "*/build/*" 2>/dev/null \
    | sed "s#^$p/##" | sort | json_array_from_lines
}

aift_intelligence() {
  local out="$AIFT_INTEL/federation-intelligence.json"
  local report="$AIFT_REPORTS/federation-intelligence.md"

  echo "Building intelligence: $out"

  {
    echo "{"
    echo '  "generatedAt": "'"$(date -u +"%Y-%m-%dT%H:%M:%SZ")"'",'
    echo '  "workspace": "'"$(json_escape "$AIFT_WORKSPACE")"'",'
    echo '  "repositories": ['

    local first=1
    for p in $(repo_paths); do
      [ "$first" = 0 ] && echo ","
      first=0

      name="$(repo_name "$p")"
      language="$(detect_language "$p")"
      runtime="$(detect_runtime "$p")"

      commands="$(safe_find_json "$p" \( -path "*/bin/*" -o -path "*/commands/*" -o -path "*/scripts/*" -o -name "*.sh" \))"
      agents="$(safe_find_json "$p" \( -iname "AGENTS.md" -o -iname "*agent*.md" -o -iname "*agent*.json" -o -iname "*agent*.js" -o -iname "*agent*.ts" -o -iname "*agent*.py" \))"
      docs="$(safe_find_json "$p" \( -name "*.md" -o -name "*.mdx" \))"
      schemas="$(safe_find_json "$p" \( -iname "*.schema.json" -o -iname "*schema*.json" \))"
      manifests="$(safe_find_json "$p" \( -iname "*manifest*.json" -o -iname "aift.repo.json" -o -iname "package.json" -o -iname "Cargo.toml" -o -iname "go.mod" -o -iname "Dockerfile" \))"

      cat <<JSON
    {
      "repo": "$(json_escape "$name")",
      "path": "$(json_escape "$p")",
      "language": "$(json_escape "$language")",
      "runtime": "$(json_escape "$runtime")",
      "commands": $commands,
      "agents": $agents,
      "documents": $docs,
      "schemas": $schemas,
      "manifests": $manifests
    }
JSON
    done

    echo
    echo "  ]"
    echo "}"
  } > "$out"

  {
    echo "# AIFT Federation Intelligence"
    echo
    echo "Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo
    for p in $(repo_paths); do
      echo "## $(repo_name "$p")"
      echo
      echo "- Language: \`$(detect_language "$p")\`"
      echo "- Runtime: \`$(detect_runtime "$p")\`"
      echo
    done
  } > "$report"

  echo "Intelligence written."
}
