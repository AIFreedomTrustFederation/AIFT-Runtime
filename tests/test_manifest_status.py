"""Contract tests for the manifest status command and whitespace-safe status output."""
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


@unittest.skipUnless(BASH and GIT, 'bash and git required')
class ManifestStatusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / 'home'
        self.workspace = self.home / 'AIFT'
        (self.workspace / 'runtime').mkdir(parents=True)
        shutil.copy2(ROOT / 'runtime/common.sh', self.workspace / 'runtime/common.sh')
        self.checkout = self.root / 'checkout'
        (self.checkout / 'runtime').mkdir(parents=True)
        shutil.copy2(ROOT / 'runtime/status.sh', self.checkout / 'runtime/status.sh')
        (self.checkout / 'runtime/status.sh').chmod(0o755)
        self.env = os.environ.copy()
        self.env.update(HOME=str(self.home), AIFT_WORKSPACE=str(self.workspace))

    def git(self, path, *args):
        return subprocess.run([GIT, '-C', str(path), *args], check=True,
                              capture_output=True, text=True)

    def add_repo(self, name='sample repo'):
        repo = self.workspace / name
        repo.mkdir()
        self.git(repo, 'init', '-q')
        self.git(repo, 'config', 'user.name', 'Test')
        self.git(repo, 'config', 'user.email', 'test@example.invalid')
        (repo / 'README.md').write_text('test\n')
        self.git(repo, 'add', 'README.md')
        self.git(repo, 'commit', '-qm', 'fixture')
        (repo / 'scratch.txt').write_text('untracked\n')
        return repo

    def run_manifest(self):
        command = json.loads((ROOT / 'aift.repo.json').read_text())['commands']['status']
        return subprocess.run([BASH, '-c', command], cwd=self.checkout, env=self.env,
                              capture_output=True, text=True)

    def test_manifest_actually_reports_repository_state(self):
        self.add_repo('project')
        result = self.run_manifest()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('project', result.stdout)
        self.assertIn('Changed files: 1', result.stdout)
        self.assertIn('?? scratch.txt', result.stdout)

    def test_manifest_rejects_missing_workspace_helper(self):
        self.add_repo('project')
        (self.workspace / 'runtime/common.sh').unlink()
        result = self.run_manifest()
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertNotIn('Changed files:', result.stdout)

    def test_repository_path_with_spaces_is_not_split(self):
        self.add_repo('two word project')
        result = self.run_manifest()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count('Changed files:'), 1, result.stdout)
        self.assertIn('two word project', result.stdout)
        self.assertIn('?? scratch.txt', result.stdout)

    def test_sourced_status_preserves_callers_working_directory(self):
        self.add_repo('project')
        result = subprocess.run([BASH, '-c',
                                 'source ./runtime/status.sh && aift_status && printf "PWD_AFTER=%s\\n" "$PWD"'],
                                cwd=self.checkout, env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('PWD_AFTER=' + str(self.checkout), result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
