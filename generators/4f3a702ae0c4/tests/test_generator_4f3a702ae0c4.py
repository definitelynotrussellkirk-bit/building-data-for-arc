"""Regression tests for the command-selected diagonal-reflection generator."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import unittest
from pathlib import Path

from puzzle_generators.base import set_ctx_observer
from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "puzzle_generators" / "per_puzzle" / "4f3a702ae0c4" / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("generator_4f3a702ae0c4", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _decode(grid):
    return [[int(ch) for ch in row] if isinstance(row, str) else list(row) for row in grid]


def canonical_row():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") == "4f3a702ae0c4":
                return row
    raise AssertionError("canonical task is missing")


def canonical_pairs():
    row = canonical_row()
    test = row["test"]
    tests = [test] if isinstance(test, dict) else test
    return [
        {"input": _decode(pair["input"]), "output": _decode(pair["output"])}
        for pair in [*row["train"], *tests]
    ]


def canonical_inputs():
    row = canonical_row()
    test = row["test"]
    tests = [test] if isinstance(test, dict) else test
    return [_decode(pair["input"]) for pair in [*row["train"], *tests]]


class DiagonalReflectionGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = load_generator()

    def test_all_canonical_inputs_are_accepted_and_profiles_match(self):
        signatures = set()
        for grid in canonical_inputs():
            self.assertEqual([], self.generator.self_check(grid))
            self.assertEqual([], self.generator.strict_canonical_like(grid))
            signatures.add(self.generator.canonical_profile_signature(grid))
        self.assertEqual(self.generator._CANONICAL_SIGNATURES, signatures)

    def test_rule_hash_matches_normalized_canonical_source(self):
        normalized = " ".join(canonical_row()["program_solution"].split())
        actual = hashlib.sha256(normalized.encode()).hexdigest()[:12]
        self.assertEqual(actual, self.generator.RULE_HASH)

    def test_real_racket_matches_all_canonical_pairs_is_pure_and_a_b_a(self):
        bundle = _load_bundle("4f3a702ae0c4")
        bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
        pairs = canonical_pairs()
        try:
            for pair in pairs:
                source = copy.deepcopy(pair["input"])
                snapshot = copy.deepcopy(source)
                self.assertEqual(pair["output"], _apply_rule(bridge, fn_name, source))
                self.assertEqual(snapshot, source)
                self.assertEqual(pair["output"], self.generator.rule_mirror(source))

            grid_a = self.generator.generate(901, 10, difficulty="easy")
            grid_b = self.generator.generate(902, 11, difficulty="hard")
            a1 = _apply_rule(bridge, fn_name, grid_a)
            _ = _apply_rule(bridge, fn_name, grid_b)
            a2 = _apply_rule(bridge, fn_name, grid_a)
            self.assertEqual(a1, a2)
            self.assertEqual(a1, self.generator.rule_mirror(grid_a))
        finally:
            bridge.shutdown()

    def test_default_draw_provenance_matches_pixels_and_global_rng_is_untouched(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(12):
                captured = []
                random.seed(7000 + seed)
                before = random.getstate()
                set_ctx_observer(captured.append)
                try:
                    first = self.generator.generate(seed, seed * 17 + 3, difficulty=band)
                    second = self.generator.generate(seed, seed * 17 + 3, difficulty=band)
                finally:
                    set_ctx_observer(None)
                after = random.getstate()
                self.assertEqual(before, after)
                self.assertEqual(first, second)
                self.assertIsNot(first, second)
                self.assertTrue(all(a is not b for a, b in zip(first, second)))
                self.assertEqual(2, len(captured))
                observed = self.generator.observe_overrides(first)
                for axis in self.generator.AXES:
                    self.assertEqual(observed[axis], captured[0].axis_value(axis))

    def test_command_override_controls_both_value_and_corner(self):
        for cmd in (1, 2):
            grid = self.generator.generate(
                17, 4, difficulty="medium", cmd=cmd, grid_n=9,
                n_cells=4, n_pattern_colors=2,
            )
            observed = self.generator.observe_overrides(grid)
            self.assertEqual(cmd, observed["cmd"])
            self.assertEqual((1, 0) if cmd == 1 else (0, 2), (grid[0][0], grid[0][-1]))
            self.assertEqual([], self.generator.self_check(grid))

    def test_every_default_lesson_window_contains_both_commands_and_multicolor(self):
        grids = [self.generator.generate(91, i, difficulty="medium") for i in range(3)]
        facts = [self.generator.observe_overrides(grid) for grid in grids]
        self.assertEqual({1, 2}, {item["cmd"] for item in facts})
        self.assertIn(2, {item["n_pattern_colors"] for item in facts})

    def test_every_official_linked_profile_is_reachable_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            counts = {signature: 0 for signature in self.generator._CANONICAL_SIGNATURES}
            strict = 0
            for sample_index in range(500):
                grid = self.generator.generate(1234, sample_index, difficulty=band)
                self.assertEqual([], self.generator.self_check(grid))
                signature = self.generator.canonical_profile_signature(grid)
                if signature is not None:
                    strict += 1
                if signature in counts:
                    counts[signature] += 1
            with self.subTest(band=band, counts=counts):
                self.assertGreaterEqual(strict, 75)
                self.assertTrue(all(value > 0 for value in counts.values()))

    def test_recombined_command_profile_is_not_an_official_signature(self):
        grid = canonical_inputs()[0]
        changed = [row[:] for row in grid]
        changed[0][0] = 0
        changed[0][-1] = 2
        self.assertEqual([], self.generator.strict_canonical_like(changed))
        self.assertNotIn(
            self.generator.canonical_profile_signature(changed),
            self.generator._CANONICAL_SIGNATURES,
        )

    def test_rule_mirror_is_pure_and_adds_reflected_cells(self):
        grid = self.generator.generate(8, 1, difficulty="hard")
        snapshot = [row[:] for row in grid]
        first = self.generator.rule_mirror(grid)
        second = self.generator.rule_mirror(grid)
        self.assertEqual(snapshot, grid)
        self.assertEqual(first, second)
        cleared = [row[:] for row in grid]
        cleared[0][0] = cleared[0][-1] = 0
        self.assertNotEqual(cleared, first)


if __name__ == "__main__":
    unittest.main()
