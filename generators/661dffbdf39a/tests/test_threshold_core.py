"""Behavioral tests for the proposed task-local threshold prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import random
import unittest
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "workspace/parametric/threshold_variant.py"
CORE = None
if SOURCE.exists():
    SPEC = importlib.util.spec_from_file_location("threshold_variant_core_test", SOURCE)
    CORE = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(CORE)


def grid(*rows):
    return [[int(cell) for cell in row] for row in rows]


BOUNDARY_INPUT = grid("550000", "005550", "555500", "555551", "000000", "000000")
BOUNDARY_OUTPUTS = {
    "1/3": grid("555500", "111155", "111155", "111155", "555500", "555500"),
    "1/2": grid("000000", "000000", "555555", "555555", "000000", "000000"),
    "2/3": grid("000000", "000000", "000000", "555555", "000000", "000000"),
}


def transpose(value):
    return [list(row) for row in zip(*value)]


class ThresholdCoreTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(CORE, "threshold prototype has not been implemented")

    def test_strict_fraction_boundaries_in_both_axes(self):
        # Catches >=, wrong denominator, and row/column orientation mistakes.
        before = copy.deepcopy(BOUNDARY_INPUT)
        for threshold, expected in BOUNDARY_OUTPUTS.items():
            with self.subTest(threshold=threshold):
                self.assertEqual(CORE.solve_python(BOUNDARY_INPUT, threshold), expected)
                inputs = [BOUNDARY_INPUT, transpose(BOUNDARY_INPUT)]
                self.assertEqual(CORE.run_racket(CORE.rule_program(threshold), inputs),
                                 [expected, transpose(expected)])
        self.assertEqual(BOUNDARY_INPUT, before)

    def test_sampler_has_exact_teaching_boundaries_and_strong_lines(self):
        # Catches perpendicular gray leakage and loss of the strict-boundary witness.
        states = set()
        shapes = set()
        markers = set()
        strong_counts = set()
        for seed in range(4):
            for sample_index in range(7):
                value = CORE.sample_input(seed, sample_index)
                h, w = len(value), len(value[0])
                shapes.add((h, w))
                self.assertIn(h, (18, 24))
                self.assertIn(w, (18, 24))
                colors = {cell for row in value for cell in row} - {0, 5}
                self.assertEqual(len(colors), 1)
                markers.update(colors)
                row_counts = [row.count(5) for row in value]
                col_counts = [column.count(5) for column in transpose(value)]
                for counts, length in ((row_counts, w), (col_counts, h)):
                    for count in (length // 3, length // 2, 2 * length // 3):
                        self.assertIn(count, counts)
                    strong = sum(3 * count > 2 * length for count in counts)
                    self.assertIn(strong, (2, 3))
                    self.assertFalse(any(count == length for count in counts))
                    # The sampler has exactly three partial candidates per axis.
                    self.assertEqual(sum(3 * count > length for count in counts), strong + 2)
                strong_counts.add((sum(3 * n > 2 * w for n in row_counts),
                                   sum(3 * n > 2 * h for n in col_counts)))
                states.add(tuple(map(tuple, value)))
        self.assertEqual(len(states), 28)
        self.assertEqual(len(shapes), 4)
        self.assertGreaterEqual(len(markers), 4)
        self.assertGreaterEqual(len(strong_counts), 3)

    def test_sampler_is_deterministic_and_does_not_change_global_rng(self):
        before = random.getstate()
        first = CORE.sample_input(17, 9)
        second = CORE.sample_input(17, 9)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertEqual(random.getstate(), before)
        self.assertNotEqual(first, CORE.sample_input(17, 10))

    def test_episode_labels_rule_and_teaching_are_consistent(self):
        # Catches per-pair resampling, Python-only labels, and query-aided teaching.
        before = random.getstate()
        input_sequences = []
        for threshold in ("1/3", "1/2", "2/3"):
            episode = CORE.make_episode(42, threshold)
            self.assertEqual(len(episode["train"]), 3)
            self.assertEqual(len(episode["test"]), 4)
            pairs = episode["train"] + episode["test"]
            inputs = [pair["input"] for pair in pairs]
            input_sequences.append(inputs)
            self.assertEqual(len({tuple(map(tuple, value)) for value in inputs}), 7)
            meta = episode["metadata"]
            self.assertEqual(meta["threshold"], threshold)
            self.assertEqual(meta["seed"], 42)
            self.assertEqual(meta["program"], CORE.rule_program(threshold))
            self.assertEqual(meta["program_sha256"],
                             hashlib.sha256(meta["program"].encode()).hexdigest())
            self.assertEqual([pair["output"] for pair in pairs],
                             CORE.run_racket(meta["program"], inputs))
            teaching = meta["teaching"]
            self.assertFalse(teaching["query_answers_used_for_identifiability"])
            self.assertEqual(teaching["surviving_hypotheses"], [f"strict>{threshold}"])
            self.assertEqual(len(teaching["demo_witnesses"]), 3)
            for indices in teaching["demo_witnesses"].values():
                self.assertTrue(indices)
                self.assertTrue(all(type(i) is int and 0 <= i < 3 for i in indices))
            self.assertEqual(len(teaching["query_certificates"]), 4)
            for index, certificate in enumerate(teaching["query_certificates"]):
                self.assertEqual(certificate["query_index"], index)
                self.assertEqual(set(certificate["eliminated_by_demonstrations"]),
                                 set(teaching["demo_witnesses"]))
        self.assertEqual(input_sequences[0], input_sequences[1])
        self.assertEqual(input_sequences[1], input_sequences[2])
        self.assertEqual(random.getstate(), before)

    def test_independent_counts_and_minimum_demo_are_supported(self):
        episode = CORE.make_episode(7, "1/2", train_count=1, query_count=2)
        self.assertEqual(len(episode["train"]), 1)
        self.assertEqual(len(episode["test"]), 2)
        self.assertEqual(episode, CORE.make_episode(7, "1/2", train_count=1, query_count=2))
        for indices in episode["metadata"]["teaching"]["demo_witnesses"].values():
            self.assertEqual(indices, [0])

    def test_rejects_noninteger_seed_index_and_counts(self):
        # bool is an int subclass, but is never an accepted seed or count.
        for invalid in (True, False, -1, 1.5, "1", None):
            with self.subTest(value=invalid):
                with self.assertRaises(ValueError):
                    CORE.sample_input(invalid, 0)
                with self.assertRaises(ValueError):
                    CORE.sample_input(0, invalid)
                with self.assertRaises(ValueError):
                    CORE.make_episode(invalid)
                for field in ("train_count", "query_count"):
                    with self.assertRaises(ValueError):
                        CORE.make_episode(0, **{field: invalid})
        for field, invalid in (("train_count", 0), ("train_count", 13),
                               ("query_count", 0), ("query_count", 17)):
            with self.assertRaises(ValueError):
                CORE.make_episode(0, **{field: invalid})

    def test_rejects_invalid_threshold_and_grid(self):
        for invalid in (None, True, 0.5, "0.5", "1/4", "2/4", ["1/2"]):
            with self.subTest(threshold=invalid):
                with self.assertRaises(ValueError):
                    CORE.rule_program(invalid)
                with self.assertRaises(ValueError):
                    CORE.solve_python(BOUNDARY_INPUT, invalid)
                with self.assertRaises(ValueError):
                    CORE.make_episode(0, invalid)
        malformed = [[], [[]], [[True]], [[1.0]], [[10]], [[-1]],
                     [[0], [0, 1]], "123", [[1] * 31], [[1]] * 31]
        for invalid in malformed:
            with self.subTest(grid=invalid):
                with self.assertRaises(ValueError):
                    CORE.solve_python(invalid)
                with self.assertRaises(ValueError):
                    CORE.run_racket(CORE.rule_program(), [invalid])
        for outside_domain in ([[0, 5]], [[1, 2, 5]]):
            with self.assertRaises(ValueError):
                CORE.solve_python(outside_domain)


if __name__ == "__main__":
    unittest.main()
