"""Focused tests for the separate, unapproved frame-lookup prototype."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import random
import tempfile
import unittest

PROTOTYPE = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"
SPEC = importlib.util.spec_from_file_location("a61246736c26_parametric", PROTOTYPE)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class MaterializationTests(unittest.TestCase):
    def test_default_preserves_exact_canonical_source(self):
        self.assertEqual(MOD.materialize_program(), MOD.canonical_record()["program_solution"])
        self.assertEqual(MOD.normalized_rule_hash(MOD.materialize_program()), "08238424436c")
        for offset in (1, 2):
            self.assertNotEqual(MOD.materialize_program(offset), MOD.materialize_program())
            self.assertIn(f"(modulo (+ (first solid) {offset}) (length row-colors))", MOD.materialize_program(offset))

    def test_parameter_validation_and_seeded_selection(self):
        for bad in (-1, 3, True, False, 1.0, "1", None):
            with self.assertRaises(ValueError):
                MOD.materialize_program(bad)
        random.seed(29)
        before = random.getstate()
        choices = [MOD.choose_offset(seed, "sampled") for seed in range(30)]
        self.assertEqual(choices, [MOD.choose_offset(seed, "sampled") for seed in range(30)])
        self.assertEqual(set(choices), {0, 1, 2})
        self.assertEqual(before, random.getstate())
        self.assertEqual(MOD.choose_offset(7, 0), 0)

    def test_unidentified_query_and_rotation_are_reported(self):
        outputs = {"0": [[[0]], [[0]], [[0]], [[1]]],
                   "1": [[[0]], [[0]], [[0]], [[2]]],
                   "2": [[[9]], [[9]], [[9]], [[9]]]}
        report = MOD.identifiability_report(outputs, 0, 3)
        self.assertFalse(report["passed"])
        self.assertEqual(report["surviving_offsets"], [0, 1])
        self.assertEqual(report["query_changing_survivors"], [1])
        self.assertFalse(report["query_rotations"][-1]["passed"])


class ExecutedPrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from arc_repl.racket_bridge import RacketBridge
        cls.bridge = RacketBridge()
        try:
            cls.bundle = MOD.create_bundle(cls.bridge, seed=1701, all_settings=True)
        except BaseException:
            cls.bridge.shutdown()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.bridge.shutdown()

    def test_executed_variants_preserve_fill_shape_and_change_frame_lookup(self):
        generator = MOD.generator_module()
        for index, pair in enumerate(self.bundle["pairs"]):
            grid = pair["input"]
            self.assertEqual(generator.self_check(grid), [])
            analysis = generator._analysis(grid)
            size = analysis["tile_size"]
            baseline = self.bundle["executed_outputs"]["0"][index]
            self.assertEqual(baseline, generator.rule_mirror(grid))
            for offset in MOD.ALLOWED_OFFSETS:
                output = self.bundle["executed_outputs"][str(offset)][index]
                self.assertEqual((len(output), len(output[0])), (len(baseline), len(baseline[0])))
                for column, solid_row in enumerate(analysis["solid_rows"]):
                    frame = analysis["row_colors"][(solid_row + offset) % 3]
                    start = column * (size + 1)
                    for row in range(size):
                        for col in range(size):
                            expected = frame if row in (0, size - 1) or col in (0, size - 1) else baseline[row][start + col]
                            self.assertEqual(output[row][start + col], expected)
        self.assertTrue(all(row["passed"] for row in self.bundle["canonical_checks"]))

    def test_all_settings_have_identifiable_demos_and_query_rotations(self):
        self.assertEqual(len(self.bundle["episodes"]), 3)
        for episode in self.bundle["episodes"]:
            offset = episode["parameters"]["frame_row_offset"]
            report = episode["identifiability"]
            self.assertTrue(report["passed"])
            self.assertEqual(report["surviving_offsets"], [offset])
            self.assertTrue(all(row["surviving_offsets"] == [offset] for row in report["query_rotations"]))
        self.assertEqual(self.bundle["witness"]["distinct_output_count"], 3)

    def test_public_projection_and_replay_then_tamper_rejection(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "bundle"
            MOD.write_bundle(target, self.bundle, command=["focused-test"])
            for episode in self.bundle["episodes"]:
                public = json.loads((target / episode["public_path"]).read_text())
                self.assertEqual(set(public), {"train", "test"})
                self.assertEqual(len(public["train"]), 3)
                self.assertEqual(len(public["test"]), 1)
                self.assertTrue(all(set(pair) == {"input", "output"} for pair in public["train"]))
                self.assertTrue(all(set(pair) == {"input"} for pair in public["test"]))
            result = MOD.check_bundle(target, self.bridge)
            self.assertTrue(result["passed"])
            self.assertEqual(result["executed_rule_pair_count"], 15)
            path = target / self.bundle["episodes"][0]["public_path"]
            bad = json.loads(path.read_text())
            bad["test"][0]["output"] = [[8]]
            path.write_text(json.dumps(bad))
            with self.assertRaises(ValueError):
                MOD.check_bundle(target, self.bridge)

    def test_written_evidence_is_new_and_source_bound(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "bundle"
            MOD.write_bundle(target, self.bundle, command=["focused-test"])
            with self.assertRaises(FileExistsError):
                MOD.write_bundle(target, self.bundle, command=["focused-test"])
        bad = copy.deepcopy(self.bundle)
        bad["source_hashes"]["generators/a61246736c26/generator.py"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source"):
            MOD.validate_bundle(bad)


if __name__ == "__main__":
    unittest.main()
