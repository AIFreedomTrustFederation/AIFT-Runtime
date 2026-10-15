"""Regression tests for AIFT workspace repository discovery."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

COMMON = Path(__file__).resolve().parents[1] / 'runtime' / 'common.sh'
GIT = shutil.which('git')
BASH = shutil.which('bash')


@unittest.skipUnless(GIT and BASH, 'git and bash are required')
class RepoPathsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / 'AIFT workspace'
        self.workspace.mkdir()
        self.primary = self.workspace / 'main repo'
        subprocess.run([GIT, 'init', '-q', str(self.primary)], check=True)
        subprocess.run([GIT, '-C', str(self.primary), '-c', 'user.name=Test',
                        '-c', 'user.email=test@example.invalid', 'commit',
                        '--allow-empty', '-qm', 'initial'], check=True)

    def discover(self):
        env = os.environ.copy()
        env['AIFT_WORKSPACE'] = str(self.workspace)
        result = subprocess.run([BASH, '-c', f'source "{COMMON}" && repo_paths'],
                                env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return set(result.stdout.splitlines())

    def test_regular_repository_is_discovered(self):
        self.assertIn(str(self.primary), self.discover())

    def test_linked_worktree_is_discovered(self):
        linked = self.workspace / 'linked worktree'
        subprocess.run([GIT, '-C', str(self.primary), 'worktree', 'add', '-q',
                        '--detach', str(linked)], check=True)
        self.assertTrue((linked / '.git').is_file())
        self.assertIn(str(linked), self.discover())

    def test_invalid_git_marker_is_not_discovered(self):
        fake = self.workspace / 'fake repo'
        fake.mkdir()
        (fake / '.git').write_text('gitdir: /nonexistent/aift-worktree\n')
        self.assertNotIn(str(fake), self.discover())


if __name__ == '__main__':
    unittest.main(verbosity=2)
