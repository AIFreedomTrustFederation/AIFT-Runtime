#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

mapfile -d '' shell_files < <(git ls-files -z '*.sh')
mapfile -d '' python_files < <(git ls-files -z '*.py')

if ((${#shell_files[@]} == 0)); then
  echo "No tracked shell scripts found" >&2
  exit 1
fi

if ((${#python_files[@]} == 0)); then
  echo "No tracked Python sources found" >&2
  exit 1
fi

for file in "${shell_files[@]}"; do
  bash -n "$file"
done

cache_dir="$(mktemp -d)"
trap 'rm -rf "$cache_dir"' EXIT
PYTHONPYCACHEPREFIX="$cache_dir" python3 -m py_compile "${python_files[@]}"

printf 'Validated %d shell scripts and %d Python sources.\n' \
  "${#shell_files[@]}" "${#python_files[@]}"
