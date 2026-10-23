"""Regression: governed pushes must never publish unrelated staged files."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GIT = shutil.which('git')
BASH = shutil.which('bash')


@unittest.skipUnless(GIT and BASH, 'git and bash are required')
class PushScopeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / 'home'
        runtime = self.home / 'AIFT' / 'runtime'
        runtime.mkdir(parents=True)
        self.workspace = self.root / 'workspace'
        self.workspace.mkdir()
        self.repo = self.workspace / 'repository with spaces'
        self.remote = self.root / 'remote.git'
        self.git('init', '--bare', '-q', '--initial-branch=main', str(self.remote), cwd=self.root)
        self.git('init', '-q', '--initial-branch=main', str(self.repo), cwd=self.root)
        self.git('config', 'user.name', 'Test Operator')
        self.git('config', 'user.email', 'operator@example.invalid')
        (self.repo / 'aift.repo.json').write_text('{"version":1}\n')
        (self.repo / 'private-notes.txt').write_text('original private notes\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'initial')
        self.git('remote', 'add', 'origin', str(self.remote))
        self.git('push', '-q', '-u', 'origin', 'main')
        (runtime / 'common.sh').write_text('''#!/usr/bin/env bash
set -euo pipefail
AIFT_REPORTS="$HOME/AIFT/reports"
mkdir -p "$AIFT_REPORTS"
repo_paths() { printf '%s\\n' "$MOCK_REPO"; }
repo_name() { basename "$1"; }
''')
        self.env = os.environ.copy()
        self.env.update(HOME=str(self.home), MOCK_REPO=str(self.repo))

    def git(self, *args, cwd=None):
        return subprocess.run([GIT, *args], cwd=cwd or self.repo,
                              text=True, capture_output=True, check=True).stdout

    def invoke(self):
        return subprocess.run([BASH, '-c',
            f'source "{ROOT / "runtime" / "push.sh"}" && aift_push'],
            cwd=self.root, env=self.env, text=True, capture_output=True)

    def remote_files(self):
        return self.git('--git-dir', str(self.remote), 'show', '--format=',
                        '--name-only', 'main').splitlines()

    def test_unrelated_staged_file_alone_must_not_be_committed(self):
        (self.repo / 'private-notes.txt').write_text('secret not approved for publication\n')
        self.git('add', 'private-notes.txt')
        original = self.git('rev-parse', 'HEAD').strip()
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), original,
                         'unrelated staged file was committed')
        self.assertEqual(self.git('rev-parse', 'refs/remotes/origin/main').strip(), original)
        self.assertIn('private-notes.txt', self.git('diff', '--cached', '--name-only'))

    def test_allowed_change_commits_without_unrelated_staged_file(self):
        (self.repo / 'aift.repo.json').write_text('{"version":2}\n')
        (self.repo / 'private-notes.txt').write_text('secret not approved for publication\n')
        self.git('add', 'private-notes.txt')
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.remote_files(), ['aift.repo.json'])
        self.assertEqual(self.git('show', 'main:private-notes.txt'), 'original private notes\n')
        self.assertIn('private-notes.txt', self.git('diff', '--cached', '--name-only'))
        self.assertIn('pushed to main', (self.home / 'AIFT' / 'reports' / 'push-report.md').read_text())

    def test_new_file_in_managed_directory_is_published(self):
        managed = self.repo / 'runtime'
        managed.mkdir()
        (managed / 'new-file.txt').write_text('approved runtime metadata\n')
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.remote_files(), ['runtime/new-file.txt'])

    def test_deleted_managed_file_is_published(self):
        (self.repo / 'aift.repo.json').unlink()
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.remote_files(), ['aift.repo.json'])
        self.assertNotIn('aift.repo.json', self.git('--git-dir', str(self.remote), 'ls-tree', '-r', '--name-only', 'main'))

    def test_staged_managed_change_reverted_in_worktree_is_not_committed(self):
        (self.repo / 'aift.repo.json').write_text('{"version":2}\n')
        self.git('add', 'aift.repo.json')
        (self.repo / 'aift.repo.json').write_text('{"version":1}\n')
        original = self.git('rev-parse', 'HEAD').strip()
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), original)


if __name__ == '__main__':
    unittest.main()
