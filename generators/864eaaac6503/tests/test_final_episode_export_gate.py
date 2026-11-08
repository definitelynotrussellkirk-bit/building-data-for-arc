"""Finite final-assembly rival-screen tests, independent of label authority."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest

for parent in Path(__file__).resolve().parents:
    for runtime in (parent / "shared/runtime", parent):
        if (runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(runtime))
            break
    else:
        continue
    break
from reviewer_support import find_root
ROOT = find_root(__file__)
SOURCE = ROOT / "generators/864eaaac6503/workspace/export_gate/final_episode_gate.py"


def identity(grid):
    return deepcopy(grid)


def only_three_by_three(grid):
    # Candidate hypothesis only, never an authoritative label source.
    return [list(row) for row in zip(*grid)][::-1] if len(grid) == len(grid[0]) == 3 else deepcopy(grid)


CANONICAL = {"input": [[0, 0, 9], [0, 0, 9], [9, 9, 9]],
             "output": [[9, 9, 9], [0, 0, 9], [0, 0, 9]]}
EXTENDED = {"input": [[1, 2, 3], [4, 5, 6]],
            "output": [[3, 6], [2, 5], [1, 4]]}
RIVALS = {"only_three_by_three": only_three_by_three}
RATIONALE = {"only_three_by_three": "Extended rotation is the declared export domain; 3x3-only behavior is a shortcut to reject."}


class FinalEpisodeExportGate(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SOURCE.is_file(), "final assembled episode export gate is missing")
        spec = importlib.util.spec_from_file_location("final_episode_gate", SOURCE)
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def test_rejects_surviving_rival_with_exact_demo_and_query_indices(self):
        episode = {"train": [deepcopy(CANONICAL)] * 3, "test": [deepcopy(EXTENDED)]}
        result = self.mod.screen_episode(episode, RIVALS, rationale=RATIONALE)
        self.assertFalse(result["allowed"])
        self.assertEqual(result["checks"][0]["demo_indices"], [0, 1, 2])
        self.assertEqual(result["checks"][0]["rivals"]["only_three_by_three"]["disagreeing_query_indices"], [3])
        self.assertEqual(result["examples"][3], {"split": "test", "index": 0})

    def test_final_demo_witness_refutes_shortcut(self):
        episode = {"train": [deepcopy(CANONICAL), deepcopy(EXTENDED)], "test": [deepcopy(CANONICAL)]}
        result = self.mod.screen_episode(episode, RIVALS, rationale=RATIONALE)
        self.assertTrue(result["allowed"])
        self.assertFalse(result["checks"][0]["rivals"]["only_three_by_three"]["fits_all_demos"])

    def test_rotation_is_explicit_and_can_reveal_lost_witness(self):
        episode = {"train": [deepcopy(CANONICAL), deepcopy(EXTENDED)], "test": [deepcopy(CANONICAL)]}
        normal = self.mod.screen_episode(episode, RIVALS, rationale=RATIONALE)
        rotated = self.mod.screen_episode(episode, RIVALS, rationale=RATIONALE, query_rotation=True)
        self.assertEqual(len(normal["checks"]), 1)
        self.assertEqual(len(rotated["checks"]), 3)
        self.assertFalse(rotated["allowed"])
        self.assertEqual([c["query_indices"] for c in rotated["checks"] if c["violations"]], [[1]])

    def test_two_informative_pairs_survive_every_query_rotation(self):
        episode = {"train": [deepcopy(CANONICAL), deepcopy(EXTENDED)], "test": [deepcopy(EXTENDED)]}
        result = self.mod.screen_episode(episode, RIVALS, rationale=RATIONALE, query_rotation=True)
        self.assertTrue(result["allowed"])
        self.assertEqual(len(result["checks"]), 3)

    def test_all_existing_queries_are_screened_without_rotating_demos(self):
        episode = {"train": [deepcopy(CANONICAL)], "test": [deepcopy(CANONICAL), deepcopy(EXTENDED)]}
        result = self.mod.screen_episode(episode, RIVALS, rationale=RATIONALE)
        self.assertEqual(result["checks"][0]["rivals"]["only_three_by_three"]["disagreeing_query_indices"], [2])
        self.assertEqual(len(result["checks"]), 1)

    def test_rival_errors_and_mutation_fail_closed(self):
        def raises(grid):
            raise RuntimeError("candidate failed")
        def mutates(grid):
            grid[0][0] = 8
            return grid
        episode = {"train": [deepcopy(CANONICAL)], "test": [deepcopy(EXTENDED)]}
        saved = deepcopy(episode)
        for name, fn in (("raises", raises), ("mutates", mutates)):
            result = self.mod.screen_episode(episode, {name: fn}, rationale={name: "Explicit diagnostic rival"})
            self.assertFalse(result["allowed"])
            self.assertTrue(result["checks"][0]["errors"])
            self.assertEqual(episode, saved)

    def test_no_rival_or_missing_rationale_or_query_labels_cannot_pass(self):
        episode = {"train": [deepcopy(CANONICAL)], "test": [deepcopy(EXTENDED)]}
        for rivals, rationale in (({}, {}), (RIVALS, {})):
            with self.assertRaises(ValueError):
                self.mod.screen_episode(episode, rivals, rationale=rationale)
        del episode["test"][0]["output"]
        with self.assertRaises(ValueError):
            self.mod.screen_episode(episode, RIVALS, rationale=RATIONALE)

    def test_agreement_with_query_does_not_verify_authoritative_labels(self):
        # Even a knowingly wrong labelled episode can pass this finite screen:
        # reference correctness is a separate export prerequisite.
        episode = {"train": [{"input": [[1, 2]], "output": [[1, 2]]}],
                   "test": [{"input": [[3, 4]], "output": [[3, 4]]}]}
        result = self.mod.screen_episode(episode, {"identity": identity}, rationale={"identity": "Diagnostic test"})
        self.assertTrue(result["allowed"])
        self.assertFalse(result["reference_labels_verified"])


if __name__ == "__main__":
    unittest.main()
