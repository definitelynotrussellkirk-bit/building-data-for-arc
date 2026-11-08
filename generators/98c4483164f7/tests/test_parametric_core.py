"""Focused, stdlib-only behavioral tests for the proposed parametric core."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "shared/runtime").is_dir())
HOME = ROOT / "generators/98c4483164f7/workspace/parametric"


def core():
    path = HOME / "core.py"
    assert path.is_file(), "parametric core has not been implemented"
    name = "test_parametric_core_98c4483164f7"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


def canonical():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        return next(row for line in handle if (row := json.loads(line))["task_id"] == "98c4483164f7")


def fixture():
    grid = [[0] * 6 for _ in range(6)]
    grid[2][2], grid[2][3], grid[3][2], grid[3][3] = 2, 5, 5, 5
    return grid


class ParametricCoreTests(unittest.TestCase):
    def test_default_is_exact_canonical_program_and_all_saved_pairs(self):
        c, record = core(), canonical()
        self.assertEqual(c.materialize_program(), record["program_solution"])
        self.assertEqual((HOME / "canonical.rkt").read_text(), record["program_solution"])
        for pair in record["train"] + record["test"]:
            with self.subTest(input=pair["input"]):
                self.assertEqual(c.transform(pair["input"]), pair["output"])

    def test_clockwise_and_stride_have_hand_checked_cells(self):
        c = core()
        painted = {(0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 1),
                   (2, 2), (2, 3), (3, 2), (3, 3)}
        spaced = {(0, 0), (0, 1), (1, 0), (1, 1), (2, 2), (2, 3), (3, 2), (3, 3)}
        for q in range(4):
            for stride, expected in ((1, painted), (2, spaced)):
                out = c.transform(fixture(), {"quarter_turns": q, "stride": stride})
                self.assertEqual({(r, col) for r, row in enumerate(out) for col, val in enumerate(row) if val}, expected)
                self.assertEqual({v for row in out for v in row}, {0, 5})
            painted = {(col, 5 - r) for r, col in painted}
            spaced = {(col, 5 - r) for r, col in spaced}

    def test_one_lawful_input_distinguishes_all_eight_settings_without_mutation(self):
        c, grid = core(), fixture()
        original = copy.deepcopy(grid)
        outputs = [json.dumps(c.transform(grid, s)) for s in c.enumerate_settings()]
        self.assertEqual(len(outputs), 8)
        self.assertEqual(len(set(outputs)), 8)
        self.assertEqual(grid, original)
        self.assertEqual(len({c.materialize_program(s) for s in c.enumerate_settings()}), 8)

    def test_partial_mapping_defaults_and_dataclass_normalization(self):
        c = core()
        self.assertEqual(c.params_dict(None), {"quarter_turns": 0, "stride": 1})
        self.assertEqual(c.params_dict({}), {"quarter_turns": 0, "stride": 1})
        self.assertEqual(c.params_dict({"stride": 2}), {"quarter_turns": 0, "stride": 2})
        self.assertEqual(c.normalize_params(c.Params(3, 2)), c.Params(3, 2))

    def test_strict_parameter_types_bounds_and_keys(self):
        c = core()
        cases = [True, 1, [], "0", {"quarter_turns": True}, {"quarter_turns": 1.0},
                 {"quarter_turns": -1}, {"quarter_turns": 4}, {"stride": False},
                 {"stride": 2.0}, {"stride": 0}, {"stride": 3}, {"stride": None},
                 {"unknown": 0}, c.Params(True, 1), c.Params(0, 9)]
        for value in cases:
            for fn in (c.normalize_params, c.materialize_program):
                with self.subTest(value=value, function=fn.__name__):
                    with self.assertRaises((TypeError, ValueError)):
                        fn(value)

    def test_invalid_and_out_of_grammar_inputs_fail(self):
        c = core()
        invalid = [None, [], [[]], [[0], [0, 1]], [[True, 2], [5, 5]],
                   [[2.0, 5], [5, 5]], [[2, 5], [5, 10]], [[2, 2], [2, 2]],
                   [[5, 5], [5, 5]], [[2, 5], [3, 5]], [[2, 0, 5], [5, 0, 5]],
                   [[0] * 6 for _ in range(6)], [[0] * 31 for _ in range(31)]]
        for grid in invalid:
            with self.subTest(grid=grid):
                with self.assertRaises((TypeError, ValueError)):
                    c.transform(grid)

    def test_edge_motif_is_in_grammar_for_every_setting(self):
        c = core()
        for settings in c.enumerate_settings():
            self.assertEqual(c.transform([[2, 5], [5, 5]], settings), [[5, 5], [5, 5]])

    def test_sampler_delegates_exact_dimensions_and_is_deterministic(self):
        c = core()
        for h, w in ((6, 30), (30, 6), (9, 9)):
            grid = c.sample_input(173, 29, grid_h=h, grid_w=w)
            self.assertEqual((len(grid), len(grid[0])), (h, w))
            self.assertEqual(grid, c.canonical_generator().generate(173, 29, grid_h=h, grid_w=w))
            self.assertEqual(grid, c.sample_input(173, 29, grid_h=h, grid_w=w))
        for value in (True, 1.0, -1):
            with self.assertRaises((TypeError, ValueError)):
                c.sample_input(0, value)
        for value in (True, 5, 31):
            with self.assertRaises((TypeError, ValueError)):
                c.sample_input(0, 0, grid_h=value)


if __name__ == "__main__":
    unittest.main(verbosity=2)
