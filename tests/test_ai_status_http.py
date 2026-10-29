"""Offline regressions for the Aetherion HTTP status probe."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "runtime/ai/status.sh"
BASH = shutil.which("bash")


class AIStatusHTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        fake_curl = self.bin / "curl"
        fake_curl.write_text(
            "#!/usr/bin/env bash\n"
            "case \"$MOCK_HTTP_STATUS\" in\n"
            "  500)\n"
            "    for arg in \"$@\"; do\n"
            "      if [[ \"$arg\" == --fail || \"$arg\" == -f || \"$arg\" == -*f* ]]; then exit 22; fi\n"
            "    done\n"
            "    exit 0 ;;\n"
            "  200) exit 0 ;;\n"
            "  *) exit 7 ;;\n"
            "esac\n"
        )
        fake_curl.chmod(0o755)

    def status(self, code):
        env = os.environ.copy()
        env.update(HOME=str(self.home), PATH=f"{self.bin}:{env['PATH']}",
                   MOCK_HTTP_STATUS=str(code))
        return subprocess.run([BASH, str(SCRIPT)], cwd=self.root, env=env,
                              capture_output=True, text=True, check=False)

    def test_http_500_does_not_claim_online(self):
        result = self.status(500)
        self.assertNotIn("ONLINE", result.stdout)
        self.assertIn("Aetherion OFFLINE", result.stdout)

    def test_http_200_retains_online_probe(self):
        result = self.status(200)
        self.assertIn("Aetherion ONLINE", result.stdout)
        self.assertIn("API responding on port 8080", result.stdout)


if __name__ == "__main__":
    unittest.main()
