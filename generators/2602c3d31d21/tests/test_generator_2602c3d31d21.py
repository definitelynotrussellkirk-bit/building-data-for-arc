"""Focused semantic regressions for generator 2602c3d31d21."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import random
import unittest

from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "2602c3d31d21"
ROOT = find_root(__file__)
MODULE, _GENERATOR_PATH, _GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
DATA_ROOT = canonical_path(ROOT).parent.parent


def _canonical_rows():
    return [
        json.loads(line)
        for line in canonical_path(ROOT).read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    ]


def _normalized_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


class Generator2602c3d31d21Tests(unittest.TestCase):
    def test_all_ten_canonical_occurrences_and_five_unique_profiles(self):
        rows = _canonical_rows()
        self.assertEqual([(row["source"], len(row["train"]), len(row["test"])) for row in rows], [
            ("training", 3, 2), ("augmented", 5, 0)
        ])
        profiles = []
        inputs = set()
        for row in rows:
            for pair in [*row["train"], *row["test"]]:
                grid = pair["input"]
                self.assertEqual(MODULE.self_check(grid), [])
                self.assertEqual(MODULE.rule_mirror(grid), pair["output"])
                profile = MODULE.canonical_profile_signature(grid)
                self.assertIn(profile, MODULE.PUBLIC_PROFILES)
                profiles.append(profile)
                inputs.add(tuple(map(tuple, grid)))
        self.assertEqual(len(profiles), 10)
        self.assertEqual(len(inputs), 5)
        self.assertEqual(set(profiles), set(MODULE.PUBLIC_PROFILES))
        self.assertTrue(all(profiles.count(profile) == 2 for profile in MODULE.PUBLIC_PROFILES))

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
                    grid = MODULE.generate(seed + 500, seed * 19 + 7, difficulty=band, scene_profile=profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(
                        MODULE.self_check(grid, meta={"overrides": {"scene_profile": profile}}),
                        [],
                    )

    def test_general_profiles_expose_exact_equivalence_partitions(self):
        expected = {
            "equal_pair": (0, 0),
            "unequal_pair": (0, 1),
            "one_pair_one_singleton": (0, 0, 1),
            "two_pairs": (0, 0, 1, 1),
            "singleton_triple": (0, 1, 1, 1),
            "all_distinct_five": (0, 1, 2, 3, 4),
            "mixed_six": (0, 0, 1, 1, 1, 2),
            "mixed_seven": (0, 0, 0, 1, 1, 2, 2),
            "collision_same_size": (0, 0),
            "collision_different_size": (0, 0),
            "equal_nonadjacent": (0, 1, 0, 2, 1),
        }
        for profile, partition in expected.items():
            info = MODULE._analysis(MODULE.generate(101, 203, difficulty="hard", scene_profile=profile))
            self.assertEqual(info["signature_partition"], partition)
            self.assertEqual(info["scene_profile"], profile)

    def test_hash_collision_profiles_defeat_size_and_congruence_shortcuts(self):
        same_size = MODULE._analysis(MODULE.generate(71, 73, scene_profile="collision_same_size"))
        different_size = MODULE._analysis(MODULE.generate(79, 83, scene_profile="collision_different_size"))
        self.assertEqual(len({shape["spd"] for shape in same_size["shapes"]}), 1)
        self.assertEqual(len({shape["size"] for shape in same_size["shapes"]}), 1)
        self.assertNotEqual(same_size["shapes"][0]["congruence"], same_size["shapes"][1]["congruence"])
        self.assertEqual(len({shape["spd"] for shape in different_size["shapes"]}), 1)
        self.assertEqual({shape["size"] for shape in different_size["shapes"]}, {4, 5})

    def test_rule_mirror_builds_headers_separators_and_symmetric_matrix(self):
        grid = MODULE.generate(301, 401, difficulty="hard", scene_profile="equal_nonadjacent")
        info = MODULE._analysis(grid)
        output = MODULE.rule_mirror(grid)
        count = len(info["key_colors"])
        self.assertEqual((len(output), len(output[0])), ((count + 1) * 3 - 1,) * 2)
        for row in range(len(output)):
            for col in range(len(output)):
                if row % 3 == 2 or col % 3 == 2:
                    self.assertEqual(output[row][col], 0)
        for index, color in enumerate(info["key_colors"]):
            start = (index + 1) * 3
            self.assertTrue(all(output[row][start] == color for row in (0, 1)))
            self.assertTrue(all(output[start][col] == color for col in (0, 1)))
        self.assertEqual(output, [list(row) for row in zip(*output)])

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
            self.assertGreater(strict, 190)
            self.assertLess(strict, 320)
            self.assertGreater(len(inputs), 790)
            self.assertGreater(len(outputs), 650)

    def test_self_check_rejects_nearest_impostors(self):
        base = MODULE.generate(331, 557, difficulty="medium", scene_profile="two_pairs")
        info = MODULE._analysis(base)
        no_keys = copy.deepcopy(base)
        for row, _ in info["key_cells"]:
            no_keys[row][-1] = 0
        missing_shape = copy.deepcopy(base)
        for row, col in info["shapes"][0]["cells"]:
            missing_shape[row][col] = 0
        duplicate_key = copy.deepcopy(base)
        duplicate_key[info["key_cells"][1][0]][-1] = info["key_colors"][0]
        extra_color = copy.deepcopy(base)
        extra_color[0][0] = next(color for color in range(1, 10) if color not in info["key_colors"])
        disconnected = copy.deepcopy(base)
        disconnected[0][0] = info["key_colors"][0]
        ragged = copy.deepcopy(base)
        ragged[0].pop()
        invalid = copy.deepcopy(base)
        invalid[0][0] = 10
        boolean = copy.deepcopy(base)
        boolean[0][0] = True
        for mutation in (no_keys, missing_shape, duplicate_key, extra_color, disconnected, ragged, invalid, boolean):
            self.assertTrue(MODULE.self_check(mutation), mutation)

    def test_override_and_determinism_contract(self):
        for overrides in ({"scene_profile": "unknown"}, {"key_count": 4}, {"texture": "no_keys"}):
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
        rows = _canonical_rows()
        canonical = rows[0]["program_solution"]
        self.assertTrue(all(row["program_solution"] == canonical for row in rows))
        paths = (
            DATA_ROOT / "base/solutions/training/6165ea8f__2602c3d31d21.json",
            DATA_ROOT / "base/solutions/augmented/6165ea8f__49315660abae.json",
        )
        for path in paths:
            target = json.loads(path.read_text())["racket_target"]
            self.assertEqual(target["canonicalization_status"], "preserved_executable_source")
            self.assertEqual(target["raw_code"], target["target_code"])
            self.assertEqual(_normalized_hash(target["raw_code"]), _normalized_hash(canonical))
        self.assertEqual(MODULE.RULE_HASH, _normalized_hash(canonical))
        self.assertEqual(MODULE.RULE_HASH, "af35f40d51ca")


if __name__ == "__main__":
    unittest.main()
