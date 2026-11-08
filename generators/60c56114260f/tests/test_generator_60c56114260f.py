"""Focused semantic regressions for generator 60c56114260f."""
from __future__ import annotations

import copy
import hashlib
import json
import random
import unittest
from collections import Counter

from reviewer_support import (
    canonical_pairs as read_canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)

TASK_ID = "60c56114260f"
ROOT = find_root(__file__)
MODULE, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def canonical_row():
    return next(json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()
                if json.loads(line).get("task_id") == TASK_ID)


def canonical_pairs():
    return read_canonical_pairs(TASK_ID, root=ROOT)


def decode(grid):
    return [[int(cell) for cell in row] if isinstance(row, str) else list(row) for row in grid]


class Generator60c56114260fTests(unittest.TestCase):
    def test_all_five_canonical_pairs(self):
        pairs = canonical_pairs(); self.assertEqual(len(pairs), 5)
        for index, pair in enumerate(pairs):
            self.assertEqual(MODULE.rule_mirror(decode(pair["input"])), decode(pair["output"]))
            self.assertEqual(MODULE.canonical_profile_signature(decode(pair["input"])), MODULE.PUBLIC_PROFILES[index])

    def test_public_profiles_are_exact(self):
        expected = [decode(pair["input"]) for pair in canonical_pairs()]
        self.assertEqual([MODULE.generate(1, 2, scene_profile=p) for p in MODULE.PUBLIC_PROFILES], expected)

    def test_every_profile_and_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.SCENE_PROFILES:
                for seed in range(20):
                    grid = MODULE.generate(seed, seed * 17 + 3, difficulty=band, scene_profile=profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MODULE.self_check(grid), [])

    def test_declared_lessons_are_exact(self):
        for profile, (object_count, shape_size) in MODULE.GENERAL_LESSONS.items():
            info = MODULE._analysis(MODULE.generate(211, 307, scene_profile=profile))
            self.assertEqual(len(info["partition"]), object_count)
            self.assertEqual({len(part["cells"]) for part in info["parts"]}, {shape_size})
            self.assertEqual(len(info["output"]), object_count)

    def test_rotation_and_reflection_equivalence(self):
        shape = ((0, 0), (0, 1), (0, 2), (1, 0))
        key = MODULE._shape_key(shape)
        for variant in MODULE._variants(shape):
            self.assertEqual(MODULE._shape_key(variant), key)
        self.assertNotEqual(key, MODULE._shape_key(((0, 0), (0, 1), (0, 2), (1, 1))))

    def test_default_census_and_diversity(self):
        for band in ("easy", "medium", "hard"):
            profiles, inputs, outputs = Counter(), set(), set()
            for seed in range(600):
                grid = MODULE.generate(seed, seed * 11 + 1, difficulty=band)
                profiles[MODULE.observe_overrides(grid)["scene_profile"]] += 1
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, MODULE.rule_mirror(grid))))
            self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
            self.assertGreater(len(inputs), 470)
            self.assertGreaterEqual(len(outputs), 11)

    def test_malformed_inputs_rejected(self):
        valid = MODULE.generate(401, 503, scene_profile="four_tetrominoes")
        mutations = []
        empty = [[0 for _ in row] for row in valid]; mutations.append(empty)
        merged = copy.deepcopy(valid)
        parts = MODULE._extract_components(merged); a, b = parts[0]["cells"], parts[1]["cells"]
        ar, ac = min(a); br, bc = min(b)
        for c in range(min(ac, bc), max(ac, bc) + 1): merged[ar][c] = merged[ar][ac]
        mutations.append(merged)
        mixed = copy.deepcopy(valid); r, c = next(iter(MODULE._extract_components(mixed)[0]["cells"])); mixed[r][c] = 9
        mutations.append(mixed)
        duplicate_color = copy.deepcopy(valid)
        first, second = MODULE._extract_components(duplicate_color)[:2]
        color = duplicate_color[next(iter(first["cells"]))[0]][next(iter(first["cells"]))[1]]
        for r, c in second["cells"]: duplicate_color[r][c] = color
        mutations.append(duplicate_color)
        ragged = copy.deepcopy(valid); ragged[0].pop(); mutations.append(ragged)
        invalid = copy.deepcopy(valid); invalid[0][0] = 10; mutations.append(invalid)
        boolean = copy.deepcopy(valid); boolean[0][0] = True; mutations.append(boolean)
        for mutation in mutations:
            self.assertTrue(MODULE.self_check(mutation), mutation)

    def test_determinism_freshness_rng_and_unknown_axes(self):
        for overrides in ({"scene_profile": "unknown"}, {"grid_h": 8}, {"texture": "warm"}):
            with self.assertRaises(ValueError): MODULE.generate(1, 2, **overrides)
        random.seed(20260721); state = random.getstate()
        first = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(first, second); self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))

    def test_source_sync_and_rule_pin(self):
        source = canonical_row()["program_solution"]
        data_root = canonical_path(ROOT).parents[1]
        base = json.loads((data_root / "base/solutions/banks/0f1ff2289d6f/H74__60c56114260f.json").read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)
        self.assertEqual(MODULE.RULE_HASH, hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12])
        self.assertEqual(MODULE.RULE_HASH, "10e74a39671a")


if __name__ == "__main__":
    unittest.main()
