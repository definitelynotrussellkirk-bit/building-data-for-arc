"""Focused semantic regressions for generator 44690b1b635f."""
from __future__ import annotations

from collections import Counter, deque
import copy
import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path


TASK_ID = "44690b1b635f"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


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
    positions = {}
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value not in (0, 8):
                positions.setdefault(value, []).append((row, col))
    singletons = [color for color, cells in positions.items() if len(cells) == 1]
    if len(positions) != 2 or len(singletons) != 1:
        raise ValueError("oracle requires two marker colors and one singleton color")
    center_color = singletons[0]
    arm_color = next(color for color in positions if color != center_color)
    start = positions[center_color][0]
    distances, queue = {start: 0}, deque([start])
    while queue:
        row, col = queue.popleft()
        for dr, dc in DIRS:
            nr, nc = row + dr, col + dc
            if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] != 8 and (nr, nc) not in distances:
                distances[(nr, nc)] = distances[(row, col)] + 1
                queue.append((nr, nc))
    output = copy.deepcopy(grid)
    for (row, col), distance in distances.items():
        if grid[row][col] == 0:
            output[row][col] = center_color if distance % 2 == 0 else arm_color
    return output


class Generator44690b1b635fTests(unittest.TestCase):
    def test_all_six_canonical_occurrences_and_three_unique_pairs(self):
        occurrences, unique = [], set()
        for row in _rows():
            for pair in list(row["train"]) + list(row["test"]):
                source, expected = _grid(pair["input"]), _grid(pair["output"])
                self.assertEqual(MODULE.self_check(source), [])
                self.assertEqual(MODULE.rule_mirror(source), expected)
                self.assertEqual(_oracle(source), expected)
                occurrences.append(MODULE.canonical_profile_signature(source))
                unique.add(json.dumps(pair, sort_keys=True))
        self.assertEqual(len(occurrences), 6)
        self.assertEqual(len(unique), 3)
        self.assertEqual(set(occurrences), set(MODULE.PUBLIC_PROFILES))

    def test_public_profiles_retain_exact_linked_wall_geometry(self):
        legal_colors = set(range(1, 10)) - {8}
        for profile in MODULE.PUBLIC_PROFILES:
            signatures, center_colors, arm_colors = set(), set(), set()
            for seed in range(112):
                grid = MODULE.generate(seed, seed * 13 + 1, scene_profile=profile)
                info = MODULE._analysis(grid)
                self.assertEqual(MODULE.canonical_profile_signature(grid), profile)
                self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                self.assertEqual(MODULE.rule_mirror(grid), _oracle(grid))
                signatures.add(MODULE._semantic_signature(grid, info["center_color"], info["arm_color"]))
                center_colors.add(info["center_color"])
                arm_colors.add(info["arm_color"])
            self.assertEqual(signatures, {MODULE._PUBLIC_MASKS[profile]})
            self.assertEqual(center_colors, legal_colors)
            self.assertEqual(arm_colors, legal_colors)

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

    def test_bfs_distance_parity_and_preservation(self):
        grid = MODULE.generate(101, 203, scene_profile="split_gate")
        info, output = MODULE._analysis(grid), MODULE.rule_mirror(grid)
        for (row, col), distance in info["distances"].items():
            if grid[row][col] == 0:
                expected = info["center_color"] if distance % 2 == 0 else info["arm_color"]
                self.assertEqual(output[row][col], expected)
        for row in range(len(grid)):
            for col in range(len(grid[0])):
                if grid[row][col] != 0:
                    self.assertEqual(output[row][col], grid[row][col])

    def test_walls_block_and_unreachable_zeros_remain_zero(self):
        for profile in ("disconnected_regions", "sealed_chamber"):
            grid = MODULE.generate(211, 307, difficulty="hard", scene_profile=profile)
            info, output = MODULE._analysis(grid), MODULE.rule_mirror(grid)
            self.assertGreater(len(info["unreachable_zeros"]), 0)
            for row, col in info["unreachable_zeros"]:
                self.assertEqual(output[row][col], 0)
            for row in range(len(grid)):
                for col in range(len(grid[0])):
                    if grid[row][col] == 8:
                        self.assertEqual(output[row][col], 8)

    def test_generalized_profiles_cover_distinct_semantic_decisions(self):
        info = {
            profile: MODULE._analysis(MODULE.generate(313, 419, difficulty="medium", scene_profile=profile))
            for profile in MODULE.GENERAL_PROFILES
        }
        self.assertEqual(info["open_field"]["wall_count"], 0)
        self.assertEqual(info["offcenter_seed"]["center"], (2, 3))
        self.assertEqual(info["edge_seed"]["center"][0], 0)
        self.assertEqual(len(info["many_arm_markers"]["arm_positions"]), 8)
        self.assertEqual(info["parity_conflict"]["arm_even_parity"], 3)
        self.assertEqual(info["split_gate"]["wall_count"], info["split_gate"]["height"] - 1)
        self.assertGreater(len(info["disconnected_regions"]["unreachable_zeros"]), 0)
        self.assertGreater(len(info["sealed_chamber"]["unreachable_zeros"]), 0)
        self.assertGreater(info["labyrinth"]["wall_count"], info["split_gate"]["wall_count"])
        self.assertGreater(info["narrow_corridor"]["wall_count"], len(info["narrow_corridor"]["reachable_zeros"]))
        self.assertGreater(info["wall_islands"]["wall_count"], 0)
        h, w = info["boundary_walls"]["height"], info["boundary_walls"]["width"]
        self.assertEqual(info["boundary_walls"]["wall_count"], 2 * h + 2 * w - 4)
        self.assertGreater(info["multiple_chambers"]["wall_count"], info["split_gate"]["wall_count"])

    def test_default_census_and_diversity(self):
        shapes = {"easy": (10, 12), "medium": (13, 16), "hard": (16, 24)}
        for band in ("easy", "medium", "hard"):
            profiles, pairs = Counter(), set()
            for seed in range(800):
                grid = MODULE.generate(seed, seed * 11 + 1, difficulty=band)
                profile = MODULE.observe_overrides(grid)["scene_profile"]
                profiles[profile] += 1
                pairs.add((tuple(map(tuple, grid)), tuple(map(tuple, MODULE.rule_mirror(grid)))))
                if profile in MODULE.GENERAL_PROFILES:
                    self.assertEqual((len(grid), len(grid[0])), shapes[band])
            self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
            public = sum(profiles[profile] for profile in MODULE.PUBLIC_PROFILES)
            self.assertGreater(public, 100)
            self.assertLess(public, 220)
            self.assertGreater(len(pairs), 450)

    def test_self_check_rejects_invalid_and_out_of_grammar_scenes(self):
        base = MODULE.generate(401, 503, scene_profile="open_field")
        empty = [[0 for _ in row] for row in base]
        one_color = copy.deepcopy(base)
        info = MODULE._analysis(one_color)
        for row, col in info["arm_positions"]:
            one_color[row][col] = info["center_color"]
        two_singletons = [[0 for _ in row] for row in base]
        two_singletons[2][2], two_singletons[3][3] = 2, 3
        ragged = copy.deepcopy(base); ragged[0].pop()
        invalid = copy.deepcopy(base); invalid[0][0] = 10
        boolean = copy.deepcopy(base); boolean[0][0] = True
        altered = copy.deepcopy(base); altered[0][0] = 8
        for mutation in (empty, one_color, two_singletons, ragged, invalid, boolean, altered):
            self.assertTrue(MODULE.self_check(mutation), mutation)
        self.assertTrue(MODULE.self_check(base, meta={"overrides": {"scene_profile": "labyrinth"}}))

    def test_override_determinism_freshness_and_rng_isolation(self):
        for overrides in ({"scene_profile": "unknown"}, {"grid_h": 10}, {"wall_mode": "split"}, {"texture": "no_seed"}):
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
            ROOT / "data/base/solutions/training/b782dc8a__44690b1b635f.json",
            ROOT / "data/base/solutions/augmented/b782dc8a__e3d5f9556c09.json",
        )
        for path in paths:
            base = json.loads(path.read_text())
            self.assertEqual(base["racket_target"]["raw_code"], canonical)
            self.assertEqual(base["racket_target"]["target_code"], canonical)
        self.assertEqual(MODULE.RULE_HASH, _hash(canonical))
        self.assertEqual(MODULE.RULE_HASH, "72a0e00e932b")


if __name__ == "__main__":
    unittest.main()
