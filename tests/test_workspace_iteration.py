"""Regression: workspace commands must not split discovered repository paths."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which('bash')


@unittest.skipUnless(BASH, 'bash is required')
class WorkspaceIterationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / 'home'
        runtime = self.home / 'AIFT' / 'runtime'
        runtime.mkdir(parents=True)
        self.reports = self.home / 'AIFT' / 'reports'
        self.reports.mkdir()
        self.repositories = [self.root / 'ordinary',
                             self.root / 'repo with spaces',
                             self.root / 'repo [brackets]']
        for repo in self.repositories:
            repo.mkdir()
        (runtime / 'common.sh').write_text('''#!/usr/bin/env bash
set -euo pipefail
AIFT_REPORTS="$HOME/AIFT/reports"
repo_paths() { printf '%s\\n' "$MOCK_REPO_ONE" "$MOCK_REPO_TWO" "$MOCK_REPO_THREE"; }
repo_name() { basename "$1"; }
git_branch() { printf '%s\\n' main; }
git_commit() { printf '%s\\n' abc123; }
git_changed_count() { printf '%s\\n' 0; }
# No actual Git operation may occur in this test. A missing remote forces
# pull and push to skip before fetch, checkout, commit, or network activity.
git() {
  case "$*" in
    config\\ --global\\ --add\\ *) return 0 ;;
    'remote get-url origin') return 1 ;;
    'status --short') return 0 ;;
    *) printf 'unexpected git command: %s\\n' "$*" >&2; return 99 ;;
  esac
}
''')
        self.env = os.environ.copy()
        self.env.update(HOME=str(self.home),
                        MOCK_REPO_ONE=str(self.repositories[0]),
                        MOCK_REPO_TWO=str(self.repositories[1]),
                        MOCK_REPO_THREE=str(self.repositories[2]))

    def run_command(self, name):
        return subprocess.run([BASH, '-c',
                               f'source "{ROOT / "runtime" / (name + ".sh")}" && aift_{name}'],
                              cwd=self.root, env=self.env, text=True,
                              capture_output=True)

    def test_status_reports_each_repository_with_original_name(self):
        result = self.run_command('status')
        self.assertEqual(result.returncode, 0, result.stderr)
        for repo in self.repositories:
            self.assertIn(repo.name, result.stdout)
            self.assertIn('Branch: main', result.stdout)
        self.assertEqual(result.stdout.count('Changed files: 0'), 3)

    def test_pull_skips_each_repository_without_remote(self):
        result = self.run_command('pull')
        self.assertEqual(result.returncode, 0, result.stderr)
        report = (self.reports / 'pull-report.md').read_text()
        for repo in self.repositories:
            self.assertIn(f'- {repo.name}: no origin remote', report)
        self.assertEqual(report.count('no origin remote'), 3)

    def test_push_skips_each_repository_without_remote(self):
        result = self.run_command('push')
        self.assertEqual(result.returncode, 0, result.stderr)
        report = (self.reports / 'push-report.md').read_text()
        for repo in self.repositories:
            self.assertIn(f'- {repo.name}: no origin remote', report)
        self.assertEqual(report.count('no origin remote'), 3)


if __name__ == '__main__':
    unittest.main(verbosity=2)
