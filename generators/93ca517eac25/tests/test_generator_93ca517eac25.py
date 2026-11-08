from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

TASK_ID = "93ca517eac25"
GENERATOR = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
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
    def test_every_canonical_pair_matches_rule(self):
        self.assertEqual(len(occurrences()), 5)
        for pair in occurrences():
            self.assertEqual(GENERATOR.rule_mirror(pair["input"]), pair["output"])

    def test_exact_public_profiles_cover_every_input(self):
        self.assertEqual(len({tuple(map(tuple, pair["input"])) for pair in occurrences()}), 5)
        for profile, pair in zip(GENERATOR.PUBLIC_PROFILES, occurrences()):
            self.assertEqual(GENERATOR.canonical_profile_signature(pair["input"]), profile)
            generated = GENERATOR.generate(7, 11, scene_profile=profile)
            self.assertEqual(generated, pair["input"])
            self.assertIsNot(generated, GENERATOR._PUBLIC_INPUTS[profile])

    def test_general_profiles_are_exact_and_observable(self):
        for band in ("easy", "medium", "hard"):
            for profile, (count, target_symmetric) in GENERATOR.GENERAL_SPECS.items():
                for seed in range(40):
                    grid = GENERATOR.generate(seed, seed * 29, difficulty=band, scene_profile=profile)
                    analysis = GENERATOR._analysis(grid)
                    self.assertEqual(analysis["errors"], [])
                    self.assertEqual(len(analysis["blue_components"]), count)
                    self.assertEqual(analysis["target_is_symmetric"], target_symmetric)
                    self.assertEqual(sum(analysis["symmetry_flags"]), 1 if target_symmetric else count - 1)
                    self.assertEqual(GENERATOR.observe_overrides(grid), {"scene_profile": profile})

    def test_rule_recolors_only_complete_minority_component(self):
        for profile in GENERATOR.GENERAL_PROFILES:
            for seed in range(60):
                grid = GENERATOR.generate(seed, seed * 31, scene_profile=profile)
                analysis = GENERATOR._analysis(grid)
                target = analysis["target_cells"]
                for r, row in enumerate(grid):
                    for c, value in enumerate(row):
                        self.assertEqual(analysis["output"][r][c], 2 if (r, c) in target else value)

    def test_counts_target_positions_shapes_and_distractors_vary(self):
        counts, positions, statuses, normalized, distractor_colors, dimensions = set(), set(), set(), set(), set(), set()
        for band in ("easy", "medium", "hard"):
            for seed in range(1600):
                grid = GENERATOR.generate(seed, seed * 37, difficulty=band)
                analysis = GENERATOR._analysis(grid)
                if analysis["scene_profile"] in GENERATOR.PUBLIC_PROFILES:
                    continue
                count = len(analysis["blue_components"])
                counts.add(count)
                positions.add((count, analysis["target_index"]))
                statuses.add(analysis["target_is_symmetric"])
                normalized.update(GENERATOR._normalize(cells) for cells in analysis["blue_components"])
                distractor_colors.update(analysis["distractor_colors"])
                dimensions.add((len(grid), len(grid[0])))
        self.assertEqual(counts, {3, 4, 5, 6})
        self.assertEqual(positions, {(count, index) for count in counts for index in range(count)})
        self.assertEqual(statuses, {False, True})
        self.assertGreaterEqual(len(normalized), 14)
        self.assertEqual(distractor_colors, {3, 4, 5, 6, 7, 8, 9})
        self.assertGreater(len(dimensions), 25)

    def test_diversity_and_profile_coverage(self):
        for band in ("easy", "medium", "hard"):
            profiles = Counter()
            inputs, outputs, shapes = set(), set(), set()
            for seed in range(800):
                grid = GENERATOR.generate(seed, seed * 41, difficulty=band)
                analysis = GENERATOR._analysis(grid)
                self.assertEqual(analysis["errors"], [])
                profiles[analysis["scene_profile"]] += 1
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, analysis["output"])))
                shapes.add((len(grid), len(grid[0])))
            self.assertEqual(set(profiles), set(GENERATOR.SCENE_PROFILES))
            self.assertGreater(len(inputs), 650)
            self.assertGreater(len(outputs), 650)
            self.assertGreater(len(shapes), 8)

    def test_malformed_and_uncalibrated_scenes_are_rejected(self):
        grid = GENERATOR.generate(5, 9, scene_profile="four_one_symmetric")
        cases = [[], [[0]], [[True]], [[10]]]
        ragged = copy.deepcopy(grid)
        ragged[0].pop()
        cases.append(ragged)
        preexisting_red = copy.deepcopy(grid)
        r, c = next((r, c) for r, row in enumerate(preexisting_red) for c, value in enumerate(row) if value == 0)
        preexisting_red[r][c] = 2
        cases.append(preexisting_red)
        no_distractors = copy.deepcopy(grid)
        for r, row in enumerate(no_distractors):
            for c, value in enumerate(row):
                if value not in (0, 1):
                    no_distractors[r][c] = 0
        cases.append(no_distractors)
        all_symmetric = [[0] * 12 for _ in range(12)]
        for top, left in ((1, 1), (1, 7), (7, 4)):
            for dr, dc in GENERATOR._mask_cells(("010", "111")):
                all_symmetric[top + dr][left + dc] = 1
        all_symmetric[10][10] = 8
        cases.append(all_symmetric)
        too_few = [[0] * 10 for _ in range(10)]
        for top, left, mask in ((1, 1, ("010", "111")), (6, 6, ("10", "11"))):
            for dr, dc in GENERATOR._mask_cells(mask):
                too_few[top + dr][left + dc] = 1
        too_few[4][8] = 7
        cases.append(too_few)
        for case in cases:
            self.assertTrue(GENERATOR.self_check(case), case)

    def test_determinism_fresh_returns_and_override_errors(self):
        for overrides in ({"scene_profile": "unknown"}, {"n_components": 4}, {"texture": "all_symmetric"}):
            with self.assertRaises(ValueError):
                GENERATOR.generate(1, 2, **overrides)
        with self.assertRaises(ValueError):
            GENERATOR.generate(1, 2, difficulty="extreme")
        random.seed(37)
        state = random.getstate()
        first = GENERATOR.generate(17, 23, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = GENERATOR.generate(17, 23, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)

    def test_source_hash_and_base_source_sync(self):
        source = canonical_row()["program_solution"]
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(GENERATOR.RULE_HASH, digest)
        base = json.loads((ROOT / "data/base/solutions/banks/0d41ded5f4cd/M90__93ca517eac25.json").read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)


if __name__ == "__main__":
    unittest.main()
