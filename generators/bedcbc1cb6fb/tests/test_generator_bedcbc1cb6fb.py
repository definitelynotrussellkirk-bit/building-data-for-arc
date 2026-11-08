"""Focused semantic and contract tests for generator bedcbc1cb6fb."""
from __future__ import annotations

import hashlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

from puzzle_generators.per_puzzle.bedcbc1cb6fb import generator
from scripts.rule_smoke import load_rules


ROOT = Path(__file__).resolve().parents[1]
BASE_FILES = (
    ROOT
    / "data/base/solutions/training/"
    "99306f82__bedcbc1cb6fb.json",
    ROOT
    / "data/base/solutions/augmented/"
    "99306f82__47d6130c35c3.json",
)


def canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for raw in handle:
            row = json.loads(raw)
            if row.get("task_id") == generator.TASK_ID:
                return row
    raise AssertionError("canonical row not found")


def canonical_pairs():
    row = canonical_row()
    test = row["test"]
    return list(row["train"]) + (
        list(test) if isinstance(test, list) else [test]
    )


def normalized_rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def reference_rule(grid):
    height = len(grid)
    width = len(grid[0])
    markers = [
        grid[index][index]
        for index in range(min(height, width))
        if grid[index][index] not in (0, 1)
    ]
    blues = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    ]
    if not blues:
        raise ValueError("missing blue frame")
    row1 = min(row for row, _col in blues) + 1
    row2 = max(row for row, _col in blues) - 1
    col1 = min(col for _row, col in blues) + 1
    col2 = max(col for _row, col in blues) - 1
    output = [row[:] for row in grid]
    for color in markers:
        if row1 > row2 or col1 > col2:
            break
        for row in range(row1, row2 + 1):
            for col in range(col1, col2 + 1):
                output[row][col] = color
        row1 += 1
        row2 -= 1
        col1 += 1
        col2 -= 1
    return output


def draw_broad_case(
    height,
    width,
    markers,
    frame_bbox,
):
    grid = [
        [0 for _col in range(width)]
        for _row in range(height)
    ]
    for index, color in markers:
        grid[index][index] = color
    row1, col1, row2, col2 = frame_bbox
    for col in range(col1, col2 + 1):
        grid[row1][col] = 1
        grid[row2][col] = 1
    for row in range(row1, row2 + 1):
        grid[row][col1] = 1
        grid[row][col2] = 1
    return grid


