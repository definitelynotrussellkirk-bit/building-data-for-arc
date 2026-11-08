"""Literal witnesses for the canonical vote and topology-dependent retention."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import unittest


PROGRAMS_PATH = Path(__file__).resolve().parents[1] / "programs.py"

# Two blue rooms become one seven-cell component through the blue marker at
# (1, 2). Each red room is larger than either blue room, and red has more total
# pixels, but no connected red component is as large as the joined blue one.
MERGE_INPUT = [
    [1, 5, 5, 5, 1, 5, 2, 5, 2],
    [0, 0, 1, 0, 0, 5, 0, 0, 0],
    [5, 5, 5, 5, 5, 5, 5, 5, 5],
    [0, 0, 5, 0, 0, 5, 0, 0, 0],
    [2, 5, 5, 1, 5, 5, 2, 5, 5],
]
FILLED = [
    [1, 5, 5, 5, 1, 5, 2, 5, 2],
    [1, 1, 1, 1, 1, 5, 2, 2, 2],
    [5, 5, 5, 5, 5, 5, 5, 5, 5],
    [2, 2, 5, 1, 1, 5, 2, 2, 2],
    [2, 5, 5, 1, 5, 5, 2, 5, 5],
]
RETAINED = [
    [1, 5, 5, 5, 1, 5, 2, 5, 2],
    [1, 1, 1, 1, 1, 5, 0, 0, 0],
    [5, 5, 5, 5, 5, 5, 5, 5, 5],
    [0, 0, 5, 0, 0, 5, 0, 0, 0],
    [2, 5, 5, 1, 5, 5, 2, 5, 5],
]

# A lawful 2x2 room lattice: the top-left room gets three blue pixel votes
# from one connected marker run, but two red votes from two separate objects.
CONTACT_INPUT = [
    [5, 1, 1, 1, 5, 2, 2, 5, 5, 5],
    [5, 0, 0, 0, 5, 0, 0, 0, 0, 5],
    [2, 0, 0, 0, 2, 0, 0, 0, 0, 2],
    [5, 0, 0, 0, 5, 0, 0, 0, 0, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 0, 0, 0, 5, 0, 0, 0, 0, 5],
    [2, 0, 0, 0, 1, 0, 0, 0, 0, 2],
    [5, 0, 0, 0, 5, 0, 0, 0, 0, 5],
    [5, 0, 0, 0, 5, 0, 0, 0, 0, 5],
    [5, 2, 2, 5, 5, 1, 1, 5, 5, 5],
]

BBOX_INPUT = [
    [1, 0, 0, 0, 0, 5, 2, 0, 0],
    [0, 5, 5, 5, 5, 5, 0, 0, 0],
    [0, 5, 5, 5, 5, 5, 0, 0, 0],
]


class ParametricProgramsTest(unittest.TestCase):
    def load_programs(self):
        self.assertTrue(PROGRAMS_PATH.is_file(), "the rule implementation is missing")
        spec = importlib.util.spec_from_file_location("majority_programs_under_test", PROGRAMS_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_retain_joined_component_after_fill(self):
        rules = self.load_programs()
        self.assertEqual(rules.evaluate(MERGE_INPUT), FILLED)
        self.assertEqual(rules.evaluate(MERGE_INPUT, "largest_filled_component"), RETAINED)
        self.assertEqual(MERGE_INPUT[1], [0, 0, 1, 0, 0, 5, 0, 0, 0])

    def test_merge_witness_rejects_room_color_and_original_blob_rivals(self):
        rules = self.load_programs()
        for rival in ("largest_room", "largest_color_total", "original_components"):
            with self.subTest(rival=rival):
                self.assertNotEqual(
                    rules.evaluate(MERGE_INPUT, "largest_filled_component", rival=rival),
                    RETAINED,
                )

    def test_all_global_maximum_components_are_retained(self):
        rules = self.load_programs()
        self.assertEqual(
            rules.evaluate([[1, 0, 5, 2, 0, 5, 3]], "largest_filled_component"),
            [[1, 1, 5, 2, 2, 5, 3]],
        )

    def test_votes_count_cardinal_contacts_and_ignore_walls(self):
        rules = self.load_programs()
        self.assertEqual(rules.evaluate([[5, 0, 2]]), [[5, 2, 2]])
        self.assertEqual(rules.evaluate([[5, 0, 5]]), [[5, 0, 5]])
        self.assertEqual(rules.evaluate([[1, 0, 2]]), [[1, 1, 2]])
        self.assertEqual(
            rules.evaluate([[0, 0, 2], [0, 1, 0], [0, 0, 0]]),
            [[1, 1, 2], [1, 1, 1], [1, 1, 1]],
        )

    def test_connected_marker_run_counts_as_three_pixel_votes(self):
        rules = self.load_programs()
        top_left = rules.region_data(CONTACT_INPUT)[0]
        self.assertEqual(top_left["counts"], {1: 3, 2: 2})
        self.assertEqual(top_left["winner"], 1)
        self.assertEqual(rules.evaluate(CONTACT_INPUT)[1][1], 1)
        self.assertEqual(rules.evaluate(CONTACT_INPUT, rival="side_only")[1][1], 2)

    def test_marker_component_rival_reverses_the_pixel_vote(self):
        rules = self.load_programs()
        try:
            output = rules.evaluate(CONTACT_INPUT, rival="marker_components")
        except ValueError as error:
            self.fail(f"the marker-component rival is not implemented: {error}")
        self.assertEqual(output[1][1], 2)
        self.assertEqual(rules.evaluate(CONTACT_INPUT)[1][1], 1)

    def test_bbox_area_does_not_replace_occupied_component_size(self):
        rules = self.load_programs()
        self.assertEqual(
            rules.evaluate(BBOX_INPUT, "largest_filled_component"),
            [[1, 0, 0, 0, 0, 5, 2, 2, 2],
             [0, 5, 5, 5, 5, 5, 2, 2, 2],
             [0, 5, 5, 5, 5, 5, 2, 2, 2]],
        )
        self.assertEqual(
            rules.evaluate(BBOX_INPUT, "largest_filled_component", rival="bbox_size"),
            [[1, 1, 1, 1, 1, 5, 2, 0, 0],
             [1, 5, 5, 5, 5, 5, 0, 0, 0],
             [1, 5, 5, 5, 5, 5, 0, 0, 0]],
        )

    def test_exact_default_preserves_the_registered_examples(self):
        rules = self.load_programs()
        ledger = rules.ROOT / "shared/data/canonical/puzzles.jsonl"
        records = [row for line in ledger.read_text(encoding="utf-8").splitlines()
                   if (row := json.loads(line)).get("task_id") == rules.TASK_ID]
        self.assertTrue(records)
        for record in records:
            self.assertEqual(rules.program({"retention": "all"}), record["program_solution"])
            for pair in record["train"]:
                self.assertEqual(rules.evaluate(pair["input"]), pair["output"])

    @unittest.skipUnless(os.environ.get("RACKET_PATH"), "run through review.py run for protected parity")
    def test_protected_racket_matches_literal_witnesses_and_every_rival(self):
        from arcpuzzles.parametric_worker import _real_evaluator
        rules = self.load_programs()
        apply, identity, bridge = _real_evaluator(rules.ROOT / "shared/runtime")
        self.assertEqual(identity["backend"], "racket")
        self.assertIs(identity["protected"], True)
        try:
            for grid in (MERGE_INPUT, CONTACT_INPUT, BBOX_INPUT,
                         [[1, 0, 5, 2, 0, 5, 3]], [[1, 0, 2]], [[5, 0, 5]],
                         [[0, 0, 2], [0, 1, 0], [0, 0, 0]]):
                for retention in rules.RETENTIONS:
                    for rival in (None, *rules.rivals_for(retention)):
                        with self.subTest(retention=retention, rival=rival, grid=grid):
                            source = (rules.program({"retention": retention}) if rival is None
                                      else rules.rival_program(rival, retention))
                            self.assertEqual(apply(source, grid), rules.evaluate(grid, retention, rival))
        finally:
            bridge.close()

    def test_unknown_settings_and_rivals_are_rejected(self):
        rules = self.load_programs()
        for settings in ({}, {"retention": True}, {"retention": "largest"},
                         {"retention": "all", "extra": 1}):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                rules.program(settings)
        with self.assertRaises(ValueError):
            rules.evaluate(MERGE_INPUT, rival="invented")


if __name__ == "__main__":
    unittest.main()
