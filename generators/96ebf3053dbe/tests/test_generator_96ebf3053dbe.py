from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from reviewer_support import canonical_path, find_root

TASK_ID = "96ebf3053dbe"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = find_root(__file__)
DATA_ROOT = canonical_path(ROOT).parent.parent
BASE = DATA_ROOT / "base/solutions/training/c9680e90__96ebf3053dbe.json"


def canonical_rows():
    return [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if json.loads(line).get("task_id") == TASK_ID]


def canonical_pairs():
    return [pair for row in canonical_rows() for pair in row["train"] + row["test"]]


class GeneratorTests(unittest.TestCase):
    def test_all_canonical_pairs(self):
        self.assertEqual(len(canonical_rows()), 1)
        self.assertEqual(len(canonical_pairs()), 4)
        for pair in canonical_pairs():
            self.assertEqual(MODULE.self_check(pair["input"]), [])
            self.assertEqual(MODULE.rule_mirror(pair["input"]), pair["output"])

    def test_public_profiles_are_exact_and_fresh(self):
        for profile, pair in zip(MODULE.PUBLIC_PROFILES, canonical_pairs()):
            self.assertEqual(MODULE.canonical_profile_signature(pair["input"]), profile)
            grid = MODULE.generate(7, 11, scene_profile=profile)
            self.assertEqual(grid, pair["input"])
            self.assertIsNot(grid, MODULE._PUBLIC_INPUTS[profile])
            self.assertIsNot(grid[0], MODULE._PUBLIC_INPUTS[profile][0])

    def test_every_general_profile_and_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.GENERAL_PROFILES:
                for seed in range(35):
                    grid = MODULE.generate(seed, seed * 29, difficulty=band, scene_profile=profile)
                    analysis = MODULE._analysis(grid)
                    self.assertEqual(analysis["errors"], [])
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MODULE.rule_mirror(grid), analysis["output"])

    def test_endpoint_transfer_semantics(self):
        seen = set()
        lengths = set()
        for profile in MODULE.GENERAL_PROFILES:
            for seed in range(100):
                grid = MODULE.generate(seed, seed * 31, scene_profile=profile)
                analysis = MODULE._analysis(grid)
                divider = analysis["divider"]
                output = analysis["output"]
                for record in analysis["records"]:
                    seen.add((record["orientation"], record["anchor_direction"]))
                    lengths.add(len(record["cells"]))
                    chosen = record["chosen"]
                    reflected = record["reflected"]
                    self.assertEqual(output[chosen[0]][chosen[1]], 2)
                    self.assertEqual(output[reflected[0]][reflected[1]], 5)
                    self.assertEqual(reflected[0], 2 * divider - chosen[0])
                    for cell in record["cells"] - {chosen}:
                        self.assertEqual(output[cell[0]][cell[1]], 7)
                    anchor = record["anchor"]
                    self.assertEqual(output[anchor[0]][anchor[1]], 7)
        self.assertTrue({("vertical", "top"), ("vertical", "bottom"), ("horizontal", "left"), ("horizontal", "right")}.issubset(seen))
        self.assertTrue({1, 2, 3, 4}.issubset(lengths))

    def test_distribution_and_dimensions(self):
        profiles, inputs, outputs, shapes, counts = Counter(), set(), set(), set(), set()
        for seed in range(3000):
            band = ("easy", "medium", "hard")[seed % 3]
            grid = MODULE.generate(seed, seed * 37, difficulty=band)
            analysis = MODULE._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, analysis["output"])))
            shapes.add((len(grid), len(grid[0])))
            counts.add(len(analysis["records"]))
        self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
        self.assertGreater(len(inputs), 2500)
        self.assertGreater(len(outputs), 2500)
        self.assertGreater(len(shapes), 25)
        self.assertEqual(counts, {2, 3, 4, 5})

    def test_strict_malformed_and_semantic_mutations(self):
        grid = MODULE.generate(5, 9, scene_profile="balanced")
        cases = [[], [[7]], [[True]], [[10]]]
        ragged = copy.deepcopy(grid)
        ragged[0].pop()
        cases.append(ragged)
        missing_divider = copy.deepcopy(grid)
        missing_divider[len(grid) // 2][0] = 7
        cases.append(missing_divider)
        orphan_two = copy.deepcopy(grid)
        orphan_two[len(grid) - 1][0] = 2
        cases.append(orphan_two)
        missing_five = copy.deepcopy(grid)
        rr, cc = next((r, c) for r, row in enumerate(missing_five) for c, v in enumerate(row) if v == 5)
        missing_five[rr][cc] = 7
        cases.append(missing_five)
        bent = copy.deepcopy(grid)
        record = MODULE._analysis(bent)["records"][0]
        r, c = next(iter(record["cells"]))
        for dr, dc in MODULE._DIRS:
            nr, nc = r + dr, c + dc
            if len(grid) // 2 < nr < len(grid) and 0 <= nc < len(grid[0]) and bent[nr][nc] == 7:
                bent[nr][nc] = 6
                break
        cases.append(bent)
        wrong_upper_color = copy.deepcopy(grid)
        wrong_upper_color[0][0] = 4
        cases.append(wrong_upper_color)
        for case in cases:
            self.assertTrue(MODULE.self_check(case), case)

    def test_override_errors_determinism_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "no_divider"}, {"grid_h": 9}):
            with self.assertRaises(ValueError):
                MODULE.generate(1, 2, **overrides)
        with self.assertRaises(ValueError):
            MODULE.generate(1, 2, difficulty="extreme")
        random.seed(37)
        before = random.getstate()
        first = MODULE.generate(17, 23, difficulty="hard")
        self.assertEqual(random.getstate(), before)
        other = MODULE.generate(91, 47, difficulty="easy")
        second = MODULE.generate(17, 23, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertNotEqual(first, other)

    def test_source_sync_and_rule_hash(self):
        source = canonical_rows()[0]["program_solution"]
        expected = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(MODULE.RULE_HASH, expected)
        base = json.loads(BASE.read_text())
        normalized = " ".join(source.split())
        self.assertEqual(" ".join(base["racket_target"]["raw_code"].split()), normalized)
        self.assertEqual(" ".join(base["racket_target"]["target_code"].split()), normalized)


if __name__ == "__main__":
    unittest.main()
