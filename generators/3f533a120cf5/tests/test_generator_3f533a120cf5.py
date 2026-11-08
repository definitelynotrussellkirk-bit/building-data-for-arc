from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest

from reviewer_support import canonical_path, find_root


generator = importlib.import_module(
    "puzzle_generators.per_puzzle.3f533a120cf5.generator"
)
ROOT = find_root(__file__)
CANON = canonical_path(ROOT)


def canonical_row():
    for line in CANON.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == generator.TASK_ID:
            return row
    raise AssertionError("canonical row missing")


def pairs(row):
    return list(row["train"]) + list(row["test"])


def rule_mirror(grid):
    h, w = len(grid), len(grid[0])
    gray = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    r1, r2 = min(r for r, _ in gray), max(r for r, _ in gray)
    c1, c2 = min(c for _, c in gray), max(c for _, c in gray)
    sep_row = next(
        r
        for r in range(h)
        if not r1 <= r <= r2
        and len({v for v in grid[r] if v != 0}) == 1
        and sum(v != 0 for v in grid[r]) > 1
    )
    sep_color = next(v for v in grid[sep_row] if v != 0)
    above_signal = sep_row > 0 and any(
        v != 0 and v != sep_color for v in grid[sep_row - 1]
    )
    key_row = sep_row - 1 if above_signal else sep_row + 1
    key_cols = [c for c, value in enumerate(grid[key_row]) if value != 0]
    key_left = min(key_cols)
    return [
        [
            grid[key_row][key_left + c - c1]
            if grid[r][c] == 5
            else sep_color
            for c in range(c1, c2 + 1)
        ]
        for r in range(r1, r2 + 1)
    ]


class Generator3f533a120cf5Tests(unittest.TestCase):
    def test_rule_hash_and_all_canonical_pairs(self):
        row = canonical_row()
        normalized = " ".join(row["program_solution"].split())
        self.assertEqual(
            hashlib.sha256(normalized.encode()).hexdigest()[:12],
            generator.RULE_HASH,
        )
        seen = set()
        for pair in pairs(row):
            grid = copy.deepcopy(pair["input"])
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(rule_mirror(grid), pair["output"])
            signature = generator.canonical_profile_signature(grid)
            self.assertIn(signature, generator._CANONICAL_SIGNATURES)
            seen.add(signature)
        self.assertEqual(seen, generator._CANONICAL_SIGNATURES)

    def test_prior_reaches_every_complete_profile_per_band(self):
        for band_index, band in enumerate(("easy", "medium", "hard")):
            seen = set()
            strict_matches = 0
            for i in range(600):
                grid = generator.generate(
                    100_000 + 10_000 * band_index + i,
                    200_000 + 10_000 * band_index + i,
                    difficulty=band,
                )
                signature = generator.canonical_profile_signature(grid)
                if signature in generator._CANONICAL_SIGNATURES:
                    strict_matches += 1
                    seen.add(signature)
            self.assertEqual(seen, generator._CANONICAL_SIGNATURES)
            self.assertGreaterEqual(strict_matches, 130)
            self.assertLessEqual(strict_matches, 260)

    def test_all_exact_axes_are_observable_together(self):
        grid = generator.generate(
            331,
            447,
            difficulty="easy",
            mask_height=6,
            mask_width=8,
            legend_side="below",
            key_side="below",
            key_distinct_colors=4,
            key_rows=3,
            gap_rows=4,
            separator_color=9,
        )
        self.assertEqual(generator.self_check(grid), [])
        self.assertEqual(
            generator.observe_overrides(grid),
            {
                "mask_height": 6,
                "mask_width": 8,
                "legend_side": "below",
                "key_side": "below",
                "key_distinct_colors": 4,
                "key_rows": 3,
                "gap_rows": 4,
                "separator_color": 9,
            },
        )

    def test_lawful_recombination_is_not_a_canonical_profile(self):
        grid = copy.deepcopy(canonical_row()["train"][0]["input"])
        info = generator._structure(grid)
        sep = info["separator_row"]
        key_rows = [sep - 1 - i for i in range(info["key_rows"])]
        left = info["legend_left"]
        # Change canonical equality pattern 0,1,2,0,0 to 0,1,2,1,0 while
        # preserving dimensions, placement, palette size, and all grammar.
        for row in key_rows:
            grid[row][left + 3] = grid[row][left + 1]
        self.assertEqual(generator.self_check(grid), [])
        self.assertNotIn(
            generator.canonical_profile_signature(grid),
            generator._CANONICAL_SIGNATURES,
        )

    def test_destructive_mutations_are_rejected(self):
        base = generator.generate(
            71,
            92,
            difficulty="medium",
            mask_height=6,
            mask_width=7,
            key_distinct_colors=3,
            key_rows=2,
            gap_rows=2,
            separator_color=9,
        )
        info = generator._structure(base)
        bad = []

        short_bar = copy.deepcopy(base)
        short_bar[info["separator_row"]][info["legend_left"]] = 0
        bad.append(short_bar)

        stray = copy.deepcopy(base)
        spot = next(
            (r, c)
            for r, row in enumerate(stray)
            for c, value in enumerate(row)
            if value == 0
            and not (info["mask_top"] <= r < info["mask_top"] + info["mask_height"])
        )
        stray[spot[0]][spot[1]] = 8 if info["separator_color"] != 8 else 7
        bad.append(stray)

        solid = copy.deepcopy(base)
        for r in range(info["mask_top"], info["mask_top"] + info["mask_height"]):
            for c in range(info["mask_left"], info["mask_left"] + info["mask_width"]):
                solid[r][c] = 5
        bad.append(solid)

        for mutation in bad:
            self.assertTrue(generator.self_check(mutation))

    def test_determinism_fresh_returns_and_global_rng_preservation(self):
        state = random.getstate()
        a = generator.generate(1234, 5678, difficulty="hard")
        self.assertEqual(state, random.getstate())
        b = generator.generate(1234, 5678, difficulty="hard")
        self.assertEqual(a, b)
        self.assertIsNot(a, b)
        a[0][0] = (a[0][0] + 1) % 10
        self.assertNotEqual(a, b)
        self.assertEqual(
            b,
            generator.generate(1234, 5678, difficulty="hard"),
        )

    def test_infeasible_combination_rejects_loudly(self):
        with self.assertRaises(ValueError):
            generator.generate(
                1,
                2,
                mask_width=3,
                key_distinct_colors=3,
            )


if __name__ == "__main__":
    unittest.main()
