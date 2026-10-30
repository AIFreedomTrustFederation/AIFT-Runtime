#!/usr/bin/env python3
"""Fail-closed, read-only validation of an Aetherion discovery registry snapshot.

A passing result establishes file consistency with a local, unsigned manifest,
not producer authenticity, repository identity, or federation acceptance.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys

SCHEMA = "aift.runtime.discovery-registry.v1"
FILES = (
    "system-map.json", "capability-graph.json", "dependency-map.json",
    "architecture-map.json", "missing-capabilities.json",
)
MAX_MANIFEST_BYTES = 16 * 1024
MAX_FILE_BYTES = 32 * 1024 * 1024


class RegistryError(Exception):
    """Registry evidence cannot be trusted for this read."""


def read_regular_file(path: Path, limit: int) -> bytes:
    """Reject symlinks, special files and oversized inputs before hashing."""
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        if path.is_symlink():
            raise RegistryError(f"symlink is not allowed: {path.name}")
        fd = os.open(path, flags)
        try:
            metadata = os.fstat(fd)
            if not stat.S_ISREG(metadata.st_mode):
                raise RegistryError(f"not a regular file: {path.name}")
            if metadata.st_size > limit:
                raise RegistryError(f"file too large: {path.name}")
            with os.fdopen(fd, "rb", closefd=False) as stream:
                data = stream.read(limit + 1)
            if len(data) > limit:
                raise RegistryError(f"file too large: {path.name}")
            return data
        finally:
            os.close(fd)
    except OSError as error:
        raise RegistryError(f"cannot read {path.name}: {error.strerror or type(error).__name__}") from error


def parse_json(raw: bytes, filename: str):
    # Python's default JSON parser silently keeps the last duplicate key.
    # Reject ambiguous objects even when a manifest correctly hashes the bytes.
    def unique_keys(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise RegistryError(f"duplicate JSON key: {filename}")
            value[key] = item
        return value

    def reject_constant(_value):
        raise RegistryError(f"non-finite JSON number: {filename}")

    def finite_float(token):
        number = float(token)
        if not math.isfinite(number):
            raise RegistryError(f"non-finite JSON number: {filename}")
        return number

    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_keys,
                          parse_constant=reject_constant, parse_float=finite_float)
    except (UnicodeDecodeError, ValueError) as error:
        raise RegistryError(f"invalid JSON: {filename}") from error


def verify_registry(registry: Path) -> str:
    """Return the verified generation identifier, or raise RegistryError."""
    manifest_path = registry / "registry-manifest.json"
    first = read_regular_file(manifest_path, MAX_MANIFEST_BYTES)
    manifest = parse_json(first, manifest_path.name)
    if not isinstance(manifest, dict) or set(manifest) != {"schema", "algorithm", "generation_id", "files"}:
        raise RegistryError("invalid manifest structure")
    if manifest["schema"] != SCHEMA or manifest["algorithm"] != "sha256":
        raise RegistryError("unsupported manifest schema or algorithm")
    digests = manifest["files"]
    if not isinstance(digests, dict) or set(digests) != set(FILES):
        raise RegistryError("manifest must bind exactly the five registry outputs")
    if any(not isinstance(digests[name], str) or not re.fullmatch(r"[0-9a-f]{64}", digests[name]) for name in FILES):
        raise RegistryError("invalid file digest")
    generation = hashlib.sha256(
        json.dumps(digests, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if manifest["generation_id"] != generation:
        raise RegistryError("manifest generation identifier mismatch")

    parsed = {}
    for name in FILES:
        raw = read_regular_file(registry / name, MAX_FILE_BYTES)
        if hashlib.sha256(raw).hexdigest() != digests[name]:
            raise RegistryError(f"digest mismatch: {name}")
        parsed[name] = parse_json(raw, name)

    # A manifest can hash perfectly while binding contradictory inventory data.
    # Require the generated architecture count to agree with the system map.
    inventory = parsed["system-map.json"]
    if not isinstance(inventory, list):
        raise RegistryError("invalid repository inventory: system-map.json must be an array")
    architecture = parsed["architecture-map.json"]
    count = architecture.get("repositories") if isinstance(architecture, dict) else None
    if type(count) is not int or count != len(inventory):
        raise RegistryError("repository count mismatch: architecture-map.json vs system-map.json")

    # The dependency map must be an exact projection of the inventory's
    # repository identities and package-manager declarations. Matching hashes
    # alone cannot establish that two independently serialized maps agree.
    expected = {}
    for entry in inventory:
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str) or not entry["name"]:
            raise RegistryError("invalid repository identity in system-map.json")
        managers = entry.get("package_managers")
        if not isinstance(managers, list) or any(not isinstance(manager, str) for manager in managers):
            raise RegistryError("invalid package managers in system-map.json")
        if entry["name"] in expected:
            raise RegistryError("duplicate repository identity in system-map.json")
        expected[entry["name"]] = managers

    dependencies = parsed["dependency-map.json"]
    if not isinstance(dependencies, list) or len(dependencies) != len(expected):
        raise RegistryError("dependency map does not match repository inventory")
    observed = {}
    for entry in dependencies:
        if (not isinstance(entry, dict) or not isinstance(entry.get("repository"), str)
                or not isinstance(entry.get("dependencies"), list)):
            raise RegistryError("invalid dependency-map.json entry")
        name, managers = entry["repository"], entry["dependencies"]
        if name in observed or any(not isinstance(manager, str) for manager in managers):
            raise RegistryError("invalid or duplicate dependency-map.json entry")
        observed[name] = managers
    if observed != expected:
        raise RegistryError("dependency map does not match repository inventory")

    # Detect a manifest refresh during the read, including a same-generation
    # rewrite with different formatting. This is not a filesystem transaction.
    if read_regular_file(manifest_path, MAX_MANIFEST_BYTES) != first:
        raise RegistryError("manifest changed during registry read")
    return generation


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=Path.home() / "AIFT" / "registry")
    args = parser.parse_args(argv)
    try:
        generation = verify_registry(args.registry)
        result = {"schema": "aift.runtime.registry-check.v1", "status": "passed",
                  "generation_id": generation, "files_verified": len(FILES)}
        code = 0
    except RegistryError as error:
        result = {"schema": "aift.runtime.registry-check.v1", "status": "failed", "reason": str(error)}
        code = 1
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
