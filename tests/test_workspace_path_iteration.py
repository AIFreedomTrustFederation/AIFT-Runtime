"""Workspace commands must handle Git repository paths containing spaces."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'runtime'
BASH = shutil.which('bash')
GIT = shutil.which('git')


@unittest.skipUnless(BASH and GIT, 'Bash and Git are required')
class WorkspacePathIterationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / 'test home'
        common = self.home / 'AIFT/runtime/common.sh'
        common.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / 'runtime/common.sh', common)
        self.workspace = self.root / 'AIFT workspace'
        self.workspace.mkdir()
        self.env = dict(os.environ, HOME=str(self.home), AIFT_WORKSPACE=str(self.workspace),
                        GIT_CONFIG_NOSYSTEM='1', GIT_TERMINAL_PROMPT='0')

    def make_repo(self, name):
        repo = self.workspace / name
        subprocess.run([GIT, 'init', '-q', str(repo)], check=True, env=self.env)
        subprocess.run([GIT, '-C', str(repo), '-c', 'user.name=AIFT Test',
                        '-c', 'user.email=aift@example.invalid', 'commit',
                        '--allow-empty', '-qm', 'fixture'], check=True, env=self.env)
        return repo

    def invoke(self, script, function):
        return subprocess.run([BASH, '-c', f'source "{SCRIPTS / script}" && {function}'],
                              cwd=self.root, env=self.env, capture_output=True, text=True)

    def test_status_displays_repository_with_spaces(self):
        self.make_repo('repo with spaces')
        result = self.invoke('status.sh', 'aift_status')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('repo with spaces', result.stdout)
        self.assertIn('Branch:', result.stdout)
        self.assertNotIn('No such file or directory', result.stderr)

    def test_pull_reports_spaced_repository_without_origin(self):
        self.make_repo('repo with spaces')
        result = self.invoke('pull.sh', 'aift_pull')
        self.assertEqual(result.returncode, 0, result.stderr)
        report = (self.workspace / 'reports/pull-report.md').read_text()
        self.assertIn('- repo with spaces: no origin remote', report)
        self.assertEqual(report.count('no origin remote'), 1)

    def test_push_reports_spaced_repository_without_origin(self):
        self.make_repo('repo with spaces')
        result = self.invoke('push.sh', 'aift_push')
        self.assertEqual(result.returncode, 0, result.stderr)
        report = (self.workspace / 'reports/push-report.md').read_text()
        self.assertIn('- repo with spaces: no origin remote', report)
        self.assertEqual(report.count('no origin remote'), 1)

    def test_mixed_repository_names_are_processed_once(self):
        self.make_repo('plainrepo')
        self.make_repo('repo with spaces')
        for script, function, report_name in (
            ('pull.sh', 'aift_pull', 'pull-report.md'),
            ('push.sh', 'aift_push', 'push-report.md'),
        ):
            with self.subTest(command=function):
                result = self.invoke(script, function)
                self.assertEqual(result.returncode, 0, result.stderr)
                report = (self.workspace / 'reports' / report_name).read_text()
                self.assertEqual(report.count('- plainrepo: no origin remote'), 1)
                self.assertEqual(report.count('- repo with spaces: no origin remote'), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
