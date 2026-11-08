"""Focused regression tests for generator 056999828b88."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "puzzle_generators" / "per_puzzle" / "056999828b88" / "generator.py"
SHAPE_PROBE_PATH = (
    ROOT
    / "repo"
    / "generators"
    / "056999828b88"
    / "workspace"
    / "shape_support_probe.py"
)
SHORTCUT_PROBE_PATH = SHAPE_PROBE_PATH.with_name("shortcut_counterexample.py")
CANDIDATE_SWEEP_PATH = SHAPE_PROBE_PATH.with_name("candidate_rival_sweep.py")


def load_generator():
    spec = importlib.util.spec_from_file_location("generator_056999828b88", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_shape_probe():
    spec = importlib.util.spec_from_file_location(
        "shape_support_probe_056999828b88",
        SHAPE_PROBE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_shortcut_probe():
    spec = importlib.util.spec_from_file_location(
        "shortcut_counterexample_056999828b88",
        SHORTCUT_PROBE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_candidate_sweep():
    spec = importlib.util.spec_from_file_location(
        "candidate_rival_sweep_056999828b88",
        CANDIDATE_SWEEP_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_task():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") == "056999828b88":
                return row
    raise AssertionError("canonical task 056999828b88 is missing")


def canonical_pairs():
    row = canonical_task()
    return row["train"] + [row["test"]]


def canonical_inputs():
    return [pair["input"] for pair in canonical_pairs()]


class PackBySizeGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = load_generator()
        cls.canonical = canonical_inputs()

    def test_rule_hash_and_exact_canonical_profile_table(self):
        self.assertEqual("d2d58f482c81", self.generator.RULE_HASH)
        derived = {self.generator._linked_profile(grid) for grid in self.canonical}
        self.assertEqual(self.generator._CANONICAL_LINKED_PROFILES, derived)

    def test_every_canonical_input_is_accepted_and_strict(self):
        for index, grid in enumerate(self.canonical):
            with self.subTest(index=index):
                self.assertEqual([], self.generator.self_check(grid))
                self.assertEqual([], self.generator.strict_canonical_like(grid))

    def test_declared_override_boundaries_are_exact_in_every_band(self):
        cases = [
            {"grid_h": 8, "grid_w": 10, "n_objects": 3},
            {"grid_h": 10, "grid_w": 12, "n_objects": 4},
        ]
        for band in ("easy", "medium", "hard"):
            for case in cases:
                grid = self.generator.generate(41, 17, difficulty=band, **case)
                observed = self.generator.observe_overrides(grid)
                with self.subTest(band=band, case=case):
                    self.assertEqual(case, {key: observed[key] for key in case})
                    self.assertEqual([], self.generator.self_check(grid, difficulty=band))

    def test_generated_outputs_preserve_canonical_shrink_relation(self):
        offsets = {"easy": 0, "medium": 1, "hard": 2}
        for band, offset in offsets.items():
            for n_objects in (3, 4):
                for sample_index in range(8):
                    slot = (sample_index + offset) % 4
                    grid = self.generator.generate(
                        20261002,
                        sample_index,
                        difficulty=band,
                        grid_h=8,
                        grid_w=10,
                        n_objects=n_objects,
                    )
                    output = self.generator._size_pack(grid)
                    if slot != 3 or n_objects == 3:
                        with self.subTest(
                            band=band,
                            n_objects=n_objects,
                            sample_index=sample_index,
                        ):
                            self.assertLessEqual(len(output), len(grid))
                            self.assertLessEqual(len(output[0]), len(grid[0]))

        reshape = 0
        total = 0
        for band in offsets:
            for sample_index in range(20):
                grid = self.generator.generate(
                    20261002, sample_index, difficulty=band
                )
                output = self.generator._size_pack(grid)
                total += 1
                reshape += not (
                    len(output) <= len(grid) and len(output[0]) <= len(grid[0])
                )
        self.assertLess(reshape, 0.30 * total, (reshape, total))

    def test_four_sample_schedule_is_identifiable(self):
        for band in ("easy", "medium", "hard"):
            for start in range(8):
                demos = []
                for sample_index in range(start, start + self.generator.EXAMPLES_NEEDED):
                    grid = self.generator.generate(12345, sample_index, difficulty=band)
                    demos.append({"input": grid, "output": self.generator._size_pack(grid)})
                query_grid = self.generator.generate(
                    12345, start + self.generator.EXAMPLES_NEEDED, difficulty=band
                )
                query = {
                    "input": query_grid,
                    "output": self.generator._size_pack(query_grid),
                }
                with self.subTest(band=band, start=start):
                    self.assertEqual([], self.generator.lesson_identifiable(demos, query))
                    for name, competitor in self.generator.LESSON_COMPETITORS.items():
                        self.assertTrue(
                            any(
                                competitor(pair["input"]) != pair["output"]
                                for pair in demos
                            ),
                            name,
                        )

    def test_free_polyomino_universe_counts_and_legacy_gap(self):
        expected = {1: 1, 2: 1, 3: 2, 4: 5, 5: 12, 6: 35}
        observed = {
            size: len(self.generator._free_polyominoes(size))
            for size in expected
        }
        self.assertEqual(expected, observed)

        line4 = ((0, 0), (0, 1), (0, 2), (0, 3))
        line4_key = self.generator._shape_key(line4)
        self.assertIn(line4_key, self.generator._free_polyominoes(4))
        self.assertNotIn(line4_key, self.generator._LEGACY_SHAPE_KEYS)

    def test_declared_canonical_shortcuts_fit_every_original_pair(self):
        expected = {
            "bbox_area_order",
            "bbox_semiperimeter_order",
            "boundary_perimeter_order",
            "adjacency_edges_order",
            "boundary_cells_order",
            "max_span_shape_order",
            "min_span_shape_order",
            "legacy_shape_lookup",
            "color_union",
            "global_color_frequency",
        }
        self.assertEqual(expected, set(self.generator.CANONICAL_SHORTCUTS))
        for name, shortcut in self.generator.CANONICAL_SHORTCUTS.items():
            for index, pair in enumerate(canonical_pairs()):
                with self.subTest(name=name, canonical_pair=index):
                    self.assertEqual(pair["output"], shortcut(pair["input"]))

    def test_slot_three_refutes_every_declared_canonical_shortcut(self):
        offsets = {"easy": 0, "medium": 1, "hard": 2}
        for band, offset in offsets.items():
            slot_three_index = (3 - offset) % 4
            for n_objects in (3, 4):
                grid = self.generator.generate(
                    918273,
                    slot_three_index,
                    difficulty=band,
                    grid_h=8,
                    grid_w=10,
                    n_objects=n_objects,
                )
                truth = self.generator._size_pack(grid)
                keys = {
                    self.generator._shape_key(obj["cells"])
                    for obj in self.generator._components(grid)
                }
                with self.subTest(band=band, n_objects=n_objects):
                    expected_sizes = [7, 8, 9] if n_objects == 3 else [1, 7, 8, 9]
                    observed_sizes = sorted(
                        len(obj["cells"])
                        for obj in self.generator._components(grid)
                    )
                    self.assertEqual(expected_sizes, observed_sizes)
                    for name, shortcut in self.generator.CANONICAL_SHORTCUTS.items():
                        if name not in {"color_union", "global_color_frequency"}:
                            self.assertNotEqual(truth, shortcut(grid), name)
                    self.assertTrue(keys - self.generator._LEGACY_SHAPE_KEYS)

    def test_size_nine_counterexample_is_valid_but_size_ten_is_rejected(self):
        offsets = {"easy": 0, "medium": 1, "hard": 2}
        for band, offset in offsets.items():
            slot_three_index = (3 - offset) % 4
            grid = self.generator.generate(
                271828,
                slot_three_index,
                difficulty=band,
                grid_h=8,
                grid_w=10,
                n_objects=3,
            )
            with self.subTest(band=band):
                self.assertEqual([], self.generator.self_check(grid, difficulty=band))
                self.assertIn(
                    9,
                    [len(obj["cells"]) for obj in self.generator._components(grid)],
                )

        oversize = copy.deepcopy(self.canonical[0])
        for r, c in (
            (3, 9),
            (3, 10),
            (4, 9),
            (4, 10),
            (4, 11),
            (5, 10),
            (5, 9),
        ):
            oversize[r][c] = 4
        self.assertTrue(
            any("1..9" in error for error in self.generator.self_check(oversize)),
            self.generator.self_check(oversize),
        )

    def test_generated_distribution_emits_broad_novel_morphology(self):
        classes_by_size = {size: set() for size in range(1, 10)}
        for band in ("easy", "medium", "hard"):
            for sample_index in range(120):
                grid = self.generator.generate(246810, sample_index, difficulty=band)
                self.assertEqual([], self.generator.self_check(grid, difficulty=band))
                for obj in self.generator._components(grid):
                    classes_by_size[len(obj["cells"])].add(
                        self.generator._shape_key(obj["cells"])
                    )

        all_classes = set().union(*classes_by_size.values())
        self.assertGreaterEqual(len(all_classes), 25)
        self.assertGreaterEqual(
            len(classes_by_size[4] - self.generator._LEGACY_SHAPE_KEYS), 2
        )
        self.assertGreaterEqual(
            len(classes_by_size[5] - self.generator._LEGACY_SHAPE_KEYS), 5
        )
        self.assertGreaterEqual(
            len(classes_by_size[6] - self.generator._LEGACY_SHAPE_KEYS), 10
        )
        self.assertGreaterEqual(len(classes_by_size[7]), 1)
        self.assertGreaterEqual(len(classes_by_size[8]), 1)
        self.assertGreaterEqual(len(classes_by_size[9]), 1)

    def test_shape_probe_reports_sliding_lesson_shortcut_survival(self):
        probe = load_shape_probe()
        self.assertEqual(
            set(self.generator.SEMANTIC_RIVALS),
            set(probe._fallback_rivals(self.generator)),
        )
        report = probe.run_census(self.generator, per_band=12, seed=161803)
        lesson = report["lesson_survival"]
        self.assertEqual(self.generator.EXAMPLES_NEEDED, lesson["n_demos"])
        self.assertEqual(27, lesson["windows"])
        self.assertEqual(
            set(self.generator.SEMANTIC_RIVALS),
            set(lesson["survivor_counts"]),
        )
        self.assertTrue(
            all(count == 0 for count in lesson["survivor_counts"].values()),
            lesson,
        )

    def test_counterexample_probe_reports_every_declared_shortcut(self):
        probe = load_shortcut_probe()
        report = probe.build_report(self.generator, GENERATOR_PATH)
        self.assertEqual(
            set(self.generator.CANONICAL_SHORTCUTS),
            set(report["shortcut_outputs"]),
        )
        self.assertTrue(report["all_shortcuts_refuted_across_cases"], report)
        self.assertEqual([], report["companion_case"]["self_check"])
        self.assertEqual([7, 8, 9], sorted(item["size"] for item in report["components"]))
        self.assertEqual([], report["self_check"])

    def test_candidate_rival_sweep_has_no_four_demo_survivor(self):
        probe = load_candidate_sweep()
        report = probe.run_sweep(
            self.generator,
            canonical_pairs(),
            seeds=range(2),
            samples_per_record=8,
        )
        self.assertEqual(64, report["canonical_fitting_candidates"])
        self.assertEqual(30, report["lesson_windows"])
        self.assertEqual([], report["survivors"], report)

    def test_declared_rivals_have_real_generated_witnesses(self):
        self.assertEqual(
            set(self.generator.SEMANTIC_RIVALS),
            set(self.generator.LESSON_COMPETITORS),
        )
        self.assertEqual(
            {
                "bbox_area_order",
                "bbox_semiperimeter_order",
                "boundary_perimeter_order",
                "adjacency_edges_order",
                "boundary_cells_order",
                "max_span_shape_order",
                "min_span_shape_order",
                "legacy_shape_lookup",
                "color_union",
                "global_color_frequency",
            },
            set(self.generator.CANONICAL_SHORTCUTS),
        )
        self.assertIn(
            "legacy_shape_lookup_conflict",
            self.generator.WITNESS_RIVALS,
        )
        self.assertIn(
            "strict_canonical_profile",
            self.generator.BRANCH_WITNESSES,
        )

        grids = [self.generator.generate(424242, index) for index in range(40)]
        for witness_name, rival_names in self.generator.WITNESS_RIVALS.items():
            firing = [
                grid
                for grid in grids
                if self.generator.SEMANTIC_WITNESSES[witness_name](grid)
            ]
            self.assertTrue(firing, witness_name)
            for grid in firing:
                truth = self.generator._size_pack(grid)
                self.assertTrue(
                    any(
                        self.generator.SEMANTIC_RIVALS[name](grid) != truth
                        for name in rival_names
                    ),
                    (witness_name, rival_names),
                )

    def test_disconnected_shared_color_with_distinct_sizes_is_valid(self):
        grid = [[0] * 10 for _ in range(8)]
        grid[0][0] = 2
        grid[3][0:2] = [7, 7]
        grid[6][0:3] = [2, 2, 2]
        self.assertEqual([], self.generator.self_check(grid))
        self.assertEqual(
            [[2, 0, 7, 7, 0, 2, 2, 2]],
            self.generator._size_pack(grid),
        )

    def test_slot_two_requires_connectivity_not_color_identity(self):
        offsets = {"easy": 0, "medium": 1, "hard": 2}
        for band, offset in offsets.items():
            for n_objects in (3, 4):
                for seed in (0, 17, 918273):
                    grid = self.generator.generate(
                        seed, (2 - offset) % 4, difficulty=band,
                        grid_h=8, grid_w=10, n_objects=n_objects,
                    )
                    comps = self.generator._components(grid)
                    with self.subTest(band=band, n_objects=n_objects, seed=seed):
                        self.assertLess(len({obj["color"] for obj in comps}), len(comps))
                        self.assertEqual([], self.generator.self_check(grid))
                        ordered = sorted(comps, key=lambda obj: len(obj["cells"]))
                        self.assertEqual(ordered[0]["color"], ordered[-1]["color"])
                        self.assertNotEqual(ordered[0]["color"], ordered[1]["color"])

    def test_connectivity_rivals_fit_all_canonical_examples(self):
        for grid in self.canonical:
            truth = self.generator._size_pack(grid)
            self.assertEqual(truth, self.generator._color_union_pack(grid))
            self.assertEqual(truth, self.generator._global_color_frequency_pack(grid))

    def test_shared_color_witnesses_refute_both_rivals_without_mutation(self):
        for band, offset in {"easy": 0, "medium": 1, "hard": 2}.items():
            for n_objects in (3, 4):
                grid = self.generator.generate(10101, (2-offset) % 4, difficulty=band,
                    grid_h=8, grid_w=10, n_objects=n_objects)
                original = copy.deepcopy(grid)
                truth = self.generator._size_pack(grid)
                for name in ("color_union", "global_color_frequency"):
                    self.assertNotEqual(truth, self.generator.SEMANTIC_RIVALS[name](grid))
                    self.assertTrue(self.generator.SEMANTIC_WITNESSES[name + "_conflict"](grid))
                self.assertEqual(original, grid)

    def test_unknown_override_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown override"):
            self.generator.generate(1, 0, typo_grid_h=8)

    def test_self_check_rejects_five_targeted_impostors(self):
        base = self.canonical[0]
        impostors = {}

        duplicate_size = copy.deepcopy(base)
        duplicate_size[2][10] = 0  # size-3 L becomes a size-2 domino
        impostors["duplicate_size"] = duplicate_size

        split_color = copy.deepcopy(base)
        split_color[4][5] = 0
        split_color[6][5] = 3  # color 3 now occupies two disconnected objects
        impostors["split_color_size_ties"] = split_color

        touching_objects = copy.deepcopy(base)
        touching_objects[1][1] = 0
        touching_objects[3][4] = 2  # directly touches the color-3 domino
        impostors["touching_objects"] = touching_objects

        oversize = copy.deepcopy(base)
        for r, c in (
            (3, 9),
            (3, 10),
            (4, 9),
            (4, 10),
            (4, 11),
            (5, 10),
            (5, 9),
        ):
            oversize[r][c] = 4  # connected size-10 feature, absent elsewhere
        impostors["size_ten"] = oversize

        two_objects = copy.deepcopy(base)
        two_objects[1][1] = 0
        impostors["two_objects"] = two_objects

        for name, grid in impostors.items():
            with self.subTest(name=name):
                self.assertTrue(self.generator.self_check(grid), name)

    def test_replay_is_deterministic_fresh_and_global_rng_pure(self):
        state_before = random.getstate()
        first = self.generator.generate(777, 19, difficulty="hard")
        state_after = random.getstate()
        second = self.generator.generate(777, 19, difficulty="hard")
        self.assertEqual(state_before, state_after)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9 if first[0][0] != 9 else 8
        third = self.generator.generate(777, 19, difficulty="hard")
        self.assertEqual(second, third)


if __name__ == "__main__":
    unittest.main()
