from __future__ import annotations

import json
import random
import unittest
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.b3750af4dac1 import generator


ROOT = Path(__file__).resolve().parents[1]


def canonical_pairs():
    from reviewer_support import canonical_pairs as read_pairs, find_root

    root = find_root(__file__)
    return [
        {"input": row["input"], "output": row["output"]}
        for row in read_pairs(generator.TASK_ID, root=root, labeled_only=True)
    ]


def frozen(grid):
    return tuple(tuple(row) for row in grid)


class B3750af4dac1GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = canonical_pairs()

    def test_rule_hash_and_all_canonical_pairs(self):
        self.assertEqual(generator.RULE_HASH, "674e022a164b")
        self.assertEqual(len(self.pairs), 3)
        observed_rows = set()
        for pair in self.pairs:
            source = pair["input"]
            before = frozen(source)
            self.assertEqual(generator.self_check(source), [])
            self.assertEqual(generator.rule_mirror(source), pair["output"])
            self.assertEqual(frozen(source), before)
            observed_rows.add(generator.observe_overrides(source)["macro_r"])
        self.assertIn(1, observed_rows)
        self.assertIn(2, observed_rows)

    def test_exact_axis_boundaries_and_loud_incompatibility(self):
        cases = (
            {"macro_r": 1},
            {"macro_r": 5},
            {"macro_c": 2},
            {"macro_c": 6},
            {"room_h": 2},
            {"room_h": 9},
            {"room_w": 2},
            {"room_w": 9},
            {"macro_r": 1, "room_w": 9},
            {"macro_c": 6, "room_w": 9},
            {"macro_r": 1, "macro_c": 6},
            {
                "macro_r": 5,
                "macro_c": 6,
                "room_h": 9,
                "room_w": 9,
            },
        )
        for overrides in cases:
            for difficulty in ("easy", "medium", "hard"):
                with self.subTest(
                    overrides=overrides, difficulty=difficulty
                ):
                    grid = generator.generate(
                        83,
                        197,
                        difficulty=difficulty,
                        **overrides,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    observed = generator.observe_overrides(grid)
                    for axis, requested in overrides.items():
                        self.assertEqual(observed[axis], requested)
        with self.assertRaisesRegex(ValueError, "at least three rooms"):
            generator.generate(0, 0, macro_r=1, macro_c=2)
        with self.assertRaisesRegex(ValueError, "1x6 lattice"):
            generator.generate(
                0,
                0,
                macro_r=1,
                macro_c=6,
                room_w=9,
            )

    def test_ordinary_draws_preserve_keyed_axes_and_rebut_fixed_answer(self):
        for difficulty in ("easy", "medium", "hard"):
            positions = set()
            widths = set()
            roles = {name: 0 for name in generator._FOCUSES}
            inputs = set()
            outputs = set()
            for seed in range(240):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = generator.generate(
                        seed,
                        seed * 31 + 7,
                        difficulty=difficulty,
                    )
                finally:
                    base.set_ctx_observer(None)
                self.assertEqual(generator.self_check(grid), [])
                self.assertTrue(captured)
                observed = generator.observe_overrides(grid)
                for axis in generator.AXES:
                    self.assertEqual(captured[-1]._drawn[axis], observed[axis])
                scene = generator._scene_analysis(grid)["geometry"]
                self.assertEqual(len(scene["matches"]), 1)
                positions.add(scene["matches"][0])
                widths.add(len(scene["output"][0]))
                inputs.add(frozen(grid))
                outputs.add(frozen(scene["output"]))
                for role, indices in scene["near_miss_roles"].items():
                    roles[role] += bool(indices)
            self.assertGreaterEqual(len(positions), 5)
            self.assertGreaterEqual(len(widths), 3)
            self.assertGreaterEqual(len(inputs), 235)
            minimum_outputs = 15 if difficulty == "easy" else 25
            self.assertGreaterEqual(len(outputs), minimum_outputs)
            self.assertTrue(all(count >= 10 for count in roles.values()), roles)

    def test_self_check_rejects_targeted_impostors(self):
        grid = generator.generate(811, 991, difficulty="hard")
        scene = generator._scene_analysis(grid)["geometry"]

        broken_boundary = [row[:] for row in grid]
        broken_boundary[0][1] = 0
        self.assertTrue(generator.self_check(broken_boundary))

        junction_door = [row[:] for row in grid]
        junction_door[scene["wall_rows"][1]][scene["wall_cols"][1]] = 7
        self.assertTrue(
            any(
                "exactly one internal separator" in error
                for error in generator.self_check(junction_door)
            )
        )

        interior_wall = [row[:] for row in grid]
        first_room_cell = generator._rule_facts(grid)["rooms"][0]["cells"][0]
        interior_wall[first_room_cell[0]][first_room_cell[1]] = 9
        self.assertTrue(
            any(
                "wall color inside a room" in error
                for error in generator.self_check(interior_wall)
            )
        )

        missing_query_color = [row[:] for row in grid]
        for row, col in generator._rule_facts(grid)["rooms"][0]["cells"]:
            if missing_query_color[row][col] == 2:
                missing_query_color[row][col] = 0
        self.assertTrue(
            any(
                "both color-2 and color-3" in error
                for error in generator.self_check(missing_query_color)
            )
        )

        ambiguous = None
        for seed in range(500):
            candidate = generator.generate(
                20_000 + seed,
                30_000 + seed,
                difficulty="medium",
            )
            facts = generator._rule_facts(candidate)
            roles = generator._near_miss_roles(facts["signatures"])
            role_indices = roles["red_count"] or roles["green_count"]
            if not role_indices:
                continue
            ambiguous = [row[:] for row in candidate]
            candidate_index = role_indices[0] + 1
            room_id = facts["order"][candidate_index]
            cells = facts["rooms"][room_id]["cells"]
            for row, col in cells:
                if ambiguous[row][col] in (2, 3):
                    ambiguous[row][col] = 0
            q2, q3 = facts["signatures"][0][2:]
            for row, col in cells[:q2]:
                ambiguous[row][col] = 2
            for row, col in cells[q2:q2 + q3]:
                ambiguous[row][col] = 3
            break
        self.assertIsNotNone(ambiguous)
        self.assertTrue(
            any(
                "exactly one candidate" in error
                for error in generator.self_check(ambiguous)
            )
        )

    def test_deterministic_fresh_returns_and_global_rng_isolation(self):
        random.seed(905_113)
        state = random.getstate()
        first = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))
        first[0][0] = 4
        self.assertNotEqual(first, second)

    def test_strict_call_validation(self):
        bad_calls = (
            {"difficulty": "expert"},
            {"bogus": 1},
            {"macro_r": True},
            {"macro_c": 2.0},
            {"room_h": "3"},
            {"room_w": 10},
            {"texture": "all_match"},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **kwargs)


if __name__ == "__main__":
    unittest.main()
