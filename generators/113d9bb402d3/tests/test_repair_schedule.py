"""Regressions for the lesson-schedule and semantic-contract repair."""
from __future__ import annotations

import importlib
import unittest


TASK_ID = "113d9bb402d3"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _pair(seed: int, sample_index: int, difficulty: str):
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


class RepairScheduleTests(unittest.TestCase):
    def test_seed_and_sample_index_are_strict_nonnegative_integers(self):
        for bad_seed in (True, 1.5, "1", None):
            with self.assertRaises((TypeError, ValueError), msg=("seed", bad_seed)):
                GEN.generate(bad_seed, 0, difficulty="easy")
        for bad_index in (True, -1, 1.5, "1", None):
            with self.assertRaises((TypeError, ValueError), msg=("sample_index", bad_index)):
                GEN.generate(0, bad_index, difficulty="easy")

    def test_default_draws_follow_declared_alternating_coverage_schedule(self):
        self.assertEqual(GEN.LESSON_SCHEDULE_PERIOD, 2)
        self.assertEqual(set(GEN.SCHEDULE_PROFILES), {"gapped", "complete"})
        for difficulty in ("easy", "medium", "hard"):
            for sample_index in range(24):
                expected = GEN.schedule_profile(17, sample_index, difficulty)
                grid = GEN.generate(17, sample_index, difficulty=difficulty)
                observed = GEN.observe_overrides(grid)["zone_coverage"]
                self.assertEqual(observed, expected)

    def test_explicit_zone_coverage_override_wins_over_schedule(self):
        for sample_index in range(4):
            for requested in GEN.ZONE_COVERAGES:
                grid = GEN.generate(
                    31,
                    sample_index,
                    difficulty="medium",
                    zone_coverage=requested,
                )
                self.assertEqual(
                    GEN.observe_overrides(grid)["zone_coverage"], requested
                )

    def test_every_five_pair_cyclic_window_refutes_fill_whole_bbox_rival(self):
        for difficulty in ("easy", "medium", "hard"):
            for seed in range(8):
                for start in range(12):
                    pairs = [
                        _pair(seed, start + offset, difficulty)
                        for offset in range(GEN.EXAMPLES_NEEDED + 1)
                    ]
                    for query_index, query in enumerate(pairs):
                        demos = [
                            pair for index, pair in enumerate(pairs)
                            if index != query_index
                        ]
                        self.assertEqual(
                            GEN.lesson_identifiable(demos, query), [],
                            (difficulty, seed, start, query_index),
                        )

    def test_retained_seed_one_start_fifteen_counterexample_is_repaired(self):
        pairs = [_pair(1, index, "easy") for index in range(15, 20)]
        self.assertIn(
            "gapped",
            {GEN.observe_overrides(pair["input"])["zone_coverage"] for pair in pairs},
        )
        for query_index, query in enumerate(pairs):
            demos = [
                pair for index, pair in enumerate(pairs) if index != query_index
            ]
            self.assertEqual(GEN.lesson_identifiable(demos, query), [])

    def test_declared_rival_matches_complete_but_is_refuted_by_gapped_bbox(self):
        rival = GEN.SEMANTIC_RIVALS["fill_all_noncyan_bbox"]
        complete = GEN.generate(
            9, 0, difficulty="easy", zone_coverage="complete"
        )
        gapped = GEN.generate(
            9, 1, difficulty="easy", zone_coverage="gapped"
        )
        self.assertEqual(rival(complete), GEN.rule_mirror(complete))
        self.assertNotEqual(rival(gapped), GEN.rule_mirror(gapped))
        witness = GEN.SEMANTIC_WITNESSES["gapped_bbox_refutes_fill_all"]
        self.assertFalse(witness(complete))
        self.assertTrue(witness(gapped))


if __name__ == "__main__":
    unittest.main()
