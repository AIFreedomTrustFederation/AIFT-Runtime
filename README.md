# AIFT-Runtime — Local Intelligence and Execution

**The runtime layer of the AI Freedom Trust Federation: local runtime intelligence, repository awareness, graph, health, governed synchronization, and execution services.**

| Federation metadata | Value |
| --- | --- |
| Layer | `runtime` |
| Role | local runtime intelligence, repository awareness, graph, health, governed synchronization, and execution services |
| Control plane | AIFT-OS |
| Doctrine | AI-Freedom-Trust / SOP-ALOHA-001 |
| Core commands | `health.sh`, `bootstrap.sh`, `runtime/doctor.sh`, `runtime/status.sh`, `runtime/verify.sh` |
| Operating standards | local-first, inspectable, sovereign by default, AI behind governed provider interfaces, verify before mutation |

AIFT-Runtime is the local execution and awareness layer that gives the Federation a practical body on a machine. Where AIFT-OS reasons across the Federation as a control plane, AIFT-Runtime lives closer to the filesystem, repositories, local graph, synchronization state, health checks, and intelligence services that make an individual workspace observable and operable.

It is not the constitutional genome, the package Forge, the cloud provider, or the economic protocol. Its responsibility is narrower and concrete: **know the local environment, expose truthful runtime state, carry governed operations, and return evidence to the control plane and human operator.**

