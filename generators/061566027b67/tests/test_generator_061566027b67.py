from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

from solvers.grounded_rules import GROUNDED_RULES


generator = importlib.import_module(
    "puzzle_generators.per_puzzle.061566027b67.generator"
)
ROOT = Path(__file__).resolve().parents[1]
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


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
        pairs.extend([test] if isinstance(test, dict) else test)
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


def prefix_for_color(grid, color):
    prefix = [[0] * 17 for _row in range(17)]
    for row in range(16):
        running = 0
        for col in range(16):
            running += grid[row][col] == color
            prefix[row + 1][col + 1] = (
                prefix[row][col + 1] + running
            )
    return prefix


def rect_sum(prefix, top, left, bottom, right):
    return (
        prefix[bottom + 1][right + 1]
        - prefix[top][right + 1]
        - prefix[bottom + 1][left]
        + prefix[top][left]
    )


def independent_maxima(grid):
    prefixes = {
        color: prefix_for_color(grid, color)
        for color in range(1, 10)
    }
    max_area = 0
    maxima = []
    for top in range(16):
        for left in range(16):
            color = grid[top][left]
            if color == 0:
                continue
            prefix = prefixes[color]
            for bottom in range(top, 16):
                for right in range(left, 16):
                    area = (
                        (bottom - top + 1)
                        * (right - left + 1)
                    )
                    if (
                        rect_sum(
                            prefix,
                            top,
                            left,
                            bottom,
                            right,
                        )
                        != area
                    ):
                        continue
                    candidate = (
                        area,
                        top,
                        left,
                        bottom,
                        right,
                        color,
                    )
                    if area > max_area:
                        max_area = area
                        maxima = [candidate]
                    elif area == max_area:
                        maxima.append(candidate)
    return tuple(maxima)


def independent_rule(grid):
    maxima = independent_maxima(grid)
    if not maxima:
        raise ValueError("no nonzero rectangle")
    _area, top, left, bottom, right, color = maxima[0]
    output = [[0] * 16 for _row in range(16)]
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            output[row][col] = color
    return output


def independent_facts(grid):
    maxima = independent_maxima(grid)
    if len(maxima) != 1:
        raise AssertionError(maxima)
    rectangle = maxima[0]
    _area, top, left, bottom, right, color = rectangle
    winner = {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
    }
    attached = {
        (row, col)
        for row in range(16)
        for col in range(16)
        if (row, col) not in winner
        and grid[row][col] == color
        and any(
            (row + delta_row, col + delta_col) in winner
            for delta_row, delta_col in CARDINAL
        )
    }
    height = bottom - top + 1
    width = right - left + 1
    short, long = sorted((height, width))
    profile = {
        (2, 7, False): "2x7_clean",
        (3, 4, True): "3x4_tab",
        (3, 3, True): "3x3_tab",
        (2, 6, True): "2x6_tab",
    }.get((short, long, len(attached) == 1))
    return {
        "rectangle": rectangle,
        "profile": profile,
        "winner_color": color,
        "attached": attached,
        "nonzero_count": sum(
            value != 0 for row in grid for value in row
        ),
        "palette": set(value for row in grid for value in row),
    }


def transform_grid(grid, transform):
    transformed = [list(row) for row in grid]
    if transform >= 4:
        transformed = [list(reversed(row)) for row in transformed]
    for _turn in range(transform % 4):
        transformed = [
            list(row) for row in zip(*reversed(transformed))
        ]
    return transformed


