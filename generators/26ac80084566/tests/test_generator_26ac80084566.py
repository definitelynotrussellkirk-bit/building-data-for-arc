"""Bounded canonical shadow-rule and generator-contract regressions."""
from __future__ import annotations

import copy
import hashlib
import json
import random
import unittest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK = "26ac80084566"
ROOT = find_root(__file__)
GENERATOR, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)
BANDS = ("easy", "medium", "hard")
OLD_SHAPES = (
    {(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)},
    {(0, 0), (1, 0), (1, 1), (2, 0)},
    {(0, 0), (0, 1), (1, 1), (2, 1)},
    {(0, 0), (0, 1), (1, 0), (1, 1)},
)


def fixture(*, side="left", rectangle=False, color=3):
    grid = [[0] * 12 for _ in range(6)]
    for row in grid:
        row[8] = 8
    cells = ((1, 2), (1, 3), (2, 2), (2, 3)) if rectangle else (
        (1, 3), (2, 2), (2, 3), (2, 4), (3, 3)
    )
    for row, col in cells:
        grid[row][col] = color
    return grid if side == "left" else [list(reversed(row)) for row in grid]


def measured(grid):
    height, width = len(grid), len(grid[0])
    wall = next(col for col in range(width) if all(row[col] == 8 for row in grid))
    cells = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row)
             if value not in (0, 8)]
    side = "left" if all(c < wall for _, c, _ in cells) else "right"
    gap = wall - max(c for _, c, _ in cells) - 1 if side == "left" else min(c for _, c, _ in cells) - wall - 1
    return {"grid_h": height, "grid_w": width, "wall_col": wall, "side": side,
            "gap": gap, "shape_row": min(r for r, _, _ in cells),
            "shape_color": cells[0][2], "palette_size": 1, "n_distinct_colors": 2}


def normalized_shape(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value not in (0, 8)]
    top, left = min(r for r, _ in cells), min(c for _, c in cells)
    return {(r - top, c - left) for r, c in cells}


