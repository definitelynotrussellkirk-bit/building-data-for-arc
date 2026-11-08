"""Focused regression tests for the crop-sort-pack generator repair."""

from __future__ import annotations

import importlib
import random
import unittest
from collections import Counter
from itertools import product


TASK_ID = "7b3c2eaee231"
from scripts.canonical_profile_gate import canonical_pairs as load_canonical_pairs


MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def official_pairs() -> list[dict[str, list[list[int]]]]:
    return load_canonical_pairs(TASK_ID)


def python_oracle(grid: list[list[int]]) -> list[list[int]]:
    crops = []
    for component in MODULE._components(grid):
        top = int(component["top"])
        left = int(component["left"])
        height = int(component["height"])
        width = int(component["width"])
        color = int(component["color"])
        crop = [
            [
                grid[top + r][left + c]
                for c in range(width)
            ]
            for r in range(height)
        ]
        crops.append((width, height, color, crop))
    crops.sort(key=lambda item: item[:3])
    out_h = max(height for _width, height, _color, _crop in crops)
    out_w = sum(width for width, _height, _color, _crop in crops) + len(crops) - 1
    out = [[0 for _ in range(out_w)] for _ in range(out_h)]
    left = 0
    for width, height, _color, crop in crops:
        top = (out_h - height) // 2
        for r, row in enumerate(crop):
            for c, value in enumerate(row):
                if value != 0:
                    out[top + r][left + c] = value
        left += width + 1
    return out


def reading_colors(grid: list[list[int]]) -> list[int]:
    return [
        int(component["color"])
        for component in sorted(
            MODULE._components(grid),
            key=lambda component: (component["top"], component["left"]),
        )
    ]


def sorted_colors(grid: list[list[int]]) -> list[int]:
    return [
        int(component["color"])
        for component in sorted(
            MODULE._components(grid),
            key=lambda component: (
                component["width"],
                component["height"],
                component["color"],
            ),
        )
    ]


