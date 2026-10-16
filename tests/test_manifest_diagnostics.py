"""Ensure federation doctor/status entries execute diagnostics and fail closed."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which('bash')
GIT = shutil.which('git')


@unittest.skipUnless(BASH and GIT, 'bash and git are required')
class ManifestDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base / 'home'
        self.workspace = self.home / 'AIFT'
        (self.workspace / 'runtime').mkdir(parents=True)
        shutil.copy2(ROOT / 'runtime/common.sh', self.workspace / 'runtime/common.sh')
        self.repo = self.workspace / 'sample-repo'
        subprocess.run([GIT, 'init', '-q', str(self.repo)], check=True)
        subprocess.run([GIT, '-C', str(self.repo), '-c', 'user.name=Audit',
                        '-c', 'user.email=audit@example.invalid', 'commit',
                        '--allow-empty', '-qm', 'initial'], check=True)
        self.env = os.environ.copy()
        self.env['HOME'] = str(self.home)
        self.env.pop('AIFT_WORKSPACE', None)

    def invoke(self, name):
        command = json.loads((ROOT / 'aift.repo.json').read_text())['commands'][name]
        return subprocess.run([BASH, '-c', command], cwd=ROOT, env=self.env,
                              text=True, capture_output=True)

    def test_doctor_manifest_runs_actual_diagnostic(self):
        result = self.invoke('doctor')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('AIFT Runtime Doctor', result.stdout)
        self.assertIn('Repos: 1', result.stdout)

    def test_status_manifest_reports_repository(self):
        result = self.invoke('status')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('sample-repo', result.stdout)
        self.assertIn('Branch:', result.stdout)
        self.assertIn('Commit:', result.stdout)

    def test_doctor_fails_if_common_missing(self):
        (self.workspace / 'runtime/common.sh').unlink()
        result = self.invoke('doctor')
        self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_status_fails_if_common_missing(self):
        (self.workspace / 'runtime/common.sh').unlink()
        result = self.invoke('status')
        self.assertNotEqual(result.returncode, 0, result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
