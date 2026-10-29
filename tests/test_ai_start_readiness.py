"""Isolated startup diagnostics and generated-script consistency regressions."""

import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
START = ROOT / "runtime/ai/start.sh"
OPTIMIZER = ROOT / "runtime/ai/optimize_aetherion.sh"
PATH_FIX = ROOT / "fix-aetherion-paths.sh"
BASH = shutil.which("bash")


@unittest.skipUnless(BASH, "bash is required")
class AIStartReadinessTests(unittest.TestCase):
    def test_launch_does_not_claim_api_online_without_probe(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ai = root / "runtime/ai"
            ai.mkdir(parents=True)
            (ai / "models").mkdir()
            (ai / "logs").mkdir()
            (ai / "models/aetherion.gguf").write_text("test fixture")
            start = ai / "start.sh"
            start.write_bytes(START.read_bytes())
            bin_dir = root / "bin"
            bin_dir.mkdir()
            # The mock never launches a real llama-server or contacts a network endpoint.
            nohup = bin_dir / "nohup"
            nohup.write_text("#!/usr/bin/env bash\nexit 0\n")
            nohup.chmod(0o755)
            env = os.environ.copy()
            env.update(HOME=str(root), PATH=f"{bin_dir}:{env['PATH']}")
            result = subprocess.run([BASH, str(start)], env=env, cwd=root,
                                    capture_output=True, text=True, timeout=10,
                                    check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("Aetherion ONLINE", result.stdout)
            self.assertIn("Aetherion STARTING", result.stdout)
            self.assertIn("readiness not yet verified", result.stdout)
            self.assertTrue((ai / "aetherion.pid").is_file())

    def test_generators_match_canonical_start_script(self):
        canonical = START.read_text()
        for generator in (OPTIMIZER, PATH_FIX):
            with self.subTest(generator=generator.name):
                text = generator.read_text()
                match = re.search(r"(?m)^cat > [^\n]*<<'SCRIPT'\n(.*?)^SCRIPT$",
                                  text, flags=re.DOTALL | re.MULTILINE)
                self.assertIsNotNone(match, f"Missing generated start script in {generator}")
                self.assertEqual(match.group(1), canonical,
                                 f"Generated start.sh drifts from canonical: {generator}")


if __name__ == "__main__":
    unittest.main()
