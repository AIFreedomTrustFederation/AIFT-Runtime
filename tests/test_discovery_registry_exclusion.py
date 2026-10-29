"""Black-box checks that generated registry state is not counted as a repository."""

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
        }
        self.assertEqual({p.name for p in self.registry.iterdir()}, generated)
        self.assertEqual(
            {repo["name"] for repo in self.read("system-map.json")},
            {"AIFT-OS", "AIFT-Runtime"},
        )
        self.assertEqual(self.read("architecture-map.json")["repositories"], 2)
        self.assertIn("Repositories: 2", result.stdout)

    def test_repeated_discovery_does_not_inventory_generated_outputs(self):
        self.discover()
        first = self.read("system-map.json")
        self.discover()
        second = self.read("system-map.json")
        self.assertEqual(second, first)
        self.assertNotIn("registry", {repo["name"] for repo in second})


if __name__ == "__main__":
    unittest.main()
