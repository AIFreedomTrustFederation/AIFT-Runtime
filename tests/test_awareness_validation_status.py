"""Isolated black-box regressions for awareness validation exit status and HTTP errors."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "validate-aetherion-awareness.sh"
BASH = shutil.which("bash")


@unittest.skipUnless(BASH, "bash required")
class AwarenessValidationStatusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.repo = self.home / "AIFT/AIFT-Runtime"
        core = self.repo / "runtime/core"
        intelligence = self.repo / "runtime/intelligence"
        core.mkdir(parents=True)
        intelligence.mkdir(parents=True)
        (core / "aetherion-discover").write_text('#!/usr/bin/env bash\nprintf "Repositories: 1\\n"\ntouch "$HOME/discovery-ran"\n')
        (core / "aetherion-agent-router.sh").write_text("# fixture\n")
        (intelligence / "discover-agents.py").write_text("# fixture\n")
        (intelligence / "resolve-task-agent.py").write_text("# fixture\n")
        (self.repo / "repo-intelligence.json").write_text("{}\n")
        (self.home / "AIFT/capabilities.json").write_text("{}\n")
        self.bin = self.root / "bin"
        self.bin.mkdir()
        fake_curl = self.bin / "curl"
        fake_curl.write_text(
            '#!/usr/bin/env bash\n'
            'if [[ "$MOCK_HTTP_STATUS" == 500 ]]; then\n'
            '  for arg in "$@"; do\n'
            '    [[ "$arg" == --fail || "$arg" == -f ]] && exit 22\n'
            '  done\n'
            'fi\n'
            'echo \'{"object":"list","data":[{"id":"aetherion.gguf"}]}\'\n'
        )
        fake_curl.chmod(0o755)

    def run_validator(self, http_status=200):
        env = dict(os.environ, HOME=str(self.home),
                   PATH=f"{self.bin}:{os.environ['PATH']}",
                   MOCK_HTTP_STATUS=str(http_status))
        return subprocess.run([BASH, str(SCRIPT)], env=env, cwd=self.root,
                              capture_output=True, text=True, timeout=10, check=False)

    def test_healthy_fixtures_remain_successful(self):
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("FAILED: 0", result.stdout)
        self.assertTrue((self.home / "discovery-ran").is_file(), result.stdout)
        self.assertIn("AETHERION AWARENESS LAYER OPERATIONAL", result.stdout)

    def test_discovery_nonzero_with_repositories_marker_is_failure(self):
        (self.repo / "runtime/core/aetherion-discover").write_text(
            '#!/usr/bin/env bash\nprintf "Repositories: 1\\n"\nexit 9\n'
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("✗ Discovery execution failed", result.stdout)
        self.assertNotIn("AETHERION AWARENESS LAYER OPERATIONAL", result.stdout)

    def test_discovery_zero_without_repositories_marker_is_failure(self):
        (self.repo / "runtime/core/aetherion-discover").write_text(
            '#!/usr/bin/env bash\nprintf "Discovery Complete\\n"\n'
        )
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("✗ Discovery execution failed", result.stdout)

    def test_missing_architecture_file_is_nonzero(self):
        (self.repo / "runtime/core/aetherion-agent-router.sh").unlink()
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("✗ Agent router", result.stdout)
        self.assertNotIn("AETHERION AWARENESS LAYER OPERATIONAL", result.stdout)

    def test_http_500_is_not_reported_as_operational(self):
        result = self.run_validator(http_status=500)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("✗ Aetherion API", result.stdout)
        self.assertNotIn("AETHERION AWARENESS LAYER OPERATIONAL", result.stdout)


if __name__ == "__main__":
    unittest.main()
