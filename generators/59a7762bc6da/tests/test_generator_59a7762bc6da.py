"""Focused semantic regressions for generator 59a7762bc6da."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

TASK_ID = "59a7762bc6da"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]


def canonical_row():
    return next(
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )


def rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


class Generator59a7762bc6daTests(unittest.TestCase):
    def test_all_four_canonical_pairs(self):
        pairs = canonical_row()["train"] + canonical_row()["test"]
        self.assertEqual(len(pairs), 4)
        for index, pair in enumerate(pairs):
            self.assertEqual(MODULE.rule_mirror(pair["input"]), pair["output"])
            self.assertEqual(MODULE.canonical_profile_signature(pair["input"]), MODULE.PUBLIC_PROFILES[index])

    def test_public_profiles_are_exact(self):
        expected = [pair["input"] for pair in canonical_row()["train"] + canonical_row()["test"]]
        actual = [MODULE.generate(1, 2, scene_profile=profile) for profile in MODULE.PUBLIC_PROFILES]
        self.assertEqual(actual, expected)

    def test_every_profile_and_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.SCENE_PROFILES:
                for seed in range(25):
                    grid = MODULE.generate(seed, seed * 19 + 3, difficulty=band, scene_profile=profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MODULE.self_check(grid), [])
                    self.assertNotEqual(MODULE.rule_mirror(grid), grid)

    def test_exact_component_recoloring(self):
        for profile in MODULE.SCENE_PROFILES:
            grid = MODULE.generate(101, 203, scene_profile=profile)
            output = MODULE.rule_mirror(grid)
            info = MODULE._analysis(grid)
            for component in info["components"]:
                expected = 8 if MODULE._diagonal_features(component)[0] >= 3 else 5
                self.assertTrue(all(output[r][c] == expected for r, c in component))
            self.assertTrue(all(output[r][c] == 7 for r, row in enumerate(grid) for c, value in enumerate(row) if value == 7))

    def test_positive_geometry_profiles(self):
        infos = {profile: MODULE._analysis(MODULE.generate(211, 307, scene_profile=profile)) for profile in (
            "single_down_right", "single_down_left", "bidirectional_x", "long_diagonal",
            "branched_positive", "edge_positive", "multiple_positive",
        )}
        self.assertEqual(MODULE._diagonal_features(infos["single_down_right"]["positive_components"][0])[1], frozenset({(1, 1)}))
        self.assertEqual(MODULE._diagonal_features(infos["single_down_left"]["positive_components"][0])[1], frozenset({(1, -1)}))
        self.assertEqual(len(MODULE._diagonal_features(infos["bidirectional_x"]["positive_components"][0])[1]), 2)
        self.assertGreaterEqual(infos["long_diagonal"]["max_diagonal"], 5)
        self.assertGreaterEqual(len(infos["branched_positive"]["positive_components"][0]), 6)
        self.assertTrue(any(MODULE._touches_edge(item, infos["edge_positive"]["height"], infos["edge_positive"]["width"])
                            for item in infos["edge_positive"]["positive_components"]))
        self.assertGreaterEqual(infos["multiple_positive"]["positive_count"], 2)

    def test_negative_witness_profiles(self):
        mixed = MODULE._analysis(MODULE.generate(223, 311, scene_profile="mixed_component_sizes"))
        singles = MODULE._analysis(MODULE.generate(227, 313, scene_profile="negative_singletons"))
        orthogonal = MODULE._analysis(MODULE.generate(229, 317, scene_profile="negative_orthogonal_runs"))
        near = MODULE._analysis(MODULE.generate(233, 319, scene_profile="near_miss_diagonal"))
        dense = MODULE._analysis(MODULE.generate(239, 323, scene_profile="dense_negative_component"))
        self.assertTrue({1, 2, 4}.issubset({len(item) for item in mixed["negative_components"]}))
        self.assertGreaterEqual(len(singles["negative_components"]), 4)
        self.assertTrue(all(len(item) == 1 for item in singles["negative_components"]))
        self.assertTrue(any(len(item) >= 4 and (_bbox_dim(item)[0] == 1 or _bbox_dim(item)[1] == 1)
                            for item in orthogonal["negative_components"]))
        self.assertTrue(any(len(item) == 4 and MODULE._diagonal_features(item)[0] == 2 for item in near["negative_components"]))
        self.assertTrue(any(len(item) >= 8 and MODULE._diagonal_features(item)[0] == 2 for item in dense["negative_components"]))

    def test_default_census_and_diversity(self):
        for band in ("easy", "medium", "hard"):
            profiles = Counter()
            pairs = set()
            for seed in range(800):
                grid = MODULE.generate(seed, seed * 11 + 1, difficulty=band)
                profiles[MODULE.observe_overrides(grid)["scene_profile"]] += 1
                pairs.add((tuple(map(tuple, grid)), tuple(map(tuple, MODULE.rule_mirror(grid)))))
            self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
            public = sum(profiles[profile] for profile in MODULE.PUBLIC_PROFILES)
            self.assertTrue(140 < public < 270)
            # Exact public lessons intentionally repeat; among the roughly
            # 600 generalized draws this still requires near-total uniqueness.
            self.assertGreater(len(pairs), 560)

    def test_minimal_and_malformed_inputs_rejected(self):
        h, w = 10, 12
        orange = [[7] * w for _ in range(h)]
        singleton = copy.deepcopy(orange); singleton[3][3] = 5
        line = copy.deepcopy(orange); line[3][2:6] = [5] * 4
        block = copy.deepcopy(orange); block[2][2] = block[2][3] = block[3][2] = block[3][3] = 5
        full_gray = [[5] * w for _ in range(h)]
        valid = MODULE.generate(401, 503, scene_profile="mixed_component_sizes")
        ragged = copy.deepcopy(valid); ragged[0].pop()
        invalid = copy.deepcopy(valid); invalid[0][0] = 4
        boolean = copy.deepcopy(valid); boolean[0][0] = True
        for mutation in (orange, singleton, line, block, full_gray, ragged, invalid, boolean):
            self.assertTrue(MODULE.self_check(mutation), mutation)
        self.assertTrue(MODULE.self_check(valid, meta={"overrides": {"scene_profile": "multiple_positive"}}))

    def test_determinism_freshness_rng_and_unknown_axes(self):
        for overrides in ({"scene_profile": "unknown"}, {"grid_h": 10}, {"texture": "warm"}, {"palette_kind": "cool"}):
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

    def test_source_sync_and_rule_pin(self):
        source = canonical_row()["program_solution"]
        base = json.loads((ROOT / "data/base/solutions/training/ecb67b6d__59a7762bc6da.json").read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)
        self.assertEqual(base["primitive_metadata"]["primitive_chain"], [
            "find-first", "fst", "snd", "flatmap", "map", "foldl", "obj-cells", "recolor-cells", "objects-8",
        ])
        self.assertEqual(MODULE.RULE_HASH, rule_hash(source))
        self.assertEqual(MODULE.RULE_HASH, "108478b11257")


def _bbox_dim(component):
    r0, c0, r1, c1 = MODULE._bbox(component)
    return r1 - r0 + 1, c1 - c0 + 1


if __name__ == "__main__":
    unittest.main()
