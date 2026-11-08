"""Focused semantic and contract tests for generator 4f065093e631."""
from __future__ import annotations

import hashlib
import json
import random
import unittest
from collections import Counter

from reviewer_support import (
    canonical_pairs as load_canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)


ROOT = find_root(__file__)
generator, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(
    "4f065093e631", root=ROOT
)
BASE_FILE = (
    canonical_path(ROOT).parent.parent
    / "base/solutions/training/"
    "890034e9__4f065093e631.json"
)


def canonical_row():
    with canonical_path(ROOT).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == generator.TASK_ID:
                return row
    raise AssertionError("canonical row not found")


def canonical_pairs():
    return load_canonical_pairs(generator.TASK_ID, root=ROOT, variant=0)


def normalized_rule_hash(source):
    return hashlib.sha256(
        " ".join(source.split()).encode()
    ).hexdigest()


def border_cells(box):
    top, left, bottom, right = box
    return {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if row in (top, bottom) or col in (left, right)
    }


def independent_source_and_target(grid):
    """Recover the calibrated source and target without generator helpers."""
    counts = Counter(value for row in grid for value in row)
    frame_color = next(
        color
        for color, count in counts.items()
        if color != 0 and count in (14, 18)
    )
    profiles = (
        (4, 5),
        (5, 4),
        (5, 6),
        (7, 4),
    )
    source = None
    dimensions = None
    for frame_height, frame_width in profiles:
        border_count = 2 * frame_height + 2 * frame_width - 4
        if counts[frame_color] != border_count:
            continue
        for top in range(22 - frame_height):
            for left in range(22 - frame_width):
                box = (
                    top,
                    left,
                    top + frame_height - 1,
                    left + frame_width - 1,
                )
                border = border_cells(box)
                if all(grid[row][col] == frame_color for row, col in border):
                    if all(
                        grid[row][col] == 0
                        for row in range(top + 1, box[2])
                        for col in range(left + 1, box[3])
                    ):
                        source = box
                        dimensions = (frame_height, frame_width)
    if source is None or dimensions is None:
        raise AssertionError("independent source not found")
    frame_height, frame_width = dimensions
    slots = []
    for top in range(22 - frame_height):
        for left in range(22 - frame_width):
            box = (
                top,
                left,
                top + frame_height - 1,
                left + frame_width - 1,
            )
            if all(
                grid[row][col] == 0
                for row in range(top + 1, box[2])
                for col in range(left + 1, box[3])
            ):
                slots.append(box)
    target = next(slot for slot in slots if slot != source)
    return frame_color, source, target


def independent_rule(grid):
    color, _source, target = independent_source_and_target(grid)
    output = [row[:] for row in grid]
    for row, col in border_cells(target):
        output[row][col] = color
    return output


