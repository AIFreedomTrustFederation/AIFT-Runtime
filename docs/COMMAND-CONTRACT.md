# Engineering command contract

Run commands from the repository root. Source QA remains separate from live
capability, security, dependency provenance and deployment acceptance.

| Command | Prerequisites | Effects and success meaning |
| --- | --- | --- |
| `bash qa-local.sh` | Repository root; Bash, Git, Python 3 and ordinary source checkout | Parses tracked shell/Python/JSON, checks LFS pointer text and runs isolated regressions. Temporary Python cache is cleaned. Does not install, synchronize, repair, download models or test inference. |
| `python3 -B scripts/run_runtime_verification.py --output /absolute/outside-checkout/new.json` | Same source QA prerequisites; clean exact commit; destination outside checkout | Runs source QA and publishes unsigned evidence using atomic replacement. Writes only explicitly requested evidence plus temporary files. Exit 0 means declared checks passed, 1 means failed checks, 2 means evidence generation/publication failed. |

The Runtime producer resolves the output path (including symlinks) and replaces
an existing destination. Use a new, explicit path outside the checkout and
archive prior evidence first; this is not Forge's no-clobber publication model.
Inspect script help/source before using evidence generation. Host filesystem
publication semantics may differ on Android/PRoot; do not convert unsupported
atomic publication into success. Provisioning and machine-specific doctor/status
commands are separate from source QA. Manifest `$HOME/AIFT` paths are declarations,
not proof those paths exist. Never run bootstrap as a source test.

Preparation PR #14 passed hosted `validate` at
`e688d6b852f818e4fd8ebe1c8deee29af0815417`
([run](https://github.com/AIFreedomTrustFederation/AIFT-Runtime/actions/runs/44213257609)).

After verification run `git diff --check` and inspect `git status --short`.
After committing, require a clean worktree. Hosted evidence must match the final
PR head; older green checks do not certify subsequent commits.
