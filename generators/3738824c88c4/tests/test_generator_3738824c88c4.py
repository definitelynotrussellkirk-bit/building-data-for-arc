"""Focused semantic and contract tests for generator 3738824c88c4."""
from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

from scripts.mine_primitive_usage import summarize_task
from solvers.grounded_rules import GROUNDED_RULES


generator = importlib.import_module(
    "puzzle_generators.per_puzzle.3738824c88c4.generator"
)
ROOT = Path(__file__).resolve().parents[1]
BASE_FILES = (
    ROOT / "data/base/solutions/training/6cbe9eb8__3738824c88c4.json",
    ROOT / "data/base/solutions/augmented/6cbe9eb8__8d221f37a55a.json",
)


def canonical_rows():
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == generator.TASK_ID:
                rows.append(row)
    return rows


def all_canonical_pairs():
    pairs = []
    for row in canonical_rows():
        test = row["test"]
        pairs.extend(row["train"])
        pairs.extend(test if isinstance(test, list) else [test])
    return pairs


def unique_canonical_pairs():
    pairs = []
    seen = set()
    for pair in all_canonical_pairs():
        key = tuple(map(tuple, pair["input"]))
        if key not in seen:
            seen.add(key)
            pairs.append(pair)
    return pairs


def normalized_rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def transform_grid(grid, orientation):
    return generator._transform(grid, orientation)


def nesting_fits(records):
    outer = records[0]
    inner_height = outer["height"] - (2 if outer["frame"] else 0)
    inner_width = outer["width"] - (2 if outer["frame"] else 0)
    for record in records[1:]:
        if (
            record["height"] > inner_height
            or record["width"] > inner_width
        ):
            return False
        inner_height = record["height"] - (2 if record["frame"] else 0)
        inner_width = record["width"] - (2 if record["frame"] else 0)
    return True


