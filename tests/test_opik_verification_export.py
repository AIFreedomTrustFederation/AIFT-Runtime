"""Offline trace evaluation preserves failures and excludes arbitrary evidence text."""

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/export_opik_verification.py"
spec = importlib.util.spec_from_file_location("opik_export", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def evidence(source_code=0, worktree_code=0):
    checks = [{"id": key, "exit_code": code, "status": "passed" if code == 0 else "failed"}
              for key, code in zip(module.CHECKS, (source_code, worktree_code))]
    return {"schema": "aift.verification.v1", "repository": module.REPOSITORY,
            "commit_sha": "a" * 40, "checks": checks,
            "overall_status": "passed" if source_code == worktree_code == 0 else "failed",
            "security": {"status": "not_checked"},
            "dependencies": {"status": "not_checked"},
            "deployment": {"status": "not_applicable"}}


class OpikVerificationExportTests(unittest.TestCase):
    def test_baseline_outcomes_survive_export_without_modifying_input(self):
        for codes in ((0, 0), (7, 0), (0, 1), (127, 1), (-9, 0)):
            with self.subTest(codes=codes):
                record = evidence(*codes)
                before = copy.deepcopy(record)
                trace = module.trace_kwargs(record)
                self.assertEqual(trace["output"]["overall_status"], record["overall_status"])
                self.assertEqual(trace["feedback_scores"][0]["value"], float(codes == (0, 0)))
                for check in record["checks"]:
                    self.assertEqual(trace["output"]["checks"][check["id"]]["exit_code"], check["exit_code"])
                self.assertEqual(record, before)

    def test_free_text_and_secrets_are_not_exported(self):
        record = evidence()
        marker = "PRIVATE-COMMAND-OUTPUT-AND-TOKEN"
        record.update(source={"run_url": marker}, generated_at=marker, limitations=[marker], token=marker)
        record["checks"][0].update(command=marker, output=marker, error=marker)
        record["security"]["reason"] = marker
        trace = module.trace_kwargs(record)
        self.assertNotIn(marker, json.dumps(trace))
        self.assertFalse(trace["metadata"]["evidence_authenticated"])
        self.assertEqual(trace["metadata"]["security"], "not_checked")

    def test_malformed_and_contradictory_records_are_rejected(self):
        variants = [None, [], {}]
        for key, value in (("schema", "other"), ("repository", "other/repo"),
                           ("commit_sha", "short"), ("overall_status", "failed"),
                           ("checks", []), ("security", {"status": "passed"})):
            record = evidence()
            record[key] = value
            variants.append(record)
        for key, value in (("id", "worktree"), ("id", []), ("exit_code", True),
                           ("exit_code", "0"), ("status", "failed")):
            record = evidence()
            record["checks"][0][key] = value
            variants.append(record)
        for record in variants:
            with self.subTest(record=record), self.assertRaises(ValueError):
                module.trace_kwargs(record)

    def test_cli_prepares_offline_payload_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp) / "evidence.json", Path(tmp) / "trace.json"
            source.write_text(json.dumps(evidence()))
            command = [sys.executable, "-B", str(SCRIPT), str(source), "--output", str(output)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            original = output.read_bytes()
            self.assertEqual(json.loads(original), module.trace_kwargs(evidence()))
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)
            self.assertEqual(output.read_bytes(), original)
            source.write_text('{"schema":"first","schema":"second"}')
            self.assertEqual(subprocess.run(command[:-1] + [str(Path(tmp) / "other.json")],
                                            capture_output=True).returncode, 2)

    def test_missing_required_evidence_never_produces_a_payload(self):
        variants = []
        for key in evidence():
            record = evidence()
            del record[key]
            variants.append((key, record))
        for index in range(2):
            for key in ("id", "exit_code", "status"):
                record = evidence()
                del record["checks"][index][key]
                variants.append((f"checks[{index}].{key}", record))
        for key in ("security", "dependencies", "deployment"):
            record = evidence()
            del record[key]["status"]
            variants.append((f"{key}.status", record))
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp) / "evidence.json", Path(tmp) / "trace.json"
            for label, record in variants:
                with self.subTest(missing=label):
                    with self.assertRaises(ValueError):
                        module.trace_kwargs(record)
                    source.write_text(json.dumps(record), encoding="utf-8")
                    before = source.read_bytes()
                    result = subprocess.run(
                        [sys.executable, "-B", str(SCRIPT), str(source), "--output", str(output)],
                        capture_output=True, text=True)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertEqual(result.stdout, "")
                    self.assertFalse(output.exists())
                    self.assertEqual(source.read_bytes(), before)

    def test_check_order_does_not_change_known_answer(self):
        for codes in ((0, 0), (0, 1), (7, 0), (-9, 127)):
            with self.subTest(codes=codes):
                record = evidence(*codes)
                expected = module.trace_kwargs(record)
                record["checks"].reverse()
                self.assertEqual(module.trace_kwargs(record), expected)


if __name__ == "__main__":
    unittest.main()
