"""Focused tests for the separate 898e7135-inspired reconstruction prototype.

These tests read challenge demonstrations/query inputs only. They never load an
evaluation solution file or assert an official answer for the public query.
Run with unittest directly; the Racket test runs when RACKET_PATH is supplied
(or racket is on PATH) and otherwise reports a named skip.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import shutil
import sys
import unittest

TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE = TASK_ROOT / "workspace/parametric/focus_reconstruction.py"
SPEC = importlib.util.spec_from_file_location("focus_reconstruction_under_test", SOURCE)
FOCUS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FOCUS)


def visible_focus():
    path = REPO_ROOT / "shared/data/raw/arc-agi_evaluation_challenges.json"
    record = json.loads(path.read_text())["898e7135"]
    return {
        "train": [{"input": row["input"], "output": row["output"]}
                  for row in record["train"]],
        "test": [{"input": row["input"]} for row in record["test"]],
    }


def frozen(grid):
    return tuple(map(tuple, grid))


class FocusReconstructionTests(unittest.TestCase):
    def test_visible_demo_reconstruction_and_source_binding(self):
        challenge = visible_focus()
        visible_bytes = (json.dumps(challenge, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False) + "\n").encode()
        self.assertEqual(hashlib.sha256(visible_bytes).hexdigest(),
                         FOCUS.FOCUS_PUBLIC_CHALLENGE_SHA256)
        for pair, shape in zip(challenge["train"], ((12, 12), (28, 20))):
            with self.subTest(shape=shape):
                observed = FOCUS.python_expected(pair["input"], "piece")
                self.assertEqual(observed, pair["output"])
                self.assertEqual((len(observed), len(observed[0])), shape)

    def test_public_query_input_grammar_without_answer_data(self):
        challenge = visible_focus()
        self.assertEqual(set(challenge["test"][0]), {"input"})
        facts = FOCUS.analyze_input(challenge["test"][0]["input"])
        self.assertEqual(facts["carrier_shape"], (10, 10))
        self.assertEqual(facts["block_scale"], 3)
        self.assertEqual(facts["hole_count"], 6)
        self.assertEqual(facts["hole_class_count"], 5)

    def test_two_demo_four_query_inputs_and_demo_only_identification(self):
        scales, counts = set(), set()
        for seed in (0, 17):
            inputs = [FOCUS.sample_input(seed, index) for index in range(6)]
            self.assertEqual(len({frozen(grid) for grid in inputs}), 6)
            for grid in inputs:
                facts = FOCUS.analyze_input(grid)
                scales.add(facts["block_scale"])
                counts.add(facts["hole_count"])
            for chosen in FOCUS.SETTINGS:
                demonstrations = [(grid, FOCUS.python_expected(grid, chosen))
                                  for grid in inputs[:2]]
                survivors = [rival for rival in FOCUS.SETTINGS
                             if all(FOCUS.python_expected(grid, rival) == output
                                    for grid, output in demonstrations)]
                self.assertEqual(survivors, [chosen])
                for query in inputs[2:]:
                    out = FOCUS.python_expected(query, chosen)
                    self.assertTrue(1 <= len(out) <= 30)
                    self.assertTrue(1 <= len(out[0]) <= 30)
        self.assertEqual(scales, {2, 3})
        self.assertEqual(counts, {3, 4, 5, 6})

    def test_seeded_fresh_inputs_leave_global_rng_untouched(self):
        random.seed(123)
        state = random.getstate()
        first = FOCUS.sample_input(17, 3)
        second = FOCUS.sample_input(17, 3)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        self.assertEqual(random.getstate(), state)
        first[0][0] = (first[0][0] + 1) % 10
        self.assertEqual(FOCUS.sample_input(17, 3), second)

    def test_ambiguous_same_shape_different_colors_is_rejected(self):
        grid = FOCUS.sample_input(17, 3)
        facts = FOCUS.analyze_input(grid)
        square_area = facts["block_scale"] ** 2
        units = [(color, cells) for color, cells in FOCUS._components(grid)
                 if color != facts["carrier_color"] and len(cells) == square_area]
        self.assertEqual(len(units), 2)
        self.assertEqual(units[0][0], units[1][0])
        palette = {color for row in grid for color in row}
        replacement = next(color for color in range(1, 10) if color not in palette)
        for r, c in units[0][1]:
            grid[r][c] = replacement
        with self.assertRaisesRegex(ValueError, "unambiguous"):
            FOCUS.python_expected(grid, "piece")

    def test_incomplete_source_block_is_rejected(self):
        grid = FOCUS.sample_input(0, 0)
        facts = FOCUS.analyze_input(grid)
        color, cells = next((color, cells) for color, cells in FOCUS._components(grid)
                            if color != facts["carrier_color"]
                            and len(cells) == facts["block_scale"] ** 2)
        r, c = cells[0]
        grid[r][c] = 0
        with self.assertRaisesRegex(ValueError, "unambiguous"):
            FOCUS.python_expected(grid, "piece")

    def test_noise_removal_preserves_reconstruction(self):
        grid = FOCUS.sample_input(17, 2)
        original = FOCUS.python_expected(grid, "piece")
        scale = FOCUS.analyze_input(grid)["block_scale"]
        for color, cells in FOCUS._components(grid):
            if len(cells) < scale * scale:
                for r, c in cells:
                    grid[r][c] = 0
        self.assertEqual(FOCUS.python_expected(grid, "piece"), original)

    def test_source_color_swap_changes_corresponding_holes(self):
        grid = FOCUS.sample_input(17, 0)
        before = FOCUS.python_expected(grid, "template")
        facts = FOCUS.analyze_input(grid)
        pieces = [(color, cells) for color, cells in FOCUS._components(grid)
                  if color != facts["carrier_color"]
                  and len(cells) >= facts["block_scale"] ** 2]
        a, b = pieces[0][0], pieces[1][0]
        changed = [[b if value == a else a if value == b else value for value in row]
                   for row in grid]
        expected = [[b if value == a else a if value == b else value for value in row]
                    for row in before]
        self.assertEqual(FOCUS.python_expected(changed, "template"), expected)

    def test_visible_demo_requires_reflection_not_only_rotation(self):
        pair = visible_focus()["train"][0]
        grid, output = pair["input"], FOCUS.python_expected(pair["input"], "template")
        piece = next(cells for color, cells in FOCUS._components(grid) if color == 3)
        unit = FOCUS._normalize({(r // 2, c // 2)
                                for r, c in FOCUS._normalize(piece)})
        target = FOCUS._normalize({(r, c) for r, row in enumerate(output)
                                   for c, color in enumerate(row) if color == 3})
        rotations = set()
        for _ in range(4):
            unit = FOCUS._normalize(unit)
            rotations.add(unit)
            unit = tuple((c, -r) for r, c in unit)
        self.assertNotIn(target, rotations)
        self.assertIn(target, FOCUS._transforms(unit))

    def test_settings_and_exact_integer_grid_contract(self):
        self.assertNotEqual(FOCUS.render_program("piece"),
                            FOCUS.render_program("template"))
        for program in map(FOCUS.render_program, FOCUS.SETTINGS):
            self.assertTrue(program.startswith("(lambda (g)"))
            self.assertIn("all-transforms", program)
            self.assertIn("upscale", program)
            self.assertNotIn("__OUTPUT_SCALE__", program)
        with self.assertRaises(ValueError):
            FOCUS.render_program("unsupported")
        with self.assertRaises(ValueError):
            FOCUS.sample_input(True, 0)
        with self.assertRaises(ValueError):
            FOCUS.python_expected([[False]], "piece")

    @unittest.skipUnless(os.environ.get("RACKET_PATH") or shutil.which("racket"),
                         "Racket executable not configured")
    def test_protected_racket_parity_visible_demos_and_generated_pool(self):
        sys.path.insert(0, str(REPO_ROOT / "shared/runtime"))
        from arc_repl.racket_bridge import RacketBridge
        bridge = RacketBridge()
        try:
            self.assertTrue(bridge.runtime_identity["protected"])
            for setting in FOCUS.SETTINGS:
                bridge.eval_text("(define focus-rule " + FOCUS.render_program(setting) + ")")
                for index in range(6):
                    grid = FOCUS.sample_input(17, index)
                    bridge.define_grid("focus-input", grid)
                    result = bridge.eval_text("(focus-rule focus-input)")
                    self.assertEqual(result, FOCUS.python_expected(grid, setting),
                                     (setting, index))
            bridge.eval_text("(define focus-rule " + FOCUS.render_program("piece") + ")")
            for pair in visible_focus()["train"]:
                bridge.define_grid("focus-input", pair["input"])
                self.assertEqual(bridge.eval_text("(focus-rule focus-input)"),
                                 pair["output"])
        finally:
            bridge.close()


if __name__ == "__main__":
    unittest.main()
