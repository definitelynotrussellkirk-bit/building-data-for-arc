"""Focused semantic regressions for generator 268b0e9a75b4."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib
import json
from pathlib import Path
import random
import unittest


TASK_ID = "268b0e9a75b4"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]


def _canonical_row():
    return next(
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )


def _grid(value):
    return [[int(cell) for cell in row] if isinstance(row, str) else list(row) for row in value]


def _normalized_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


class Generator268b0e9a75b4Tests(unittest.TestCase):
    def test_all_five_canonical_pairs_and_profiles(self):
        row = _canonical_row()
        pairs = [*row["train"], row["test"]]
        self.assertEqual(len(pairs), 5)
        profiles = []
        for pair in pairs:
            source, expected = _grid(pair["input"]), _grid(pair["output"])
            self.assertEqual(MODULE.self_check(source), [])
            self.assertEqual(MODULE.rule_mirror(source), expected)
            profile = MODULE.canonical_profile_signature(source)
            self.assertIn(profile, MODULE.PUBLIC_PROFILES)
            profiles.append(profile)
            info = MODULE._analysis(source)
            self.assertEqual(info["object_counts"], (2, 2, 1))
            self.assertEqual(info["branch"], "unique")
        self.assertEqual(profiles, list(MODULE.PUBLIC_PROFILES))

    def test_public_profiles_preserve_complete_linked_masks(self):
        for profile in MODULE.PUBLIC_PROFILES:
            seen = set()
            for seed in range(40):
                grid = MODULE.generate(seed, seed * 13 + 1, scene_profile=profile)
                self.assertEqual(MODULE.canonical_profile_signature(grid), profile)
                self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                seen.add(tuple(map(tuple, grid)))
            self.assertGreater(len(seen), 30)

    def test_forced_profiles_are_exact_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.SCENE_PROFILES:
                for seed in range(20):
                    grid = MODULE.generate(seed + 700, seed * 19 + 3, difficulty=band, scene_profile=profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(
                        MODULE.self_check(grid, meta={"overrides": {"scene_profile": profile}}),
                        [],
                    )

    def test_unique_candidate_order_and_size_profiles(self):
        expected = {
            "unique_middle": ((2, 1, 2), 1),
            "unique_smallest": ((2, 2, 1), 2),
            "unique_at_edge": ((1, 2, 2), 0),
            "two_colors": ((2, 1), 1),
            "four_colors": ((2, 2, 1, 2), 2),
        }
        for profile, (counts, chosen_position) in expected.items():
            info = MODULE._analysis(MODULE.generate(101, 203, difficulty="hard", scene_profile=profile))
            self.assertEqual(info["object_counts"], counts)
            self.assertEqual(info["order"].index(info["chosen_color"]), chosen_position)
            self.assertEqual(info["branch"], "unique")
        smallest = MODULE._analysis(MODULE.generate(107, 211, scene_profile="unique_smallest"))
        self.assertLess(smallest["chosen"]["size"], min(
            obj["size"] for obj in smallest["components"] if obj is not smallest["chosen"]
        ))

    def test_multiple_candidates_and_fallback_order(self):
        multiple = MODULE._analysis(MODULE.generate(301, 401, scene_profile="multiple_unique_first"))
        self.assertEqual(multiple["object_counts"], (1, 1, 2))
        self.assertEqual(multiple["chosen_color"], multiple["unique_colors"][0])
        for profile in ("fallback_highest", "fallback_largest_same_color", "fallback_highest_over_global_size"):
            info = MODULE._analysis(MODULE.generate(307, 409, scene_profile=profile))
            self.assertEqual(info["branch"], "fallback")
            self.assertEqual(info["chosen_color"], max(info["order"]))
            same_color = [obj for obj in info["components"] if obj["color"] == info["chosen_color"]]
            self.assertEqual(info["chosen"]["size"], max(obj["size"] for obj in same_color))
        global_counterexample = MODULE._analysis(
            MODULE.generate(313, 419, scene_profile="fallback_highest_over_global_size")
        )
        self.assertLess(global_counterexample["chosen"]["size"], max(
            obj["size"] for obj in global_counterexample["components"]
        ))

    def test_hollow_and_foreign_crops_preserve_bbox_cells(self):
        hollow_grid = MODULE.generate(331, 421, scene_profile="unique_hollow")
        foreign_grid = MODULE.generate(337, 431, scene_profile="foreign_inside_crop")
        hollow = MODULE._analysis(hollow_grid)
        foreign = MODULE._analysis(foreign_grid)
        self.assertTrue(MODULE._has_enclosed_zero(hollow["chosen_crop"]))
        self.assertTrue(any(
            value not in (0, foreign["chosen_color"])
            for row in foreign["chosen_crop"] for value in row
        ))
        self.assertEqual(MODULE.rule_mirror(hollow_grid), hollow["chosen_crop"])
        self.assertEqual(MODULE.rule_mirror(foreign_grid), foreign["chosen_crop"])

    def test_default_prior_coverage_and_diversity(self):
        for band in ("easy", "medium", "hard"):
            profiles = Counter()
            inputs = set()
            outputs = set()
            for seed in range(800):
                grid = MODULE.generate(seed, seed * 11 + 1, difficulty=band)
                profiles[MODULE.observe_overrides(grid)["scene_profile"]] += 1
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, MODULE.rule_mirror(grid))))
            self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
            strict = sum(profiles[profile] for profile in MODULE.PUBLIC_PROFILES)
            self.assertGreater(strict, 180)
            self.assertLess(strict, 310)
            self.assertGreater(len(inputs), 780)
            # Cropping discards all distractor placement, so output support is
            # intrinsically smaller than full-scene input support.
            self.assertGreater(len(outputs), 480)

    def test_self_check_rejects_nearest_impostors(self):
        base = MODULE.generate(401, 503, scene_profile="unique_middle")
        all_background = [[0 for _ in row] for row in base]
        single_color = [[0] * 5 for _ in range(5)]
        single_color[1][1] = single_color[1][2] = 3
        too_many_colors = copy.deepcopy(base)
        used = {value for row in base for value in row}
        additions = [value for value in range(1, 10) if value not in used][:2]
        too_many_colors[0][0] = additions[0]
        too_many_colors[-1][-1] = additions[1]
        two_singletons = [[1, 0, 2], [0, 0, 0], [0, 0, 0]]
        ragged = copy.deepcopy(base)
        ragged[0].pop()
        invalid = copy.deepcopy(base)
        invalid[0][0] = 10
        boolean = copy.deepcopy(base)
        boolean[0][0] = True
        for mutation in (all_background, single_color, too_many_colors, two_singletons, ragged, invalid, boolean):
            self.assertTrue(MODULE.self_check(mutation), mutation)
        self.assertTrue(MODULE.self_check(base, meta={"overrides": {"scene_profile": "unique_at_edge"}}))

    def test_override_and_determinism_contract(self):
        for overrides in ({"scene_profile": "unknown"}, {"palette_size": 3}, {"texture": "no_unique"}):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    MODULE.generate(1, 2, **overrides)
        random.seed(20260721)
        state = random.getstate()
        first = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))

    def test_rule_authorities_and_pin_are_synchronized(self):
        row = _canonical_row()
        canonical = row["program_solution"]
        base = json.loads((
            ROOT / "data/base/solutions/banks/ba76b91f26f9/E109__268b0e9a75b4.json"
        ).read_text())
        self.assertEqual(base["racket_target"]["raw_code"], canonical)
        self.assertEqual(base["racket_target"]["target_code"], canonical)
        self.assertEqual(MODULE.RULE_HASH, _normalized_hash(canonical))
        self.assertEqual(MODULE.RULE_HASH, "210dc0194f51")


if __name__ == "__main__":
    unittest.main()
