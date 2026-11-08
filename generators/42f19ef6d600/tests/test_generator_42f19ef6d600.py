"""Focused semantic regressions for generator 42f19ef6d600."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib
import json
import random
import unittest
from reviewer_support import canonical_path, find_root


TASK_ID = "42f19ef6d600"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = find_root(__file__)
DATA_ROOT = canonical_path(ROOT).parent.parent
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _row():
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row {TASK_ID}")


def _grid(value):
    return [[int(cell) for cell in row] if isinstance(row, str) else list(row) for row in value]


def _normalized(source):
    return " ".join(source.split())


def _hash(source):
    return hashlib.sha256(_normalized(source).encode()).hexdigest()[:12]


def _oracle(grid):
    height, width = len(grid), len(grid[0])
    seen, objects = set(), []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 7 or (row, col) in seen:
                continue
            stack, cells = [(row, col)], []
            seen.add((row, col))
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            objects.append(cells)
    output = copy.deepcopy(grid)
    for cells in objects:
        r1, c1 = min(r for r, _ in cells), min(c for _, c in cells)
        r2, c2 = max(r for r, _ in cells), max(c for _, c in cells)
        obj_height, obj_width = r2 - r1 + 1, c2 - c1 + 1
        solid = len(cells) == obj_height * obj_width
        if obj_height != obj_width or obj_height < 2:
            continue
        if solid:
            marks = (
                [(r1 - 1, c) for c in range(c1, c2 + 1)]
                + [(r2 + 1, c) for c in range(c1, c2 + 1)]
                + [(r, c1 - 1) for r in range(r1, r2 + 1)]
                + [(r, c2 + 1) for r in range(r1, r2 + 1)]
            )
        else:
            marks = [(r1 - 1, c1), (r1 - 1, c2), (r2 + 1, c1), (r2 + 1, c2), (r1, c1 - 1), (r2, c1 - 1), (r1, c2 + 1), (r2, c2 + 1)]
        for r, c in marks:
            if 0 <= r < height and 0 <= c < width and grid[r][c] == 7:
                output[r][c] = 2
    return output


class Generator42f19ef6d600Tests(unittest.TestCase):
    def test_all_four_canonical_pairs_and_profiles(self):
        row = _row()
        pairs = list(row["train"]) + list(row["test"])
        self.assertEqual(len(pairs), 4)
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
            self.assertGreater(len(seen), 6)

    def test_every_forced_profile_is_exact_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.SCENE_PROFILES:
                for seed in range(20):
                    grid = MODULE.generate(seed + 700, seed * 19 + 3, difficulty=band, scene_profile=profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MODULE.self_check(grid, meta={"overrides": {"scene_profile": profile}}), [])
                    self.assertEqual(MODULE.rule_mirror(grid), _oracle(grid))

    def test_solid_hollow_and_irregular_branches(self):
        solid = MODULE._analysis(MODULE.generate(101, 203, scene_profile="solid_square"))
        hollow = MODULE._analysis(MODULE.generate(103, 207, scene_profile="hollow_square"))
        irregular = MODULE._analysis(MODULE.generate(107, 211, scene_profile="irregular_square"))
        self.assertTrue(solid["squares"][0]["solid"])
        self.assertEqual(len(solid["eligible_marks"]), 16)
        self.assertFalse(hollow["squares"][0]["solid"])
        self.assertEqual(len(hollow["eligible_marks"]), 8)
        self.assertFalse(irregular["squares"][0]["solid"])
        self.assertEqual(irregular["squares"][0]["size"], 7)
        self.assertEqual(len(irregular["eligible_marks"]), 8)

    def test_count_size_and_mixed_lessons(self):
        mixed = MODULE._analysis(MODULE.generate(211, 307, scene_profile="mixed_solid_hollow"))
        three = MODULE._analysis(MODULE.generate(223, 311, scene_profile="three_squares"))
        four = MODULE._analysis(MODULE.generate(227, 313, scene_profile="four_squares"))
        size_two = MODULE._analysis(MODULE.generate(229, 317, scene_profile="size_two_solid"))
        size_six = MODULE._analysis(MODULE.generate(233, 319, scene_profile="size_six_hollow"))
        self.assertEqual({obj["solid"] for obj in mixed["squares"]}, {True, False})
        self.assertGreater(len({obj["color"] for obj in mixed["squares"]}), 1)
        self.assertEqual((len(three["squares"]), len(four["squares"])), (3, 4))
        self.assertEqual((size_two["squares"][0]["height"], size_six["squares"][0]["height"]), (2, 6))

    def test_filter_clipping_nesting_and_blocking_lessons(self):
        edge = MODULE._analysis(MODULE.generate(313, 419, scene_profile="edge_clipped"))
        decoys = MODULE._analysis(MODULE.generate(317, 421, scene_profile="nonsquare_decoys"))
        nested = MODULE._analysis(MODULE.generate(319, 423, scene_profile="same_color_nested"))
        blocked = MODULE._analysis(MODULE.generate(323, 427, scene_profile="blocked_marks"))
        self.assertTrue(edge["clipped_marks"])
        self.assertTrue(decoys["ignored"])
        self.assertTrue(nested["nested"])
        self.assertTrue(blocked["blocked_marks"])
        for info in (edge, decoys, nested, blocked):
            self.assertEqual(info["output"], _oracle(MODULE.generate({"edge_clipped":313,"nonsquare_decoys":317,"same_color_nested":319,"blocked_marks":323}[info["scene_profile"]], {"edge_clipped":419,"nonsquare_decoys":421,"same_color_nested":423,"blocked_marks":427}[info["scene_profile"]], scene_profile=info["scene_profile"])))

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
            self.assertGreater(strict, 140)
            self.assertLess(strict, 280)
            self.assertGreater(len(inputs), 500)
            self.assertGreater(len(outputs), 500)

    def test_self_check_rejects_invalid_or_unlabeled_scenes(self):
        base = MODULE.generate(401, 503, scene_profile="mixed_solid_hollow")
        empty = [[7 for _ in row] for row in base]
        singleton = [[7 for _ in row] for row in base]
        singleton[len(singleton) // 2][len(singleton[0]) // 2] = 3
        clipped_two = [[7 for _ in row] for row in base]
        for row in range(2):
            for col in range(2):
                clipped_two[row][col] = 3
        ragged = copy.deepcopy(base); ragged[0].pop()
        invalid = copy.deepcopy(base); invalid[0][0] = 10
        reserved = copy.deepcopy(base); reserved[0][0] = 2
        boolean = copy.deepcopy(base); boolean[0][0] = True
        for mutation in (empty, singleton, clipped_two, ragged, invalid, reserved, boolean):
            self.assertTrue(MODULE.self_check(mutation), mutation)
        self.assertTrue(MODULE.self_check(base, meta={"overrides": {"scene_profile": "solid_square"}}))

    def test_override_determinism_freshness_and_rng_isolation(self):
        for overrides in ({"scene_profile": "unknown"}, {"grid_h": 10}, {"texture": "full_grid"}, {"n_squares": 2}):
            with self.assertRaises(ValueError):
                MODULE.generate(1, 2, **overrides)
        random.seed(20260721); state = random.getstate()
        first = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))

    def test_rule_authorities_and_pin(self):
        canonical = _row()["program_solution"]
        base = json.loads((DATA_ROOT / "base/solutions/training/14b8e18c__42f19ef6d600.json").read_text())
        self.assertEqual(_normalized(base["racket_target"]["raw_code"]), _normalized(canonical))
        self.assertEqual(_normalized(base["racket_target"]["target_code"]), _normalized(canonical))
        self.assertEqual(MODULE.RULE_HASH, _hash(canonical))
        self.assertEqual(MODULE.RULE_HASH, "07ef8e3cc031")


if __name__ == "__main__":
    unittest.main()
