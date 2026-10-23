"""Regression: federation registry must preserve each discovered repository path."""
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


@unittest.skipUnless(BASH and GIT, 'bash and git are required')
class RegistryPathsTests(unittest.TestCase):
    def test_registry_preserves_whitespace_and_glob_characters(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            home = base / 'home'
            runtime = home / 'AIFT' / 'runtime'
            runtime.mkdir(parents=True)
            for name in ('common.sh', 'repo.sh', 'registry.sh'):
                shutil.copy2(ROOT / 'runtime' / name, runtime / name)

            workspace = base / 'workspace with spaces'
            workspace.mkdir()
            names = ('ordinary', 'repo with spaces', 'repo [brackets]', 'repo #hash')
            for name in names:
                repo = workspace / name
                subprocess.run([GIT, 'init', '-q', str(repo)], check=True)
                (repo / 'run.sh').write_text('#!/bin/sh\n')

            env = dict(os.environ, HOME=str(home), AIFT_WORKSPACE=str(workspace))
            command = 'source "$HOME/AIFT/runtime/registry.sh" && aift_registry'
            result = subprocess.run([BASH, '-c', command], cwd=base, env=env,
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            output = workspace / 'registry' / 'federation-index.json'
            records = json.loads(output.read_text())['repositories']
            self.assertEqual(len(records), len(names))
            self.assertEqual({r['name'] for r in records}, set(names))
            self.assertEqual({r['path'] for r in records},
                             {str(workspace / name) for name in names})
            self.assertTrue(all(r['language'] == 'shell' for r in records))
            self.assertTrue(all(isinstance(r['changedFiles'], int) for r in records))


if __name__ == '__main__':
    unittest.main(verbosity=2)
