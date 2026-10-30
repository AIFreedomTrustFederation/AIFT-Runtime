"""The standalone installer must not revert maintained discovery-engine fixes."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "runtime/core/aetherion-discover"
INSTALLER = ROOT / "runtime/core/install-aetherion-discovery-v1.sh"
BASH = shutil.which("bash")
PYTHON = shutil.which("python")


@unittest.skipUnless(BASH and PYTHON, "bash and python are required")
class DiscoveryInstallerConsistencyTests(unittest.TestCase):
    def test_embedded_engine_is_byte_identical_to_canonical_source(self):
        installer = INSTALLER.read_text(encoding="utf-8")
        delimiter = "cat > \"$CORE/aetherion-discover\" <<'DISCOVER'\n"
        self.assertIn(delimiter, installer)
        body = installer.split(delimiter, 1)[1].split("\nDISCOVER\n", 1)[0] + "\n"
        self.assertEqual(body.encode(), CANONICAL.read_bytes())

    def test_install_and_run_preserves_registry_exclusion_and_atomic_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            workspace = home / "AIFT"
            (workspace / "runtime/core").mkdir(parents=True)
            (workspace / "AIFT-OS").mkdir()
            (workspace / "AIFT-OS/go.mod").write_text("module example.invalid/aift-os\n")
            (workspace / "AIFT-Runtime").mkdir()
            (workspace / "AIFT-Runtime/README.md").write_text("# Runtime fixture\n")
            env = dict(os.environ, HOME=str(home))
            installed = workspace / "runtime/core/aetherion-discover"
            for _ in range(2):
                install = subprocess.run(
                    [BASH, str(INSTALLER)], env=env, cwd=home,
                    capture_output=True, text=True, timeout=15, check=False,
                )
                self.assertEqual(install.returncode, 0, install.stdout + install.stderr)
                self.assertEqual(installed.read_bytes(), CANONICAL.read_bytes())
                discovery = subprocess.run(
                    [BASH, str(installed)], env=env, cwd=home,
                    capture_output=True, text=True, timeout=15, check=False,
                )
                self.assertEqual(discovery.returncode, 0, discovery.stdout + discovery.stderr)
                # The installer creates AIFT/runtime/core; the heuristic scanner
                # currently counts that top-level directory too.
                self.assertIn("Repositories: 3", discovery.stdout)
                registry = workspace / "registry"
                system = json.loads((registry / "system-map.json").read_text())
                self.assertEqual({item["name"] for item in system}, {"AIFT-OS", "AIFT-Runtime", "runtime"})
                self.assertEqual(
                    json.loads((registry / "architecture-map.json").read_text())["repositories"], 3
                )
                self.assertFalse(list(registry.glob(".aetherion-*.tmp")))
                manifest = json.loads((registry / "registry-manifest.json").read_text())
                self.assertEqual(len(manifest["files"]), 5)
                for filename, digest in manifest["files"].items():
                    self.assertEqual(hashlib.sha256((registry / filename).read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
