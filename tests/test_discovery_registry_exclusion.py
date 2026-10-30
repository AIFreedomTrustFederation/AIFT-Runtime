"""Black-box checks that generated registry state is not counted as a repository."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "runtime/core/aetherion-discover"
BASH = shutil.which("bash")
PYTHON = shutil.which("python")


@unittest.skipUnless(BASH and PYTHON, "bash and python are required")
class DiscoveryRegistryExclusionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.aift = self.home / "AIFT"
        self.registry = self.aift / "registry"
        self.registry.mkdir(parents=True)
        os_repo = self.aift / "AIFT-OS"
        os_repo.mkdir()
        (os_repo / "go.mod").write_text("module example.invalid/aift-os\n")
        runtime_repo = self.aift / "AIFT-Runtime"
        runtime_repo.mkdir()
        (runtime_repo / "README.md").write_text("# Runtime fixture\n")

    def discover(self):
        env = dict(os.environ, HOME=str(self.home))
        result = subprocess.run(
            [BASH, str(SCRIPT)], env=env, cwd=self.home,
            capture_output=True, text=True, timeout=15, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def read(self, filename):
        return json.loads((self.registry / filename).read_text())

    def test_registry_is_not_a_discovered_repository(self):
        result = self.discover()
        system = self.read("system-map.json")
        names = {repo["name"] for repo in system}
        self.assertEqual(names, {"AIFT-OS", "AIFT-Runtime"})
        self.assertEqual(self.read("architecture-map.json")["repositories"], 2)
        self.assertEqual({item["repository"] for item in self.read("dependency-map.json")}, names)
        self.assertIn("Repositories: 2", result.stdout)

    def test_missing_registry_is_initialized_on_first_discovery(self):
        self.registry.rmdir()
        result = self.discover()
        self.assertTrue(self.registry.is_dir())
        generated = {
            "system-map.json", "capability-graph.json", "dependency-map.json",
            "architecture-map.json", "missing-capabilities.json",
            "registry-manifest.json",
        }
        self.assertEqual({p.name for p in self.registry.iterdir()}, generated)
        self.assertEqual(
            {repo["name"] for repo in self.read("system-map.json")},
            {"AIFT-OS", "AIFT-Runtime"},
        )
        self.assertEqual(self.read("architecture-map.json")["repositories"], 2)
        self.assertIn("Repositories: 2", result.stdout)

    def test_failed_atomic_publication_keeps_previous_json_intact(self):
        """A failed replacement must not truncate the last valid registry file."""
        self.discover()
        previous = (self.registry / "system-map.json").read_bytes()
        (self.aift / "AIFT-OS" / "package.json").write_text('{"name":"fixture"}')

        # sitecustomize runs only in the disposable child interpreter.
        # The old direct-write implementation never calls os.replace,
        # so this test fails against the old implementation.
        hooks = self.home / "hooks"
        hooks.mkdir()
        (hooks / "sitecustomize.py").write_text(
            "import os\n"
            "_replace = os.replace\n"
            "def reject_system_map(src, dst):\n"
            "    if os.fspath(dst).endswith('/system-map.json'):\n"
            "        raise OSError('injected atomic publication failure')\n"
            "    return _replace(src, dst)\n"
            "os.replace = reject_system_map\n"
        )
        env = dict(os.environ, HOME=str(self.home), PYTHONPATH=str(hooks))
        result = subprocess.run(
            [BASH, str(SCRIPT)], env=env, cwd=self.home,
            capture_output=True, text=True, timeout=15, check=False,
        )
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("injected atomic publication failure", result.stderr)
        self.assertEqual((self.registry / "system-map.json").read_bytes(), previous)
        self.assertFalse(
            list(self.registry.glob(".aetherion-*.tmp")),
            "Failed publication must clean up temporary files",
        )

    def test_all_outputs_use_atomic_replacement(self):
        """All registry products must publish via same-directory os.replace."""
        hooks = self.home / "hooks"
        hooks.mkdir()
        log_path = self.home / "replacements.txt"
        (hooks / "sitecustomize.py").write_text(
            "import os\n"
            "_replace = os.replace\n"
            "def log_replace(src, dst):\n"
            "    with open(os.environ['AIFT_REPLACE_LOG'], 'a') as log:\n"
            "        log.write(os.path.basename(os.fspath(dst)) + chr(10))\n"
            "    return _replace(src, dst)\n"
            "os.replace = log_replace\n"
        )
        env = dict(
            os.environ, HOME=str(self.home), PYTHONPATH=str(hooks),
            AIFT_REPLACE_LOG=str(log_path),
        )
        result = subprocess.run(
            [BASH, str(SCRIPT)], env=env, cwd=self.home,
            capture_output=True, text=True, timeout=15, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        expected = {
            "system-map.json", "capability-graph.json", "dependency-map.json",
            "architecture-map.json", "missing-capabilities.json",
            "registry-manifest.json",
        }
        self.assertEqual(set(log_path.read_text().splitlines()), expected)
        self.assertEqual(len(log_path.read_text().splitlines()), len(expected))
        self.assertEqual(log_path.read_text().splitlines()[-1], "registry-manifest.json")
        self.assertFalse(list(self.registry.glob(".aetherion-*.tmp")))


    def test_manifest_binds_exactly_five_registry_outputs(self):
        self.discover()
        manifest = self.read("registry-manifest.json")
        expected = {
            "system-map.json", "capability-graph.json", "dependency-map.json",
            "architecture-map.json", "missing-capabilities.json",
        }
        self.assertEqual(manifest["schema"], "aift.runtime.discovery-registry.v1")
        self.assertEqual(manifest["algorithm"], "sha256")
        self.assertEqual(set(manifest["files"]), expected)
        for filename, digest in manifest["files"].items():
            self.assertEqual(len(digest), 64)
            self.assertEqual(
                digest, hashlib.sha256((self.registry / filename).read_bytes()).hexdigest()
            )
        generation = hashlib.sha256(
            json.dumps(manifest["files"], sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        self.assertEqual(manifest["generation_id"], generation)
        before = (self.registry / "registry-manifest.json").read_bytes()
        self.discover()
        self.assertEqual((self.registry / "registry-manifest.json").read_bytes(), before)

    def test_interrupted_refresh_keeps_old_manifest_and_exposes_mismatch(self):
        self.discover()
        old_manifest = (self.registry / "registry-manifest.json").read_bytes()
        old_digests = self.read("registry-manifest.json")["files"]
        (self.aift / "AIFT-OS" / "package.json").write_text('{"name":"changed"}')

        hooks = self.home / "late-hooks"
        hooks.mkdir()
        (hooks / "sitecustomize.py").write_text(
            "import os\n"
            "_replace = os.replace\n"
            "def reject_architecture(src, dst):\n"
            "    if os.fspath(dst).endswith('/architecture-map.json'):\n"
            "        raise OSError('injected late registry failure')\n"
            "    return _replace(src, dst)\n"
            "os.replace = reject_architecture\n"
        )
        env = dict(os.environ, HOME=str(self.home), PYTHONPATH=str(hooks))
        result = subprocess.run(
            [BASH, str(SCRIPT)], env=env, cwd=self.home,
            capture_output=True, text=True, timeout=15, check=False,
        )
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("injected late registry failure", result.stderr)
        self.assertEqual((self.registry / "registry-manifest.json").read_bytes(), old_manifest)
        mismatches = [
            filename for filename, digest in old_digests.items()
            if hashlib.sha256((self.registry / filename).read_bytes()).hexdigest() != digest
        ]
        self.assertIn("system-map.json", mismatches)
        self.discover()
        repaired = self.read("registry-manifest.json")
        self.assertNotEqual(repaired["generation_id"], self.read_old_generation(old_manifest))
        for filename, digest in repaired["files"].items():
            self.assertEqual(
                hashlib.sha256((self.registry / filename).read_bytes()).hexdigest(), digest
            )

    @staticmethod
    def read_old_generation(raw):
        return json.loads(raw)["generation_id"]

    def test_repeated_discovery_does_not_inventory_generated_outputs(self):
        self.discover()
        first = self.read("system-map.json")
        self.discover()
        second = self.read("system-map.json")
        self.assertEqual(second, first)
        self.assertNotIn("registry", {repo["name"] for repo in second})


if __name__ == "__main__":
    unittest.main()
