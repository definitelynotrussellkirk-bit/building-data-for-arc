"""Focused semantic regressions for generator 66e63986855b."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import unittest

from arcpuzzles import Catalog
from reviewer_support import canonical_path, find_root
from solvers.grounded_rules import GROUNDED_RULES


ROOT = find_root(__file__)
TASK_ID = "66e63986855b"
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
if not SOURCE.exists():
    SOURCE = ROOT / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location("rowfront_legacy_regressions", SOURCE)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
BASE_PATH = (
    ROOT
    / "shared/data/base/solutions/training/bf32578f__66e63986855b.json"
)
if not BASE_PATH.exists():
    BASE_PATH = ROOT / "data/base/solutions/training/bf32578f__66e63986855b.json"


def canonical_row():
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def normalized_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def independent_rule(grid):
    height, width = len(grid), len(grid[0])
    cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    ]
    color = grid[cells[0][0]][cells[0][1]]
    first_row = min(row for row, _col in cells)
    last_row = max(row for row, _col in cells)
    maximum_col = max(col for _row, col in cells)
    output = [[0 for _col in range(width)] for _row in range(height)]
    for row in range(height):
        row_cells = [col for cell_row, col in cells if cell_row == row]
        if not row_cells or row in (first_row, last_row):
            continue
        frontier = max(row_cells)
        for col in range(frontier + 1, 2 * maximum_col - frontier + 1):
            if 0 <= col < width:
                output[row][col] = color
    return output


class Generator66e63986855bTests(unittest.TestCase):
    def test_all_canonical_pairs_profiles_placements_and_rule(self):
        row = canonical_row()
        pairs = row["train"] + row["test"]
        expected = (
            ("connected_c", "top_left"),
            ("sparse_symmetric", "floating"),
            ("sparse_symmetric", "left_margin"),
            ("thick_symmetric", "left_margin"),
        )
        self.assertEqual(len(pairs), len(expected))
        for pair, (profile, placement) in zip(pairs, expected):
            source = copy.deepcopy(pair["input"])
            snapshot = copy.deepcopy(source)
            observed = MODULE.observe_overrides(source)
            self.assertEqual(MODULE.self_check(source), [])
            self.assertEqual(observed["profile"], profile)
            self.assertEqual(observed["placement"], placement)
            self.assertEqual(MODULE.canonical_profile_signature(source), profile)
            self.assertEqual(independent_rule(source), pair["output"])
            self.assertEqual(MODULE.rule_mirror(source), pair["output"])
            self.assertEqual(source, snapshot)

    def test_every_profile_placement_and_dimension_boundary_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.PROFILES:
                for placement in MODULE.PLACEMENTS:
                    for height, width in ((6, 7), (14, 18)):
                        overrides = {
                            "grid_h": height,
                            "grid_w": width,
                            "color": 9,
                            "profile": profile,
                            "placement": placement,
                        }
                        grid = MODULE.generate(
                            317,
                            911,
                            difficulty=band,
                            **overrides,
                        )
                        self.assertEqual(
                            MODULE.observe_overrides(grid), overrides
                        )
                        self.assertEqual(
                            MODULE.self_check(
                                grid,
                                difficulty=band,
                                meta={"overrides": overrides},
                            ),
                            [],
                        )
                        self.assertEqual(
                            MODULE.rule_mirror(grid),
                            independent_rule(grid),
                        )

    def test_default_census_covers_linked_axes_and_is_diverse(self):
        for band_index, band in enumerate(("easy", "medium", "hard")):
            profiles = Counter()
            placements = Counter()
            linked = Counter()
            inputs = set()
            outputs = set()
            for offset in range(250):
                seed = 10_000 * band_index + offset
                grid = MODULE.generate(
                    seed,
                    seed * 29 + 7,
                    difficulty=band,
                )
                observed = MODULE.observe_overrides(grid)
                profiles[observed["profile"]] += 1
                placements[observed["placement"]] += 1
                linked[(observed["profile"], observed["placement"])] += 1
                inputs.add(json.dumps(grid, separators=(",", ":")))
                outputs.add(
                    json.dumps(
                        independent_rule(grid),
                        separators=(",", ":"),
                    )
                )
                self.assertEqual(MODULE.self_check(grid), [])
            self.assertEqual(set(profiles), set(MODULE.PROFILES))
            self.assertEqual(set(placements), set(MODULE.PLACEMENTS))
            self.assertGreaterEqual(len(linked), 14)
            self.assertGreaterEqual(len(inputs), 235)
            self.assertGreaterEqual(len(outputs), 225)

    def test_mirror_fit_and_visible_branch_are_construction_invariants(self):
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for offset in range(400):
                seed = 50_000 + 10_000 * band_index + offset
                grid = MODULE.generate(
                    seed,
                    seed * 17 + 3,
                    difficulty=band,
                )
                analysis = MODULE._analysis(grid)
                self.assertEqual(analysis["errors"], [])
                self.assertTrue(
                    all(end < analysis["grid_w"] for end in analysis["mirror_ends"])
                )
                self.assertGreaterEqual(analysis["mirror_depth"], 2)
                self.assertNotEqual(MODULE.rule_mirror(grid), grid)

    def test_semantic_impostors_are_rejected(self):
        valid = MODULE.generate(
            701,
            809,
            profile="connected_c",
            placement="top_left",
            grid_h=10,
            grid_w=18,
            color=4,
        )
        info = MODULE._analysis(valid)
        first = info["first_row"]
        last = info["last_row"]
        maximum = info["maximum_col"]

        mutations = []

        row_gap = copy.deepcopy(valid)
        gap_row = first + 2
        row_gap[gap_row] = [0] * len(row_gap[gap_row])
        mutations.append(row_gap)

        second_color = copy.deepcopy(valid)
        second_color[first][info["minimum_col"]] = 7
        mutations.append(second_color)

        row_hole = copy.deepcopy(valid)
        row_hole[first][info["minimum_col"] + 1] = 0
        mutations.append(row_hole)

        hidden_branch = copy.deepcopy(valid)
        interior = first + 1
        for col in range(info["minimum_col"], maximum + 1):
            hidden_branch[interior][col] = 4
        mutations.append(hidden_branch)

        short_endpoint = copy.deepcopy(valid)
        short_endpoint[first][maximum] = 0
        mutations.append(short_endpoint)

        sparse = MODULE.generate(
            17,
            23,
            profile="sparse_symmetric",
            placement="top_left",
            grid_h=6,
            grid_w=7,
            color=3,
        )
        overflow = copy.deepcopy(sparse)
        sparse_info = MODULE._analysis(sparse)
        for endpoint_row in (
            sparse_info["first_row"],
            sparse_info["last_row"],
        ):
            for col in range(len(overflow[0])):
                overflow[endpoint_row][col] = 0
            overflow[endpoint_row][-1] = 3
        mutations.append(overflow)

        for mutation in mutations:
            self.assertTrue(MODULE.self_check(mutation), mutation)
            self.assertEqual(MODULE.observe_overrides(mutation), {})

    def test_negative_recombination_keeps_oracle_broader_than_curriculum(self):
        # Four occupied rows are outside the calibrated >=5-row curriculum,
        # but remain a lawful input to the broad canonical row-front rule.
        recombined = [
            [0, 0, 3, 0, 0, 0, 0],
            [0, 3, 0, 0, 0, 0, 0],
            [3, 0, 0, 0, 0, 0, 0],
            [0, 0, 3, 0, 0, 0, 0],
        ]
        expected = independent_rule(recombined)
        self.assertTrue(MODULE.self_check(recombined))
        self.assertEqual(MODULE.rule_mirror(recombined), expected)
        self.assertNotEqual(recombined, expected)

    def test_determinism_freshness_global_rng_and_unknown_inputs(self):
        for kwargs in (
            {"profile": "unknown"},
            {"placement": "center"},
            {"texture": "warm"},
            {"grid_h": 5},
            {"grid_w": 19},
            {"color": 0},
        ):
            with self.assertRaises(ValueError):
                MODULE.generate(1, 2, **kwargs)
        with self.assertRaises(ValueError):
            MODULE.generate(1, 2, difficulty="extreme")

        random.seed(20260723)
        state = random.getstate()
        first = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(
            all(left is not right for left, right in zip(first, second))
        )
        pristine = copy.deepcopy(second)
        first[0][0] = (first[0][0] + 1) % 10
        self.assertEqual(
            MODULE.generate(97, 103, difficulty="hard"),
            pristine,
        )

    def test_source_sync_and_rule_pin(self):
        row = canonical_row()
        source = row["program_solution"]
        base = json.loads(BASE_PATH.read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)
        self.assertEqual(
            normalized_hash(GROUNDED_RULES[TASK_ID]),
            normalized_hash(source),
        )
        self.assertEqual(MODULE.RULE_HASH, normalized_hash(source))
        self.assertEqual(MODULE.RULE_HASH, "e9ecd02cbe2e")

    def test_racket_parity_on_canonical_generated_and_recombined_inputs(self):
        source = canonical_row()["program_solution"]
        grids = [
            pair["input"]
            for pair in canonical_row()["train"] + canonical_row()["test"]
        ]
        grids.extend(
            MODULE.generate(
                80_000 + index,
                index * 31 + 5,
                difficulty=("easy", "medium", "hard")[index % 3],
                profile=MODULE.PROFILES[index % len(MODULE.PROFILES)],
                placement=MODULE.PLACEMENTS[index % len(MODULE.PLACEMENTS)],
            )
            for index in range(12)
        )
        grids.append(
            [
                [0, 0, 3, 0, 0, 0, 0],
                [0, 3, 0, 0, 0, 0, 0],
                [3, 0, 0, 0, 0, 0, 0],
                [0, 0, 3, 0, 0, 0, 0],
            ]
        )
        snapshots = copy.deepcopy(grids)
        receipt = Catalog(ROOT).apply(TASK_ID, grids)
        self.assertEqual(receipt["executed_rule_hash"], MODULE.RULE_HASH)
        self.assertEqual(len(receipt["results"]), len(grids))
        for grid, snapshot, result in zip(grids, snapshots, receipt["results"]):
            expected = independent_rule(grid)
            self.assertEqual(result["output"], expected)
            self.assertEqual(MODULE.rule_mirror(grid), expected)
            self.assertEqual(grid, snapshot)


if __name__ == "__main__":
    unittest.main()
