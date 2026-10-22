"""Registry entries must represent whole Git checkout paths, not shell words."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which("bash")
GIT = shutil.which("git")


@unittest.skipUnless(BASH and GIT, "bash and git are required")
class RegistryPathsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / "home"
        self.workspace = self.home / "AIFT"
        runtime = self.workspace / "runtime"
        runtime.mkdir(parents=True)
        for name in ("common.sh", "repo.sh"):
            shutil.copy2(ROOT / "runtime" / name, runtime / name)
        self.repos = [self.workspace / "ordinary", self.workspace / "repo with spaces", self.workspace / "repo [brackets]"]
        for repo in self.repos:
            repo.mkdir()
            subprocess.run([GIT, "init", "-q", "-b", "main", str(repo)], check=True)
            subprocess.run([GIT, "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run([GIT, "-C", str(repo), "config", "user.name", "Test"], check=True)
            (repo / "README.md").write_text("fixture\n")
            subprocess.run([GIT, "-C", str(repo), "add", "README.md"], check=True)
            subprocess.run([GIT, "-C", str(repo), "commit", "-qm", "fixture"], check=True)

    def run_registry(self):
        env = os.environ.copy()
        env["HOME"] = str(self.home)
        env["AIFT_WORKSPACE"] = str(self.workspace)
        return subprocess.run([BASH, "-c", f'source "{ROOT / "runtime" / "registry.sh"}" && aift_registry'],
                              env=env, cwd=self.temp.name, capture_output=True, text=True)

    def test_registry_preserves_whitespace_and_glob_characters(self):
        result = self.run_registry()
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads((self.workspace / "registry" / "federation-index.json").read_text())
        self.assertEqual({entry["name"] for entry in data["repositories"]},
                         {repo.name for repo in self.repos})
        self.assertEqual({entry["path"] for entry in data["repositories"]},
                         {str(repo) for repo in self.repos})
        self.assertTrue(all(entry["branch"] == "main" for entry in data["repositories"]))
        self.assertTrue(all(entry["changedFiles"] == 0 for entry in data["repositories"]))

    def test_registry_does_not_include_workspace_support_directories(self):
        result = self.run_registry()
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads((self.workspace / "registry" / "federation-index.json").read_text())
        self.assertEqual(len(data["repositories"]), len(self.repos))
        self.assertNotIn("registry", {entry["name"] for entry in data["repositories"]})


if __name__ == "__main__":
    unittest.main()
