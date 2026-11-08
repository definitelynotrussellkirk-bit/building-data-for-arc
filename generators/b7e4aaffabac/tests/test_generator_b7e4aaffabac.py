from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

from reviewer_support import canonical_path, find_root

TASK = "b7e4aaffabac"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = find_root(__file__)
BASES = (
    "solutions/training/d6ad076f__b7e4aaffabac.json",
    "solutions/augmented/d6ad076f__06076cde34a6.json",
)


def canonical_rows():
    return [
        json.loads(line)
        for line in canonical_path(ROOT).read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    ]


def decode(grid):
    return [[int(value) for value in row] if isinstance(row, str) else list(row) for row in grid]


def all_pairs(row):
    test = row["test"]
    return row["train"] + ([test] if isinstance(test, dict) else test)


class GeneratorTests(unittest.TestCase):
    def test_every_canonical_occurrence_and_public_profile(self):
        rows = canonical_rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual({row["source"] for row in rows}, {"training", "augmented"})
        self.assertEqual(sum(len(all_pairs(row)) for row in rows), 8)
        self.assertEqual(len({row["program_solution"] for row in rows}), 1)
        seen = set()
        for row in rows:
            for pair in all_pairs(row):
                grid, expected = decode(pair["input"]), decode(pair["output"])
                profile = MODULE.canonical_profile_signature(grid)
                self.assertIn(profile, MODULE.PUBLIC_PROFILES)
                self.assertEqual(MODULE.rule_mirror(grid), expected)
                self.assertEqual(MODULE.self_check(grid), [])
                self.assertEqual(MODULE.generate(1, 2, scene_profile=profile), grid)
                seen.add(profile)
        self.assertEqual(seen, set(MODULE.PUBLIC_PROFILES))

    def test_every_general_profile_every_band_is_observable(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.GENERAL_PROFILES:
                for seed in range(40):
                    grid = MODULE.generate(seed, seed * 17, difficulty=band, scene_profile=profile)
                    analysis = MODULE._analysis(grid)
                    self.assertEqual(analysis["errors"], [], (band, profile, seed, analysis))
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MODULE.rule_mirror(grid), analysis["output"])

    def test_bridge_is_exact_shrunken_overlap(self):
        for profile in MODULE.GENERAL_PROFILES:
            for seed in range(100):
                grid = MODULE.generate(seed, seed * 5, scene_profile=profile)
                analysis = MODULE._analysis(grid)
                first, second = analysis["ordered"]
                if analysis["orientation"] == "horizontal":
                    expected = {
                        (row, col)
                        for row in range(max(first["r1"], second["r1"]) + 1, min(first["r2"], second["r2"]))
                        for col in range(first["c2"] + 1, second["c1"])
                    }
                else:
                    expected = {
                        (row, col)
                        for row in range(first["r2"] + 1, second["r1"])
                        for col in range(max(first["c1"], second["c1"]) + 1, min(first["c2"], second["c2"]))
                    }
                changed = {
                    (row, col)
                    for row in range(len(grid))
                    for col in range(len(grid[0]))
                    if grid[row][col] != analysis["output"][row][col]
                }
                self.assertEqual(changed, expected)
                self.assertTrue(all(analysis["output"][row][col] == 8 for row, col in expected))
                self.assertEqual(analysis["bridge_area"], analysis["gap"] * analysis["band_span"])

    def test_profile_branches_have_promised_geometry(self):
        for seed in range(120):
            for orientation in ("horizontal", "vertical"):
                aligned = MODULE._analysis(MODULE.generate(seed, seed, scene_profile=f"{orientation}_aligned"))
                offset = MODULE._analysis(MODULE.generate(seed, seed, scene_profile=f"{orientation}_offset"))
                edge = MODULE._analysis(MODULE.generate(seed, seed, scene_profile=f"{orientation}_edge"))
                self.assertEqual(aligned["orientation"], orientation)
                self.assertTrue(aligned["aligned"])
                self.assertFalse(aligned["edge_touch"])
                self.assertEqual(offset["orientation"], orientation)
                self.assertFalse(offset["aligned"])
                self.assertFalse(offset["edge_touch"])
                self.assertEqual(edge["orientation"], orientation)
                self.assertTrue(edge["edge_touch"])
            minimal = MODULE._analysis(MODULE.generate(seed, seed, scene_profile="minimal_overlap"))
            wide = MODULE._analysis(MODULE.generate(seed, seed, scene_profile="wide_gap"))
            self.assertEqual(minimal["raw_overlap"], 3)
            self.assertEqual(minimal["band_span"], 1)
            self.assertGreaterEqual(wide["gap"], 4)

    def test_distribution_and_diversity(self):
        profiles = Counter()
        inputs, outputs, shapes = set(), set(), set()
        colors, orientations, gaps, overlaps, bridge_areas = set(), set(), set(), set(), set()
        for seed in range(2400):
            band = ("easy", "medium", "hard")[seed % 3]
            grid = MODULE.generate(seed, seed * 29, difficulty=band)
            analysis = MODULE._analysis(grid)
            self.assertEqual(analysis["errors"], [], (seed, analysis))
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, analysis["output"])))
            shapes.add((len(grid), len(grid[0])))
            colors.update(value for row in grid for value in row)
            orientations.add(analysis["orientation"])
            gaps.add(analysis["gap"])
            overlaps.add(analysis["raw_overlap"])
            bridge_areas.add(analysis["bridge_area"])
        self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
        self.assertGreater(len(inputs), 1450)
        self.assertGreater(len(outputs), 1450)
        self.assertGreater(len(shapes), 140)
        self.assertEqual(colors, set(range(10)) - {8})
        self.assertEqual(orientations, {"horizontal", "vertical"})
        self.assertTrue(set(range(1, 8)).issubset(gaps))
        self.assertTrue(set(range(3, 9)).issubset(overlaps))
        self.assertGreater(len(bridge_areas), 20)

    def test_malformed_and_uncalibrated_inputs_fail_closed(self):
        cases = [[], [[]], [[True]], [[10]], [[0] * 8 for _ in range(8)]]
        one = MODULE.generate(2, 3, scene_profile="horizontal_aligned")
        one = [[value if value == MODULE._analysis(one)["features"][0]["color"] else 0 for value in row] for row in one]
        cases.append(one)
        nonrect = MODULE.generate(3, 4, scene_profile="horizontal_aligned")
        feature = MODULE._analysis(nonrect)["features"][0]
        nonrect[feature["r1"]][feature["c1"]] = 0
        cases.append(nonrect)
        zero_bridge = MODULE.generate(4, 5, scene_profile="horizontal_aligned")
        analysis = MODULE._analysis(zero_bridge)
        for row in range(analysis["ordered"][1]["r1"] + 2, analysis["ordered"][1]["r2"] + 1):
            for col in range(analysis["ordered"][1]["c1"], analysis["ordered"][1]["c2"] + 1):
                zero_bridge[row][col] = 0
        cases.append(zero_bridge)
        for grid in cases:
            self.assertTrue(MODULE.self_check(grid), grid)

    def test_determinism_fresh_returns_and_unknown_overrides(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "x"}, {"orientation": "vertical"}):
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

    def test_rule_hash_and_bases_are_exactly_source_synchronized(self):
        source = canonical_rows()[0]["program_solution"]
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(MODULE.RULE_HASH, digest)
        for path in BASES:
            candidates = (ROOT / "data/base" / path, ROOT / "shared/data/base" / path)
            base_path = next((candidate for candidate in candidates if candidate.is_file()), None)
            self.assertIsNotNone(base_path, path)
            base = json.loads(base_path.read_text())
            normalized = " ".join(source.split())
            self.assertEqual(" ".join(base["racket_target"]["raw_code"].split()), normalized)
            self.assertEqual(" ".join(base["racket_target"]["target_code"].split()), normalized)
            self.assertEqual(base["primitive_metadata"]["source"], "mined_from_racket")


if __name__ == "__main__":
    unittest.main()