class Generator3738824c88c4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = canonical_rows()
        cls.all_pairs = all_canonical_pairs()
        cls.pairs = unique_canonical_pairs()

    def test_all_linked_rows_pairs_profiles_and_rule(self):
        self.assertEqual(len(self.rows), 2)
        self.assertEqual(len(self.all_pairs), 8)
        self.assertEqual(len(self.pairs), 4)
        expected_records = (
            ((12, 11, True), (6, 7, True), (4, 5, False), (2, 2, False)),
            ((9, 12, True), (5, 5, True), (3, 3, False), (2, 2, False)),
            ((8, 8, True), (6, 6, False), (3, 3, False)),
            ((15, 13, True), (7, 9, True), (3, 4, False), (2, 2, False)),
        )
        for index, (profile, pair) in enumerate(
            zip(generator.SCENE_PROFILES, self.pairs)
        ):
            source = pair["input"]
            snapshot = [row[:] for row in source]
            self.assertEqual(source, generator._profile_grid(profile))
            self.assertEqual(generator.self_check(source), [])
            self.assertEqual(generator.canonical_profile_index(source), index)
            self.assertEqual(
                generator.observe_overrides(source),
                {
                    "scene_profile": profile,
                    "orientation": "identity",
                    "palette_mode": "canonical",
                },
            )
            records = generator._qualifying_records(source)
            self.assertEqual(
                tuple(
                    (
                        record["height"],
                        record["width"],
                        record["frame"],
                    )
                    for record in records
                ),
                expected_records[index],
            )
            self.assertTrue(nesting_fits(records))
            self.assertEqual(generator.rule_mirror(source), pair["output"])
            self.assertEqual(source, snapshot)
        for pair in self.all_pairs:
            self.assertEqual(
                generator.rule_mirror(pair["input"]),
                pair["output"],
            )

    def test_global_d4_and_every_exact_axis_combination(self):
        for band in ("easy", "medium", "hard"):
            for profile_index, profile in enumerate(
                generator.SCENE_PROFILES
            ):
                for orientation_index, orientation in enumerate(
                    generator.ORIENTATIONS
                ):
                    for palette_index, palette_mode in enumerate(
                        generator.PALETTE_MODES
                    ):
                        seed = (
                            10_000
                            + 1_000 * profile_index
                            + 100 * orientation_index
                            + 10 * palette_index
                            + len(band)
                        )
                        grid = generator.generate(
                            seed,
                            seed * 17 + 3,
                            difficulty=band,
                            scene_profile=profile,
                            orientation=orientation,
                            palette_mode=palette_mode,
                        )
                        self.assertEqual(generator.self_check(grid), [])
                        self.assertEqual(
                            generator.observe_overrides(grid),
                            {
                                "scene_profile": profile,
                                "orientation": orientation,
                                "palette_mode": palette_mode,
                            },
                        )
                        self.assertTrue(
                            nesting_fits(generator._qualifying_records(grid))
                        )
                        self.assertNotEqual(grid, generator.rule_mirror(grid))
        for index, pair in enumerate(self.pairs):
            for orientation in generator.ORIENTATIONS:
                transformed = transform_grid(pair["input"], orientation)
                self.assertEqual(generator.self_check(transformed), [])
                self.assertEqual(
                    generator.canonical_profile_index(transformed),
                    index,
                )

    def test_main_and_disjoint_distributions_are_complete_and_diverse(self):
        for start in (0, 50_000):
            for band_index, band in enumerate(
                ("easy", "medium", "hard")
            ):
                profiles = Counter()
                orientations = Counter()
                palettes = Counter()
                inputs = set()
                outputs = set()
                for offset in range(300):
                    seed = start + 10_000 * band_index + offset
                    grid = generator.generate(
                        seed,
                        seed * 29 + 7,
                        difficulty=band,
                    )
                    output = generator.rule_mirror(grid)
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertNotEqual(grid, output)
                    observed = generator.observe_overrides(grid)
                    profiles[observed["scene_profile"]] += 1
                    orientations[observed["orientation"]] += 1
                    palettes[observed["palette_mode"]] += 1
                    inputs.add(json.dumps(grid, separators=(",", ":")))
                    outputs.add(json.dumps(output, separators=(",", ":")))
                self.assertEqual(set(profiles), set(generator.SCENE_PROFILES))
                self.assertEqual(
                    set(orientations),
                    set(generator.ORIENTATIONS),
                )
                self.assertEqual(set(palettes), set(generator.PALETTE_MODES))
                self.assertGreaterEqual(len(inputs), 270)
                self.assertGreaterEqual(len(outputs), 270)

    def test_strict_checker_rejects_nearby_recombinations(self):
        canonical = generator._profile_grid(
            "profile_14x22_4rect"
        )
        mutations = []

        removed_object_cell = [row[:] for row in canonical]
        removed_object_cell[1][2] = 0
        mutations.append(removed_object_cell)

        zero_outer_object = [
            [0 if value == 8 else value for value in row]
            for row in canonical
        ]
        mutations.append(zero_outer_object)

        merged_colors = [
            [4 if value == 5 else value for value in row]
            for row in canonical
        ]
        mutations.append(merged_colors)

        marginal_swap = [row[:] for row in canonical]
        marginal_swap[0][0], marginal_swap[0][1] = (
            marginal_swap[0][1],
            marginal_swap[0][0],
        )
        mutations.append(marginal_swap)

        cropped = [row[:-1] for row in canonical]
        mutations.append(cropped)

        ragged = [row[:] for row in canonical]
        ragged[0] = ragged[0][:-1]
        mutations.append(ragged)

        for mutation in mutations:
            self.assertTrue(generator.self_check(mutation))
            self.assertEqual(generator.observe_overrides(mutation), {})

        invalid_grids = (
            [],
            [[0] * 31],
            [[False, 1], [1, 0]],
            [[10, 1], [1, 0]],
        )
        for invalid in invalid_grids:
            self.assertTrue(generator.self_check(invalid))

    def test_source_sync_rule_hash_and_primitive_metadata(self):
        source = self.rows[0]["program_solution"]
        self.assertEqual(
            " ".join(source.split()),
            " ".join(GROUNDED_RULES[generator.TASK_ID].split()),
        )
        expected_hash = normalized_rule_hash(source)[:12]
        self.assertEqual(generator.RULE_HASH, expected_hash)
        mined = summarize_task(generator.TASK_ID, source)
        for path in BASE_FILES:
            row = json.loads(path.read_text())
            self.assertEqual(row["racket_target"]["raw_code"], source)
            self.assertEqual(row["racket_target"]["target_code"], source)
            self.assertEqual(
                row["primitive_metadata"]["primitive_chain"],
                mined["primitive_chain"],
            )
            self.assertEqual(
                row["primitive_metadata"]["family_chain"],
                mined["family_chain"],
            )

    def test_determinism_fresh_returns_global_rng_and_invalid_calls(self):
        before = random.getstate()
        first = generator.generate(321, 654, difficulty="hard")
        after = random.getstate()
        second = generator.generate(321, 654, difficulty="hard")
        self.assertEqual(before, after)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = (first[0][0] + 1) % 10
        third = generator.generate(321, 654, difficulty="hard")
        self.assertEqual(second, third)

        with self.assertRaises(ValueError):
            generator.generate(1, 2, difficulty="extreme")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, scene_profile="unknown")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, orientation="diagonal")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, palette_mode="merged")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, bogus_axis=1)


if __name__ == "__main__":
    unittest.main()
