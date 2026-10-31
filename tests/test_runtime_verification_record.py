"""Regression tests for commit-bound runtime source verification records."""

import importlib.util
import json
import subprocess
import tempfile
import unittest
from unittest import mock
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/run_runtime_verification.py"
spec = importlib.util.spec_from_file_location("runtime_verification", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RuntimeVerificationRecordTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        self.output = self.base / "evidence.json"
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Test")
        (self.repo / "qa-local.sh").write_text("#!/usr/bin/env bash\nexit 0\n")
        self.git("add", "qa-local.sh")
        self.git("commit", "-qm", "fixture")
        self.sha = self.git("rev-parse", "HEAD").stdout.strip()

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, check=True,
                              capture_output=True, text=True)

    def record(self):
        return json.loads(self.output.read_text())

    def test_clean_success_records_exact_commit_and_explicit_unknowns(self):
        self.assertEqual(module.generate(self.repo, self.output, {}), 0)
        record = self.record()
        self.assertEqual(record["schema"], "aift.verification.v1")
        self.assertEqual(record["repository"], module.REPOSITORY)
        self.assertEqual(record["commit_sha"], self.sha)
        self.assertEqual(record["overall_status"], "passed")
        self.assertEqual([c["status"] for c in record["checks"]], ["passed", "passed"])
        self.assertEqual(record["security"]["status"], "not_checked")
        self.assertEqual(record["dependencies"]["status"], "not_checked")

    def test_failed_qa_writes_failed_evidence(self):
        (self.repo / "qa-local.sh").write_text("#!/usr/bin/env bash\nexit 7\n")
        self.git("add", "qa-local.sh")
        self.git("commit", "-qm", "failing fixture")
        self.assertEqual(module.generate(self.repo, self.output, {}), 1)
        self.assertEqual(self.record()["checks"][0]["exit_code"], 7)
        self.assertEqual(self.record()["overall_status"], "failed")

    def test_dirty_before_qa_fails_closed(self):
        (self.repo / "untracked.txt").write_text("unexpected")
        self.assertEqual(module.generate(self.repo, self.output, {}), 1)
        self.assertEqual(self.record()["checks"][1]["status"], "failed")

    def test_qa_mutation_fails_closed(self):
        (self.repo / "qa-local.sh").write_text("#!/usr/bin/env bash\ntouch generated.txt\n")
        self.git("add", "qa-local.sh")
        self.git("commit", "-qm", "mutating fixture")
        self.assertEqual(module.generate(self.repo, self.output, {}), 1)
        self.assertEqual(self.record()["checks"][1]["status"], "failed")

    def test_qa_changes_head_without_dirty_worktree_fails_closed(self):
        # A clean worktree is not sufficient: the evidence must describe
        # the same commit before and after source QA.
        script = ("#!/usr/bin/env bash\n"
                  "git commit --allow-empty -qm changed-during-qa\n")
        (self.repo / "qa-local.sh").write_text(script)
        self.git("add", "qa-local.sh")
        self.git("commit", "-qm", "fixture with moving head")
        original = self.git("rev-parse", "HEAD").stdout.strip()
        self.assertEqual(module.generate(self.repo, self.output, {}), 1)
        record = self.record()
        self.assertEqual(record["commit_sha"], original)
        self.assertEqual(record["checks"][0]["status"], "passed")
        self.assertEqual(record["checks"][1]["status"], "failed")
        self.assertEqual(record["overall_status"], "failed")
        self.assertNotEqual(self.git("rev-parse", "HEAD").stdout.strip(), original)
        self.assertEqual(self.git("status", "--porcelain").stdout, "")

    def test_replace_failure_preserves_previous_evidence_and_cleans_stage(self):
        original = b'{"previous": true}\n'
        self.output.write_bytes(original)
        with mock.patch.object(module.os, "replace", side_effect=OSError("simulated rename failure")):
            self.assertEqual(module.generate(self.repo, self.output, {}), 2)
        self.assertEqual(self.output.read_bytes(), original)
        self.assertEqual(list(self.base.glob(".evidence.json.*.tmp")), [])

    def test_sync_failure_preserves_previous_evidence_and_cleans_stage(self):
        original = b'{"previous": true}\n'
        self.output.write_bytes(original)
        with mock.patch.object(module.os, "fsync", side_effect=OSError("simulated sync failure")):
            self.assertEqual(module.generate(self.repo, self.output, {}), 2)
        self.assertEqual(self.output.read_bytes(), original)
        self.assertEqual(list(self.base.glob(".evidence.json.*.tmp")), [])

    def test_success_replaces_previous_evidence_without_stage_files(self):
        self.output.write_bytes(b'{"previous": true}\n')
        self.assertEqual(module.generate(self.repo, self.output, {}), 0)
        self.assertEqual(self.record()["commit_sha"], self.sha)
        self.assertEqual(list(self.base.glob(".evidence.json.*.tmp")), [])

    def test_commit_mismatch_rejected_without_artifact(self):
        self.assertEqual(module.generate(self.repo, self.output, {"GITHUB_SHA": "0" * 40}), 2)
        self.assertFalse(self.output.exists())

    def test_repository_mismatch_rejected_without_artifact(self):
        self.assertEqual(module.generate(self.repo, self.output, {"GITHUB_REPOSITORY": "other/repo"}), 2)
        self.assertFalse(self.output.exists())

    def test_actions_missing_identity_rejected_before_qa(self):
        complete = {"GITHUB_ACTIONS": "true", "GITHUB_SHA": self.sha,
                    "GITHUB_REPOSITORY": module.REPOSITORY, "GITHUB_RUN_ID": "12345"}
        for key in ("GITHUB_SHA", "GITHUB_REPOSITORY", "GITHUB_RUN_ID"):
            with self.subTest(missing=key):
                env = {k: v for k, v in complete.items() if k != key}
                self.assertEqual(module.generate(self.repo, self.output, env), 2)
                self.assertFalse(self.output.exists())

    def test_actions_invalid_run_id_rejected_before_qa(self):
        for run_id in ("", "0", "00", "01", "-1", "123abc", " 123", "１２３"):
            with self.subTest(run_id=run_id):
                env = {"GITHUB_ACTIONS": "true", "GITHUB_SHA": self.sha,
                       "GITHUB_REPOSITORY": module.REPOSITORY, "GITHUB_RUN_ID": run_id}
                self.assertEqual(module.generate(self.repo, self.output, env), 2)
                self.assertFalse(self.output.exists())

    def test_actions_complete_identity_and_local_compatibility(self):
        env = {"GITHUB_ACTIONS": "true", "GITHUB_SHA": self.sha,
               "GITHUB_REPOSITORY": module.REPOSITORY, "GITHUB_RUN_ID": "12345"}
        self.assertEqual(module.generate(self.repo, self.output, env), 0)
        self.assertEqual(self.record()["source"], {
            "type": "github-actions",
            "run_url": f"https://github.com/{module.REPOSITORY}/actions/runs/12345",
        })
        self.output.unlink()
        self.assertEqual(module.generate(self.repo, self.output, {}), 0)
        self.assertEqual(self.record()["source"], {"type": "local", "run_url": None})

    def test_output_inside_checkout_rejected(self):
        self.assertEqual(module.generate(self.repo, self.repo / "evidence.json", {}), 2)
        self.assertFalse((self.repo / "evidence.json").exists())


if __name__ == "__main__":
    unittest.main()
