"""Focused semantic regressions for generator a8d6e6039a6f."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "a8d6e6039a6f"
gen = importlib.import_module(
    "puzzle_generators.per_puzzle.a8d6e6039a6f.generator"
)


def normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def canonical_row() -> dict:
    return next(
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )


class FrameKeyStampGeneratorTests(unittest.TestCase):
    def test_version_and_hash_are_current(self):
        self.assertEqual("4.0.0", gen.VERSION)
        self.assertEqual("9921e422d6f8", gen.RULE_HASH)

    def test_catalog_cardinalities(self):
        self.assertEqual(32, gen.LAYOUT_COUNT)
        self.assertEqual(8, gen.PUBLIC_PATTERN_COUNT)
        self.assertEqual(256, gen.PATTERN_COUNT)
        self.assertEqual(12, gen.PALETTE_COUNT)
        self.assertEqual(61_489_152, gen.SCENE_COUNT)

    def test_layout_catalog_has_balanced_frame_counts(self):
        self.assertEqual(14, len(gen.GENERAL_LAYOUTS[3]))
        self.assertEqual(14, len(gen.GENERAL_LAYOUTS[4]))

    def test_every_layout_has_unambiguous_key_spots(self):
        for layout, spots in zip(gen.LAYOUTS, gen.LAYOUT_SPOTS):
            self.assertTrue(spots)
            self.assertTrue(gen._layout_valid(layout[0], layout[1], layout[2]))

    def test_generalized_catalog_reaches_all_eight_key_spots(self):
        reached = set().union(*(set(spots) for spots in gen.LAYOUT_SPOTS[4:]))
        self.assertEqual(set(range(8)), reached)

    def test_patterns_are_connected_and_use_both_roles(self):
        for pattern in gen.PATTERNS:
            self.assertTrue(gen._connected_pattern(pattern))
            self.assertEqual({1, 2}, {value for row in pattern for value in row if value})

    def test_patterns_have_unique_reading_order_color_roles(self):
        for pattern in gen.PATTERNS:
            first = next(value for row in pattern for value in row if value)
            self.assertEqual(1, first)

    def test_palettes_are_all_ordered_distinct_pairs(self):
        self.assertEqual(12, len(gen.PALETTES))
        self.assertEqual(12, len(set(gen.PALETTES)))
        self.assertTrue(all(a != b and {a, b} <= {6, 7, 8, 9} for a, b in gen.PALETTES))

    def test_three_frame_key_orders_are_all_distinct_triples(self):
        self.assertEqual(24, len(gen.KEY_ORDERS[3]))
        self.assertTrue(all(len(set(keys)) == 3 for keys in gen.KEY_ORDERS[3]))

    def test_four_frame_key_orders_are_all_permutations(self):
        self.assertEqual(set(gen.KEY_ORDERS[4]), set(__import__("itertools").permutations((1, 2, 3, 4))))

    def test_all_canonical_pairs_reconstruct_exactly(self):
        row = canonical_row()
        for pair in row["train"] + row["test"]:
            analysis = gen._analysis(pair["input"])
            self.assertEqual([], analysis["errors"])
            self.assertEqual(pair["input"], gen._grid_from_code(analysis["scene_code"]))

    def test_all_canonical_outputs_match_python_oracle(self):
        row = canonical_row()
        for pair in row["train"] + row["test"]:
            self.assertEqual(pair["output"], gen.rule_mirror(pair["input"]))

    def test_all_canonical_profiles_are_public(self):
        row = canonical_row()
        signatures = {
            gen.canonical_profile_signature(pair["input"])
            for pair in row["train"] + row["test"]
        }
        self.assertEqual({f"public_layout_{index}" for index in range(4)}, signatures)

    def test_canonical_inputs_use_both_frame_counts(self):
        row = canonical_row()
        counts = {
            gen._analysis(pair["input"])["facts"]["frame_count"]
            for pair in row["train"] + row["test"]
        }
        self.assertEqual({3, 4}, counts)

    def test_scene_code_boundaries_round_trip(self):
        for code in (0, 1, gen.SCENE_COUNT - 2, gen.SCENE_COUNT - 1):
            grid = gen.generate(0, 0, scene_code=code)
            self.assertEqual([], gen.self_check(grid))
            self.assertEqual({"scene_code": code}, gen.observe_overrides(grid))
            self.assertEqual(code, gen._analysis(grid)["scene_code"])

    def test_scene_code_type_and_range_fail_loudly(self):
        for value in (-1, gen.SCENE_COUNT, True, "1"):
            with self.assertRaises((TypeError, ValueError)):
                gen.generate(0, 0, scene_code=value)

    def test_unknown_override_fails_loudly(self):
        with self.assertRaises(ValueError):
            gen.generate(0, 0, grid_h=12)

    def test_unknown_difficulty_fails_loudly(self):
        with self.assertRaises(ValueError):
            gen.generate(0, 0, difficulty="expert")

    def test_generation_is_deterministic(self):
        for band in (None, "easy", "medium", "hard"):
            self.assertEqual(
                gen.generate(17, 23, difficulty=band),
                gen.generate(17, 23, difficulty=band),
            )

    def test_generation_returns_fresh_grids(self):
        first = gen.generate(17, 23, difficulty="hard")
        expected = copy.deepcopy(first)
        first[0][0] = 9
        self.assertEqual(expected, gen.generate(17, 23, difficulty="hard"))

    def test_generation_preserves_process_global_rng(self):
        random.seed(1907)
        before = random.getstate()
        gen.generate(77, 3, difficulty="medium")
        self.assertEqual(before, random.getstate())

    def test_rule_mirror_is_input_pure(self):
        grid = gen.generate(32, 8, difficulty="hard")
        before = copy.deepcopy(grid)
        gen.rule_mirror(grid)
        self.assertEqual(before, grid)

    def test_self_check_is_observational(self):
        grid = gen.generate(42, 4, difficulty="medium")
        before = copy.deepcopy(grid)
        self.assertEqual([], gen.self_check(grid, difficulty="medium", meta={"x": 1}))
        self.assertEqual(before, grid)

    def test_empty_ragged_boolean_and_foreign_color_fail(self):
        self.assertTrue(gen.self_check([]))
        self.assertTrue(gen.self_check([[0], [0, 0]]))
        self.assertTrue(gen.self_check([[False]]))
        self.assertTrue(gen.self_check([[10]]))

    def test_removed_frame_border_is_rejected(self):
        grid = gen.generate(91, 2, difficulty="easy")
        frame = gen.LAYOUTS[gen._analysis(grid)["facts"]["layout_index"]][2][0]
        bad = copy.deepcopy(grid)
        bad[frame[0]][frame[2]] = 0
        self.assertTrue(gen.self_check(bad))

    def test_duplicate_frame_key_is_rejected(self):
        grid = gen.generate(92, 3, difficulty="hard")
        analysis = gen._analysis(grid)
        frame = gen.LAYOUTS[analysis["facts"]["layout_index"]][2][0]
        bad = copy.deepcopy(grid)
        current = analysis["facts"]["key_spot"]
        alternate = next(index for index in gen.LAYOUT_SPOTS[analysis["facts"]["layout_index"]] if index != current)
        row, col = gen._key_spots(frame)[alternate]
        bad[row][col] = 1
        self.assertTrue(gen.self_check(bad))

    def test_disconnected_template_cell_is_rejected(self):
        grid = gen.generate(93, 4, difficulty="medium")
        bad = copy.deepcopy(grid)
        bad[0][0] = 6
        self.assertTrue(gen.self_check(bad))

    def test_template_recolor_is_rejected(self):
        grid = gen.generate(94, 5, difficulty="medium")
        bad = copy.deepcopy(grid)
        cell = next(
            (row, col)
            for row, values in enumerate(bad)
            for col, value in enumerate(values)
            if value >= 6
        )
        bad[cell[0]][cell[1]] = 1
        self.assertTrue(gen.self_check(bad))

    def test_output_removes_source_template_and_keys(self):
        grid = gen.generate(101, 6, difficulty="hard")
        output = gen.rule_mirror(grid)
        analysis = gen._analysis(grid)
        layout = gen.LAYOUTS[analysis["facts"]["layout_index"]]
        top, left = layout[3][analysis["facts"]["placement"]]
        pattern = gen.PATTERNS[analysis["facts"]["pattern_index"]]
        for row, values in enumerate(pattern):
            for col, label in enumerate(values):
                if label:
                    self.assertEqual(0, output[top + row][left + col])
        self.assertFalse(any(value in (1, 2, 3, 4) for row in output for value in row))

    def test_transform_primitives_match_expected(self):
        pattern = ((6, 0, 7), (6, 7, 7))
        self.assertEqual(pattern, gen._transform(pattern, 1))
        self.assertEqual(gen._rotate_cw(pattern), gen._transform(pattern, 2))
        self.assertEqual(gen._flip_lr(pattern), gen._transform(pattern, 3))
        self.assertEqual(gen._flip_ud(pattern), gen._transform(pattern, 4))

    def test_every_forced_key_controls_a_stamp(self):
        layout_index = 4
        for key_index, keys in enumerate(gen.KEY_ORDERS[3]):
            code = gen._encode_scene(layout_index, key_index, 0, 8, 0, 0)
            grid = gen.generate(0, 0, scene_code=code)
            output = gen.rule_mirror(grid)
            self.assertNotEqual(grid, output)
            self.assertEqual(keys, gen._analysis(grid)["facts"]["keys"])

    def test_all_key_spots_round_trip_on_generalized_layouts(self):
        witnessed = set()
        for layout_index in range(4, gen.LAYOUT_COUNT):
            for spot in gen.LAYOUT_SPOTS[layout_index]:
                code = gen._encode_scene(layout_index, 0, spot, 8, 0, 0)
                facts = gen._analysis(gen.generate(0, 0, scene_code=code))["facts"]
                self.assertEqual(spot, facts["key_spot"])
                witnessed.add(spot)
        self.assertEqual(set(range(8)), witnessed)

    def test_all_palettes_round_trip(self):
        for palette_index, palette in enumerate(gen.PALETTES):
            code = gen._encode_scene(4, 0, 0, 8, palette_index, 0)
            facts = gen._analysis(gen.generate(0, 0, scene_code=code))["facts"]
            self.assertEqual(palette, facts["palette"])

    def test_all_template_placements_round_trip(self):
        for placement in range(gen.PLACEMENT_COUNT):
            code = gen._encode_scene(4, 0, 0, 8, 0, placement)
            facts = gen._analysis(gen.generate(0, 0, scene_code=code))["facts"]
            self.assertEqual(placement, facts["placement"])

    def test_natural_stream_reaches_every_public_profile(self):
        profiles = {
            gen.canonical_profile_signature(gen.generate(seed, 0, difficulty="medium"))
            for seed in range(500)
        }
        self.assertTrue({f"public_layout_{index}" for index in range(4)} <= profiles)

    def test_natural_stream_keeps_substantial_public_prior(self):
        for band in ("easy", "medium", "hard"):
            matches = sum(
                gen.canonical_profile_signature(gen.generate(seed, 0, difficulty=band)).startswith("public_")
                for seed in range(1000)
            )
            self.assertGreaterEqual(matches, 150)
            self.assertLessEqual(matches, 250)

    def test_natural_stream_is_highly_pair_diverse(self):
        for band in ("easy", "medium", "hard"):
            grids = [gen.generate(seed, 0, difficulty=band) for seed in range(1000)]
            outputs = [gen.rule_mirror(grid) for grid in grids]
            self.assertGreaterEqual(len({str(grid) for grid in grids}), 985)
            self.assertGreaterEqual(len({str(grid) for grid in outputs}), 980)

    def test_easy_and_hard_generalized_frame_counts_differ(self):
        easy = {
            gen._analysis(gen.generate(seed, 0, difficulty="easy"))["facts"]["frame_count"]
            for seed in range(300)
            if gen.canonical_profile_signature(gen.generate(seed, 0, difficulty="easy")) == "generalized"
        }
        hard = {
            gen._analysis(gen.generate(seed, 0, difficulty="hard"))["facts"]["frame_count"]
            for seed in range(300)
            if gen.canonical_profile_signature(gen.generate(seed, 0, difficulty="hard")) == "generalized"
        }
        self.assertEqual({3}, easy)
        self.assertEqual({4}, hard)

    def test_rule_hash_matches_all_source_authorities(self):
        hashes = []
        row = canonical_row()
        hashes.append(normalized_hash(row["program_solution"]))
        bank = json.loads((ROOT / "data/custom_puzzles/banks/ece0cc5101a3/puzzles.json").read_text())
        hashes.append(normalized_hash(next(item for item in bank if item["id"] == "hard_p07")["program_solution"]))
        base = json.loads((ROOT / "data/base/solutions/banks/ece0cc5101a3/hard_p07__a8d6e6039a6f.json").read_text())
        hashes.append(normalized_hash(base["racket_target"]["raw_code"]))
        hashes.append(normalized_hash(base["racket_target"]["target_code"]))
        self.assertEqual([gen.RULE_HASH] * 4, hashes)

    def test_base_description_covers_steps_and_negative_constraints(self):
        base = json.loads((ROOT / "data/base/solutions/banks/ece0cc5101a3/hard_p07__a8d6e6039a6f.json").read_text())
        description = base["description_target"]
        self.assertGreaterEqual(len(description["solution_steps"]), 5)
        self.assertGreaterEqual(len(description["negative_constraints"]), 4)
        self.assertTrue(description["semantic_primitives"])

    def test_task_is_removed_from_stale_source_ledger(self):
        stale = (ROOT / "data/derived/beautify_stale_sources.txt").read_text().splitlines()
        self.assertNotIn(TASK_ID, stale)


if __name__ == "__main__":
    unittest.main()
