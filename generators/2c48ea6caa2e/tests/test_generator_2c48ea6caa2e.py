"""Focused semantic and contract tests for generator 2c48ea6caa2e."""
from __future__ import annotations

import hashlib
import json
import random
import unittest
from collections import Counter

from reviewer_support import (
    canonical_pairs as read_canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)


TASK_ID = "2c48ea6caa2e"
ROOT = find_root(__file__)
generator, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(
    TASK_ID,
    root=ROOT,
)


def canonical_rows():
    rows = []
    with canonical_path(ROOT).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == generator.TASK_ID:
                rows.append(row)
    return rows


def all_canonical_pairs():
    return read_canonical_pairs(
        generator.TASK_ID,
        root=ROOT,
        labeled_only=True,
    )


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


def independent_rule(grid):
    height = len(grid)
    width = len(grid[0])
    blues = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    ]
    if not blues:
        return [[0 for _col in range(width)] for _row in range(height)]
    top = min(row for row, _col in blues)
    bottom = max(row for row, _col in blues)
    left = min(col for _row, col in blues)
    right = max(col for _row, col in blues)
    row_counts = [
        sum(value == 1 for value in values) for values in grid
    ]
    col_counts = [
        sum(grid[row][col] == 1 for row in range(height))
        for col in range(width)
    ]
    return [
        [
            1
            if grid[row][col] == 1
            else 2
            if (
                top <= row <= bottom
                and left <= col <= right
                and grid[row][col] == 0
                and (row_counts[row] >= 4 or col_counts[col] >= 4)
            )
            else 0
            for col in range(width)
        ]
        for row in range(height)
    ]


def transform_grid(grid, transform):
    transformed = [row[:] for row in grid]
    if transform >= 4:
        transformed = [list(reversed(row)) for row in transformed]
    for _turn in range(transform % 4):
        transformed = [
            list(row) for row in zip(*reversed(transformed))
        ]
    return transformed


def blue_bbox(grid):
    blues = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    ]
    return (
        min(row for row, _col in blues),
        min(col for _row, col in blues),
        max(row for row, _col in blues),
        max(col for _row, col in blues),
    )


def normalized_blue_mask(grid):
    top, left, bottom, right = blue_bbox(grid)
    return tuple(
        tuple(grid[row][col] for col in range(left, right + 1))
        for row in range(top, bottom + 1)
    )


def row_col_counts(mask):
    rows = tuple(sum(row) for row in mask)
    cols = tuple(
        sum(mask[row][col] for row in range(len(mask)))
        for col in range(len(mask[0]))
    )
    return rows, cols


