"""Focused semantic regressions for generator 4326f5c2ded0."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path


TASK_ID = "4326f5c2ded0"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]


def _rows():
    rows = []
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            rows.append(row)
    if len(rows) != 2:
        raise AssertionError(f"expected two canonical rows for {TASK_ID}, found {len(rows)}")
    return rows


def _grid(value):
    return [[int(cell) for cell in row] if isinstance(row, str) else list(row) for row in value]


def _hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _oracle(grid):
    height, width = len(grid), len(grid[0])
    cells = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    if not cells:
        raise ValueError("canonical max-of is undefined for an empty cell list")
    bottom = max(r for r, _, _ in cells)
    output = [[0 for _ in range(width)] for _ in range(height)]
    for row, col, color in cells:
        target_col = col - (bottom - row)
        if 0 <= target_col < width:
            output[row][target_col] = color
    return output


class Generator4326f5c2ded0Tests(unittest.TestCase):
    def test_all_twelve_canonical_occurrences_and_six_unique_pairs(self):
        rows = _rows()
        occurrences, unique = [], set()
        for row in rows:
            for pair in list(row["train"]) + list(row["test"]):
                source, expected = _grid(pair["input"]), _grid(pair["output"])
                self.assertEqual(MODULE.self_check(source), [])
                self.assertEqual(MODULE.rule_mirror(source), expected)
                self.assertEqual(_oracle(source), expected)
                occurrences.append(MODULE.canonical_profile_signature(source))
                unique.add(json.dumps(pair, sort_keys=True))
        self.assertEqual(len(occurrences), 12)
        self.assertEqual(len(unique), 6)
        self.assertEqual(set(occurrences), set(MODULE.PUBLIC_PROFILES))
        original = list(rows[0]["train"]) + list(rows[0]["test"])
        self.assertEqual(
            [MODULE.canonical_profile_signature(_grid(pair["input"])) for pair in original],
            list(MODULE.PUBLIC_PROFILES),
        )

    def test_public_profiles_retain_exact_geometry_under_color_variation(self):
        for profile in MODULE.PUBLIC_PROFILES:
            signatures, colors = set(), set()
            for seed in range(27):
                grid = MODULE.generate(seed, seed * 13 + 1, scene_profile=profile)
                self.assertEqual(MODULE.canonical_profile_signature(grid), profile)
                self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                self.assertEqual(MODULE.rule_mirror(grid), _oracle(grid))
                signatures.add(MODULE._semantic_signature(grid))
                colors.update(value for row in grid for value in row if value)
            self.assertEqual(signatures, {MODULE._PUBLIC_MASKS[profile]})
            self.assertEqual(colors, set(range(1, 10)))

    def test_every_forced_profile_is_exact_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.SCENE_PROFILES:
                for seed in range(12):
                    grid = MODULE.generate(seed + 700, seed * 19 + 3, difficulty=band, scene_profile=profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(
                        MODULE.self_check(grid, difficulty=band, meta={"overrides": {"scene_profile": profile}}),
                        [],
                    )
                    self.assertEqual(MODULE.rule_mirror(grid), _oracle(grid))

    def test_bottom_row_controls_row_dependent_shift(self):
        grid = [[0] * 12 for _ in range(10)]
        grid[1][8], grid[4][8], grid[7][8] = 2, 3, 4
        expected = [[0] * 12 for _ in range(10)]
        expected[1][2], expected[4][5], expected[7][8] = 2, 3, 4
        self.assertEqual(MODULE.rule_mirror(grid), expected)
        moved_bottom = copy.deepcopy(grid)
        moved_bottom[9][11] = 6
        result = MODULE.rule_mirror(moved_bottom)
        self.assertEqual((result[1][0], result[4][3], result[7][6], result[9][11]), (2, 3, 4, 6))

    def test_multicolor_components_and_clipping_semantics(self):
        multi = MODULE.generate(211, 307, scene_profile="multicolor_cells")
        disconnected = MODULE.generate(223, 311, scene_profile="disconnected_objects")
        clipped = MODULE.generate(227, 313, scene_profile="clipped_left")
        severe = MODULE.generate(229, 317, scene_profile="severe_clipping")
        self.assertGreater(len(MODULE._analysis(multi)["colors"]), 1)
        self.assertGreater(MODULE._analysis(disconnected)["component_count"], 1)
        self.assertGreater(len(MODULE._analysis(clipped)["clipped_cells"]), 0)
        self.assertGreaterEqual(len(MODULE._analysis(severe)["clipped_cells"]) * 5, len(MODULE._analysis(severe)["cells"]) * 2)
        for grid in (multi, disconnected, clipped, severe):
            self.assertEqual(MODULE.rule_mirror(grid), _oracle(grid))

    def test_generalized_structural_lessons_are_observable(self):
        expected = {
            "two_row_signal": lambda info: len(info["occupied_rows"]) == 2,
            "tall_signal": lambda info: info["occupied_rows"][-1] - info["occupied_rows"][0] >= 8,
            "sparse_points": lambda info: info["component_count"] == len(info["cells"]),
            "bottom_anchor_cell": lambda info: info["bottom_count"] == 1 and info["component_count"] > 1,
            "row_gap": lambda info: info["row_gap"],
        }
        for profile, predicate in expected.items():
            info = MODULE._analysis(MODULE.generate(313, 419, scene_profile=profile))
            self.assertEqual(info["scene_profile"], profile)
            self.assertTrue(predicate(info), profile)

    def test_default_census_and_diversity(self):
        for band in ("easy", "medium", "hard"):
            profiles, pairs = Counter(), set()
            for seed in range(800):
                grid = MODULE.generate(seed, seed * 11 + 1, difficulty=band)
                profiles[MODULE.observe_overrides(grid)["scene_profile"]] += 1
                pairs.add((tuple(map(tuple, grid)), tuple(map(tuple, MODULE.rule_mirror(grid)))))
            self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
            public = sum(profiles[profile] for profile in MODULE.PUBLIC_PROFILES)
            self.assertGreater(public, 220)
            self.assertLess(public, 390)
            self.assertGreater(len(pairs), 400)

    def test_self_check_rejects_invalid_identity_and_mismatched_scenes(self):
        base = MODULE.generate(401, 503, scene_profile="connected_outline")
        empty = [[0 for _ in row] for row in base]
        identity = [[0 for _ in row] for row in base]
        identity[len(identity) // 2][len(identity[0]) // 2] = 3
        ragged = copy.deepcopy(base)
        ragged[0].pop()
        invalid = copy.deepcopy(base)
        invalid[0][0] = 10
        boolean = copy.deepcopy(base)
        boolean[0][0] = True
        for mutation in (empty, identity, ragged, invalid, boolean):
            self.assertTrue(MODULE.self_check(mutation), mutation)
        self.assertTrue(MODULE.self_check(base, meta={"overrides": {"scene_profile": "row_gap"}}))

    def test_override_determinism_freshness_and_rng_isolation(self):
        for overrides in ({"scene_profile": "unknown"}, {"grid_h": 10}, {"texture": "outline"}, {"shape_w": 4}):
            with self.assertRaises(ValueError):
                MODULE.generate(1, 2, **overrides)
        random.seed(20260721)
        state = random.getstate()
        first = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))

    def test_both_rule_authorities_and_pin(self):
        rows = _rows()
        canonical = rows[0]["program_solution"]
        self.assertEqual(rows[1]["program_solution"], canonical)
        paths = (
            ROOT / "data/base/solutions/training/423a55dc__4326f5c2ded0.json",
            ROOT / "data/base/solutions/augmented/423a55dc__8e73f10130ae.json",
        )
        for path in paths:
            base = json.loads(path.read_text())
            self.assertEqual(base["racket_target"]["raw_code"], canonical)
            self.assertEqual(base["racket_target"]["target_code"], canonical)
        self.assertEqual(MODULE.RULE_HASH, _hash(canonical))
        self.assertEqual(MODULE.RULE_HASH, "884d94dde3d6")


if __name__ == "__main__":
    unittest.main()
