"""Local Git regression tests for safe federation pull behavior."""
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
class PullSafetyTests(unittest.TestCase):
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
        self.env.update(HOME=str(self.home), MOCK_REPO=str(self.repo), GIT_CONFIG_GLOBAL=os.devnull)

    def git(self, *args, cwd=None):
        return subprocess.run([GIT, *args], cwd=cwd or self.repo,
                              text=True, capture_output=True, check=True).stdout

    def invoke(self):
        return subprocess.run([BASH, '-c',
            f'source "{ROOT / "runtime" / "pull.sh"}" && aift_pull'],
            cwd=self.root, env=self.env, text=True, capture_output=True)

    def report(self):
        return (self.home / 'AIFT' / 'reports' / 'pull-report.md').read_text()

    def test_feature_branch_with_local_edits_is_never_switched(self):
        self.git('checkout', '-qb', 'feature/unfinished')
        (self.repo / 'aift.repo.json').write_text('{"version":99}\n')
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git('branch', '--show-current').strip(), 'feature/unfinished')
        self.assertEqual((self.repo / 'aift.repo.json').read_text(), '{"version":99}\n')
        self.assertIn('skipped', self.report())

    def test_clean_feature_branch_is_never_switched(self):
        self.git('checkout', '-qb', 'feature/committed')
        (self.repo / 'feature.txt').write_text('work in progress\n')
        self.git('add', 'feature.txt')
        self.git('commit', '-qm', 'feature')
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git('branch', '--show-current').strip(), 'feature/committed')
        self.assertIn('skipped', self.report())

    def test_dirty_default_branch_is_not_synchronized(self):
        (self.repo / 'aift.repo.json').write_text('{"version":2}\n')
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git('branch', '--show-current').strip(), 'main')
        self.assertIn('uncommitted changes', self.report())

    def test_full_workflow_stops_before_push_when_pull_is_blocked(self):
        self.git('checkout', '-qb', 'feature/unfinished')
        runtime = self.home / 'AIFT' / 'runtime'
        shutil.copyfile(ROOT / 'runtime' / 'pull.sh', runtime / 'pull.sh')
        for name, function in (
            ('registry', 'aift_registry'), ('intel', 'aift_intelligence'),
            ('dashboard', 'aift_dashboard'), ('graph', 'aift_graph'),
            ('doctor', 'aift_doctor'), ('verify', 'aift_verify'),
            ('push', 'aift_push'),
        ):
            (runtime / f'{name}.sh').write_text(
                f'{function}() {{ printf "%s\\n" "{function}" >> "$TRACE_FILE"; }}\n'
            )
        trace = self.root / 'workflow-trace.txt'
        env = dict(self.env, TRACE_FILE=str(trace))
        result = subprocess.run(
            [BASH, '-c',
             f'source "{ROOT / "runtime" / "workflow.sh"}"; '
             'if aift_update; then exit 0; else exit $?; fi'],
            cwd=self.root, env=env, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(trace.exists(), 'workflow continued after unsafe pull')
        self.assertEqual(self.git('branch', '--show-current').strip(), 'feature/unfinished')

    def test_clean_default_branch_fast_forwards(self):
        other = self.root / 'other'
        self.git('clone', '-q', str(self.remote), str(other), cwd=self.root)
        self.git('config', 'user.name', 'Remote Tester', cwd=other)
        self.git('config', 'user.email', 'remote@example.invalid', cwd=other)
        (other / 'new-file.txt').write_text('remote content\n')
        self.git('add', 'new-file.txt', cwd=other)
        self.git('commit', '-qm', 'remote update', cwd=other)
        self.git('push', '-q', 'origin', 'main', cwd=other)
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.repo / 'new-file.txt').read_text(), 'remote content\n')
        self.assertIn('pulled main', self.report())

    def test_diverged_default_branch_reports_failure(self):
        other = self.root / 'other'
        self.git('clone', '-q', str(self.remote), str(other), cwd=self.root)
        self.git('config', 'user.name', 'Remote Tester', cwd=other)
        self.git('config', 'user.email', 'remote@example.invalid', cwd=other)
        (other / 'remote.txt').write_text('remote\n')
        self.git('add', 'remote.txt', cwd=other)
        self.git('commit', '-qm', 'remote update', cwd=other)
        self.git('push', '-q', 'origin', 'main', cwd=other)
        (self.repo / 'local.txt').write_text('local\n')
        self.git('add', 'local.txt')
        self.git('commit', '-qm', 'local update')
        local_head = self.git('rev-parse', 'HEAD').strip()
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), local_head)
        self.assertIn('manual merge needed', self.report())


if __name__ == '__main__':
    unittest.main()
