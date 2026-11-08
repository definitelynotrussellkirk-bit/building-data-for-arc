"""Input-branch support regressions; canonical labeling remains with Racket.

Output copies below are opaque fixtures for the worker's labeled-pair interface,
not claims about the reference transformation. This guard checks input coverage;
the retained Racket audit separately establishes the seed-10 answer disagreement.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import unittest

from arcpuzzles.worker import lesson_check
from reviewer_support import find_root, load_selected_generator


TASK_ID = "1f3e27c86f7a"
ROOT = find_root(__file__)
GENERATOR, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def input_pair(grid):
    """Provide opaque, shape-valid labels without implementing another oracle."""
    return {"input": grid, "output": deepcopy(grid)}


class HiddenQueryOutput(dict):
    """Make accidental access to a private query answer observable."""

    def __getitem__(self, key):
        if key == "output":
            raise AssertionError("the lesson guard read the hidden query output")
        return super().__getitem__(key)

    def get(self, key, default=None):
        if key == "output":
            raise AssertionError("the lesson guard read the hidden query output")
        return super().get(key, default)


class LessonGuard1f3e27c86f7aTests(unittest.TestCase):
    def guard(self, demos, query):
        hook = getattr(GENERATOR, "lesson_identifiable", None)
        self.assertTrue(callable(hook), "the generator must declare a lesson support guard")
        reasons = hook(demos, query)
        self.assertIsInstance(reasons, list)
        self.assertTrue(all(isinstance(reason, str) for reason in reasons))
        return reasons

    def branch_pair(self, branch, *, seed=31, sample_index=41):
        grid = GENERATOR.generate(seed, sample_index, difficulty="medium", rule_branch=branch)
        return input_pair(grid)

    def retained_episode(self):
        pairs = [input_pair(GENERATOR.generate(10, index, difficulty="medium")) for index in range(5)]
        return {"train": pairs[:4], "test": pairs[4:]}

    def test_seed10_all_stripe_demos_do_not_support_bottom_align_query(self):
        episode = self.retained_episode()
        pairs = episode["train"] + episode["test"]
        self.assertEqual(
            ["stripe", "stripe", "stripe", "stripe", "bottom_align"],
            [GENERATOR.observe_overrides(pair["input"])["rule_branch"] for pair in pairs],
        )
        self.assertTrue(all(GENERATOR.self_check(pair["input"]) == [] for pair in pairs))
        reasons = self.guard(episode["train"], episode["test"][0])
        self.assertTrue(reasons)
        self.assertIn("bottom_align", " ".join(reasons))

    def test_each_branch_is_supported_by_a_distinct_same_branch_demonstration(self):
        for branch in GENERATOR.BRANCHES:
            with self.subTest(branch=branch):
                demo = self.branch_pair(branch)
                query = self.branch_pair(branch, seed=37, sample_index=43)
                self.assertNotEqual(demo["input"], query["input"])
                self.assertEqual([], self.guard([demo], query))

    def test_every_branch_is_rejected_when_only_other_branches_are_demonstrated(self):
        for branch in GENERATOR.BRANCHES:
            with self.subTest(branch=branch):
                demos = [self.branch_pair(other) for other in GENERATOR.BRANCHES if other != branch]
                reasons = self.guard(demos, self.branch_pair(branch, seed=37, sample_index=43))
                self.assertTrue(reasons)
                self.assertIn(branch, " ".join(reasons))

    def test_query_output_can_be_absent_masked_or_arbitrary(self):
        demo = self.branch_pair("stripe")
        for branch, supported in (("stripe", True), ("bottom_align", False)):
            with self.subTest(branch=branch):
                grid = self.branch_pair(branch, seed=37, sample_index=43)["input"]
                visible = {"input": grid}
                expected = self.guard([demo], visible)
                self.assertEqual(supported, not expected)
                for output in (None, [], [[9]], {"private": "unavailable"}):
                    query = {"input": grid, "output": output}
                    self.assertEqual(expected, self.guard([demo], query))
                self.assertEqual(expected, self.guard([demo], HiddenQueryOutput(visible)))

    def test_guard_does_not_mutate_demonstrations_or_query(self):
        for query_branch in ("stripe", "bottom_align"):
            with self.subTest(branch=query_branch):
                demos = [self.branch_pair("stripe")]
                query = self.branch_pair(query_branch, seed=37, sample_index=43)
                before = deepcopy((demos, query))
                self.guard(demos, query)
                self.assertEqual(before, (demos, query))

    def test_invalid_query_and_demonstration_inputs_fail_closed(self):
        valid = self.branch_pair("stripe")
        ragged = deepcopy(valid["input"])
        ragged[0].pop()
        boolean = deepcopy(valid["input"])
        boolean[0][0] = True
        outside_palette = deepcopy(valid["input"])
        outside_palette[0][0] = 10
        invalid = (None, [], [[]], [[1]], ["12345678"] * 8,
                   ragged, boolean, outside_palette, [[0] * 8 for _ in range(8)])
        for index, grid in enumerate(invalid):
            with self.subTest(index=index, split="query"):
                self.assertTrue(self.guard([valid], {"input": grid}))
            with self.subTest(index=index, split="demo"):
                # A valid witness does not hide another malformed demonstration.
                self.assertTrue(self.guard([valid, {"input": grid}], valid))

    def test_missing_pairs_and_empty_demonstrations_fail_closed(self):
        valid = self.branch_pair("stripe")
        for demos, query in (([], valid), (None, valid), ({}, valid),
                             ([valid], None), ([valid], {}),
                             ([None, valid], valid), ([{}, valid], valid)):
            with self.subTest(demos_type=type(demos).__name__, query_type=type(query).__name__):
                self.assertTrue(self.guard(demos, query))

    def test_worker_rejects_automatic_unsupported_lesson(self):
        episode = self.retained_episode()
        before = deepcopy(episode)
        request = {"demonstration_policy": {"automatic": True, "declared_minimum": 4}}
        with self.assertRaisesRegex(ValueError, "Automatic lesson unsupported.*bottom_align"):
            lesson_check(GENERATOR, episode, request)
        self.assertEqual(before, episode)

    def test_worker_retains_explicit_unsupported_lesson_diagnostic(self):
        episode = self.retained_episode()
        before = deepcopy(episode)
        request = {"demonstration_policy": {"automatic": False, "declared_minimum": 4}}
        verdict = lesson_check(GENERATOR, episode, request)
        self.assertEqual("diagnostic_unsupported", verdict["status"])
        self.assertEqual("hook_only", verdict["contract"])
        self.assertIn("bottom_align", " ".join(verdict["queries"][0]["reasons"]))
        self.assertEqual(before, episode)

    def test_pointwise_draws_match_the_pre_guard_source(self):
        cases = [(10, index, "medium", {}) for index in range(5)]
        cases.extend((31, 41, band, {"rule_branch": branch})
                     for band in ("easy", "medium", "hard") for branch in GENERATOR.BRANCHES)
        values = [{"seed": seed, "sample_index": index, "difficulty": band,
                   "overrides": overrides,
                   "input": GENERATOR.generate(seed, index, difficulty=band, **overrides)}
                  for seed, index, band, overrides in cases]
        digest = hashlib.sha256(json.dumps(values, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual("788dc7c1114430d0eef029b968f9fecec08b0bac42d8cdd3258795df756cd686", digest)


if __name__ == "__main__":
    unittest.main()
