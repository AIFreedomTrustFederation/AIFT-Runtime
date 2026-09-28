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
mapfile -d '' tracked_runtime_state < <(git ls-files -z '*.pid' '*.log')

if ((${#shell_files[@]} == 0)); then
  echo "No tracked shell scripts found" >&2
  exit 1
fi

if ((${#python_files[@]} == 0)); then
  echo "No tracked Python sources found" >&2
  exit 1
fi

if ((${#tracked_runtime_state[@]} != 0)); then
  printf 'Machine-local runtime state must not be tracked:\n' >&2
  printf '  %s\n' "${tracked_runtime_state[@]}" >&2
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

printf 'Validated %d shell scripts and %d Python sources.\n' \
  "${#shell_files[@]}" "${#python_files[@]}"
