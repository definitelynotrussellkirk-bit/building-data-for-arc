from __future__ import annotations

import copy
import importlib
import json
import random
import unittest
from pathlib import Path

from reviewer_support import canonical_path, find_root


TASK_ID = "d2708f8b731b"
ROOT = find_root(__file__)
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _canonical_inputs():
    inputs = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            for split in ("train", "test"):
                raw = row.get(split)
                pairs = raw if isinstance(raw, list) else [raw]
                for pair in pairs:
                    if not isinstance(pair, dict) or "input" not in pair:
                        continue
                    grid = pair["input"]
                    if grid and isinstance(grid[0], str):
                        grid = [[int(value) for value in row] for row in grid]
                    inputs.append(grid)
    return inputs


class GeneratorD2708F8B731BTests(unittest.TestCase):
    def test_canonical_inputs_pass_structural_self_check(self):
        inputs = _canonical_inputs()
        self.assertEqual(len(inputs), 3)
        for grid in inputs:
            self.assertEqual(GEN.self_check(grid), [])

    def test_exact_axes_survive_all_boundary_combinations(self):
        for difficulty in ("easy", "medium", "hard"):
            for grid_h in (12, 20):
                for grid_w in (16, 24):
                    for n_shapes in (2, 4):
                        for repeat_target in (False, True):
                            grid = GEN.generate(
                                73,
                                91,
                                difficulty=difficulty,
                                grid_h=grid_h,
                                grid_w=grid_w,
                                n_shapes=n_shapes,
                                repeat_target=repeat_target,
                            )
                            observed = GEN.observe_overrides(grid)
                            self.assertEqual(len(grid), grid_h)
                            self.assertEqual(len(grid[0]), grid_w)
                            self.assertEqual(observed["n_shapes"], n_shapes)
                            self.assertEqual(
                                observed["repeat_target"], repeat_target
                            )

    def test_repeated_target_and_nonidentity_order_are_realized(self):
        for seed in range(40):
            grid = GEN.generate(
                seed,
                700 + seed,
                difficulty="hard",
                n_shapes=4,
                repeat_target=True,
            )
            obs = GEN.task_observables(grid)
            self.assertTrue(obs["valid"], obs["errors"])
            self.assertEqual(obs["n_targets"], 5)
            self.assertNotEqual(obs["target_shape_order"][:4], [0, 1, 2, 3])
            self.assertEqual(len(obs["shape_sizes"]), 1)

    def test_deterministic_fresh_returns_and_global_rng_purity(self):
        state = random.getstate()
        first = GEN.generate(19, 23, difficulty="medium")
        self.assertEqual(random.getstate(), state)
        second = GEN.generate(19, 23, difficulty="medium")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        first[0][0] = (first[0][0] + 1) % 10
        self.assertNotEqual(first, second)

    def test_self_check_rejects_targeted_impostors(self):
        base = GEN.generate(
            211,
            313,
            difficulty="hard",
            n_shapes=4,
            repeat_target=True,
        )
        obs = GEN.task_observables(base)
        self.assertTrue(obs["valid"])

        no_swatch = copy.deepcopy(base)
        sr, sc = obs["prototype_records"][0]["swatch_cell"]
        no_swatch[sr][sc] = 0

        answer_leak = copy.deepcopy(base)
        sep = obs["separator_col"]
        leaked = False
        for r in range(len(answer_leak)):
            for c in range(sep + 1, len(answer_leak[0])):
                if answer_leak[r][c] == 0:
                    answer_leak[r][c] = 2
                    leaked = True
                    break
            if leaked:
                break
        self.assertTrue(leaked)

        unmatched_target = copy.deepcopy(base)
        tr, tc = obs["target_records"][0]["cells"][0]
        unmatched_target[tr][tc] = 0

        unused_prototype = copy.deepcopy(base)
        doomed_shape = obs["prototype_records"][0]["shape"]
        for record in obs["target_records"]:
            if record["shape"] == doomed_shape:
                for r, c in record["cells"]:
                    unused_prototype[r][c] = 0

        no_separator = copy.deepcopy(base)
        for r in range(len(no_separator)):
            no_separator[r][sep] = 1

        impostors = {
            "no_swatch": no_swatch,
            "answer_leak": answer_leak,
            "unmatched_target": unmatched_target,
            "unused_prototype": unused_prototype,
            "no_separator": no_separator,
        }
        for name, grid in impostors.items():
            with self.subTest(name=name):
                self.assertTrue(GEN.self_check(grid), name)


if __name__ == "__main__":
    unittest.main()
