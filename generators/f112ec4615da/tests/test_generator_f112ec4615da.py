from __future__ import annotations

import hashlib
import json
import random
import unittest
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.f112ec4615da import generator


ROOT = Path(__file__).resolve().parents[1]


def canonical_row():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == generator.TASK_ID:
                return row
    raise KeyError(generator.TASK_ID)


def canonical_pairs():
    row = canonical_row()
    return list(row["train"]) + list(row["test"])


def independent_rule(grid):
    height = len(grid)
    width = len(grid[0])
    half_h = height // 2
    half_w = width // 2
    output = [[0] * half_w for _ in range(half_h)]
    for row in range(half_h):
        for col in range(half_w):
            values = (
                grid[row][col],
                grid[row + half_h][col + half_w],
                grid[row + half_h][col],
                grid[row][col + half_w],
            )
            value = 0
            for candidate in values:
                if candidate != 0:
                    value = candidate
            output[row][col] = value
    return output


class F112ec4615daGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = canonical_row()
        cls.pairs = canonical_pairs()

    def test_all_public_pairs_match_rule_and_complete_profiles(self):
        self.assertEqual(len(self.pairs), 7)
        profiles = set()
        for pair in self.pairs:
            grid = pair["input"]
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(independent_rule(grid), pair["output"])
            self.assertEqual(generator.rule_mirror(grid), pair["output"])
            self.assertEqual(grid, before)
            signature = generator.canonical_profile_signature(grid)
            self.assertIsNotNone(signature)
            profiles.add(signature)
        self.assertEqual(
            profiles,
            generator._CANONICAL_PROFILE_SIGNATURES,
        )

    def test_complete_profile_prior_is_stable_and_diverse(self):
        for start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                matches = 0
                profiles = set()
                pairs = set()
                for offset in range(600):
                    seed = start + offset
                    grid = generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                    output = independent_rule(grid)
                    pairs.add(
                        (
                            tuple(map(tuple, grid)),
                            tuple(map(tuple, output)),
                        )
                    )
                    signature = generator.canonical_profile_signature(grid)
                    if signature is not None:
                        matches += 1
                        profiles.add(signature)
                self.assertGreaterEqual(matches, 100)
                self.assertLessEqual(matches, 210)
                self.assertEqual(
                    profiles,
                    generator._CANONICAL_PROFILE_SIGNATURES,
                )
                self.assertGreaterEqual(len(pairs), 595)

    def test_forced_dimension_boundaries_are_exact(self):
        for height, width in (
            (6, 6),
            (6, 30),
            (30, 6),
            (30, 30),
        ):
            for band in ("easy", "medium", "hard"):
                grid = generator.generate(
                    height * 31,
                    width * 37,
                    difficulty=band,
                    grid_h=height,
                    grid_w=width,
                )
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(
                    generator.observe_overrides(grid),
                    {"grid_h": height, "grid_w": width},
                )
                self.assertTrue(
                    all(generator._winner_counts(grid).values())
                )

    def test_rule_is_exact_priority_chain_and_input_pure(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(180):
                grid = generator.generate(
                    seed,
                    seed * 29 + 7,
                    difficulty=band,
                )
                before = [row[:] for row in grid]
                expected = independent_rule(grid)
                actual = generator.rule_mirror(grid)
                self.assertEqual(actual, expected)
                self.assertEqual(grid, before)
                self.assertEqual(
                    (len(actual), len(actual[0])),
                    (len(grid) // 2, len(grid[0]) // 2),
                )
                if not generator.is_canonical_profile(grid):
                    self.assertTrue(
                        all(generator._winner_counts(grid).values())
                    )

    def test_profile_color_relabeling_and_lawful_nonprofile(self):
        for index, profile in enumerate(generator._PROFILE_MASKS):
            for shift in range(9):
                colors = tuple(
                    1 + ((shift + offset * 2) % 9)
                    for offset in range(4)
                )
                if len(set(colors)) != 4:
                    continue
                grid = generator._draw_profile(profile, colors)
                self.assertEqual(generator.self_check(grid), [])
                self.assertTrue(generator.is_canonical_profile(grid))
                self.assertEqual(
                    generator.rule_mirror(grid),
                    independent_rule(grid),
                )

        hybrid = generator.generate(
            83,
            97,
            grid_h=12,
            grid_w=14,
        )
        self.assertEqual(generator.self_check(hybrid), [])
        self.assertFalse(generator.is_canonical_profile(hybrid))
        self.assertEqual(
            generator.rule_mirror(hybrid),
            independent_rule(hybrid),
        )

        _coerced, features, errors = generator._scene_analysis(hybrid)
        self.assertEqual(errors, [])
        relabeled = dict(zip(features["colors"], reversed(features["colors"])))
        transformed_input = [
            [relabeled.get(value, value) for value in row]
            for row in hybrid
        ]
        transformed_output = [
            [relabeled.get(value, value) for value in row]
            for row in independent_rule(hybrid)
        ]
        self.assertEqual(
            generator.rule_mirror(transformed_input),
            transformed_output,
        )

    def test_removed_controls_odd_sizes_and_strict_types(self):
        bad_calls = (
            {"difficulty": "expert"},
            {"bogus": 1},
            {"grid_h": "6"},
            {"grid_w": 6.0},
            {"grid_h": True},
            {"grid_h": 4},
            {"grid_h": 32},
            {"grid_h": 7},
            {"grid_w": 5},
            {"grid_w": 19},
            {"grid_n": 10},
            {"palette_size": 4},
            {"quadrant_density": 0.5},
            {"quadrant_layout": "scattered"},
            {"anchor_corners": True},
            {"texture": "full_quadrants"},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **kwargs)

    def test_every_return_path_records_exact_provenance(self):
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
                observed = generator.observe_overrides(grid)
                for key in generator.AXES:
                    self.assertEqual(captured[-1]._drawn[key], observed[key])
                profiled += generator.is_canonical_profile(grid)
        self.assertGreater(profiled, 125)

        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = generator.generate(
                91,
                117,
                difficulty="easy",
                grid_h=30,
                grid_w=6,
            )
        finally:
            base.set_ctx_observer(None)
        self.assertEqual(
            captured[-1]._drawn,
            generator.observe_overrides(grid),
        )
        self.assertEqual(
            captured[-1]._override_used,
            {"grid_h": 30, "grid_w": 6},
        )

    def test_self_check_rejects_structural_impostors(self):
        valid = generator.generate(1, 2, grid_h=10, grid_w=12)
        _coerced, features, errors = generator._scene_analysis(valid)
        self.assertEqual(errors, [])
        half_h = features["half_h"]
        half_w = features["half_w"]
        colors = features["colors"]
        mutations = []

        empty_quad = [row[:] for row in valid]
        for row in range(half_h):
            for col in range(half_w):
                empty_quad[row][col] = 0
        mutations.append(empty_quad)

        full_quad = [row[:] for row in valid]
        for row in range(half_h):
            for col in range(half_w):
                full_quad[row][col] = colors[0]
        mutations.append(full_quad)

        mixed_color = [row[:] for row in valid]
        mixed_color[0][0] = colors[1]
        mutations.append(mixed_color)

        repeated_color = [row[:] for row in valid]
        for row in range(half_h):
            for col in range(half_w, len(repeated_color[0])):
                if repeated_color[row][col] != 0:
                    repeated_color[row][col] = colors[0]
        mutations.append(repeated_color)

        ragged = [row[:] for row in valid]
        ragged[-1] = ragged[-1][:-1]
        mutations.append(ragged)
        mutations.append([[0] * 8 for _ in range(7)])
        mutations.append([[0] * 7 for _ in range(8)])
        mutations.append([[0] * 6 for _ in range(4)])
        mutations.append([[0] * 22 for _ in range(6)])

        invalid_value = [row[:] for row in valid]
        invalid_value[0][0] = 10
        mutations.append(invalid_value)

        for mutation in mutations:
            self.assertTrue(generator.self_check(mutation), mutation)

    def test_bands_cover_profiles_priority_palette_and_diversity(self):
        mean_areas = {}
        mean_density = {}
        palette = set()
        for band in ("easy", "medium", "hard"):
            areas = []
            densities = []
            pairs = set()
            profiles = set()
            all_winners = 0
            for seed in range(600):
                grid = generator.generate(
                    seed,
                    seed * 43 + 11,
                    difficulty=band,
                )
                output = generator.rule_mirror(grid)
                pairs.add(
                    (
                        tuple(map(tuple, grid)),
                        tuple(map(tuple, output)),
                    )
                )
                _coerced, features, errors = generator._scene_analysis(grid)
                self.assertEqual(errors, [])
                areas.append(len(grid) * len(grid[0]))
                densities.append(
                    sum(features["occupancies"])
                    / (len(grid) * len(grid[0]))
                )
                palette.update(features["colors"])
                all_winners += all(features["winner_counts"].values())
                signature = generator.canonical_profile_signature(grid)
                if signature is not None:
                    profiles.add(signature)

            mean_areas[band] = sum(areas) / len(areas)
            mean_density[band] = sum(densities) / len(densities)
            self.assertGreaterEqual(len(pairs), 595)
            self.assertGreaterEqual(all_winners, 500)
            self.assertEqual(
                profiles,
                generator._CANONICAL_PROFILE_SIGNATURES,
            )

        self.assertEqual(palette, set(range(1, 10)))
        self.assertLess(mean_areas["easy"], mean_areas["medium"])
        self.assertLess(mean_areas["medium"], mean_areas["hard"])
        self.assertLess(mean_density["easy"], mean_density["medium"])
        self.assertLess(mean_density["medium"], mean_density["hard"])

    def test_source_pin_determinism_freshness_and_global_rng(self):
        canonical = self.row["program_solution"]
        normalized = hashlib.sha256(
            " ".join(canonical.split()).encode()
        ).hexdigest()
        self.assertEqual(generator.RULE_HASH, normalized[:12])
        base_row = json.loads(
            (
                ROOT
                / "data/base/solutions/training"
                / "ea9794b1__f112ec4615da.json"
            ).read_text()
        )
        self.assertEqual(
            base_row["racket_target"]["raw_code"], canonical
        )
        self.assertEqual(
            base_row["racket_target"]["target_code"], canonical
        )

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
