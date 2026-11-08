"""Focused semantic and contract tests for generator 5c9fd75979d1."""
from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter, deque
from pathlib import Path

from solvers.grounded_rules import GROUNDED_RULES
from reviewer_support import find_root, canonical_path


generator = importlib.import_module(
    "puzzle_generators.per_puzzle.5c9fd75979d1.generator"
)
ROOT = find_root(__file__)
DATA = canonical_path(ROOT).parent.parent
BASE_FILES = (
    DATA
    / "base/solutions/training/"
    "80214e03__5c9fd75979d1.json",
    DATA
    / "base/solutions/augmented/"
    "80214e03__cc1f1f3107d3.json",
)


def canonical_row():
    with canonical_path(ROOT).open() as handle:
        for raw in handle:
            row = json.loads(raw)
            if (
                row.get("task_id") == generator.TASK_ID
                and row.get("source") == "training"
            ):
                return row
    raise AssertionError("canonical training row not found")


def canonical_pairs():
    row = canonical_row()
    test = row["test"]
    return row["train"] + (
        test if isinstance(test, list) else [test]
    )


def normalized_rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def independent_components(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            start = (start_row, start_col)
            if color == 0 or start in seen:
                continue
            queue = deque([start])
            seen.add(start)
            cells = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for delta_row, delta_col in (
                    (-1, 0),
                    (0, -1),
                    (0, 1),
                    (1, 0),
                ):
                    candidate = (
                        row + delta_row,
                        col + delta_col,
                    )
                    if (
                        0 <= candidate[0] < height
                        and 0 <= candidate[1] < width
                        and candidate not in seen
                        and grid[candidate[0]][candidate[1]] == color
                    ):
                        seen.add(candidate)
                        queue.append(candidate)
            rows = [row for row, _col in cells]
            cols = [col for _row, col in cells]
            result.append(
                (
                    color,
                    min(rows),
                    min(cols),
                    max(rows),
                    max(cols),
                )
            )
    return result


def independent_analysis(grid):
    retained = [
        record
        for record in independent_components(grid)
        if (
            (record[3] - record[1] + 1)
            * (record[4] - record[2] + 1)
            > 2
        )
    ]
    row_breaks = sorted({
        coordinate
        for record in retained
        for coordinate in (record[1], record[3] + 1)
    })
    col_breaks = sorted({
        coordinate
        for record in retained
        for coordinate in (record[2], record[4] + 1)
    })
    row_groups = [
        (row_breaks[index], row_breaks[index + 1] - 1)
        for index in range(len(row_breaks) - 1)
    ]
    col_slots = [
        (col_breaks[index], col_breaks[index + 1] - 1)
        for index in range(len(col_breaks) - 1)
    ]

    def color_for(row_group, col_slot):
        for color, top, left, bottom, right in retained:
            if (
                top <= row_group[0]
                and bottom >= row_group[1]
                and left <= col_slot[0]
                and right >= col_slot[1]
            ):
                return color
        return 0

    original = [
        [
            color_for(row_group, col_slot)
            for col_slot in col_slots
        ]
        for row_group in row_groups
    ]
    return {
        "row_groups": row_groups,
        "col_slots": col_slots,
        "original": original,
        "output": [list(reversed(row)) for row in original],
    }


def bbox_holes(grid):
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value
    ]
    top = min(row for row, _col in cells)
    bottom = max(row for row, _col in cells)
    left = min(col for _row, col in cells)
    right = max(col for _row, col in cells)
    return sum(
        grid[row][col] == 0
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
    )


