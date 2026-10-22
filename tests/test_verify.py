import os
import shutil
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'runtime/verify.sh'
BASH = shutil.which('bash')

class VerifyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / 'home'
        common = self.home / 'AIFT/runtime/common.sh'
        common.parent.mkdir(parents=True)
        common.write_text('''#!/usr/bin/env bash
set -euo pipefail
AIFT_REPORTS="$HOME/AIFT/reports"
mkdir -p "$AIFT_REPORTS"
repo_paths() { printf '%s' "${MOCK_REPOS-}"; }
repo_name() { printf '%s\n' "${1##*/}"; }
''')
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.env = os.environ.copy()
        self.env.update(HOME=str(self.home), PATH=f'{self.bin}:' + self.env['PATH'])

    def command(self, name, content):
        path = self.bin / name
        path.write_text('#!/usr/bin/env bash\n' + content)
        path.chmod(0o755)

    def run_verify(self, repos):
        self.env['MOCK_REPOS'] = '\n'.join(str(r) for r in repos)
        return subprocess.run([BASH, '-c', f'source "{SCRIPT}" && aift_verify'], cwd=self.root,
                              env=self.env, text=True, capture_output=True)

    def report(self):
        return (self.home / 'AIFT/reports/verify-report.md').read_text()

    def test_failed_node_check_propagates_and_is_reported(self):
        repo = self.root / 'node project'
        repo.mkdir()
        (repo / 'package.json').write_text('{"scripts":{"lint":"exit 0","typecheck":"exit 0","test":"exit 0","build":"exit 0"}}')
        self.command('npm', '[[ "$2" == test ]] && exit 7\nexit 0\n')
        result = self.run_verify([repo])
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('- FAIL: npm run test', self.report())
        self.assertIn('Failed checks: 1', self.report())

    def test_successful_node_checks_pass(self):
        repo = self.root / 'node project'
        repo.mkdir()
        (repo / 'package.json').write_text('{"scripts":{"lint":"exit 0","typecheck":"exit 0","test":"exit 0","build":"exit 0"}}')
        self.command('npm', 'exit 0\n')
        result = self.run_verify([repo])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.report().count('- PASS: npm run'), 4)
        self.assertIn('Failed checks: 0', self.report())

    def test_empty_discovery_fails_closed(self):
        result = self.run_verify([])
        self.assertEqual(result.returncode, 1)
        self.assertIn('No repositories discovered', self.report())

    def test_failed_fallback_git_check_propagates(self):
        repo = self.root / 'plain repo'
        repo.mkdir()
        self.command('git', 'exit 4\n')
        result = self.run_verify([repo])
        self.assertEqual(result.returncode, 1)
        self.assertIn('- FAIL: git status --short', self.report())

    def test_missing_node_tool_is_not_reported_as_success(self):
        repo = self.root / 'node project'
        repo.mkdir()
        (repo / 'package.json').write_text('{"scripts":{"lint":"exit 0","typecheck":"exit 0","test":"exit 0","build":"exit 0"}}')
        for executable in ('date', 'mkdir'):
            (self.bin / executable).symlink_to(shutil.which(executable))
        self.env['PATH'] = str(self.bin)
        result = self.run_verify([repo])
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('- FAIL: npm unavailable', self.report())

    def test_multiple_repositories_continue_and_aggregate(self):
        first = self.root / 'first repo'
        second = self.root / 'second repo'
        for repo in (first, second):
            repo.mkdir()
            (repo / 'package.json').write_text('{"scripts":{"lint":"exit 0","typecheck":"exit 0","test":"exit 0","build":"exit 0"}}')
        self.command('npm', '[[ "$PWD" == *"first repo"* && "$2" == test ]] && exit 2\nexit 0\n')
        result = self.run_verify([first, second])
        self.assertEqual(result.returncode, 1)
        self.assertIn('## first repo', self.report())
        self.assertIn('## second repo', self.report())
        self.assertIn('Failed checks: 1', self.report())

    def test_node_project_without_verification_scripts_fails(self):
        repo = self.root / 'node project'
        repo.mkdir()
        (repo / 'package.json').write_text('{}')
        self.command('npm', 'exit 0\n')
        result = self.run_verify([repo])
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('FAIL: No lint, typecheck, test, or build script declared', self.report())
        self.assertNotIn('- PASS: npm run', self.report())

    def test_node_project_with_one_script_reports_three_skips(self):
        repo = self.root / 'node project'
        repo.mkdir()
        (repo / 'package.json').write_text('{"scripts":{"test":"echo ok"}}')
        self.command('npm', '[[ "$2" == test ]] || exit 12\nexit 0\n')
        result = self.run_verify([repo])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('- PASS: npm run test', self.report())
        self.assertEqual(self.report().count('- SKIP: npm run'), 3)

    def test_blank_script_is_not_verification_coverage(self):
        repo = self.root / 'node project'
        repo.mkdir()
        (repo / 'package.json').write_text('{"scripts":{"lint":"   "}}')
        self.command('npm', 'exit 0\n')
        result = self.run_verify([repo])
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('FAIL: No lint, typecheck, test, or build script declared', self.report())

if __name__ == '__main__':
    unittest.main(verbosity=2)
