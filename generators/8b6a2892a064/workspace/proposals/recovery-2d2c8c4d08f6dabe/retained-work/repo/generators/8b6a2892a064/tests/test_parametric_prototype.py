"""Focused proposed-parametric tests; these do not approve canonical source."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

TASK_ID = "8b6a2892a064"


def prototype_source():
    # Pure contract tests can inspect a task-only copy without a runtime.
    # Normal packet/copied-runtime execution binds through its own ledger and
    # selected-source manifest rather than assuming a fixed directory depth.
    try:
        from reviewer_support import find_root, load_selected_generator
    except ModuleNotFoundError as exc:
        if exc.name != "reviewer_support":
            raise
        local = Path(__file__).resolve().parent.parent / "workspace/parametric/prototype.py"
        if local.is_file():
            return local
        raise
    root = find_root(__file__)
    _, selected_source, _ = load_selected_generator(TASK_ID, root=root)
    relative = f"generators/{TASK_ID}/workspace/parametric/prototype.py"
    manifest = root / "RUNTIME_MANIFEST.json"
    if manifest.is_file():
        mappings = json.loads(manifest.read_text()).get("files", [])
        matches = [row["runtime_path"] for row in mappings if row.get("library_path") == relative]
        if len(set(matches)) == 1:
            source = root / matches[0]
            if not source.resolve().is_relative_to(root):
                raise ValueError("prototype manifest path escapes the selected tree")
            return source
        if matches:
            raise ValueError("ambiguous prototype runtime mapping")
    adjacent = selected_source.parent / "workspace/parametric/prototype.py"
    if adjacent.is_file():
        return adjacent
    mirrored = root / relative
    if mirrored.is_file():
        return mirrored
    raise FileNotFoundError(f"No task-local prototype in selected tree {root}")


SOURCE = prototype_source()
spec = importlib.util.spec_from_file_location("line_rotation_parametric", SOURCE)
prototype = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = prototype
body = SOURCE.read_bytes()
exec(compile(body, str(SOURCE), "exec"), prototype.__dict__)


class PrototypeContractTests(unittest.TestCase):
    def test_supported_settings_and_canonical_default(self):
        self.assertEqual(prototype.Parameters(), prototype.Parameters("all", 3))
        self.assertEqual(len(prototype.SETTINGS), 6)
        self.assertEqual(len({prototype.emit_rule(p) for p in prototype.SETTINGS}), 6)
        for mode, threshold in (("diagonal", 3), ("all", 4), ("all", True)):
            with self.subTest(mode=mode, threshold=threshold), self.assertRaises(ValueError):
                prototype.Parameters(mode, threshold)
        self.assertIn("background", prototype.REJECTED_CONTROLS)
        self.assertIn("turn_direction", prototype.REJECTED_CONTROLS)

    def test_seeded_parameters_are_once_per_episode_and_layout_independent(self):
        for seed in range(12):
            self.assertEqual(prototype.sample_parameters(seed), prototype.sample_parameters(seed))
        self.assertGreater(len({prototype.sample_parameters(s) for s in range(24)}), 1)
        first, receipt = prototype.draw_inputs(271828, 7, max_attempts=32)
        second, _ = prototype.draw_inputs(271828, 7, max_attempts=32)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 7)
        self.assertEqual(len({prototype.digest(grid) for grid in first}), 7)
        self.assertEqual(receipt["accepted"], 7)
        for grid in first:
            components = prototype.validate_input(grid)
            self.assertEqual(sorted((c["orientation"], c["length"]) for c in components),
                             [("h", 3), ("h", 5), ("s", 1), ("v", 3), ("v", 5)])

    def test_bounded_duplicate_sampling_fails_without_short_episode(self):
        grid = prototype.draw_input(__import__("random").Random(3))
        with self.assertRaises(prototype.SamplingError) as ctx:
            prototype.draw_inputs(7, 2, max_attempts=3, sampler=lambda _: copy.deepcopy(grid))
        self.assertEqual(ctx.exception.receipt["accepted"], 1)
        self.assertEqual(ctx.exception.receipt["attempts"], 3)
        self.assertEqual(ctx.exception.receipt["rejections"]["duplicate"], 2)
        self.assertEqual(ctx.exception.receipt["requested"], 2)

    def test_inadmissible_grids_and_counts_are_rejected(self):
        for grid in ([], [[7]], [[7, 2, 2]], [[2, 2], [7, 2]], [[2, 7, 3]], [[True]]):
            with self.subTest(grid=grid), self.assertRaises(ValueError):
                prototype.validate_input(grid)
        for demos, queries in ((0, 4), (3, 0), (True, 4), (3, -1)):
            with self.subTest(demos=demos, queries=queries), self.assertRaises(ValueError):
                prototype.generate_episode(0, demos=demos, queries=queries)
        with self.assertRaises(TypeError):
            prototype.generate_episode(0, background=0)

    def test_public_name_uses_only_visible_payload(self):
        episode = {
            "train": [{"input": [[7, 2, 7]], "output": [[7, 2, 7]]}],
            "test": [{"input": [[7, 3, 7]], "output": [[3, 7, 7]]}],
            "private": {"seed": 17, "parameters": {"rotate_when": "all", "min_length": 3}},
        }
        visible = prototype.public_challenge(episode)
        original_name = prototype.public_filename(episode)
        episode["private"] = {"seed": -999, "parameters": {"rotate_when": "vertical", "min_length": 5}}
        episode["test"][0]["output"] = [[7, 7, 3]]
        self.assertEqual(prototype.public_challenge(episode), visible)
        self.assertEqual(prototype.public_filename(episode), original_name)
        self.assertEqual(set(visible), {"train", "test"})
        self.assertEqual(set(visible["test"][0]), {"input"})
        self.assertRegex(original_name, r"^challenge-[0-9a-f]{24}\.json$")
        episode["train"][0]["output"] = [[2, 7, 7]]
        self.assertNotEqual(prototype.public_filename(episode), original_name)


class PrototypeRacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evaluator = prototype.RacketEvaluator()

    @classmethod
    def tearDownClass(cls):
        cls.evaluator.close()

    def test_all_six_complete_episodes_and_demo_only_query_evidence(self):
        names = set()
        for parameters in prototype.SETTINGS:
            with self.subTest(parameters=parameters):
                episode = prototype.generate_episode(20261023, parameters=parameters,
                                                     demos=3, queries=4, evaluator=self.evaluator)
                self.assertEqual(len(episode["train"]), 3)
                self.assertEqual(len(episode["test"]), 4)
                inputs = [p["input"] for p in episode["train"] + episode["test"]]
                self.assertEqual(len({prototype.digest(g) for g in inputs}), 7)
                evidence = episode["private"]
                self.assertEqual(evidence["parameters"], parameters.as_dict())
                self.assertEqual(evidence["rule_sha256"], hashlib.sha256(evidence["rule"].encode()).hexdigest())
                self.assertEqual(evidence["demo_survivors"], [parameters.as_dict()])
                self.assertEqual(len(evidence["query_evidence"]), 4)
                for query in evidence["query_evidence"]:
                    self.assertTrue(query["identified_from_demonstrations"])
                    self.assertEqual(query["survivors"], [parameters.as_dict()])
                    self.assertEqual(len(query["rivals"]), 5)
                    for rival in query["rivals"]:
                        self.assertTrue(rival["demo_mismatch_indices"])
                        self.assertTrue(all(0 <= i < 3 for i in rival["demo_mismatch_indices"]))
                        self.assertTrue(rival["differs_on_query"])
                names.add(prototype.public_filename(episode))
        self.assertEqual(len(names), 6)

    def test_separate_counts(self):
        episode = prototype.generate_episode(11, demos=1, queries=2, evaluator=self.evaluator)
        self.assertEqual((len(episode["train"]), len(episode["test"])), (1, 2))
        self.assertEqual(len(episode["private"]["query_evidence"]), 2)

    def test_clipping_singletons_and_selection(self):
        grid = [[7] * 6 for _ in range(6)]
        grid[0][1:4] = [2, 2, 2]
        grid[5][5] = 2
        expected = [[7] * 6 for _ in range(6)]
        expected[0][2] = expected[1][2] = expected[5][5] = 2
        actual = self.evaluator.apply_many(prototype.emit_rule(prototype.Parameters()), [grid])[0]
        self.assertEqual(actual, expected)
        for parameters in (prototype.Parameters("all", 5), prototype.Parameters("vertical", 3)):
            self.assertEqual(self.evaluator.apply_many(prototype.emit_rule(parameters), [grid])[0], grid)

    def test_canonical_default_matches_exact_canonical_on_public_inputs(self):
        from reviewer_support import canonical_pairs, canonical_path, find_root
        root = find_root(__file__)
        unique = {}
        for pair in canonical_pairs(TASK_ID, root=root):
            unique.setdefault(prototype.digest(pair["input"]), pair)
        self.assertEqual(len(unique), 4)
        rules = set()
        with canonical_path(root).open() as handle:
            for line in handle:
                if line.strip():
                    row = json.loads(line)
                    if row.get("task_id") == TASK_ID:
                        rules.add(row["program_solution"])
        self.assertEqual(len(rules), 1)
        inputs = [p["input"] for p in unique.values()]
        expected = self.evaluator.apply_many(next(iter(rules)), inputs)
        actual = self.evaluator.apply_many(prototype.emit_rule(prototype.Parameters()), inputs)
        self.assertEqual(actual, expected)
        self.assertEqual(actual, [p["output"] for p in unique.values()])


if __name__ == "__main__":
    unittest.main()
