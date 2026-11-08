from __future__ import annotations

import hashlib
import json
import random
import unittest
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.f4f11295a6f5 import generator
from solvers.grounded_rules import GROUNDED_RULES


ROOT = Path(__file__).resolve().parents[1]


def canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == generator.TASK_ID:
                return row
    raise KeyError(generator.TASK_ID)


def canonical_pairs():
    row = canonical_row()
    test = row["test"]
    return list(row["train"]) + (
        [test] if isinstance(test, dict) else list(test)
    )


def coerce(grid):
    return [
        [int(value) for value in row]
        if isinstance(row, str)
        else list(row)
        for row in grid
    ]


def independent_rule(grid):
    grid = coerce(grid)
    positions = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    top = min(row for row, _col in positions)
    bottom = max(row for row, _col in positions)
    left = min(col for _row, col in positions)
    right = max(col for _row, col in positions)
    pattern = [
        values[left:right + 1]
        for values in grid[top:bottom + 1]
    ]
    pattern_h = len(pattern)
    pattern_w = len(pattern[0])
    return [
        [
            (
                pattern[row % pattern_h][col % pattern_w]
                if pattern[row // pattern_h][col // pattern_w] != 0
                else 0
            )
            for col in range(pattern_w * pattern_w)
        ]
        for row in range(pattern_h * pattern_h)
    ]


class F4f11295a6f5GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = canonical_row()
        cls.pairs = canonical_pairs()

    def test_all_public_pairs_match_rule_and_complete_profiles(self):
        self.assertEqual(len(self.pairs), 4)
        profiles = set()
        for pair in self.pairs:
            grid = pair["input"]
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(independent_rule(grid), pair["output"])
            self.assertEqual(generator.rule_mirror(grid), pair["output"])
            self.assertEqual(grid, before)
            profiles.add(generator.canonical_profile_index(grid))
        self.assertEqual(profiles, set(range(4)))

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
                    pairs.add((
                        tuple(map(tuple, grid)),
                        tuple(map(tuple, output)),
                    ))
                    profile = generator.canonical_profile_index(grid)
                    if profile is not None:
                        matches += 1
                        profiles.add(profile)
                self.assertGreaterEqual(matches, 75)
                self.assertLessEqual(matches, 135)
                self.assertEqual(profiles, set(range(4)))
                self.assertGreaterEqual(len(pairs), 595)

    def test_forced_pattern_boundaries_and_values_are_exact(self):
        for value in generator._PATTERN_SIZES:
            for label in ("pattern_h", "pattern_w"):
                grid = generator.generate(
                    value,
                    value * 13,
                    **{label: value},
                )
                self.assertEqual(
                    generator.observe_overrides(grid)[label],
                    value,
                )
        for pattern_h, pattern_w in (
            (2, 2),
            (2, 5),
            (5, 2),
            (5, 5),
        ):
            for band in ("easy", "medium", "hard"):
                grid = generator.generate(
                    pattern_h * 31,
                    pattern_w * 37,
                    difficulty=band,
                    pattern_h=pattern_h,
                    pattern_w=pattern_w,
                )
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(
                    generator.observe_overrides(grid),
                    {
                        "pattern_h": pattern_h,
                        "pattern_w": pattern_w,
                    },
                )
                self.assertEqual(
                    (len(grid), len(grid[0])),
                    (pattern_h * pattern_h, pattern_w * pattern_w),
                )

    def test_rule_is_exact_for_single_multi_and_nonsquare_patterns(self):
        seen_color_counts = set()
        seen_nonsquare = False
        for band in ("easy", "medium", "hard"):
            for seed in range(240):
                grid = generator.generate(
                    seed,
                    seed * 29 + 7,
                    difficulty=band,
                )
                before = [row[:] for row in grid]
                expected = independent_rule(grid)
                self.assertEqual(generator.rule_mirror(grid), expected)
                self.assertEqual(grid, before)
                self.assertEqual(
                    (len(grid), len(grid[0])),
                    (len(expected), len(expected[0])),
                )
                _coerced, features, errors = generator._scene_analysis(grid)
                self.assertEqual(errors, [])
                seen_color_counts.add(features["color_count"])
                seen_nonsquare |= (
                    features["pattern_h"] != features["pattern_w"]
                )
        self.assertEqual(seen_color_counts, {1, 2, 3})
        self.assertTrue(seen_nonsquare)

    def test_d4_translation_color_metamorphism_and_nonprofile(self):
        for index, source in enumerate(generator._PROFILE_PATTERNS):
            signatures = set()
            bboxes = set()
            colors = set()
            for shift in range(100):
                grid = generator._draw_profile(
                    source,
                    random.Random(index * 1000 + shift),
                )
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(generator.canonical_profile_index(grid), index)
                self.assertEqual(
                    generator.rule_mirror(grid),
                    independent_rule(grid),
                )
                signatures.add(generator.canonical_profile_signature(grid))
                _coerced, features, _errors = generator._scene_analysis(grid)
                bboxes.add(features["bbox"])
                colors.update(features["colors"])
            self.assertGreaterEqual(len(signatures), 4)
            self.assertGreaterEqual(len(bboxes), 20)
            self.assertEqual(colors, set(generator._COLORS))

        hybrid = generator.generate(
            83,
            97,
            pattern_h=5,
            pattern_w=2,
        )
        self.assertEqual(generator.self_check(hybrid), [])
        self.assertIsNone(generator.canonical_profile_index(hybrid))
        transformed_input = [
            [
                0 if value == 0 else 10 - value
                for value in row
            ]
            for row in hybrid
        ]
        transformed_output = [
            [
                0 if value == 0 else 10 - value
                for value in row
            ]
            for row in independent_rule(hybrid)
        ]
        self.assertEqual(
            generator.rule_mirror(transformed_input),
            transformed_output,
        )

    def test_removed_controls_and_strict_types(self):
        bad_calls = (
            {"difficulty": "expert"},
            {"bogus": 1},
            {"pattern_h": "3"},
            {"pattern_w": 3.0},
            {"pattern_h": True},
            {"pattern_h": 1},
            {"pattern_h": 6},
            {"pattern_size": 3},
            {"fg_color": 7},
            {"fg_density": 0.5},
            {"pattern_layout": "diag"},
            {"padding_top": 1},
            {"padding_left": 1},
            {"decoy_density": 0.0},
            {"edge_force": True},
            {"texture": "checker"},
            {"texture": "full_pattern"},
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
        self.assertGreater(profiled, 90)

        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = generator.generate(
                91,
                117,
                difficulty="easy",
                pattern_h=5,
                pattern_w=2,
            )
        finally:
            base.set_ctx_observer(None)
        self.assertEqual(
            captured[-1]._drawn,
            generator.observe_overrides(grid),
        )
        self.assertEqual(
            captured[-1]._override_used,
            {"pattern_h": 5, "pattern_w": 2},
        )

    def test_self_check_rejects_structural_impostors(self):
        valid = generator.generate(
            1,
            2,
            difficulty="hard",
            pattern_h=4,
            pattern_w=4,
        )
        _coerced, features, errors = generator._scene_analysis(valid)
        self.assertEqual(errors, [])
        mutations = []

        empty = [[0] * len(valid[0]) for _row in valid]
        mutations.append(empty)

        singleton = [[0] * len(valid[0]) for _row in valid]
        singleton[0][0] = 2
        mutations.append(singleton)

        full_crop = [[0] * len(valid[0]) for _row in valid]
        for row in range(4):
            for col in range(4):
                full_crop[row][col] = 2
        mutations.append(full_crop)

        wrong_height = [row[:] for row in valid[:-1]]
        mutations.append(wrong_height)

        four_colors = [row[:] for row in valid]
        top, left, _bottom, _right = features["bbox"]
        for offset, color in enumerate((1, 2, 3, 4)):
            four_colors[top][left + offset] = color
        mutations.append(four_colors)

        ragged = [row[:] for row in valid]
        ragged[-1] = ragged[-1][:-1]
        mutations.append(ragged)

        invalid_value = [row[:] for row in valid]
        invalid_value[0][0] = 10
        mutations.append(invalid_value)

        for mutation in mutations:
            self.assertTrue(generator.self_check(mutation), mutation)

    def test_bands_cover_profiles_sizes_colors_and_diversity(self):
        mean_areas = {}
        color_counts = {}
        crop_shapes = {}
        palette = set()
        for band in ("easy", "medium", "hard"):
            areas = []
            pairs = set()
            profiles = set()
            counts = set()
            shapes = set()
            for seed in range(600):
                grid = generator.generate(
                    seed,
                    seed * 43 + 11,
                    difficulty=band,
                )
                output = generator.rule_mirror(grid)
                pairs.add((
                    tuple(map(tuple, grid)),
                    tuple(map(tuple, output)),
                ))
                _coerced, features, errors = generator._scene_analysis(grid)
                self.assertEqual(errors, [])
                areas.append(len(grid) * len(grid[0]))
                counts.add(features["color_count"])
                shapes.add((
                    features["pattern_h"],
                    features["pattern_w"],
                ))
                palette.update(features["colors"])
                self.assertEqual(
                    (len(grid), len(grid[0])),
                    (len(output), len(output[0])),
                )
                profile = generator.canonical_profile_index(grid)
                if profile is not None:
                    profiles.add(profile)

            mean_areas[band] = sum(areas) / len(areas)
            color_counts[band] = counts
            crop_shapes[band] = shapes
            self.assertGreaterEqual(len(pairs), 595)
            self.assertEqual(profiles, set(range(4)))

        self.assertEqual(palette, set(generator._COLORS))
        self.assertEqual(color_counts["easy"], {1, 2})
        self.assertEqual(color_counts["medium"], {1, 2})
        self.assertEqual(color_counts["hard"], {1, 2, 3})
        self.assertTrue(any(h != w for h, w in crop_shapes["medium"]))
        self.assertTrue((5, 5) in crop_shapes["hard"])
        self.assertLess(mean_areas["easy"], mean_areas["medium"])
        self.assertLess(mean_areas["medium"], mean_areas["hard"])

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
                / "8f2ea7aa__f4f11295a6f5.json"
            ).read_text()
        )
        self.assertEqual(
            base_row["racket_target"]["raw_code"], canonical
        )
        self.assertEqual(
            base_row["racket_target"]["target_code"], canonical
        )
        self.assertEqual(GROUNDED_RULES[generator.TASK_ID], canonical)

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
