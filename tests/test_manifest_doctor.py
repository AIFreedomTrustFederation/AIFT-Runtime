"""The federation's doctor command must execute diagnostics, not only define a function."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which('bash')


@unittest.skipUnless(BASH, 'bash is required')
class ManifestDoctorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / 'home'
        self.common = self.home / 'AIFT/runtime/common.sh'
        self.common.parent.mkdir(parents=True)
        self.common.write_text('''#!/usr/bin/env bash
AIFT_WORKSPACE="$HOME/AIFT"
repo_paths() { printf '%s\\n' "$HOME/AIFT/example-repo"; }
''')
        self.checkout = self.root / 'checkout'
        (self.checkout / 'runtime').mkdir(parents=True)
        shutil.copy2(ROOT / 'runtime/doctor.sh', self.checkout / 'runtime/doctor.sh')
        (self.checkout / 'runtime/doctor.sh').chmod(0o755)
        self.env = os.environ.copy()
        self.env['HOME'] = str(self.home)

    def run_manifest(self):
        command = json.loads((ROOT / 'aift.repo.json').read_text())['commands']['doctor']
        return subprocess.run([BASH, '-c', command], cwd=self.checkout,
                              env=self.env, text=True, capture_output=True)

    def test_doctor_command_runs_diagnostics(self):
        result = self.run_manifest()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('AIFT Runtime Doctor', result.stdout)
        self.assertIn('Repos: 1', result.stdout)
        self.assertIn('Workspace:', result.stdout)

    def test_missing_common_fails_closed(self):
        self.common.unlink()
        result = self.run_manifest()
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertNotIn('AIFT Runtime Doctor', result.stdout)

    def test_missing_doctor_script_fails(self):
        (self.checkout / 'runtime/doctor.sh').unlink()
        result = self.run_manifest()
        self.assertNotEqual(result.returncode, 0, result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
