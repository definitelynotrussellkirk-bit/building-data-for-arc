from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from collections import Counter

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "8b6a2892a064"
GENERATOR = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = find_root(__file__)
DATA_ROOT = canonical_path(ROOT).parents[1]
CANONICAL_PAIRS = canonical_pairs(TASK_ID, root=ROOT)


def canonical_rows():
    return [
        json.loads(line)
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    ]


def occurrences():
    return CANONICAL_PAIRS


def unique_pairs():
    result = {}
    for pair in occurrences():
        result.setdefault(tuple(map(tuple, pair["input"])), pair)
    return list(result.values())


class GeneratorTests(unittest.TestCase):
    def test_all_canonical_occurrences_match_rule(self):
        self.assertEqual(len(occurrences()), 8)
        for pair in occurrences():
            self.assertEqual(
                GENERATOR.rule_mirror(pair["input"]), pair["output"]
            )

    def test_exact_public_profiles_cover_unique_inputs(self):
        self.assertEqual(len(unique_pairs()), 4)
        for profile, pair in zip(GENERATOR.PUBLIC_PROFILES, unique_pairs()):
            self.assertEqual(
                GENERATOR.canonical_profile_signature(pair["input"]), profile
            )
            generated = GENERATOR.generate(7, 11, scene_profile=profile)
            self.assertEqual(generated, pair["input"])
            self.assertIsNot(generated, GENERATOR._PUBLIC_INPUTS[profile])

    def test_general_blueprints_are_exact_and_observable(self):
        for band in ("easy", "medium", "hard"):
            for profile, blueprint in GENERATOR.GENERAL_BLUEPRINTS.items():
                expected = GENERATOR._blueprint_signature(blueprint)
                for seed in range(24):
                    grid = GENERATOR.generate(
                        seed, seed * 29, difficulty=band, scene_profile=profile
                    )
                    analysis = GENERATOR._analysis(grid)
                    self.assertEqual(analysis["errors"], [])
                    self.assertEqual(analysis["blueprint_signature"], expected)
                    self.assertEqual(
                        GENERATOR.observe_overrides(grid),
                        {"scene_profile": profile},
                    )

    def test_component_rotation_is_exact(self):
        for profile in GENERATOR.GENERAL_PROFILES:
            for seed in range(30):
                grid = GENERATOR.generate(seed, seed * 31, scene_profile=profile)
                analysis = GENERATOR._analysis(grid)
                output = analysis["output"]
                color = analysis["foreground_color"]
                expected = set()
                for descriptor in analysis["descriptors"]:
                    orientation = descriptor["orientation"]
                    length = descriptor["length"]
                    rows, cols = descriptor["rows"], descriptor["cols"]
                    half = length // 2
                    if orientation == "s":
                        expected.add((rows[0], cols[0]))
                    elif orientation == "h":
                        center = (cols[0] + cols[-1]) // 2
                        expected.update((r, center) for r in range(rows[0] - half, rows[0] + half + 1))
                    else:
                        center = (rows[0] + rows[-1]) // 2
                        expected.update((center, c) for c in range(cols[0] - half, cols[0] + half + 1))
                actual = {(r, c) for r, row in enumerate(output) for c, value in enumerate(row) if value == color}
                self.assertEqual(actual, expected)

    def test_all_colors_orientations_and_counts_occur(self):
        colors, orientations, counts = set(), set(), set()
        for seed in range(900):
            grid = GENERATOR.generate(seed, seed * 37, difficulty="hard")
            analysis = GENERATOR._analysis(grid)
            colors.add(analysis["foreground_color"])
            orientations.update(d["orientation"] for d in analysis["descriptors"])
            counts.add(analysis["component_count"])
        self.assertEqual(colors, {0, 1, 2, 3, 4, 5, 6, 8, 9})
        self.assertEqual(orientations, {"s", "h", "v"})
        self.assertEqual(counts, {2, 3, 5, 6, 7, 8, 10})

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
            self.assertGreater(len(inputs), 500)
            self.assertGreater(len(outputs), 500)
            self.assertGreater(len(shapes), 15)

    def test_malformed_and_unpublished_blueprints_are_rejected(self):
        grid = GENERATOR.generate(5, 9, scene_profile="three_mixed")
        cases = [[], [[7]], [[True]], [[10]]]
        ragged = copy.deepcopy(grid)
        ragged[0].pop()
        cases.append(ragged)
        multi_color = copy.deepcopy(grid)
        r, c = next((r, c) for r, row in enumerate(multi_color) for c, value in enumerate(row) if value != 7)
        multi_color[r][c] = 6 if multi_color[r][c] != 6 else 5
        cases.append(multi_color)
        even_line = [[7] * 7 for _ in range(7)]
        even_line[3][2] = even_line[3][3] = 2
        cases.append(even_line)
        bent = [[7] * 7 for _ in range(7)]
        bent[3][2] = bent[3][3] = bent[4][3] = 2
        cases.append(bent)
        unpublished = [[7] * 9 for _ in range(9)]
        for c in range(2, 9):
            unpublished[4][c] = 2
        cases.append(unpublished)
        for case in cases:
            self.assertTrue(GENERATOR.self_check(case))

    def test_determinism_fresh_returns_and_override_errors(self):
        for overrides in (
            {"scene_profile": "unknown"},
            {"line_count": 5},
            {"texture": "no_lines"},
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

    def test_source_hash_and_duplicate_source_sync(self):
        rows = canonical_rows()
        source = rows[0]["program_solution"]
        self.assertTrue(all(row["program_solution"] == source for row in rows))
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(GENERATOR.RULE_HASH, digest)
        for relative in (
            "base/solutions/training/f0f8a26d__8b6a2892a064.json",
            "base/solutions/augmented/f0f8a26d__424fc6d31f7a.json",
        ):
            base = json.loads((DATA_ROOT / relative).read_text(encoding="utf-8"))
            normalized_source = " ".join(source.split())
            self.assertEqual(
                " ".join(base["racket_target"]["raw_code"].split()), normalized_source
            )
            self.assertEqual(
                " ".join(base["racket_target"]["target_code"].split()), normalized_source
            )


if __name__ == "__main__":
    unittest.main()
