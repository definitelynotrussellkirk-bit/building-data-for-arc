from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

from reviewer_support import canonical_path, find_root

TASK = "e706449ebf4c"
MOD = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = find_root(__file__)
DATA_ROOT = canonical_path(ROOT).parents[1]
BASES = (
    "data/base/solutions/training/c97c0139__e706449ebf4c.json",
    "data/base/solutions/augmented/c97c0139__3692ae875598.json",
)


def canonical_rows():
    return [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if json.loads(line).get("task_id") == TASK]


def row_pairs(row):
    test = row["test"]
    return row["train"] + ([test] if isinstance(test, dict) else test)


class GeneratorTests(unittest.TestCase):
    def test_all_canonical_occurrences_and_public_profiles_exact(self):
        rows = canonical_rows()
        self.assertEqual({row["source"] for row in rows}, {"training", "augmented"})
        pairs = [pair for row in rows for pair in row_pairs(row)]
        self.assertEqual(len(pairs), 6)
        self.assertEqual(len({tuple(map(tuple, pair["input"])) for pair in pairs}), 3)
        seen = set()
        for pair in pairs:
            profile = MOD.canonical_profile_signature(pair["input"])
            self.assertIn(profile, MOD.PUBLIC_PROFILES)
            seen.add(profile)
            grid = MOD.generate(11, 29, scene_profile=profile)
            self.assertEqual(grid, pair["input"])
            self.assertEqual(MOD.rule_mirror(grid), pair["output"])
            self.assertEqual(MOD.self_check(grid), [])
            self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})
        self.assertEqual(seen, set(MOD.PUBLIC_PROFILES))

    def test_every_general_profile_in_every_band(self):
        for band in (None, "easy", "medium", "hard"):
            for profile in MOD.GENERAL_PROFILES:
                for seed in range(40):
                    grid = MOD.generate(seed, seed * 19, difficulty=band, scene_profile=profile)
                    analysis = MOD._analysis(grid)
                    self.assertEqual(analysis["errors"], [], (band, profile, seed, analysis))
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MOD.rule_mirror(grid), analysis["output"])

    def test_profiles_isolate_parity_orientation_count_clipping_and_interactions(self):
        for seed in range(80):
            for profile in MOD.GENERAL_PROFILES:
                grid = MOD.generate(seed, seed * 7, scene_profile=profile)
                facts = MOD._analysis(grid)["facts"]
                bars = facts["bars"]
                if profile.startswith("single_"):
                    parts = profile.split("_")
                    self.assertEqual(len(bars), 1)
                    self.assertEqual(bars[0]["orientation"], parts[1])
                    self.assertEqual(bars[0]["parity"], parts[2])
                    self.assertFalse(bars[0]["clipped_sides"])
                elif profile == "two_parallel":
                    self.assertEqual(len(bars), 2)
                    self.assertEqual(len({bar["orientation"] for bar in bars}), 1)
                elif profile == "two_perpendicular":
                    self.assertEqual(len(bars), 2)
                    self.assertEqual(len({bar["orientation"] for bar in bars}), 2)
                elif profile == "three_mixed":
                    self.assertEqual(len(bars), 3)
                elif profile == "clipped_edge":
                    self.assertEqual(len(bars[0]["clipped_sides"]), 1)
                elif profile == "clipped_both_edges":
                    self.assertGreaterEqual(len(bars[0]["clipped_sides"]), 2)
                elif profile == "overlapping_auras":
                    self.assertTrue(facts["overlapping_auras"])
                    self.assertFalse(facts["aura_hits_other_bar"])
                elif profile == "aura_hits_other_bar":
                    self.assertTrue(facts["aura_hits_other_bar"])

    def test_exact_doubled_coordinate_odd_even_geometry_and_red_preservation(self):
        odd = [[0] * 8 for _ in range(7)]
        odd[3][2:5] = [2, 2, 2]
        odd_out = MOD.rule_mirror(odd)
        self.assertEqual({(row, col) for row in range(7) for col in range(8) if odd_out[row][col] == 8}, {(2, 3), (4, 3)})
        even = [[0] * 9 for _ in range(7)]
        even[3][2:6] = [2, 2, 2, 2]
        even_out = MOD.rule_mirror(even)
        self.assertEqual({(row, col) for row in range(7) for col in range(9) if even_out[row][col] == 8}, {(2, 3), (2, 4), (4, 3), (4, 4)})
        hit = MOD.generate(9, 4, scene_profile="aura_hits_other_bar")
        hit_out = MOD.rule_mirror(hit)
        for row in range(len(hit)):
            for col in range(len(hit[0])):
                if hit[row][col] == 2:
                    self.assertEqual(hit_out[row][col], 2)

    def test_distribution_covers_declared_semantics_and_varies_materially(self):
        profiles = Counter()
        inputs, outputs, shapes = set(), set(), set()
        lengths, counts, orientations, parities, clipped = set(), set(), set(), set(), set()
        for seed in range(3000):
            grid = MOD.generate(seed, seed * 31, difficulty=("easy", "medium", "hard")[seed % 3])
            analysis = MOD._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            facts = analysis["facts"]
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, facts["output"])))
            shapes.add((len(grid), len(grid[0])))
            counts.add(len(facts["bars"]))
            for bar in facts["bars"]:
                lengths.add(bar["length"])
                orientations.add(bar["orientation"])
                parities.add(bar["parity"])
                clipped.add(bool(bar["clipped_sides"]))
        self.assertEqual(set(profiles), set(MOD.SCENE_PROFILES))
        self.assertGreater(len(inputs), 2600)
        self.assertGreater(len(outputs), 2600)
        self.assertGreater(len(shapes), 100)
        self.assertEqual(counts, {1, 2, 3})
        self.assertEqual(orientations, {"horizontal", "vertical"})
        self.assertEqual(parities, {"odd", "even"})
        self.assertEqual(clipped, {False, True})
        self.assertTrue({5, 7, 9, 10, 14}.issubset(lengths))

    def test_malformed_and_semantic_impostors_fail_closed(self):
        cases = [[], [[]], [[True]], [[9]], [[2], [2, 0]], [[0] * 8 for _ in range(8)], [[2] * 8 for _ in range(8)]]
        short = [[0] * 8 for _ in range(8)]
        short[3][3:5] = [2, 2]
        cases.append(short)
        bent = [[0] * 9 for _ in range(9)]
        for row, col in ((3, 3), (3, 4), (3, 5), (4, 5)):
            bent[row][col] = 2
        cases.append(bent)
        four = [[0] * 20 for _ in range(20)]
        for index in range(4):
            for col in range(3):
                four[2 + index * 4][2 + col] = 2
        cases.append(four)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)
        with self.assertRaises(ValueError):
            MOD.rule_mirror([])

    def test_determinism_unknowns_freshness_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "warm"}, {"n_bars": 2}):
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

    def test_generate_rejects_non_literal_call_scalars(self):
        for bad_seed in (True, False, 1.0, 1.75, "1"):
            with self.subTest(axis="seed", value=bad_seed):
                with self.assertRaises((TypeError, ValueError)):
                    MOD.generate(bad_seed, 0)
        for bad_index in (True, False, 1.0, 1.75, "1"):
            with self.subTest(axis="sample_index", value=bad_index):
                with self.assertRaises((TypeError, ValueError)):
                    MOD.generate(991, bad_index)
        with self.assertRaises(ValueError):
            MOD.generate(991, -1)

    def test_default_schedule_interleaves_canonical_shaped_joint_witnesses(self):
        canonical_profiles = {
            (len(pair["input"]), len(pair["input"][0]), len({value for row in pair["input"] for value in row}))
            for row in canonical_rows()
            for pair in row_pairs(row)
        }
        for band in ("easy", "medium", "hard"):
            grid = MOD.generate(12345, 4, difficulty=band)
            profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
            self.assertIn(profile, canonical_profiles, (band, profile))
            self.assertEqual(MOD._analysis(grid)["scene_profile"], "aura_hits_other_bar")
            self.assertTrue(MOD._witness_half_cell_center(grid))
            self.assertTrue(MOD._witness_red_bar_preservation(grid))

    def test_default_four_pair_window_is_rotation_safe(self):
        seed = 24674232131726
        pairs = []
        for sample_index in range(4):
            grid = MOD.generate(seed, sample_index, difficulty="easy")
            pairs.append({"input": grid, "output": MOD.rule_mirror(grid)})
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            self.assertEqual(
                MOD.lesson_identifiable(demos, pairs[query_index]),
                [],
                (query_index, [MOD._analysis(pair["input"])["scene_profile"] for pair in pairs]),
            )

    def test_semantic_rivals_and_lesson_identifiability(self):
        odd = MOD.generate(31, 0, scene_profile="single_horizontal_odd")
        even = MOD.generate(31, 1, scene_profile="single_horizontal_even")
        hit = MOD.generate(31, 2, scene_profile="aura_hits_other_bar")

        self.assertEqual(MOD.strict_canonical_like(odd), [])
        self.assertFalse(MOD._witness_half_cell_center(odd))
        self.assertTrue(MOD._witness_half_cell_center(even))
        self.assertEqual(MOD._rival_integer_center_radius(odd), MOD.rule_mirror(odd))
        self.assertNotEqual(MOD._rival_integer_center_radius(even), MOD.rule_mirror(even))

        self.assertTrue(MOD._witness_red_bar_preservation(hit))
        self.assertNotEqual(MOD._rival_overwrite_other_red(hit), MOD.rule_mirror(hit))
        for row in canonical_rows():
            for pair in row_pairs(row):
                self.assertEqual(MOD._rival_overwrite_other_red(pair["input"]), pair["output"])

        odd_pair = {"input": odd, "output": MOD.rule_mirror(odd)}
        even_pair = {"input": even, "output": MOD.rule_mirror(even)}
        hit_pair = {"input": hit, "output": MOD.rule_mirror(hit)}
        reasons = MOD.lesson_identifiable([odd_pair], even_pair)
        self.assertTrue(any("integer_center_radius" in reason for reason in reasons), reasons)
        self.assertEqual(MOD.lesson_identifiable([even_pair, hit_pair], odd_pair), [])

        self.assertEqual(
            set(MOD.SEMANTIC_RIVALS),
            {"integer_center_radius", "overwrite_other_red"},
        )
        self.assertEqual(
            MOD.WITNESS_RIVALS,
            {
                "half_cell_center": ["integer_center_radius"],
                "red_bar_preservation": ["overwrite_other_red"],
            },
        )
        self.assertEqual(set(MOD.CANONICAL_SHORTCUTS), {"overwrite_other_red"})

    def test_rule_hash_grounded_rule_and_both_base_sources_are_synced(self):
        rows = canonical_rows()
        sources = {row["program_solution"] for row in rows}
        self.assertEqual(len(sources), 1)
        source = sources.pop()
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(MOD.RULE_HASH, digest)
        from solvers.grounded_rules import GROUNDED_RULES
        self.assertEqual(GROUNDED_RULES[TASK], source)
        for path in BASES:
            base = json.loads((DATA_ROOT / path.removeprefix("data/")).read_text())
            self.assertEqual(base["racket_target"]["raw_code"], source)
            self.assertEqual(base["racket_target"]["target_code"], source)


if __name__ == "__main__":
    unittest.main()
