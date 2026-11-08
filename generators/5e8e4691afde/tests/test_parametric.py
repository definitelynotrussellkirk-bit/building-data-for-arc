"""Focused tests of the separate proposed rotation/scale prototype only."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import tempfile
import unittest
from unittest import mock


SOURCE = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"
SPEC = importlib.util.spec_from_file_location("arc_5e8e4691afde_parametric", SOURCE)
PROTOTYPE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROTOTYPE
SPEC.loader.exec_module(PROTOTYPE)
P = PROTOTYPE


class ControlsAndSamplingTests(unittest.TestCase):
    def test_invalid_parameters(self):
        for value in (True, False, -1, 4, 1.0, "1", None):
            with self.subTest(quarter_turns=value), self.assertRaises(ValueError):
                P.Setting(quarter_turns=value)
        for value in (True, False, -1, 0, 3, 1.0, "1", None):
            with self.subTest(distance_scale=value), self.assertRaises(ValueError):
                P.Setting(distance_scale=value)
        with self.assertRaises(ValueError):
            P.program_for({"quarter_turns": 0, "distance_scale": 1})

    def test_invalid_sampling_controls(self):
        for name in ("demos", "queries", "max_attempts"):
            for value in (True, False, 0, -1, 1.5, "4", None, 100001):
                with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                    P.sample_inputs(17, **{name: value})
        for name in ("seed", "episode_index"):
            for value in (True, False, -1, 1.0, "17", None, 2**64):
                kwargs = {"seed": 17, "episode_index": 0, name: value}
                with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                    P.sample_inputs(**kwargs)

    def test_finite_rejection(self):
        with mock.patch.object(P, "_draw_scene", return_value=None) as draw:
            with self.assertRaisesRegex(P.SamplingError, "0/7 inputs after 9/9 attempts"):
                P.sample_inputs(17, max_attempts=9)
            self.assertEqual(draw.call_count, 9)

    def test_determinism_freshness_rng_uniqueness_and_sizes(self):
        random.seed(999)
        state = random.getstate()
        first = P.sample_inputs(17, demos=2, queries=4)
        second = P.sample_inputs(17, demos=2, queries=4)
        self.assertEqual(random.getstate(), state)
        self.assertEqual(first, second)
        self.assertIsNot(first[0][0], second[0][0])
        self.assertIsNot(first[0][0][0], second[0][0][0])
        demos, queries, receipt = first
        self.assertEqual((len(demos), len(queries)), (2, 4))
        self.assertEqual(len({P.grid_id(g) for g in demos + queries}), 6)
        self.assertEqual((len(queries[0]), len(queries[0][0])), (30, 30))
        for grid in queries:
            self.assertGreater(len(grid), max(map(len, demos)))
            self.assertGreater(len(grid[0]), max(len(g[0]) for g in demos))
        self.assertEqual(receipt["attempts"] - receipt["rejections"], 6)
        self.assertNotEqual(P.sample_inputs(17, 1)[0], first[0])
        self.assertEqual(P.sampled_setting(17), P.sampled_setting(17))
        extra_demos, extra_queries, _ = P.sample_inputs(23, demos=1, queries=5)
        self.assertEqual((len(extra_demos), len(extra_queries)), (1, 5))
        self.assertEqual(len({P.grid_id(g) for g in extra_demos + extra_queries}), 6)

    def test_all_candidates_lawful_and_demonstrations_identify(self):
        demos, queries, _ = P.sample_inputs(31, demos=1, queries=4)
        for grid in demos + queries:
            info = P.scene_info(grid)
            predictions = []
            for setting in P.SETTINGS:
                nr, nc = P.target_center(info, setting)
                self.assertTrue(1 <= nr < len(grid) - 1 and 1 <= nc < len(grid[0]) - 1)
                predictions.append(P.grid_id(P.mirror(grid, setting)))
            self.assertEqual(len(set(predictions)), 8)
        for setting in P.SETTINGS:
            train = [{"input": g, "output": P.mirror(g, setting)} for g in demos]
            self.assertEqual(P.fit_candidates(train), (setting,))
        with self.assertRaises(ValueError):
            P.fit_candidates([])

    def test_cli_invalid_controls_fail_before_racket_or_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "absent"
            invalid = [
                ["--demos", "0"], ["--queries", "-1"], ["--seed", "-1"],
                ["--quarter-turns", "4"], ["--distance-scale", "3"],
                ["--count", "0"], ["--max-attempts", "0"],
                ["--sample-settings", "--distance-scale", "1"],
                ["--all-settings", "--quarter-turns", "0"],
            ]
            with mock.patch.object(P, "RacketLabeler") as labeler, mock.patch("sys.stderr"):
                for args in invalid:
                    with self.subTest(args=args), self.assertRaises(SystemExit) as exit_context:
                        P.main(["--out", str(output), *args])
                    self.assertEqual(exit_context.exception.code, 2)
                labeler.assert_not_called()
            self.assertFalse(output.exists())


class RacketPrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.labeler = P.RacketLabeler()
        cls.episodes = [P.make_episode(cls.labeler, 17, setting=setting, demos=2, queries=4)
                        for setting in P.SETTINGS]

    @classmethod
    def tearDownClass(cls):
        cls.labeler.bridge.shutdown()

    def test_default_is_exact_canonical_and_all_five_labels_match(self):
        canonical = P.canonical_row()
        self.assertEqual(P.program_for(), canonical["program_solution"])
        pairs = canonical["train"] + canonical["test"]
        self.assertEqual(len(pairs), 5)
        outputs = self.labeler.outputs(P.program_for(), [pair["input"] for pair in pairs])
        self.assertEqual(outputs, [pair["output"] for pair in pairs])
        self.assertEqual(outputs, [P.mirror(pair["input"]) for pair in pairs])
        self.assertEqual(len({P.program_for(setting) for setting in P.SETTINGS}), 8)
        self.assertEqual(len(P.verify_canonical_default(self.labeler)), 5)

    def test_all_eight_settings_execute_with_four_identified_queries(self):
        for setting, episode in zip(P.SETTINGS, self.episodes):
            self.assertEqual(episode["settings"], setting.as_dict())
            self.assertEqual(len(episode["train"]), 2)
            self.assertEqual(len(episode["test"]), 4)
            self.assertEqual(episode["identifiability"]["survivors"], [setting.as_dict()])
            self.assertEqual(episode["identifiability"]["fit_uses"], "demonstration_inputs_and_outputs_only")
            self.assertEqual(len(episode["identifiability"]["eliminations"]), 8)
            self.assertTrue(all(check["surviving_prediction_count"] == 1
                                for check in episode["identifiability"]["queries"]))
            inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
            self.assertEqual(len({P.grid_id(g) for g in inputs}), 6)
            self.assertEqual([pair["output"] for pair in episode["train"] + episode["test"]],
                             [P.mirror(g, setting) for g in inputs])
        self.assertTrue(self.labeler.bridge.runtime_identity["protected"])
        self.assertEqual(self.episodes[0], P.make_episode(self.labeler, 17, demos=2, queries=4))
        # Identical layouts across settings prevent a hidden-setting input cue.
        inputs = [[pair["input"] for pair in ep["train"] + ep["test"]] for ep in self.episodes]
        self.assertTrue(all(grids == inputs[0] for grids in inputs))
        other_counts = P.make_episode(self.labeler, 17, setting=P.Setting(1, 2), demos=1, queries=2)
        self.assertEqual((len(other_counts["train"]), len(other_counts["test"])), (1, 2))

    def test_public_writer_is_racket_backed_sorted_isolated_and_content_named(self):
        witness = P.difference_witness(self.labeler, self.episodes[0]["train"][0]["input"])
        self.assertNotEqual(witness["settings"][0]["output"], witness["settings"][1]["output"])
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "export"
            write_order = []
            real_write = Path.write_bytes

            def record_write(path, data):
                if path.parent.name == "public":
                    write_order.append(path.name)
                return real_write(path, data)

            with mock.patch.object(Path, "write_bytes", autospec=True, side_effect=record_write):
                manifest = P.write_export(destination, list(reversed(self.episodes)), witness=witness,
                                          runtime_identity=self.labeler.bridge.runtime_identity,
                                          command="focused unittest")
            ids = [P.public_challenge_id(ep) for ep in self.episodes]
            self.assertEqual(manifest["public_ids"], sorted(ids))
            self.assertEqual(write_order, [identifier + ".json" for identifier in sorted(ids)])
            self.assertEqual(sorted(path.name for path in (destination / "public").iterdir()),
                             [identifier + ".json" for identifier in sorted(ids)])
            self.assertEqual(len(list((destination / "private/programs").glob("*.rkt"))), 8)
            for episode in self.episodes:
                identifier = P.public_challenge_id(episode)
                payload = (destination / "public" / f"{identifier}.json").read_bytes()
                self.assertEqual(hashlib.sha256(payload).hexdigest(), identifier)
                self.assertEqual(payload, P.public_challenge_bytes(episode))
                public = json.loads(payload)
                self.assertEqual(set(public), {"train", "test"})
                self.assertTrue(all(set(pair) == {"input", "output"} for pair in public["train"]))
                self.assertTrue(all(set(pair) == {"input"} for pair in public["test"]))
                private = json.loads((destination / "private/episodes" / f"{identifier}.json").read_text())
                self.assertEqual(private["program"], episode["program"])
                code = destination / "private/programs" / f"{episode['program_sha256']}.rkt"
                self.assertEqual(hashlib.sha256(code.read_bytes()).hexdigest(), episode["program_sha256"])
            with self.assertRaises(FileExistsError):
                P.write_export(destination, self.episodes, witness=witness,
                               runtime_identity={}, command="must not overwrite")

    def test_query_labels_private_metadata_and_duplicate_rejection(self):
        episode = self.episodes[0]
        poisoned = copy.deepcopy(episode)
        poisoned.update(seed=123456789, settings={"hidden": "sentinel"}, program="private sentinel")
        for pair in poisoned["test"]:
            pair["output"] = [[0 for _ in row] for row in pair["input"]]
        self.assertEqual(P.public_challenge_bytes(episode), P.public_challenge_bytes(poisoned))
        self.assertEqual(P.public_challenge_id(episode), P.public_challenge_id(poisoned))
        self.assertEqual(P.fit_candidates(episode["train"]), P.fit_candidates(poisoned["train"]))
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "must-not-exist"
            with self.assertRaisesRegex(ValueError, "duplicate visible payload"):
                P.write_export(destination, [episode, poisoned], witness={}, runtime_identity={}, command="duplicate")
            self.assertFalse(destination.exists())
            # The actual writer also emits unchanged public names/bytes when
            # supplied private-only changes; this deliberately poisoned private
            # record is disposable test data, never retained execution evidence.
            first = Path(directory) / "one"
            second = Path(directory) / "two"
            P.write_export(first, [episode], witness={}, runtime_identity={}, command="one")
            P.write_export(second, [poisoned], witness={}, runtime_identity={}, command="two")
            public_name = P.public_challenge_id(episode) + ".json"
            self.assertEqual((first / "public" / public_name).read_bytes(),
                             (second / "public" / public_name).read_bytes())


if __name__ == "__main__":
    unittest.main()
