from __future__ import annotations

import copy
import importlib
import json
import random
import unittest
from pathlib import Path


generator = importlib.import_module(
    "puzzle_generators.per_puzzle.36b22ff07a2e.generator"
)
ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "data" / "canonical" / "puzzles.jsonl"


def _canonical_pairs():
    pairs = []
    for line in CANON.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") != generator.TASK_ID:
            continue
        pairs.extend(row.get("train") or [])
        test = row.get("test") or []
        if isinstance(test, dict):
            pairs.append(test)
        else:
            pairs.extend(test)
    return [pair for pair in pairs if "input" in pair and "output" in pair]


def _generated(**overrides):
    return generator.generate(
        71717,
        81818,
        difficulty="medium",
        lattice_shape="2x2",
        scene_profile="dense_varied",
        background_color=4,
        frame_color=8,
        **overrides,
    )


class Generator36b22ff07a2eTests(unittest.TestCase):
    def test_rule_hash_and_all_eight_canonical_pairs(self):
        pairs = _canonical_pairs()
        self.assertEqual(generator.RULE_HASH, "24e4023e7c9d")
        self.assertEqual(len(pairs), 8)
        for pair in pairs:
            grid = copy.deepcopy(pair["input"])
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.rule_mirror(grid), pair["output"])
            self.assertEqual(grid, pair["input"])

    def test_all_exact_axes_are_observable_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for shape_index, shape in enumerate(generator.LATTICE_SHAPES):
                for profile_index, profile in enumerate(generator.SCENE_PROFILES):
                    background = (shape_index + profile_index + 1) % 10
                    frame = (background + 4) % 10
                    grid = generator.generate(
                        1000 + shape_index,
                        2000 + profile_index,
                        difficulty=band,
                        lattice_shape=shape,
                        scene_profile=profile,
                        background_color=background,
                        frame_color=frame,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(
                        generator.observe_overrides(grid),
                        {
                            "lattice_shape": shape,
                            "scene_profile": profile,
                            "background_color": background,
                            "frame_color": frame,
                        },
                    )

    def test_four_consecutive_lessons_cover_all_profiles(self):
        for band in ("easy", "medium", "hard"):
            for start in (0, 17, 100):
                observed = []
                for offset in range(4):
                    grid = generator.generate(31, start + offset, difficulty=band)
                    observed.append(generator.observe_overrides(grid)["scene_profile"])
                expected = [
                    generator.SCENE_PROFILES[(start + offset) % 4]
                    for offset in range(4)
                ]
                self.assertEqual(observed, expected)
                self.assertEqual(set(observed), set(generator.SCENE_PROFILES))

    def test_determinism_fresh_returns_and_global_rng_isolation(self):
        random.seed(987654321)
        state_before = random.getstate()
        first = generator.generate(123, 456, difficulty="hard")
        state_after = random.getstate()
        second = generator.generate(123, 456, difficulty="hard")
        self.assertEqual(state_before, state_after)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        original = second[0][0]
        first[0][0] = (first[0][0] + 1) % 10
        self.assertEqual(second[0][0], original)

    def test_unknown_controls_and_equal_scene_colors_reject(self):
        with self.assertRaises(ValueError):
            generator.generate(1, 2, difficulty="impossible")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, unknown_axis=7)
        with self.assertRaises(ValueError):
            generator.generate(1, 2, background_color=3, frame_color=3)

    def test_destructive_mutations_are_rejected(self):
        base = _generated()
        facts = generator._analysis(base)["facts"]
        background = facts["background_color"]
        frame = facts["frame_color"]
        records = sorted(facts["room_records"], key=lambda item: item["bbox"])

        # Merge two adjacent rooms by carving through their field separator.
        merged = copy.deepcopy(base)
        left = records[0]["bbox"]
        right = records[1]["bbox"]
        row = max(left[0], right[0])
        for col in range(left[3] + 1, right[1]):
            merged[row][col] = background

        # Put two distinct marker colors inside an otherwise empty room.
        multicolor = copy.deepcopy(base)
        empty = next(record for record in records if record["marker_size"] == 0)
        top, left_col, _, _ = empty["bbox"]
        marker_colors = [c for c in range(10) if c not in (background, frame)]
        multicolor[top][left_col] = marker_colors[0]
        multicolor[top][left_col + 1] = marker_colors[1]

        # Remove all markers, destroying the demonstrated extraction branch.
        no_markers = copy.deepcopy(base)
        for row_index, row_values in enumerate(no_markers):
            for col_index, value in enumerate(row_values):
                if value not in (background, frame):
                    no_markers[row_index][col_index] = background

        # Break the single-color outer border invariant.
        bad_border = copy.deepcopy(base)
        bad_border[0][0] = frame

        for mutation in (merged, multicolor, no_markers, bad_border):
            self.assertTrue(generator.self_check(mutation), mutation)


if __name__ == "__main__":
    unittest.main()
