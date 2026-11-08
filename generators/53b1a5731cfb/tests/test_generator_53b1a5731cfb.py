from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path

TASK = "53b1a5731cfb"
MOD = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/base/solutions/banks/056856052daa/hard_p02__53b1a5731cfb.json"


def canonical_rows():
    return [
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    ]


def canonical_pairs():
    return [pair for row in canonical_rows() for pair in row["train"] + row["test"]]


class GeneratorTests(unittest.TestCase):
    def test_all_canonical_inputs_and_both_official_route_branches(self):
        pairs = canonical_pairs()
        self.assertEqual(len(pairs), 4)
        modes = []
        for pair in pairs:
            self.assertEqual(MOD.self_check(pair["input"]), [])
            self.assertEqual(MOD.rule_mirror(pair["input"]), pair["output"])
            modes.append(MOD.observe_overrides(pair["input"])["route_mode"])
        self.assertEqual(modes.count("key_door"), 2)
        self.assertEqual(modes.count("portal_bypass"), 2)

    def test_generated_inputs_have_the_canonical_marker_grammar(self):
        for band in ("easy", "medium", "hard"):
            for mode in ("key_door", "portal_bypass"):
                for seed in range(40):
                    grid = MOD.generate(seed, seed * 7, difficulty=band, route_mode=mode)
                    values = [value for row in grid for value in row]
                    self.assertEqual(set(values), {0, 2, 3, 4, 5, 6, 8})
                    self.assertEqual(
                        {color: values.count(color) for color in (2, 3, 4, 5, 6)},
                        {2: 1, 3: 1, 4: 1, 5: 1, 6: 2},
                    )
                    self.assertEqual(MOD.self_check(grid), [])
                    self.assertEqual(MOD.observe_overrides(grid)["route_mode"], mode)

    def test_key_door_and_portal_bypass_semantics_are_distinct(self):
        for band in ("easy", "medium", "hard"):
            key_grid = MOD.generate(101, 8, difficulty=band, route_mode="key_door")
            bypass_grid = MOD.generate(101, 9, difficulty=band, route_mode="portal_bypass")
            key_route = MOD._stateful_search(key_grid)
            bypass_route = MOD._stateful_search(bypass_grid)
            self.assertTrue((key_route.used_key, key_route.used_door, key_route.used_portal) == (True, True, True))
            self.assertTrue((bypass_route.used_key, bypass_route.used_door, bypass_route.used_portal) == (False, False, True))
            self.assertFalse(MOD._stateful_search(key_grid, allow_portal=False).reachable)
            self.assertFalse(MOD._stateful_search(key_grid, allow_door_after_key=False).reachable)
            self.assertFalse(MOD._stateful_search(bypass_grid, allow_portal=False).reachable)

    def test_four_example_schedule_always_covers_both_branches(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(50):
                modes = [
                    MOD.observe_overrides(MOD.generate(seed, index, difficulty=band))["route_mode"]
                    for index in range(MOD.EXAMPLES_NEEDED)
                ]
                self.assertEqual(modes, ["key_door", "portal_bypass", "key_door", "portal_bypass"])

    def test_exact_override_boundaries_are_observable(self):
        for band in ("easy", "medium", "hard"):
            for h in (9, 13):
                for w in (12, 17):
                    for mode in ("key_door", "portal_bypass"):
                        grid = MOD.generate(211, 13, difficulty=band, grid_h=h, grid_w=w, route_mode=mode)
                        self.assertEqual(
                            MOD.observe_overrides(grid),
                            {"grid_h": h, "grid_w": w, "route_mode": mode},
                        )

    def test_structural_self_check_rejects_targeted_impostors(self):
        source = MOD.generate(307, 4, difficulty="hard", route_mode="key_door")
        cases = {}
        cases["missing_key"] = copy.deepcopy(source)
        kr, kc = next((r, c) for r, row in enumerate(source) for c, v in enumerate(row) if v == 4)
        cases["missing_key"][kr][kc] = 0
        cases["singleton_portal"] = copy.deepcopy(source)
        pr, pc = next((r, c) for r, row in enumerate(source) for c, v in enumerate(row) if v == 6)
        cases["singleton_portal"][pr][pc] = 0
        cases["broken_border"] = copy.deepcopy(source)
        cases["broken_border"][0][1] = 0
        cases["door_removed"] = copy.deepcopy(source)
        dr, dc = next((r, c) for r, row in enumerate(source) for c, v in enumerate(row) if v == 5)
        cases["door_removed"][dr][dc] = 0
        cases["all_background"] = [[8 for _ in row] for row in source]
        for name, grid in cases.items():
            self.assertTrue(MOD.self_check(grid), name)

    def test_determinism_freshness_unknowns_and_global_rng(self):
        with self.assertRaises(ValueError):
            MOD.generate(1, 2, difficulty="extreme")
        for overrides in ({"texture": "default"}, {"route_mode": "bad"}, {"grid_h": 8}, {"grid_w": 18}):
            with self.assertRaises(ValueError):
                MOD.generate(1, 2, **overrides)
        random.seed(401)
        state = random.getstate()
        first = MOD.generate(409, 17, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MOD.generate(409, 17, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))

    def test_rule_hash_and_selected_authorities_are_synchronized(self):
        rows = canonical_rows()
        self.assertEqual(len(rows), 1)
        source = rows[0]["program_solution"]
        expected = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(MOD.RULE_HASH, expected)
        base = json.loads(BASE.read_text())
        self.assertEqual(base["racket_target"]["target_code"], source)
        self.assertNotEqual(base["racket_target"]["raw_code"], source)


if __name__ == "__main__":
    unittest.main()
