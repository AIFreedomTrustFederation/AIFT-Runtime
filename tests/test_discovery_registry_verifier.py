"""Fail-closed registry reader regression and real-generator integration tests."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "runtime/core/verify-discovery-registry.py"
GENERATOR = ROOT / "runtime/core/aetherion-discover"
FILES = (
    "system-map.json", "capability-graph.json", "dependency-map.json",
    "architecture-map.json", "missing-capabilities.json",
)

spec = importlib.util.spec_from_file_location("aift_registry_verifier", VERIFIER)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class RegistryVerifierTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.registry = self.home / "AIFT" / "registry"
        self.registry.mkdir(parents=True)
        for filename in FILES:
            value = [] if filename in ("system-map.json", "dependency-map.json") else (
                {"repositories": 0} if filename == "architecture-map.json" else {}
            )
            (self.registry / filename).write_text(json.dumps(value) + "\n", encoding="utf-8")
        self.write_manifest()

    def write_manifest(self):
        digests = {
            name: hashlib.sha256((self.registry / name).read_bytes()).hexdigest()
            for name in FILES
        }
        generation = hashlib.sha256(
            json.dumps(digests, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        manifest = {"schema": "aift.runtime.discovery-registry.v1", "algorithm": "sha256",
                    "generation_id": generation, "files": digests}
        (self.registry / "registry-manifest.json").write_text(json.dumps(manifest))
        return generation

    def run_cli(self):
        return subprocess.run(
            [sys.executable, str(VERIFIER), "--registry", str(self.registry)],
            capture_output=True, text=True, check=False, timeout=15,
        )

    def test_valid_snapshot_is_accepted(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        output = json.loads(result.stdout)
        self.assertEqual(output["status"], "passed")
        self.assertEqual(output["files_verified"], 5)
        self.assertEqual(output["generation_id"], verifier.verify_registry(self.registry))

    def test_inconsistent_repository_count_fails_even_with_matching_hashes(self):
        (self.registry / "architecture-map.json").write_text('{"repositories": 1}')
        self.write_manifest()
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("repository count mismatch", result.stdout)

    def test_boolean_repository_count_fails(self):
        (self.registry / "architecture-map.json").write_text('{"repositories": true}')
        self.write_manifest()
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("repository count mismatch", result.stdout)

    def test_nonlist_system_map_fails_even_with_matching_hashes(self):
        (self.registry / "system-map.json").write_text('{}')
        self.write_manifest()
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("invalid repository inventory", result.stdout)

    def set_inventory_projection(self, inventory, dependencies):
        (self.registry / "system-map.json").write_text(json.dumps(inventory))
        (self.registry / "architecture-map.json").write_text(
            json.dumps({"repositories": len(inventory)})
        )
        (self.registry / "dependency-map.json").write_text(json.dumps(dependencies))
        self.write_manifest()

    def test_nonempty_dependency_projection_is_accepted(self):
        self.set_inventory_projection(
            [{"name": "AIFT-OS", "package_managers": ["go"]}],
            [{"repository": "AIFT-OS", "dependencies": ["go"]}],
        )
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_wrong_dependency_fails_even_with_valid_manifest_hashes(self):
        self.set_inventory_projection(
            [{"name": "AIFT-OS", "package_managers": ["go"]}],
            [{"repository": "AIFT-OS", "dependencies": ["npm"]}],
        )
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("dependency map does not match", result.stdout)

    def test_missing_dependency_entry_fails(self):
        self.set_inventory_projection(
            [{"name": "AIFT-OS", "package_managers": ["go"]}], []
        )
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("dependency map does not match", result.stdout)

    def test_duplicate_dependency_entry_fails(self):
        self.set_inventory_projection(
            [{"name": "AIFT-OS", "package_managers": ["go"]},
             {"name": "AIFT-Runtime", "package_managers": ["npm"]}],
            [{"repository": "AIFT-OS", "dependencies": ["go"]},
             {"repository": "AIFT-OS", "dependencies": ["go"]}],
        )
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("duplicate dependency-map.json", result.stdout)

    def test_malformed_dependency_map_fails(self):
        self.set_inventory_projection([], {})
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("dependency map does not match", result.stdout)

    def test_duplicate_system_repository_identity_fails(self):
        self.set_inventory_projection(
            [{"name": "AIFT-OS", "package_managers": ["go"]},
             {"name": "AIFT-OS", "package_managers": ["npm"]}],
            [{"repository": "AIFT-OS", "dependencies": ["go"]}],
        )
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("duplicate repository identity", result.stdout)

    def test_duplicate_manifest_key_fails_closed(self):
        manifest = self.registry / "registry-manifest.json"
        content = manifest.read_text(encoding="utf-8")
        self.assertIn('"algorithm": "sha256"', content)
        manifest.write_text(content.replace(
            '"algorithm": "sha256"',
            '"algorithm": "sha256", "algorithm": "sha256"', 1,
        ), encoding="utf-8")
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("duplicate JSON key: registry-manifest.json", result.stdout)

    def test_duplicate_payload_key_fails_with_matching_hashes(self):
        (self.registry / "architecture-map.json").write_text(
            '{"repositories": 0, "repositories": 0}', encoding="utf-8"
        )
        self.write_manifest()
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("duplicate JSON key: architecture-map.json", result.stdout)

    def test_nested_duplicate_payload_key_fails_with_matching_hashes(self):
        (self.registry / "capability-graph.json").write_text(
            '{"nested": {"enabled": true, "enabled": true}}', encoding="utf-8"
        )
        self.write_manifest()
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("duplicate JSON key: capability-graph.json", result.stdout)

    def test_nonfinite_literal_payload_fails_with_matching_hashes(self):
        (self.registry / "capability-graph.json").write_text(
            '{"nested": {"state": NaN}}', encoding="utf-8"
        )
        self.write_manifest()
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("non-finite JSON number", result.stdout)

    def test_overflowed_exponent_payload_fails_with_matching_hashes(self):
        (self.registry / "missing-capabilities.json").write_text(
            '{"nested": {"risk": 1e9999}}', encoding="utf-8"
        )
        self.write_manifest()
        result = self.run_cli()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("non-finite JSON number", result.stdout)

    def test_finite_float_payload_remains_valid(self):
        (self.registry / "capability-graph.json").write_text(
            '{"nested": {"risk": 1.25}}', encoding="utf-8"
        )
        self.write_manifest()
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_missing_manifest_fails_closed(self):
        (self.registry / "registry-manifest.json").unlink()
        self.assertEqual(self.run_cli().returncode, 1)

    def test_tampered_payload_fails_closed(self):
        (self.registry / FILES[0]).write_text('{"changed":true}')
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("digest mismatch", result.stdout)

    def test_invalid_generation_identifier_fails_closed(self):
        path = self.registry / "registry-manifest.json"
        data = json.loads(path.read_text())
        data["generation_id"] = "0" * 64
        path.write_text(json.dumps(data))
        self.assertEqual(self.run_cli().returncode, 1)

    def test_malformed_payload_fails_even_with_matching_hash(self):
        (self.registry / FILES[1]).write_text("not-json")
        self.write_manifest()
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid JSON", result.stdout)

    def test_symlinked_payload_is_rejected(self):
        original = self.registry / FILES[0]
        target = self.home / "external.json"
        target.write_bytes(original.read_bytes())
        original.unlink()
        original.symlink_to(target)
        self.assertEqual(self.run_cli().returncode, 1)

    def test_manifest_replacement_during_read_is_rejected(self):
        original = verifier.read_regular_file
        manifest = self.registry / "registry-manifest.json"
        calls = 0

        def replace_between_reads(path, limit):
            nonlocal calls
            if path == manifest:
                calls += 1
                if calls == 2:
                    manifest.write_text(manifest.read_text() + "\n")
            return original(path, limit)

        with mock.patch.object(verifier, "read_regular_file", side_effect=replace_between_reads):
            with self.assertRaisesRegex(verifier.RegistryError, "changed during registry read"):
                verifier.verify_registry(self.registry)

    def test_missing_payload_fails_closed(self):
        (self.registry / FILES[4]).unlink()
        self.assertEqual(self.run_cli().returncode, 1)

    @unittest.skipUnless(GENERATOR.is_file() and shutil.which("bash") and shutil.which("python"),
                         "real generator requires the repository checkout, Bash and Python")
    def test_real_generator_outputs_are_accepted(self):
        (self.home / "AIFT" / "AIFT-OS").mkdir()
        (self.home / "AIFT" / "AIFT-OS" / "go.mod").write_text("module example.invalid/aift\n")
        env = dict(os.environ, HOME=str(self.home))
        produced = subprocess.run(["bash", str(GENERATOR)], cwd=self.home, env=env,
                                  capture_output=True, text=True, timeout=15, check=False)
        self.assertEqual(produced.returncode, 0, produced.stdout + produced.stderr)
        self.assertEqual(self.run_cli().returncode, 0)
        (self.registry / "system-map.json").write_text("[]")
        self.assertEqual(self.run_cli().returncode, 1)


if __name__ == "__main__":
    unittest.main()
