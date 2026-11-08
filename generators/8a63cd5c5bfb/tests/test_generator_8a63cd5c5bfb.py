from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

TASK_ID = "8a63cd5c5bfb"
GENERATOR = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def canonical_row():
    return next(
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )


def occurrences():
    row = canonical_row()
    return row["train"] + row["test"]


class GeneratorTests(unittest.TestCase):
    def test_all_canonical_pairs_match_rule(self):
        self.assertEqual(len(occurrences()), 5)
        for pair in occurrences():
            self.assertEqual(
                GENERATOR.rule_mirror(pair["input"]), pair["output"]
            )

    def test_exact_public_profiles_cover_every_input(self):
        self.assertEqual(len({tuple(map(tuple, pair["input"])) for pair in occurrences()}), 5)
        for profile, pair in zip(GENERATOR.PUBLIC_PROFILES, occurrences()):
            self.assertEqual(
                GENERATOR.canonical_profile_signature(pair["input"]), profile
            )
            generated = GENERATOR.generate(7, 11, scene_profile=profile)
            self.assertEqual(generated, pair["input"])
            self.assertIsNot(generated, GENERATOR._PUBLIC_INPUTS[profile])

    def test_general_profiles_are_exact_and_observable(self):
        for band in ("easy", "medium", "hard"):
            for profile, role_counts in GENERATOR.GENERAL_ROLE_COUNTS.items():
                for seed in range(24):
                    grid = GENERATOR.generate(
                        seed, seed * 29, difficulty=band, scene_profile=profile
                    )
                    analysis = GENERATOR._analysis(grid)
                    self.assertEqual(analysis["errors"], [])
                    self.assertEqual(analysis["role_counts"], role_counts)
                    self.assertEqual(
                        GENERATOR.observe_overrides(grid),
                        {"scene_profile": profile},
                    )

    def test_only_empty_border_cells_change(self):
        for profile in ("border_pair", "interior_pair", "mixed_three"):
            for seed in range(60):
                grid = GENERATOR.generate(seed, seed * 31, scene_profile=profile)
                analysis = GENERATOR._analysis(grid)
                output = analysis["output"]
                r0, c0, r1, c1 = analysis["rectangle"]
                for r, row in enumerate(grid):
                    for c, value in enumerate(row):
                        on_border = (
                            r0 <= r <= r1 and c0 <= c <= c1
                            and (r in (r0, r1) or c in (c0, c1))
                        )
                        expected = 8 if on_border and value == 0 else value
                        self.assertEqual(output[r][c], expected)

    def test_both_diagonals_and_all_distractor_colors_occur(self):
        diagonals, colors = set(), set()
        for seed in range(800):
            grid = GENERATOR.generate(seed, seed * 37, scene_profile="mixed_three")
            analysis = GENERATOR._analysis(grid)
            diagonals.add(analysis["diagonal"])
            colors.update(
                value for row in grid for value in row if value not in (0, 3)
            )
        self.assertEqual(diagonals, {"main", "anti"})
        self.assertEqual(colors, {1, 2, 4, 5, 6, 7, 8, 9})

    def test_diversity_and_profile_coverage(self):
        for band in ("easy", "medium", "hard"):
            profiles = Counter()
            inputs, outputs, shapes = set(), set(), set()
            for seed in range(600):
                grid = GENERATOR.generate(seed, seed * 41, difficulty=band)
                analysis = GENERATOR._analysis(grid)
                self.assertEqual(analysis["errors"], [])
                profiles[analysis["scene_profile"]] += 1
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, analysis["output"])))
                shapes.add((len(grid), len(grid[0])))
            self.assertEqual(set(profiles), set(GENERATOR.SCENE_PROFILES))
            self.assertGreater(len(inputs), 450)
            self.assertGreater(len(outputs), 450)
            self.assertGreater(len(shapes), 8)

    def test_malformed_and_unpublished_role_counts_are_rejected(self):
        grid = GENERATOR.generate(5, 9, scene_profile="mixed_three")
        cases = [[], [[0]], [[True]], [[10]]]
        ragged = copy.deepcopy(grid)
        ragged[0].pop()
        cases.append(ragged)
        missing_green = copy.deepcopy(grid)
        r, c = GENERATOR._analysis(grid)["greens"][0]
        missing_green[r][c] = 0
        cases.append(missing_green)
        third_green = copy.deepcopy(grid)
        r, c = next(
            (r, c) for r, row in enumerate(third_green) for c, value in enumerate(row)
            if value == 0
        )
        third_green[r][c] = 3
        cases.append(third_green)
        unpublished = copy.deepcopy(grid)
        analysis = GENERATOR._analysis(unpublished)
        r0, c0, r1, c1 = analysis["rectangle"]
        r, c = next(
            (r, c) for r, row in enumerate(unpublished) for c, value in enumerate(row)
            if value == 0 and not (r0 <= r <= r1 and c0 <= c <= c1)
        )
        unpublished[r][c] = 6
        cases.append(unpublished)
        self.assertEqual(GENERATOR._analysis(unpublished)["role_counts"], (2, 1, 1))
        for case in cases:
            self.assertTrue(GENERATOR.self_check(case))

    def test_determinism_fresh_returns_and_override_errors(self):
        for overrides in (
            {"scene_profile": "unknown"},
            {"grid_h": 9},
            {"texture": "no_corners"},
        ):
            with self.assertRaises(ValueError):
                GENERATOR.generate(1, 2, **overrides)
        random.seed(37)
        state = random.getstate()
        first = GENERATOR.generate(17, 23, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = GENERATOR.generate(17, 23, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)

    def test_source_hash_and_base_sync(self):
        source = canonical_row()["program_solution"]
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(GENERATOR.RULE_HASH, digest)
        base = json.loads((
            ROOT / "data/base/solutions/banks/8edfaf6db623/M102__8a63cd5c5bfb.json"
        ).read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)


if __name__ == "__main__":
    unittest.main()
