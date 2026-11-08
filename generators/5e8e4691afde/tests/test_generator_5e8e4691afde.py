"""Focused semantic regressions for generator 5e8e4691afde."""
from __future__ import annotations

import copy
import hashlib
import json
import random
import unittest
from collections import Counter
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "5e8e4691afde"
ROOT = find_root(__file__)
MODULE, _, _ = load_selected_generator(TASK_ID, root=ROOT)
DATA_ROOT = canonical_path(ROOT).parent.parent


def canonical_row():
    return next(json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()
                if json.loads(line).get("task_id") == TASK_ID)


class Generator5e8e4691afdeTests(unittest.TestCase):
    def test_all_five_canonical_pairs(self):
        pairs = canonical_row()["train"] + canonical_row()["test"]
        self.assertEqual(len(pairs), 5)
        for index, pair in enumerate(pairs):
            self.assertEqual(MODULE.rule_mirror(pair["input"]), pair["output"])
            self.assertEqual(MODULE.canonical_profile_signature(pair["input"]), MODULE.PUBLIC_PROFILES[index])

    def test_public_profiles_are_exact(self):
        expected = [pair["input"] for pair in canonical_row()["train"] + canonical_row()["test"]]
        self.assertEqual([MODULE.generate(1, 2, scene_profile=p) for p in MODULE.PUBLIC_PROFILES], expected)

    def test_every_profile_and_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.SCENE_PROFILES:
                for seed in range(20):
                    grid = MODULE.generate(seed, seed * 17 + 3, difficulty=band, scene_profile=profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MODULE.self_check(grid), [])

    def test_rule_geometry(self):
        for profile in MODULE.SCENE_PROFILES:
            grid = MODULE.generate(101, 203, scene_profile=profile)
            info = MODULE._analysis(grid)
            output = MODULE.rule_mirror(grid)
            nr, nc = info["new_center"]
            self.assertEqual(output[nr][nc], info["color"])
            for r in range(len(output)):
                for c in range(len(output[0])):
                    if (r, c) != (nr, nc) and (r - c == nr - nc or r + c == nr + nc):
                        self.assertEqual(output[r][c], 4)

    def test_path_vector_relocates_frame(self):
        for profile, shift in MODULE.GENERAL_SHIFTS.items():
            info = MODULE._analysis(MODULE.generate(211, 307, scene_profile=profile))
            self.assertEqual(info["shift"], shift)
            self.assertEqual(info["new_center"],
                             (info["center"][0] + shift[0], info["center"][1] + shift[1]))

    def test_default_census_and_diversity(self):
        for band in ("easy", "medium", "hard"):
            profiles, inputs, outputs = Counter(), set(), set()
            for seed in range(500):
                grid = MODULE.generate(seed, seed * 11 + 1, difficulty=band)
                profiles[MODULE.observe_overrides(grid)["scene_profile"]] += 1
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, MODULE.rule_mirror(grid))))
            self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
            self.assertGreater(len(inputs), 400)
            self.assertGreater(len(outputs), 390)

    def test_malformed_inputs_rejected(self):
        valid = MODULE.generate(401, 503, scene_profile="diagonal_down_right")
        mutations = []
        empty = [[0 for _ in row] for row in valid]; mutations.append(empty)
        no_gray = copy.deepcopy(valid)
        for r, row in enumerate(no_gray):
            for c, value in enumerate(row):
                if value == 5: no_gray[r][c] = 0
        mutations.append(no_gray)
        disconnected = copy.deepcopy(valid)
        disconnected[0][0] = 5; mutations.append(disconnected)
        extra4 = copy.deepcopy(valid); extra4[0][0] = 4; mutations.append(extra4)
        third_color = copy.deepcopy(valid); third_color[0][0] = 2; mutations.append(third_color)
        ragged = copy.deepcopy(valid); ragged[0].pop(); mutations.append(ragged)
        invalid = copy.deepcopy(valid); invalid[0][0] = 10; mutations.append(invalid)
        boolean = copy.deepcopy(valid); boolean[0][0] = True; mutations.append(boolean)
        for mutation in mutations:
            self.assertTrue(MODULE.self_check(mutation), mutation)

    def test_determinism_freshness_rng_and_unknown_axes(self):
        for overrides in ({"scene_profile": "unknown"}, {"grid_size": 15}, {"texture": "warm"}):
            with self.assertRaises(ValueError): MODULE.generate(1, 2, **overrides)
        random.seed(20260721); state = random.getstate()
        first = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(first, second); self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))

    def test_source_sync_and_rule_pin(self):
        source = canonical_row()["program_solution"]
        base = json.loads((DATA_ROOT / "base/solutions/training/2b9ef948__5e8e4691afde.json").read_text())
        # The base authority is compact; the canonical rule is pretty-printed.
        # RULE_HASH uses this same whitespace normalization.
        self.assertEqual(" ".join(base["racket_target"]["raw_code"].split()), " ".join(source.split()))
        self.assertEqual(" ".join(base["racket_target"]["target_code"].split()), " ".join(source.split()))
        self.assertEqual(MODULE.RULE_HASH, hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12])
        self.assertEqual(MODULE.RULE_HASH, "ee2251228926")


if __name__ == "__main__":
    unittest.main()
