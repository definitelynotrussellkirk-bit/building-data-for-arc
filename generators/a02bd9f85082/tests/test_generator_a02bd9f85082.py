"""Focused semantic regressions for generator a02bd9f85082."""
from __future__ import annotations

import copy
import hashlib
import json
import random
import unittest
from pathlib import Path

from puzzle_generators.per_puzzle.a02bd9f85082 import generator as gen


ROOT = Path(__file__).resolve().parents[1]


def _parse_grid(value):
    if value and isinstance(value[0], str):
        return [[int(cell) for cell in row] for row in value]
    return copy.deepcopy(value)


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row["task_id"] == gen.TASK_ID:
                return row
    raise AssertionError("canonical task row is missing")


def _pairs(row):
    for split in ("train", "test"):
        values = row[split]
        values = values if isinstance(values, list) else [values]
        yield from values


class GeneratorA02bd9f85082Tests(unittest.TestCase):
    def test_rule_hash_and_all_canonical_pairs(self):
        row = _canonical_row()
        normalized = " ".join(row["program_solution"].split())
        digest = hashlib.sha256(normalized.encode()).hexdigest()
        self.assertEqual(gen.RULE_HASH, digest[:12])
        signatures = set()
        for pair in _pairs(row):
            source = _parse_grid(pair["input"])
            expected = _parse_grid(pair["output"])
            untouched = copy.deepcopy(source)
            self.assertEqual(gen.self_check(source), [])
            signatures.add(gen.canonical_profile_signature(source))
            self.assertEqual(gen.rule_mirror(source), expected)
            self.assertEqual(source, untouched)
        self.assertEqual(
            signatures,
            {f"public_profile_{index}" for index in range(1, 6)},
        )

    def test_every_band_and_family_is_valid_and_observable(self):
        for band in ("easy", "medium", "hard"):
            for family in gen.SCENE_FAMILIES:
                for seed in range(100):
                    grid = gen.generate(
                        seed,
                        seed % 5,
                        difficulty=band,
                        scene_family=family,
                    )
                    self.assertEqual(gen.self_check(grid), [])
                    self.assertEqual(
                        gen.observe_overrides(grid),
                        {"scene_family": family},
                    )
                    facts = gen._analyze(grid)["facts"]
                    self.assertEqual(facts["scene_family"], family)
                    self.assertEqual(facts["visible_turns"], (0, 1, 2, 3))

    def test_linked_family_covers_all_public_profiles_and_overlaps(self):
        signatures = set()
        overlap_witnesses = 0
        for band in ("easy", "medium", "hard"):
            for seed in range(300):
                grid = gen.generate(
                    seed,
                    0,
                    difficulty=band,
                    scene_family="linked",
                )
                facts = gen._analyze(grid)["facts"]
                signatures.add(gen.canonical_profile_signature(grid))
                overlap_witnesses += facts["overlap_count"] > 0
        self.assertEqual(
            signatures,
            {f"public_profile_{index}" for index in range(1, 6)},
        )
        self.assertGreater(overlap_witnesses, 300)

    def test_generalized_family_is_novel_and_varied(self):
        sizes = set()
        overlap_counts = set()
        signatures = set()
        for band in ("easy", "medium", "hard"):
            for seed in range(300):
                grid = gen.generate(
                    seed,
                    1,
                    difficulty=band,
                    scene_family="generalized",
                )
                facts = gen._analyze(grid)["facts"]
                self.assertIsNone(facts["profile_index"])
                sizes.add(facts["source_size"])
                overlap_counts.add(facts["overlap_count"])
                signatures.add(gen.canonical_profile_signature(grid))
        self.assertGreaterEqual(len(sizes), 3)
        self.assertGreaterEqual(len(overlap_counts), 3)
        self.assertGreaterEqual(len(signatures), 6)

    def test_later_turns_overwrite_collisions(self):
        grid = gen.generate(
            12,
            0,
            difficulty="hard",
            scene_family="linked",
        )
        facts = gen._analyze(grid)["facts"]
        for seed in range(200):
            candidate = gen.generate(
                seed,
                0,
                difficulty="hard",
                scene_family="linked",
            )
            candidate_facts = gen._analyze(candidate)["facts"]
            if candidate_facts["overlap_count"]:
                grid, facts = candidate, candidate_facts
                break
        self.assertGreater(facts["overlap_count"], 0)
        owners = {}
        pivot = facts["pivot"]
        for turn in range(4):
            for row, col in facts["source"]:
                delta = (row - pivot[0], col - pivot[1])
                turned = gen._turn_cell(delta, turn)
                owners[(pivot[0] + turned[0], pivot[1] + turned[1])] = turn
        output = gen.rule_mirror(grid)
        for (row, col), turn in owners.items():
            self.assertEqual(output[row][col], facts["legend"][turn])

    def test_structural_impostors_are_rejected(self):
        valid = gen.generate(22, 0, scene_family="linked")
        cases = []

        broken_legend = copy.deepcopy(valid)
        broken_legend[0][1] = broken_legend[0][0]
        cases.append(broken_legend)

        moved_legend = copy.deepcopy(valid)
        moved_legend[0][5] = moved_legend[0][3]
        moved_legend[0][3] = 0
        cases.append(moved_legend)

        second_pivot = copy.deepcopy(valid)
        second_pivot[-1][-1] = 5
        cases.append(second_pivot)

        disconnected = copy.deepcopy(valid)
        source_color = gen._analyze(valid)["facts"]["source_color"]
        disconnected[-1][-1] = source_color
        cases.append(disconnected)

        for grid in cases:
            self.assertTrue(gen.self_check(grid), grid)

    def test_determinism_freshness_global_rng_and_validation(self):
        random.seed(923)
        state = random.getstate()
        first = gen.generate(
            17,
            4,
            difficulty="hard",
            scene_family="generalized",
        )
        self.assertEqual(random.getstate(), state)
        second = gen.generate(
            17,
            4,
            difficulty="hard",
            scene_family="generalized",
        )
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9 if first[0][0] != 9 else 8
        self.assertNotEqual(first, second)
        with self.assertRaises(ValueError):
            gen.generate(1, 0, difficulty="impossible")
        with self.assertRaises(ValueError):
            gen.generate(1, 0, bogus_axis="x")
        with self.assertRaises(ValueError):
            gen.generate(1, 0, scene_family="unknown")


if __name__ == "__main__":
    unittest.main()
