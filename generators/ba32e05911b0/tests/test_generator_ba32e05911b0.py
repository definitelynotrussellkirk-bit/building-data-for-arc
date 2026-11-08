from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

TASK = "ba32e05911b0"
from reviewer_support import canonical_path, find_root, load_selected_generator
ROOT = find_root(__file__)
MODULE, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)
DATA_ROOT = ROOT if (ROOT / "data/base").is_dir() else ROOT / "shared"
BASES = (
    "data/base/solutions/training/891232d6__ba32e05911b0.json",
    "data/base/solutions/augmented/891232d6__e76673e350b9.json",
)


def canonical_rows():
    return [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if json.loads(line).get("task_id") == TASK]


def pairs(row):
    test = row["test"]
    return row["train"] + ([test] if isinstance(test, dict) else test)


class GeneratorTests(unittest.TestCase):
    def test_all_ten_canonical_occurrences_and_five_public_profiles(self):
        rows = canonical_rows()
        self.assertEqual(len(rows), 2)
        self.assertEqual(sum(len(pairs(row)) for row in rows), 10)
        self.assertEqual(len({row["program_solution"] for row in rows}), 1)
        seen = set()
        for row in rows:
            for pair in pairs(row):
                grid, expected = pair["input"], pair["output"]
                profile = MODULE.canonical_profile_signature(grid)
                self.assertIn(profile, MODULE.PUBLIC_PROFILES)
                self.assertEqual(MODULE.rule_mirror(grid), expected)
                self.assertEqual(MODULE.self_check(grid), [])
                self.assertEqual(MODULE.generate(1, 2, scene_profile=profile), grid)
                seen.add(profile)
        self.assertEqual(seen, set(MODULE.PUBLIC_PROFILES))

    def test_every_general_profile_every_band_is_exactly_observable(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.GENERAL_PROFILES:
                for seed in range(45):
                    grid = MODULE.generate(seed, seed * 17, difficulty=band, scene_profile=profile)
                    analysis = MODULE._analysis(grid)
                    self.assertEqual(analysis["errors"], [], (band, profile, seed, analysis))
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MODULE.rule_mirror(grid), analysis["output"])

    def test_event_profiles_isolate_source_branches(self):
        for seed in range(120):
            analyses = {profile: MODULE._analysis(MODULE.generate(seed, seed, scene_profile=profile)) for profile in MODULE.GENERAL_PROFILES}
            self.assertEqual(analyses["clear_climb"]["rolls"], [])
            self.assertIn("top_exit", analyses["clear_climb"]["event_kinds"])
            self.assertEqual(len(analyses["short_roll"]["rolls"]), 1)
            self.assertLessEqual(analyses["short_roll"]["rolls"][0]["length"], 2)
            self.assertEqual(len(analyses["long_roll"]["rolls"]), 1)
            self.assertGreaterEqual(analyses["long_roll"]["rolls"][0]["length"], 4)
            self.assertGreaterEqual(len(analyses["multi_roll"]["rolls"]), 2)
            self.assertIn("blocked_stop", analyses["blocked_stop"]["event_kinds"])
            self.assertIn("edge_stop", analyses["edge_stop"]["event_kinds"])
            self.assertEqual(analyses["multiple_markers"]["marker_count"], 2)
            dense = analyses["dense_distractors"]
            self.assertGreaterEqual(dense["orange_count"] / (len(dense["output"]) * len(dense["output"][0])), 0.16)

    def test_roll_pattern_and_original_grid_collision_semantics(self):
        for profile in ("short_roll", "long_roll", "multi_roll", "dense_distractors"):
            for seed in range(80):
                grid = MODULE.generate(seed, seed * 3, scene_profile=profile)
                analysis = MODULE._analysis(grid)
                for event in analysis["rolls"]:
                    row, col, end, nxt = event["row"], event["col"], event["run_end"], event["next_col"]
                    output = analysis["output"]
                    self.assertEqual(output[row][col], 8)
                    self.assertEqual(output[row + 1][col], 4)
                    self.assertTrue(all(output[row + 1][cc] == 2 for cc in range(col + 1, end + 1)))
                    self.assertEqual(output[row + 1][nxt], 3)
                    self.assertFalse(any(grid[row + 1][cc] == 7 for cc in range(col + 1, nxt + 1)))

    def test_distribution_matches_canonical_scale_and_is_diverse(self):
        profiles = Counter()
        inputs, outputs, shapes = set(), set(), set()
        markers, components, events, colors = set(), set(), set(), set()
        for seed in range(2600):
            band = ("easy", "medium", "hard")[seed % 3]
            grid = MODULE.generate(seed, seed * 29, difficulty=band)
            analysis = MODULE._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, analysis["output"])))
            shapes.add((len(grid), len(grid[0])))
            markers.add(analysis["marker_count"])
            components.add(analysis["orange_components"])
            events.update(analysis["event_kinds"])
            colors.update(value for row in analysis["output"] for value in row)
        self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
        self.assertGreater(len(inputs), 1450)
        self.assertGreater(len(outputs), 1450)
        self.assertGreater(len(shapes), 150)
        self.assertEqual(markers, {1, 2, 3})
        self.assertGreater(max(components), 45)
        self.assertEqual(events, {"top_exit", "roll", "blocked_stop", "edge_stop"})
        self.assertEqual(colors, {0, 2, 3, 4, 6, 7, 8})

    def test_malformed_inputs_fail_closed(self):
        cases = [[], [[]], [[True]], [[1]], [[0] * 8 for _ in range(8)], [[7] * 8 for _ in range(8)]]
        ragged = MODULE.generate(2, 3, scene_profile="clear_climb")
        ragged[0].pop()
        cases.append(ragged)
        too_many = MODULE.generate(3, 4, scene_profile="multiple_markers")
        too_many[-1][0] = too_many[-1][-1] = 6
        cases.append(too_many)
        for grid in cases:
            self.assertTrue(MODULE.self_check(grid), grid)

    def test_determinism_fresh_returns_global_rng_and_unknown_axes(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "warm"}, {"n_markers": 2}):
            with self.assertRaises(ValueError):
                MODULE.generate(1, 2, **overrides)
        with self.assertRaises(ValueError):
            MODULE.generate(1, 2, difficulty="extreme")
        random.seed(19)
        state = random.getstate()
        first = MODULE.generate(4, 5, difficulty="hard")
        self.assertEqual(state, random.getstate())
        second = MODULE.generate(4, 5, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])

    def test_rule_hash_and_archival_bases_match_whitespace_normalized_authority(self):
        source = canonical_rows()[0]["program_solution"]
        self.assertEqual(MODULE.RULE_HASH, hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12])
        for path in BASES:
            base = json.loads((DATA_ROOT / path).read_text())
            # Archival files are minified; the selected authority is pretty-printed.
            # Preserve every token while comparing the library rule-hash contract.
            self.assertEqual(" ".join(base["racket_target"]["raw_code"].split()), " ".join(source.split()))
            self.assertEqual(" ".join(base["racket_target"]["target_code"].split()), " ".join(source.split()))


if __name__ == "__main__":
    unittest.main()
