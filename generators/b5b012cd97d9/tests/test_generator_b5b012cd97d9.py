"""Focused semantic and contract tests for generator b5b012cd97d9."""
from __future__ import annotations

import hashlib
import json
import math
import random
import unittest
from collections import Counter
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_path, canonical_pairs as load_canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
generator, _GENERATOR_PATH, _GENERATOR_SHA256 = load_selected_generator(
    "b5b012cd97d9", root=ROOT
)
BASE_FILES = (
    ROOT / "shared/data/base/solutions/training/8abad3cf__b5b012cd97d9.json",
    ROOT / "shared/data/base/solutions/augmented/8abad3cf__fb68478596dd.json",
)


def canonical_row():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for raw in handle:
            row = json.loads(raw)
            if row.get("task_id") == generator.TASK_ID:
                return row
    raise AssertionError("canonical row not found")


def canonical_pairs():
    return [
        {"input": row["input"], "output": row["output"]}
        for row in load_canonical_pairs(
            generator.TASK_ID, root=ROOT, variant=0, labeled_only=True
        )
    ]


def normalized_rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def reference_rule(grid):
    counts = Counter(value for row in grid for value in row)
    nonzero = {
        color: count
        for color, count in counts.items()
        if color != 0
    }
    maximum = max(nonzero.values())
    background_candidates = [
        color
        for color, count in nonzero.items()
        if count == maximum
    ]
    if len(background_candidates) != 1:
        raise ValueError("background must have a unique nonzero maximum")
    background = background_candidates[0]
    entries = [
        (counts[color], color)
        for color in sorted(counts)
        if color != background
    ]
    ordered = sorted(
        entries,
        key=lambda entry: entry[0],
        reverse=True,
    )
    big_count, big_color = ordered[0]
    repeated = [entry for entry in ordered[1:] if entry[0] > 1]
    small = repeated[0] if repeated else None
    single = next(
        (entry for entry in entries if entry[0] == 1),
        None,
    )

    def side(count):
        result = math.isqrt(count)
        if result * result != count:
            raise ValueError("non-square role count")
        return result

    big_side = side(big_count)
    small_side = side(small[0]) if small else 0
    output_height = max(
        big_side,
        small_side + int(single is not None),
    )
    small_col = 2 if single else 0
    big_col = small_col + small_side + 1
    output_width = big_col + big_side
    small_row = output_height - small_side
    output = [
        [background for _col in range(output_width)]
        for _row in range(output_height)
    ]
    for row in range(big_side):
        for col in range(big_col, big_col + big_side):
            output[row][col] = big_color
    if small:
        for row in range(small_row, output_height):
            for col in range(small_col, small_col + small_side):
                output[row][col] = small[1]
    if single:
        output[-1][0] = single[1]
    return output


def mass_grid(entries, *, background=7, height=10, width=10):
    cells = [
        color
        for color, count in entries
        for _index in range(count)
    ]
    if len(cells) >= height * width / 2:
        raise AssertionError("background must remain the unique mode")
    values = cells + [background] * (height * width - len(cells))
    return [
        values[row * width:(row + 1) * width]
        for row in range(height)
    ]


class GeneratorB5b012cd97d9Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = canonical_pairs()

    def test_all_canonical_pairs_profiles_and_rule(self):
        self.assertEqual(len(self.pairs), 3)
        for index, (pair, profile) in enumerate(
            zip(self.pairs, generator.SCENE_PROFILES)
        ):
            source = pair["input"]
            snapshot = [row[:] for row in source]
            self.assertEqual(generator.self_check(source), [])
            self.assertEqual(
                generator.observe_overrides(source),
                {
                    "scene_profile": profile,
                    "layout_variant": "canonical",
                },
            )
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
                for offset in range(300):
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
                self.assertGreaterEqual(len(inputs), 285)
                self.assertGreaterEqual(len(outputs), 255)

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
            profiles_by_band["easy"]["no_single_7x4_3_2"],
            profiles_by_band["easy"]["zero_big_5x10_4_2"],
        )
        self.assertGreater(
            profiles_by_band["hard"]["zero_big_5x10_4_2"],
            profiles_by_band["hard"]["no_single_7x4_3_2"],
        )

    def test_structural_and_semantic_mutations_are_rejected(self):
        first, second, third = (
            [row[:] for row in pair["input"]]
            for pair in self.pairs
        )
        padded = [[7] * 9]
        padded.extend([[7] + row + [7] for row in first])
        padded.append([7] * 9)

        wrong_count = [row[:] for row in first]
        wrong_count[0][0] = 7

        unsupported_layout = [row[:] for row in first]
        unsupported_layout[0][0], unsupported_layout[0][5] = (
            unsupported_layout[0][5],
            unsupported_layout[0][0],
        )

        zero_in_nonzero_profile = [
            [0 if value == 4 else value for value in row]
            for row in first
        ]

        added_singleton = [row[:] for row in second]
        added_singleton[3][0] = 1

        zero_big_removed = [
            [6 if value == 0 else value for value in row]
            for row in third
        ]

        for mutation in (
            padded,
            wrong_count,
            unsupported_layout,
            zero_in_nonzero_profile,
            added_singleton,
            zero_big_removed,
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
            mass_grid(((2, 25), (4, 9), (6, 1))),
            mass_grid(((9, 16), (6, 4))),
            mass_grid(((0, 16), (4, 9), (2, 1))),
            mass_grid(((3, 9),)),
            mass_grid(((8, 9), (5, 4), (1, 1), (2, 1))),
        )
        for grid in cases:
            snapshot = [row[:] for row in grid]
            self.assertEqual(
                generator.rule_mirror(grid),
                reference_rule(grid),
            )
            self.assertEqual(grid, snapshot)
            self.assertNotEqual(generator.self_check(grid), [])

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
        programs = {
            variant["program_solution"]
            for variant in Catalog(ROOT).get(generator.TASK_ID)["variants"]
            if isinstance(variant.get("program_solution"), str)
        }
        self.assertEqual(programs, {canonical})
        expected = normalized_rule_hash(canonical)
        self.assertEqual(generator.RULE_HASH, expected[:12])
        # Base-solution JSON retains archival raw/target programs; the selected
        # catalog program is a later canonical authority and need not be byte- or
        # whitespace-equivalent to those provenance snapshots.  The two copied
        # base records must, however, agree with each other exactly.
        archival = []
        for path in BASE_FILES:
            base = json.loads(path.read_text())
            racket = base["racket_target"]
            self.assertEqual(racket["target_status"], "verified_racket_available")
            self.assertTrue(racket["raw_code"].strip())
            self.assertTrue(racket["target_code"].strip())
            archival.append((racket["raw_code"], racket["target_code"]))
        self.assertEqual(archival[0], archival[1])


if __name__ == "__main__":
    unittest.main()
