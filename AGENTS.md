# Repository Instructions

These instructions apply to the entire repository.

## Working discipline

- Preserve the local-first, inspectable runtime model described in `README.md`.
- Inspect the target script and its callers before changing runtime behavior.
- Do not run synchronization, installation, repair, or mutation scripts merely to
  validate a source change.
- Keep generated files, Python bytecode, logs, model artifacts, credentials, and
  machine-local state out of commits.

## Required verification

Run the canonical dependency-free source gate from the repository root:

```sh
bash qa-local.sh
git diff --check
```

Before concluding work on a clean committed tree, also prove that validation is
non-mutating:

```sh
test -z "$(git status --porcelain)"
```

While preparing a commit, use `git status --short` instead and confirm that only
the intended files are changed.
