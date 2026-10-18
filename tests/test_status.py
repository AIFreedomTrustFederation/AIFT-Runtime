"""Regression tests for local AIFT repository status reporting."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'runtime' / 'status.sh'
COMMON = Path(__file__).resolve().parents[1] / 'runtime' / 'common.sh'
GIT = shutil.which('git')
BASH = shutil.which('bash')


@unittest.skipUnless(GIT and BASH, 'git and bash are required')
class StatusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / 'home'
        common = self.home / 'AIFT/runtime/common.sh'
        common.parent.mkdir(parents=True)
        shutil.copyfile(COMMON, common)
        self.workspace = self.root / 'AIFT_workspace'
        self.workspace.mkdir()
        self.start_dir = self.root / 'invocation directory'
        self.start_dir.mkdir()

    def make_repo(self, name):
        repo = self.workspace / name
        subprocess.run([GIT, 'init', '-q', str(repo)], check=True)
        subprocess.run([GIT, '-C', str(repo), '-c', 'user.name=AIFT Test',
                        '-c', 'user.email=test@example.invalid', 'commit',
                        '--allow-empty', '-qm', 'initial'], check=True)
        (repo / 'change.txt').write_text(name)
        return repo

    def run_status(self):
        env = os.environ.copy()
        env.update(HOME=str(self.home), AIFT_WORKSPACE=str(self.workspace))
        return subprocess.run(
            [BASH, '-c', f'source "{SCRIPT}" && aift_status && printf "\\nFINAL_PWD=%s\\n" "$PWD"'],
            cwd=self.start_dir, env=env, capture_output=True, text=True)

    def test_status_reports_each_repository_with_spaces(self):
        self.make_repo('first repo')
        self.make_repo('second repo')
        result = self.run_status()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('\nfirst repo\n', result.stdout)
        self.assertIn('\nsecond repo\n', result.stdout)
        self.assertEqual(result.stdout.count('Changed files: 1'), 2)
        self.assertEqual(result.stdout.count('?? change.txt'), 2)

    def test_status_supports_workspace_path_with_spaces(self):
        self.workspace = self.root / 'AIFT workspace with spaces'
        self.workspace.mkdir()
        self.make_repo('nested repo')
        result = self.run_status()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('\nnested repo\n', result.stdout)
        self.assertIn('Changed files: 1', result.stdout)

    def test_status_supports_linked_worktree(self):
        repo = self.make_repo('mainrepo')
        linked = self.workspace / 'linked worktree'
        subprocess.run([GIT, '-C', str(repo), 'worktree', 'add', '-q',
                        '--detach', str(linked)], check=True)
        (linked / 'linked.txt').write_text('changed')
        result = self.run_status()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('\nlinked worktree\n', result.stdout)
        self.assertEqual(result.stdout.count('Changed files: 1'), 2)

    def test_status_does_not_change_callers_directory(self):
        self.make_repo('plainrepo')
        result = self.run_status()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f'FINAL_PWD={self.start_dir}\n', result.stdout)

    def test_status_reports_plain_repository(self):
        self.make_repo('plainrepo')
        result = self.run_status()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('\nplainrepo\n', result.stdout)
        self.assertIn('Changed files: 1', result.stdout)
        self.assertIn('?? change.txt', result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