The covenant is carried in the [One Eternal Scroll of ALO'ha](https://aifreedomtrustfederation.github.io/AI-Freedom-Trust/docs/pdf/one-eternal-scroll-of-aloha.pdf) and implemented through [SOP-ALOHA-001](https://github.com/AIFreedomTrustFederation/AI-Freedom-Trust/blob/main/SOP-ALOHA-001.md).

---

## Book I — Intelligence Close to the Ground

A federation cannot be truthful if its central model knows more about a repository than the machine actually running it. AIFT-Runtime therefore begins close to the ground: local paths, local Git state, available commands, repository awareness, health, graph relationships, and actual execution results.

Its `runtime/` tree contains the services through which that awareness becomes operational. `doctor.sh` examines the runtime environment. `status.sh` reports state. `registry.sh` and `repo.sh` work with local repository awareness. `graph.sh` exposes relationships. `intel.sh` and the `intelligence/` and `ai/` paths carry the intelligence layer. `pull.sh` and `push.sh` govern synchronization rather than treating Git mutation as an invisible background act. `verify.sh` closes the loop by checking that the runtime remains coherent after work is performed.

### Illuminated passage — memory that remains attributable

![Circleunchain Memory Network](https://raw.githubusercontent.com/AIFreedomTrustFederation/AI-Freedom-Trust/main/docs/images/aetherion/circleunchain-memory-network.png)

For Runtime, the memory-network image represents local awareness with provenance. A graph is useful because relationships remain attributable to real repositories and states, not because the runtime has created an abstract picture detached from the files it describes.

---

## Book II — Runtime in the Federation Architecture

The Runtime occupies the boundary between federation-wide orchestration and machine-local reality.

- **AIFT-OS → Runtime:** the control plane asks what exists, what is healthy, what can execute, and what evidence the local machine can provide.
- **Runtime → AIFT-OS:** the runtime returns repository state, graph relationships, health, verification results, synchronization outcomes, and intelligence gathered from actual local conditions.
- **AIFT-Genesis → Runtime:** identity and constitutional inheritance may describe what a repository is allowed to be; Runtime does not rewrite that identity. It discovers and serves the instantiated system.
- **AIFT-Forge → Runtime:** reusable runtime and agent patterns may be inherited from Forge, but the local execution path remains accountable to real files and commands.
- **VPS ↔ Runtime:** provider-node and server infrastructure can expose workloads and node state through runtime adapters, while VPS retains authority over deployment and infrastructure policy.
- **Aetherion ↔ Runtime:** economic or wallet services may be invoked only through governed interfaces. Runtime does not gain transaction or custody authority because it can execute a command.
- **TheMindofAll ↔ Runtime:** locally owned models and model manifests may become intelligence providers while their provenance, license, and loading rules remain in the model repository.

The distinction matters: **AIFT-OS decides across the federation; AIFT-Runtime proves what the local environment can actually do.**

---

## Book III — SOP-ALOHA-001 at Runtime

The covenant loop becomes a machine-local execution discipline:

```text
Receive → Inspect → Name → Propose → Consent → Act → Verify → Record → Return
```

**Receive** accepts a requested local operation or federation query. **Inspect** reads the actual environment, repository awareness, health, and state before mutation. **Name** identifies the repository, command, risk, dependencies, and expected result. **Propose** describes the operation when judgment or risk is involved. **Consent** is required when the command exceeds delegated synchronization, verification, or low-risk execution boundaries. **Act** calls the real local operation. **Verify** checks the resulting runtime and repository state. **Record** leaves inspectable output, graph/state information, or Git evidence appropriate to the action. **Return** sends the result back to AIFT-OS or the human operator without converting uncertainty into success.

### Execution prerequisites and verification limits

The checked-in scripts currently have two distinct invocation styles. `bootstrap.sh` and `health.sh` contain top-level commands and are intended to run from the repository root in a Termux environment. Bootstrap requires `git-lfs`, pulls LFS objects, checks for `runtime/ai/models/aetherion.gguf`, and invokes `runtime/ai/start.sh` only if it is executable. Health prints Git/LFS/model information and queries the local `127.0.0.1:8080/health` endpoint; its output is diagnostic, not proof of service readiness.

### Local model artifact and startup checks

The source-validation gate in [`qa-local.sh`](qa-local.sh) checks that tracked `*.gguf` entries are well-formed Git LFS pointers; it does not download model bytes or test inference. [`bootstrap.sh`](bootstrap.sh) invokes `git lfs pull`, then checks only that `runtime/ai/models/aetherion.gguf` exists. It does not independently verify that the file contains a loadable GGUF model. Successful source CI or a "Bootstrap complete" message therefore does not prove that the model is loaded or serving requests.

[`runtime/ai/start.sh`](runtime/ai/start.sh) expects `$HOME/Aetherion/llama.cpp/build/bin/llama-server` and a writable `runtime/ai/logs/` directory; the script does not create the log directory. It attempts a background launch and immediately prints "Aetherion ONLINE" without checking process startup or HTTP readiness. [`runtime/ai/status.sh`](runtime/ai/status.sh) considers either a live recorded PID or a response from `127.0.0.1:8080/v1/models` sufficient to print "ONLINE"; neither proves that the intended model is loaded or can generate output. [`health.sh`](health.sh) probes the local `/health` endpoint but does not test inference. Before reporting operational readiness, inspect the downloaded model, server log, HTTP response, and a representative local inference request. The configured server binds to `127.0.0.1`; these scripts do not establish public API access or an authentication boundary.

By contrast, `runtime/doctor.sh`, `runtime/status.sh`, and `runtime/verify.sh` **define shell functions** (`aift_doctor`, `aift_status`, and `aift_verify`) rather than invoking them automatically. They source `$HOME/AIFT/runtime/common.sh`, so that workspace file and its helpers must exist. Run these functions from a configured workspace, for example:

```bash
source ./runtime/doctor.sh && aift_doctor
source ./runtime/status.sh && aift_status
source ./runtime/verify.sh && aift_verify
```

`aift_verify` writes per-command PASS/FAIL results to `$AIFT_REPORTS/verify-report.md` and returns a nonzero status when an attempted Node, Cargo, Go, or fallback Git check fails, when a required tool is missing, or when no repositories are discovered. It continues checking other repositories so the report captures all observed failures. Run `source ./runtime/verify.sh && aift_verify` from a configured workspace; a nonzero result now signals an unsuccessful verification. Node checks still use `npm run <script> --if-present`, so a successful command may mean that the corresponding script was absent; inspect each project's scripts and command output before claiming coverage. This source-level behavior is not proof that a live model or service is healthy.


The federation manifest's `commands.verify` invokes `bash -c 'source ./runtime/verify.sh && aift_verify'` from the repository root. Direct execution of `./runtime/verify.sh` only defines the function and does not verify repositories. This command requires Bash, `$HOME/AIFT/runtime/common.sh`, a configured workspace, and writable reports directory. Failures are returned to the caller. The manifest's `doctor` and `status` entries now source the required `$HOME/AIFT/runtime/common.sh`, source the function-only scripts, and invoke `aift_doctor` or `aift_status`. The explicit common-file preflight prevents a missing workspace helper from silently producing a successful, empty diagnostic. These commands report diagnostics and repository state, not application readiness or successful builds. Running `./runtime/doctor.sh` or `./runtime/status.sh` directly still only defines the functions.

Repository discovery in `runtime/common.sh` recognizes both ordinary Git checkouts (a `.git` directory) and linked Git worktrees (a `.git` file) immediately beneath `$AIFT_WORKSPACE`. Invalid Git markers are ignored. `aift_verify`, `aift_status`, `aift_pull`, and `aift_push` now preserve spaces and shell glob characters in discovered repository paths. Repository discovery is line-delimited, so paths containing newline characters remain unsupported. This source-level improvement does not verify remote synchronization or eliminate the synchronization risks described below.

The dependency-free `bash qa-local.sh` source gate runs isolated regression tests for verification exit status and repository discovery; it does not execute live workspace builds or runtime health checks.

The experimental [`runtime/intelligence/test-runner.py`](runtime/intelligence/test-runner.py) reads a task-specific transformer report and runs `npm run check` and `npm run build` in `$HOME/AIFT/Aether_Coin_biozonecurrency`. It writes a JSON test report with `mutation_allowed` and now exits nonzero when either command fails or the transformer report is missing; callers must check the process exit status as well as the report. This test runner does not apply patches, prove production readiness, or enforce authorization. `python3 -m unittest discover -s tests -p 'test_intelligence_test_runner.py'` exercises its failure and success paths using isolated fake npm commands.


Primary entry points are intentionally simple:

```bash
./bootstrap.sh
./health.sh
source ./runtime/doctor.sh && aift_doctor
source ./runtime/status.sh && aift_status
source ./runtime/verify.sh && aift_verify
```

Additional runtime services include:

```bash
source ./runtime/graph.sh && aift_graph
source ./runtime/dashboard.sh && aift_dashboard
source ./runtime/intel.sh && aift_intelligence
source ./runtime/registry.sh && aift_registry
source ./runtime/pull.sh && aift_pull
source ./runtime/push.sh && aift_push
```

These are sourced function entry points, not standalone executables: running `runtime/intel.sh`, `runtime/pull.sh`, or `runtime/push.sh` directly only defines functions and does not perform the named operation. They depend on helpers installed under `$HOME/AIFT/runtime/`. `runtime/repo.sh` is a library of detection functions, not an executable report command. **Review local changes and remote branches before invoking `aift_pull` or `aift_push`**: `aift_push` can change local branches, create commits, and publish them without an approval prompt. `runtime/workflow.sh` likewise defines `aift_update`, which chains these mutating operations; its presence does not implement the delegation policy described above.

`aift_push` now stages only existing managed paths (`FEDERATION.md`, `aift.repo.json`, `federation-os-bridge.sh`, `commands/`, `runtime/`, `registry/`, `intelligence/`, `reports/`, `manifests/`, `scripts/`, and `aift-os.sh`) and commits only those paths. Missing optional paths no longer block other managed changes. Unrelated staged files remain staged and are not included in the automated commit. Newly added files and tracked deletions inside managed paths are still eligible for publication. This is a path boundary, **not** approval of file contents: review changes inside managed directories before unattended publishing. `python3 -m unittest discover -s tests -p 'test_push_scope.py'` exercises this behavior against isolated local Git remotes.

The dashboard and graph generators are function-only scripts: executing their files directly does not generate a report. In a configured workspace, source and invoke the functions as shown above. Both generators preserve spaces and shell glob characters in discovered repository paths; newline-containing paths remain unsupported.

The registry generator is also function-only. From a configured workspace, `source ./runtime/registry.sh && aift_registry` writes `$AIFT_REGISTRY/federation-index.json`. Registry entries now preserve repository names and paths containing spaces or shell glob characters; newline-containing paths remain unsupported. This is a local inventory, not proof of remote synchronization or application readiness.

Synchronization deserves particular care. Pull and push are not morally neutral merely because Git makes them easy. A governed runtime should know which repository it is changing, whether local work would be overwritten, whether the remote has diverged, and whether the operator has delegated the action.

### Risk-based delegation for automation

Routine, reversible operations such as documentation corrections, diagnostics, tests, and safe synchronization may run without per-action approval when covered by standing operator delegation, repository permissions, and automated checks. Verify relevant tests and repository state before publishing changes; respect branch protections and record the resulting commit or failure. Escalate major doctrinal or constitutional revisions, trust-identity and governing-authority changes, security-sensitive policy changes, destructive resets, and other high-impact operations for explicit review. Delegation is an intended governance policy, **not** an authorization gate currently enforced by `runtime/pull.sh`, `runtime/push.sh`, or `runtime/workflow.sh`; those scripts must not be treated as implementing this classification merely because the README describes it. `aift_pull` now refuses to switch branches: each discovered repository must be on its detected remote default branch with a clean working tree. It reports and skips non-default branches, detached HEADs, and uncommitted changes; it returns nonzero when any repository is blocked, fetch fails, or a pull cannot fast-forward. `aift_update` stops before later stages, including push, when the pull stage fails, even when called inside a conditional shell expression. Repositories without an `origin` remain skipped. This safety preflight does not govern standalone `aift_push` calls or provide a general approval gate. Run `python3 -m unittest discover -s tests -p 'test_pull_safety.py'` to exercise isolated Git fixtures; live Termux synchronization and external remote availability are not established by these tests.


---

## Book IV — The Local Body of the Federation

AIFT-Runtime allows one device to participate in a larger federation without becoming a dumb terminal. Local state remains visible. Local repositories remain sovereign. Local models and tools can be integrated behind provider interfaces. Federation-wide intelligence can ask the machine what it knows without requiring the machine to surrender all of its data to a centralized service.

That is why runtime awareness is a constitutional feature as well as an engineering feature. Local-first systems preserve the possibility of refusal, inspection, repair, and continued operation even when a remote service is unavailable.

### The Return of the Word

In AIFT-Runtime, the Word returns as local truth made reportable. A request reaches the machine, the machine inspects itself, an approved command acts upon reality, verification tests the result, and the result returns with enough evidence to remain understandable. Intelligence becomes trustworthy because it stays close enough to the ground to know when it is wrong.
