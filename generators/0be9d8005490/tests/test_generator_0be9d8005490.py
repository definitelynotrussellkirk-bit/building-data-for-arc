from __future__ import annotations

from collections import Counter
import copy
import hashlib
from importlib import import_module
import json
from pathlib import Path
import random
import unittest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "0be9d8005490"
generator = import_module(
    "puzzle_generators.per_puzzle.0be9d8005490.generator"
)


def canonical_rows():
    return [
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    ]


def unique_public_pairs():
    pairs = {}
    for row in canonical_rows():
        for split in ("train", "test"):
            for pair in row.get(split, []):
                key = tuple(tuple(values) for values in pair["input"])
                pairs[key] = pair
    return list(pairs.values())


def mismatch_count(grid, template, top, left):
    return sum(
        grid[top + row][left + col] != (0 if value == -1 else value)
        for row, values in enumerate(template)
        for col, value in enumerate(values)
    )


class Generator0be9d8005490Tests(unittest.TestCase):
    def test_all_four_public_pairs_are_positive_controls(self):
        pairs = unique_public_pairs()
        self.assertEqual(len(pairs), 4)
        observed = []
        for pair in pairs:
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            self.assertEqual(generator.self_check(source), [])
            actual = generator.rule_mirror(source)
            self.assertEqual(source, before)
            self.assertEqual(actual, pair["output"])
            analysis = generator._analyze_scene(source)
            self.assertIsNotNone(analysis)
            observed.append(analysis["scene_profile"])
        self.assertEqual(set(observed), set(generator._PUBLIC_PATTERNS))

    def test_every_profile_is_observable_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in generator.SCENE_PROFILES:
                for seed in range(12):
                    grid = generator.generate(
                        seed,
                        seed * 31 + 7,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    analysis = generator._analyze_scene(grid)
                    self.assertIsNotNone(analysis)
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(
                        generator.observe_overrides(grid),
                        {"scene_profile": profile},
                    )
                    self.assertEqual(
                        generator.self_check(
                            grid,
                            difficulty=band,
                            meta={"overrides": {"scene_profile": profile}},
                        ),
                        [],
                    )

    def test_exact_profiles_preserve_public_template_morphology(self):
        for profile, spec in generator._PUBLIC_PATTERNS.items():
            expected = generator._normal_pattern(spec["template"])
            for seed in range(40):
                grid = generator.generate(
                    seed + 100,
                    seed,
                    difficulty="medium",
                    scene_profile=profile,
                )
                analysis = generator._analyze_scene(grid)
                self.assertEqual(
                    generator._normal_pattern(analysis["template"]),
                    expected,
                )
                self.assertEqual(len(analysis["matches"]), spec["targets"])

    def test_distribution_has_dense_noise_and_all_profiles(self):
        expected_ranges = {
            "easy": (47, 58),
            "medium": (59, 74),
            "hard": (75, 90),
        }
        for band_index, band in enumerate(("easy", "medium", "hard")):
            profiles = Counter()
            distinct = set()
            target_counts = Counter()
            for index in range(1000):
                grid = generator.generate(
                    10000 + index,
                    index * 17 + band_index,
                    difficulty=band,
                )
                analysis = generator._analyze_scene(grid)
                self.assertIsNotNone(analysis)
                profiles[analysis["scene_profile"]] += 1
                target_counts[len(analysis["matches"])] += 1
                low, high = expected_ranges[band]
                self.assertLessEqual(low, analysis["noise_nonzero"])
                self.assertLessEqual(analysis["noise_nonzero"], high)
                distinct.add(tuple(tuple(row) for row in grid))
            self.assertEqual(set(profiles), set(generator.SCENE_PROFILES))
            self.assertGreaterEqual(min(profiles.values()), 70)
            self.assertEqual(set(target_counts), {1, 2})
            self.assertGreaterEqual(len(distinct), 980)

    def test_generalized_profile_contains_a_one_mismatch_decoy(self):
        for seed in range(100):
            grid = generator.generate(
                seed,
                9000 + seed,
                difficulty="hard",
                scene_profile="generalized",
            )
            analysis = generator._analyze_scene(grid)
            excluded = {analysis["origin"], *analysis["matches"]}
            near = [
                (top, left)
                for top in range(20)
                for left in range(20)
                if (top, left) not in excluded
                and mismatch_count(
                    grid,
                    analysis["template"],
                    top,
                    left,
                )
                == 1
            ]
            self.assertTrue(near)

    def test_self_check_rejects_nearest_destructive_mutations(self):
        grid = generator.generate(
            77,
            91,
            difficulty="easy",
            scene_profile="wild5_body4_targets1",
        )
        analysis = generator._analyze_scene(grid)

        mutations = []
        rectangular = [row[:] for row in grid]
        rectangular.append([0] * 22)
        mutations.append(rectangular)

        wrong_palette = copy.deepcopy(grid)
        wrong_palette[0][0] = 3
        mutations.append(wrong_palette)

        broken_template = copy.deepcopy(grid)
        yellow_row, yellow_col = next(
            (row, col)
            for row in range(22)
            for col in range(22)
            if broken_template[row][col] == 4
        )
        broken_template[yellow_row][yellow_col] = 0
        mutations.append(broken_template)

        occupied_target = copy.deepcopy(grid)
        target_top, target_left = analysis["matches"][0]
        wild_row, wild_col = next(
            (row, col)
            for row, values in enumerate(analysis["template"])
            for col, value in enumerate(values)
            if value == -1
        )
        occupied_target[target_top + wild_row][target_left + wild_col] = 1
        mutations.append(occupied_target)

        broken_target = copy.deepcopy(grid)
        body_row, body_col = next(
            (row, col)
            for row, values in enumerate(analysis["template"])
            for col, value in enumerate(values)
            if value in (1, 8)
        )
        broken_target[target_top + body_row][target_left + body_col] = 0
        mutations.append(broken_target)

        no_yellow = copy.deepcopy(grid)
        for row in range(22):
            for col in range(22):
                if no_yellow[row][col] == 4:
                    no_yellow[row][col] = 0
        mutations.append(no_yellow)

        for mutation in mutations:
            self.assertTrue(generator.self_check(mutation))
            self.assertEqual(generator.observe_overrides(mutation), {})

    def test_rule_mirror_is_broad_input_pure_and_exact(self):
        grid = [
            [4, 1, 4, 0, 0, 0, 0],
            [8, 1, 8, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 8, 1, 8, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
        before = copy.deepcopy(grid)
        output = generator.rule_mirror(grid)
        self.assertEqual(grid, before)
        self.assertEqual(output[2][3], 4)
        self.assertEqual(output[2][5], 4)
        self.assertEqual(output[3][3:6], [8, 1, 8])
        with self.assertRaises(ValueError):
            generator.rule_mirror([[0, 1], [1, 0]])

    def test_output_changes_exactly_target_wildcards(self):
        for profile in generator.SCENE_PROFILES:
            for seed in range(30):
                grid = generator.generate(
                    seed,
                    5000 + seed,
                    difficulty="hard",
                    scene_profile=profile,
                )
                analysis = generator._analyze_scene(grid)
                output = generator.rule_mirror(grid)
                changed = [
                    (row, col)
                    for row in range(22)
                    for col in range(22)
                    if grid[row][col] != output[row][col]
                ]
                self.assertEqual(
                    len(changed),
                    analysis["wildcard_count"] * len(analysis["matches"]),
                )
                self.assertTrue(
                    all(grid[row][col] == 0 and output[row][col] == 4 for row, col in changed)
                )

    def test_invalid_calls_determinism_freshness_and_global_rng(self):
        with self.assertRaises(ValueError):
            generator.generate(0, 0, difficulty="impossible")
        with self.assertRaises(ValueError):
            generator.generate(0, 0, unknown_axis=1)
        with self.assertRaises(ValueError):
            generator.generate(0, 0, scene_profile="unknown")

        random.seed(123456)
        state = random.getstate()
        first = generator.generate(51, 81, difficulty="medium")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(51, 81, difficulty="medium")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9
        self.assertNotEqual(first, second)

    def test_all_rule_authorities_are_byte_identical(self):
        from solvers.grounded_rules import GROUNDED_RULES

        rows = canonical_rows()
        self.assertEqual(len(rows), 2)
        canonical = rows[0]["program_solution"]
        self.assertTrue(all(row["program_solution"] == canonical for row in rows))
        self.assertEqual(GROUNDED_RULES[TASK_ID], canonical)
        for relative in (
            "data/base/solutions/training/bb52a14b__0be9d8005490.json",
            "data/base/solutions/augmented/bb52a14b__5a65a60b2d34.json",
        ):
            record = json.loads((ROOT / relative).read_text())
            self.assertEqual(record["racket_target"]["raw_code"], canonical)
            self.assertEqual(record["racket_target"]["target_code"], canonical)
        self.assertEqual(
            generator.RULE_HASH,
            hashlib.sha256(canonical.encode()).hexdigest()[:12],
        )


if __name__ == "__main__":
    unittest.main()
