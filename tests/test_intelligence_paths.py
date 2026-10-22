"""Integration regression: federation intelligence must preserve repository paths."""
import json
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
class IntelligencePathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / 'home'
        runtime = self.home / 'AIFT' / 'runtime'
        runtime.mkdir(parents=True)
        for script in ('common.sh', 'repo.sh', 'intel.sh'):
            shutil.copy2(ROOT / 'runtime' / script, runtime / script)
        self.workspace = self.root / 'AIFT workspace'
        self.workspace.mkdir()
        self.repos = []
        for name in ('ordinary', 'repo with spaces', 'repo [brackets]', 'repo #hash'):
            repo = self.workspace / name
            subprocess.run([GIT, 'init', '-q', str(repo)], check=True)
            (repo / 'scripts').mkdir()
            (repo / 'scripts' / 'hello.sh').write_text('#!/bin/sh\necho hello\n')
            (repo / 'AGENTS.md').write_text('agent instructions\n')
            (repo / 'aift.repo.json').write_text('{}\n')
            self.repos.append(repo)

    def run_intelligence(self):
        env = os.environ.copy()
        env.update(HOME=str(self.home), AIFT_WORKSPACE=str(self.workspace))
        return subprocess.run([BASH, '-c', 'source "$HOME/AIFT/runtime/intel.sh" && aift_intelligence'],
                              cwd=self.root, env=env, text=True, capture_output=True)

    def test_json_indexes_each_repository_once_with_original_path(self):
        result = self.run_intelligence()
        self.assertEqual(result.returncode, 0, result.stderr)
        output = self.workspace / 'intelligence' / 'federation-intelligence.json'
        entries = json.loads(output.read_text())['repositories']
        self.assertEqual(len(entries), len(self.repos))
        self.assertEqual({e['path'] for e in entries}, {str(r) for r in self.repos})
        self.assertEqual({e['repo'] for e in entries}, {r.name for r in self.repos})

    def test_relative_paths_are_not_corrupted_by_regex_metacharacters(self):
        result = self.run_intelligence()
        self.assertEqual(result.returncode, 0, result.stderr)
        output = self.workspace / 'intelligence' / 'federation-intelligence.json'
        entries = json.loads(output.read_text())['repositories']
        for entry in entries:
            self.assertEqual(entry['commands'], ['scripts/hello.sh'], entry['repo'])
            self.assertEqual(entry['agents'], ['AGENTS.md'], entry['repo'])
            self.assertIn('aift.repo.json', entry['manifests'], entry['repo'])

    def test_markdown_reports_each_repository_once(self):
        result = self.run_intelligence()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = (self.workspace / 'reports' / 'federation-intelligence.md').read_text()
        for repo in self.repos:
            self.assertEqual(report.count(f'## {repo.name}\n'), 1, repo.name)
        self.assertEqual(report.count('- Runtime: ' + chr(96)), len(self.repos))


if __name__ == '__main__':
    unittest.main(verbosity=2)
