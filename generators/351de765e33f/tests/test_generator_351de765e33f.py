from __future__ import annotations

import copy
import hashlib
import json
import unittest

import importlib

gen = importlib.import_module("puzzle_generators.per_puzzle.351de765e33f.generator")


class Generator351de765e33fTests(unittest.TestCase):
    def test_rule_hash_pins_canonical_source(self):
        with open("data/canonical/puzzles.jsonl", encoding="utf-8") as handle:
            row = next(
                json.loads(line)
                for line in handle
                if '"task_id": "351de765e33f"' in line
            )
        digest = hashlib.sha256(
            " ".join(row["program_solution"].split()).encode()
        ).hexdigest()[:12]
        self.assertEqual(gen.RULE_HASH, digest)

    def test_every_profile_is_exactly_observable_and_self_checked(self):
        for index, profile in enumerate(gen.SCENE_PROFILES):
            grid = gen.generate(
                seed=1000 + index,
                sample_index=index,
                difficulty="medium",
                scene_profile=profile,
            )
            self.assertEqual(gen.observe_overrides(grid), {"scene_profile": profile})
            self.assertEqual(gen.self_check(grid), [])

    def test_each_band_schedule_covers_every_profile(self):
        for band in ("easy", "medium", "hard"):
            observed = {
                gen.observe_overrides(gen.generate(2000 + i, i, difficulty=band))[
                    "scene_profile"
                ]
                for i in range(16)
            }
            self.assertEqual(observed, set(gen.SCENE_PROFILES))

    def test_mirror_changes_exactly_rank_two(self):
        for index, profile in enumerate(gen.SCENE_PROFILES):
            grid = gen.generate(3000 + index, index, scene_profile=profile)
            signature = gen.semantic_signature(grid)
            out = gen.rule_mirror(grid)
            changed = {
                (row, col)
                for row in range(len(grid))
                for col in range(len(grid[0]))
                if grid[row][col] != out[row][col]
            }
            objects = gen._components(grid)
            self.assertEqual(len(changed), signature["target_size"])
            self.assertEqual(changed, set(objects[1]["cells"]))
            self.assertTrue(all(out[row][col] == 8 for row, col in changed))

    def test_self_check_rejects_targeted_impostors(self):
        base = gen.generate(4000, 0, scene_profile="canonical_942")
        objects = gen._components(base)

        missing_cell = copy.deepcopy(base)
        row, col = objects[0]["cells"][0]
        missing_cell[row][col] = 0

        reserved_cyan = copy.deepcopy(base)
        for row, col in objects[-1]["cells"]:
            reserved_cyan[row][col] = 8

        duplicate_color = copy.deepcopy(base)
        for row, col in objects[1]["cells"]:
            duplicate_color[row][col] = objects[0]["color"]

        extra_object = copy.deepcopy(base)
        occupied = {cell for obj in objects for cell in obj["cells"]}
        extra = next(
            (row, col)
            for row in range(len(base))
            for col in range(len(base[0]))
            if (row, col) not in occupied
            and all(
                (row + dr, col + dc) not in occupied
                for dr, dc in gen._DIR8
            )
        )
        extra_object[extra[0]][extra[1]] = 9

        for impostor in (missing_cell, reserved_cyan, duplicate_color, extra_object):
            self.assertTrue(gen.self_check(impostor))

    def test_deterministic_fresh_and_global_input_pure(self):
        first = gen.generate(5000, 9, difficulty="hard")
        second = gen.generate(5000, 9, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        frozen = copy.deepcopy(second)
        first[0][0] = (first[0][0] + 1) % 10
        self.assertEqual(gen.generate(5000, 9, difficulty="hard"), frozen)


if __name__ == "__main__":
    unittest.main()
