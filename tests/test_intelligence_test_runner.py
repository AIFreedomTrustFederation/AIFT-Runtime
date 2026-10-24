"""Regression: intelligence test failures must be visible to automation callers."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

RUNNER = Path(__file__).resolve().parents[1] / 'runtime/intelligence/test-runner.py'


class IntelligenceTestRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / 'home'
        self.repo = self.home / 'AIFT' / 'Aether_Coin_biozonecurrency'
        self.repo.mkdir(parents=True)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.env = dict(os.environ, HOME=str(self.home), PATH=str(self.bin) + os.pathsep + os.environ.get('PATH', ''))
        self.task = 'sample-task'

    def transformer(self):
        path = self.home / 'AIFT/registry/patch-execution/mutation/transformer' / (self.task + '-transform-report.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'candidates': [{'file': 'example.txt'}]}))

    def npm(self, fail_command=None):
        executable = self.bin / 'npm'
        executable.write_text('#!/bin/sh\n'
                              f'if [ "$1 $2" = "run {fail_command}" ]; then exit 17; fi\n'
                              'exit 0\n')
        executable.chmod(0o755)

    def run_runner(self):
        return subprocess.run([sys.executable, str(RUNNER), self.task], env=self.env,
                              cwd=self.root, capture_output=True, text=True)

    def report(self):
        path = self.home / 'AIFT/registry/patch-execution/tests' / (self.task + '-test-report.json')
        return json.loads(path.read_text())

    def test_missing_transformer_report_fails_closed(self):
        result = self.run_runner()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('Missing transformer report', result.stdout)

    def test_failed_check_returns_failure_and_blocks_mutation(self):
        self.transformer()
        self.npm('check')
        result = self.run_runner()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(self.report()['mutation_allowed'])
        self.assertEqual(self.report()['tests'][0]['exit_code'], 17)

    def test_failed_build_returns_failure_and_blocks_mutation(self):
        self.transformer()
        self.npm('build')
        result = self.run_runner()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(self.report()['mutation_allowed'])
        self.assertEqual(self.report()['tests'][1]['exit_code'], 17)

    def test_successful_checks_return_success_with_report(self):
        self.transformer()
        self.npm()
        result = self.run_runner()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(self.report()['mutation_allowed'])
        self.assertEqual([test['exit_code'] for test in self.report()['tests']], [0, 0])


if __name__ == '__main__':
    unittest.main()
