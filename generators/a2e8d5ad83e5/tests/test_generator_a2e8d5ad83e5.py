from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

TASK = "a2e8d5ad83e5"
MOD = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASES = {
    "training": "data/base/solutions/training/e9bb6954__a2e8d5ad83e5.json",
    "augmented": "data/base/solutions/augmented/e9bb6954__2ad069de7ab3.json",
}


def canonical_rows():
    return [
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    ]


def training_pairs():
    row = next(row for row in canonical_rows() if row["source"] == "training")
    return row["train"] + row["test"]


class GeneratorTests(unittest.TestCase):
    def test_all_canonical_occurrences_and_exact_public_profiles(self):
        self.assertEqual([(row["source"], len(row["train"]), len(row["test"])) for row in canonical_rows()], [("training", 4, 1), ("augmented", 5, 0)])
        for row in canonical_rows():
            for pair in row["train"] + row["test"]:
                self.assertEqual(MOD.rule_mirror(pair["input"]), pair["output"])
                self.assertEqual(MOD.self_check(pair["input"]), [])
        for profile, pair in zip(MOD.PUBLIC_PROFILES, training_pairs()):
            generated = MOD.generate(1, 2, scene_profile=profile)
            self.assertEqual(generated, pair["input"])
            self.assertEqual(MOD.canonical_profile_signature(generated), profile)
            self.assertIsNot(generated, MOD._PUBLIC_INPUTS[profile])

    def test_every_general_profile_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MOD.GENERAL_PROFILES:
                for seed in range(40):
                    grid = MOD.generate(seed, seed * 17, difficulty=band, scene_profile=profile)
                    analysis = MOD._analysis(grid)
                    self.assertEqual(analysis["errors"], [], (band, profile, seed))
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})
                    self.assertGreaterEqual(analysis["noise_cells"], 16)
                    self.assertGreaterEqual(len(analysis["palette"]), 8)

    def test_cross_and_distinct_color_cancellation_semantics(self):
        for profile in MOD.GENERAL_PROFILES:
            for seed in range(30):
                grid = MOD.generate(seed, seed * 23, scene_profile=profile)
                analysis = MOD._analysis(grid)
                output = analysis["output"]
                for row in range(len(grid)):
                    for col in range(len(grid[0])):
                        hits = {
                            anchor["color"]
                            for anchor in analysis["anchors"]
                            if anchor["center"][0] == row or anchor["center"][1] == col
                        }
                        expected = 0 if len(hits) > 1 else next(iter(hits)) if hits else grid[row][col]
                        self.assertEqual(output[row][col], expected)

    def test_same_color_hits_do_not_cancel(self):
        grid = MOD.generate(19, 31, scene_profile="same_color_pair")
        analysis = MOD._analysis(grid)
        color = analysis["anchor_colors"][0]
        self.assertEqual(len(set(analysis["anchor_colors"])), 1)
        for row, col in (
            (analysis["anchors"][0]["center"][0], analysis["anchors"][1]["center"][1]),
            (analysis["anchors"][1]["center"][0], analysis["anchors"][0]["center"][1]),
        ):
            self.assertEqual(analysis["output"][row][col], color)

    def test_aligned_distinct_centers_cancel_shared_axis(self):
        row_grid = MOD.generate(7, 11, scene_profile="same_row_centers")
        row_analysis = MOD._analysis(row_grid)
        shared_row = row_analysis["anchors"][0]["center"][0]
        self.assertTrue(all(value == 0 for value in row_analysis["output"][shared_row]))
        col_grid = MOD.generate(13, 17, scene_profile="same_col_centers")
        col_analysis = MOD._analysis(col_grid)
        shared_col = col_analysis["anchors"][0]["center"][1]
        self.assertTrue(all(row[shared_col] == 0 for row in col_analysis["output"]))

    def test_broad_source_accepts_filled_rectangle_but_calibration_rejects_it(self):
        grid = [[0] * 12 for _ in range(10)]
        for row in range(2, 4):
            for col in range(3, 6):
                grid[row][col] = 6
        output = MOD.rule_mirror(grid)
        self.assertTrue(all(output[2][col] == 6 for col in range(12)))
        self.assertTrue(all(output[row][4] == 6 for row in range(10)))
        self.assertTrue(MOD.self_check(grid))

    def test_distribution_and_branch_coverage(self):
        profiles = Counter()
        inputs, outputs, shapes, colors, counts, sizes = set(), set(), set(), set(), set(), set()
        for seed in range(3300):
            band = ("easy", "medium", "hard")[seed % 3]
            grid = MOD.generate(seed, seed * 29, difficulty=band)
            analysis = MOD._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, analysis["output"])))
            shapes.add((len(grid), len(grid[0])))
            colors.update(analysis["palette"])
            counts.add(analysis["anchor_count"])
            sizes.update(analysis["anchor_sizes"])
        self.assertEqual(set(profiles), set(MOD.SCENE_PROFILES))
        self.assertGreater(len(inputs), 2700)
        self.assertGreater(len(outputs), 2700)
        self.assertGreater(len(shapes), 120)
        self.assertEqual(colors, set(range(1, 10)))
        self.assertEqual(counts, {1, 2, 3, 4})
        self.assertTrue({(2, 2), (3, 3), (4, 4)}.issubset(sizes))

    def test_malformed_and_uncalibrated_inputs(self):
        cases = [[], [[]], [[True]], [[10]], [[0] * 8 for _ in range(8)]]
        ragged = MOD.generate(3, 5, scene_profile="two_squares")
        ragged[0].pop()
        cases.append(ragged)
        anchor_only = [[0] * 12 for _ in range(12)]
        for row in range(3, 6):
            for col in range(4, 7):
                anchor_only[row][col] = 2
        cases.append(anchor_only)
        rectangle = MOD.generate(37, 41, scene_profile="one_square")
        anchor = MOD._analysis(rectangle)["anchors"][0]
        r1, c1, r2, c2 = anchor["bbox"]
        extension = c2 + 1 if c2 + 1 < len(rectangle[0]) else c1 - 1
        for row in range(max(0, r1 - 1), min(len(rectangle), r2 + 2)):
            rectangle[row][extension] = 0
        for row in range(r1, r2 + 1):
            rectangle[row][extension] = anchor["color"]
        cases.append(rectangle)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)

    def test_override_errors_determinism_fresh_returns_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "noise"}, {"grid_h": 18}):
            with self.assertRaises(ValueError):
                MOD.generate(1, 2, **overrides)
        with self.assertRaises(ValueError):
            MOD.generate(1, 2, difficulty="extreme")
        random.seed(47)
        state = random.getstate()
        first = MOD.generate(17, 23, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MOD.generate(17, 23, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)

    def test_rule_hash_and_both_base_sources_are_synced(self):
        rows = canonical_rows()
        sources = {row["source"]: row["program_solution"] for row in rows}
        self.assertEqual(len(set(sources.values())), 1)
        source = next(iter(sources.values()))
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(MOD.RULE_HASH, digest)
        for source_name, relative in BASES.items():
            base = json.loads((ROOT / relative).read_text())
            self.assertEqual(base["racket_target"]["raw_code"], sources[source_name])
            self.assertEqual(base["racket_target"]["target_code"], sources[source_name])


if __name__ == "__main__":
    unittest.main()
