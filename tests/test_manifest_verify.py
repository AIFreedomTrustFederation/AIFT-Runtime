"""Contract tests: the federation manifest's verify command must actually verify."""
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
class ManifestVerifyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / 'home'
        self.common = self.home / 'AIFT/runtime/common.sh'
        self.common.parent.mkdir(parents=True)
        self.common.write_text('''#!/usr/bin/env bash
set -euo pipefail
AIFT_REPORTS="$HOME/AIFT/reports"
mkdir -p "$AIFT_REPORTS"
repo_paths() { printf '%s' "$MOCK_REPOS"; }
repo_name() { basename "$1"; }
''')
        self.checkout = self.root / 'checkout'
        (self.checkout / 'runtime').mkdir(parents=True)
        shutil.copy2(ROOT / 'runtime/verify.sh', self.checkout / 'runtime/verify.sh')
        (self.checkout / 'runtime/verify.sh').chmod(0o755)
        self.env = os.environ.copy()
        self.env['HOME'] = str(self.home)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.env['PATH'] = str(self.bin) + ':' + self.env['PATH']

    def run_manifest(self, repos):
        self.env['MOCK_REPOS'] = '\n'.join(map(str, repos))
        command = json.loads((ROOT / 'aift.repo.json').read_text())['commands']['verify']
        return subprocess.run([BASH, '-c', command], cwd=self.checkout, env=self.env,
                              text=True, capture_output=True)

    def report_path(self):
        return self.home / 'AIFT/reports/verify-report.md'

    def test_manifest_invocation_performs_checks_and_writes_report(self):
        repo = self.root / 'node project'
        repo.mkdir()
        (repo / 'package.json').write_text('{}')
        npm = self.bin / 'npm'
        npm.write_text('#!/usr/bin/env bash\nexit 0\n')
        npm.chmod(0o755)
        result = self.run_manifest([repo])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Failed checks: 0', self.report_path().read_text())
        self.assertEqual(self.report_path().read_text().count('- PASS: npm run'), 4)

    def test_manifest_invocation_propagates_failed_project_check(self):
        repo = self.root / 'broken node project'
        repo.mkdir()
        (repo / 'package.json').write_text('{}')
        npm = self.bin / 'npm'
        npm.write_text('#!/usr/bin/env bash\nexit 7\n')
        npm.chmod(0o755)
        result = self.run_manifest([repo])
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn('- FAIL: npm run lint --if-present', self.report_path().read_text())

    def test_manifest_invocation_propagates_failed_discovery(self):
        result = self.run_manifest([])
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn('No repositories discovered', self.report_path().read_text())

    def test_manifest_invocation_fails_when_workspace_common_missing(self):
        self.common.unlink()
        result = self.run_manifest([])
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse(self.report_path().exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
