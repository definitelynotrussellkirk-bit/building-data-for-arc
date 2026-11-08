"""Focused regression tests for the per-color bounding-box generator."""

from __future__ import annotations

import importlib.util
import random
import unittest
from pathlib import Path

from puzzle_generators import base
from reviewer_support import canonical_pairs as read_canonical_pairs, find_root


ROOT = find_root(__file__)
_GENERATOR_CANDIDATES = (
    ROOT / "puzzle_generators" / "per_puzzle" / "7f666a786bf3" / "generator.py",
    ROOT / "generators" / "7f666a786bf3" / "generator.py",
)
GENERATOR_PATH = next((path for path in _GENERATOR_CANDIDATES if path.is_file()), None)
if GENERATOR_PATH is None:
    raise FileNotFoundError(f"selected generator missing under {ROOT}")


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_7f666a786bf3",
        GENERATOR_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    for pair in read_canonical_pairs(
        "7f666a786bf3", root=ROOT, labeled_only=True
    ):
        yield pair["input"], pair["output"]


class BoundingBoxPerColorGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = load_generator()
        cls.pairs = list(canonical_pairs())

    def test_all_canonical_pairs_are_accepted_and_exact(self):
        self.assertEqual(len(self.pairs), 4)
        signatures = set()
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(self.generator.self_check(grid), [])
            self.assertEqual(self.generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)
            self.assertTrue(self.generator.is_canonical_profile(grid))
            signatures.add(
                self.generator.canonical_profile_signature(grid)
            )
        self.assertEqual(
            signatures,
            self.generator._CANONICAL_PROFILE_SIGNATURES,
        )
        self.assertEqual(len(signatures), 4)

    def test_complete_profile_prior_reaches_every_linked_signature(self):
        for start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                counts = {
                    signature: 0
                    for signature in self.generator._CANONICAL_PROFILE_SIGNATURES
                }
                inputs = set()
                outputs = set()
                for offset in range(300):
                    seed = start + offset
                    grid = self.generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                    self.assertEqual(self.generator.self_check(grid), [])
                    inputs.add(tuple(map(tuple, grid)))
                    outputs.add(
                        tuple(map(tuple, self.generator.rule_mirror(grid)))
                    )
                    signature = self.generator.canonical_profile_signature(grid)
                    if signature in counts:
                        counts[signature] += 1
                with self.subTest(start=start, band=band, counts=counts):
                    self.assertGreaterEqual(sum(counts.values()), 90)
                    self.assertLessEqual(sum(counts.values()), 155)
                    self.assertTrue(all(count > 0 for count in counts.values()))
                    self.assertGreaterEqual(len(inputs), 270)
                    self.assertGreaterEqual(len(outputs), 270)

    def test_general_path_covers_counts_edges_and_marker_grammars(self):
        seen_counts = set()
        seen_edges = set()
        seen_styles = set()
        seen_box_shapes = set()
        seen_colors = set()
        for markers in (2, 3, 4):
            for n_colors in (2, 3, 4):
                for edge_touching in (False, True):
                    for seed in range(20):
                        sample_index = seed * 3 + markers
                        grid = self.generator.generate(
                            seed,
                            sample_index,
                            difficulty="hard",
                            grid_h=18,
                            grid_w=20,
                            n_colors=n_colors,
                            markers_per_color=markers,
                            edge_touching=edge_touching,
                        )
                        self.assertEqual(self.generator.self_check(grid), [])
                        observed = self.generator.observe_overrides(grid)
                        self.assertEqual(observed["n_colors"], n_colors)
                        self.assertEqual(
                            observed["markers_per_color"], markers
                        )
                        self.assertEqual(
                            observed["edge_touching"], edge_touching
                        )
                        seen_counts.add((n_colors, markers))
                        seen_edges.add(edge_touching)
                        scene = self.generator._analyze_scene(grid)
                        for color, cells in scene["by_color"].items():
                            box = scene["boxes"][color]
                            seen_styles.add(
                                self.generator._marker_style(cells, box)
                            )
                            seen_box_shapes.add(
                                (box[2] - box[0] + 1, box[3] - box[1] + 1)
                            )
                            seen_colors.add(color)
        self.assertEqual(
            seen_counts,
            {
                (n_colors, markers)
                for n_colors in (2, 3, 4)
                for markers in (2, 3, 4)
            },
        )
        self.assertEqual(seen_edges, {False, True})
        self.assertEqual(
            seen_styles,
            {"opposite_corners", "split_extrema", "interior"},
        )
        self.assertGreaterEqual(len(seen_box_shapes), 8)
        self.assertEqual(seen_colors, set(range(1, 10)))

    def test_all_boundary_overrides_survive_every_difficulty_band(self):
        calls = (
            {"grid_h": 6},
            {"grid_h": 18},
            {"grid_w": 8},
            {"grid_w": 20},
            {"n_colors": 2},
            {"n_colors": 4},
            {"markers_per_color": 2},
            {"markers_per_color": 4},
            {"edge_touching": False},
            {"edge_touching": True},
            {
                "grid_h": 6,
                "grid_w": 8,
                "n_colors": 4,
                "markers_per_color": 4,
                "edge_touching": False,
            },
            {
                "grid_h": 6,
                "grid_w": 8,
                "n_colors": 4,
                "markers_per_color": 4,
                "edge_touching": True,
            },
            {
                "grid_h": 18,
                "grid_w": 20,
                "n_colors": 2,
                "markers_per_color": 2,
                "edge_touching": False,
            },
        )
        for band in ("easy", "medium", "hard"):
            for index, kwargs in enumerate(calls):
                grid = self.generator.generate(
                    97,
                    131 + index,
                    difficulty=band,
                    **kwargs,
                )
                self.assertEqual(self.generator.self_check(grid), [])
                observed = self.generator.observe_overrides(grid)
                for name, expected in kwargs.items():
                    self.assertEqual(observed[name], expected)

        bad_calls = (
            {"difficulty": "expert"},
            {"unknown": 1},
            {"grid_h": 5},
            {"grid_h": 19},
            {"grid_w": 7},
            {"grid_w": 21},
            {"n_colors": 1},
            {"n_colors": 5},
            {"markers_per_color": 1},
            {"markers_per_color": 5},
            {"edge_touching": 1},
            {"grid_h": "6"},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    self.generator.generate(0, 0, **kwargs)

    def test_keyed_provenance_matches_every_observable_axis(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(120):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = self.generator.generate(
                        seed,
                        seed * 19 + 7,
                        difficulty=band,
                    )
                finally:
                    base.set_ctx_observer(None)
                observed = self.generator.observe_overrides(grid)
                recorded = captured[-1].recorded_draws()
                for name in self.generator.AXES:
                    self.assertEqual(recorded[name], observed[name])

        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = self.generator.generate(
                17,
                23,
                difficulty="easy",
                grid_h=6,
                grid_w=20,
                n_colors=4,
                markers_per_color=4,
                edge_touching=True,
            )
        finally:
            base.set_ctx_observer(None)
        self.assertEqual(
            {
                name: value
                for name, value in captured[-1].recorded_draws().items()
                if name in self.generator.AXES
            },
            self.generator.observe_overrides(grid),
        )

    def test_self_check_rejects_targeted_structural_impostors(self):
        blank = [[0] * 10 for _ in range(7)]
        self.assertTrue(
            any(
                "2..4 nonzero" in error
                for error in self.generator.self_check(blank)
            )
        )

        unequal = [row[:] for row in self.pairs[0][0]]
        unequal[1][2] = 5
        self.assertEqual(self.generator.self_check(unequal), [])

        too_many = [row[:] for row in unequal]
        too_many[2][1] = 5
        too_many[2][2] = 5
        self.assertTrue(
            any(
                "2..4 sparse markers" in error
                for error in self.generator.self_check(too_many)
            )
        )

        overlapping = [[0] * 10 for _ in range(8)]
        overlapping[1][1] = 3
        overlapping[3][4] = 3
        overlapping[2][3] = 7
        overlapping[5][6] = 7
        self.assertTrue(
            any(
                "overlap" in error
                for error in self.generator.self_check(overlapping)
            )
        )

        solid = [[0] * 10 for _ in range(8)]
        for r in (1, 2):
            for c in (1, 2):
                solid[r][c] = 3
        solid[4][5] = 7
        solid[6][7] = 7
        self.assertTrue(
            any(
                "background cell" in error
                for error in self.generator.self_check(solid)
            )
        )

        one_dimensional = [[0] * 10 for _ in range(8)]
        one_dimensional[1][1] = 3
        one_dimensional[1][4] = 3
        one_dimensional[4][5] = 7
        one_dimensional[6][7] = 7
        self.assertTrue(
            any(
                "two rows and two columns" in error
                for error in self.generator.self_check(one_dimensional)
            )
        )

    def test_cross_profile_recombination_is_rejected_by_teaching_gate(self):
        # Each color group is individually a canonical diagonal pair, but the
        # two complete bboxes have been recombined so they overlap.  The Racket
        # program can execute this input, yet it is not a lawful lesson because
        # overwrite order would decide the overlap color.
        recombined = [[0] * 10 for _ in range(8)]
        recombined[1][1] = 5
        recombined[3][4] = 5
        recombined[2][3] = 8
        recombined[4][5] = 8
        errors = self.generator.self_check(recombined)
        self.assertTrue(any("overlap" in error for error in errors))
        self.assertIsNone(
            self.generator.canonical_profile_signature(recombined)
        )


    def test_mixed_marker_counts_are_lawful_and_refute_shared_count_shortcut(self):
        witness = [[0] * 10 for _ in range(8)]
        witness[1][1] = 3
        witness[3][3] = 3
        witness[4][6] = 7
        witness[5][6] = 7
        witness[6][8] = 7

        self.assertEqual(self.generator.self_check(witness), [])
        observed = self.generator.observe_overrides(witness)
        self.assertEqual(observed["markers_per_color"], 2)
        self.assertTrue(observed["mixed_marker_counts"])

        rival = self.generator.CANONICAL_SHORTCUTS["uniform_marker_count"]
        self.assertTrue(
            all(rival(grid) == expected for grid, expected in self.pairs)
        )
        self.assertNotEqual(rival(witness), self.generator.rule_mirror(witness))
        self.assertTrue(
            self.generator.SEMANTIC_WITNESSES["mixed_marker_counts"](witness)
        )

    def test_default_schedule_and_every_query_rotation_refute_all_competitors(self):
        self.assertEqual(self.generator.EXAMPLES_NEEDED, 3)
        self.assertEqual(self.generator.LESSON_SCHEDULE_PERIOD, 2)
        for band in ("easy", "medium", "hard"):
            for start in range(self.generator.LESSON_SCHEDULE_PERIOD):
                pairs = []
                mixed_flags = []
                for sample_index in range(start, start + 4):
                    grid = self.generator.generate(811, sample_index, difficulty=band)
                    mixed_flags.append(
                        self.generator.observe_overrides(grid)["mixed_marker_counts"]
                    )
                    pairs.append(
                        {"input": grid, "output": self.generator.rule_mirror(grid)}
                    )
                self.assertEqual(sum(mixed_flags), 2)
                for query_index, query in enumerate(pairs):
                    demos = [
                        pair for index, pair in enumerate(pairs)
                        if index != query_index
                    ]
                    self.assertEqual(
                        self.generator.lesson_identifiable(demos, query), []
                    )
                    for name, rival in self.generator.LESSON_COMPETITORS.items():
                        self.assertFalse(
                            all(rival(pair["input"]) == pair["output"] for pair in demos),
                            msg=f"{band=} {start=} {query_index=} {name=}",
                        )

    def test_mixed_marker_count_override_is_exact_and_incompatibility_is_explicit(self):
        for band in ("easy", "medium", "hard"):
            for floor in (2, 3):
                grid = self.generator.generate(101, 8, difficulty=band,
                    grid_h=18, grid_w=20, n_colors=4,
                    markers_per_color=floor, mixed_marker_counts=True,
                    edge_touching=True)
                observed = self.generator.observe_overrides(grid)
                self.assertEqual(observed["markers_per_color"], floor)
                self.assertTrue(observed["mixed_marker_counts"])
                scene = self.generator._analyze_scene(grid)
                counts = {len(cells) for cells in scene["by_color"].values()}
                self.assertGreater(len(counts), 1)
                self.assertEqual(min(counts), floor)

            uniform = self.generator.generate(102, 9, difficulty=band,
                markers_per_color=4, mixed_marker_counts=False)
            self.assertEqual(
                self.generator.observe_overrides(uniform)["markers_per_color"], 4
            )
            self.assertFalse(
                self.generator.observe_overrides(uniform)["mixed_marker_counts"]
            )

        with self.assertRaisesRegex(ValueError, "mixed_marker_counts.*markers_per_color"):
            self.generator.generate(0, 0, markers_per_color=4,
                                    mixed_marker_counts=True)

    def test_default_distribution_exposes_both_count_modes_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            flags = []
            for sample_index in range(40):
                grid = self.generator.generate(401, sample_index, difficulty=band)
                flags.append(
                    self.generator.observe_overrides(grid)["mixed_marker_counts"]
                )
            self.assertEqual(flags[::2], [True] * 20)
            self.assertEqual(flags[1::2], [False] * 20)

    def test_semantic_contract_is_executable_and_strict(self):
        for seed in range(60):
            grid = self.generator.generate(seed, seed, difficulty="medium")
            self.assertEqual(self.generator.strict_canonical_like(grid), [])
        self.assertEqual(
            set(self.generator.WITNESS_RIVALS["mixed_marker_counts"]),
            {"uniform_marker_count"},
        )
        self.assertIn("uniform_marker_count", self.generator.SEMANTIC_RIVALS)
        self.assertIn("uniform_marker_count", self.generator.CANONICAL_SHORTCUTS)
        self.assertIn("uniform_marker_count", self.generator.LESSON_COMPETITORS)

    def test_determinism_fresh_returns_input_purity_and_global_rng(self):
        random.seed(20260724)
        before_state = random.getstate()
        first = self.generator.generate(19, 31, difficulty="medium")
        after_state = random.getstate()
        second = self.generator.generate(19, 31, difficulty="medium")
        self.assertEqual(before_state, after_state)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(
            all(left is not right for left, right in zip(first, second))
        )

        original = [row[:] for row in first]
        output_a = self.generator.rule_mirror(first)
        unrelated = self.generator.generate(20, 32, difficulty="hard")
        self.generator.rule_mirror(unrelated)
        output_b = self.generator.rule_mirror(first)
        self.assertEqual(first, original)
        self.assertEqual(output_a, output_b)
        self.assertIsNot(output_a, output_b)


if __name__ == "__main__":
    unittest.main()
