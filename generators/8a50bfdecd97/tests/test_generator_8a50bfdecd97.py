from __future__ import annotations

import copy
import hashlib
import json
import random
import unittest
from collections import Counter

from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)

TASK_ID = "8a50bfdecd97"
ROOT = find_root(__file__)
GENERATOR, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(
    TASK_ID, root=ROOT
)


def _data_path(relative):
    for candidate in (ROOT / relative, ROOT / "shared" / relative):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(relative)


def canonical_rows():
    return [
        json.loads(line)
        for line in canonical_path(ROOT).read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    ]


def occurrences():
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


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
            generated = GENERATOR.generate(13, 17, scene_profile=profile)
            self.assertEqual(generated, pair["input"])
            self.assertIsNot(generated, GENERATOR._PUBLIC_INPUTS[profile])

    def test_general_profiles_are_exact_and_observable(self):
        for band in ("easy", "medium", "hard"):
            for profile, mask in GENERATOR.GENERAL_MASKS.items():
                for seed in range(24):
                    grid = GENERATOR.generate(
                        seed, seed * 29, difficulty=band, scene_profile=profile
                    )
                    analysis = GENERATOR._analysis(grid)
                    self.assertEqual(analysis["errors"], [])
                    self.assertEqual(analysis["shape_mask"], mask)
                    self.assertEqual(
                        GENERATOR.observe_overrides(grid),
                        {"scene_profile": profile},
                    )

    def test_both_diagonals_and_both_destination_rows_occur(self):
        top_sides = set()
        destination_orientations = set()
        for seed in range(500):
            grid = GENERATOR.generate(
                seed, seed * 31, difficulty="hard", scene_profile="pattern_cross"
            )
            analysis = GENERATOR._analysis(grid)
            top = next(
                bracket for bracket in analysis["brackets"]
                if bracket["orientation"] == "top"
            )
            top_sides.add(top["side"])
            destination_orientations.add(analysis["row_bracket"]["orientation"])
        self.assertEqual(top_sides, {"left", "right"})
        self.assertEqual(destination_orientations, {"top", "bottom"})

    def test_diversity_and_branch_coverage(self):
        for band in ("easy", "medium", "hard"):
            profiles = Counter()
            inputs, outputs, shapes, colors = set(), set(), set(), set()
            for seed in range(600):
                grid = GENERATOR.generate(seed, seed * 37, difficulty=band)
                analysis = GENERATOR._analysis(grid)
                self.assertEqual(analysis["errors"], [])
                profiles[analysis["scene_profile"]] += 1
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, analysis["output"])))
                shapes.add((len(grid), len(grid[0])))
                colors.add(analysis["shape_color"])
            self.assertEqual(set(profiles), set(GENERATOR.SCENE_PROFILES))
            self.assertGreater(len(inputs), 520)
            self.assertGreater(len(outputs), 500)
            minimum_shape_counts = {"easy": 10, "medium": 20, "hard": 30}
            self.assertGreaterEqual(len(shapes), minimum_shape_counts[band])
            self.assertEqual(colors, {0, 1, 2, 3, 5, 6, 8, 9})

    def test_malformed_grids_are_rejected(self):
        grid = GENERATOR.generate(5, 9, scene_profile="pattern_ell")
        cases = [[], [[7]], [[True]], [[10]]]
        ragged = copy.deepcopy(grid)
        ragged[0].pop()
        cases.append(ragged)
        missing_shape = copy.deepcopy(grid)
        for r, c in GENERATOR._analysis(grid)["shape_cells"]:
            missing_shape[r][c] = 7
        cases.append(missing_shape)
        broken_bracket = copy.deepcopy(grid)
        bracket_cell = min(GENERATOR._analysis(grid)["brackets"][0]["cells"])
        broken_bracket[bracket_cell[0]][bracket_cell[1]] = 7
        cases.append(broken_bracket)
        extra_color = copy.deepcopy(grid)
        extra_color[len(grid) // 2][len(grid[0]) // 2] = 6
        cases.append(extra_color)
        for case in cases:
            self.assertTrue(GENERATOR.self_check(case))

    def test_unpublished_pattern_is_a_calibrated_candidate(self):
        grid = GENERATOR.generate(41, 43, scene_profile="pattern_vbar3")
        r, c = max(GENERATOR._analysis(grid)["shape_cells"])
        grid[r][c] = 7
        analysis = GENERATOR._analysis(grid)
        self.assertEqual(analysis["shape_mask"], ("1", "1"))
        self.assertEqual(
            analysis["errors"],
            ["movable bitmap ('1', '1') does not match a declared profile"],
        )
        self.assertTrue(GENERATOR.self_check(grid))
        self.assertIsNone(GENERATOR.canonical_profile_signature(grid))
        with self.assertRaises(ValueError):
            GENERATOR.observe_overrides(grid)

    def test_determinism_fresh_returns_and_override_errors(self):
        for overrides in (
            {"scene_profile": "unknown"},
            {"shape_size": 2},
            {"texture": "no_shape"},
        ):
            with self.assertRaises(ValueError):
                GENERATOR.generate(1, 2, **overrides)
        random.seed(91)
        state = random.getstate()
        first = GENERATOR.generate(17, 23, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = GENERATOR.generate(17, 23, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)

    def test_selected_source_sync_preserves_archival_raw_code(self):
        rows = canonical_rows()
        source = rows[0]["program_solution"]
        self.assertTrue(all(row["program_solution"] == source for row in rows))
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(GENERATOR.RULE_HASH, digest)
        for relative in (
            "data/base/solutions/training/df9fd884__8a50bfdecd97.json",
            "data/base/solutions/augmented/df9fd884__d60e0182b9b1.json",
        ):
            base = json.loads(_data_path(relative).read_text())
            self.assertEqual(base["racket_target"]["target_code"], source)
            self.assertTrue(base["racket_target"]["raw_code"].strip())
            self.assertNotEqual(base["racket_target"]["raw_code"], source)


if __name__ == "__main__":
    unittest.main()
