"""Focused regressions for the 5545f144-inspired waypoint-route family."""

from __future__ import annotations

from copy import deepcopy
import unittest

from puzzle_generators.generic.concepts.waypoint_route import gen1, gen2


class WaypointRouteGeneratorTests(unittest.TestCase):
    def test_generation_is_deterministic_and_self_checked(self) -> None:
        for difficulty in ("easy", "medium", "hard"):
            first = gen1.generate_task(207, difficulty=difficulty)
            second = gen1.generate_task(207, difficulty=difficulty)
            self.assertEqual(first, second)
            self.assertEqual([], gen1.self_check_task(first))
            self.assertEqual("5545f144", first["meta"]["source_task_id"])
            self.assertEqual(gen1.RULE_HASH, first["meta"]["rule_hash"])

    def test_unknown_difficulty_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            gen1.generate_task(1, difficulty="impossible")

    def test_output_mutation_is_rejected(self) -> None:
        task = deepcopy(gen1.generate_task(17, difficulty="hard"))
        task["train"][0]["output"][0][0] = (
            task["train"][0]["output"][0][0] + 1
        ) % 10
        self.assertTrue(
            any("output disagrees" in finding for finding in gen1.self_check_task(task))
        )

    def test_rule_hash_mutation_is_rejected(self) -> None:
        task = deepcopy(gen1.generate_task(29))
        task["meta"]["rule_hash"] = "bad"
        self.assertIn(
            "task meta.rule_hash does not match RULE_HASH",
            gen1.self_check_task(task),
        )


class OrderedCursorWaypointRouteGeneratorTests(unittest.TestCase):
    def test_generation_is_deterministic_and_self_checked(self) -> None:
        for difficulty in ("easy", "medium", "hard"):
            first = gen2.generate_task(207, difficulty=difficulty)
            second = gen2.generate_task(207, difficulty=difficulty)
            self.assertEqual(first, second)
            self.assertEqual([], gen2.self_check_task(first))
            self.assertEqual("5545f144", first["meta"]["source_task_id"])
            self.assertEqual(gen2.RULE_HASH, first["meta"]["rule_hash"])

    def test_head_and_tail_colors_are_distinct(self) -> None:
        task = gen2.generate_task(31, difficulty="hard")
        for pair in task["train"] + task["test"]:
            state = gen2._parse_last_state(pair["input"])
            self.assertNotEqual(state["head_color"], state["tail_color"])
            self.assertEqual(gen2._apply(pair["input"]), pair["output"])

    def test_output_mutation_is_rejected(self) -> None:
        task = deepcopy(gen2.generate_task(43))
        task["test"][0]["output"][0][0] = (
            task["test"][0]["output"][0][0] + 1
        ) % 10
        self.assertTrue(
            any("output disagrees" in finding for finding in gen2.self_check_task(task))
        )


if __name__ == "__main__":
    unittest.main()