class Generator4f065093e631Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = canonical_row()
        cls.pairs = canonical_pairs()

    def test_all_canonical_pairs_profiles_and_rule(self):
        expected_profiles = generator.SCENE_PROFILES
        self.assertEqual(len(self.pairs), len(expected_profiles))
        for pair, profile in zip(self.pairs, expected_profiles):
            source = pair["input"]
            snapshot = [row[:] for row in source]
            self.assertEqual(generator.self_check(source), [])
            self.assertEqual(
                generator.observe_overrides(source),
                {"scene_profile": profile},
            )
            self.assertEqual(
                generator.canonical_profile_index(source),
                generator.SCENE_PROFILES.index(profile),
            )
            self.assertEqual(independent_rule(source), pair["output"])
            self.assertEqual(generator.rule_mirror(source), pair["output"])
            self.assertEqual(source, snapshot)

    def test_every_exact_profile_in_every_band_and_fallback(self):
        for band in ("easy", "medium", "hard"):
            for profile_index, profile in enumerate(
                generator.SCENE_PROFILES
            ):
                seed = 10_000 + 100 * profile_index + len(band)
                grid = generator.generate(
                    seed,
                    seed * 17 + 3,
                    difficulty=band,
                    scene_profile=profile,
                )
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(
                    generator.observe_overrides(grid),
                    {"scene_profile": profile},
                )
                self.assertEqual(
                    generator.rule_mirror(grid),
                    independent_rule(grid),
                )
                fallback = generator._fallback_scene(
                    profile,
                    9,
                    1,
                    2,
                )
                self.assertEqual(generator.self_check(fallback), [])
                self.assertEqual(
                    generator.observe_overrides(fallback),
                    {"scene_profile": profile},
                )
        with self.assertRaises(ValueError):
            generator.generate(1, 2, scene_profile="unknown")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, bogus_axis=1)
        with self.assertRaises(ValueError):
            generator.generate(1, 2, difficulty="extreme")

    def test_main_and_disjoint_distributions_are_complete_and_diverse(self):
        for start in (0, 50_000):
            for band_index, band in enumerate(
                ("easy", "medium", "hard")
            ):
                profiles = Counter()
                inputs = set()
                outputs = set()
                for offset in range(200):
                    seed = start + 10_000 * band_index + offset
                    grid = generator.generate(
                        seed,
                        seed * 29 + 7,
                        difficulty=band,
                    )
                    output = independent_rule(grid)
                    observed = generator.observe_overrides(grid)
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(generator.rule_mirror(grid), output)
                    profiles[observed["scene_profile"]] += 1
                    inputs.add(json.dumps(grid, separators=(",", ":")))
                    outputs.add(
                        json.dumps(output, separators=(",", ":"))
                    )
                self.assertEqual(
                    set(profiles), set(generator.SCENE_PROFILES)
                )
                self.assertEqual(len(inputs), 200)
                self.assertEqual(len(outputs), 200)

    def test_source_target_and_change_count_are_exact(self):
        for profile in generator.SCENE_PROFILES:
            grid = generator.generate(
                700 + generator.SCENE_PROFILES.index(profile),
                91,
                scene_profile=profile,
            )
            color, source, target = independent_source_and_target(grid)
            output = generator.rule_mirror(grid)
            changed = {
                (row, col)
                for row in range(21)
                for col in range(21)
                if grid[row][col] != output[row][col]
            }
            self.assertEqual(changed, border_cells(target))
            self.assertTrue(changed.isdisjoint(border_cells(source)))
            self.assertTrue(all(output[row][col] == color for row, col in changed))

    def test_structural_and_semantic_mutations_are_rejected(self):
        original = self.pairs[0]["input"]

        extra_frame_color = [row[:] for row in original]
        extra_frame_color[0][0] = 8

        broken_source_border = [row[:] for row in original]
        broken_source_border[10][3] = 0

        dirty_target_interior = [row[:] for row in original]
        dirty_target_interior[8][12] = 3

        collapsed_palette = [
            [3 if value == 4 else value for value in row]
            for row in original
        ]

        third_slot = [row[:] for row in original]
        for row in (1, 2):
            for col in (1, 2, 3):
                third_slot[row][col] = 0

        for mutation in (
            extra_frame_color,
            broken_source_border,
            dirty_target_interior,
            collapsed_palette,
            third_slot,
            [],
            [[0] * 31],
            [[False, 2], [1, 3]],
            [[10, 2], [1, 3]],
            [row[:-1] for row in original],
        ):
            self.assertTrue(generator.self_check(mutation), mutation)
            self.assertEqual(generator.observe_overrides(mutation), {})

    def test_rule_mirror_is_broader_than_training_acceptance(self):
        extra_frame_color = [row[:] for row in self.pairs[0]["input"]]
        extra_frame_color[0][0] = 8
        snapshot = [row[:] for row in extra_frame_color]
        self.assertTrue(generator.self_check(extra_frame_color))
        output = generator.rule_mirror(extra_frame_color)
        self.assertNotEqual(output, extra_frame_color)
        self.assertEqual(extra_frame_color, snapshot)

    def test_determinism_fresh_returns_and_global_rng(self):
        state = random.getstate()
        first = generator.generate(441, 17, difficulty="hard")
        self.assertEqual(state, random.getstate())
        second = generator.generate(441, 17, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = (first[0][0] + 1) % 10
        self.assertEqual(
            second,
            generator.generate(441, 17, difficulty="hard"),
        )

    def test_rule_source_hashes_are_synchronized(self):
        canonical = self.row["program_solution"]
        base = json.loads(BASE_FILE.read_text())
        expected = normalized_rule_hash(canonical)
        self.assertEqual(expected[:12], generator.RULE_HASH)
        # raw_code is the immutable archival rule. It need not equal the
        # reviewed active rule, but the archive must retain its baseline hash.
        self.assertEqual(
            normalized_rule_hash(base["racket_target"]["raw_code"]),
            "04dc58ab5b0ed9048b0c9b19eb6fc5583f61fac391583ab74b2e22bbcf59db96",
        )
        # target_code is the selected rule and must track the canonical rule.
        self.assertEqual(
            normalized_rule_hash(base["racket_target"]["target_code"]),
            expected,
        )


if __name__ == "__main__":
    unittest.main()
