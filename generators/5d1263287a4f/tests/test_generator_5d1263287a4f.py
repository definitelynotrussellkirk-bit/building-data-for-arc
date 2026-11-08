"""Focused semantic regressions for generator 5d1263287a4f."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import statistics
import unittest
from collections import Counter, deque

from reviewer_support import canonical_path, find_root
from solvers.grounded_rules import GROUNDED_RULES

TASK_ID = "5d1263287a4f"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = find_root(__file__)


def comps(grid, background=0):
    height, width = len(grid), len(grid[0])
    seen = [[False] * width for _ in range(height)]
    count = 0
    for row in range(height):
        for column in range(width):
            if grid[row][column] == background or seen[row][column]:
                continue
            count += 1
            queue = deque([(row, column)])
            seen[row][column] = True
            while queue:
                r, c = queue.popleft()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and grid[nr][nc] != background
                    ):
                        seen[nr][nc] = True
                        queue.append((nr, nc))
    return count


def modal_bg(grid):
    return Counter(value for row in grid for value in row).most_common(1)[0][0]


def canonical_row():
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


def normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


class Generator5d1263287a4fTests(unittest.TestCase):
    def test_all_canonical_train_and_test_pairs(self):
        row = canonical_row()
        pairs = [*row["train"], *row["test"]]
        self.assertEqual(len(pairs), 4)
        for pair in pairs:
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            self.assertEqual(MODULE.self_check(source), [])
            self.assertEqual(MODULE.rule_mirror(source), pair["output"])
            self.assertEqual(source, before)

    def test_every_pattern_and_band_uses_only_copy_or_mirror_decoys(self):
        for band in ("easy", "medium", "hard"):
            for pattern in MODULE.TILE_PATTERNS:
                for seed in range(16):
                    grid = MODULE.generate(
                        seed,
                        seed * 23 + 5,
                        difficulty=band,
                        tile_pattern=pattern,
                    )
                    h, w = len(grid), len(grid[0])
                    third = w // 3
                    left = [row[:third] for row in grid]
                    middle = [row[third:2 * third] for row in grid]
                    right = [row[2 * third:] for row in grid]
                    mirror = [list(reversed(row)) for row in left]
                    self.assertIn(middle, (left, mirror))
                    self.assertIn(right, (left, mirror))
                    self.assertNotEqual(left, mirror)
                    self.assertIn(
                        MODULE.observe_overrides(grid)["panel_layout"],
                        MODULE.PANEL_LAYOUTS,
                    )
                    self.assertEqual(MODULE.rule_mirror(grid), left)
                    self.assertEqual(MODULE.self_check(grid), [])
                    self.assertTrue(2 <= h <= 10)
                    self.assertTrue(2 <= third <= 10)
                    self.assertIn(len({v for row in left for v in row}), (3, 4))

    def test_exact_override_boundaries_are_observable_in_every_band(self):
        cases = [
            {"grid_h": 2, "grid_w_third": 2, "palette_size": 3},
            {"grid_h": 2, "grid_w_third": 2, "palette_size": 4},
            {"grid_h": 10, "grid_w_third": 10, "palette_size": 3},
            {"grid_h": 10, "grid_w_third": 10, "palette_size": 4},
        ]
        for band in ("easy", "medium", "hard"):
            for pattern in MODULE.TILE_PATTERNS:
                for layout in MODULE.PANEL_LAYOUTS:
                    for case in cases:
                        grid = MODULE.generate(
                            101,
                            207,
                            difficulty=band,
                            tile_pattern=pattern,
                            panel_layout=layout,
                            **case,
                        )
                        observed = MODULE.observe_overrides(grid)
                        self.assertEqual(
                            observed, {**case, "panel_layout": layout}
                        )
                        self.assertEqual(MODULE.self_check(grid), [])

    def test_self_check_rejects_rule_hiding_and_malformed_impostors(self):
        base = MODULE.generate(311, 509, difficulty="medium")
        h, w = len(base), len(base[0])
        third = w // 3
        modal = modal_bg(base)
        foreground = next(v for row in base for v in row if v != modal)

        all_background = [[modal] * w for _ in range(h)]
        full_one_color = [[foreground] * w for _ in range(h)]
        singleton = [[modal] * w for _ in range(h)]
        singleton[h // 2][w // 2] = foreground
        solid_2x2 = [[modal] * w for _ in range(h)]
        for r in range(min(2, h)):
            for c in range(min(2, w)):
                solid_2x2[r][c] = foreground
        short_line = [[modal] * w for _ in range(h)]
        for c in range(min(4, w)):
            short_line[h // 2][c] = foreground
        middle_mismatch = copy.deepcopy(base)
        middle_mismatch[0][third] = (middle_mismatch[0][third] + 1) % 10
        right_mismatch = copy.deepcopy(base)
        right_mismatch[-1][2 * third] = (right_mismatch[-1][2 * third] + 1) % 10
        ragged = copy.deepcopy(base)
        ragged[-1].pop()
        nondivisible = [row[:-1] for row in base]
        invalid_color = copy.deepcopy(base)
        invalid_color[0][0] = 10
        boolean_color = copy.deepcopy(base)
        boolean_color[0][0] = True

        for mutation in (
            all_background,
            full_one_color,
            singleton,
            solid_2x2,
            short_line,
            middle_mismatch,
            right_mismatch,
            ragged,
            nondivisible,
            invalid_color,
            boolean_color,
        ):
            self.assertTrue(MODULE.self_check(mutation), mutation)

    def test_negative_recombination_is_rejected(self):
        first = MODULE.generate(
            401, 607, difficulty="hard", grid_h=5, grid_w_third=5
        )
        second = MODULE.generate(
            409, 613, difficulty="hard", grid_h=5, grid_w_third=5
        )
        tile_a = [row[:5] for row in first]
        tile_b = [row[:5] for row in second]
        self.assertNotEqual(tile_a, tile_b)
        recombined = [tile_a[r] + tile_b[r] + tile_a[r] for r in range(5)]
        self.assertTrue(MODULE.self_check(recombined))

    def test_default_fragmentation_stays_in_canonical_envelope(self):
        counts = []
        for band in ("easy", "medium", "hard"):
            for seed in range(1, 41):
                grid = MODULE.generate(seed, seed, difficulty=band)
                counts.append(comps(grid, modal_bg(grid)))
        self.assertEqual(statistics.median(counts), 3)
        self.assertGreaterEqual(sum(value == 3 for value in counts), 55)

    def test_determinism_freshness_global_rng_and_invalid_overrides(self):
        invalid = (
            {"grid_h": 1},
            {"grid_w_third": 11},
            {"palette_size": 2},
            {"tile_pattern": "unrelated_panels"},
            {"unknown_axis": 1},
        )
        for overrides in invalid:
            with self.assertRaises(ValueError):
                MODULE.generate(1, 2, **overrides)

        random.seed(20260723)
        state = random.getstate()
        first = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))
        first[0][0] = (first[0][0] + 1) % 10
        self.assertEqual(
            second, MODULE.generate(97, 103, difficulty="hard")
        )

    def test_rule_pin_and_authorities_match(self):
        source = canonical_row()["program_solution"]
        grounded = GROUNDED_RULES[TASK_ID]
        self.assertEqual(normalized_hash(source), normalized_hash(grounded))
        self.assertEqual(MODULE.RULE_HASH, normalized_hash(source))
        self.assertEqual(MODULE.RULE_HASH, "92f6a0f9f7b3")


    @staticmethod
    def _pair(grid):
        return {"input": grid, "output": MODULE.rule_mirror(grid)}

    @staticmethod
    def _rightmost(grid):
        third = len(grid[0]) // 3
        return [row[2 * third:] for row in grid]

    def test_known_20261008_shortcut_window_is_identifiable(self):
        pairs = [
            self._pair(MODULE.generate(20261008, index, difficulty="medium"))
            for index in range(4)
        ]
        self.assertEqual(MODULE.lesson_identifiable(pairs[:3], pairs[3]), [])
        self.assertTrue(
            any(self._rightmost(pair["input"]) != pair["output"] for pair in pairs[:3])
        )

    def test_every_three_draw_window_refutes_rightmost_shortcut(self):
        self.assertEqual(MODULE.EXAMPLES_NEEDED, 3)
        self.assertEqual(MODULE.LESSON_SCHEDULE_PERIOD, 4)
        self.assertEqual(set(MODULE.SCHEDULE_PROFILES), set(MODULE.PANEL_LAYOUTS))
        for band in ("easy", "medium", "hard"):
            for seed in range(8):
                for start in range(8):
                    pairs = [
                        self._pair(
                            MODULE.generate(seed, start + offset, difficulty=band)
                        )
                        for offset in range(4)
                    ]
                    self.assertEqual(
                        MODULE.lesson_identifiable(pairs[:3], pairs[3]), [],
                        (band, seed, start),
                    )
                    self.assertTrue(
                        any(
                            self._rightmost(pair["input"]) != pair["output"]
                            for pair in pairs[:3]
                        ),
                        (band, seed, start),
                    )

    def test_layout_schedule_matches_observed_layout_and_overrides_stay_exact(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(6):
                for sample_index in range(8):
                    scheduled = MODULE.schedule_profile(seed, sample_index, band)
                    grid = MODULE.generate(seed, sample_index, difficulty=band)
                    self.assertEqual(
                        MODULE.observe_overrides(grid)["panel_layout"], scheduled
                    )
                    for layout in MODULE.PANEL_LAYOUTS:
                        overridden = MODULE.generate(
                            seed,
                            sample_index,
                            difficulty=band,
                            panel_layout=layout,
                        )
                        self.assertEqual(
                            MODULE.observe_overrides(overridden)["panel_layout"], layout
                        )

    def test_declared_rightmost_shortcut_fits_canonical_but_has_generated_witness(self):
        shortcut = MODULE.CANONICAL_SHORTCUTS["rightmost_panel"]
        row = canonical_row()
        for pair in [*row["train"], *row["test"]]:
            self.assertEqual(shortcut(pair["input"]), pair["output"])
        witness = MODULE.generate(11, 0, difficulty="medium", panel_layout="right_mirror")
        self.assertNotEqual(shortcut(witness), MODULE.rule_mirror(witness))

    def test_lesson_hook_rejects_underidentified_and_malformed_lessons(self):
        demos = [
            self._pair(
                MODULE.generate(
                    700 + index,
                    index,
                    difficulty="medium",
                    panel_layout=layout,
                )
            )
            for index, layout in enumerate(
                ("all_same", "middle_mirror", "all_same")
            )
        ]
        query = self._pair(
            MODULE.generate(
                800,
                3,
                difficulty="medium",
                panel_layout="both_mirror",
            )
        )
        reasons = MODULE.lesson_identifiable(demos, query)
        self.assertTrue(any("rightmost_panel" in reason for reason in reasons), reasons)

        malformed = copy.deepcopy(demos)
        malformed[0].pop("output")
        malformed_reasons = MODULE.lesson_identifiable(malformed, query)
        self.assertTrue(
            any("demo 0" in reason and "output" in reason for reason in malformed_reasons),
            malformed_reasons,
        )


if __name__ == "__main__":
    unittest.main()
