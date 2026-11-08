from __future__ import annotations

import hashlib
import json
import random
import unittest
from collections import Counter

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "d377a54f20c6"
ROOT = find_root(__file__)
MOD, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK, root=ROOT)
DATA_ROOT = canonical_path(ROOT).parent.parent
BASE = "base/solutions/training/8cb8642d__d377a54f20c6.json"
AUGMENTED_BASE = "base/solutions/augmented/8cb8642d__357ed0ee7f7c.json"
ARCHIVAL_RAW_SHA256 = "108312a76f4854479a12fa0f9e70bde1846ca1ab07395272f60e2da2d695670e"


def canonical_rows():
    return [row for line in canonical_path(ROOT).read_text().splitlines()
            if line.strip() and (row := json.loads(line)).get("task_id") == TASK]


def unique_pairs():
    out = {}
    for pair in canonical_pairs(TASK, root=ROOT):
        out.setdefault(tuple(map(tuple, pair["input"])), pair)
    return list(out.values())


class GeneratorTests(unittest.TestCase):
    def test_every_canonical_occurrence_and_public_profile_exact(self):
        pairs = canonical_pairs(TASK, root=ROOT)
        unique = unique_pairs()
        self.assertEqual(len(canonical_rows()), 2)
        self.assertEqual(len(pairs), 8)
        self.assertEqual(len(unique), 4)
        for pair in pairs:
            self.assertEqual(MOD.rule_mirror(pair["input"]), pair["output"])
            self.assertEqual(MOD.self_check(pair["input"]), [])
        for profile, pair in zip(MOD.PUBLIC_PROFILES, unique):
            grid = MOD.generate(11, 29, scene_profile=profile)
            self.assertEqual(grid, pair["input"])
            self.assertEqual(MOD.rule_mirror(grid), pair["output"])
            self.assertEqual(MOD.canonical_profile_signature(grid), profile)
            self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})

    def test_every_general_profile_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MOD.GENERAL_PROFILES:
                for seed in range(50):
                    grid = MOD.generate(seed, seed * 19, difficulty=band, scene_profile=profile)
                    analysis = MOD._analysis(grid)
                    self.assertEqual(analysis["errors"], [], (band, profile, seed, analysis))
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MOD.rule_mirror(grid), analysis["output"])
                    self.assertGreaterEqual(analysis["changed"] / (len(grid) * len(grid[0])), 0.01)

    def test_profiles_isolate_geometry_palette_and_marker_rivals(self):
        for seed in range(80):
            analyses = {profile: MOD._analysis(MOD.generate(seed, seed * 7, scene_profile=profile)) for profile in MOD.GENERAL_PROFILES}
            odd = analyses["square_odd_side"]["objects"][0]
            even = analyses["square_even_side"]["objects"][0]
            self.assertEqual(odd["height"], odd["width"])
            self.assertEqual(odd["height"] % 2, 1)
            self.assertEqual(even["height"], even["width"])
            self.assertEqual(even["height"] % 2, 0)
            self.assertGreater(analyses["landscape_center_row"]["objects"][0]["width"], analyses["landscape_center_row"]["objects"][0]["height"])
            self.assertGreater(analyses["portrait_center_column"]["objects"][0]["height"], analyses["portrait_center_column"]["objects"][0]["width"])
            self.assertGreaterEqual(analyses["extreme_landscape"]["objects"][0]["width"] - analyses["extreme_landscape"]["objects"][0]["height"], 5)
            self.assertGreaterEqual(analyses["extreme_portrait"]["objects"][0]["height"] - analyses["extreme_portrait"]["objects"][0]["width"], 5)
            self.assertEqual(len(analyses["multiple_objects"]["objects"]), 2)
            shared = analyses["shared_marker_color"]["objects"]
            self.assertEqual(len({obj["marker"] for obj in shared}), 1)
            cross = analyses["cross_role_palette"]["objects"]
            self.assertTrue({obj["main"] for obj in cross}.intersection(obj["marker"] for obj in cross))
            border = analyses["border_marker_erased"]["objects"][0]
            r1, c1, r2, c2 = border["bbox"]
            self.assertTrue(any(r in (r1, r2) or c in (c1, c2) for r, c in border["marker_cells"]))
            self.assertGreater(len(analyses["multiple_marker_pixels"]["objects"][0]["marker_cells"]), 1)
            self.assertEqual(len(analyses["mixed_parities"]["objects"]), 3)

    def test_exact_stroke_and_marker_position_irrelevance(self):
        first = [[0] * 15 for _ in range(11)]
        second = [[0] * 15 for _ in range(11)]
        for grid in (first, second):
            for row in range(2, 9):
                for col in range(2, 13):
                    grid[row][col] = 2
        first[3][3] = 5
        second[7][11] = 5
        out_a = MOD.rule_mirror(first)
        out_b = MOD.rule_mirror(second)
        self.assertEqual(out_a, out_b)
        for row in range(2, 9):
            for col in range(2, 13):
                rr, cc = row - 2, col - 2
                expected = 2 if rr in (0, 6) or cc in (0, 10) else (5 if MOD._stroke(rr - 1, cc - 1, 5, 9) else 0)
                self.assertEqual(out_a[row][col], expected)
        self.assertTrue(all(out_a[row][col] == 0 for row in range(11) for col in range(15) if not (2 <= row <= 8 and 2 <= col <= 12)))

    def test_distribution(self):
        profiles = Counter()
        inputs, outputs, shapes, object_counts, dimensions = set(), set(), set(), set(), set()
        colors = set()
        for seed in range(3000):
            grid = MOD.generate(seed, seed * 31, difficulty=("easy", "medium", "hard")[seed % 3])
            analysis = MOD._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, analysis["output"])))
            shapes.add((len(grid), len(grid[0])))
            object_counts.add(len(analysis["objects"]))
            dimensions.update((obj["height"], obj["width"]) for obj in analysis["objects"])
            colors.update(value for row in grid for value in row)
        self.assertEqual(set(profiles), set(MOD.SCENE_PROFILES))
        self.assertGreater(len(inputs), 2500)
        self.assertGreater(len(outputs), 2500)
        self.assertGreater(len(shapes), 100)
        self.assertGreater(len(dimensions), 35)
        self.assertEqual(object_counts, {1, 2, 3})
        self.assertEqual(colors, set(range(10)))

    def test_malformed_and_impostors_fail_closed(self):
        cases = [[], [[]], [[True]], [[10]], [[1], [1, 2]], [[0] * 8 for _ in range(8)], [[2] * 8 for _ in range(8)]]
        one_color = [[0] * 9 for _ in range(9)]
        for row in range(1, 8):
            for col in range(1, 8):
                one_color[row][col] = 3
        cases.append(one_color)
        hole = [row[:] for row in one_color]
        hole[4][4] = 5
        hole[3][3] = 0
        cases.append(hole)
        tiny = [[0] * 7 for _ in range(7)]
        for row in range(2, 5):
            for col in range(2, 5):
                tiny[row][col] = 2
        tiny[3][3] = 6
        cases.append(tiny)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)
        with self.assertRaises(ValueError):
            MOD.rule_mirror([])

    def test_determinism_unknowns_freshness_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "warm"}, {"rect_height": 8}):
            with self.assertRaises(ValueError):
                MOD.generate(1, 2, **overrides)
        with self.assertRaises(ValueError):
            MOD.generate(1, 2, difficulty="extreme")
        random.seed(47)
        state = random.getstate()
        first = MOD.generate(17, 23, difficulty="hard")
        self.assertEqual(state, random.getstate())
        second = MOD.generate(17, 23, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])

    def test_rule_hash_and_base_sync(self):
        sources = {row["program_solution"] for row in canonical_rows()}
        self.assertEqual(len(sources), 1)
        source = sources.pop()
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(MOD.RULE_HASH, digest)
        for path in (BASE, AUGMENTED_BASE):
            base = json.loads((DATA_ROOT / path).read_text())
            # raw_code preserves the imported archival bytes; only target_code
            # is synchronized to the canonical program's exact source text.
            raw_source = base["racket_target"]["raw_code"]
            self.assertEqual(hashlib.sha256(raw_source.encode()).hexdigest(), ARCHIVAL_RAW_SHA256)
            self.assertEqual(base["racket_target"]["target_code"], source)


if __name__ == "__main__":
    unittest.main()
