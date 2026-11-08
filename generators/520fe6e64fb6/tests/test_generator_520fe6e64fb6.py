"""Focused semantic regressions for generator 520fe6e64fb6."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
import random
import unittest
from pathlib import Path
from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "520fe6e64fb6"
ROOT = find_root(__file__)
MODULE, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _rows():
    rows = []
    for line in canonical_path(ROOT).read_text().splitlines():
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
    nines = [(r, c) for r in range(height) for c in range(width) if grid[r][c] == 9]
    sevens = [(r, c) for r in range(height) for c in range(width) if grid[r][c] == 7]
    r9a, c9a = min(r for r, _ in nines), min(c for _, c in nines)
    r9b, c9b = max(r for r, _ in nines), max(c for _, c in nines)
    r7a, c7a = min(r for r, _ in sevens), min(c for _, c in sevens)
    r7b, c7b = max(r for r, _ in sevens), max(c for _, c in sevens)
    output = copy.deepcopy(grid)
    for row, col in nines:
        output[row][col] = 7
    for row, col in sevens:
        output[row][col] = 6
    if c9a == c7a:
        for row in range(1 + min(r9b, r7b), max(r9a, r7a)):
            if any(grid[row][col] == 0 for col in range(width)):
                for col in range(c9a, c9b + 1):
                    if grid[row][col] == 6:
                        output[row][col] = 2
    else:
        for col in range(1 + min(c9b, c7b), max(c9a, c7a)):
            if any(grid[row][col] == 0 for row in range(height)):
                for row in range(r9a, r9b + 1):
                    if grid[row][col] == 6:
                        output[row][col] = 2
    return output


class Generator520fe6e64fb6Tests(unittest.TestCase):
    def test_all_eight_canonical_occurrences_and_four_unique_pairs(self):
        occurrences, unique = [], set()
        for row in _rows():
            for pair in list(row["train"]) + list(row["test"]):
                source, expected = _grid(pair["input"]), _grid(pair["output"])
                self.assertEqual(MODULE.self_check(source), [])
                self.assertEqual(MODULE.rule_mirror(source), expected)
                self.assertEqual(_oracle(source), expected)
                occurrences.append(MODULE.canonical_profile_signature(source))
                unique.add(json.dumps(pair, sort_keys=True))
        self.assertEqual(len(occurrences), 8)
        self.assertEqual(len(unique), 4)
        self.assertEqual(set(occurrences), set(MODULE.PUBLIC_PROFILES))

    def test_public_profiles_retain_complete_linked_geometry(self):
        for profile in MODULE.PUBLIC_PROFILES:
            grid = MODULE.generate(101, 203, scene_profile=profile)
            expected = [[int(value) for value in row] for row in MODULE._PUBLIC_INPUTS[profile]]
            self.assertEqual(grid, expected)
            self.assertEqual(MODULE.canonical_profile_signature(grid), profile)
            self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
            self.assertEqual(MODULE.rule_mirror(grid), _oracle(grid))

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

    def test_target_transmutation_and_zero_preservation(self):
        for profile in MODULE.SCENE_PROFILES:
            grid = MODULE.generate(211, 307, scene_profile=profile)
            output = MODULE.rule_mirror(grid)
            for row in range(len(grid)):
                for col in range(len(grid[0])):
                    if grid[row][col] == 9:
                        self.assertEqual(output[row][col], 7)
                    elif grid[row][col] == 7:
                        self.assertEqual(output[row][col], 6)
                    elif grid[row][col] == 0:
                        self.assertEqual(output[row][col], 0)

    def test_vertical_and_horizontal_global_trigger_semantics(self):
        vertical = MODULE.generate(223, 311, scene_profile="outside_row_triggers")
        horizontal = MODULE.generate(227, 313, scene_profile="outside_col_triggers")
        for grid, orientation in ((vertical, "vertical"), (horizontal, "horizontal")):
            info = MODULE._analysis(grid)
            self.assertEqual(info["orientation"], orientation)
            self.assertTrue(info["outside_only_triggers"])
            self.assertGreater(info["trigger_count"], 0)
            self.assertGreater(len(info["connector_cells"]), 0)
            self.assertEqual(MODULE.rule_mirror(grid), _oracle(grid))

    def test_all_trigger_unequal_irregular_and_multiple_branches(self):
        complete = [
            MODULE._analysis(MODULE.generate(seed, seed + 88, scene_profile="all_between_triggered"))
            for seed in range(20)
        ]
        unequal = MODULE._analysis(MODULE.generate(239, 323, scene_profile="unequal_blocks"))
        irregular = MODULE._analysis(MODULE.generate(241, 327, scene_profile="irregular_markers"))
        multiple = MODULE._analysis(MODULE.generate(251, 331, scene_profile="multiple_components"))
        fallback = MODULE._analysis(MODULE.generate(257, 337, scene_profile="off_alignment_fallback"))
        boundary = MODULE._analysis(MODULE.generate(263, 341, scene_profile="boundary_blocks"))
        self.assertEqual({info["orientation"] for info in complete}, {"vertical", "horizontal"})
        self.assertTrue(all(info["trigger_count"] == info["between_count"] for info in complete))
        self.assertNotEqual(unequal["nine_shape"], unequal["seven_shape"])
        self.assertFalse(irregular["nines_rect"])
        self.assertGreater(multiple["nine_components"], 1)
        self.assertEqual(fallback["orientation"], "horizontal")
        self.assertNotEqual(fallback["c9a"], fallback["c7a"])
        self.assertTrue(boundary["touches_boundary"])

    def test_equal_minimum_column_alone_selects_vertical_branch(self):
        grid = MODULE.generate(269, 347, scene_profile="multiple_components")
        info = MODULE._analysis(grid)
        self.assertEqual(info["c9a"], info["c7a"])
        self.assertEqual(info["orientation"], "vertical")
        fallback = MODULE.generate(271, 349, scene_profile="off_alignment_fallback")
        fallback_info = MODULE._analysis(fallback)
        self.assertNotEqual(fallback_info["c9a"], fallback_info["c7a"])
        self.assertEqual(fallback_info["orientation"], "horizontal")

    def test_default_census_and_diversity(self):
        general_shapes = {"easy": (8, 8), "medium": (16, 16), "hard": (26, 26)}
        for band in ("easy", "medium", "hard"):
            profiles, pairs = Counter(), set()
            for seed in range(800):
                grid = MODULE.generate(seed, seed * 11 + 1, difficulty=band)
                profile = MODULE.observe_overrides(grid)["scene_profile"]
                profiles[profile] += 1
                pairs.add((tuple(map(tuple, grid)), tuple(map(tuple, MODULE.rule_mirror(grid)))))
                if profile in MODULE.GENERAL_PROFILES:
                    self.assertEqual((len(grid), len(grid[0])), general_shapes[band])
            self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
            public = sum(profiles[profile] for profile in MODULE.PUBLIC_PROFILES)
            self.assertGreater(public, 140)
            self.assertLess(public, 260)
            self.assertGreater(len(pairs), 400)

    def test_self_check_rejects_minimal_and_malformed_impostors(self):
        base = MODULE.generate(401, 503, scene_profile="vertical_nines_top")
        empty = [[6 for _ in row] for row in base]
        only_nine = copy.deepcopy(empty); only_nine[1][1] = 9
        no_trigger = copy.deepcopy(empty); no_trigger[1][2] = 9; no_trigger[-2][2] = 7
        ragged = copy.deepcopy(base); ragged[0].pop()
        invalid = copy.deepcopy(base); invalid[0][0] = 10
        boolean = copy.deepcopy(base); boolean[0][0] = True
        altered = copy.deepcopy(base); altered[0][0] = 0
        for mutation in (empty, only_nine, no_trigger, ragged, invalid, boolean):
            self.assertTrue(MODULE.self_check(mutation), mutation)
        self.assertEqual(MODULE.self_check(altered), [])
        self.assertEqual(MODULE.rule_mirror(altered)[0][0], 0)
        self.assertTrue(MODULE.self_check(base, meta={"overrides": {"scene_profile": "horizontal_nines_left"}}))

    def test_override_determinism_freshness_and_rng_isolation(self):
        for overrides in ({"scene_profile": "unknown"}, {"grid_h": 8}, {"orientation": "vertical"}, {"texture": "no_blocks"}):
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
        base_root = ROOT / "shared/data/base/solutions"
        if not base_root.is_dir():
            base_root = ROOT / "data/base/solutions"
        paths = (
            base_root / "training/fc10701f__520fe6e64fb6.json",
            base_root / "augmented/fc10701f__b1e2b0d3c0f8.json",
        )
        for path in paths:
            base = json.loads(path.read_text())
            # Archived source keeps its original formatting; only selected code is synchronized.
            self.assertEqual(" ".join(base["racket_target"]["raw_code"].split()),
                             " ".join(canonical.split()))
            self.assertEqual(base["racket_target"]["target_code"], canonical)
        self.assertEqual(MODULE.RULE_HASH, _hash(canonical))
        self.assertEqual(MODULE.RULE_HASH, "82e4ce2077ce")


if __name__ == "__main__":
    unittest.main()
