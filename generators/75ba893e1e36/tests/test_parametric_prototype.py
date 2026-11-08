"""Portable unittest tests for the PROPOSED parametric prototype only.

These do not test or import the selected production generator. Canonical labels
are authoring data, used only after the separate blind solve. No pytest dependency.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import canonical_pairs, canonical_path, find_root

ROOT = find_root(__file__)
PROTOTYPE = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"
SPEC = importlib.util.spec_from_file_location("tile75_parametric_prototype", PROTOTYPE)
assert SPEC and SPEC.loader
proto = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(proto)


class TestPrototypeContract(unittest.TestCase):
    def test_seed_schedule_inputs_and_parameter_bounds(self):
        self.assertEqual(proto.DEFAULT_PARAMETERS, ("mirror", 2))
        self.assertEqual(proto.choose_parameters(proto.DEFAULT_SEED), proto.DEFAULT_PARAMETERS)
        self.assertEqual({proto.choose_parameters(seed) for seed in range(6)}, set(proto.SETTINGS))
        self.assertEqual(len({proto.program_for(*setting) for setting in proto.SETTINGS}), 6)
        for invalid in (-1, True, 2.0, "2"):
            with self.assertRaises(ValueError):
                proto.choose_parameters(invalid)
        for first, pairs in (("vertical", 2), ("mirror", 0), ("input", 4), ("mirror", True)):
            with self.assertRaises(ValueError):
                proto.program_for(first, pairs)
        for seed in (0, 1, 5, 6, 17):
            inputs = proto.episode_inputs(seed)
            self.assertEqual(inputs, proto.episode_inputs(seed))
            self.assertEqual(len(inputs), 4)
            self.assertEqual(len({json.dumps(grid) for grid in inputs}), 4)
            self.assertTrue(all(proto.validate_input(grid) == grid for grid in inputs))
        self.assertTrue(all(proto.episode_inputs(seed) == proto.episode_inputs(0) for seed in range(6)))
        with self.assertRaises(ValueError):
            proto.validate_input([[5, 7, 5], [7, 8, 7], [8, 5, 8]])
        # Canonical train[3] is a lawful two-color input: presence of all three
        # allowed colors is a witness sampling choice, not a rule precondition.
        two_color = [[7, 5, 7], [5, 5, 7], [7, 7, 5]]
        self.assertEqual(proto.validate_input(two_color), two_color)


class TestPrototypeRuntime(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        status = racket_runtime_status()
        if not status["available"]:
            raise unittest.SkipTest("Optional Racket runtime unavailable: " + status["reason"])
        cls.bridge = RacketBridge(timeout=10.0, startup_timeout=30.0)
        cls.addClassCleanup(cls.bridge.shutdown)
        cls.episodes = [proto.build_episode(seed, cls.bridge) for seed in range(6)]

    def test_every_setting_executes_one_complete_episode(self):
        for seed, episode in enumerate(self.episodes):
            setting = proto.choose_parameters(seed)
            self.assertEqual(episode["parameters"], {"first_tile": setting[0], "tile_pairs": setting[1]})
            self.assertEqual(episode["program"], proto.program_for(*setting))
            self.assertEqual((len(episode["train"]), len(episode["test"])), (3, 1))
            self.assertEqual(episode["seed"], seed)
            for pair in episode["train"] + episode["test"]:
                self.assertEqual(len(pair["output"]), 3)
                self.assertEqual(len(pair["output"][0]), 6 * setting[1])
                self.assertLessEqual(len(pair["output"][0]), 30)
                self.assertEqual({cell for row in pair["output"] for cell in row}, {5, 7, 8})

    def test_each_demo_identifies_its_setting_among_all_six(self):
        # All settings were run by Racket on the same lawful input witnesses.
        for chosen in self.episodes:
            for rival in self.episodes:
                if chosen["parameters"] == rival["parameters"]:
                    continue
                for index in range(3):
                    self.assertEqual(chosen["train"][index]["input"], rival["train"][index]["input"])
                    self.assertNotEqual(chosen["train"][index]["output"], rival["train"][index]["output"])
                self.assertNotEqual(chosen["test"][0]["output"], rival["test"][0]["output"])

    def test_original_program_and_execution_agree_with_all_canonical_pairs(self):
        program = proto.program_for(*proto.DEFAULT_PARAMETERS)
        authority = []
        with canonical_path(ROOT).open(encoding="utf-8") as stream:
            for line in stream:
                if line.strip():
                    row = json.loads(line)
                    if row.get("task_id") == proto.TASK_ID:
                        authority.append(row["program_solution"])
        self.assertEqual(authority, [program])
        pairs = canonical_pairs(proto.TASK_ID, root=ROOT, labeled_only=True)
        self.assertEqual(len(pairs), 5)
        for pair in pairs:
            self.assertEqual(proto.execute_program(self.bridge, program, pair["input"]), pair["output"])

    def test_public_challenges_omit_hidden_metadata_and_query_answers(self):
        for episode in self.episodes:
            public = proto.public_challenge(episode)
            self.assertEqual(set(public), {"train", "test"})
            self.assertTrue(all(set(pair) == {"input", "output"} for pair in public["train"]))
            self.assertTrue(all(set(pair) == {"input"} for pair in public["test"]))
            self.assertEqual((len(public["train"]), len(public["test"])), (3, 1))
            original_cell = episode["test"][0]["input"][0][0]
            public["test"][0]["input"][0][0] = 0
            self.assertEqual(episode["test"][0]["input"][0][0], original_cell)


if __name__ == "__main__":
    unittest.main(verbosity=2)
