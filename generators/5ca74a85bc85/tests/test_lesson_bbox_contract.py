"""Portable regressions for the source-bound filled-bounding-box audit."""
import copy
import unittest

from reviewer_support import find_root, load_selected_generator
from arcpuzzles.worker import lesson_check

MODULE, SOURCE, SOURCE_HASH = load_selected_generator("5ca74a85bc85", root=find_root(__file__))


def audited_episode():
    grids = [MODULE.generate(0, index) for index in (3, 4, 5, 6)]
    pairs = [{"input": grid, "output": MODULE.rule_mirror(grid)} for grid in grids]
    return {"train": pairs[:3], "test": pairs[3:]}


class BboxLessonContractTests(unittest.TestCase):
    def test_automatic_generation_rejects_audited_ambiguity(self):
        episode = audited_episode()
        before = copy.deepcopy(episode)
        with self.assertRaisesRegex(ValueError, "filled_source_bbox.*fits every demo"):
            lesson_check(MODULE, episode, {"demonstration_policy": {
                "automatic": True, "declared_minimum": None}})
        self.assertEqual(episode, before)

    def test_explicit_counts_retain_audited_diagnostic(self):
        verdict = lesson_check(MODULE, audited_episode(), {"demonstration_policy": {
            "automatic": False, "declared_minimum": None}})
        self.assertEqual(verdict["status"], "diagnostic_unsupported")
        self.assertEqual(verdict["rivals"], {"LESSON_COMPETITORS:filled_source_bbox": "ambiguous"})

    def test_sparse_demonstration_refutes_rival(self):
        episode = audited_episode()
        episode["train"].append(copy.deepcopy(episode["test"][0]))
        verdict = lesson_check(MODULE, episode, {"demonstration_policy": {
            "automatic": True, "declared_minimum": None}})
        self.assertEqual(verdict["status"], "passed_declared_rivals")
        self.assertEqual(verdict["rivals"], {"LESSON_COMPETITORS:filled_source_bbox": "refuted"})

    def test_rival_is_pure_total_and_deterministic_on_declared_profiles(self):
        rival = MODULE.LESSON_COMPETITORS["filled_source_bbox"]
        for profile in MODULE.SCENE_PROFILES:
            grid = MODULE.generate(83, 103, scene_profile=profile)
            before = copy.deepcopy(grid)
            first = rival(grid)
            self.assertEqual(grid, before)
            self.assertEqual(first, rival(grid))
            self.assertIsNot(first, grid)
            self.assertTrue(all(a is not b for a, b in zip(first, grid)))
            self.assertEqual((len(first), len(first[0])), (len(grid), len(grid[0])))


if __name__ == "__main__":
    unittest.main()
