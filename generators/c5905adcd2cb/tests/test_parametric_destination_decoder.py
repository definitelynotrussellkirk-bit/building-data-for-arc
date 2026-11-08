"""Focused tests for the proposed destination-decoder prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import unittest

for _parent in Path(__file__).resolve().parents:
    for _runtime in (_parent / "shared/runtime", _parent):
        if (_runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(_runtime))
            break
    else:
        continue
    break

from reviewer_support import canonical_path, find_root

ROOT = find_root(__file__)
SOURCE = ROOT / "generators/c5905adcd2cb/workspace/parametric/destination_decoder_episodes.py"


class PrototypeAvailability(unittest.TestCase):
    def test_prototype_exists(self):
        self.assertTrue(SOURCE.is_file(), "the requested runnable prototype is missing")


@unittest.skipUnless(SOURCE.is_file(), "prototype not implemented yet")
class DestinationDecoderPrototype(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("destination_decoder_episodes", SOURCE)
        cls.mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(cls.mod)
        cls.bridge = cls.mod.open_bridge()

    @classmethod
    def tearDownClass(cls):
        cls.bridge.shutdown()

    def canonical_program(self):
        for line in canonical_path(ROOT).read_text().splitlines():
            row = json.loads(line)
            if row.get("task_id") == "c5905adcd2cb" and row.get("source") == "training":
                return row["program_solution"]
        self.fail("canonical training authority missing")

    def test_direct_setting_is_exact_canonical_authority(self):
        programs = self.mod.programs()
        self.assertEqual(self.mod.DEFAULT_DESTINATION_DECODER, "direct")
        self.assertEqual(programs["direct"], self.canonical_program())
        self.assertNotEqual(programs["direct"], programs["transpose"])

    def test_reference_programs_disagree_on_off_diagonal_destination(self):
        episode = self.mod.build_episode(
            self.bridge, seed=9, destination_decoder="direct", n_train=3, n_test=2
        )
        witness = next(
            pair["input"] for pair in episode["train"]
            if self.mod.destination_coordinates(pair["input"])[0]
            != self.mod.destination_coordinates(pair["input"])[1]
        )
        outputs = {
            setting: self.mod.execute(self.bridge, setting, [witness])[0]
            for setting in self.mod.ALLOWED_DESTINATION_DECODERS
        }
        self.assertNotEqual(outputs["direct"], outputs["transpose"])

    def test_seed_is_reproducible_and_parameter_is_episode_fixed(self):
        seen = set()
        for seed in (0, 1):
            first = self.mod.build_episode(self.bridge, seed=seed)
            second = self.mod.build_episode(self.bridge, seed=seed)
            self.assertEqual(first, second)
            self.assertEqual(len(first["train"]), 3)
            self.assertEqual(len(first["test"]), 2)
            seen.add(first["destination_decoder"])
            pairs = first["train"] + first["test"]
            actual = self.mod.execute(
                self.bridge,
                first["destination_decoder"],
                [pair["input"] for pair in pairs],
            )
            self.assertEqual(actual, [pair["output"] for pair in pairs])
            self.assertEqual(
                first["rival_check"]["demo_survivors"],
                [first["destination_decoder"]],
            )
            self.assertTrue(first["rival_check"]["identifiable_from_demos"])
        self.assertEqual(seen, set(self.mod.ALLOWED_DESTINATION_DECODERS))

    def test_explicit_setting_switch_preserves_inputs_but_changes_labels(self):
        direct = self.mod.build_episode(self.bridge, seed=21, destination_decoder="direct")
        transposed = self.mod.build_episode(self.bridge, seed=21, destination_decoder="transpose")
        direct_pairs = direct["train"] + direct["test"]
        transposed_pairs = transposed["train"] + transposed["test"]
        self.assertEqual(
            [pair["input"] for pair in direct_pairs],
            [pair["input"] for pair in transposed_pairs],
        )
        self.assertTrue(any(
            left["output"] != right["output"]
            for left, right in zip(direct_pairs, transposed_pairs)
        ))

    def test_public_challenge_omits_hidden_setting_code_and_query_answers(self):
        episode = self.mod.build_episode(self.bridge, seed=0)
        challenge = self.mod.public_challenge(episode)
        self.assertEqual(set(challenge), {"train", "test"})
        self.assertTrue(all(set(pair) == {"input", "output"} for pair in challenge["train"]))
        self.assertTrue(all(set(pair) == {"input"} for pair in challenge["test"]))
        challenge["train"][0]["input"][0][0] = 99
        self.assertNotEqual(challenge["train"][0]["input"], episode["train"][0]["input"])

    def test_invalid_parameters_fail_closed(self):
        for kwargs in (
            {"seed": True},
            {"seed": 1.0},
            {"seed": 1, "n_train": 0},
            {"seed": 1, "n_test": 0},
            {"seed": 1, "destination_decoder": "diagonal"},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises((TypeError, ValueError)):
                self.mod.build_episode(self.bridge, **kwargs)


if __name__ == "__main__":
    unittest.main()
