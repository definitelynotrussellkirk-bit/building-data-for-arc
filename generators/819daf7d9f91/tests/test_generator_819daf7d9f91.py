"""Focused regressions for Guided L-Paths generator 819daf7d9f91."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "819daf7d9f91"
gen = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _canonical_task():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"canonical task {TASK_ID} not found")


def _blank(height=10, width=11):
    return [[0 for _ in range(width)] for _ in range(height)]


class TestCanonicalRuleAndHash(unittest.TestCase):
    def test_rule_hash_matches_canonical_program(self):
        task = _canonical_task()
        source = task["program_solution"]
        actual = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(gen.RULE_HASH, actual)

    def test_all_canonical_inputs_are_accepted(self):
        task = _canonical_task()
        for split in ("train", "test"):
            pairs = task[split] if isinstance(task[split], list) else [task[split]]
            for index, pair in enumerate(pairs):
                input_grid = [[int(value) for value in row] for row in pair["input"]]
                output_grid = [[int(value) for value in row] for row in pair["output"]]
                self.assertEqual(
                    gen.self_check(input_grid),
                    [],
                    f"canonical {split}[{index}] was rejected",
                )
                self.assertEqual(gen._rule_mirror(input_grid), output_grid)


class TestOverrideAndLessonContract(unittest.TestCase):
    def test_exact_axes_are_observable_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for scene_profile in gen.SCENE_PROFILES:
                for grid_profile in gen.GRID_PROFILES:
                    grid = gen.generate(
                        9137,
                        29,
                        difficulty=band,
                        scene_profile=scene_profile,
                        grid_profile=grid_profile,
                    )
                    self.assertEqual(gen.self_check(grid), [])
                    self.assertEqual(
                        gen.observe_overrides(grid),
                        {
                            "scene_profile": scene_profile,
                            "grid_profile": grid_profile,
                        },
                    )

    def test_invalid_contract_inputs_reject_loudly(self):
        for kwargs in (
            {"scene_profile": "cmd3_pairs1"},
            {"grid_profile": "tiny"},
            {"unknown_axis": True},
        ):
            with self.assertRaises(ValueError, msg=f"did not reject {kwargs}"):
                gen.generate(1, 2, **kwargs)
        with self.assertRaises(ValueError):
            gen.generate(1, 2, difficulty="extreme")

    def test_every_four_scheduled_examples_refute_named_rivals(self):
        for band in ("easy", "medium", "hard"):
            for start in (0, 4, 8, 12):
                demos = []
                for sample_index in range(start, start + 4):
                    grid = gen.generate(
                        77_000 + start,
                        sample_index,
                        difficulty=band,
                    )
                    demos.append({"input": grid, "output": gen._rule_mirror(grid)})
                self.assertEqual(
                    gen.lesson_identifiable(demos, demos[-1]["input"]),
                    [],
                    f"lesson failed for {band} starting at {start}",
                )
                observed = [gen.observe_overrides(d["input"]) for d in demos]
                commands = {int(row["scene_profile"][3]) for row in observed}
                pair_counts = {
                    int(row["scene_profile"].split("pairs", 1)[1])
                    for row in observed
                }
                self.assertEqual(commands, {1, 2})
                self.assertTrue(any(count >= 3 for count in pair_counts))


class TestSelfCheckMutations(unittest.TestCase):
    def test_rejects_targeted_impostors(self):
        valid = gen.generate(
            4,
            0,
            difficulty="medium",
            scene_profile="cmd1_pairs2",
            grid_profile="canonical",
        )
        mutations = {}

        no_command = copy.deepcopy(valid)
        no_command[0][0] = 0
        mutations["no command"] = no_command

        no_pairs = _blank()
        no_pairs[0][0] = 1
        mutations["no endpoint pairs"] = no_pairs

        singleton = copy.deepcopy(valid)
        facts = gen._analyze(singleton)["facts"]
        color = facts["colors"][0]
        second = facts["markers"][color][1]
        singleton[second[0]][second[1]] = 0
        mutations["singleton endpoint"] = singleton

        collinear = _blank()
        collinear[0][0] = 1
        collinear[2][2] = 3
        collinear[2][7] = 3
        mutations["collinear endpoints"] = collinear

        repeated_command = copy.deepcopy(valid)
        repeated_command[-1][-1] = repeated_command[0][0]
        mutations["repeated command color"] = repeated_command

        triple = copy.deepcopy(valid)
        facts = gen._analyze(triple)["facts"]
        color = facts["colors"][0]
        empty = next(
            (row, col)
            for row in range(1, len(triple))
            for col in range(len(triple[0]))
            if triple[row][col] == 0
        )
        triple[empty[0]][empty[1]] = color
        mutations["three markers for one endpoint color"] = triple

        for name, grid in mutations.items():
            self.assertTrue(gen.self_check(grid), f"accepted impostor: {name}")
            with self.assertRaises(ValueError, msg=f"observed impostor: {name}"):
                gen.observe_overrides(grid)


class TestDeterminism(unittest.TestCase):
    def test_replay_freshness_and_process_rng_state(self):
        random.seed(0x819DAF)
        before = random.getstate()
        first = gen.generate(12345, 678, difficulty="hard")
        after = random.getstate()
        second = gen.generate(12345, 678, difficulty="hard")
        self.assertEqual(before, after)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(row_a is not row_b for row_a, row_b in zip(first, second)))
        snapshot = copy.deepcopy(second)
        first[0][0] = 9
        self.assertEqual(second, snapshot)


if __name__ == "__main__":
    unittest.main()
