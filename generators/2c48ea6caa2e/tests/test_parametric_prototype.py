"""Focused tests for the isolated threshold-rule prototype.

These tests do not alter or approve the selected canonical generator.  They
exercise only workspace/parametric/prototype.py and its retained Racket rules.
"""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


TASK_DIR = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = TASK_DIR / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    if not PROTOTYPE_PATH.is_file():
        raise AssertionError(f"missing parametric prototype: {PROTOTYPE_PATH}")
    spec = importlib.util.spec_from_file_location(
        "task_2c48ea6caa2e_parametric_prototype",
        PROTOTYPE_PATH,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot import parametric prototype: {PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ThresholdParametricPrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prototype = load_prototype()

    def test_parameter_contract_and_episode_level_selection(self):
        p = self.prototype
        self.assertEqual(p.TASK_ID, "2c48ea6caa2e")
        self.assertEqual(p.ALLOWED_THRESHOLDS, (3, 4, 5))
        self.assertEqual(p.DEFAULT_THRESHOLD, 4)

        selected = {p.choose_threshold(seed) for seed in range(512)}
        self.assertEqual(selected, set(p.ALLOWED_THRESHOLDS))
        for seed in range(24):
            episode = p.build_episode(seed)
            self.assertEqual(
                episode["meta"]["threshold"],
                p.choose_threshold(seed),
            )
            self.assertEqual(len(episode["train"]), 3)
            self.assertEqual(len(episode["test"]), 1)
            self.assertEqual(
                episode["program"],
                p.program_for(episode["meta"]["threshold"]),
            )

        for bad in (True, False, 3.0, "4", None):
            with self.subTest(bad=bad):
                with self.assertRaises((TypeError, ValueError)):
                    p.choose_threshold(bad)
        for bad in (2, 6, True, 4.0, "4", None):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    p.program_for(bad)

    def test_each_complete_episode_refutes_both_parameter_rivals(self):
        p = self.prototype
        for threshold in p.ALLOWED_THRESHOLDS:
            episode = p.build_episode(9000 + threshold, threshold=threshold)
            self.assertEqual(episode["meta"]["threshold"], threshold)
            self.assertEqual(p.parameter_rival_findings(episode), [])
            for split in ("train", "test"):
                for pair in episode[split]:
                    self.assertEqual(
                        pair["output"],
                        p.apply_python(pair["input"], threshold),
                    )
                    for rival in p.ALLOWED_THRESHOLDS:
                        if rival == threshold:
                            continue
                        self.assertNotEqual(
                            pair["output"],
                            p.apply_python(pair["input"], rival),
                        )

    def test_retained_rules_match_programs_and_public_challenge_hides_rule(self):
        p = self.prototype
        for threshold in p.ALLOWED_THRESHOLDS:
            self.assertEqual(
                p.rule_path(threshold).read_text(encoding="utf-8"),
                p.program_for(threshold),
            )
            episode = p.build_episode(12000 + threshold, threshold=threshold)
            public = p.public_challenge(episode)
            self.assertEqual(len(public["train"]), 3)
            self.assertEqual(len(public["test"]), 1)
            self.assertNotIn("output", public["test"][0])
            serialized = json.dumps(public, sort_keys=True)
            self.assertNotIn("threshold", serialized)
            self.assertNotIn("program", serialized)
            self.assertNotIn("rule!", serialized)

    def test_materialize_executes_exact_racket_and_records_parity(self):
        p = self.prototype
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence_path = root / "evidence.json"
            public_dir = root / "public"
            report = p.materialize(
                evidence_path,
                public_dir=public_dir,
                seed_start=16000,
            )
            self.assertEqual(report["status"], "prototype")
            self.assertEqual(
                {row["threshold"] for row in report["episodes"]},
                set(p.ALLOWED_THRESHOLDS),
            )
            self.assertTrue(evidence_path.is_file())
            for row in report["episodes"]:
                self.assertTrue(row["every_demo_refutes_all_alternatives"])
                self.assertTrue(row["public_path"].endswith(".json"))
                self.assertTrue((public_dir / Path(row["public_path"]).name).is_file())
                for execution in row["executions"]:
                    self.assertTrue(execution["racket_matches_python"])
                    self.assertTrue(execution["chosen_differs_from_all_rivals"])


if __name__ == "__main__":
    unittest.main()
