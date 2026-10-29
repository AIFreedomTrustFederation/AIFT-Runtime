"""Isolated regressions for Aetherion configuration HTTP error handling."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "verify-aetherion-runtime.sh"
BASH = shutil.which("bash")
GIT = shutil.which("git")


@unittest.skipUnless(BASH and GIT, "bash and git are required")
class VerifyAetherionHTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.home = self.root / "home"
        self.home.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()

        ai = self.repo / "runtime/ai"
        (ai / "models").mkdir(parents=True)
        (ai / "logs").mkdir()
        with (ai / "models/aetherion.gguf").open("wb") as model:
            model.truncate(1_000_000_001)  # Sparse fixture; no real model bytes.
        (self.repo / ".gitignore").write_text("runtime/ai/models/\n")
        (ai / "start.sh").write_text('#!/usr/bin/env bash\nAI_HOME="$(dirname "$0")"\n')
        (ai / "start.sh").chmod(0o755)
        (ai / "optimize_aetherion.sh").write_text("#!/usr/bin/env bash\n")
        (self.repo / SOURCE.name).write_bytes(SOURCE.read_bytes())
        llama = self.home / "Aetherion/llama.cpp/build/bin/llama-server"
        llama.parent.mkdir(parents=True)
        llama.write_text("#!/bin/sh\nexit 0\n")
        llama.chmod(0o755)

        fake_lfs = self.bin / "git-lfs"
        fake_lfs.write_text('#!/bin/sh\n[ "$1" = ls-files ] && echo "oid aetherion.gguf"\n')
        fake_lfs.chmod(0o755)
        fake_curl = self.bin / "curl"
        fake_curl.write_text(
            '#!/usr/bin/env bash\n'
            'is_models=0\nfail=0\n'
            'for arg in "$@"; do\n'
            '  [[ "$arg" == *"/v1/models"* ]] && is_models=1\n'
            '  [[ "$arg" == --fail || "$arg" == -f || "$arg" == -*f* ]] && fail=1\n'
            'done\n'
            'code="$MOCK_ROOT_STATUS"\n'
            '(( is_models )) && code="$MOCK_MODELS_STATUS"\n'
            'if [[ "$code" == 500 ]]; then\n'
            '  if (( fail )); then exit 22; fi\n'
            '  echo \'{"error":"models unavailable"}\'\n'
            '  exit 0\n'
            'fi\n'
            'if (( is_models )); then echo \'{"object":"list","models":[],"data":[]}\' ; else echo ok; fi\n'
        )
        fake_curl.chmod(0o755)
        self.env = os.environ.copy()
        self.env.update(HOME=str(self.home), PATH=f"{self.bin}:{self.env['PATH']}")
        subprocess.run([GIT, "init", "-q", str(self.repo)], check=True)
        subprocess.run([GIT, "-C", str(self.repo), "remote", "add", "origin", "https://example.invalid/repo.git"], check=True)
        subprocess.run([GIT, "-C", str(self.repo), "add", "."], check=True)
        subprocess.run([GIT, "-C", str(self.repo), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture"], check=True)

    def verify(self, models=200, root=200):
        env = dict(self.env, MOCK_MODELS_STATUS=str(models), MOCK_ROOT_STATUS=str(root))
        return subprocess.run([BASH, str(self.repo / SOURCE.name)], cwd=self.repo, env=env,
                              capture_output=True, text=True, timeout=10, check=False)

    def test_http_500_models_error_cannot_pass_configuration(self):
        result = self.verify(models=500)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("✗ Aetherion API online", result.stdout)
        self.assertNotIn("✓ AETHERION RUNTIME FULLY CONFIGURED", result.stdout)

    def test_http_500_root_error_cannot_pass_configuration(self):
        result = self.verify(root=500)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("✗ API responding", result.stdout)

    def test_http_200_preserves_success(self):
        result = self.verify()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("✓ AETHERION RUNTIME FULLY CONFIGURED", result.stdout)
        self.assertIn("FAILED: 0", result.stdout)


if __name__ == "__main__":
    unittest.main()