class CropSortPackGeneratorTests(unittest.TestCase):
    def test_rule_hash_and_all_canonical_pairs(self):
        self.assertEqual("afe9721b6609", MODULE.RULE_HASH)
        signatures = set()
        for pair in official_pairs():
            grid = pair["input"]
            self.assertEqual([], MODULE.self_check(grid))
            self.assertEqual([], MODULE.strict_canonical_like(grid))
            self.assertEqual(pair["output"], python_oracle(grid))
            self.assertEqual(pair["output"], MODULE.rule_mirror(grid))
            signatures.add(MODULE.canonical_profile_signature(grid))
        self.assertEqual(MODULE._CANONICAL_SIGNATURES, signatures)

    def test_every_schedule_window_identifies_the_rule(self):
        for band in ("easy", "medium", "hard"):
            for start in range(len(MODULE.SCHEDULE_PROFILES)):
                seed = 70_000 + 100 * start + len(band)
                demos = []
                for sample_index in range(start, start + MODULE.EXAMPLES_NEEDED):
                    grid = MODULE.generate(seed, sample_index, difficulty=band)
                    demos.append({"input": grid, "output": MODULE.rule_mirror(grid)})
                query_grid = MODULE.generate(
                    seed,
                    start + MODULE.EXAMPLES_NEEDED,
                    difficulty=band,
                )
                query = {
                    "input": query_grid,
                    "output": MODULE.rule_mirror(query_grid),
                }
                with self.subTest(band=band, start=start):
                    self.assertEqual([], MODULE.lesson_identifiable(demos, query))

    def test_semantic_witnesses_really_kill_their_named_rivals(self):
        fired = Counter()
        for sample_index in range(64):
            grid = MODULE.generate(80_000 + sample_index, sample_index, difficulty="hard")
            expected = MODULE.rule_mirror(grid)
            for witness_name, predicate in MODULE.SEMANTIC_WITNESSES.items():
                if not predicate(grid):
                    continue
                fired[witness_name] += 1
                self.assertTrue(
                    any(
                        MODULE.SEMANTIC_RIVALS[rival_name](grid) != expected
                        for rival_name in MODULE.WITNESS_RIVALS[witness_name]
                    )
                )
        self.assertEqual(set(MODULE.SEMANTIC_WITNESSES), set(fired))

    def test_default_prior_is_anchored_and_covers_every_official_profile(self):
        for band in ("easy", "medium", "hard"):
            official_counts = Counter()
            axis_counts = Counter()
            for seed in range(600):
                grid = MODULE.generate(seed, seed * 19 + 7, difficulty=band)
                self.assertEqual([], MODULE.self_check(grid, difficulty=band))
                observed = MODULE.observe_overrides(grid)
                axis_counts[(observed["shape_family"], observed["lesson_profile"])] += 1
                signature = MODULE.canonical_profile_signature(grid)
                if signature in MODULE._CANONICAL_SIGNATURES:
                    official_counts[signature] += 1
            with self.subTest(band=band):
                self.assertGreaterEqual(sum(official_counts.values()), 100)
                self.assertEqual(MODULE._CANONICAL_SIGNATURES, set(official_counts))
                self.assertTrue(
                    all(
                        axis_counts[(family, lesson)] > 0
                        for family, lesson in product(
                            MODULE.SHAPE_FAMILIES,
                            MODULE.LESSON_PROFILES,
                        )
                    )
                )

    def test_every_default_draw_refutes_input_reading_order(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(250):
                grid = MODULE.generate(seed, seed * 23 + 11, difficulty=band)
                self.assertNotEqual(reading_colors(grid), sorted_colors(grid))

    def test_procedural_distribution_exposes_vertical_centering(self):
        witnesses = 0
        for seed in range(400):
            grid = MODULE.generate(
                seed,
                seed * 29 + 13,
                difficulty="hard",
                shape_family="procedural",
            )
            components = MODULE._components(grid)
            heights = [int(component["height"]) for component in components]
            if max(heights) - min(heights) < 2:
                continue
            output = python_oracle(grid)
            # A shorter crop must receive at least one row of top padding under
            # center packing; a top-alignment rival predicts zero for all.
            by_key = sorted(
                components,
                key=lambda component: (
                    component["width"],
                    component["height"],
                    component["color"],
                ),
            )
            left = 0
            max_h = max(heights)
            centered_here = False
            for component in by_key:
                height = int(component["height"])
                width = int(component["width"])
                expected_top = (max_h - height) // 2
                if expected_top > 0:
                    first_nonzero = next(
                        r
                        for r in range(max_h)
                        if any(output[r][left + c] != 0 for c in range(width))
                    )
                    self.assertEqual(expected_top, first_nonzero)
                    centered_here = True
                left += width + 1
            witnesses += int(centered_here)
        self.assertGreaterEqual(witnesses, 80)

    def test_all_declared_override_tuples_are_exact(self):
        for band in ("easy", "medium", "hard"):
            for canvas, lesson, family in product(
                MODULE.CANVAS_PROFILES,
                MODULE.LESSON_PROFILES,
                MODULE.SHAPE_FAMILIES,
            ):
                for seed in range(10):
                    grid = MODULE.generate(
                        seed,
                        seed * 31 + 17,
                        difficulty=band,
                        canvas=canvas,
                        lesson_profile=lesson,
                        shape_family=family,
                    )
                    self.assertEqual(
                        {
                            "canvas": canvas,
                            "lesson_profile": lesson,
                            "shape_family": family,
                        },
                        MODULE.observe_overrides(grid),
                    )
        with self.assertRaisesRegex(ValueError, "unknown override"):
            MODULE.generate(0, 0, made_up_axis=1)

    def test_determinism_fresh_returns_and_global_rng_purity(self):
        state = random.getstate()
        first = MODULE.generate(91, 17, difficulty="hard")
        self.assertEqual(state, random.getstate())
        expected = [row[:] for row in first]
        first[0][0] = 9 if first[0][0] != 9 else 8
        second = MODULE.generate(91, 17, difficulty="hard")
        self.assertEqual(expected, second)
        between = MODULE.generate(5, 99, difficulty="easy")
        self.assertNotEqual([], between)
        third = MODULE.generate(91, 17, difficulty="hard")
        self.assertEqual(expected, third)

    def test_self_check_rejects_structural_mutations_but_accepts_width_ties(self):
        pair = official_pairs()[1]
        tied_width_grid = [row[:] for row in pair["input"]]
        self.assertEqual([], MODULE.self_check(tied_width_grid))

        components = MODULE._components(tied_width_grid)
        removed = [row[:] for row in tied_width_grid]
        for r, c in components[0]["cells"]:
            removed[r][c] = 0
        self.assertTrue(MODULE.self_check(removed))

        recolored = [row[:] for row in tied_width_grid]
        replacement = int(components[1]["color"])
        for r, c in components[0]["cells"]:
            recolored[r][c] = replacement
        self.assertIn("objects must use distinct colors", MODULE.self_check(recolored))

        ragged = [row[:] for row in tied_width_grid]
        ragged[-1].pop()
        self.assertTrue(MODULE.self_check(ragged))

        invalid = [row[:] for row in tied_width_grid]
        invalid[0][0] = 10
        self.assertIn(
            "grid contains a non-integer or color outside 0..9",
            MODULE.self_check(invalid),
        )


if __name__ == "__main__":
    unittest.main()
