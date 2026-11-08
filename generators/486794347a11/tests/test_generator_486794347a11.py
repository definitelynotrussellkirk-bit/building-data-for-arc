from __future__ import annotations

import copy
import importlib
import importlib.util
import json
import unittest
from pathlib import Path

gen = importlib.import_module("puzzle_generators.per_puzzle.486794347a11.generator")


ROOT = Path(__file__).resolve().parents[1]


class MarkerCountScaleGeneratorTests(unittest.TestCase):
    @staticmethod
    def shortcut_probe_module():
        path = ROOT / "workspace" / "marker_shortcut_probe.py"
        if not path.is_file():
            raise unittest.SkipTest("source-only workspace probe is not in this runtime")
        spec = importlib.util.spec_from_file_location("marker_shortcut_probe", path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"unable to load shortcut probe from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def marker_geometry_shortcut_factor(grid):
        """Plausible no-count rival induced by the phase-layout schedule."""
        analysis = gen._analysis_or_raise(grid)
        markers = analysis["markers"]
        has_adjacent_pair = any(
            right - left == 1 for left, right in zip(markers, markers[1:])
        )
        spans_both_edges = markers[0] == 0 and markers[-1] == analysis["width"] - 1
        return 3 if has_adjacent_pair or spans_both_edges else 2

    @staticmethod
    def marker_component_shortcut_factor(grid):
        """Plausible rival that counts contiguous marker runs, not marker cells."""
        markers = gen._analysis_or_raise(grid)["markers"]
        components = 1 + sum(
            right - left > 1 for left, right in zip(markers, markers[1:])
        )
        return 2 if components == 2 else 3

    @staticmethod
    def marker_span_gap_shortcut_factor(grid):
        """Depth-two proxy found by the deterministic marker-feature census."""
        markers = gen._analysis_or_raise(grid)["markers"]
        gaps = [right - left for left, right in zip(markers, markers[1:])]
        span = markers[-1] - markers[0]
        return 3 if span > 2 and min(gaps) <= 2 else 2

    def canonical_row(self):
        path = ROOT / "data/canonical/puzzles.jsonl"
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
        self.fail("canonical row not found")

    def test_canonical_pairs_are_accepted_and_mirrored(self):
        row = self.canonical_row()
        for pair in [*row["train"], *row["test"]]:
            self.assertEqual([], gen.self_check(pair["input"]))
            self.assertEqual(pair["output"], gen.rule_mirror(pair["input"]))

    def test_exact_boundary_overrides_are_observable(self):
        for shape_kind in gen.SHAPES:
            grid = gen.generate(
                19,
                7,
                difficulty="hard",
                grid_h=7,
                grid_w=8,
                n_markers=3,
                blob_color=9,
                shape_kind=shape_kind,
            )
            self.assertEqual([], gen.self_check(grid))
            self.assertEqual(
                {
                    "grid_h": 7,
                    "grid_w": 8,
                    "n_markers": 3,
                    "blob_color": 9,
                    "shape_kind": shape_kind,
                },
                gen.observe_overrides(grid),
            )

    def test_unknown_override_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown override axis"):
            gen.generate(0, 0, typo_axis=1)

    def test_schedule_breaks_canonical_shortcuts_in_every_three_draw_window(self):
        for start in range(24):
            grids = [gen.generate(41, start + offset, difficulty="medium") for offset in range(3)]
            self.assertEqual({2, 3}, {gen.observe_overrides(grid)["n_markers"] for grid in grids})
            self.assertTrue(any(gen._height_decoupled(grid) for grid in grids))
            self.assertTrue(any(gen._colour_decoupled(grid) for grid in grids))
            self.assertTrue(any(gen._irregular_markers(grid) for grid in grids))

    def test_schedule_breaks_marker_geometry_shortcut_in_every_three_draw_window(self):
        for difficulty in (None, "easy", "medium", "hard"):
            for seed in (0, 1, 17, 41):
                for start in range(24):
                    grids = [
                        gen.generate(seed, start + offset, difficulty=difficulty)
                        for offset in range(3)
                    ]
                    self.assertTrue(
                        any(
                            self.marker_geometry_shortcut_factor(grid)
                            != gen.observe_overrides(grid)["n_markers"]
                            for grid in grids
                        ),
                        (difficulty, seed, start),
                    )

    def test_marker_geometry_shortcut_is_part_of_semantic_contract(self):
        rival = "marker_geometry_scale"
        witness = "marker_geometry_decoupling"
        self.assertIn(rival, gen.SEMANTIC_RIVALS)
        self.assertIn(rival, gen.LESSON_COMPETITORS)
        self.assertIn(rival, gen.CANONICAL_SHORTCUTS)
        self.assertEqual([rival], gen.WITNESS_RIVALS[witness])

        for sample_index in (0, 2):
            grid = gen.generate(17, sample_index, difficulty="medium")
            self.assertTrue(gen.SEMANTIC_WITNESSES[witness](grid))
            self.assertNotEqual(gen.rule_mirror(grid), gen.SEMANTIC_RIVALS[rival](grid))

    def test_schedule_breaks_marker_component_shortcut_in_every_three_draw_window(self):
        for difficulty in (None, "easy", "medium", "hard"):
            for seed in (0, 1, 17, 41):
                for start in range(24):
                    grids = [
                        gen.generate(seed, start + offset, difficulty=difficulty)
                        for offset in range(3)
                    ]
                    self.assertTrue(
                        any(
                            self.marker_component_shortcut_factor(grid)
                            != gen.observe_overrides(grid)["n_markers"]
                            for grid in grids
                        ),
                        (difficulty, seed, start),
                    )

    def test_marker_component_shortcut_is_part_of_semantic_contract(self):
        rival = "marker_component_scale"
        witness = "marker_component_decoupling"
        self.assertIn(rival, gen.SEMANTIC_RIVALS)
        self.assertIn(rival, gen.LESSON_COMPETITORS)
        self.assertIn(rival, gen.CANONICAL_SHORTCUTS)
        self.assertEqual([rival], gen.WITNESS_RIVALS[witness])

        for sample_index in (0, 2):
            grid = gen.generate(17, sample_index, difficulty="medium")
            self.assertTrue(gen.SEMANTIC_WITNESSES[witness](grid))
            self.assertNotEqual(gen.rule_mirror(grid), gen.SEMANTIC_RIVALS[rival](grid))

    def test_schedule_breaks_marker_span_gap_shortcut_in_every_four_draw_window(self):
        for difficulty in (None, "easy", "medium", "hard"):
            for seed in (0, 1, 17, 41):
                for start in range(24):
                    grids = [
                        gen.generate(seed, start + offset, difficulty=difficulty)
                        for offset in range(4)
                    ]
                    self.assertTrue(
                        any(
                            self.marker_span_gap_shortcut_factor(grid)
                            != gen.observe_overrides(grid)["n_markers"]
                            for grid in grids
                        ),
                        (difficulty, seed, start),
                    )

    def test_declared_lesson_size_covers_slowest_marker_rival(self):
        self.assertGreaterEqual(gen.EXAMPLES_NEEDED, 4)
        rivals = (
            self.marker_geometry_shortcut_factor,
            self.marker_component_shortcut_factor,
            self.marker_span_gap_shortcut_factor,
        )
        for difficulty in (None, "easy", "medium", "hard"):
            for seed in (0, 1, 17, 41):
                for start in range(24):
                    grids = [
                        gen.generate(seed, start + offset, difficulty=difficulty)
                        for offset in range(gen.EXAMPLES_NEEDED)
                    ]
                    for rival in rivals:
                        self.assertTrue(
                            any(
                                rival(grid)
                                != gen.observe_overrides(grid)["n_markers"]
                                for grid in grids
                            ),
                            (rival.__name__, difficulty, seed, start),
                        )

    def test_marker_span_gap_shortcut_is_part_of_semantic_contract(self):
        rival = "marker_span_gap_scale"
        witness = "marker_span_gap_decoupling"
        self.assertIn(rival, gen.SEMANTIC_RIVALS)
        self.assertIn(rival, gen.LESSON_COMPETITORS)
        self.assertIn(rival, gen.CANONICAL_SHORTCUTS)
        self.assertEqual([rival], gen.WITNESS_RIVALS[witness])

        for sample_index in (1, 5):
            grid = gen.generate(17, sample_index, difficulty="medium")
            self.assertTrue(gen.SEMANTIC_WITNESSES[witness](grid))
            self.assertNotEqual(gen.rule_mirror(grid), gen.SEMANTIC_RIVALS[rival](grid))

    def test_self_check_rejects_targeted_impostors(self):
        base = gen.generate(7, 2, difficulty="medium")

        no_markers = copy.deepcopy(base)
        no_markers[0] = [0] * len(no_markers[0])
        self.assertTrue(gen.self_check(no_markers))

        marker_below = copy.deepcopy(base)
        marker_below[1][0] = 1
        self.assertTrue(gen.self_check(marker_below))

        solid_bbox = copy.deepcopy(base)
        analysis = gen._analysis_or_raise(base)
        r1, c1, r2, c2 = analysis["bbox"]
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                solid_bbox[row][col] = analysis["body_color"]
        self.assertTrue(gen.self_check(solid_bbox))

        second_colour = copy.deepcopy(base)
        row, col = analysis["body_cells"][0]
        second_colour[row][col] = 9 if analysis["body_color"] != 9 else 8
        self.assertTrue(gen.self_check(second_colour))

    def test_fresh_deterministic_returns(self):
        first = gen.generate(123, 11, difficulty="hard")
        second = gen.generate(123, 11, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9
        self.assertNotEqual(first, second)

    def test_shortcut_probe_detects_exact_univariate_feature(self):
        probe = self.shortcut_probe_module()
        rows = [
            {"span": 1, "touches_edge": 0},
            {"span": 2, "touches_edge": 1},
            {"span": 3, "touches_edge": 0},
            {"span": 4, "touches_edge": 1},
        ]
        labels = [2, 2, 3, 3]
        exact = probe.exact_univariate_features(rows, labels)
        self.assertIn("span", exact)
        self.assertNotIn("touches_edge", exact)

    def test_shortcut_probe_features_do_not_include_marker_count(self):
        probe = self.shortcut_probe_module()
        grid = gen.generate(7, 7, difficulty="medium")
        features = probe.marker_features(grid, gen._analysis_or_raise)
        self.assertNotIn("n_markers", features)
        self.assertNotIn("marker_count", features)
        self.assertEqual(2, features["components"])

    def test_shortcut_probe_result_is_json_serializable(self):
        probe = self.shortcut_probe_module()
        result = probe.run_probe(
            "puzzle_generators.per_puzzle.486794347a11.generator",
            seeds=2,
            samples=8,
        )
        json.dumps(result, sort_keys=True)


if __name__ == "__main__":
    unittest.main()
