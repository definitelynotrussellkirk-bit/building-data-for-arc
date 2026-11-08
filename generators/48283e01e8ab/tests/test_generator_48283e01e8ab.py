"""Focused semantic regressions for generator 48283e01e8ab."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
import random
import unittest

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK_ID = "48283e01e8ab"
ROOT = find_root(__file__)
MODULE, _, _ = load_selected_generator(TASK_ID, root=ROOT)
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _rows():
    rows = []
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            rows.append(row)
    if len(rows) != 2:
        raise AssertionError(f"expected two canonical rows for {TASK_ID}, found {len(rows)}")
    return rows


def _hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _oracle(grid):
    height, width = len(grid), len(grid[0])
    output, seen = copy.deepcopy(grid), set()
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 6 or (row, col) in seen:
                continue
            stack, cells = [(row, col)], []
            seen.add((row, col))
            while stack:
                current = stack.pop()
                cells.append(current)
                for dr, dc in DIRS:
                    neighbor = current[0] + dr, current[1] + dc
                    if 0 <= neighbor[0] < height and 0 <= neighbor[1] < width and grid[neighbor[0]][neighbor[1]] == 6 and neighbor not in seen:
                        seen.add(neighbor)
                        stack.append(neighbor)
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            size = len(cells)
            if size == 6:
                color = 5
            elif size == 5:
                color = 3
            elif size == 4:
                color = 8
            elif size == 3 and (max(rows) == min(rows) or max(cols) == min(cols)):
                color = 2
            elif size == 3:
                color = 4
            elif size == 2:
                color = 9
            else:
                color = 6
            for r, c in cells:
                output[r][c] = color
    return output


class Generator48283e01e8abTests(unittest.TestCase):
    def test_all_six_canonical_occurrences_and_three_unique_pairs(self):
        occurrences, unique = [], set()
        for pair in canonical_pairs(TASK_ID, root=ROOT):
            source, expected = pair["input"], pair["output"]
            self.assertEqual(MODULE.self_check(source), [])
            self.assertEqual(MODULE.rule_mirror(source), expected)
            self.assertEqual(_oracle(source), expected)
            occurrences.append(MODULE.canonical_profile_signature(source))
            unique.add((tuple(map(tuple, source)), tuple(map(tuple, expected))))
        self.assertEqual(len(occurrences), 6)
        self.assertEqual(len(unique), 3)
        self.assertEqual(set(occurrences), set(MODULE.PUBLIC_PROFILES))

    def test_public_profiles_retain_every_component_and_gray_background(self):
        for profile in MODULE.PUBLIC_PROFILES:
            grid = MODULE.generate(101, 203, scene_profile=profile)
            expected = [[int(value) for value in row] for row in MODULE._PUBLIC_INPUTS[profile]]
            self.assertEqual(grid, expected)
            self.assertEqual(MODULE.canonical_profile_signature(grid), profile)
            self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
            self.assertEqual(MODULE.rule_mirror(grid), _oracle(grid))
            self.assertEqual(Counter(value for row in grid for value in row).most_common(1)[0][0], 7)

    def test_every_forced_profile_is_exact_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.SCENE_PROFILES:
                for seed in range(10):
                    grid = MODULE.generate(seed + 700, seed * 19 + 3, difficulty=band, scene_profile=profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(
                        MODULE.self_check(grid, difficulty=band, meta={"overrides": {"scene_profile": profile}}),
                        [],
                    )
                    self.assertEqual(MODULE.rule_mirror(grid), _oracle(grid))

    def test_all_size_and_shape_color_branches(self):
        grid = MODULE.generate(211, 307, scene_profile="all_classes_once")
        info = MODULE._analysis(grid)
        self.assertEqual(info["sizes"], (1, 2, 3, 3, 4, 5, 6, 7, 8))
        self.assertEqual(info["target_colors"], (2, 3, 4, 5, 6, 6, 6, 8, 9))
        self.assertEqual(len(info["foreign_cells"]), 5)
        self.assertEqual(MODULE.rule_mirror(grid), _oracle(grid))
        line = next(component for component in info["components"] if component["size"] == 3 and component["line3"])
        bend = next(component for component in info["components"] if component["size"] == 3 and not component["line3"])
        self.assertEqual((line["target_color"], bend["target_color"]), (2, 4))

    def test_repeated_and_unknown_size_lessons(self):
        lines = MODULE._analysis(MODULE.generate(223, 311, scene_profile="repeated_lines"))
        bends = MODULE._analysis(MODULE.generate(227, 313, scene_profile="repeated_bends"))
        unknown = MODULE._analysis(MODULE.generate(229, 317, scene_profile="unknown_sizes_mixed"))
        self.assertEqual(lines["target_colors"], (2, 2, 2, 2))
        self.assertEqual(bends["target_colors"], (4, 4, 4, 4))
        self.assertEqual(unknown["sizes"], (1, 2, 7, 8))
        self.assertEqual(unknown["target_colors"], (6, 6, 6, 9))
        grid = MODULE.generate(229, 317, scene_profile="unknown_sizes_mixed")
        output = MODULE.rule_mirror(grid)
        self.assertNotEqual(output, grid)
        for component in unknown["components"]:
            if component["size"] in (1, 7, 8):
                for row, col in component["cells"]:
                    self.assertEqual(output[row][col], 6)

    def test_noncanonical_shapes_edges_and_foreign_cells(self):
        six = MODULE._analysis(MODULE.generate(313, 419, scene_profile="size6_nonrect"))
        five = MODULE._analysis(MODULE.generate(317, 421, scene_profile="size5_nonplus"))
        four = MODULE._analysis(MODULE.generate(319, 423, scene_profile="size4_varied"))
        edge = MODULE._analysis(MODULE.generate(323, 427, scene_profile="edge_components"))
        foreign_grid = MODULE.generate(327, 431, scene_profile="foreign_preserved")
        foreign = MODULE._analysis(foreign_grid)
        self.assertEqual(six["target_colors"], (5, 5))
        self.assertEqual(five["target_colors"], (3, 3, 3))
        self.assertEqual(four["target_colors"], (8, 8, 8))
        self.assertGreaterEqual(sum(component["touches_edge"] for component in edge["components"]), 2)
        self.assertEqual(len(foreign["foreign_cells"]), 5)
        output = MODULE.rule_mirror(foreign_grid)
        for row, col, color in foreign["foreign_cells"]:
            self.assertEqual(output[row][col], color)

    def test_default_census_and_diversity(self):
        general_shapes = {"easy": (9, 9), "medium": (9, 10), "hard": (10, 10)}
        teaching_shapes = {"easy": (12, 12), "medium": (13, 13), "hard": (14, 14)}
        for band in ("easy", "medium", "hard"):
            profiles, pairs = Counter(), set()
            for seed in range(800):
                grid = MODULE.generate(seed, seed * 11 + 1, difficulty=band)
                profile = MODULE.observe_overrides(grid)["scene_profile"]
                profiles[profile] += 1
                pairs.add((tuple(map(tuple, grid)), tuple(map(tuple, MODULE.rule_mirror(grid)))))
                if profile == "all_classes_once":
                    self.assertEqual((len(grid), len(grid[0])), teaching_shapes[band])
                elif profile in MODULE.GENERAL_PROFILES:
                    self.assertEqual((len(grid), len(grid[0])), general_shapes[band])
            self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
            public = sum(profiles[profile] for profile in MODULE.PUBLIC_PROFILES)
            self.assertGreaterEqual(public, 160)
            self.assertLessEqual(public, 240)
            self.assertGreater(len(pairs), 550)

    def test_self_check_rejects_minimal_impostors_and_bad_scenes(self):
        base = MODULE.generate(401, 503, scene_profile="all_classes_once")
        all_background = [[7 for _ in row] for row in base]
        singleton = copy.deepcopy(all_background); singleton[2][2] = 6
        line = copy.deepcopy(all_background); line[2][2:5] = [6, 6, 6]
        block = copy.deepcopy(all_background); block[2][2] = block[2][3] = block[3][2] = block[3][3] = 6
        full = [[6 for _ in row] for row in base]
        ragged = copy.deepcopy(base); ragged[0].pop()
        invalid = copy.deepcopy(base); invalid[0][0] = 10
        boolean = copy.deepcopy(base); boolean[0][0] = True
        for mutation in (all_background, singleton, line, block, full, ragged, invalid, boolean):
            self.assertTrue(MODULE.self_check(mutation), mutation)
        self.assertTrue(MODULE.self_check(base, meta={"overrides": {"scene_profile": "size4_varied"}}))

    def test_override_determinism_freshness_and_rng_isolation(self):
        for overrides in ({"scene_profile": "unknown"}, {"grid_h": 9}, {"shape_set": "mixed"}, {"texture": "full_grid"}):
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
        data_root = canonical_path(ROOT).parent.parent
        paths = (
            data_root / "base/solutions/training/ad38a9d0__48283e01e8ab.json",
            data_root / "base/solutions/augmented/ad38a9d0__5254aece3d38.json",
        )
        for path in paths:
            base = json.loads(path.read_text())
            self.assertEqual(" ".join(base["racket_target"]["raw_code"].split()), " ".join(canonical.split()))
            self.assertEqual(base["racket_target"]["target_code"], canonical)
        self.assertEqual(MODULE.RULE_HASH, _hash(canonical))
        self.assertEqual(MODULE.RULE_HASH, "79a3d3708716")


if __name__ == "__main__":
    unittest.main()
