"""Focused tests for the proposed, task-local questions gate (stdlib only)."""
from __future__ import annotations

import copy
import importlib.util
import json
from collections import Counter
from pathlib import Path
import unittest

TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[1]
SPEC = importlib.util.spec_from_file_location(
    "column_fall_question_gate", TASK_ROOT / "workspace/questions/question_gate.py"
)
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


def canonical_row():
    for line in (REPO_ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == "6fde852adb54" and row.get("source") == "training":
            return row
    raise AssertionError("canonical task is missing")


class QuestionGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = canonical_row()
        cls.demos = cls.row["train"]
        cls.witness = gate.make_witness()
        cls.predict = staticmethod(gate.GENERATOR.rule_mirror)

    def assess(self, demos, query):
        return gate.lesson_gate(demos, query, canonical_predict=self.predict)

    def test_witness_is_lawful_and_exposes_count_versus_run(self):
        self.assertEqual([], gate.GENERATOR.self_check(self.witness))
        facts = gate.GENERATOR._parse(self.witness)["facts"]
        component = next(c for c in facts["obstacle_components"] if (13, 5) in c)
        self.assertEqual({5: 3, 6: 4, 7: 3}, dict(Counter(c for _, c in component)))
        self.assertEqual({5: 3, 6: 2, 7: 3}, gate.column_run_lengths(component))
        expected = self.predict(self.witness)
        rival = gate.rival_predict(self.witness)
        self.assertEqual(6, gate.difference_cells(expected, rival))
        self.assertEqual([9, 9, 9], [expected[r][6] for r in (11, 12, 13)])
        self.assertEqual([9, 9, 9], [rival[r][5] for r in (11, 12, 13)])

    def test_rival_fits_all_three_canonical_demonstrations(self):
        for pair in self.demos:
            self.assertEqual(pair["output"], gate.rival_predict(pair["input"]))

    def test_ambiguous_lesson_is_rejected(self):
        report = self.assess(self.demos, {"input": self.witness})
        self.assertEqual("ambiguous", report["status"])
        self.assertEqual([True, True, True], report["demo_matches"])
        self.assertEqual(6, report["query_difference_cells"])

    def test_query_output_is_never_read(self):
        class SealedQuery(dict):
            def __getitem__(self, key):
                if key == "output":
                    raise AssertionError("held-out output was read")
                return super().__getitem__(key)

            def get(self, key, *args):
                if key == "output":
                    raise AssertionError("held-out output was read")
                return super().get(key, *args)

        expected = self.assess(self.demos, {"input": self.witness})
        self.assertEqual(expected, self.assess(self.demos, SealedQuery(
            input=self.witness, output=object(), private_answer="deliberately wrong"
        )))
        self.assertEqual(expected, self.assess(self.demos, {
            "input": self.witness, "output": [[False]],
        }))

    def test_surviving_but_answer_equivalent_rival_is_accepted(self):
        report = self.assess(self.demos, {"input": self.row["test"][0]["input"]})
        self.assertEqual("pass", report["status"])
        self.assertEqual([True, True, True], report["demo_matches"])
        self.assertEqual(0, report["query_difference_cells"])

    def test_one_discriminating_demo_repairs_the_lesson(self):
        extra = {"input": self.witness, "output": self.predict(self.witness)}
        query = gate.make_witness(height=16, width=18, start=6, reflected=True)
        report = self.assess(self.demos + [extra], {"input": query})
        self.assertNotEqual(self.witness, query)
        self.assertEqual("pass", report["status"])
        self.assertEqual([True, True, True, False], report["demo_matches"])
        self.assertEqual(6, report["query_difference_cells"])

    def test_invalid_query_is_rejected_without_reference_call(self):
        def forbidden(_):
            raise AssertionError("invalid query should be rejected first")
        for query in ({}, {"input": []}, {"input": [[7] * 14]},
                      {"input": [[7, 9, 1, 5]]}, {"input": [[False] * 14] * 14}):
            report = gate.lesson_gate(self.demos, query, canonical_predict=forbidden)
            self.assertEqual("invalid", report["status"])

    def test_wrong_demo_label_and_reference_error_do_not_pass(self):
        demos = copy.deepcopy(self.demos)
        demos[0]["output"][0][0] = 0
        self.assertEqual("invalid", self.assess(demos, {"input": self.witness})["status"])
        def broken(_):
            raise RuntimeError("reference unavailable")
        report = gate.lesson_gate(self.demos, {"input": self.witness}, canonical_predict=broken)
        self.assertEqual("reference_error", report["status"])

    def test_sampler_is_deterministic_and_draws_real_counterexamples(self):
        for sample_index in range(4):
            first = gate.sample_witness(17, sample_index)
            before = copy.deepcopy(first)
            second = gate.sample_witness(17, sample_index)
            self.assertEqual(first, second)
            self.assertIsNot(first, second)
            self.assertEqual([], gate.GENERATOR.self_check(first))
            self.assertEqual(6, gate.difference_cells(self.predict(first), gate.rival_predict(first)))
            gate.rival_predict(first)
            self.assess(self.demos, {"input": first})
            self.assertEqual(before, first)

    def test_witness_sampler_rejects_unsupported_boundaries(self):
        for kwargs in ({"height": 13}, {"width": 25}, {"start": 1},
                       {"height": True}, {"palette": (7, 9, 1, 1)},
                       {"palette": (False, 9, 1, 5)}, {"reflected": 1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                gate.make_witness(**kwargs)
        for args in ((True, 0), (17, -1), (17, "0")):
            with self.subTest(args=args), self.assertRaises(ValueError):
                gate.sample_witness(*args)


if __name__ == "__main__":
    unittest.main()