class Generator5c9fd75979d1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = canonical_pairs()

    def test_all_canonical_pairs_profiles_and_rule(self):
        self.assertEqual(len(self.pairs), len(generator.SCENE_PROFILES))
        for pair, profile in zip(
            self.pairs,
            generator.SCENE_PROFILES,
        ):
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
            self.assertEqual(
                independent_analysis(source)["output"],
                pair["output"],
            )
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
                    independent_analysis(grid)["output"],
                )
                role_count = generator._PROFILE_DATA[profile]["role_count"]
                fallback = generator._fallback_scene(
                    profile,
                    tuple(range(1, role_count + 1)),
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
                for offset in range(150):
                    seed = start + 10_000 * band_index + offset
                    grid = generator.generate(
                        seed,
                        seed * 29 + 7,
                        difficulty=band,
                    )
                    output = independent_analysis(grid)["output"]
                    observed = generator.observe_overrides(grid)
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(generator.rule_mirror(grid), output)
                    profiles[observed["scene_profile"]] += 1
                    inputs.add(json.dumps(grid, separators=(",", ":")))
                    outputs.add(
                        json.dumps(output, separators=(",", ":"))
                    )
                self.assertEqual(
                    set(profiles),
                    set(generator.SCENE_PROFILES),
                )
                self.assertEqual(len(inputs), 150)
                self.assertGreaterEqual(len(outputs), 140)

    def test_hard_band_has_more_noise_without_losing_profiles(self):
        easy_holes = 0
        hard_holes = 0
        for seed in range(120):
            easy = generator.generate(
                20_000 + seed,
                seed * 11 + 1,
                difficulty="easy",
            )
            hard = generator.generate(
                20_000 + seed,
                seed * 11 + 1,
                difficulty="hard",
            )
            easy_holes += bbox_holes(easy)
            hard_holes += bbox_holes(hard)
            self.assertEqual(generator.self_check(easy), [])
            self.assertEqual(generator.self_check(hard), [])
        self.assertGreater(hard_holes, easy_holes * 1.5)

    def test_structural_and_semantic_mutations_are_rejected(self):
        original = generator.generate(
            731,
            19,
            scene_profile="noisy_3x3_repeat6",
        )
        analysis = independent_analysis(original)

        solid = [row[:] for row in original]
        for row_index, (row_start, row_end) in enumerate(
            analysis["row_groups"]
        ):
            for col_index, (col_start, col_end) in enumerate(
                analysis["col_slots"]
            ):
                color = analysis["original"][row_index][col_index]
                for row in range(row_start, row_end + 1):
                    for col in range(col_start, col_end + 1):
                        solid[row][col] = color

        outside_color = [row[:] for row in original]
        outside_color[0][0] = next(
            value for row in original for value in row if value
        )

        wrong_slot_color = [row[:] for row in original]
        first_color = analysis["original"][0][0]
        other_color = next(
            value
            for row in original
            for value in row
            if value not in (0, first_color)
        )
        row_start, _row_end = analysis["row_groups"][0]
        col_start, _col_end = analysis["col_slots"][0]
        wrong_slot_color[row_start][col_start] = other_color

        collapsed_role = [
            [
                first_color if value == other_color else value
                for value in row
            ]
            for row in original
        ]

        sparse_slot = [row[:] for row in original]
        row_start, row_end = analysis["row_groups"][0]
        col_start, col_end = analysis["col_slots"][0]
        for row in range(row_start, row_end + 1):
            for col in range(col_start, col_end + 1):
                if row != row_start and col != col_start:
                    sparse_slot[row][col] = 0

        for mutation in (
            solid,
            outside_color,
            wrong_slot_color,
            collapsed_role,
            sparse_slot,
        ):
            self.assertNotEqual(generator.self_check(mutation), [])

        malformed = (
            [],
            [[]],
            [[1], [1, 2]],
            [[True]],
            [[10]],
            [[0] * 31],
        )
        for grid in malformed:
            self.assertNotEqual(generator.self_check(grid), [])

    def test_rule_mirror_is_broad_but_self_check_is_calibrated(self):
        grid = [[0 for _col in range(8)] for _row in range(8)]
        colors = ((1, 2), (3, 4))
        for slot_row in range(2):
            for slot_col in range(2):
                for row in range(1 + 3 * slot_row, 4 + 3 * slot_row):
                    for col in range(1 + 3 * slot_col, 4 + 3 * slot_col):
                        grid[row][col] = colors[slot_row][slot_col]
        expected = [[2, 1], [4, 3]]
        self.assertEqual(generator.rule_mirror(grid), expected)
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

    def test_canonical_hash_and_preserved_archival_sources(self):
        canonical = GROUNDED_RULES[generator.TASK_ID]
        expected = normalized_rule_hash(canonical)
        self.assertEqual(generator.RULE_HASH, expected[:12])
        self.assertEqual(normalized_rule_hash(canonical_row()["program_solution"]), expected)
        # Imported raw/target text is historical provenance, not the canonical
        # execution authority. Preserve it rather than rewrite it to fit a hash.
        archival = {
            "raw_code": "29a3620fd294a66a5d782b4f75145b59a1ee17ec9328fd9747f5878d55111edf",
            "target_code": "03ffbe030b540f25cc80ac6ec05e432007ea132e96d9cdf3108eece5d0c8266f",
        }
        for path in BASE_FILES:
            base = json.loads(path.read_text())
            racket = base["racket_target"]
            self.assertEqual(base["task_id"], generator.TASK_ID)
            for field, digest in archival.items():
                self.assertEqual(normalized_rule_hash(racket[field]), digest)


if __name__ == "__main__":
    unittest.main()
