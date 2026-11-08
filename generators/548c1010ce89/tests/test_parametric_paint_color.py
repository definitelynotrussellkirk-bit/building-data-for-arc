"""Prototype-only checks for the episode-level empty-line paint color."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

ROOT = find_root(__file__)
TASK_ROOT = ROOT / "generators/548c1010ce89"
PROTOTYPE = TASK_ROOT / "workspace/parametric/prototype.py"


def load_prototype():
    assert PROTOTYPE.is_file(), "parametric paint-color prototype is missing"
    spec = importlib.util.spec_from_file_location("parametric_paint_color_548c1010ce89", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ParametricPaintColorTests(unittest.TestCase):
    def test_default_program_is_exact_canonical_and_inputs_are_fixed_per_episode(self):
        prototype = load_prototype()
        canonical = prototype.canonical_record(ROOT)["program_solution"]
        self.assertEqual(prototype.program_for(2, "both", root=ROOT), canonical)
        self.assertNotEqual(prototype.program_for(6, "both", root=ROOT), canonical)
        for invalid in (True, 2.0, "2", 0, 9, None):
            with self.assertRaises(ValueError):
                prototype.program_for(invalid, "both", root=ROOT)
        first = prototype.episode_inputs(0, root=ROOT)
        second = prototype.episode_inputs(0, root=ROOT)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 7)
        self.assertEqual(len({json.dumps(grid) for grid in first}), 7)

    def test_materialized_episodes_have_three_demos_four_queries_and_no_surviving_rival(self):
        prototype = load_prototype()
        with tempfile.TemporaryDirectory(prefix="548c1010ce89-parametric-") as temp:
            out = Path(temp) / "evidence"
            report = prototype.write_evidence(out, seeds=(0, 1), root=ROOT)
            self.assertEqual(report["status"], "prototype_passed")
            self.assertTrue(report["canonical_default_exact"])
            self.assertEqual(report["settings_covered"], [2, 6])
            self.assertTrue(report["shared_inputs_across_settings"])
            self.assertEqual(len(report["episodes"]), 2)
            public_ids = set()
            for row in report["episodes"]:
                public = json.loads((out / row["public_path"]).read_text())
                private = json.loads((out / row["private_path"]).read_text())
                self.assertEqual(len(public["train"]), 3)
                self.assertEqual(len(public["test"]), 4)
                self.assertTrue(all(set(pair) == {"input", "output"} for pair in public["train"]))
                self.assertTrue(all(set(pair) == {"input"} for pair in public["test"]))
                self.assertEqual(public_challenge_id(public), row["public_id"])
                self.assertEqual(public_challenge_bytes(public), (out / row["public_path"]).read_bytes())
                public_ids.add(row["public_id"])
                self.assertEqual(len(private["query_answers"]), 4)
                self.assertEqual(private["input_seed"], (row["seed"] // 2) ^ 0x548C1010)
                self.assertEqual(private["surviving_declared_rivals"], [])
                for rival in private["rivals"].values():
                    self.assertTrue(rival["demonstration_mismatch_indices"])
                self.assertTrue(all(private["query_outputs_differ_from_other_color"]))
            self.assertEqual(len(public_ids), 2)

    def test_writer_supports_multiple_complete_paired_input_groups(self):
        prototype = load_prototype()
        with tempfile.TemporaryDirectory(prefix="548c1010ce89-parametric-groups-") as temp:
            out = Path(temp) / "evidence"
            report = prototype.write_evidence(out, seeds=(0, 1, 2, 3), root=ROOT)
            self.assertEqual(report["status"], "prototype_passed")
            self.assertTrue(report["shared_inputs_across_settings"])
            self.assertEqual(report["input_groups_checked"], 2)
            public_ids = [row["public_id"] for row in report["episodes"]]
            self.assertEqual(public_ids, sorted(public_ids))
            rows = {row["seed"]: json.loads((out / row["private_path"]).read_text()) for row in report["episodes"]}
            self.assertEqual(rows[0]["input_sha256"], rows[1]["input_sha256"])
            self.assertEqual(rows[2]["input_sha256"], rows[3]["input_sha256"])
            self.assertNotEqual(rows[0]["input_sha256"], rows[2]["input_sha256"])

    def test_canonical_ledger_remains_readable_from_portable_root(self):
        records = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()]
        self.assertEqual(sum(row.get("task_id") == "548c1010ce89" for row in records), 2)


if __name__ == "__main__":
    unittest.main()
