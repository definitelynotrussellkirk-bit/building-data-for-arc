"""Focused stdlib checks for the opt-in periodic continuation prototype.

Run with the packet's run_with_racket.py; these are not canonical battery results.
"""
from __future__ import annotations

import copy
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"


class ParametricTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = None
        cls.runner = None
        if SOURCE.is_file():
            spec = importlib.util.spec_from_file_location("periodic_parametric_test_subject", SOURCE)
            cls.module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = cls.module
            spec.loader.exec_module(cls.module)
            cls.runner = cls.module.RacketRunner()

    @classmethod
    def tearDownClass(cls):
        if cls.runner is not None:
            cls.runner.close()

    def setUp(self):
        self.assertTrue(SOURCE.is_file(), "missing task-local parametric prototype")
        self.p = self.module

    def episode(self, **kwargs):
        return self.p.generate_episode(runner=self.runner, **kwargs)

    def test_default_is_exact_canonical_program_and_labels(self):
        self.assertEqual(self.p.program(self.p.DEFAULT), self.p.canonical_record()["program_solution"])
        record = self.p.canonical_record()
        self.assertEqual(len(record["train"] + record["test"]), 4)
        for pair in record["train"] + record["test"]:
            self.assertEqual(self.runner.apply(self.p.program(self.p.DEFAULT), pair["input"]),
                             pair["output"])

    def test_all_settings_have_two_demos_and_four_distinct_queries(self):
        for settings in self.p.SETTINGS:
            with self.subTest(settings=settings):
                episode = self.episode(seed=17, settings=settings, demos=2, queries=4)
                self.assertEqual(episode["settings"], settings)
                self.assertEqual((len(episode["train"]), len(episode["test"])), (2, 4))
                pairs = episode["train"] + episode["test"]
                self.assertEqual(len({json.dumps(pair["input"]) for pair in pairs}), 6)
                self.assertEqual([len(pair["input"]) for pair in episode["train"]], [9, 7])
                certificate = episode["certificate"]
                self.assertEqual(certificate["surviving_settings"], [settings])
                self.assertEqual(certificate["surviving_shortcuts"], [])
                self.assertEqual(len(certificate["queries"]), 4)
                self.assertTrue(all(row["all_survivors_agree"] for row in certificate["queries"]))
                self.assertEqual(len(certificate["shortcut_rejections"]), 7)
                self.assertTrue(all(certificate["shortcut_rejections"].values()))

    def test_shared_input_seed_isolates_the_rule_effect(self):
        episodes = [self.episode(seed=11 + index, input_seed=92, settings=settings,
                                 demos=2, queries=4)
                    for index, settings in enumerate(self.p.SETTINGS)]
        inputs = [[pair["input"] for pair in episode["train"] + episode["test"]]
                  for episode in episodes]
        self.assertTrue(all(value == inputs[0] for value in inputs))
        public_ids = {self.p.public_challenge_id(episode) for episode in episodes}
        self.assertEqual(len(public_ids), 4)
        self.assertEqual({len(episode["train"][0]["output"]) for episode in episodes}, {12, 13})
        self.assertEqual({max(map(max, episode["train"][0]["output"])) for episode in episodes},
                         {2, 3})

    def test_independent_count_limits_and_deterministic_sampling(self):
        full = self.episode(seed=42, settings=self.p.DEFAULT, demos=8, queries=8)
        self.assertEqual((len(full["train"]), len(full["test"])), (8, 8))
        self.assertEqual(len({json.dumps(p["input"]) for p in full["train"] + full["test"]}), 16)
        small = self.episode(seed=42, demos=3, queries=1)
        self.assertEqual((len(small["train"]), len(small["test"])), (3, 1))
        self.assertEqual(small, self.episode(seed=42, demos=3, queries=1))

    def test_cli_rejects_explicit_null_settings(self):
        import subprocess
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "export"
            result = subprocess.run(
                [sys.executable, str(SOURCE), "--settings", "null", "--out", str(destination)],
                text=True, capture_output=True, timeout=30)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertFalse(destination.exists())

    def test_numeric_settings_and_controls_are_exact_integers(self):
        for key in self.p.DEFAULT:
            for value in (True, False, 2.0, "2", None, [], 0, 4):
                with self.subTest(key=key, value=value):
                    settings = dict(self.p.DEFAULT, **{key: value})
                    with self.assertRaises(ValueError):
                        self.p.program(settings)
        for settings in ({}, {"extension_divisor": 2},
                         dict(self.p.DEFAULT, surprise=2), []):
            with self.assertRaises(ValueError):
                self.p.program(settings)
        for field, values in (
            ("seed", (True, 1.0, "1", -1, 2**63)),
            ("input_seed", (False, 1.0, "1", -1, 2**63)),
            ("demos", (True, 2.0, "2", 1, 9)),
            ("queries", (False, 4.0, "4", 0, 9)),
        ):
            for value in values:
                with self.subTest(field=field, value=value):
                    kwargs = {"seed": 1, field: value}
                    with self.assertRaises(ValueError):
                        self.episode(**kwargs)

    def test_ceiling_shortcut_really_uses_integer_ceiling_in_arc_racket(self):
        # ARC's "/" is integer division; ceiling(/ h d) silently stays floor.
        for divisor in (2, 3):
            settings = dict(self.p.DEFAULT, extension_divisor=divisor)
            grid = self.p.GENERATOR.generate(23, 19, grid_h=7, grid_w=3, period=4)
            answer = self.runner.apply(self.p.rival_programs(settings)["ceiling_extension"], grid)
            self.assertEqual(len(answer), 7 + (7 + divisor - 1) // divisor)
            self.assertNotEqual(len(answer), 7 + 7 // divisor)

    def test_program_parity_at_input_boundaries(self):
        axes = ((4, 3, 2), (4, 12, 2), (18, 3, 6), (18, 12, 6), (7, 3, 4), (9, 12, 6))
        for settings, (height, width, period) in itertools.product(self.p.SETTINGS, axes):
            grid = self.p.GENERATOR.generate(23, 19, grid_h=height, grid_w=width, period=period)
            self.assertEqual(self.p.GENERATOR.self_check(grid), [])
            answer = self.runner.apply(self.p.program(settings), grid)
            self.assertEqual(answer, self.p.diagnostic_output(grid, settings))
            self.assertEqual(len(answer), height + height // settings["extension_divisor"])
            self.assertLessEqual(len(answer), 30)

    def test_ambiguous_demonstrations_are_rejected_without_query_answers(self):
        train = copy.deepcopy(self.p.canonical_record()["train"][:2])
        query_inputs = [self.p.canonical_record()["test"][0]["input"]]
        with self.assertRaisesRegex(ValueError, "demonstrations leave"):
            self.p.lesson_certificate(train, query_inputs, self.p.DEFAULT, self.runner)

    def test_public_identity_ignores_private_metadata_and_query_labels(self):
        episode = self.episode(seed=7, settings=self.p.DEFAULT, demos=2, queries=4)
        original = self.p.public_challenge_bytes(episode)
        changed = copy.deepcopy(episode)
        changed.update(seed=991, input_seed=87, settings={"hidden": "different"},
                       program_solution="private", arbitrary_private="do not expose")
        changed["test"][0]["output"] = [[9]]
        self.assertEqual(self.p.public_challenge_bytes(changed), original)
        self.assertEqual(self.p.public_challenge_id(changed), self.p.public_challenge_id(episode))
        visible = json.loads(original)
        self.assertEqual(set(visible), {"train", "test"})
        self.assertTrue(all(set(pair) == {"input"} for pair in visible["test"]))
        changed = copy.deepcopy(episode)
        changed["test"][0]["input"][0][0] = 1 - changed["test"][0]["input"][0][0]
        self.assertNotEqual(self.p.public_challenge_id(changed), self.p.public_challenge_id(episode))

    def test_writer_uses_sorted_visible_bytes_and_exact_program_files(self):
        episodes = [self.episode(seed=31, settings=setting, demos=2, queries=4)
                    for setting in reversed(self.p.SETTINGS)]
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "export"
            manifest = self.p.write_export(episodes, destination, runner=self.runner)
            expected = sorted(episodes, key=self.p.public_challenge_id)
            self.assertEqual((destination / "public.jsonl").read_bytes(),
                             b"".join(self.p.public_challenge_bytes(ep) for ep in expected))
            self.assertEqual(sorted(p.stem for p in (destination / "public").iterdir()),
                             [self.p.public_challenge_id(ep) for ep in expected])
            for episode in expected:
                public_id = self.p.public_challenge_id(episode)
                self.assertEqual((destination / "public" / (public_id + ".json")).read_bytes(),
                                 self.p.public_challenge_bytes(episode))
                program_path = destination / "private" / "programs" / (episode["program_sha256"] + ".rkt")
                self.assertEqual(program_path.read_text(), episode["program_solution"])
            self.assertEqual(manifest["episodes"], 4)
            self.assertEqual(manifest["query_pairs"], 16)
            self.assertTrue(manifest["racket_runtime"]["protected"])
            with self.assertRaises(FileExistsError):
                self.p.write_export(episodes, destination, runner=self.runner)

    def test_writer_rejects_duplicate_public_batch_before_creating_destination(self):
        episode = self.episode(seed=5, settings=self.p.DEFAULT, demos=2, queries=4)
        changed = copy.deepcopy(episode)
        changed["seed"] = 911
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "export"
            with self.assertRaisesRegex(ValueError, "duplicate public"):
                self.p.write_export([episode, changed], destination, runner=self.runner)
            self.assertFalse(destination.exists())

    def test_writer_rejects_bad_query_labels_and_duplicate_inputs(self):
        episode = self.episode(seed=5, settings=self.p.DEFAULT, demos=2, queries=4)
        bad_label = copy.deepcopy(episode)
        bad_label["test"][0]["output"][0][0] = 9
        duplicate = copy.deepcopy(episode)
        duplicate["test"][0] = copy.deepcopy(duplicate["train"][0])
        boolean_cell = copy.deepcopy(episode)
        boolean_cell["test"][0]["output"][0][0] = True
        for candidate, reason in ((bad_label, "Racket"), (duplicate, "distinct"),
                                  (boolean_cell, "integer")):
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as temporary:
                destination = Path(temporary) / "export"
                with self.assertRaisesRegex(ValueError, reason):
                    self.p.write_export([candidate], destination, runner=self.runner)
                self.assertFalse(destination.exists())

    def test_writer_serializes_all_metadata_before_creating_destination(self):
        episode = self.episode(seed=5, settings=self.p.DEFAULT, demos=2, queries=4)
        for extra, command in (({"not_json"}, None), (None, {"not_json"}),
                               (float("nan"), None)):
            with self.subTest(extra=extra, command=command), tempfile.TemporaryDirectory() as temporary:
                destination = Path(temporary) / "export"
                candidate = copy.deepcopy(episode)
                candidate["arbitrary_private"] = extra
                with self.assertRaises((TypeError, ValueError)):
                    self.p.write_export([candidate], destination, runner=self.runner, command=command)
                self.assertFalse(destination.exists(), "serialization failure left partial export")

    def test_sampler_reports_bounded_exhaustion_without_cloning(self):
        original = self.p.GENERATOR.generate
        witness = original(12, 1)
        def duplicates(seed, sample_index, **kwargs):
            if kwargs.get("grid_h") == 7:
                return original(seed, sample_index, **kwargs)
            return copy.deepcopy(witness)
        with patch.object(self.p.GENERATOR, "generate", side_effect=duplicates):
            with self.assertRaisesRegex(ValueError, "sampling exhausted"):
                self.episode(seed=12, demos=2, queries=4)


if __name__ == "__main__":
    unittest.main(verbosity=2)

