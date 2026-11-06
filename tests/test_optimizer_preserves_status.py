"""Isolated optimizer regressions; never touch a live model or process."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "runtime/ai/optimize_aetherion.sh"
BASH = shutil.which("bash")


@unittest.skipUnless(BASH, "bash is required")
class OptimizerStatusPreservationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"
        self.ai = self.home / "AIFT/runtime/ai"
        self.ai.mkdir(parents=True)
        (self.ai / "models").mkdir()
        (self.ai / "logs").mkdir()
        (self.ai / "models/aetherion.gguf").write_text("test fixture")
        self.bin = self.root / "bin"
        self.bin.mkdir()
        # Never run the real process-discovery, process-killing or model-launch commands.
        for name, body in {
            "pgrep": "exit 1\n",
            "pkill": 'echo CALLED > "$MOCK_KILL_MARKER"\nexit 99\n',
            "nohup": "exit 0\n",
        }.items():
            stub = self.bin / name
            stub.write_text("#!/usr/bin/env bash\n" + body)
            stub.chmod(0o755)
        self.kill_marker = self.root / "kill-marker"
        self.optimizer = self.ai / "optimize_aetherion.sh"
        # Adapt only the Termux interpreter path for this isolated Linux test.
        source = SOURCE.read_text().replace(
            "#!/data/data/com.termux/files/usr/bin/bash", "#!/usr/bin/env bash"
        )
        self.optimizer.write_text(source)
        self.optimizer.chmod(0o755)

    def run_optimizer(self):
        env = os.environ.copy()
        env.update(HOME=str(self.home), PATH=f"{self.bin}:{env['PATH']}",
                   MOCK_KILL_MARKER=str(self.kill_marker))
        return subprocess.run([BASH, str(self.optimizer)], cwd=self.root,
                              env=env, capture_output=True, text=True, timeout=15,
                              check=False)

    def test_existing_status_is_preserved_byte_for_byte(self):
        status = self.ai / "status.sh"
        original = b"#!/usr/bin/env bash\n# canonical HTTP health probe\nexit 0\n"
        status.write_bytes(original)
        status.chmod(0o755)
        result = self.run_optimizer()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(status.read_bytes(), original)
        self.assertEqual(status.stat().st_mode & 0o777, 0o755)
        self.assertFalse(self.kill_marker.exists())

    def test_missing_status_fails_before_mutation(self):
        start = self.ai / "start.sh"
        start.write_text("original start\n")
        result = self.run_optimizer()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing status script", result.stderr)
        self.assertEqual(start.read_text(), "original start\n")
        self.assertFalse((self.ai / "stop.sh").exists())
        self.assertFalse((self.ai / "status.sh").exists())
        self.assertFalse(self.kill_marker.exists())


if __name__ == "__main__":
    unittest.main()
