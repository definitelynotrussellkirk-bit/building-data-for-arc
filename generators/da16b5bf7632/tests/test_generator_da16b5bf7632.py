"""Focused semantic regressions for generator da16b5bf7632."""
from __future__ import annotations

import copy
import hashlib
import json
import random
import unittest
from puzzle_generators.per_puzzle.da16b5bf7632 import generator as gen
from reviewer_support import canonical_path, find_root


ROOT = find_root(__file__)


def _canonical_row():
    with canonical_path(ROOT).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row["task_id"] == gen.TASK_ID:
                return row
    raise AssertionError("canonical task row is missing")


def _pairs(row):
    for split in ("train", "test"):
        values = row[split]
        values = values if isinstance(values, list) else [values]
        for pair in values:
            yield pair


class GeneratorDa16b5bf7632Tests(unittest.TestCase):
    def test_rule_hash_and_all_five_canonical_pairs(self):
        row = _canonical_row()
        digest = hashlib.sha256(row["program_solution"].encode()).hexdigest()
        self.assertEqual(gen.RULE_HASH, digest[:12])
        signatures = set()
        for pair in _pairs(row):
            source = copy.deepcopy(pair["input"])
            self.assertEqual(gen.self_check(source), [])
            signatures.add(gen.canonical_profile_signature(source))
            self.assertEqual(gen.rule_mirror(source), pair["output"])
            self.assertEqual(source, pair["input"])
        self.assertEqual(
            signatures,
            {
                "public_topology_1",
                "public_topology_2",
                "public_topology_3",
                "public_topology_4",
            },
        )

    def test_every_band_and_family_is_valid_and_observable(self):
        for band in ("easy", "medium", "hard"):
            for family in gen.SCENE_FAMILIES:
                for seed in range(80):
                    grid = gen.generate(
                        seed,
                        seed % 3,
                        difficulty=band,
                        scene_family=family,
                    )
                    self.assertEqual(gen.self_check(grid), [])
                    self.assertEqual(
                        gen.observe_overrides(grid),
                        {"scene_family": family},
                    )
                    analysis = gen._analyze(grid)
                    self.assertEqual(analysis["facts"]["scene_family"], family)
                    self.assertNotEqual(
                        analysis["facts"]["hole_sequence"],
                        tuple(
                            sorted(
                                analysis["facts"]["hole_sequence"],
                                reverse=True,
                            )
                        ),
                    )

    def test_linked_family_covers_every_public_topology(self):
        signatures = set()
        tie_witnesses = 0
        four_component_witnesses = 0
        same_color_witnesses = 0
        for band in ("easy", "medium", "hard"):
            for seed in range(200):
                grid = gen.generate(
                    seed,
                    0,
                    difficulty=band,
                    scene_family="linked",
                )
                facts = gen._analyze(grid)["facts"]
                signatures.add(gen.canonical_profile_signature(grid))
                tie_witnesses += facts["has_tie"]
                four_component_witnesses += facts["component_count"] == 4
                same_color_witnesses += facts["same_color_disconnected"]
        self.assertEqual(
            signatures,
            {
                "public_topology_1",
                "public_topology_2",
                "public_topology_3",
                "public_topology_4",
            },
        )
        self.assertGreater(tie_witnesses, 100)
        self.assertGreater(four_component_witnesses, 100)
        self.assertGreater(same_color_witnesses, 100)

    def test_generalized_family_is_novel_and_covers_ties_and_hole_three(self):
        ties = 0
        hole_three = 0
        component_counts = set()
        for band in ("easy", "medium", "hard"):
            for seed in range(200):
                grid = gen.generate(
                    seed,
                    1,
                    difficulty=band,
                    scene_family="generalized",
                )
                facts = gen._analyze(grid)["facts"]
                self.assertIsNone(facts["linked_index"])
                ties += facts["has_tie"]
                hole_three += 3 in facts["hole_sequence"]
                component_counts.add(facts["component_count"])
        self.assertGreater(ties, 200)
        self.assertGreater(hole_three, 50)
        self.assertEqual(component_counts, {3, 4, 5})

    def test_equal_hole_ties_keep_bbox_reading_order(self):
        rng = random.Random(402)
        specs = (
            (gen.T_TETROMINO, "zero"),
            (gen.FRAME_4, "first_one"),
            (gen.FRAME_3X4, "second_one"),
        )
        grid = gen._pack_specs(rng, specs, 12, 18)
        analysis = gen._analyze(grid)
        self.assertEqual(analysis["errors"], [])
        records = analysis["facts"]["records"]
        one_hole = [record for record in records if record["holes"] == 1]
        self.assertEqual(len(one_hole), 2)
        output = gen.rule_mirror(grid)
        first_width = one_hole[0]["bbox"][3] - one_hole[0]["bbox"][1] + 1
        self.assertEqual(output[0][0], one_hole[0]["color"])
        self.assertTrue(all(row[first_width] == 0 for row in output))
        self.assertEqual(output[0][first_width + 1], one_hole[1]["color"])

    def test_structural_impostors_are_rejected(self):
        blank = gen.full_grid(12, 18, 0)
        all_zero_holes = gen.full_grid(12, 18, 0)
        for col, color in ((1, 2), (5, 3), (9, 4)):
            all_zero_holes[1][col] = color
        only_two = gen._pack_specs(
            random.Random(1),
            ((gen.FRAME_3, "a"), (gen.T_TETROMINO, "b")),
            12,
            18,
        )
        already_sorted_generalization = gen._pack_specs(
            random.Random(2),
            (
                (gen.DOUBLE_4X5, "a"),
                (gen.FRAME_3X4, "b"),
                (gen.T_TETROMINO, "c"),
            ),
            12,
            18,
        )
        tied_only = gen._pack_specs(
            random.Random(3),
            (
                (gen.FRAME_4, "a"),
                (gen.FRAME_3X4, "b"),
                (gen.FRAME_5X3, "c"),
            ),
            12,
            18,
        )
        for grid in (
            blank,
            all_zero_holes,
            only_two,
            already_sorted_generalization,
            tied_only,
        ):
            self.assertTrue(gen.self_check(grid), grid)

    def test_determinism_freshness_global_rng_and_validation(self):
        random.seed(923)
        state = random.getstate()
        first = gen.generate(
            17,
            4,
            difficulty="hard",
            scene_family="generalized",
        )
        self.assertEqual(random.getstate(), state)
        second = gen.generate(
            17,
            4,
            difficulty="hard",
            scene_family="generalized",
        )
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9 if first[0][0] != 9 else 8
        self.assertNotEqual(first, second)
        with self.assertRaises(ValueError):
            gen.generate(1, 0, difficulty="impossible")
        with self.assertRaises(ValueError):
            gen.generate(1, 0, bogus_axis="x")
        with self.assertRaises(ValueError):
            gen.generate(1, 0, scene_family="unknown")


if __name__ == "__main__":
    unittest.main()
