#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path

BASE = Path.home() / "AIFT"

INPUT = BASE / "registry/patch-plans/quantum-vault-refined.json"
OUTPUT = BASE / "registry/patch-plans/quantum-vault-execution.json"


def main():

    print("""
================================
 Aetherion Patch Synthesizer v1
================================
""")

    if not INPUT.exists():
        print("Missing:")
        print(INPUT)
        sys.exit(1)

    with open(INPUT) as f:
        data = json.load(f)

    files = []

    if "files" in data:
        files = data["files"]
    elif "targets" in data:
        files = data["targets"]

    execution = {
        "task": "quantum-vault",
        "strategy": "dependency-first",
        "generated_by": "Aetherion Patch Synthesizer v1",
        "phases": [
            {
                "phase": 1,
                "name": "core-service",
                "action": "analyze_contract",
                "targets": [
                    "server/services/quantum-vault.ts"
                ]
            },
            {
                "phase": 2,
                "name": "security-primitives",
                "action": "validate_exports",
                "targets": [
                    "client/src/lib/quantum-vault/bitcoin-security.ts",
                    "client/src/lib/quantum-vault/fractal-sharding.ts",
                    "client/src/lib/quantum-vault/index.ts",
                    "client/src/lib/quantum-vault/smart-contracts.ts",
                    "client/src/lib/quantum-vault/notification-services.ts"
                ]
            },
            {
                "phase": 3,
                "name": "consumer-update",
                "action": "dependency_alignment",
                "targets": [
                    "client/src/components/security/QuantumSecureVaultManager.tsx"
                ]
            },
            {
                "phase": 4,
                "name": "route-validation",
                "action": "verify_imports",
                "targets": [
                    "server/routes/mysterion.ts",
                    "server/services/mysterion-ai.ts"
                ]
            },
            {
                "phase": 5,
                "name": "secondary-links",
                "action": "verify_consumers",
                "targets": [
                    "client/src/lib/fractalcoin/index.ts"
                ]
            }
        ],
        "source_files": files,
        "requires_confirmation": True
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT, "w") as f:
        json.dump(execution, f, indent=2)

    print("Generated:")
    print(OUTPUT)

    print("")
    print("PHASE PLAN:")
    for p in execution["phases"]:
        print(f'{p["phase"]}. {p["name"]}')
        for t in p["targets"]:
            print(" -", t)


if __name__ == "__main__":
    main()
