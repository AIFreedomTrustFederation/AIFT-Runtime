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

Primary entry points are intentionally simple:

```bash
./bootstrap.sh
./health.sh
./runtime/doctor.sh
./runtime/status.sh
./runtime/verify.sh
```

Additional runtime services include:

```bash
./runtime/graph.sh
./runtime/intel.sh
./runtime/repo.sh
./runtime/registry.sh
./runtime/pull.sh
./runtime/push.sh
```

Synchronization deserves particular care. Pull and push are not morally neutral merely because Git makes them easy. A governed runtime should know which repository it is changing, whether local work would be overwritten, whether the remote has diverged, and whether the operator has delegated the action.

---

## Book IV — The Local Body of the Federation

AIFT-Runtime allows one device to participate in a larger federation without becoming a dumb terminal. Local state remains visible. Local repositories remain sovereign. Local models and tools can be integrated behind provider interfaces. Federation-wide intelligence can ask the machine what it knows without requiring the machine to surrender all of its data to a centralized service.

That is why runtime awareness is a constitutional feature as well as an engineering feature. Local-first systems preserve the possibility of refusal, inspection, repair, and continued operation even when a remote service is unavailable.

### The Return of the Word

In AIFT-Runtime, the Word returns as local truth made reportable. A request reaches the machine, the machine inspects itself, an approved command acts upon reality, verification tests the result, and the result returns with enough evidence to remain understandable. Intelligence becomes trustworthy because it stays close enough to the ground to know when it is wrong.
