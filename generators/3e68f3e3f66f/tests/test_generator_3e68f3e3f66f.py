"""Focused semantic regressions for generator 3e68f3e3f66f."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path


TASK_ID = "3e68f3e3f66f"
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
    legend = [value for value in grid[0] if value != 0]
    source = next((row, col) for row in range(height) for col in range(width) if grid[row][col] == 5)
    anchors = sorted((row, col) for row in range(height) for col in range(width) if grid[row][col] == 6)
    motif = [
        (row, col)
        for row in range(1, height)
        for col in range(width)
        if grid[row][col] not in (0, 5, 6)
    ]
    output = copy.deepcopy(grid)
    for index, (anchor_row, anchor_col) in enumerate(anchors):
        for row, col in motif:
            target_row = anchor_row + row - source[0]
            target_col = anchor_col + col - source[1]
            if 0 <= target_row < height and 0 <= target_col < width:
                output[target_row][target_col] = legend[index]
    return output


class Generator3e68f3e3f66fTests(unittest.TestCase):
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

    def test_count_legend_and_row_major_lessons(self):
        single = MODULE._analysis(MODULE.generate(101, 203, scene_profile="single_broadcast"))
        four = MODULE._analysis(MODULE.generate(103, 207, scene_profile="four_broadcasts"))
        row_major = MODULE._analysis(MODULE.generate(107, 211, scene_profile="row_major_counterexample"))
        self.assertEqual((len(single["legend"]), len(single["anchors"])), (1, 1))
        self.assertEqual((len(four["legend"]), len(four["anchors"])), (4, 4))
        self.assertEqual(len(row_major["legend"]), 2)
        self.assertGreater(row_major["anchors"][0][1], row_major["anchors"][1][1])
        output = row_major["output"]
        for index, anchor in enumerate(row_major["anchors"]):
            projected = MODULE._projected_cells(row_major["motif"], row_major["source"], anchor)
            changed_colors = {output[row][col] for row, col in projected}
            self.assertEqual(changed_colors, {row_major["legend"][index]})

    def test_motif_membership_and_legend_layout_lessons(self):
        noncontiguous = MODULE._analysis(MODULE.generate(211, 307, scene_profile="noncontiguous_legend"))
        multicolor = MODULE._analysis(MODULE.generate(223, 311, scene_profile="multicolor_motif"))
        disconnected = MODULE._analysis(MODULE.generate(227, 313, scene_profile="disconnected_motif"))
        legend_colored = MODULE._analysis(MODULE.generate(229, 317, scene_profile="legend_colored_motif"))
        extra_source = MODULE._analysis(MODULE.generate(233, 319, scene_profile="extra_source_marker"))
        sparse = MODULE._analysis(MODULE.generate(239, 323, scene_profile="sparse_wide_motif"))
        self.assertNotEqual(noncontiguous["legend_positions"], tuple(range(len(noncontiguous["legend"]))))
        self.assertGreater(len(multicolor["motif_colors"]), 1)
        self.assertEqual(len(disconnected["motif"]), 2)
        self.assertTrue(set(legend_colored["motif_colors"]) & set(legend_colored["legend"]))
        self.assertEqual(len(extra_source["sources"]), 2)
        self.assertEqual(extra_source["source"], min(extra_source["sources"]))
        self.assertGreaterEqual(max(max(abs(dr), abs(dc)) for dr, dc in sparse["relative_offsets"]), 4)

    def test_clipping_and_sequential_overlap_lessons(self):
        clipped = MODULE._analysis(MODULE.generate(313, 419, scene_profile="clipped_copy"))
        overlap = MODULE._analysis(MODULE.generate(317, 421, scene_profile="overlapping_copies"))
        self.assertGreater(clipped["clipped_cells"], 0)
        self.assertTrue(overlap["copies_overlap"])
        self.assertEqual(clipped["output"], _oracle(MODULE.generate(313, 419, scene_profile="clipped_copy")))
        self.assertEqual(overlap["output"], _oracle(MODULE.generate(317, 421, scene_profile="overlapping_copies")))
        common = set(MODULE._projected_cells(overlap["motif"], overlap["source"], overlap["anchors"][0]))
        common &= set(MODULE._projected_cells(overlap["motif"], overlap["source"], overlap["anchors"][1]))
        self.assertTrue(common)
        for row, col in common:
            self.assertEqual(overlap["output"][row][col], overlap["legend"][1])

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
        base = MODULE.generate(401, 503, scene_profile="multicolor_motif")
        empty = [[0 for _ in row] for row in base]
        unmatched = copy.deepcopy(base)
        next(row for row in range(len(unmatched)) if 6 in unmatched[row])
        for row in unmatched:
            if 6 in row:
                row[row.index(6)] = 0
                break
        too_many_sources = copy.deepcopy(base)
        too_many_sources[-1][0] = too_many_sources[-1][1] = too_many_sources[-1][2] = 5
        ragged = copy.deepcopy(base)
        ragged[0].pop()
        invalid = copy.deepcopy(base)
        invalid[0][0] = 10
        boolean = copy.deepcopy(base)
        boolean[0][0] = True
        for mutation in (empty, unmatched, too_many_sources, ragged, invalid, boolean):
            self.assertTrue(MODULE.self_check(mutation), mutation)
        self.assertTrue(MODULE.self_check(base, meta={"overrides": {"scene_profile": "single_broadcast"}}))

    def test_override_determinism_freshness_and_rng_isolation(self):
        for overrides in ({"scene_profile": "unknown"}, {"grid_h": 12}, {"n_legend": 3}):
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
        base = json.loads((ROOT / "data/base/solutions/banks/cc07013acae1/H64__3e68f3e3f66f.json").read_text())
        self.assertEqual(base["racket_target"]["raw_code"], canonical)
        self.assertEqual(base["racket_target"]["target_code"], canonical)
        self.assertEqual(MODULE.RULE_HASH, _hash(canonical))
        self.assertEqual(MODULE.RULE_HASH, "4f92f2063a9e")


if __name__ == "__main__":
    unittest.main()
