"""Task-local tests for generator 1216927d148b (pairwise intersection gallery).

Covers the repaired defects:
- distribution_drift: generated panels must be single 4-connected one-color
  glyphs (median object count 3, like the canonical task), not random scatter.
- missing_rule_hash: RULE_HASH pins the canonical program_solution.
- override_preflight_failure: boundary overrides accepted, incompatible
  combinations rejected loudly, observe_overrides matches realized grids.
"""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import unittest
from pathlib import Path

from reviewer_support import canonical_path, find_root

ROOT = find_root(__file__)
TASK_ID = "1216927d148b"

gen = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _panels(grid):
    h = len(grid)
    return [
        [(r, dc) for r in range(h) for dc in range(5) if grid[r][c0 + dc] != 0]
        for c0 in (0, 6, 12)
    ]


def _n_components(cells):
    cells = {tuple(c) for c in cells}
    count = 0
    while cells:
        stack = [cells.pop()]
        count += 1
        while stack:
            r, c = stack.pop()
            for nb in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if nb in cells:
                    cells.remove(nb)
                    stack.append(nb)
    return count


class TestDistributionShape(unittest.TestCase):
    def test_panels_are_single_connected_glyphs(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(10):
                grid = gen.generate(seed, seed * 17 + 3, difficulty=band)
                panels = _panels(grid)
                self.assertTrue(all(panels), f"empty panel: {band}/{seed}")
                for cells in panels:
                    self.assertEqual(
                        _n_components(cells), 1,
                        f"panel is not one connected glyph: {band}/{seed}",
                    )
                # median object count must stay 3 like the canonical task
                self.assertEqual(
                    sum(_n_components(p) for p in panels), 3,
                )

    def test_panel_colors_pairwise_distinct(self):
        for seed in range(10):
            grid = gen.generate(seed, seed, difficulty="medium")
            colors = []
            for c0 in (0, 6, 12):
                seen = {grid[r][c0 + dc]
                        for r in range(len(grid)) for dc in range(5)
                        if grid[r][c0 + dc] != 0}
                self.assertEqual(len(seen), 1)
                colors.append(next(iter(seen)))
            self.assertEqual(len(set(colors)), 3)

    def test_pairwise_witnesses_present(self):
        for seed in range(10):
            grid = gen.generate(seed, seed, difficulty="easy")
            masks = [set(p) for p in _panels(grid)]
            for a, b in ((0, 1), (0, 2), (1, 2)):
                self.assertTrue(masks[a] & masks[b])


class TestRuleHashPin(unittest.TestCase):
    def test_rule_hash_matches_canonical(self):
        src = None
        with canonical_path(ROOT).open(encoding="utf-8") as fh:
            for line in fh:
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    src = row["program_solution"]
                    break
        self.assertIsNotNone(src)
        actual = hashlib.sha256(" ".join(src.split()).encode()).hexdigest()[:12]
        self.assertEqual(gen.RULE_HASH, actual)


class TestOverrideContract(unittest.TestCase):
    def test_boundary_overrides_accepted(self):
        for case in (
            {"grid_h": 5}, {"grid_h": 12},
            {"panel_cell_count": 1}, {"panel_cell_count": 25},
            {"grid_h": 5, "panel_cell_count": 25},
            {"grid_h": 12, "panel_cell_count": 1},
            {"palette_kind": "warm"}, {"palette_kind": "cool"},
            {"texture": "varied"},
        ):
            grid = gen.generate(7, 7, difficulty="medium", **case)
            self.assertEqual(gen.self_check(grid, difficulty="medium"), [],
                             f"self_check rejected {case}")
            observed = gen.observe_overrides(grid)
            for axis, value in case.items():
                if axis in observed:
                    self.assertEqual(observed[axis], value,
                                     f"{axis} not honored in {case}")

    def test_incompatible_combinations_reject_loudly(self):
        for case in (
            {"texture": "empty_panels", "panel_cell_count": 25},
            {"texture": "full_panels", "panel_cell_count": 1},
            {"texture": "empty_panels", "palette_kind": "warm"},
            {"texture": "warm", "palette_kind": "cool"},
            {"texture": "bogus"},
        ):
            with self.assertRaises(ValueError, msg=f"no loud reject: {case}"):
                gen.generate(3, 3, difficulty="medium", **case)

    def test_deterministic_replay_and_fresh_objects(self):
        first = gen.generate(11, 5, difficulty="hard")
        second = gen.generate(11, 5, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        snapshot = copy.deepcopy(first)
        gen.generate(11, 5, difficulty="hard")
        self.assertEqual(first, snapshot, "generate mutated a previous return")


class TestSelfCheckImpostors(unittest.TestCase):
    """Four targeted impostors the strengthened self_check must reject."""

    def _base(self):
        return gen.generate(4, 4, difficulty="medium")

    def test_accepts_canonical_inputs(self):
        with canonical_path(ROOT).open(encoding="utf-8") as fh:
            for line in fh:
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    break
        for split in ("train", "test"):
            for pair in row[split]:
                self.assertEqual(
                    gen.self_check(pair["input"]), [],
                    f"self_check rejected a canonical {split} input",
                )

    def test_rejects_scattered_panel(self):
        grid = self._base()
        h = len(grid)
        # redraw panel A as a deliberately disconnected glyph
        color = next(grid[r][c] for r in range(h) for c in range(5)
                     if grid[r][c] != 0)
        for r in range(h):
            for c in range(5):
                grid[r][c] = 0
        grid[0][0] = color
        grid[h - 1][4] = color
        errors = gen.self_check(grid)
        self.assertTrue(any("connected" in e for e in errors), errors)

    def test_rejects_mixed_color_panel(self):
        grid = self._base()
        h = len(grid)
        r, c = next((r, c) for r in range(h) for c in range(5) if grid[r][c])
        grid[r][c] = (grid[r][c] % 9) + 1
        if grid[r][c] == grid[r][(c + 1) % 5]:
            grid[r][c] = (grid[r][c] % 9) + 1
        errors = gen.self_check(grid)
        self.assertTrue(any("mixes colors" in e or "not pairwise distinct" in e
                            for e in errors), errors)

    def test_rejects_empty_intersection(self):
        grid = self._base()
        h = len(grid)
        # erase panel B wherever it intersects panel A -> AB witness gone
        for r in range(h):
            for dc in range(5):
                if grid[r][dc] != 0 and grid[r][6 + dc] != 0:
                    grid[r][6 + dc] = 0
        errors = gen.self_check(grid)
        self.assertTrue(any("AB" in e or "empty" in e or "connected" in e
                            for e in errors), errors)

    def test_rejects_missing_separator(self):
        grid = self._base()
        grid[0][5] = 3
        self.assertTrue(any("separator" in e for e in gen.self_check(grid)))

    def test_rejects_wrong_width(self):
        grid = [row[:16] for row in self._base()]
        self.assertTrue(gen.self_check(grid))


class TestDegenerateTextures(unittest.TestCase):
    def test_degenerate_draws_match_meta_contract(self):
        for name in gen.DEGENERATE_TEXTURES:
            grid = gen.generate(5, 5, difficulty="medium", texture=name)
            self.assertEqual(
                gen.self_check(grid, difficulty="medium",
                               meta={"texture": name}), [],
                f"degenerate {name} failed its own contract",
            )
        # and the normal (non-degenerate) reading must reject the broken ones
        empty = gen.generate(5, 5, difficulty="medium", texture="empty_panels")
        self.assertTrue(gen.self_check(empty))
        single = gen.generate(5, 5, difficulty="medium", texture="single_panel")
        self.assertTrue(gen.self_check(single))


if __name__ == "__main__":
    unittest.main()
