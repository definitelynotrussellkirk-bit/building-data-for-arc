"""Task-local finite-rival teaching checks; no Racket labeling is claimed."""
from __future__ import annotations

import copy
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


def gate_source():
    try:
        from reviewer_support import find_root, load_selected_generator
    except ModuleNotFoundError as exc:
        if exc.name != "reviewer_support":
            raise
        local = Path(__file__).resolve().parent.parent / "workspace/lesson_gate/gate.py"
        return local
    root = find_root(__file__)
    _, selected, _ = load_selected_generator("8b6a2892a064", root=root)
    relative = "generators/8b6a2892a064/workspace/lesson_gate/gate.py"
    manifest = root / "RUNTIME_MANIFEST.json"
    if manifest.is_file():
        rows = json.loads(manifest.read_text()).get("files", [])
        matches = {r["runtime_path"] for r in rows if r.get("library_path") == relative}
        if len(matches) > 1:
            raise ValueError("ambiguous lesson-gate runtime mapping")
        if matches:
            source = root / next(iter(matches))
            if not source.resolve().is_relative_to(root):
                raise ValueError("lesson-gate source escapes selected tree")
            return source
    adjacent = selected.parent / "workspace/lesson_gate/gate.py"
    if adjacent.is_file():
        return adjacent
    return root / relative


SPEC = importlib.util.spec_from_file_location("finite_lesson_gate", gate_source())
gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gate
SOURCE_BYTES = Path(SPEC.origin).read_bytes()
exec(compile(SOURCE_BYTES, str(SPEC.origin), "exec"), gate.__dict__)


def pair(value, label):
    return {"input": [[value]], "output": [[label]]}


def identity(grid):
    return copy.deepcopy(grid)


