from __future__ import annotations

import hashlib
import json
import random
import unittest
from collections import Counter

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "bdb419bbf286"
ROOT = find_root(__file__)
MODULE, _, _ = load_selected_generator(TASK, root=ROOT)
BASE_RELATIVE = "data/base/solutions/banks/e00836ab832d/H132__bdb419bbf286.json"


def row():
    path = canonical_path(ROOT)
    return next(
        json.loads(line)
        for line in path.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    )


def pairs():
    return canonical_pairs(TASK, root=ROOT, labeled_only=True)


def base_path():
    candidates = (ROOT / BASE_RELATIVE, ROOT / "shared" / BASE_RELATIVE)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(BASE_RELATIVE)


def last_marker_output(grid):
    analysis = MODULE._analysis(grid)
    shape = analysis["shape"]
    a = analysis["marker_3"][-1]
    b = analysis["marker_4"][-1]
    dr, dc = b[0] - a[0], b[1] - a[1]
    return MODULE._paint_output(
        len(grid),
        len(grid[0]),
        MODULE._translated(shape, dr, dc),
    )


class GeneratorTests(unittest.TestCase):
    def test_all_public_pairs(self):
        self.assertEqual(len(pairs()), 5)
        for profile, pair in zip(MODULE.PUBLIC_PROFILES, pairs()):
            self.assertEqual(MODULE.rule_mirror(pair["input"]), pair["output"])
            self.assertEqual(MODULE.self_check(pair["input"]), [])
            self.assertEqual(MODULE.generate(1, 2, scene_profile=profile), pair["input"])
            self.assertEqual(MODULE.canonical_profile_signature(pair["input"]), profile)

    def test_every_profile_band_observable(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.GENERAL_PROFILES:
                for seed in range(45):
                    grid = MODULE.generate(seed, seed * 17, difficulty=band, scene_profile=profile)
                    analysis = MODULE._analysis(grid)
                    self.assertEqual(analysis["errors"], [], (band, profile, seed, analysis))
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MODULE.rule_mirror(grid), analysis["output"])

    def test_profiles_isolate_semantics(self):
        for seed in range(100):
            for profile, signs in (
                ("down_right", (1, 1)),
                ("up_right", (-1, 1)),
                ("up_left", (-1, -1)),
                ("down_left", (1, -1)),
            ):
                analysis = MODULE._analysis(MODULE.generate(seed, seed, scene_profile=profile))
                self.assertEqual(
                    (1 if analysis["dr"] > 0 else -1, 1 if analysis["dc"] > 0 else -1),
                    signs,
                )
                self.assertFalse(analysis["copies_overlap"])
            axis = MODULE._analysis(MODULE.generate(seed, seed, scene_profile="axis_aligned"))
            self.assertTrue(axis["dr"] == 0 or axis["dc"] == 0)
            overlap = MODULE._analysis(MODULE.generate(seed, seed, scene_profile="overlapping_copies"))
            self.assertTrue(overlap["copies_overlap"])
            clipped = MODULE._analysis(MODULE.generate(seed, seed, scene_profile="clipped_copies"))
            self.assertTrue(
                any(
                    not (0 <= row < len(clipped["output"]) and 0 <= col < len(clipped["output"][0]))
                    for cells in clipped["copies"]
                    for row, col in cells
                )
            )
            marker_grid = MODULE.generate(seed, seed, scene_profile="marker_decoys")
            marker = MODULE._analysis(marker_grid)
            self.assertTrue(len(marker["marker_3"]) > 1 or len(marker["marker_4"]) > 1)
            self.assertEqual(marker["first_4"][0] - marker["first_3"][0], marker["dr"])
            last_vector = (
                marker["marker_4"][-1][0] - marker["marker_3"][-1][0],
                marker["marker_4"][-1][1] - marker["marker_3"][-1][1],
            )
            self.assertNotEqual(last_vector, (marker["dr"], marker["dc"]))
            self.assertNotEqual(last_marker_output(marker_grid), marker["output"])
            irrelevant = MODULE.generate(seed, seed, scene_profile="irrelevant_colors")
            self.assertTrue(any(value not in (0, 2, 3, 4) for line in irrelevant for value in line))
            large = MODULE._analysis(MODULE.generate(seed, seed, scene_profile="large_shape"))
            self.assertGreaterEqual(large["shape_size"], 7)

    def test_output_is_exact_union_and_clears_input(self):
        for profile in MODULE.GENERAL_PROFILES:
            for seed in range(80):
                grid = MODULE.generate(seed, seed * 3, scene_profile=profile)
                analysis = MODULE._analysis(grid)
                expected = {
                    (row + k * analysis["dr"], col + k * analysis["dc"])
                    for row, col in analysis["shape"]
                    for k in range(3)
                    if 0 <= row + k * analysis["dr"] < len(grid)
                    and 0 <= col + k * analysis["dc"] < len(grid[0])
                }
                actual = {
                    (row, col)
                    for row, line in enumerate(analysis["output"])
                    for col, value in enumerate(line)
                    if value == 8
                }
                self.assertEqual(actual, expected)
                self.assertTrue(all(value in (0, 8) for line in analysis["output"] for value in line))

    def test_distribution(self):
        profiles = Counter()
        inputs, outputs, shapes, vectors, sizes = set(), set(), set(), set(), set()
        marker_counts, colors, overlap = set(), set(), set()
        for seed in range(2500):
            grid = MODULE.generate(seed, seed * 29, difficulty=("easy", "medium", "hard")[seed % 3])
            analysis = MODULE._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, analysis["output"])))
            shapes.add((len(grid), len(grid[0])))
            vectors.add((analysis["dr"], analysis["dc"]))
            sizes.add(analysis["shape_size"])
            marker_counts.add((len(analysis["marker_3"]), len(analysis["marker_4"])))
            colors.update(value for line in grid for value in line)
            overlap.add(analysis["copies_overlap"])
        self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
        self.assertGreater(len(inputs), 1450)
        self.assertGreater(len(outputs), 1450)
        self.assertGreater(len(shapes), 180)
        self.assertGreater(len(vectors), 25)
        self.assertTrue(set(range(3, 11)).issubset(sizes))
        self.assertIn((2, 3), marker_counts)
        self.assertEqual(colors, set(range(10)) - {8})
        self.assertEqual(overlap, {False, True})

    def test_malformed_fail_closed(self):
        cases = [[], [[]], [[True]], [[8]], [[0] * 8 for _ in range(8)]]
        missing = MODULE.generate(2, 3, scene_profile="down_right")
        analysis = MODULE._analysis(missing)
        for marker_row, marker_col in analysis["marker_4"]:
            missing[marker_row][marker_col] = 0
        cases.append(missing)
        for grid in cases:
            self.assertTrue(MODULE.self_check(grid), grid)

    def test_determinism_and_unknowns(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "warm"}, {"marker_offset_r": 1}):
            with self.assertRaises(ValueError):
                MODULE.generate(1, 2, **overrides)
        with self.assertRaises(ValueError):
            MODULE.generate(1, 2, difficulty="extreme")
        random.seed(9)
        state = random.getstate()
        first = MODULE.generate(4, 5, difficulty="hard")
        self.assertEqual(state, random.getstate())
        second = MODULE.generate(4, 5, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])

    def test_source_sync(self):
        source = row()["program_solution"]
        self.assertEqual(
            MODULE.RULE_HASH,
            hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12],
        )
        base = json.loads(base_path().read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)


if __name__ == "__main__":
    unittest.main()


def test_every_generalized_scene_teaches_first_marker_selection():
    for profile in MODULE.GENERAL_PROFILES:
        for seed in range(32):
            grid = MODULE.generate(seed, seed * 31, scene_profile=profile)
            analysis = MODULE._analysis(grid)
            assert len(analysis["marker_3"]) >= 2, (profile, seed)
            assert len(analysis["marker_4"]) >= 2, (profile, seed)
            last_vector = (
                analysis["marker_4"][-1][0] - analysis["marker_3"][-1][0],
                analysis["marker_4"][-1][1] - analysis["marker_3"][-1][1],
            )
            assert last_vector != (analysis["dr"], analysis["dc"]), (profile, seed)
            assert last_marker_output(grid) != analysis["output"], (profile, seed)
