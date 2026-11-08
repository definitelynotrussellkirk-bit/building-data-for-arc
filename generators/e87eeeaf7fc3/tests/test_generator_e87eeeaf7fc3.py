from __future__ import annotations

import json
import random
import unittest
from collections import Counter
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.e87eeeaf7fc3 import generator


ROOT = Path(__file__).resolve().parents[1]


def as_grid(value):
    return [
        [int(cell) for cell in row] if isinstance(row, str) else list(row)
        for row in value
    ]


def canonical_pairs():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != generator.TASK_ID:
                continue
            for split in ("train", "test"):
                value = row.get(split)
                pairs = value if isinstance(value, list) else [value]
                for pair in pairs:
                    if pair:
                        yield as_grid(pair["input"]), as_grid(pair["output"])


class E87eeeaf7fc3GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())

    def test_all_public_pairs_match_rule_and_complete_profiles(self):
        self.assertEqual(len(self.pairs), 5)
        profiles = set()
        ranks = set()
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)
            self.assertTrue(generator.is_canonical_profile(grid))
            signature = generator.canonical_profile_signature(grid)
            profiles.add(signature)
            ranks.add(signature[3])
        self.assertEqual(
            profiles,
            generator._CANONICAL_PROFILE_SIGNATURES,
        )
        self.assertEqual(ranks, {0, 1, 2, 3})

    def test_complete_profile_prior_is_stable_on_two_ranges(self):
        for start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                matches = 0
                profiles = set()
                inputs = set()
                outputs = set()
                for offset in range(600):
                    seed = start + offset
                    grid = generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    inputs.add(tuple(map(tuple, grid)))
                    outputs.add(
                        tuple(map(tuple, generator.rule_mirror(grid)))
                    )
                    if generator.is_canonical_profile(grid):
                        matches += 1
                        profiles.add(
                            generator.canonical_profile_signature(grid)
                        )
                self.assertGreaterEqual(matches, 30)
                self.assertLessEqual(matches, 95)
                self.assertEqual(
                    profiles,
                    generator._CANONICAL_PROFILE_SIGNATURES,
                )
                self.assertGreaterEqual(len(inputs), 570)
                self.assertGreaterEqual(len(outputs), 570)

    def test_general_path_covers_tree_loop_and_marker_roles(self):
        observed_ranks = {"tree": set(), "looped": set()}
        off_path_counts = set()
        for kind in generator._GRAPH_KINDS:
            for seed in range(300):
                grid = generator.generate(
                    seed,
                    seed * 29 + 3,
                    difficulty="hard",
                    grid_h=18,
                    grid_w=19,
                    graph_kind=kind,
                )
                self.assertEqual(generator.self_check(grid), [])
                scene = generator._analyze_scene(grid)
                observed_ranks[kind].add(scene["cycle_rank"])
                off_path_counts.add(len(scene["off_path"]))
                self.assertEqual(
                    set(scene["path_23"]) & set(scene["path_34"]),
                    {scene["markers"][3]},
                )
                self.assertIn(
                    scene["degrees"][scene["markers"][2]],
                    (1, 2),
                )
                self.assertIn(
                    scene["degrees"][scene["markers"][3]],
                    (2, 3),
                )
                self.assertEqual(
                    scene["degrees"][scene["markers"][4]],
                    1,
                )
        self.assertEqual(observed_ranks["tree"], {0})
        self.assertEqual(observed_ranks["looped"], {1, 2, 3, 4})
        self.assertGreaterEqual(len(off_path_counts), 12)

    def test_rule_paints_only_ordered_route_and_clears_other_open_cells(self):
        for kind in generator._GRAPH_KINDS:
            for seed in range(120):
                grid = generator.generate(
                    seed,
                    seed * 31 + 7,
                    difficulty="medium",
                    graph_kind=kind,
                )
                scene = generator._analyze_scene(grid)
                output = generator.rule_mirror(grid)
                for r, row in enumerate(grid):
                    for c, value in enumerate(row):
                        if value == 5:
                            expected = 5
                        elif (r, c) in scene["route"]:
                            expected = 8
                        else:
                            expected = 0
                        self.assertEqual(output[r][c], expected)
                self.assertGreaterEqual(len(scene["off_path"]), 4)
                self.assertTrue(
                    all(output[r][c] == 0 for r, c in scene["off_path"])
                )

    def test_boundaries_and_strict_controls(self):
        boundary_calls = (
            {"grid_h": 9},
            {"grid_h": 20},
            {"grid_w": 9},
            {"grid_w": 20},
            {"graph_kind": "tree"},
            {"graph_kind": "looped"},
            {"grid_h": 9, "grid_w": 9, "graph_kind": "looped"},
            {"grid_h": 20, "grid_w": 20, "graph_kind": "tree"},
        )
        for kwargs in boundary_calls:
            for band in ("easy", "medium", "hard"):
                grid = generator.generate(17, 23, difficulty=band, **kwargs)
                self.assertEqual(generator.self_check(grid), [])
                observed = generator.observe_overrides(grid)
                for key, value in kwargs.items():
                    self.assertEqual(observed[key], value)

        bad_calls = (
            {"difficulty": "expert"},
            {"bogus": 1},
            {"grid_h": "9"},
            {"grid_w": 9.0},
            {"grid_h": True},
            {"graph_kind": 1},
            {"grid_h": 8},
            {"grid_h": 21},
            {"grid_w": 8},
            {"grid_w": 21},
            {"graph_kind": "maze"},
            {"texture": "no_markers"},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **kwargs)

    def test_profile_default_and_forced_paths_record_exact_provenance(self):
        profiled = 0
        for band in ("easy", "medium", "hard"):
            for seed in range(240):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = generator.generate(
                        seed,
                        seed * 37 + 5,
                        difficulty=band,
                    )
                finally:
                    base.set_ctx_observer(None)
                ctx = captured[-1]
                observed = generator.observe_overrides(grid)
                for key in generator.AXES:
                    self.assertEqual(ctx._drawn[key], observed[key])
                profiled += generator.is_canonical_profile(grid)
        self.assertGreater(profiled, 40)

        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = generator.generate(
                91,
                117,
                difficulty="easy",
                grid_h=20,
                grid_w=9,
                graph_kind="looped",
            )
        finally:
            base.set_ctx_observer(None)
        self.assertEqual(
            captured[-1]._drawn,
            generator.observe_overrides(grid),
        )
        self.assertEqual(
            captured[-1]._override_used,
            {"grid_h": 20, "grid_w": 9, "graph_kind": "looped"},
        )

    def test_self_check_rejects_structural_impostors(self):
        valid = generator.generate(
            1,
            2,
            grid_h=13,
            grid_w=13,
            graph_kind="looped",
        )
        mutations = []

        missing_marker = [row[:] for row in valid]
        scene = generator._analyze_scene(missing_marker)
        r, c = scene["markers"][3]
        missing_marker[r][c] = 0
        mutations.append(missing_marker)

        duplicate_marker = [row[:] for row in valid]
        r, c = next(iter(scene["off_path"]))
        duplicate_marker[r][c] = 2
        mutations.append(duplicate_marker)

        border_hole = [row[:] for row in valid]
        border_hole[0][1] = 0
        mutations.append(border_hole)

        bad_color = [row[:] for row in valid]
        bad_color[1][1] = 7
        mutations.append(bad_color)

        disconnected = [row[:] for row in valid]
        disconnected[1][1] = 0
        mutations.append(disconnected)

        ragged = [row[:] for row in valid]
        ragged[-1] = ragged[-1][:-1]
        mutations.append(ragged)

        for mutation in mutations:
            self.assertTrue(generator.self_check(mutation), mutation)

    def test_lawful_cross_profile_recombination_is_rejected(self):
        # Keep profile 0's exact 12x12 tree/open-count/degree topology, but
        # splice in profile 1's (8, 5) path lengths and (1, 3, 1) marker
        # degrees. Marginal checks all pass; the linked public profile must not.
        cells = set(generator._PROFILE_FALLBACKS[0][0])
        markers = ((10, 8), (5, 10), (1, 10))
        grid = generator._paint_scene(12, 12, cells, markers)
        self.assertEqual(generator.self_check(grid), [])
        signature = generator.canonical_profile_signature(grid)
        self.assertEqual(signature[:5], generator._profile_signature(
            generator._PROFILE_SPECS[0]
        )[:5])
        self.assertEqual(signature[5:7], (8, 5))
        self.assertEqual(signature[-1], (1, 3, 1))
        self.assertFalse(generator.is_canonical_profile(grid))
        self.assertNotIn(
            signature,
            generator._CANONICAL_PROFILE_SIGNATURES,
        )

    def test_bands_are_ordered_and_both_graph_kinds_are_live(self):
        means = {}
        for band in ("easy", "medium", "hard"):
            areas = []
            kinds = Counter()
            for seed in range(500):
                grid = generator.generate(
                    seed,
                    seed * 43 + 11,
                    difficulty=band,
                )
                areas.append(len(grid) * len(grid[0]))
                kinds[generator.observe_overrides(grid)["graph_kind"]] += 1
            means[band] = sum(areas) / len(areas)
            self.assertGreaterEqual(kinds["tree"], 150)
            self.assertGreaterEqual(kinds["looped"], 150)
        self.assertLess(means["easy"], means["medium"])
        self.assertLess(means["medium"], means["hard"])

    def test_deterministic_fresh_returns_and_global_rng_isolation(self):
        random.seed(9981)
        state = random.getstate()
        first = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))


if __name__ == "__main__":
    unittest.main()
