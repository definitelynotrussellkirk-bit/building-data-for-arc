"""Executable prototype contracts; run with stdlib unittest, no pytest needed."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import random
import unittest

from reviewer_support import canonical_path, find_root


TASK = Path(__file__).resolve().parents[1]
PROTOTYPE = TASK / "workspace/parametric/prototype.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def boxes(height, width, rectangles):
    grid = [[3] * width for _ in range(height)]
    for top, left, bottom, right in rectangles:
        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                grid[row][col] = 0
    return grid


def changed(source, output):
    return {(r, c) for r, row in enumerate(source) for c, cell in enumerate(row)
            if cell != output[r][c]}


class RectanglePrototypeTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PROTOTYPE.is_file(), "requested rectangle prototype is not implemented")
        self.p = load(PROTOTYPE, "rectangle_parameter_test")

    def test_default_program_is_the_exact_canonical_authority(self):
        root = find_root(__file__)
        with canonical_path(root).open() as handle:
            records = [json.loads(line) for line in handle if line.strip()]
        canonical = next(r for r in records if r["task_id"] == "1e7eb285f158")
        self.assertEqual(self.p.program(self.p.DEFAULT), canonical["program_solution"])

    def test_inset_depth_on_nonsquare_rectangle_has_literal_changed_cells(self):
        source = boxes(7, 9, [(1, 1, 5, 7)])
        original = copy.deepcopy(source)
        expected = {
            1: {(r, c) for r in (2, 3, 4) for c in (2, 3, 4, 5, 6)},
            2: {(3, 3), (3, 4), (3, 5)},
        }
        for depth in (1, 2):
            for policy in ("row_major_first", "row_major_last"):
                output = self.p.solve(source, {"inset_depth": depth, "tie_policy": policy})
                self.assertEqual(changed(source, output), expected[depth])
                self.assertTrue(all(output[r][c] == 8 for r, c in expected[depth]))
        self.assertEqual(source, original)

    def test_three_by_three_is_nonempty_only_for_depth_one(self):
        source = boxes(5, 5, [(1, 1, 3, 3)])
        for depth, expected in ((1, {(2, 2)}), (2, set())):
            output = self.p.solve(source, {**self.p.DEFAULT, "inset_depth": depth})
            self.assertEqual(changed(source, output), expected)

    def test_tie_order_uses_top_left_then_bottom_right_for_residual_ties(self):
        # Same origin: 4x9 and 6x6 both have area 36. Canonical enumeration
        # encounters the 4x9 first; reversing the full order chooses the 6x6.
        source = boxes(8, 11, [(1, 1, 4, 9), (1, 1, 6, 6)])
        first = self.p.solve(source, self.p.DEFAULT)
        last = self.p.solve(source, {**self.p.DEFAULT, "tie_policy": "row_major_last"})
        self.assertEqual(changed(source, first), {(r, c) for r in (2, 3) for c in range(2, 9)})
        self.assertEqual(changed(source, last), {(r, c) for r in range(2, 6) for c in range(2, 6)})

    def test_unique_largest_area_beats_first_last_height_and_width(self):
        source = boxes(18, 18, [(1, 1, 7, 5), (1, 10, 6, 15), (10, 10, 14, 16)])
        for setting in self.p.SETTINGS:
            output = self.p.solve(source, setting)
            expected = ({(r, c) for r in range(2, 6) for c in range(11, 15)}
                        if setting["inset_depth"] == 1 else
                        {(r, c) for r in (3, 4) for c in (12, 13)})
            self.assertEqual(changed(source, output), expected)

    def test_matched_inputs_distinct_pairs_and_demo_only_certificates(self):
        expected_shortcuts = {
            "paint_full_rectangle", "paint_all_maxima", "first_maximal_rectangle",
            "last_maximal_rectangle", "tallest_rectangle", "widest_rectangle",
            "column_major_order", "reverse_secondary_tie", "foreground_echo", "identity",
        }
        for seed in (0, 17):
            baseline = None
            for setting in self.p.SETTINGS:
                episode = self.p.generate(seed, setting, demos=3, queries=4)
                self.assertEqual(len(episode["train"]), 3)
                self.assertEqual(len(episode["test"]), 4)
                inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
                keys = [json.dumps(grid) for grid in inputs]
                self.assertEqual(len(set(keys)), 7)
                if baseline is None:
                    baseline = inputs
                self.assertEqual(inputs, baseline, "input distribution must not reveal settings")
                cert = self.p.certify(episode["train"], setting)
                self.assertEqual(cert["surviving_settings"], [setting])
                self.assertEqual({row["name"] for row in cert["eliminated_shortcuts"]}, expected_shortcuts)
                self.assertTrue(all(0 <= row["witness_demo"] < 3
                                    for row in cert["eliminated_shortcuts"]))

    def test_counts_are_independent_and_maximum_request_is_not_shortened(self):
        one = self.p.generate(29, self.p.DEFAULT, demos=3, queries=1)
        many = self.p.generate(29, self.p.DEFAULT, demos=12, queries=12)
        self.assertEqual((len(one["train"]), len(one["test"])), (3, 1))
        self.assertEqual((len(many["train"]), len(many["test"])), (12, 12))
        self.assertEqual(one["train"], many["train"][:3])
        self.assertEqual(one["test"], many["test"][:1])
        keys = [json.dumps(p["input"]) for p in many["train"] + many["test"]]
        self.assertEqual(len(set(keys)), 24)

    def test_determinism_does_not_change_global_rng_or_alias_returned_grids(self):
        random.seed(923)
        before = random.getstate()
        first = self.p.generate(7, self.p.DEFAULT, demos=3, queries=1)
        self.assertEqual(random.getstate(), before)
        second = self.p.generate(7, self.p.DEFAULT, demos=3, queries=1)
        self.assertEqual(first, second)
        first["train"][0]["input"][0][0] = 9
        self.assertNotEqual(first, second)

    def test_settings_counts_and_seeds_require_declared_exact_types(self):
        invalid_settings = [None, {}, {**self.p.DEFAULT, "inset_depth": True},
                            {**self.p.DEFAULT, "inset_depth": 1.0},
                            {**self.p.DEFAULT, "inset_depth": 3},
                            {**self.p.DEFAULT, "tie_policy": "bottom_right"},
                            {**self.p.DEFAULT, "extra": 0}]
        for setting in invalid_settings:
            with self.subTest(setting=setting), self.assertRaises(ValueError):
                self.p.program(setting)
        for name, values in (("demos", (True, 3.0, 0, 2, 13)),
                             ("queries", (True, 4.0, 0, -1, 13)),
                             ("seed", (True, 1.0, -1, 2**63))):
            for value in values:
                args = dict(seed=0, settings=self.p.DEFAULT, demos=3, queries=4)
                args[name] = value
                with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                    self.p.generate(**args)

    def test_grid_validation_rejects_booleans_floats_ragged_and_oversized(self):
        for grid in ([], [[]], [[False]], [[1.0]], [[1], [1, 2]], [[10]], [[0] * 31]):
            with self.subTest(grid=grid), self.assertRaises(ValueError):
                self.p.solve(grid, self.p.DEFAULT)
        self.assertEqual(self.p.solve([[4]], self.p.DEFAULT), [[4]])

    def test_certificate_rejects_underidentified_or_incorrect_demonstrations(self):
        source = boxes(7, 9, [(1, 1, 5, 7)])
        output = self.p.solve(source, self.p.DEFAULT)
        with self.assertRaisesRegex(ValueError, "identif"):
            self.p.certify([{"input": source, "output": output}], self.p.DEFAULT)
        episode = self.p.generate(0, self.p.DEFAULT, demos=3, queries=4)
        episode["train"][0]["output"][0][0] = 8
        with self.assertRaisesRegex(ValueError, "chosen|match"):
            self.p.certify(episode["train"], self.p.DEFAULT)

    def test_sampler_failure_has_a_finite_retry_limit(self):
        # Duplicate candidate provider isolates retry/dedup behavior from RNG.
        grid = boxes(7, 9, [(1, 1, 5, 7)])
        calls = []
        def repeated(*args):
            calls.append(args)
            return copy.deepcopy(grid)
        original = self.p._sample_scene
        self.p._sample_scene = repeated
        try:
            with self.assertRaisesRegex(ValueError, "retry|distinct|sampling"):
                self.p.generate(0, self.p.DEFAULT, demos=3, queries=4)
        finally:
            self.p._sample_scene = original
        self.assertLessEqual(len(calls), 33)

    def test_adapter_uses_adjacent_source_and_declared_promotion_contract(self):
        adapter = load(PROTOTYPE.with_name("adapter.py"), "rectangle_adapter_test")
        contract = json.loads(PROTOTYPE.with_name("promotion.json").read_text())
        self.assertEqual(adapter.program(contract["default"]), self.p.program(self.p.DEFAULT))
        episode = adapter.generate(0, contract["default"], 3, 4)
        self.assertEqual((len(episode["train"]), len(episode["test"])), (3, 4))
        self.assertEqual(contract["limits"], {"demos": [3, 12], "queries": [1, 12]})

    def test_protected_racket_executes_literal_boundaries_and_canonical_examples(self):
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule
        from reviewer_support import canonical_pairs
        cases = [
            boxes(7, 9, [(1, 1, 5, 7)]),
            boxes(5, 5, [(1, 1, 3, 3)]),
            boxes(8, 11, [(1, 1, 4, 9), (1, 1, 6, 6)]),
            boxes(13, 13, [(1, 7, 5, 11), (7, 1, 11, 5)]),
        ]
        with RacketBridge(timeout=20) as bridge:
            self.assertIs(bridge.runtime_identity["protected"], True)
            def execute(program, grid):
                literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
                return bridge.eval_text(f"({wrap_rule(program)} {literal})")
            for setting in self.p.SETTINGS:
                for source in cases:
                    self.assertEqual(execute(self.p.program(setting), source), self.p.solve(source, setting))
            for pair in canonical_pairs("1e7eb285f158", root=find_root(__file__)):
                self.assertEqual(execute(self.p.program(self.p.DEFAULT), pair["input"]), pair["output"])


if __name__ == "__main__":
    unittest.main()
