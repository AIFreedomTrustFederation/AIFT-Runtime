# AIFT Universal OS — AIFT-Runtime Alignment

> **Proposed integration, not proof of implementation or deployment.** The current repository remains sovereign and its README/AGENTS requirements control. Central architecture is under review in [AIFT-OS PR #92](https://github.com/AIFreedomTrustFederation/AIFT-OS/pull/92).

## Existing boundary

The repository currently provides local discovery, health, graph, governed synchronization and execution scripts. It is not yet verified as a native Linux service manager, boot image, phone HAL or certified physical device controller.

## Responsibility in the future platform

**Role:** Local host service and device capability runtime.

**Produces:** Service health, capability descriptors, local hardware and filesystem adapters, offline execution audit, supervised startup and restart evidence.

**Consumers:** AIFT-OS control plane, the native Living Universe shell and hosted service bridge through explicitly versioned authenticated APIs.

**Limits:** Do not autonomously run sync/install/repair commands merely to verify documentation; never claim ROS/phone/UEFI/physical support without target-specific tests.

## Interface and evidence map

~~~mermaid
flowchart LR
  HOST["Verified local host state"] --> RUNTIME["AIFT-Runtime adapters"]
  RUNTIME --> API["Proposed versioned capabilities / health APIs"]
  API --> OS["AIFT-OS control plane"]
  API --> DESKTOP["Authorized desktop / hosted consumers"]
  POLICY["User consent + scoped host authority"] --> RUNTIME
~~~

This diagram is an **integration target**, not evidence that the endpoints are deployed. A public browser has no implicit host filesystem, camera or shell access.

## Staged acceptance

1. Record current runnable scripts, supported host environments and actual output before adding service claims.
2. Define a typed capability descriptor, API version and unsupported/degraded error state; pin producer and consumer SHAs.
3. Prove an unprivileged supervised Linux service starts/restarts offline in a **disposable virtual machine**, including denial/fault tests.
4. Connect exactly one scoped OS or desktop consumer; verify actual data, not mocks masquerading as live.
5. Do not generalize success to real Android phones, Macs, robots or safety critical workloads.

**Verification gate:** Bash qa-local.sh plus exact-head CI; later a disposable Linux VM must demonstrate supervised service boot, offline/restart, denial paths, source hash and logs.

## Security and governance

Never change physical boot entries, firmware, device drivers, real actuators, production deployment, signing keys, identity policies or data custody through an unattended docs task. No permissions are granted by this roadmap. Continue to preserve source-level truth, negative evidence, ownership and local-first autonomy.

## Architecture references

[Native, hosted and embodied layers](https://github.com/AIFreedomTrustFederation/AIFT-OS/pull/92) · [Current AIFT-OS repository](https://github.com/AIFreedomTrustFederation/AIFT-OS) · [AIFT-Forge SDK](https://github.com/AIFreedomTrustFederation/AIFT-Forge).