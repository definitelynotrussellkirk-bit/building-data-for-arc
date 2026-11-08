from __future__ import annotations

import json
import random
import unittest
from pathlib import Path

from reviewer_support import canonical_path, find_root, load_selected_generator


ROOT = find_root(__file__)
generator, _, _ = load_selected_generator("d833a288bd7d", root=ROOT)
from puzzle_generators import base


def as_grid(value):
    return [
        [int(cell) for cell in row] if isinstance(row, str) else list(row)
        for row in value
    ]


def canonical_pairs():
    with canonical_path(ROOT).open() as handle:
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


def reverse_rotation_rival(grid):
    scene = generator._analyze_scene(grid)
    turns = (scene["source_diag"] - scene["target_diag"]) % 4
    rotated = generator._rotate_shape(scene["shape"], turns)
    out = [[0 for _ in range(scene["w"])] for _ in range(scene["h"])]
    for dr, row in enumerate(rotated):
        for dc, value in enumerate(row):
            out[scene["r0"] + dr][scene["c0"] + dc] = value
    marker = scene["corners"][scene["target_diag"]]
    out[marker[0]][marker[1]] = 4
    return out


class D833a288bd7dGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = list(canonical_pairs())

    def test_all_canonical_pairs_match_rule_and_complete_profiles(self):
        self.assertEqual(len(self.pairs), 10)
        profiles = set()
        unique_inputs = set()
        rotations = set()
        for grid, expected in self.pairs:
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertTrue(generator.is_canonical_profile(grid))
            self.assertEqual(generator.rule_mirror(grid), expected)
            self.assertEqual(grid, before)
            profile = generator.canonical_profile_signature(grid)
            profiles.add(profile)
            unique_inputs.add(tuple(map(tuple, grid)))
            scene = generator._analyze_scene(grid)
            rotations.add(
                (scene["target_diag"] - scene["source_diag"]) % 4
            )
        self.assertEqual(profiles, generator._CANONICAL_PROFILE_SIGNATURES)
        self.assertEqual(len(profiles), 5)
        self.assertEqual(len(unique_inputs), 5)
        self.assertEqual(rotations, {1, 2, 3})

    def test_complete_profile_prior_is_substantive_stable_and_diverse(self):
        for start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                matches = 0
                profiles = set()
                grids = set()
                outputs = set()
                for offset in range(500):
                    seed = start + offset
                    grid = generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    grids.add(tuple(map(tuple, grid)))
                    outputs.add(
                        tuple(map(tuple, generator.rule_mirror(grid)))
                    )
                    if generator.is_canonical_profile(grid):
                        matches += 1
                        profiles.add(
                            generator.canonical_profile_signature(grid)
                        )
                self.assertGreaterEqual(matches, 25)
                self.assertLessEqual(matches, 65)
                self.assertEqual(
                    profiles,
                    generator._CANONICAL_PROFILE_SIGNATURES,
                )
                self.assertGreaterEqual(len(grids), 480)
                self.assertGreaterEqual(len(outputs), 480)

    def test_general_path_witnesses_every_axis_and_rotation(self):
        dimensions = set()
        sources = set()
        targets = set()
        rotations = set()
        shape_bitmaps = set()
        for dim in range(3, 7):
            for source in range(4):
                for target in range(4):
                    for seed in range(6):
                        grid = generator.generate(
                            seed,
                            seed * 31 + dim * 7 + source * 4 + target,
                            difficulty="hard",
                            grid_h=20,
                            grid_w=20,
                            shape_dim=dim,
                            source_diag=source,
                            target_diag=target,
                        )
                        self.assertEqual(generator.self_check(grid), [])
                        observed = generator.observe_overrides(grid)
                        self.assertEqual(observed["shape_dim"], dim)
                        self.assertEqual(observed["source_diag"], source)
                        self.assertEqual(observed["target_diag"], target)
                        dimensions.add(dim)
                        sources.add(source)
                        targets.add(target)
                        rotations.add((target - source) % 4)
                        shape_bitmaps.add(
                            generator._analyze_scene(grid)["shape"]
                        )
        self.assertEqual(dimensions, {3, 4, 5, 6})
        self.assertEqual(sources, {0, 1, 2, 3})
        self.assertEqual(targets, {0, 1, 2, 3})
        self.assertEqual(rotations, {0, 1, 2, 3})
        self.assertGreater(len(shape_bitmaps), 100)

    def test_boundaries_and_strict_controls(self):
        boundary_calls = (
            {"grid_h": 10},
            {"grid_h": 20},
            {"grid_w": 10},
            {"grid_w": 20},
            {"shape_dim": 3},
            {"shape_dim": 6},
            {"source_diag": 0},
            {"source_diag": 3},
            {"target_diag": 0},
            {"target_diag": 3},
            {
                "grid_h": 10,
                "grid_w": 10,
                "shape_dim": 6,
                "source_diag": 0,
                "target_diag": 3,
            },
            {
                "grid_h": 20,
                "grid_w": 20,
                "shape_dim": 3,
                "source_diag": 3,
                "target_diag": 0,
            },
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
            {"grid_h": "10"},
            {"grid_w": 10.0},
            {"shape_dim": True},
            {"source_diag": "0"},
            {"target_diag": 3.0},
            {"grid_h": 9},
            {"grid_w": 21},
            {"shape_dim": 2},
            {"shape_dim": 7},
            {"source_diag": -1},
            {"source_diag": 4},
            {"target_diag": -1},
            {"target_diag": 4},
            {"texture": "full_grid"},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **kwargs)

    def test_profile_and_forced_paths_record_exact_provenance(self):
        profiled = 0
        for band in ("easy", "medium", "hard"):
            for seed in range(240):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                finally:
                    base.set_ctx_observer(None)
                ctx = captured[-1]
                observed = generator.observe_overrides(grid)
                for key in generator.AXES:
                    self.assertEqual(ctx._drawn[key], observed[key])
                profiled += generator.is_canonical_profile(grid)
        self.assertGreater(profiled, 35)

    def test_self_check_rejects_structural_impostors(self):
        original, _ = self.pairs[0]
        scene = generator._analyze_scene(original)

        hole = [row[:] for row in original]
        hole[scene["r0"]][scene["c0"]] = 0
        self.assertTrue(
            any("densely fill" in error for error in generator.self_check(hole))
        )

        monochrome = [row[:] for row in original]
        for r, c, _ in scene["shape_cells"]:
            monochrome[r][c] = 1
        self.assertTrue(
            any("both colors" in error for error in generator.self_check(monochrome))
        )

        missing_source = [row[:] for row in original]
        sr, sc = scene["corners"][scene["source_diag"]]
        missing_source[sr][sc] = 0
        self.assertTrue(generator.self_check(missing_source))

        two_sources = [row[:] for row in original]
        other = (scene["source_diag"] + 1) % 4
        rr, cc = scene["corners"][other]
        cr, cc0 = scene["cluster"][0]
        two_sources[cr][cc0] = 0
        two_sources[rr][cc] = 4
        self.assertTrue(
            any("exactly one yellow" in error for error in generator.self_check(two_sources))
        )

        short_cluster = [row[:] for row in original]
        rr, cc = scene["cluster"][0]
        short_cluster[rr][cc] = 0
        self.assertTrue(
            any("three" in error for error in generator.self_check(short_cluster))
        )

        line_cluster = [row[:] for row in original]
        for rr, cc in scene["cluster"]:
            line_cluster[rr][cc] = 0
        for rr, cc in ((7, 0), (7, 1), (7, 2)):
            line_cluster[rr][cc] = 4
        self.assertTrue(
            any("L scaffold" in error for error in generator.self_check(line_cluster))
        )

        axis_cluster = [row[:] for row in original]
        rr, cc = scene["cluster"][0]
        axis_cluster[rr][cc] = 0
        axis_cluster[scene["center_r"]][0] = 4
        self.assertTrue(
            any("strict quadrant" in error for error in generator.self_check(axis_cluster))
        )

        extra_color = [row[:] for row in original]
        extra_color[0][9] = 2
        self.assertTrue(
            any("values" in error for error in generator.self_check(extra_color))
        )

    def test_lawful_source_recombination_is_not_canonical(self):
        grid, _ = self.pairs[0]
        hybrid = [row[:] for row in grid]
        scene = generator._analyze_scene(hybrid)
        old_r, old_c = scene["corners"][scene["source_diag"]]
        new_diag = 1
        new_r, new_c = scene["corners"][new_diag]
        hybrid[old_r][old_c] = 0
        hybrid[new_r][new_c] = 4
        self.assertEqual(generator.self_check(hybrid), [])
        self.assertNotEqual(
            generator.rule_mirror(hybrid),
            generator.rule_mirror(grid),
        )
        self.assertFalse(generator.is_canonical_profile(hybrid))

    def test_deterministic_fresh_returns_and_global_rng_isolation(self):
        random.seed(9981)
        state = random.getstate()
        first = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        first[0][0] = 99
        self.assertNotEqual(first, second)


    def test_seed_zero_indices_10_to_13_no_longer_teach_reverse_rotation(self):
        demos = []
        for sample_index in (10, 11, 12):
            grid = generator.generate(0, sample_index, difficulty="easy")
            demos.append({"input": grid, "output": generator.rule_mirror(grid)})
        query_grid = generator.generate(0, 13, difficulty="easy")
        query = {"input": query_grid, "output": generator.rule_mirror(query_grid)}

        turns = [
            (generator._analyze_scene(pair["input"])["target_diag"]
             - generator._analyze_scene(pair["input"])["source_diag"]) % 4
            for pair in demos
        ]
        self.assertTrue(any(turn in (1, 3) for turn in turns), turns)
        self.assertTrue(any(reverse_rotation_rival(pair["input"]) != pair["output"] for pair in demos))
        self.assertEqual(generator.lesson_identifiable(demos, query), [])

    def test_three_demo_windows_cover_an_odd_turn_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for start in range(4):
                demos = []
                for sample_index in range(start, start + generator.EXAMPLES_NEEDED):
                    grid = generator.generate(20261024 + start, sample_index, difficulty=band)
                    scene = generator._analyze_scene(grid)
                    self.assertEqual(
                        (scene["target_diag"] - scene["source_diag"]) % 4,
                        sample_index % 4,
                    )
                    demos.append({"input": grid, "output": generator.rule_mirror(grid)})
                query_grid = generator.generate(
                    20261024 + start,
                    start + generator.EXAMPLES_NEEDED,
                    difficulty=band,
                )
                query = {"input": query_grid, "output": generator.rule_mirror(query_grid)}
                self.assertEqual(generator.lesson_identifiable(demos, query), [])

    def test_semantic_hooks_name_and_witness_the_reverse_rotation_rival(self):
        grid = generator.generate(31, 1, difficulty="easy")
        self.assertEqual(generator.strict_canonical_like(grid), [])
        self.assertIn("reverse_rotation", generator.SEMANTIC_RIVALS)
        self.assertIn("odd_quarter_turn", generator.SEMANTIC_WITNESSES)
        self.assertEqual(generator.WITNESS_RIVALS["odd_quarter_turn"], ["reverse_rotation"])
        self.assertTrue(generator.SEMANTIC_WITNESSES["odd_quarter_turn"](grid))
        self.assertNotEqual(
            generator.SEMANTIC_RIVALS["reverse_rotation"](grid),
            generator.rule_mirror(grid),
        )


if __name__ == "__main__":
    unittest.main()