class LessonGateTests(unittest.TestCase):
    def test_demo_eliminated_rival_is_never_evaluated_on_queries(self):
        calls = []
        def eliminated(grid):
            calls.append(grid[0][0])
            if grid[0][0] != 1:
                raise AssertionError("a demo-eliminated rival reached a query")
            return copy.deepcopy(grid)
        episode = {"train": [pair(1, 9)], "test": [pair(2, 2)]}
        result = gate.score_episode(episode, {"eliminated": eliminated})
        self.assertEqual(calls, [1])
        self.assertTrue(result["passed"])
        self.assertEqual(result["demo_survivors"], [])
        self.assertEqual(result["queries"][0]["rivals"][0]["refuting_demo_indices"], [0])
        self.assertEqual(result["queries"][0]["ambiguous_rivals"], [])

    def test_surviving_rival_can_agree_on_one_query_and_disagree_on_another(self):
        episode = {"train": [pair(1, 1)], "test": [pair(2, 2), pair(3, 4)]}
        result = gate.score_episode(episode, {"identity": identity})
        self.assertFalse(result["passed"])
        self.assertEqual(result["demo_survivors"], ["identity"])
        self.assertEqual(result["queries"][0]["ambiguous_rivals"], [])
        self.assertEqual(result["queries"][1]["ambiguous_rivals"], ["identity"])
        self.assertTrue(result["queries"][0]["rivals"][0]["agrees_with_supplied_label"])
        self.assertFalse(result["queries"][1]["rivals"][0]["agrees_with_supplied_label"])

    def test_query_answers_cannot_change_frozen_demo_survivors(self):
        episode = {"train": [pair(1, 1)], "test": [pair(2, 2), pair(3, 4)]}
        first = gate.score_episode(episode, {"identity": identity})
        changed = copy.deepcopy(episode)
        changed["test"][0]["output"] = [[8]]
        changed["test"][1]["output"] = [[3]]
        second = gate.score_episode(changed, {"identity": identity})
        self.assertEqual(first["demo_survivors"], second["demo_survivors"])
        self.assertEqual(first["demo_evidence"], second["demo_evidence"])
        self.assertNotEqual(first["queries"][0]["ambiguous_rivals"], second["queries"][0]["ambiguous_rivals"])
        self.assertNotEqual(first["queries"][1]["ambiguous_rivals"], second["queries"][1]["ambiguous_rivals"])

    def test_all_labels_and_requested_counts_are_required(self):
        good = {"train": [pair(1, 1)], "test": [pair(2, 2), pair(3, 3)]}
        for split in ("train", "test"):
            broken = copy.deepcopy(good)
            del broken[split][0]["output"]
            with self.subTest(split=split), self.assertRaises(gate.LessonGateError):
                gate.score_episode(broken, {"identity": identity})
        for kwargs in ({"expected_demos": 3}, {"expected_queries": 4}, {"expected_queries": True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(gate.LessonGateError):
                gate.score_episode(good, {"identity": identity}, **kwargs)
        for split in ("train", "test"):
            broken = copy.deepcopy(good)
            broken[split] = []
            with self.subTest(empty=split), self.assertRaises(gate.LessonGateError):
                gate.score_episode(broken, {"identity": identity})

    def test_duplicate_inputs_across_demonstrations_and_queries_are_rejected(self):
        for episode in (
            {"train": [pair(1, 1), pair(1, 2)], "test": [pair(3, 3)]},
            {"train": [pair(1, 1)], "test": [pair(1, 1)]},
            {"train": [pair(1, 1)], "test": [pair(2, 2), pair(2, 3)]},
        ):
            with self.subTest(episode=episode), self.assertRaises(gate.LessonGateError):
                gate.score_episode(episode, {"identity": identity})

    def test_input_is_not_mutated_even_if_a_competitor_mutates_its_copy(self):
        episode = {"train": [pair(1, 1)], "test": [pair(2, 2)]}
        original = copy.deepcopy(episode)
        gate.score_episode(episode, {"identity": identity})
        self.assertEqual(episode, original)
        def mutating(grid):
            grid[0][0] = 9
            return grid
        with self.assertRaisesRegex(gate.LessonGateError, "mutated"):
            gate.score_episode(episode, {"mutating": mutating})
        self.assertEqual(episode, original)

    def test_malformed_grids_and_missing_competitors_fail(self):
        good = {"train": [pair(1, 1)], "test": [pair(2, 2)]}
        for grid in ([], [[True]], [[11]], [[1], [2, 3]], [[]]):
            broken = copy.deepcopy(good)
            broken["test"][0]["input"] = grid
            with self.subTest(grid=grid), self.assertRaises(gate.LessonGateError):
                gate.score_episode(broken, {"identity": identity})
        for rivals in ({}, {"bad": None}, {"": identity}):
            with self.subTest(rivals=rivals), self.assertRaises(gate.LessonGateError):
                gate.score_episode(good, rivals)

    def test_json_and_jsonl_keep_every_episode(self):
        first = {"train": [pair(1, 1)], "test": [pair(2, 2)]}
        second = {"train": [pair(3, 3)], "test": [pair(4, 4)]}
        self.assertEqual(gate.parse_episodes(json.dumps(first)), [first])
        self.assertEqual(gate.parse_episodes(json.dumps([first, second])), [first, second])
        self.assertEqual(gate.parse_episodes(json.dumps(first) + "\n" + json.dumps(second) + "\n"), [first, second])
        for text in ("", "[]", "{}", json.dumps(first) + "\n{broken"):
            with self.subTest(text=text), self.assertRaises(gate.LessonGateError):
                gate.parse_episodes(text)

    def test_cli_exit_codes_and_receipt_hashes(self):
        source = Path(__file__).resolve()
        selected = types.SimpleNamespace(LESSON_COMPETITORS={"identity": identity}, VERSION="test-only")
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        cases = [
            ({"train": [pair(1, 1)], "test": [pair(2, 2)]}, 0),
            ({"train": [pair(1, 1)], "test": [pair(2, 3)]}, 1),
            ({"train": [pair(1, 1)], "test": [{"input": [[2]]}]}, 2),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            upstream = root / "upstream-receipt.json"
            upstream.write_text('{"test_fixture": true, "labels_are_test_values": true}\n')
            for index, (episode, expected_code) in enumerate(cases):
                input_path, output_path = root / f"episode-{index}.json", root / f"score-{index}.json"
                input_path.write_text(json.dumps(episode))
                args = ["--input", str(input_path), "--upstream-receipt", str(upstream),
                        "--expect-demos", "1", "--expect-queries", "1", "--out", str(output_path)]
                with self.subTest(exit_code=expected_code), patch.object(
                    gate, "_selected_generator", return_value=(selected, source, source_hash)
                ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(gate.main(args), expected_code)
                if expected_code == 2:
                    self.assertFalse(output_path.exists())
                else:
                    report = json.loads(output_path.read_text())
                    self.assertEqual(report["generator_source_sha256"], source_hash)
                    self.assertEqual(report["inputs"][0]["sha256"], hashlib.sha256(input_path.read_bytes()).hexdigest())
                    self.assertEqual(report["upstream_receipts"][0]["sha256"], hashlib.sha256(upstream.read_bytes()).hexdigest())
                    self.assertFalse(report["labels_reexecuted"])
                    self.assertEqual(report["status"], "pass" if expected_code == 0 else "ambiguous")


if __name__ == "__main__":
    unittest.main()
