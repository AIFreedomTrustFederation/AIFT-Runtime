#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

mapfile -d '' shell_files < <(
  {
    git ls-files -z '*.sh'
    git grep -Ilz '^#!.*bash' --
  } | sort -zu
)
mapfile -d '' python_files < <(git ls-files -z '*.py')
mapfile -d '' json_files < <(git ls-files -z '*.json')
mapfile -d '' model_files < <(git ls-files -z '*.gguf')
mapfile -d '' tracked_runtime_state < <(git ls-files -z '*.pid' '*.log')
mapfile -d '' tracked_backup_files < <(
  git ls-files -z '*.bak' '*.backup' '*.backup.*' '*.orig' '*~'
)

if ((${#shell_files[@]} == 0)); then
  echo "No tracked shell scripts found" >&2
  exit 1
fi

if ((${#python_files[@]} == 0)); then
  echo "No tracked Python sources found" >&2
  exit 1
fi

if ((${#json_files[@]} == 0)); then
  echo "No tracked JSON documents found" >&2
  exit 1
fi

if ((${#model_files[@]} == 0)); then
  echo "No tracked GGUF model pointers found" >&2
  exit 1
fi

if ((${#tracked_runtime_state[@]} != 0)); then
  printf 'Machine-local runtime state must not be tracked:\n' >&2
  printf '  %s\n' "${tracked_runtime_state[@]}" >&2
  exit 1
fi

if ((${#tracked_backup_files[@]} != 0)); then
  printf 'Generated backup files must not be tracked:\n' >&2
  printf '  %s\n' "${tracked_backup_files[@]}" >&2
  exit 1
fi

for probe in runtime/ai/aetherion.pid runtime/ai/logs/aetherion.log; do
  if ! git check-ignore --quiet --no-index "$probe"; then
    printf 'Machine-local runtime state is not ignored: %s\n' "$probe" >&2
    exit 1
  fi
done

for file in "${shell_files[@]}"; do
  bash -n "$file"
done

cache_dir="$(mktemp -d)"
trap 'rm -rf "$cache_dir"' EXIT
PYTHONPYCACHEPREFIX="$cache_dir" python3 -m py_compile "${python_files[@]}"

for file in "${json_files[@]}"; do
  python3 - "$file" <<'PY'
import json
import sys


def reject_duplicate_keys(pairs):
    document = {}
    for key, value in pairs:
        if key in document:
            raise ValueError(f"duplicate JSON key: {key!r}")
        document[key] = value
    return document


with open(sys.argv[1], encoding="utf-8") as source:
    json.load(source, object_pairs_hook=reject_duplicate_keys)
PY
done

for file in "${model_files[@]}"; do
  if [[ "$(git check-attr filter -- "$file")" != *': lfs' ]]; then
    printf 'GGUF model is not assigned to Git LFS: %s\n' "$file" >&2
    exit 1
  fi

  mapfile -t pointer < <(git show "HEAD:$file")
  if ((${#pointer[@]} != 3)) ||
    [[ "${pointer[0]}" != 'version https://git-lfs.github.com/spec/v1' ]] ||
    [[ ! "${pointer[1]}" =~ ^oid\ sha256:[0-9a-f]{64}$ ]] ||
    [[ ! "${pointer[2]}" =~ ^size\ [1-9][0-9]*$ ]]; then
    printf 'Invalid Git LFS pointer for GGUF model: %s\n' "$file" >&2
    exit 1
  fi
done

printf 'Validated %d shell scripts, %d Python sources, %d JSON documents, and %d model pointers.\n' \
  "${#shell_files[@]}" "${#python_files[@]}" "${#json_files[@]}" \
  "${#model_files[@]}"