class GeneratorContractTests(unittest.TestCase):
    def test_boolean_grid_is_rejected(self):
        self.assertTrue(GENERATOR.self_check([[True]]))

    def test_unknown_override_is_rejected(self):
        with self.assertRaises(ValueError):
            GENERATOR.generate(0, 0, unknown_axis=1)

    def test_malformed_grids_have_exact_type_and_size_rejections(self):
        cases = [
            [], [[]], [[True]], [[1.0]], [["1"]], [[-1]], [[10]],
            [[0], [0, 0]], ((0, 8),), [(0, 8)], ["08"],
            [[0] for _ in range(31)], [[0] * 31], None,
            tuple(fixture()), [tuple(row) for row in fixture()],
        ]
        # Otherwise-lawful grids isolate numeric validation from wall/shape checks.
        for value in (False, 0.0):
            grid = fixture(); grid[0][0] = value; cases.append(grid)
        for value in (True, 3.0, -1, 10):
            grid = fixture()
            for row in grid:
                for col, cell in enumerate(row):
                    if cell == 3:
                        row[col] = value
            cases.append(grid)
        for grid in cases:
            with self.subTest(grid=grid):
                self.assertTrue(GENERATOR.self_check(grid))
                self.assertTrue(GENERATOR.strict_canonical_like(grid))
                with self.assertRaises(ValueError):
                    GENERATOR.rule_mirror(grid)

    def test_wall_and_foreground_grammar_rejects_concrete_violations(self):
        cases = {}
        grid = fixture(); grid[0][8] = 0; cases["broken wall"] = grid
        grid = fixture(); grid[0][0] = 8; cases["stray eight"] = grid
        grid = fixture()
        for row in grid:
            row[10] = 8
        cases["two walls"] = grid
        grid = [[0] * 12 for _ in range(6)]; grid[4] = [8] * 12; grid[1][2] = 3
        cases["horizontal wall only"] = grid
        grid = fixture(); grid[2][10] = 3; cases["both sides"] = grid
        grid = fixture(); grid[2][2] = 4; cases["two foreground colors"] = grid
        grid = fixture(); grid[0][0] = 3; cases["disconnected foreground"] = grid
        for name, grid in cases.items():
            with self.subTest(name=name):
                self.assertTrue(GENERATOR.self_check(grid))
                self.assertTrue(GENERATOR.strict_canonical_like(grid))

    def test_empty_shape_and_any_touching_row_are_rejected(self):
        empty = [[0] * 12 for _ in range(6)]
        for row in empty:
            row[8] = 8
        touching = copy.deepcopy(empty)
        for row, col in ((1, 5), (2, 5), (2, 6), (2, 7)):
            touching[row][col] = 3
        # Some cells could be newly filled, but the declared input gap is zero.
        for grid in (empty, touching):
            with self.subTest(grid=grid):
                self.assertTrue(GENERATOR.self_check(grid))
                self.assertTrue(GENERATOR.strict_canonical_like(grid))

    def test_seed_and_index_types_are_strict_and_negative_seeds_are_supported(self):
        for value in (True, False, 1.0, "1", None):
            with self.subTest(seed=value), self.assertRaises(ValueError):
                GENERATOR.generate(value, 0)
            with self.subTest(sample_index=value), self.assertRaises(ValueError):
                GENERATOR.generate(1, value)
        with self.assertRaises(ValueError):
            GENERATOR.generate(1, -1)
        for seed in (-17, 0, 2**63):
            self.assertEqual(GENERATOR.self_check(GENERATOR.generate(seed, 0)), [])

    def test_determinism_fresh_returns_and_global_rng_isolation(self):
        random.seed(1729)
        state = random.getstate()
        first = GENERATOR.generate(17, 3)
        second = GENERATOR.generate(17, 3)
        self.assertEqual(random.getstate(), state)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = (first[0][0] + 1) % 10
        self.assertEqual(second, GENERATOR.generate(17, 3))

    def test_difficulty_defaults_stay_banded_and_unknown_difficulty_rejects(self):
        bounds = {"easy": (5, 9, 7, 12), "medium": (9, 18, 10, 22), "hard": (18, 30, 18, 30)}
        for band, (h0, h1, w0, w1) in bounds.items():
            for index in range(4):
                with self.subTest(band=band, index=index):
                    grid = GENERATOR.generate(13, index, difficulty=band)
                    self.assertTrue(h0 <= len(grid) <= h1)
                    self.assertTrue(w0 <= len(grid[0]) <= w1)
                    self.assertEqual(GENERATOR.self_check(grid), [])
        self.assertEqual(GENERATOR.self_check(GENERATOR.generate(13, 0, difficulty=None)), [])
        for difficulty in ("extreme", "", 1, True):
            with self.subTest(difficulty=difficulty), self.assertRaises(ValueError):
                GENERATOR.generate(13, 0, difficulty=difficulty)

    def test_template_indices_preserve_old_shapes_and_add_canonical_profile(self):
        canonical_six = {(0, 0), (0, 1), (1, 1), (2, 0), (2, 1), (2, 2)}
        for index in range(8):
            grid = GENERATOR.generate(19, 0, grid_h=12, grid_w=18, side="left", wall_col=12, gap=2, shape_idx=index)
            with self.subTest(shape_idx=index):
                self.assertEqual(GENERATOR.self_check(grid), [])
                self.assertEqual(GENERATOR.observe_overrides(grid)["shape_idx"], index)
                if index < 4:
                    self.assertEqual(normalized_shape(grid), OLD_SHAPES[index])
                if index == 4:
                    self.assertEqual(normalized_shape(grid), canonical_six)

    def test_explicit_side_wall_gap_and_all_legal_colors_are_realized(self):
        for side, wall in (("left", 20), ("right", 9)):
            for color in (1, 2, 3, 4, 5, 6, 7, 9):
                requested = {"grid_h": 10, "grid_w": 30, "side": side, "wall_col": wall,
                             "gap": 8, "shape_color": color, "shape_idx": 0,
                             "shape_row": 0 if side == "left" else 7}
                with self.subTest(side=side, color=color):
                    grid = GENERATOR.generate(23, 1, **requested)
                    actual = measured(grid)
                    self.assertEqual({key: actual[key] for key in requested if key != "shape_idx"},
                                     {key: value for key, value in requested.items() if key != "shape_idx"})
                    self.assertEqual(GENERATOR.self_check(grid), [])

    def test_numeric_axes_reject_coercion_and_out_of_range_values(self):
        ranges = {"grid_h": (3, 31), "grid_w": (5, 31), "shape_idx": (-1, 8),
                  "shape_color": (0, 8, 10), "gap": (0, 9), "wall_col": (-1, 30),
                  "shape_row": (-1, 30)}
        for axis, invalid in ranges.items():
            for value in (*invalid, True, False, 1.0, "1", None):
                with self.subTest(axis=axis, value=value), self.assertRaises(ValueError):
                    GENERATOR.generate(0, 0, **{axis: value})
        for side in ("up", "", 0, True):
            with self.subTest(side=side), self.assertRaises(ValueError):
                GENERATOR.generate(0, 0, side=side)

    def test_infeasible_side_wall_gap_combinations_reject(self):
        cases = (
            {"side": "left", "wall_col": 1},
            {"side": "right", "wall_col": 4},
            {"side": "left", "wall_col": 4, "gap": 8},
            {"side": "left", "wall_col": 0},
            {"side": "right", "wall_col": 5},
            {"side": "left", "wall_col": 4, "shape_row": 2},
        )
        for controls in cases:
            with self.subTest(controls=controls), self.assertRaises(ValueError):
                GENERATOR.generate(0, 0, grid_h=4, grid_w=6, shape_idx=0, **controls)

    def test_explicit_wall_conditions_default_gap(self):
        # A 3-column shape has exactly one lawful gap at either pinned wall.
        # Choosing an unconstrained default gap first must not reject this request.
        for seed in range(8):
            for side, wall in (("left", 4), ("right", 5)):
                with self.subTest(seed=seed, side=side, wall_col=wall):
                    grid = GENERATOR.generate(seed, 0, grid_h=6, grid_w=10,
                                              shape_idx=0, side=side, wall_col=wall)
                    observed = measured(grid)
                    self.assertEqual(observed["wall_col"], wall)
                    self.assertEqual(observed["side"], side)
                    self.assertEqual(observed["gap"], 1)
                    self.assertEqual(GENERATOR.self_check(grid), [])

    def test_palette_texture_aliases_agree_and_conflicts_reject(self):
        for palette in ("default", "warm", "cool", "varied"):
            with self.subTest(palette=palette):
                explicit = GENERATOR.generate(29, 2, palette_kind=palette)
                alias = GENERATOR.generate(29, 2, texture=palette)
                both = GENERATOR.generate(29, 2, palette_kind=palette, texture=palette)
                self.assertEqual(explicit, alias)
                self.assertEqual(explicit, both)
                self.assertEqual(GENERATOR.self_check(alias), [])
        for controls in ({"palette_kind": "warm", "texture": "cool"},
                         {"palette_kind": "unknown"}, {"texture": "unknown"},
                         {"palette_kind": True}, {"texture": 1}):
            with self.subTest(controls=controls), self.assertRaises(ValueError):
                GENERATOR.generate(29, 2, **controls)

    def test_fixed_axes_enforce_their_exact_contract(self):
        fixed = {"palette_size": 1, "n_distinct_colors": 2,
                 "position_bias": "8line_divides_shape_offset", "density": "sparse"}
        self.assertEqual(GENERATOR.self_check(GENERATOR.generate(31, 1, **fixed)), [])
        bad = {"palette_size": (0, 2, True, 1.0, "1"),
               "n_distinct_colors": (1, 3, True, 2.0, "2"),
               "position_bias": ("random", 0), "density": ("dense", 0)}
        for axis, values in bad.items():
            for value in values:
                with self.subTest(axis=axis, value=value), self.assertRaises(ValueError):
                    GENERATOR.generate(31, 1, **{axis: value})

    def test_declared_negative_textures_are_invalid_inputs(self):
        for texture in ("no_line", "no_shape", "shape_touching_line"):
            with self.subTest(texture=texture):
                grid = GENERATOR.generate(37, 0, texture=texture)
                self.assertTrue(GENERATOR.self_check(grid))
                self.assertTrue(GENERATOR.strict_canonical_like(grid))
                with self.assertRaises(ValueError):
                    GENERATOR.rule_mirror(grid)

    def test_observed_controls_are_concrete_grid_properties(self):
        for side in ("left", "right"):
            grid = GENERATOR.generate(41, 2, grid_h=12, grid_w=18, side=side, gap=2, shape_idx=4)
            observed = GENERATOR.observe_overrides(grid)
            with self.subTest(side=side):
                expected = measured(grid)
                self.assertEqual({key: observed[key] for key in expected}, expected)
                self.assertEqual(observed["shape_idx"], 4)

    def test_rule_mirror_leaves_input_unchanged_and_adds_shadow(self):
        grid = fixture()
        original = copy.deepcopy(grid)
        output = GENERATOR.rule_mirror(grid)
        self.assertEqual(grid, original)
        self.assertIsNot(grid, output)
        self.assertEqual(output[1][2], 0)
        self.assertEqual(output[1][7], 3)
        self.assertEqual(output[2][2:8], [3] * 6)
        self.assertEqual(output[0], original[0])

    def test_default_schedule_covers_color_order_in_each_three_demo_window(self):
        for band in BANDS:
            for start in range(4):
                grids = [GENERATOR.generate(53, start + offset, difficulty=band) for offset in range(3)]
                colors = {measured(grid)["shape_color"] for grid in grids}
                with self.subTest(band=band, start=start):
                    self.assertIn(9, colors)
                    self.assertTrue(any(color < 8 for color in colors))

    def test_default_schedule_alternates_sides_and_has_rich_profiles(self):
        self.assertEqual(GENERATOR.EXAMPLES_NEEDED, 3)
        for band in BANDS:
            for index in range(4):
                grid = GENERATOR.generate(44, index, difficulty=band)
                actual = measured(grid)
                with self.subTest(band=band, index=index):
                    self.assertEqual(actual["side"], "left" if index % 2 == 0 else "right")
                    if index in (0, 1):
                        by_row = {}
                        for row, values in enumerate(grid):
                            cols = [col for col, value in enumerate(values) if value not in (0, 8)]
                            if cols:
                                by_row[row] = (min(cols), max(cols))
                        self.assertGreater(len({minimum for minimum, _ in by_row.values()}), 1)
                        self.assertGreater(len({maximum for _, maximum in by_row.values()}), 1)


class CanonicalRacketAndLessonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with canonical_path(ROOT).open(encoding="utf-8") as handle:
            programs = {row["program_solution"]
                        for row in (json.loads(line) for line in handle if line.strip())
                        if row.get("task_id") == TASK}
        if len(programs) != 1:
            raise AssertionError("One exact canonical source is required")
        cls.program = next(iter(programs))
        cls.wrapped = wrap_rule(cls.program)
        cls.bridge = RacketBridge()
        cls.addClassCleanup(cls.bridge.close)
        cls.outputs = {}

    @classmethod
    def tearDownClass(cls):
        print(json.dumps({
            "unique_canonical_racket_inputs": len(cls.outputs),
            "canonical_rule_applications": len(cls.outputs),
            "canonical_program_sha256": hashlib.sha256(cls.program.encode()).hexdigest(),
            "generator_sha256": SOURCE_SHA256,
        }, sort_keys=True), flush=True)

    def racket(self, grid):
        key = json.dumps(grid, separators=(",", ":"))
        if key not in self.outputs:
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            self.outputs[key] = self.bridge.eval_text(f"({self.wrapped} {literal})")
        return copy.deepcopy(self.outputs[key])

    def pair(self, grid):
        return {"input": grid, "output": self.racket(grid)}

    def test_all_three_canonical_labels_and_inputs_are_preserved(self):
        self.assertEqual(self.bridge.runtime_identity["backend"], "racket")
        self.assertIs(self.bridge.runtime_identity["protected"], True)
        pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
        self.assertEqual(len(pairs), 3)
        for pair in pairs:
            with self.subTest(split=pair["split"], index=pair["pair_index"]):
                self.assertEqual(GENERATOR.self_check(pair["input"]), [])
                self.assertEqual(GENERATOR.strict_canonical_like(pair["input"]), [])
                self.assertEqual(GENERATOR.rule_mirror(pair["input"]), pair["output"])
                self.assertEqual(self.racket(pair["input"]), pair["output"])

    def test_explicit_dimension_boundaries_execute_on_both_sides_in_every_band(self):
        for band in BANDS:
            for height, width in ((4, 6), (30, 30)):
                for side in ("left", "right"):
                    shape_row = 0 if side == "left" else height - 3
                    grid = GENERATOR.generate(47, 0, difficulty=band, grid_h=height, grid_w=width,
                                              shape_idx=0, side=side, gap=1, shape_row=shape_row)
                    with self.subTest(band=band, dimensions=(height, width), side=side):
                        self.assertEqual((len(grid), len(grid[0])), (height, width))
                        self.assertEqual(measured(grid)["side"], side)
                        self.assertEqual(measured(grid)["shape_row"], shape_row)
                        self.assertEqual(GENERATOR.self_check(grid), [])
                        self.assertEqual(GENERATOR.rule_mirror(grid), self.racket(grid))

    def test_lawful_non_template_shapes_are_accepted_and_racket_labeled(self):
        grid = [[0] * 16 for _ in range(10)]
        for row in grid:
            row[12] = 8
        for row in range(1, 8):
            grid[row][2] = 6
        for col in range(3, 9):
            grid[7][col] = 6
        for value in (grid, [list(reversed(row)) for row in grid]):
            with self.subTest(side=measured(value)["side"]):
                self.assertEqual(GENERATOR.self_check(value), [])
                self.assertEqual(GENERATOR.strict_canonical_like(value), [])
                self.assertNotIn("shape_idx", GENERATOR.observe_overrides(value))
                self.assertEqual(GENERATOR.rule_mirror(value), self.racket(value))
        # The validator's lawful grammar is wider than the generator's 4-row minimum.
        for value in ([[2, 0, 0, 8, 0, 0]], [[0, 0, 8, 0, 0, 2]]):
            self.assertEqual(GENERATOR.self_check(value), [])
            self.assertEqual(GENERATOR.strict_canonical_like(value), [])
            self.assertEqual(GENERATOR.rule_mirror(value), self.racket(value))

    def test_three_consecutive_default_demos_identify_all_four_schedule_starts(self):
        for band in BANDS:
            for start in range(4):
                grids = [GENERATOR.generate(53, start + offset, difficulty=band) for offset in range(4)]
                demos = [self.pair(grid) for grid in grids[:3]]
                with self.subTest(band=band, start=start):
                    self.assertEqual({measured(pair["input"])["side"] for pair in demos}, {"left", "right"})
                    self.assertEqual(GENERATOR.lesson_identifiable(demos, {"input": grids[3]}), [])
                    for grid in grids:
                        self.assertEqual(GENERATOR.rule_mirror(grid), self.racket(grid))

    def test_one_side_ambiguity_is_query_dependent_and_query_outputs_are_ignored(self):
        demos = [self.pair(fixture(side="left"))]
        ambiguous = {"input": fixture(side="right", color=5)}
        equivalent = {"input": fixture(side="left", color=5)}
        self.assertTrue(GENERATOR.lesson_identifiable(demos, ambiguous))
        self.assertEqual(GENERATOR.lesson_identifiable(demos, equivalent), [])
        for query in (ambiguous, equivalent):
            expected = GENERATOR.lesson_identifiable(demos, query)
            for hidden_answer in (None, [[True]], "deliberately not a grid"):
                candidate = {"input": copy.deepcopy(query["input"]), "output": hidden_answer}
                self.assertEqual(GENERATOR.lesson_identifiable(demos, candidate), expected)

    def test_color_order_rivals_use_only_demo_evidence(self):
        lower = [self.pair(fixture(side=side, color=3)) for side in ("left", "right")]
        upper = [self.pair(fixture(side=side, color=9)) for side in ("left", "right")]
        self.assertTrue(GENERATOR.lesson_identifiable(lower, {"input": fixture(color=9)}))
        self.assertTrue(GENERATOR.lesson_identifiable(upper, {"input": fixture(color=3)}))
        # A surviving color-order rule can agree with a particular query.
        self.assertEqual(GENERATOR.lesson_identifiable(lower, {"input": fixture(color=5)}), [])
        both = lower + [upper[0]]
        for color in (3, 9):
            query = {"input": fixture(side="right", color=color), "output": "private answer ignored"}
            self.assertEqual(GENERATOR.lesson_identifiable(both, query), [])

    def test_rectangular_and_overridden_lessons_cannot_borrow_schedule_guarantee(self):
        demos = [self.pair(fixture(side=side, rectangle=True)) for side in ("left", "right")]
        rich_query = {"input": fixture(color=5)}
        self.assertTrue(GENERATOR.lesson_identifiable(demos, rich_query))
        controlled = [self.pair(GENERATOR.generate(59, index, side="left", shape_idx=3)) for index in range(3)]
        self.assertTrue(GENERATOR.lesson_identifiable(controlled, {"input": fixture(side="right")}))
        rich = [self.pair(fixture(side=side)) for side in ("left", "right")]
        self.assertEqual(GENERATOR.lesson_identifiable(rich, rich_query), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
