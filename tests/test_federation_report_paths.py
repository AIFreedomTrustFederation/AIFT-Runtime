"""Integration test: report generators preserve repository paths."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FederationReportPaths(unittest.TestCase):
    def test_reports_preserve_repository_names(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            home = base / 'home'
            runtime = home / 'AIFT' / 'runtime'
            runtime.mkdir(parents=True)
            for name in ('common.sh', 'repo.sh', 'dashboard.sh', 'graph.sh'):
                shutil.copy2(ROOT / 'runtime' / name, runtime / name)
            workspace = base / 'workspace with spaces'
            workspace.mkdir()
            names = ('ordinary', 'repo with spaces', 'repo [brackets]', 'repo #hash')
            for name in names:
                repo = workspace / name
                subprocess.run(['git', 'init', '-q', str(repo)], check=True)
                (repo / 'run.sh').write_text('#!/bin/sh\n')
            env = dict(os.environ, HOME=str(home), AIFT_WORKSPACE=str(workspace))
            for service, filename, prefix in (
                ('dashboard', 'federation-dashboard.md', '## '),
                ('graph', 'federation-graph.txt', '├── '),
            ):
                with self.subTest(service=service):
                    command = f'source "$HOME/AIFT/runtime/{service}.sh" && aift_{service}'
                    result = subprocess.run(['bash', '-c', command], env=env,
                                            text=True, capture_output=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    report = (workspace / 'reports' / filename).read_text()
                    headings = [line for line in report.splitlines()
                                if line.startswith(prefix) and line != '├── Control Plane']
                    self.assertEqual(headings, [prefix + name for name in sorted(names)])


if __name__ == '__main__':
    unittest.main()
