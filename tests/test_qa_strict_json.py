"""Black-box regressions for the tracked-JSON source QA gate."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

QA = Path(__file__).resolve().parents[1] / "qa-local.sh"


class StrictRuntimeJsonQaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "QA Fixture")
        self.git("config", "user.email", "qa@example.invalid")
        shutil.copyfile(QA, self.repo / "qa-local.sh")
        (self.repo / ".gitignore").write_text(
            "runtime/ai/*.pid\nruntime/ai/logs/*.log\n", encoding="utf-8"
        )
        (self.repo / ".gitattributes").write_text(
            "*.gguf filter=lfs diff=lfs merge=lfs -text\n", encoding="utf-8"
        )
        (self.repo / "model.gguf").write_text(
            "version https://git-lfs.github.com/spec/v1\n"
            + "oid sha256:" + "a" * 64 + "\n"
            + "size 123\n", encoding="utf-8"
        )
        (self.repo / "dummy.py").write_text("x = 1\n", encoding="utf-8")
        (self.repo / "tests").mkdir()
        (self.repo / "tests" / "test_fixture.py").write_text(
            "import unittest\nclass Fixture(unittest.TestCase):\n"
            "    def test_ok(self):\n        self.assertTrue(True)\n", encoding="utf-8"
        )
        self.json_file = self.repo / "config.json"
        self.set_json('{"value": 1.5}')

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, check=True,
                              text=True, capture_output=True)

    def set_json(self, payload):
        self.json_file.write_text(payload + "\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")

    def qa(self):
        return subprocess.run(["bash", "qa-local.sh"], cwd=self.repo,
                              capture_output=True, text=True, timeout=30)

    def test_finite_json_and_scientific_notation_pass(self):
        for payload in ('{"value": 1e100}', '{"value": -2.5e-10}', '{"value": 0}'):
            with self.subTest(payload=payload):
                self.set_json(payload)
                result = self.qa()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("Validated", result.stdout)

    def test_nonfinite_json_is_rejected(self):
        for payload in ('{"value": NaN}', '{"value": Infinity}',
                        '{"value": -Infinity}', '{"value": 1e9999}',
                        '{"value": -1e9999}'):
            with self.subTest(payload=payload):
                self.set_json(payload)
                result = self.qa()
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn("non-finite JSON number", result.stderr)

    def test_duplicate_keys_still_rejected(self):
        self.set_json('{"value": 1, "value": 2}')
        result = self.qa()
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("duplicate JSON key", result.stderr)


if __name__ == "__main__":
    unittest.main()