class GeneratorBedcbc1cb6fbTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = canonical_pairs()

    def test_all_canonical_pairs_profiles_and_rule(self):
        self.assertEqual(len(self.pairs), 4)
        observed_profiles = []
        for index, pair in enumerate(self.pairs):
            source = pair["input"]
            snapshot = [row[:] for row in source]
            observed = generator.observe_overrides(source)
            self.assertEqual(generator.self_check(source), [])
            self.assertEqual(observed["layout_variant"], "canonical")
            self.assertEqual(
                generator.canonical_profile_index(source),
                index,
            )
            self.assertEqual(
                generator.exact_public_profile_index(source),
                index,
            )
            self.assertEqual(reference_rule(source), pair["output"])
            self.assertEqual(generator.rule_mirror(source), pair["output"])
            self.assertEqual(source, snapshot)
            observed_profiles.append(observed["scene_profile"])
        self.assertEqual(
            tuple(observed_profiles),
            generator.SCENE_PROFILES,
        )

    def test_every_exact_axis_combination(self):
        for band in ("easy", "medium", "hard"):
            for profile_index, profile in enumerate(
                generator.SCENE_PROFILES
            ):
                for variant_index, variant in enumerate(
                    generator.LAYOUT_VARIANTS
                ):
                    seed = (
                        10_000
                        + 100 * profile_index
                        + 10 * variant_index
                        + len(band)
                    )
                    grid = generator.generate(
                        seed,
                        seed * 17 + 3,
                        difficulty=band,
                        scene_profile=profile,
                        layout_variant=variant,
                    )
                    expected = {
                        "scene_profile": profile,
                        "layout_variant": variant,
                    }
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(
                        generator.observe_overrides(grid),
                        expected,
                    )
                    self.assertEqual(
                        generator.rule_mirror(grid),
                        reference_rule(grid),
                    )
                    expected_index = (
                        profile_index if variant == "canonical" else None
                    )
                    self.assertEqual(
                        generator.exact_public_profile_index(grid),
                        expected_index,
                    )
        with self.assertRaises(ValueError):
            generator.generate(1, 2, scene_profile="unknown")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, layout_variant="unknown")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, bogus_axis=True)
        with self.assertRaises(ValueError):
            generator.generate(1, 2, difficulty="extreme")

    def test_main_and_disjoint_distributions_are_complete_and_diverse(self):
        expected_axes = {
            (profile, variant)
            for profile in generator.SCENE_PROFILES
            for variant in generator.LAYOUT_VARIANTS
        }
        for start in (0, 50_000):
            for band_index, band in enumerate(
                ("easy", "medium", "hard")
            ):
                axes = Counter()
                inputs = set()
                outputs = set()
                for offset in range(400):
                    seed = start + 1_000 * band_index + offset
                    grid = generator.generate(
                        seed,
                        seed * 29 + 7,
                        difficulty=band,
                    )
                    observed = generator.observe_overrides(grid)
                    output = reference_rule(grid)
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(generator.rule_mirror(grid), output)
                    axes[(
                        observed["scene_profile"],
                        observed["layout_variant"],
                    )] += 1
                    inputs.add(json.dumps(grid, separators=(",", ":")))
                    outputs.add(
                        json.dumps(output, separators=(",", ":"))
                    )
                self.assertEqual(set(axes), expected_axes)
                self.assertGreaterEqual(len(inputs), 300)
                self.assertGreaterEqual(len(outputs), 300)

    def test_canonical_prior_and_difficulty_profile_weighting(self):
        profiles_by_band = {}
        for band_index, band in enumerate(("easy", "medium", "hard")):
            profiles = Counter()
            variants = Counter()
            for offset in range(1_000):
                seed = 30_000 + 2_000 * band_index + offset
                grid = generator.generate(
                    seed,
                    seed * 31 + 11,
                    difficulty=band,
                )
                observed = generator.observe_overrides(grid)
                profiles[observed["scene_profile"]] += 1
                variants[observed["layout_variant"]] += 1
            self.assertEqual(set(profiles), set(generator.SCENE_PROFILES))
            self.assertEqual(set(variants), set(generator.LAYOUT_VARIANTS))
            self.assertGreaterEqual(variants["canonical"], 340)
            self.assertLessEqual(variants["canonical"], 460)
            profiles_by_band[band] = profiles
        self.assertGreater(
            profiles_by_band["easy"]["two_markers_10x10"],
            profiles_by_band["easy"]["five_markers_20x20"],
        )
        self.assertGreater(
            profiles_by_band["hard"]["five_markers_20x20"],
            profiles_by_band["hard"]["two_markers_10x10"],
        )

    def test_structural_and_semantic_mutations_are_rejected(self):
        first = [row[:] for row in self.pairs[0]["input"]]
        second = [row[:] for row in self.pairs[1]["input"]]
        third = [row[:] for row in self.pairs[2]["input"]]

        broken_frame = [row[:] for row in first]
        broken_frame[3][6] = 0

        duplicate_marker = [row[:] for row in first]
        duplicate_marker[1][1] = duplicate_marker[0][0]

        moved_marker = [row[:] for row in first]
        moved_marker[0][0], moved_marker[0][1] = (
            moved_marker[0][1],
            moved_marker[0][0],
        )

        extra_marker = [row[:] for row in second]
        extra_marker[8][0] = 4

        wrong_linked_frame = [row[:] for row in third]
        for col in range(4, 14):
            wrong_linked_frame[13][col] = 0
            wrong_linked_frame[14][col] = 1
        wrong_linked_frame[14][4] = 1
        wrong_linked_frame[14][13] = 1

        recombined = draw_broad_case(
            12,
            12,
            ((0, 2), (1, 3)),
            (2, 2, 9, 10),
        )

        for mutation in (
            broken_frame,
            duplicate_marker,
            moved_marker,
            extra_marker,
            wrong_linked_frame,
            recombined,
        ):
            self.assertNotEqual(generator.self_check(mutation), [])
            self.assertEqual(generator.observe_overrides(mutation), {})

        malformed = (
            [],
            [[]],
            [[1], [1, 2]],
            [[True]],
            [[10]],
            [[0] * 31],
            [[7] * 7 for _row in range(7)],
            [[2] * 2 for _row in range(2)],
        )
        for grid in malformed:
            self.assertNotEqual(generator.self_check(grid), [])

    def test_rule_mirror_is_broad_beyond_calibrated_profiles(self):
        cases = (
            draw_broad_case(
                12,
                13,
                ((0, 2), (2, 7)),
                (3, 4, 10, 11),
            ),
            draw_broad_case(
                18,
                16,
                ((1, 9), (3, 5), (5, 4)),
                (7, 2, 16, 14),
            ),
            draw_broad_case(
                9,
                14,
                ((0, 8),),
                (2, 5, 7, 12),
            ),
        )
        for grid in cases:
            snapshot = [row[:] for row in grid]
            self.assertEqual(
                generator.rule_mirror(grid),
                reference_rule(grid),
            )
            self.assertEqual(grid, snapshot)
            self.assertNotEqual(generator.self_check(grid), [])

    def test_marker_color_permutation_commutes(self):
        mapping = {
            0: 0,
            1: 1,
            2: 9,
            3: 8,
            4: 7,
            5: 6,
            6: 5,
            7: 4,
            8: 3,
            9: 2,
        }
        for pair in self.pairs:
            transformed_input = [
                [mapping[value] for value in row]
                for row in pair["input"]
            ]
            transformed_output = [
                [mapping[value] for value in row]
                for row in pair["output"]
            ]
            self.assertEqual(generator.self_check(transformed_input), [])
            self.assertEqual(
                generator.rule_mirror(transformed_input),
                transformed_output,
            )

    def test_determinism_fresh_returns_and_global_rng_isolation(self):
        random.seed(1729)
        state = random.getstate()
        first = generator.generate(991, 17, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(991, 17, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9 if first[0][0] != 9 else 8
        third = generator.generate(991, 17, difficulty="hard")
        self.assertEqual(second, third)

    def test_source_sync_and_rule_hash(self):
        canonical = canonical_row()["program_solution"]
        live = load_rules([generator.TASK_ID])[generator.TASK_ID]
        expected = normalized_rule_hash(canonical)
        self.assertEqual(normalized_rule_hash(live), expected)
        self.assertEqual(generator.RULE_HASH, expected[:12])
        for path in BASE_FILES:
            base = json.loads(path.read_text())
            racket = base["racket_target"]
            self.assertEqual(
                normalized_rule_hash(racket["raw_code"]),
                expected,
            )
            self.assertEqual(
                normalized_rule_hash(racket["target_code"]),
                expected,
            )
            self.assertEqual(racket["raw_code"], racket["target_code"])


if __name__ == "__main__":
    unittest.main()
