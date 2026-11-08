"""Focused semantic regressions for generator 6cc68e9e1125."""

from __future__ import annotations

import importlib.util
import json
import random
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = (
    ROOT
    / "puzzle_generators"
    / "per_puzzle"
    / "6cc68e9e1125"
    / "generator.py"
)


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_6cc68e9e1125",
        GENERATOR_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") != "6cc68e9e1125":
                continue
            test = row["test"]
            tests = [test] if isinstance(test, dict) else test
            return [*row["train"], *tests]
    raise AssertionError("canonical task 6cc68e9e1125 is missing")


class MergeConflictGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()

    def test_all_canonical_pairs_are_exact_and_linked(self):
        pairs = canonical_pairs()
        self.assertEqual(3, len(pairs))
        self.assertEqual(
            {"public_profile_1", "public_profile_2", "public_profile_3"},
            {
                self.generator.canonical_profile_signature(pair["input"])
                for pair in pairs
            },
        )
        for pair in pairs:
            self.assertEqual([], self.generator.self_check(pair["input"]))
            self.assertEqual(
                pair["output"],
                self.generator.rule_mirror(pair["input"]),
            )

    def test_every_generated_scene_contains_a_true_worked_example(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(180):
                grid = self.generator.generate(
                    seed,
                    seed * 23 + 9,
                    difficulty=band,
                )
                analysis = self.generator._analyze(grid)
                self.assertEqual([], analysis["errors"])
                panels = analysis["facts"]["panels"]
                self.assertEqual(
                    panels[2],
                    self.generator._merge(panels[0], panels[1]),
                )
                self.assertEqual(
                    analysis["facts"]["output"],
                    self.generator._merge(panels[3], panels[4]),
                )

    def test_linked_branch_reaches_every_public_profile_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            profiles = set()
            distinct = set()
            exact_public = 0
            for seed in range(360):
                grid = self.generator.generate(
                    10_000 + seed,
                    seed,
                    difficulty=band,
                    scene_family="linked",
                )
                signature = self.generator.canonical_profile_signature(grid)
                profiles.add(signature)
                distinct.add(tuple(map(tuple, grid)))
                exact_public += tuple(map(tuple, grid)) in {
                    tuple(map(tuple, public))
                    for public in self.generator._PUBLIC_INPUTS
                }
            with self.subTest(band=band):
                self.assertEqual(
                    {"public_profile_1", "public_profile_2", "public_profile_3"},
                    profiles,
                )
                self.assertGreaterEqual(len(distinct), 280)
                self.assertGreater(exact_public, 0)
                self.assertLess(exact_public, 75)

    def test_generalized_branch_exercises_equal_and_conflict_relations(self):
        expected_sizes = {"easy": 3, "medium": 4, "hard": 5}
        for band, size in expected_sizes.items():
            relations = set()
            for seed in range(160):
                grid = self.generator.generate(
                    30_000 + seed,
                    seed,
                    difficulty=band,
                    scene_family="generalized",
                )
                analysis = self.generator._analyze(grid)
                self.assertEqual([], analysis["errors"])
                self.assertEqual("generalized", analysis["facts"]["scene_family"])
                self.assertEqual(size, analysis["facts"]["panel_size"])
                relations.add(
                    (
                        analysis["facts"]["relation"],
                        analysis["facts"]["query_relation"],
                    )
                )
            with self.subTest(band=band):
                self.assertEqual(
                    {("equal", "equal"), ("conflict", "conflict")},
                    relations,
                )

    def test_structural_checker_rejects_targeted_impostors(self):
        base = self.generator.generate(
            77,
            11,
            difficulty="medium",
            scene_family="generalized",
        )
        mutations = []

        missing_separator = [row[:] for row in base]
        missing_separator[0][4] = 0
        mutations.append(missing_separator)

        wrong_key_result = [row[:] for row in base]
        wrong_key_result[0][10] = (
            1 if wrong_key_result[0][10] != 1 else 2
        )
        mutations.append(wrong_key_result)

        blank_query_operand = [row[:] for row in base]
        panels = self.generator._split_panels(blank_query_operand)
        for row in range(len(blank_query_operand)):
            left = self.generator._panel_left(4, len(panels[4][0]))
            for col in range(len(panels[4][0])):
                blank_query_operand[row][left + col] = 0
        mutations.append(blank_query_operand)

        panels = [
            [row[:] for row in panel]
            for panel in self.generator._split_panels(base)
        ]
        for row in range(len(panels[1])):
            for col in range(len(panels[1][0])):
                if panels[0][row][col] != 0:
                    panels[1][row][col] = 0
        panels[2] = self.generator._merge(panels[0], panels[1])
        no_demo_overlap = self.generator._assemble(tuple(panels))
        mutations.append(no_demo_overlap)

        for index, mutation in enumerate(mutations):
            with self.subTest(index=index):
                self.assertTrue(self.generator.self_check(mutation))

    def test_cross_profile_recombination_is_lawful_but_not_linked(self):
        first = self.generator._split_panels(canonical_pairs()[1]["input"])
        second = self.generator._split_panels(canonical_pairs()[2]["input"])
        recombined = self.generator._assemble(
            (first[0], first[1], first[2], second[3], second[4])
        )

        self.assertEqual([], self.generator.self_check(recombined))
        self.assertTrue(
            self.generator.canonical_profile_signature(recombined).startswith(
                "generalized:"
            )
        )

    def test_replay_is_deterministic_fresh_and_global_rng_pure(self):
        state = random.getstate()
        first = self.generator.generate(111, 222, difficulty="hard")
        self.assertEqual(state, random.getstate())
        second = self.generator.generate(111, 222, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9 if first[0][0] != 9 else 8
        third = self.generator.generate(111, 222, difficulty="hard")
        self.assertEqual(second, third)

    def test_bad_calls_fail_loudly(self):
        with self.assertRaises(ValueError):
            self.generator.generate(1, 2, difficulty="impossible")
        with self.assertRaises(ValueError):
            self.generator.generate(1, 2, fake_axis=True)


if __name__ == "__main__":
    unittest.main()
