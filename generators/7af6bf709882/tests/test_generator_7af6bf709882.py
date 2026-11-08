from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path

TASK = "7af6bf709882"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASE_PATHS = (
    ROOT / "data/base/solutions/training/cad67732__7af6bf709882.json",
    ROOT / "data/base/solutions/augmented/cad67732__957bd73c5689.json",
)


def canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row
    raise AssertionError("canonical row missing")


def pairs(row):
    test = row["test"]
    return list(row["train"]) + ([test] if isinstance(test, dict) else list(test))


class GeneratorTests(unittest.TestCase):
    def test_canonical_and_all_assigned_base_pairs_are_accepted(self):
        canonical = canonical_row()
        self.assertEqual(len(pairs(canonical)), 4)
        seen = set()
        for pair in pairs(canonical):
            grid = pair["input"]
            self.assertEqual(MODULE.self_check(grid), [])
            self.assertEqual(MODULE.rule_mirror(grid), pair["output"])
            seen.add(tuple(map(tuple, grid)))

        accepted = 0
        for path in BASE_PATHS:
            row = json.loads(path.read_text())
            context = row["visible_context"]
            for pair in context["train"]:
                self.assertEqual(MODULE.self_check(pair["input"]), [], path)
                self.assertEqual(MODULE.rule_mirror(pair["input"]), pair["output"])
                accepted += 1
                seen.add(tuple(map(tuple, pair["input"])))
            for item in context["test_inputs"]:
                self.assertEqual(MODULE.self_check(item["input"]), [], path)
                accepted += 1
                seen.add(tuple(map(tuple, item["input"])))
        self.assertEqual(accepted, 8)
        self.assertEqual(len(seen), 4)

    def test_determinism_fresh_returns_global_rng_and_rule_hash(self):
        before = random.getstate()
        first = MODULE.generate(8103, 17, difficulty="hard")
        middle = random.getstate()
        second = MODULE.generate(8103, 17, difficulty="hard")
        after = random.getstate()
        self.assertEqual(before, middle)
        self.assertEqual(before, after)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9 if first[0][0] != 9 else 8
        self.assertNotEqual(first, second)

        source = canonical_row()["program_solution"]
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(MODULE.RULE_HASH, digest)
        for path in BASE_PATHS:
            target = json.loads(path.read_text())["racket_target"]["target_code"]
            self.assertEqual(target, source)

    def test_override_boundaries_are_exact_and_observable(self):
        bounds = {
            "grid_h": (5, 15),
            "grid_w": (5, 15),
            "period_r": (2, 5),
            "period_c": (-4, 4),
            "motif_size": (2, 9),
            "palette_size": (2, 4),
        }
        seed = 7000
        for axis, values in bounds.items():
            for value in values:
                for band in ("easy", "medium", "hard"):
                    grid = MODULE.generate(seed, seed % 31, difficulty=band, **{axis: value})
                    self.assertEqual(MODULE.self_check(grid), [], (axis, value, band))
                    self.assertEqual(MODULE.observe_overrides(grid)[axis], value)
                    seed += 1

        exact = dict(
            grid_h=10, grid_w=10, period_r=3, period_c=3,
            motif_size=6, palette_size=3,
        )
        grid = MODULE.generate(99, 3, **exact)
        self.assertEqual(MODULE.observe_overrides(grid), exact)
        with self.assertRaises(ValueError):
            MODULE.generate(1, 1, grid_h=5, period_r=5)
        with self.assertRaises(ValueError):
            MODULE.generate(1, 1, palette_size=4, motif_size=2)
        with self.assertRaises(ValueError):
            MODULE.generate(1, 1, unknown_axis=3)

    def test_default_schedule_teaches_all_column_anchor_branches(self):
        signs = []
        examples = []
        for sample_index in range(4):
            grid = MODULE.generate(123456, sample_index)
            analysis = MODULE._analyze(grid)
            signs.append((analysis["period_c"] > 0) - (analysis["period_c"] < 0))
            examples.append({"input": grid, "output": MODULE.rule_mirror(grid)})
        self.assertEqual(set(signs[:3]), {-1, 0, 1})
        self.assertEqual(MODULE.lesson_identifiable(examples[:3], examples[3]), [])

    def test_generated_periods_are_same_lattice_and_answer_equivalent(self):
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for seed in range(80):
                grid = MODULE.generate(
                    900000 + seed, seed * 13 + band_index, difficulty=band
                )
                analysis = MODULE._analyze(grid)
                pr, pc = analysis["period_r"], analysis["period_c"]
                expected = MODULE.rule_mirror(grid)
                for dr, dc, _ in analysis["periods"]:
                    self.assertEqual(dr % pr, 0)
                    self.assertEqual(dc, (dr // pr) * pc)
                    self.assertEqual(
                        MODULE._solve_with_period(grid, (dr, dc)), expected
                    )

    def test_semantic_mutations_fail_closed(self):
        fixtures = MODULE.mutation_fixtures()
        self.assertGreaterEqual(len(fixtures), 6)
        for name, grid in fixtures:
            self.assertTrue(MODULE.self_check(grid), name)


if __name__ == "__main__":
    unittest.main()
