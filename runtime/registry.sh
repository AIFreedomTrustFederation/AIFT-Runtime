#!/usr/bin/env bash
source "$HOME/AIFT/runtime/common.sh"
source "$HOME/AIFT/runtime/repo.sh"

aift_registry() {
  local out="$AIFT_REGISTRY/federation-index.json"

  echo "Building registry: $out"

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
      branch="$(git_branch "$p")"
      commit="$(git_commit "$p")"
      changed="$(git_changed_count "$p")"
      language="$(detect_language "$p")"
      runtime="$(detect_runtime "$p")"

      cat <<JSON
    {
      "name": "$(json_escape "$name")",
      "path": "$(json_escape "$p")",
      "branch": "$(json_escape "$branch")",
      "commit": "$(json_escape "$commit")",
      "changedFiles": $changed,
      "language": "$(json_escape "$language")",
      "runtime": "$(json_escape "$runtime")",
      "repoManifest": "$(json_escape "$p/aift.repo.json")",
      "federationDoc": "$(json_escape "$p/FEDERATION.md")"
    }
JSON
    done

    echo
    echo "  ]"
    echo "}"
  } > "$out"

  echo "Registry written."
}
