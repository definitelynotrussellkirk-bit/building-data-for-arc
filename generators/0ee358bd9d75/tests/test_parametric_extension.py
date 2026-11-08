"""Task-local prototype coverage, separate from canonical generator repairs."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from arcpuzzles import Catalog
from arc_repl.racket_bridge import RacketBridge, RacketUnavailableError
from reviewer_support import (canonical_pairs, find_root, load_selected_generator,
                              public_challenge_bytes, public_challenge_id)


TASK_ID = "0ee358bd9d75"
ROOT = find_root(__file__)
PROTOTYPE_HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def load_module(name):
    spec = importlib.util.spec_from_file_location(
        "section_parametric_" + name, PROTOTYPE_HOME / (name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def independent_answer(grid, selection):
    """Test oracle: count each returned-grid section, never sampler metadata."""
    row_edges = [-1] + [r for r, row in enumerate(grid) if not any(row)] + [len(grid)]
    col_edges = [-1] + [
        c for c in range(len(grid[0])) if not any(row[c] for row in grid)
    ] + [len(grid[0])]
    result = []
    for top, bottom in zip(row_edges, row_edges[1:]):
        row = []
        for left, right in zip(col_edges, col_edges[1:]):
            counts = Counter(
                grid[r][c]
                for r in range(top + 1, bottom)
                for c in range(left + 1, right)
                if grid[r][c]
            )
            extreme = (max if selection == "most_frequent" else min)(counts.values())
            colors = [color for color, count in counts.items() if count == extreme]
            if len(colors) != 1:
                raise AssertionError("ambiguous independent oracle")
            row.append(colors[0])
        result.append(row)
    return result


class ParametricExtensionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prototype = load_module("prototype")
        cls.bridge = RacketBridge()

    @classmethod
    def tearDownClass(cls):
        cls.bridge.close()

    def test_default_program_and_all_canonical_pairs_preserve_canonical_behavior(self):
        prototype = self.prototype
        canonical = Catalog(ROOT).get(TASK_ID)["variants"]
        programs = {variant["program_solution"] for variant in canonical}
        self.assertEqual(len(programs), 1)
        canonical_program = programs.pop()
        self.assertEqual(prototype.materialize_program(), canonical_program)
        pairs = canonical_pairs(TASK_ID, root=ROOT)
        self.assertEqual(len(pairs), 8)
        self.assertEqual(len({json.dumps(pair["input"]) for pair in pairs}), 4)
        outputs = prototype.execute_program(
            prototype.materialize_program(), [pair["input"] for pair in pairs],
            bridge=self.bridge,
        )
        self.assertEqual(outputs, [pair["output"] for pair in pairs])

    def test_exact_lawful_witness_changes_selected_colors_without_reordering(self):
        prototype = self.prototype
        grid = prototype.differing_witness()
        generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
        self.assertEqual(generator.self_check(grid), [])
        before = deepcopy(grid)
        outputs = {
            selection: prototype.execute_program(
                prototype.materialize_program(selection), [grid], bridge=self.bridge
            )[0]
            for selection in prototype.SELECTIONS
        }
        self.assertEqual(outputs["most_frequent"], [[1, 3], [5, 7]])
        self.assertEqual(outputs["least_frequent"], [[2, 4], [6, 8]])
        self.assertEqual(grid, before)

    def test_sampler_has_lawful_distinct_extrema_and_meaningful_size_range(self):
        prototype = self.prototype
        generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
        shapes = set()
        for seed in (0, 1, 2, 3, 50000, 50001, 50002, 50003):
            inputs = prototype.sample_inputs(seed)
            self.assertEqual(len(inputs), 4)
            self.assertEqual(inputs, prototype.sample_inputs(seed))
            for grid in inputs:
                self.assertEqual(generator.self_check(grid), [])
                info = prototype.validate_input(grid, require_mixed=True)
                self.assertTrue(all(2 <= len(s["counts"]) <= 3 for s in info["sections"]))
                most = independent_answer(grid, "most_frequent")
                least = independent_answer(grid, "least_frequent")
                self.assertTrue(all(a != b for x, y in zip(most, least) for a, b in zip(x, y)))
                shapes.add((len(grid), len(grid[0])))
        self.assertIn((30, 30), shapes)
        self.assertIn((8, 8), shapes)
        self.assertTrue(any(h != w for h, w in shapes))

    def test_episodes_fix_one_rule_and_share_inputs_across_settings(self):
        prototype = self.prototype
        for seed in (1, 50003):
            expected_inputs = prototype.sample_inputs(seed)
            for selection in prototype.SELECTIONS:
                episode = prototype.generate_episode(seed, selection=selection, bridge=self.bridge)
                self.assertEqual(episode["selection"], selection)
                self.assertEqual(episode["program"], prototype.materialize_program(selection))
                pairs = episode["train"] + episode["test"]
                self.assertEqual(len(episode["train"]), 3)
                self.assertEqual(len(episode["test"]), 1)
                self.assertEqual([pair["input"] for pair in pairs], expected_inputs)
                for pair in pairs:
                    self.assertEqual(pair["output"], independent_answer(pair["input"], selection))
                    rival = next(value for value in prototype.SELECTIONS if value != selection)
                    self.assertNotEqual(pair["output"], independent_answer(pair["input"], rival))
        for seed in (0, 50000):
            episode = prototype.generate_episode(seed, selection=None, bridge=self.bridge)
            self.assertEqual(episode["selection"], prototype.choose_selection(seed))
            self.assertEqual(episode["selection"], prototype.choose_selection(seed))

    def test_every_holdout_rotation_is_identifiable_from_visible_demos(self):
        prototype = self.prototype
        for selection in prototype.SELECTIONS:
            episode = prototype.generate_episode(17, selection=selection, bridge=self.bridge)
            for query_index in range(4):
                rotated = prototype.rotate_episode(episode, query_index)
                self.assertEqual(len(rotated["train"]), 3)
                self.assertEqual(len(rotated["test"]), 1)
                rivals = [candidate for candidate in prototype.SELECTIONS if all(
                    independent_answer(pair["input"], candidate) == pair["output"]
                    for pair in rotated["train"]
                )]
                self.assertEqual(rivals, [selection])
                self.assertEqual(rotated["test"][0], (episode["train"] + episode["test"])[query_index])

    def test_public_challenge_omits_parameters_program_and_query_answers(self):
        prototype = self.prototype
        episode = prototype.generate_episode(3, selection="least_frequent", bridge=self.bridge)
        public = prototype.public_challenge(episode)
        self.assertEqual(set(public), {"train", "test"})
        self.assertTrue(all(set(pair) == {"input", "output"} for pair in public["train"]))
        self.assertTrue(all(set(pair) == {"input"} for pair in public["test"]))
        self.assertNotIn("least_frequent", json.dumps(public))
        before = deepcopy(episode)
        public["train"][0]["input"][0][0] = 99
        self.assertEqual(episode, before)

    def test_invalid_controls_and_ambiguous_inputs_raise(self):
        prototype = self.prototype
        for selection in ("median", "auto", False, 1):
            with self.assertRaises(ValueError):
                prototype.materialize_program(selection)
        for seed in (True, "2", 2.5):
            with self.assertRaises(ValueError):
                prototype.sample_inputs(seed)
        for grid in ([], [[1], [2, 3]], [[True]], [[10]], [[1.0]], [[0] * 8 for _ in range(8)]):
            with self.assertRaises(ValueError):
                prototype.validate_input(grid)
        tied = prototype.differing_witness()
        tied[0][0] = 2
        tied[0][1] = 0
        with self.assertRaisesRegex(ValueError, "unique"):
            prototype.validate_input(tied)
        episode = prototype.generate_episode(3, bridge=self.bridge)
        for index in (-1, 4, True, 1.5):
            with self.assertRaises(ValueError):
                prototype.rotate_episode(episode, index)

    def test_census_retains_executed_evidence_for_every_declared_setting(self):
        audit = load_module("audit")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "evidence"
            report = audit.run_census(output, seeds=(0, 50000), bridge=self.bridge)
            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["counts"]["canonical_pairs"], 8)
            self.assertEqual(report["counts"]["generated_inputs"], 8)
            self.assertEqual(report["counts"]["generated_racket_labels"], 16)
            self.assertEqual(report["counts"]["rotations_checked"], 16)
            self.assertEqual(report["counts"]["ambiguous_rotations"], 0)
            self.assertEqual(report["counts"]["oracle_mismatches"], 0)
            self.assertEqual({path.name for path in output.iterdir()}, {"public", "private"})
            manifest = json.loads((output / "private" / "manifest.json").read_text())
            self.assertTrue(manifest["source_hashes"])
            for index, selection in enumerate(self.prototype.SELECTIONS):
                basename = f"episode-{index:03d}"
                private = json.loads((output / "private" / "episodes" / (basename + ".json")).read_text())
                visible = self.prototype.public_turn(private)
                public_path = output / "public" / (public_challenge_id(visible) + ".json")
                public = json.loads(public_path.read_text())
                self.assertEqual(private["selection"], selection)
                self.assertEqual(public, self.prototype.public_challenge(private))
                self.assertEqual(public_path.read_bytes(), public_challenge_bytes(visible))
            with self.assertRaises(FileExistsError):
                audit.run_census(output, seeds=(0,), bridge=self.bridge)

    def test_census_retains_runtime_startup_failure(self):
        audit = load_module("audit")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "evidence"
            with patch.dict(os.environ, {"RACKET_PATH": str(Path(directory) / "missing-racket")}):
                with self.assertRaises(RacketUnavailableError):
                    audit.run_census(output, seeds=(0,))
            failure = output / "private" / "failure.json"
            self.assertTrue(failure.is_file(), "runtime failure must leave an honest receipt")
            retained = json.loads(failure.read_text())
            self.assertEqual(retained["status"], "failed")
            self.assertEqual(retained["exception"], "RacketUnavailableError")
            self.assertEqual(retained["seeds"], [0])


if __name__ == "__main__":
    unittest.main()
