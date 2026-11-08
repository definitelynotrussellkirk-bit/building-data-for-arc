"""Regression tests for the linked-profile transform-code generator repair."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = (
    ROOT / "puzzle_generators" / "per_puzzle" / "d7a79f2f335e" / "generator.py"
)


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_d7a79f2f335e", GENERATOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") != "d7a79f2f335e":
                continue
            tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
            pairs = [*row["train"], *tests]
            return [
                {
                    "input": [[int(value) for value in row] for row in pair["input"]],
                    "output": [[int(value) for value in row] for row in pair["output"]],
                }
                for pair in pairs
            ]
    raise AssertionError("canonical task d7a79f2f335e is missing")


class TransformCodeGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = load_generator()

    def test_rule_mirror_and_self_check_match_every_canonical_pair(self):
        signatures = set()
        for pair in canonical_pairs():
            self.assertEqual([], self.generator.self_check(pair["input"]))
            self.assertEqual([], self.generator.strict_canonical_like(pair["input"]))
            self.assertEqual(pair["output"], self.generator.rule_mirror(pair["input"]))
            signatures.add(self.generator.profile_signature(pair["input"]))
        self.assertEqual(self.generator._CANONICAL_SIGNATURES, signatures)

    def test_every_three_example_window_contains_a_decisive_anchor(self):
        for band in ("easy", "medium", "hard"):
            for start in range(32):
                demos = []
                for offset in range(self.generator.EXAMPLES_NEEDED):
                    grid = self.generator.generate(1000 + start, start + offset, difficulty=band)
                    demos.append({"input": grid, "output": self.generator.rule_mirror(grid)})
                query_grid = self.generator.generate(
                    1000 + start,
                    start + self.generator.EXAMPLES_NEEDED,
                    difficulty=band,
                )
                query = {
                    "input": query_grid,
                    "output": self.generator.rule_mirror(query_grid),
                }
                self.assertEqual(
                    [],
                    self.generator.lesson_identifiable(demos, query),
                    msg=f"band={band} start={start}",
                )

    def test_profile_override_is_exact_and_unknown_axes_reject(self):
        for profile in self.generator.PROFILE_NAMES:
            grid = self.generator.generate(77, 9, difficulty="hard", profile=profile)
            self.assertEqual({"profile": profile}, self.generator.observe_overrides(grid))
            self.assertEqual([], self.generator.self_check(grid))
        with self.assertRaisesRegex(ValueError, "unknown override"):
            self.generator.generate(77, 9, typo_profile="l_two_all")

    def test_negative_recombination_and_all_mutations_are_rejected(self):
        fixtures = dict(self.generator.mutation_fixtures())
        recombined = fixtures["negative_linked_recombination"]
        self.assertTrue(self.generator.self_check(recombined))
        self.assertTrue(self.generator.strict_canonical_like(recombined))
        for name, grid in fixtures.items():
            with self.subTest(name=name):
                self.assertTrue(self.generator.self_check(grid))

    def test_all_profiles_and_strict_floor_are_reached_per_band(self):
        for band in ("easy", "medium", "hard"):
            counts = {profile: 0 for profile in self.generator.PROFILE_NAMES}
            strict = 0
            for index in range(400):
                grid = self.generator.generate(50000 + index, index * 13 + 7, difficulty=band)
                counts[self.generator.observe_overrides(grid)["profile"]] += 1
                strict += not self.generator.strict_canonical_like(grid)
            with self.subTest(band=band, counts=counts):
                self.assertTrue(all(count > 0 for count in counts.values()))
                self.assertGreaterEqual(strict / 400, self.generator.MIN_STRICT_FRAC)


if __name__ == "__main__":
    unittest.main()