class Generator061566027b67Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = canonical_rows()
        cls.all_pairs = all_canonical_pairs()
        cls.pairs = unique_canonical_pairs()

    def test_all_canonical_rows_pairs_and_profiles(self):
        self.assertEqual(len(self.rows), 2)
        self.assertEqual(len(self.all_pairs), 8)
        self.assertEqual(len(self.pairs), 4)
        profiles = set()
        for index, pair in enumerate(self.pairs):
            grid = pair["input"]
            snapshot = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(independent_rule(grid), pair["output"])
            self.assertEqual(generator.rule_mirror(grid), pair["output"])
            self.assertEqual(grid, snapshot)
            self.assertEqual(
                generator.canonical_profile_index(grid),
                index,
            )
            facts = independent_facts(grid)
            profiles.add(facts["profile"])
            self.assertEqual(facts["palette"], set(range(10)))
            self.assertTrue(72 <= facts["nonzero_count"] <= 102)
        self.assertEqual(
            profiles,
            set(generator.RECTANGLE_PROFILES),
        )

    def test_all_global_d4_symmetries_commute(self):
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
                    independent_rule(transformed_input),
                    transformed_output,
                )
                self.assertEqual(
                    generator.rule_mirror(transformed_input),
                    transformed_output,
                )
                self.assertEqual(
                    generator.canonical_profile_index(
                        transformed_input
                    ),
                    index,
                )

    def test_every_exact_axis_cross_is_observed(self):
        for band in ("easy", "medium", "hard"):
            for profile in generator.RECTANGLE_PROFILES:
                for winner_color in (1, 9):
                    expected = {
                        "rectangle_profile": profile,
                        "winner_color": winner_color,
                    }
                    seed = (
                        10_000
                        + 100 * generator.RECTANGLE_PROFILES.index(profile)
                        + 10 * winner_color
                        + len(band)
                    )
                    grid = generator.generate(
                        seed,
                        seed * 19 + 3,
                        difficulty=band,
                        **expected,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(
                        generator.observe_overrides(grid),
                        expected,
                    )
                    self.assertEqual(
                        generator.rule_mirror(grid),
                        independent_rule(grid),
                    )

    def test_default_distribution_is_complete_stable_and_diverse(self):
        density_ranges = {
            "easy": (72, 82),
            "medium": (82, 92),
            "hard": (92, 102),
        }
        for start in (0, 50_000):
            for band_index, band in enumerate(
                ("easy", "medium", "hard")
            ):
                profiles = set()
                colors = set()
                densities = []
                pairs_seen = set()
                for offset in range(120):
                    seed = start + band_index * 10_000 + offset
                    grid = generator.generate(
                        seed,
                        seed * 29 + 7,
                        difficulty=band,
                    )
                    facts = independent_facts(grid)
                    output = independent_rule(grid)
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(generator.rule_mirror(grid), output)
                    profiles.add(facts["profile"])
                    colors.add(facts["winner_color"])
                    densities.append(facts["nonzero_count"])
                    pairs_seen.add((
                        tuple(map(tuple, grid)),
                        tuple(map(tuple, output)),
                    ))
                self.assertEqual(
                    profiles,
                    set(generator.RECTANGLE_PROFILES),
                )
                self.assertEqual(colors, set(range(1, 10)))
                self.assertGreaterEqual(
                    min(densities),
                    density_ranges[band][0],
                )
                self.assertLessEqual(
                    max(densities),
                    density_ranges[band][1],
                )
                self.assertGreaterEqual(len(pairs_seen), 119)

    def test_structural_and_semantic_mutations_are_rejected(self):
        clean = [row[:] for row in self.pairs[0]["input"]]
        attached_clean = [row[:] for row in clean]
        attached_clean[10][2] = 6
        tabbed = [row[:] for row in self.pairs[1]["input"]]
        missing_tab = [row[:] for row in tabbed]
        missing_tab[2][3] = 0
        missing_palette = [row[:] for row in clean]
        missing_palette = [
            [8 if value == 9 else value for value in row]
            for row in missing_palette
        ]
        invalid_color = [row[:] for row in clean]
        invalid_color[0][0] = 10
        for mutation in (
            attached_clean,
            missing_tab,
            missing_palette,
            invalid_color,
            [],
            [[0] * 16 for _row in range(16)],
            [[0] * 15 for _row in range(16)],
            [[0] * 16 for _row in range(15)],
            [[0] * 16 for _row in range(17)],
        ):
            self.assertTrue(generator.self_check(mutation), mutation)

    def test_plausible_cross_profile_recombination_is_calibrated_out(self):
        candidate = [row[:] for row in self.pairs[0]["input"]]
        candidate[10][2] = 6
        self.assertEqual(
            generator.self_check(candidate),
            [
                "winner dimensions and attached-tab role must match "
                "a published profile"
            ],
        )
        self.assertTrue(independent_rule(candidate))
        with self.assertRaisesRegex(ValueError, "published profile"):
            generator.rule_mirror(candidate)

    def test_source_sync_hash_determinism_freshness_and_global_rng(self):
        sources = {row["program_solution"] for row in self.rows}
        self.assertEqual(len(sources), 1)
        source = next(iter(sources))
        for relative_path in (
            "data/base/solutions/training/"
            "91714a58__061566027b67.json",
            "data/base/solutions/augmented/"
            "91714a58__dc9241d3c790.json",
        ):
            target = json.loads(
                (ROOT / relative_path).read_text()
            )["racket_target"]
            self.assertEqual(target["raw_code"], source)
            self.assertEqual(target["target_code"], source)
        self.assertEqual(
            normalized_rule_hash(
                GROUNDED_RULES[generator.TASK_ID]
            ),
            normalized_rule_hash(source),
        )
        self.assertEqual(
            generator.RULE_HASH,
            normalized_rule_hash(source)[:12],
        )

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
        first[0][0] = 9 if first[0][0] != 9 else 0
        self.assertEqual(
            generator.generate(37, 43, difficulty="hard"),
            again,
        )


if __name__ == "__main__":
    unittest.main()
