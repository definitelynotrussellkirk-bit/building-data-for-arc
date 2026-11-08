"""Focused semantic regressions for generator 4201f3b3ea1b."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path


TASK_ID = "4201f3b3ea1b"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]


def _row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row {TASK_ID}")


def _grid(value):
    return [[int(cell) for cell in row] if isinstance(row, str) else list(row) for row in value]


def _hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _oracle(grid):
    height, width = len(grid), len(grid[0])
    source = next((row, col) for row in range(height) for col in range(width) if grid[row][col] == 5)
    anchors = [(row, col) for row in range(height) for col in range(width) if grid[row][col] == 6]
    motif = [
        (row, col, grid[row][col])
        for row in range(height) for col in range(width)
        if grid[row][col] not in (0, 5, 6)
    ]
    output = copy.deepcopy(grid)
    for anchor_row, anchor_col in anchors:
        for row, col, color in motif:
            target_row = anchor_row + row - source[0]
            target_col = anchor_col + col - source[1]
            if 0 <= target_row < height and 0 <= target_col < width:
                output[target_row][target_col] = color
    return output


class Generator4201f3b3ea1bTests(unittest.TestCase):
    def test_all_five_canonical_pairs_and_profiles(self):
        row = _row()
        pairs = list(row["train"]) + [row["test"]]
        self.assertEqual(len(pairs), 5)
        profiles = []
        for pair in pairs:
            source, expected = _grid(pair["input"]), _grid(pair["output"])
            self.assertEqual(MODULE.self_check(source), [])
            self.assertEqual(MODULE.rule_mirror(source), expected)
            self.assertEqual(_oracle(source), expected)
            profiles.append(MODULE.canonical_profile_signature(source))
        self.assertEqual(profiles, list(MODULE.PUBLIC_PROFILES))

    def test_public_profiles_retain_complete_linked_geometry(self):
        for profile in MODULE.PUBLIC_PROFILES:
            seen = set()
            for seed in range(60):
                grid = MODULE.generate(seed, seed * 13 + 1, scene_profile=profile)
                self.assertEqual(MODULE.canonical_profile_signature(grid), profile)
                self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                self.assertEqual(MODULE.rule_mirror(grid), _oracle(grid))
                seen.add(tuple(map(tuple, grid)))
            self.assertGreater(len(seen), 20)

    def test_every_forced_profile_is_exact_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.SCENE_PROFILES:
                for seed in range(20):
                    grid = MODULE.generate(seed + 700, seed * 19 + 3, difficulty=band, scene_profile=profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MODULE.self_check(grid, meta={"overrides": {"scene_profile": profile}}), [])
                    self.assertEqual(MODULE.rule_mirror(grid), _oracle(grid))

    def test_anchor_and_motif_count_lessons(self):
        single_anchor = MODULE._analysis(MODULE.generate(101, 203, scene_profile="single_anchor"))
        four_anchors = MODULE._analysis(MODULE.generate(103, 207, scene_profile="four_anchors"))
        single_cell = MODULE._analysis(MODULE.generate(107, 211, scene_profile="single_cell_motif"))
        six_cells = MODULE._analysis(MODULE.generate(109, 213, scene_profile="six_cell_motif"))
        self.assertEqual(len(single_anchor["anchors"]), 1)
        self.assertEqual(len(four_anchors["anchors"]), 4)
        self.assertEqual(len(single_cell["motif"]), 1)
        self.assertEqual(len(six_cells["motif"]), 6)

    def test_complete_global_motif_and_first_source_lessons(self):
        mono = MODULE._analysis(MODULE.generate(211, 307, scene_profile="monochrome_motif"))
        wide = MODULE._analysis(MODULE.generate(223, 311, scene_profile="disconnected_wide_motif"))
        row_zero = MODULE._analysis(MODULE.generate(227, 313, scene_profile="row_zero_motif"))
        extra_source = MODULE._analysis(MODULE.generate(229, 317, scene_profile="extra_source_marker"))
        self.assertEqual(len(mono["motif_colors"]), 1)
        self.assertGreaterEqual(max(max(abs(dr), abs(dc)) for dr, dc in wide["relative_offsets"]), 4)
        self.assertTrue(any(row == 0 for row, _, _ in row_zero["motif"]))
        self.assertEqual(len(extra_source["sources"]), 2)
        self.assertEqual(extra_source["source"], min(extra_source["sources"]))

    def test_clipping_overlap_and_marker_overwrite_lessons(self):
        clipped_grid = MODULE.generate(313, 419, scene_profile="clipped_stamp")
        overlap_grid = MODULE.generate(317, 421, scene_profile="overlapping_stamps")
        overwrite_grid = MODULE.generate(319, 423, scene_profile="overwrite_markers")
        clipped, overlap, overwrite = map(MODULE._analysis, (clipped_grid, overlap_grid, overwrite_grid))
        self.assertGreater(clipped["clipped_cells"], 0)
        self.assertTrue(overlap["stamps_overlap"])
        self.assertTrue(overwrite["marker_overwrites"])
        for grid, info in ((clipped_grid, clipped), (overlap_grid, overlap), (overwrite_grid, overwrite)):
            self.assertEqual(info["output"], _oracle(grid))
        self.assertTrue(any(overwrite["output"][row][col] != overwrite_grid[row][col] for row, col in overwrite["marker_overwrites"]))

    def test_default_prior_and_diversity(self):
        for band in ("easy", "medium", "hard"):
            profiles, inputs, outputs = Counter(), set(), set()
            for seed in range(800):
                grid = MODULE.generate(seed, seed * 11 + 1, difficulty=band)
                profiles[MODULE.observe_overrides(grid)["scene_profile"]] += 1
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, MODULE.rule_mirror(grid))))
            self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
            strict = sum(profiles[profile] for profile in MODULE.PUBLIC_PROFILES)
            self.assertGreater(strict, 180)
            self.assertLess(strict, 320)
            self.assertGreater(len(inputs), 650)
            self.assertGreater(len(outputs), 650)

    def test_self_check_rejects_invalid_or_unlabeled_scenes(self):
        base = MODULE.generate(401, 503, scene_profile="six_cell_motif")
        empty = [[0 for _ in row] for row in base]
        no_anchor = copy.deepcopy(base)
        for row in no_anchor:
            for col, value in enumerate(row):
                if value == 6:
                    row[col] = 0
        too_many_sources = copy.deepcopy(base)
        too_many_sources[-1][0] = too_many_sources[-1][1] = 5
        ragged = copy.deepcopy(base)
        ragged[0].pop()
        invalid = copy.deepcopy(base)
        invalid[0][0] = 10
        boolean = copy.deepcopy(base)
        boolean[0][0] = True
        for mutation in (empty, no_anchor, too_many_sources, ragged, invalid, boolean):
            self.assertTrue(MODULE.self_check(mutation), mutation)
        self.assertTrue(MODULE.self_check(base, meta={"overrides": {"scene_profile": "single_anchor"}}))

    def test_override_determinism_freshness_and_rng_isolation(self):
        for overrides in ({"scene_profile": "unknown"}, {"grid_h": 8}, {"texture": "no_anchor"}, {"n_motif": 3}):
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

    def test_rule_authorities_and_pin(self):
        canonical = _row()["program_solution"]
        base = json.loads((ROOT / "data/base/solutions/banks/cc07013acae1/E64__4201f3b3ea1b.json").read_text())
        self.assertEqual(base["racket_target"]["raw_code"], canonical)
        self.assertEqual(base["racket_target"]["target_code"], canonical)
        self.assertEqual(MODULE.RULE_HASH, _hash(canonical))
        self.assertEqual(MODULE.RULE_HASH, "d92ee10172c2")


if __name__ == "__main__":
    unittest.main()
