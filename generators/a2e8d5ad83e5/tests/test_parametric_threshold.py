"""Focused source-mode tests for the proposed minimum-anchor-area prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)


TASK = "a2e8d5ad83e5"
HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = HOME / "workspace/parametric/prototype.py"
ADAPTER = HOME / "workspace/parametric/adapter.py"
ROOT = find_root(__file__)
SETTINGS = (4, 9, 16)


def load_local(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class PrototypeInterfaceTests(unittest.TestCase):
    def test_task_local_public_api_exists(self):
        self.assertTrue(PROTOTYPE.is_file(), "Missing task-local threshold prototype.py")
        self.assertTrue(ADAPTER.is_file(), "Missing task-local promotion adapter.py")
        prototype = load_local(PROTOTYPE, "_threshold_a2e8d5ad83e5_api_test")
        adapter = load_local(ADAPTER, "_threshold_a2e8d5ad83e5_adapter_api_test")
        for name in ("materialize_rule", "execute_rule", "generate_episode", "export_episodes"):
            self.assertTrue(callable(getattr(prototype, name, None)), name)
        for name in ("program", "generate"):
            self.assertTrue(callable(getattr(adapter, name, None)), name)


class ThresholdPrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prototype = load_local(PROTOTYPE, "_threshold_a2e8d5ad83e5_behavior_test")
        cls.adapter = load_local(ADAPTER, "_threshold_a2e8d5ad83e5_adapter_behavior_test")
        cls.bridge = RacketBridge()
        cls.addClassCleanup(cls.bridge.close)
        cls.episodes = {}
        cls.executions = {}
        with canonical_path(ROOT).open(encoding="utf-8") as handle:
            cls.canonical = {
                row["program_solution"]
                for row in (json.loads(line) for line in handle if line.strip())
                if row.get("task_id") == TASK
            }

    def episode(self, threshold=4, demos=3, queries=4):
        key = (threshold, demos, queries)
        if key not in self.episodes:
            self.episodes[key] = self.prototype.generate_episode(
                37,
                settings={"minimum_anchor_area": threshold},
                demos=demos,
                queries=queries,
                bridge=self.bridge,
            )
        return self.episodes[key]

    def execute(self, source, grid):
        key = (source, json.dumps(grid, separators=(",", ":")))
        if key not in self.executions:
            self.executions[key] = self.prototype.execute_rule(source, grid, bridge=self.bridge)
        return copy.deepcopy(self.executions[key])

    @staticmethod
    def inputs(episode):
        return [pair["input"] for split in ("train", "test") for pair in episode[split]]

    def test_canonical_bytes_and_known_pair_execute_in_protected_racket(self):
        self.assertEqual(len(self.canonical), 1)
        source = self.prototype.materialize_rule()
        self.assertEqual({source}, self.canonical)
        self.assertEqual(self.prototype.materialize_rule(4), source)
        self.assertEqual(self.bridge.runtime_identity["backend"], "racket")
        self.assertIs(self.bridge.runtime_identity["protected"], True)
        pair = canonical_pairs(TASK, root=ROOT, labeled_only=True)[0]
        self.assertEqual(self.execute(source, pair["input"]), pair["output"])

    def test_literal_area_boundaries_change_only_qualifying_anchors(self):
        # (height, width, threshold, active, center row, center column).
        # Areas immediately below and at the proposed thresholds are explicit.
        cases = (
            (1, 3, 4, False, 2, 4),
            (2, 2, 4, True, 2, 3),
            (2, 4, 9, False, 2, 4),
            (3, 3, 9, True, 3, 4),
            (3, 5, 16, False, 3, 5),
            (4, 4, 16, True, 3, 4),
        )
        for height, width, threshold, active, center_row, center_col in cases:
            grid = [[0] * 12 for _ in range(10)]
            for row in range(2, 2 + height):
                for col in range(3, 3 + width):
                    grid[row][col] = 6
            with self.subTest(area=height * width, threshold=threshold):
                result = self.execute(self.prototype.materialize_rule(threshold), grid)
                if active:
                    self.assertEqual(result[center_row][0], 6)
                    self.assertEqual(result[0][center_col], 6)
                    self.assertEqual(result[-1][-1], 0)
                else:
                    self.assertEqual(result, grid)

    def test_large_aligned_anchors_preserve_distinct_color_cancellation(self):
        # Both 4x4 anchors qualify at every setting; their center row is 3.
        for second_color in (2, 7):
            grid = [[0] * 16 for _ in range(10)]
            for row in range(2, 6):
                for col in range(1, 5):
                    grid[row][col] = 2
                for col in range(10, 14):
                    grid[row][col] = second_color
            for threshold in SETTINGS:
                with self.subTest(second_color=second_color, threshold=threshold):
                    result = self.execute(self.prototype.materialize_rule(threshold), grid)
                    self.assertEqual(result[3], [2 if second_color == 2 else 0] * 16)
                    self.assertEqual(result[0][2], 2)
                    self.assertEqual(result[0][11], second_color)

    def test_settings_require_exact_keys_and_typed_allowed_values(self):
        bad_settings = (
            {}, {"minimum_anchor_area": 5}, {"minimum_anchor_area": True},
            {"minimum_anchor_area": 4.0}, {"minimum_anchor_area": "4"},
            {"minimum_anchor_area": 4, "extra": 0}, [], "4",
        )
        for settings in bad_settings:
            with self.subTest(settings=settings):
                with self.assertRaises(ValueError):
                    self.prototype.generate_episode(37, settings=settings, bridge=self.bridge)
                with self.assertRaises(ValueError):
                    self.adapter.program(settings)
        for threshold in (True, 4.0, "4", 0, 5, 17, None):
            with self.subTest(threshold=threshold):
                with self.assertRaises(ValueError):
                    self.prototype.materialize_rule(threshold)

    def test_seed_and_input_seed_reject_inexact_or_out_of_range_values(self):
        for value in (True, False, 0.0, "0", -1, 2**63):
            with self.subTest(argument="seed", value=value):
                with self.assertRaises(ValueError):
                    self.prototype.generate_episode(value, bridge=self.bridge)
            with self.subTest(argument="input_seed", value=value):
                with self.assertRaises(ValueError):
                    self.prototype.generate_episode(37, input_seed=value, bridge=self.bridge)
        for seed, input_seed in ((0, 2**63 - 1), (2**63 - 1, 0)):
            with self.subTest(seed=seed, input_seed=input_seed):
                episode = self.prototype.generate_episode(
                    seed, input_seed=input_seed, demos=1, queries=1, bridge=self.bridge
                )
                self.assertEqual(episode["seed"], seed)
                self.assertEqual(episode["input_seed"], input_seed)
                self.assertEqual((len(episode["train"]), len(episode["test"])), (1, 1))

    def test_demo_and_query_counts_reject_inexact_or_unsupported_values(self):
        for argument in ("demos", "queries"):
            for value in (True, False, 1.0, "1", 0, 9, -1):
                with self.subTest(argument=argument, value=value):
                    with self.assertRaises(ValueError):
                        self.prototype.generate_episode(37, bridge=self.bridge, **{argument: value})

    def test_independent_count_limits_and_unique_inputs(self):
        for demos, queries in ((1, 4), (3, 4), (8, 8)):
            with self.subTest(demos=demos, queries=queries):
                episode = self.episode(demos=demos, queries=queries)
                self.assertEqual(len(episode["train"]), demos)
                self.assertEqual(len(episode["test"]), queries)
                encoded = [json.dumps(grid) for grid in self.inputs(episode)]
                self.assertEqual(len(encoded), len(set(encoded)))

    def test_same_input_seed_is_matched_across_settings(self):
        baseline = self.episode()
        for threshold in SETTINGS:
            with self.subTest(threshold=threshold):
                episode = self.episode(threshold)
                self.assertEqual(self.inputs(episode), self.inputs(baseline))
                self.assertEqual(episode["settings"], {"minimum_anchor_area": threshold})
                self.assertEqual(episode["seed"], 37)
                self.assertIs(type(episode["input_seed"]), int)
                self.assertEqual(episode["input_seed"], baseline["input_seed"])
                self.assertEqual(episode["program_solution"], self.prototype.materialize_rule(threshold))
        explicit = self.prototype.generate_episode(
            41, settings={"minimum_anchor_area": 9}, input_seed=baseline["input_seed"],
            bridge=self.bridge,
        )
        self.assertEqual(self.inputs(explicit), self.inputs(baseline))

    def test_demonstrations_alone_identify_each_setting(self):
        programs = {threshold: self.prototype.materialize_rule(threshold) for threshold in SETTINGS}
        for chosen in SETTINGS:
            with self.subTest(chosen=chosen):
                demos = self.episode(chosen)["train"]
                survivors = [
                    threshold for threshold, program in programs.items()
                    if all(self.execute(program, pair["input"]) == pair["output"] for pair in demos)
                ]
                self.assertEqual(survivors, [chosen])
                # The advertised minimum of one demonstration must teach the rule.
                first_survivors = [
                    threshold for threshold, program in programs.items()
                    if self.execute(program, demos[0]["input"]) == demos[0]["output"]
                ]
                self.assertEqual(first_survivors, [chosen])

    def test_all_episode_labels_execute_under_the_fixed_rule(self):
        for threshold in SETTINGS:
            episode = self.episode(threshold)
            self.assertIsInstance(episode["certificate"], dict)
            for split in ("train", "test"):
                for index, pair in enumerate(episode[split]):
                    with self.subTest(threshold=threshold, split=split, pair=index):
                        for key in ("input", "output"):
                            for row in pair[key]:
                                for cell in row:
                                    self.assertIs(type(cell), int)
                                    self.assertTrue(0 <= cell <= 9)
                        self.assertEqual(
                            self.execute(episode["program_solution"], pair["input"]), pair["output"]
                        )

    def test_adapter_preserves_exact_program_and_independent_counts(self):
        for threshold in SETTINGS:
            setting = {"minimum_anchor_area": threshold}
            self.assertEqual(self.adapter.program(setting), self.prototype.materialize_rule(threshold))
        episode = self.adapter.generate(37, {"minimum_anchor_area": 4}, 1, 4)
        expected = self.episode(demos=1, queries=4)
        self.assertEqual(episode["train"], expected["train"])
        self.assertEqual(episode["test"], expected["test"])
        self.assertEqual(episode["program_solution"], expected["program_solution"])

    def test_public_export_projection_and_private_metadata(self):
        episode = self.episode()
        identifier = public_challenge_id(episode)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "export"
            self.prototype.export_episodes([episode], output)
            public_file = output / "public" / f"{identifier}.json"
            self.assertEqual(list((output / "public").iterdir()), [public_file])
            self.assertEqual(public_file.read_bytes(), public_challenge_bytes(episode))
            self.assertEqual(hashlib.sha256(public_file.read_bytes()).hexdigest(), identifier)
            visible = json.loads(public_file.read_bytes())
            self.assertEqual(set(visible), {"train", "test"})
            self.assertTrue(all(set(pair) == {"input", "output"} for pair in visible["train"]))
            self.assertTrue(all(set(pair) == {"input"} for pair in visible["test"]))
            private = json.loads((output / "private" / f"{identifier}.json").read_bytes())
            self.assertEqual(private["settings"], episode["settings"])
            self.assertEqual(private["test"], episode["test"])
            self.assertTrue((output / "private" / "manifest.json").is_file())

    def test_hidden_metadata_and_query_answers_cannot_change_public_name(self):
        episode = self.episode()
        modified = copy.deepcopy(episode)
        modified["seed"] = 73
        modified["input_seed"] = 101
        modified["settings"] = {"minimum_anchor_area": 16}
        modified["program_solution"] = self.prototype.materialize_rule(16)
        modified["certificate"] = {"private_probe": "changed"}
        modified["test"][0]["output"][0][0] = (modified["test"][0]["output"][0][0] + 1) % 10
        self.assertEqual(public_challenge_id(episode), public_challenge_id(modified))
        with tempfile.TemporaryDirectory() as temporary:
            outputs = [Path(temporary) / name for name in ("first", "second")]
            for value, output in zip((episode, modified), outputs):
                self.prototype.export_episodes([value], output)
            first = next((outputs[0] / "public").iterdir())
            second = next((outputs[1] / "public").iterdir())
            self.assertEqual(first.name, second.name)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_visible_input_changes_public_name(self):
        episode = self.episode()
        modified = copy.deepcopy(episode)
        modified["test"][0]["input"][0][0] = (modified["test"][0]["input"][0][0] + 1) % 10
        self.assertNotEqual(public_challenge_id(episode), public_challenge_id(modified))
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "export"
            self.prototype.export_episodes([episode, modified], output)
            self.assertEqual(
                {path.name for path in (output / "public").iterdir()},
                {f"{public_challenge_id(value)}.json" for value in (episode, modified)},
            )

    def test_malformed_public_grids_are_rejected_before_publication(self):
        malformed = ([], [[]], [[True]], [[1.0]], [["1"]], [[10]], [[-1]], [[0], [0, 0]])
        for grid in malformed:
            modified = copy.deepcopy(self.episode())
            modified["test"][0]["input"] = grid
            with self.subTest(grid=grid), tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary) / "export"
                with self.assertRaises(ValueError):
                    public_challenge_bytes(modified)
                with self.assertRaises(ValueError):
                    self.prototype.export_episodes([modified], output)
                self.assertFalse(output.exists())

    def test_duplicate_visible_episodes_rejected_before_output_exists(self):
        episode = self.episode()
        duplicate = copy.deepcopy(episode)
        duplicate["seed"] = 71
        duplicate["test"][0]["output"][0][0] = (duplicate["test"][0]["output"][0][0] + 1) % 10
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "export"
            with self.assertRaises(ValueError):
                self.prototype.export_episodes([episode, duplicate], output)
            self.assertFalse(output.exists())

    def test_export_refuses_overwrite_and_preserves_existing_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "existing"
            output.mkdir()
            sentinel = output / "keep.txt"
            sentinel.write_bytes(b"untouched\n")
            with self.assertRaises((FileExistsError, ValueError)):
                self.prototype.export_episodes([self.episode()], output)
            self.assertEqual(sentinel.read_bytes(), b"untouched\n")
            self.assertEqual(list(output.iterdir()), [sentinel])


if __name__ == "__main__":
    unittest.main(verbosity=2)