class Generator2c48ea6caa2eTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = canonical_rows()
        cls.all_pairs = all_canonical_pairs()
        cls.pairs = unique_canonical_pairs()

    def test_all_linked_rows_pairs_masks_and_rule(self):
        self.assertEqual(len(self.rows), 2)
        self.assertEqual(len(self.all_pairs), 8)
        self.assertEqual(len(self.pairs), 4)
        expected_counts = (
            ((5, 2, 1, 3, 2, 2, 5), (5, 2, 5, 1, 0, 2, 5)),
            ((5, 1, 1, 0, 1, 2, 6), (4, 1, 1, 0, 1, 2, 1, 1, 5)),
            ((7, 2, 0, 2, 5, 2, 1, 6), (6, 3, 0, 3, 2, 1, 2, 2, 6)),
            ((6, 2, 0, 0, 2, 5, 0, 2, 6), (6, 0, 3, 2, 1, 2, 0, 3, 6)),
        )
        for index, pair in enumerate(self.pairs):
            source = pair["input"]
            snapshot = [row[:] for row in source]
            self.assertEqual(generator.self_check(source), [])
            self.assertEqual(
                generator.canonical_profile_index(source),
                index,
            )
            self.assertEqual(
                row_col_counts(normalized_blue_mask(source)),
                expected_counts[index],
            )
            self.assertEqual(independent_rule(source), pair["output"])
            self.assertEqual(generator.rule_mirror(source), pair["output"])
            self.assertEqual(source, snapshot)
        for pair in self.all_pairs:
            self.assertEqual(
                generator.rule_mirror(pair["input"]),
                pair["output"],
            )

    def test_global_d4_metamorphism_for_every_complete_mask(self):
        for index, pair in enumerate(self.pairs):
            for transform in range(8):
                transformed_input = transform_grid(
                    pair["input"],
                    transform,
                )
                transformed_output = transform_grid(
                    pair["output"],
                    transform,
                )
                self.assertEqual(
                    generator.canonical_profile_index(transformed_input),
                    index,
                )
                self.assertEqual(generator.self_check(transformed_input), [])
                self.assertEqual(
                    independent_rule(transformed_input),
                    transformed_output,
                )
                self.assertEqual(
                    generator.rule_mirror(transformed_input),
                    transformed_output,
                )

    def test_every_exact_axis_combination_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile_index, profile in enumerate(
                generator.SCENE_PROFILES
            ):
                for orientation_index, orientation in enumerate(
                    generator.ORIENTATIONS
                ):
                    for padding_index, padding in enumerate(
                        generator.PADDING_PROFILES
                    ):
                        seed = (
                            10_000
                            + 1_000 * profile_index
                            + 100 * orientation_index
                            + 10 * padding_index
                            + len(band)
                        )
                        grid = generator.generate(
                            seed,
                            seed * 17 + 3,
                            difficulty=band,
                            scene_profile=profile,
                            orientation=orientation,
                            padding_profile=padding,
                        )
                        self.assertEqual(generator.self_check(grid), [])
                        self.assertEqual(
                            generator.observe_overrides(grid),
                            {
                                "scene_profile": profile,
                                "orientation": orientation,
                                "padding_profile": padding,
                            },
                        )
                        self.assertEqual(
                            generator.rule_mirror(grid),
                            independent_rule(grid),
                        )
        with self.assertRaises(ValueError):
            generator.generate(1, 2, difficulty="extreme")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, scene_profile="unknown")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, orientation="diagonal")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, padding_profile="unbounded")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, bogus_axis=1)

    def test_generate_rejects_non_integer_coordinates(self):
        for bad_seed in (True, False, 1.0, 1.75, "1", None):
            with self.subTest(seed=bad_seed):
                with self.assertRaises(TypeError):
                    generator.generate(bad_seed, 0)
        for bad_index in (True, False, 1.0, 1.75, "1", None, -1):
            with self.subTest(sample_index=bad_index):
                with self.assertRaises(ValueError):
                    generator.generate(0, bad_index)

    def test_declared_majority_shortcut_fits_canonical_and_is_refuted(self):
        rival = generator.CANONICAL_SHORTCUTS["bbox_majority"]
        self.assertIs(
            rival,
            generator.SEMANTIC_RIVALS["bbox_majority"],
        )
        self.assertIs(
            rival,
            generator.LESSON_COMPETITORS["bbox_majority"],
        )
        for pair in self.all_pairs:
            self.assertEqual(rival(pair["input"]), pair["output"])

        witness = generator.generate(
            17,
            1,
            scene_profile="threshold_witness_9x9",
            orientation="identity",
            padding_profile="canonical",
        )
        self.assertTrue(
            generator.SEMANTIC_WITNESSES["fixed_threshold_not_majority"](
                witness
            )
        )
        self.assertNotEqual(generator.rule_mirror(witness), rival(witness))
        self.assertEqual(
            generator.WITNESS_RIVALS["fixed_threshold_not_majority"],
            ("bbox_majority",),
        )

    def test_default_schedule_anchors_profiles_and_teaches_the_shortcut(self):
        expected_profiles = (
            "canonical_profile_anchor",
            "threshold_witness",
            "published_variation",
            "threshold_witness",
        )
        self.assertEqual(generator.SCHEDULE_PROFILES, expected_profiles)
        canonical_profiles = {
            (len(pair["input"]), len(pair["input"][0]), 2)
            for pair in self.pairs
        }
        for band in ("easy", "medium", "hard"):
            grids = [
                generator.generate(1234, index, difficulty=band)
                for index in range(8)
            ]
            for index, grid in enumerate(grids):
                self.assertEqual(
                    generator.schedule_profile(1234, index, band),
                    expected_profiles[index % 4],
                )
                if index % 4 == 0:
                    profile = (
                        len(grid),
                        len(grid[0]),
                        len({value for row in grid for value in row}),
                    )
                    self.assertIn(profile, canonical_profiles)
                if index % 2 == 1:
                    self.assertTrue(
                        generator.SEMANTIC_WITNESSES[
                            "fixed_threshold_not_majority"
                        ](grid)
                    )
            for start in range(4):
                demos = [
                    {
                        "input": grids[start + offset],
                        "output": generator.rule_mirror(
                            grids[start + offset]
                        ),
                    }
                    for offset in range(3)
                ]
                query_grid = grids[start + 3]
                query = {
                    "input": query_grid,
                    "output": generator.rule_mirror(query_grid),
                }
                self.assertEqual(
                    generator.lesson_identifiable(demos, query),
                    [],
                )

    def test_pinned_profile_floor_has_exact_support_in_every_band(self):
        canonical_profiles = {
            (len(pair["input"]), len(pair["input"][0]), 2)
            for pair in self.pairs
        }
        total_exact = 0
        for band in ("easy", "medium", "hard"):
            exact = 0
            for index in range(20):
                seed = int(
                    hashlib.sha256(
                        f"profile-floor:v1:{generator.TASK_ID}:{band}:{index}".encode()
                    ).hexdigest()[:12],
                    16,
                )
                sample_index = seed % 7919 + index
                grid = generator.generate(seed, sample_index, difficulty=band)
                profile = (
                    len(grid),
                    len(grid[0]),
                    len({value for row in grid for value in row}),
                )
                exact += profile in canonical_profiles
            self.assertGreaterEqual(exact, 1, band)
            total_exact += exact
        self.assertGreaterEqual(total_exact, 15)

    def test_main_and_disjoint_distributions_are_complete_and_diverse(self):
        for start in (0, 50_000):
            for band_index, band in enumerate(
                ("easy", "medium", "hard")
            ):
                profiles = Counter()
                orientations = Counter()
                paddings = Counter()
                inputs = set()
                outputs = set()
                for offset in range(300):
                    seed = start + 10_000 * band_index + offset
                    grid = generator.generate(
                        seed,
                        seed * 29 + 7,
                        difficulty=band,
                    )
                    output = independent_rule(grid)
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertNotEqual(grid, output)
                    self.assertEqual(generator.rule_mirror(grid), output)
                    observed = generator.observe_overrides(grid)
                    profiles[observed["scene_profile"]] += 1
                    orientations[observed["orientation"]] += 1
                    paddings[observed["padding_profile"]] += 1
                    inputs.add(json.dumps(grid, separators=(",", ":")))
                    outputs.add(json.dumps(output, separators=(",", ":")))
                self.assertEqual(set(profiles), set(generator.SCENE_PROFILES))
                self.assertEqual(set(orientations), set(generator.ORIENTATIONS))
                self.assertEqual(set(paddings), set(generator.PADDING_PROFILES))
                self.assertGreater(len(inputs), 280)
                self.assertGreater(len(outputs), 280)

    def test_checker_rejects_shortcuts_and_marginal_recombination(self):
        canonical = [row[:] for row in self.pairs[0]["input"]]

        solid = [[1 for _col in range(10)] for _row in range(10)]
        self.assertTrue(generator.self_check(solid))

        missing = [row[:] for row in canonical]
        missing[2][2] = 0
        self.assertTrue(generator.self_check(missing))

        extra = [row[:] for row in canonical]
        extra[4][3] = 1
        self.assertTrue(generator.self_check(extra))

        distractor = [row[:] for row in canonical]
        distractor[0][0] = 3
        snapshot = [row[:] for row in distractor]
        self.assertTrue(generator.self_check(distractor))
        self.assertEqual(
            generator.rule_mirror(distractor),
            independent_rule(distractor),
        )
        self.assertEqual(generator.rule_mirror(distractor)[0][0], 0)
        self.assertEqual(distractor, snapshot)

        # A 2x2 switch preserves every blue row and column count, so a
        # marginal-only checker would accept it.  It is still not one of the
        # demonstrated answer-bearing occupancy bitmaps.
        recombined = [row[:] for row in canonical]
        before_counts = row_col_counts(normalized_blue_mask(recombined))
        self.assertEqual(
            (
                recombined[2][5],
                recombined[2][8],
                recombined[8][5],
                recombined[8][8],
            ),
            (0, 1, 1, 0),
        )
        recombined[2][5] = 1
        recombined[2][8] = 0
        recombined[8][5] = 0
        recombined[8][8] = 1
        self.assertEqual(
            row_col_counts(normalized_blue_mask(recombined)),
            before_counts,
        )
        self.assertTrue(generator.self_check(recombined))
        self.assertEqual(
            generator.rule_mirror(recombined),
            independent_rule(recombined),
        )

    def test_source_sync_hash_determinism_freshness_and_global_rng(self):
        source = self.rows[0]["program_solution"]
        self.assertTrue(all(
            row["program_solution"] == source for row in self.rows
        ))
        self.assertEqual(
            generator.RULE_HASH,
            normalized_rule_hash(source)[:12],
        )
        self.assertEqual(generator.TASK_ID, TASK_ID)
        self.assertTrue(GENERATOR_PATH.name == "generator.py")
        self.assertEqual(len(GENERATOR_SHA256), 64)

        state = random.getstate()
        first = generator.generate(37, 43, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        snapshot = [row[:] for row in first]
        generator.generate(91, 97, difficulty="easy")
        self.assertEqual(first, snapshot)
        again = generator.generate(37, 43, difficulty="hard")
        self.assertEqual(first, again)
        self.assertIsNot(first, again)
        self.assertTrue(all(
            old_row is not new_row
            for old_row, new_row in zip(first, again)
        ))
        first[0][0] = 1 if first[0][0] != 1 else 0
        self.assertEqual(
            generator.generate(37, 43, difficulty="hard"),
            again,
        )


if __name__ == "__main__":
    unittest.main()
