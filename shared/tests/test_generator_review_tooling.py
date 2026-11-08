from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

from scripts import generator_selfcheck
from src.core.canonical_pairs import load_task_pairs


ROOT = Path(__file__).resolve().parents[1]


class CanonicalPairHelperTests(unittest.TestCase):
    def test_normalizes_singleton_and_list_pair_containers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            canonical = Path(directory) / "puzzles.jsonl"
            canonical.write_text(
                json.dumps(
                    {
                        "task_id": "task",
                        "train": [
                            {"input": ["01", "20"], "output": ["10", "02"]}
                        ],
                        "test": {
                            "input": [[3, 0], [0, 3]],
                            "output": [[0, 3], [3, 0]],
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            pairs = load_task_pairs("task", canonical)
            self.assertEqual(2, len(pairs))
            self.assertEqual([[0, 1], [2, 0]], pairs[0]["input"])
            self.assertEqual("test", pairs[1]["split"])

    def test_selfcheck_rejecting_canonical_input_is_blocking(self) -> None:
        module = types.SimpleNamespace(self_check=lambda grid: ["not accepted"])
        report = generator_selfcheck.Report("task")
        pairs = [
            {
                "input": [[1]],
                "output": [[1]],
                "split": "train",
                "row_index": 0,
                "pair_index": 0,
            }
        ]
        with mock.patch.object(
            generator_selfcheck, "load_task_pairs", return_value=pairs
        ):
            generator_selfcheck.check_canonical_inputs(
                "task", module, report
            )
        self.assertEqual(2, report.exit_code)
        self.assertIn("rejected canonical", report.errors[0])


class OverrideResultExportTests(unittest.TestCase):
    def test_writes_per_case_realized_observations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "override-results.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/check_generator_override_contract.py",
                    "78806e443729",
                    "--seeds",
                    "1",
                    "--bands",
                    "easy",
                    "--write-results",
                    str(output),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("78806e443729", payload["task_id"])
            self.assertEqual(payload["case_count"], len(payload["cases"]))
            self.assertTrue(payload["cases"])
            self.assertTrue(
                any(
                    case["realized_observations"]
                    for case in payload["cases"]
                    if case["accepted"]
                )
            )


class SelfcheckCliTests(unittest.TestCase):
    def test_task_id_and_seeds_aliases(self) -> None:
        report = generator_selfcheck.Report("task")
        report.has_self_check = True
        with mock.patch.object(
            generator_selfcheck, "selfcheck_generator", return_value=report
        ) as selfcheck:
            self.assertEqual(
                0,
                generator_selfcheck.main(
                    ["--task-id", "task", "--seeds", "7"]
                ),
            )
        selfcheck.assert_called_once_with(
            "task", n=7, timeout_sec=10.0, require_mutation_sensitivity=False
        )


if __name__ == "__main__":
    unittest.main()
