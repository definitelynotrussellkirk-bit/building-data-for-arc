from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "3f5263211041"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = find_root(__file__)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


class GeneratorTests(unittest.TestCase):
    def test_canonical_authority_and_python_mirror(self):
        self.assertEqual(len(PAIRS), 5)
        mirror = getattr(MODULE, "rule_mirror", None)
        self.assertTrue(callable(mirror), "generator must expose a Python rule mirror")
        for pair in PAIRS:
            self.assertEqual(MODULE.self_check(pair["input"]), [])
            self.assertEqual(mirror(copy.deepcopy(pair["input"])), pair["output"])

    def test_rule_hash_is_pinned_to_selected_authority(self):
        rows = []
        with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    rows.append(row)
        self.assertEqual(len(rows), 1)
        expected = hashlib.sha256(" ".join(rows[0]["program_solution"].split()).encode()).hexdigest()[:12]
        self.assertEqual(MODULE.RULE_HASH, expected)

    def test_unknown_and_invalid_overrides_are_rejected(self):
        with self.assertRaises(ValueError):
            MODULE.generate(1, 2, unknown_axis=7)
        for kwargs in (
            {"library": True},
            {"library": -1},
            {"program": 99},
            {"palette_kind": "not-a-palette"},
        ):
            with self.assertRaises((TypeError, ValueError), msg=kwargs):
                MODULE.generate(1, 2, **kwargs)

    def test_every_advertised_axis_is_exact_observable_and_effective(self):
        observer = getattr(MODULE, "observe_overrides", None)
        self.assertTrue(callable(observer), "exact axes need a pixel observer")
        domains = {
            "library": range(4),
            "program": range(7),
            "palette_kind": ("default", "warm", "cool", "varied"),
        }
        for axis, values in domains.items():
            grids = []
            for value in values:
                grid = MODULE.generate(17, 23, **{axis: value})
                self.assertEqual(MODULE.self_check(grid), [], (axis, value))
                self.assertEqual(observer(grid)[axis], value)
                grids.append(tuple(map(tuple, grid)))
            self.assertEqual(len(set(grids)), len(grids), axis)

    def test_joint_override_round_trip_and_determinism(self):
        observer = getattr(MODULE, "observe_overrides", None)
        self.assertTrue(callable(observer))
        random.seed(90210)
        state = random.getstate()
        for library in range(4):
            for program in range(7):
                for palette_kind in ("default", "warm", "cool", "varied"):
                    kwargs = {
                        "library": library,
                        "program": program,
                        "palette_kind": palette_kind,
                    }
                    first = MODULE.generate(31, 47, difficulty="hard", **kwargs)
                    second = MODULE.generate(31, 47, difficulty="hard", **kwargs)
                    self.assertEqual(first, second)
                    self.assertEqual(observer(first), kwargs)
                    self.assertEqual(MODULE.self_check(first), [])
        self.assertEqual(random.getstate(), state)

    def test_generated_distribution_is_structurally_lawful_and_varied(self):
        mirror = getattr(MODULE, "rule_mirror", None)
        self.assertTrue(callable(mirror))
        inputs, outputs, frame_orders, key_orders, palette_sizes = set(), set(), set(), set(), set()
        for seed in range(160):
            band = ("easy", "medium", "hard")[seed % 3]
            grid = MODULE.generate(seed, seed * 37, difficulty=band)
            self.assertEqual(MODULE.self_check(grid), [], seed)
            out = mirror(copy.deepcopy(grid))
            self.assertTrue(out and out[0])
            self.assertTrue(all(len(row) == len(out[0]) for row in out))
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, out)))
            analysis = MODULE._analysis(grid)
            frame_orders.add(tuple(frame["shape_index"] for frame in analysis["frames"]))
            key_orders.add(tuple(frame["key"] for frame in analysis["frames"]))
            palette_sizes.add(len({cell for row in grid for cell in row}))
        self.assertGreater(len(inputs), 150)
        self.assertGreater(len(outputs), 120)
        self.assertGreater(len(frame_orders), 3)
        self.assertGreater(len(key_orders), 6)
        self.assertTrue(palette_sizes <= {8, 9, 10})
        self.assertTrue(palette_sizes)

    def test_self_check_rejects_retained_missing_key_and_program_mutations(self):
        grid = MODULE.generate(5, 9, library=0, program=0, palette_kind="default")
        analysis = MODULE._analysis(grid) if hasattr(MODULE, "_analysis") else None
        if analysis:
            first = analysis["frames"][0]
            missing_key = copy.deepcopy(grid)
            missing_key[first["top"] - 1][first["left"]:first["right"] + 1] = [0] * (first["right"] - first["left"] + 1)
        else:
            missing_key = copy.deepcopy(grid)
            missing_key[0] = [0] * len(missing_key[0])
        self.assertTrue(MODULE.self_check(missing_key), "missing frame key must be rejected")

        empty_program = copy.deepcopy(grid)
        empty_program[-2] = [0] * len(empty_program[-2])
        empty_program[-1] = [0] * len(empty_program[-1])
        self.assertTrue(MODULE.self_check(empty_program), "empty code rows must be rejected")

        bad_transform = copy.deepcopy(grid)
        c = next(i for i, value in enumerate(bad_transform[-1]) if value)
        bad_transform[-1][c] = 4
        self.assertTrue(MODULE.self_check(bad_transform), "unknown transform command must be rejected")

    def test_canonical_shortcut_fits_canonical_but_generated_witness_refutes_it(self):
        shortcuts = getattr(MODULE, "CANONICAL_SHORTCUTS", {})
        witnesses = getattr(MODULE, "SEMANTIC_WITNESSES", {})
        rivals = getattr(MODULE, "SEMANTIC_RIVALS", {})
        links = getattr(MODULE, "WITNESS_RIVALS", {})
        self.assertIn("fixed_key_positions", shortcuts)
        self.assertIn("fixed_key_positions", rivals)
        self.assertIn("permuted_key_legend", witnesses)
        self.assertIn("fixed_key_positions", links.get("permuted_key_legend", []))
        shortcut = shortcuts["fixed_key_positions"]
        for pair in PAIRS:
            self.assertEqual(shortcut(copy.deepcopy(pair["input"])), pair["output"])
        found = False
        for seed in range(100):
            grid = MODULE.generate(seed, seed * 19)
            if witnesses["permuted_key_legend"](copy.deepcopy(grid)):
                self.assertNotEqual(shortcut(copy.deepcopy(grid)), MODULE.rule_mirror(copy.deepcopy(grid)))
                found = True
                break
        self.assertTrue(found, "generator must emit a fixed-key-position counterexample")

    def test_every_four_pair_window_is_rotation_safe_against_shortcut(self):
        # These exact windows were the two failures retained by the first
        # 300-lesson rotated census.  Every four-pair lesson needs at least
        # two counterexamples so holding one out cannot revive the rival.
        cases = (("easy", 2225315974, 11), ("medium", 1569988426, 64))
        for band, seed, start in cases:
            flags = [
                MODULE.SEMANTIC_WITNESSES["permuted_key_legend"](
                    MODULE.generate(seed, start + offset, difficulty=band)
                )
                for offset in range(4)
            ]
            self.assertGreaterEqual(sum(flags), 2, (band, seed, start, flags))

        for band in ("easy", "medium", "hard"):
            for seed in range(8):
                for start in range(8):
                    flags = [
                        MODULE.SEMANTIC_WITNESSES["permuted_key_legend"](
                            MODULE.generate(seed, start + offset, difficulty=band)
                        )
                        for offset in range(4)
                    ]
                    self.assertGreaterEqual(sum(flags), 2, (band, seed, start, flags))

    def test_lesson_hook_rejects_ambiguous_and_accepts_distinguishing_demo(self):
        hook = getattr(MODULE, "lesson_identifiable", None)
        self.assertTrue(callable(hook))
        canonical_demos = [copy.deepcopy(pair) for pair in PAIRS[:2]]

        witness = None
        ordinary = None
        for seed in range(200):
            grid = MODULE.generate(seed, seed * 13)
            pair = {"input": grid, "output": MODULE.rule_mirror(copy.deepcopy(grid))}
            if MODULE.SEMANTIC_WITNESSES["permuted_key_legend"](grid):
                witness = pair
            else:
                ordinary = pair
            if witness is not None and ordinary is not None:
                break
        self.assertIsNotNone(witness)
        self.assertIsNotNone(ordinary)
        self.assertTrue(hook(canonical_demos, witness))
        self.assertEqual(hook([witness], ordinary), [])


if __name__ == "__main__":
    unittest.main()
