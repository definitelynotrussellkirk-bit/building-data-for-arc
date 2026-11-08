from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import importlib

generator = importlib.import_module("puzzle_generators.per_puzzle.023f0cc17b52.generator")


ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "data" / "canonical" / "puzzles.jsonl"


def _canonical_row():
    for line in CANON.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == generator.TASK_ID:
            return row
    raise RuntimeError("canonical row missing")


class Generator023f0cc17b52Tests(unittest.TestCase):
    def test_all_canonical_pairs_and_signatures(self):
        row = _canonical_row()
        pairs = row["train"] + [row["test"]]
        signatures = set()
        for pair in pairs:
            grid = copy.deepcopy(pair["input"])
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.rule_mirror(grid), pair["output"])
            signature = generator.profile_signature(grid)
            self.assertIn(signature, generator.CANONICAL_PROFILE_SIGNATURES)
            signatures.add(signature)
        self.assertEqual(signatures, generator.CANONICAL_PROFILE_SIGNATURES)

    def test_default_prior_reaches_every_canonical_profile_in_every_band(self):
        for band_index, band in enumerate(("easy", "medium", "hard")):
            seen = set()
            for i in range(240):
                grid = generator.generate(
                    100_000 + band_index * 10_000 + i,
                    200_000 + band_index * 10_000 + i,
                    difficulty=band,
                )
                signature = generator.profile_signature(grid)
                if signature in generator.CANONICAL_PROFILE_SIGNATURES:
                    seen.add(signature)
            self.assertEqual(seen, generator.CANONICAL_PROFILE_SIGNATURES)

    def test_exact_axes_are_observable(self):
        grid = generator.generate(
            33,
            44,
            difficulty="easy",
            grid_h=12,
            grid_w=14,
            main_height=5,
            main_width=5,
            main_color=9,
            shape_kind="blob",
            has_decoy=True,
            clips_output=True,
        )
        self.assertEqual(
            generator.observe_overrides(grid),
            {
                "grid_h": 12,
                "grid_w": 14,
                "main_height": 5,
                "main_width": 5,
                "main_color": 9,
                "shape_kind": "blob",
                "has_decoy": True,
                "clips_output": True,
            },
        )

    def test_lawful_recombination_is_not_canonical(self):
        grid = [[0] * 10 for _ in range(8)]
        for r in range(1, 4):
            for c in range(1, 5):
                grid[r][c] = 4
        grid[5][5] = 1  # 8x10 and 3x4 from profile 0; delta from profile 1.
        self.assertEqual(generator.self_check(grid), [])
        self.assertFalse(generator.is_canonical_profile(grid))

    def test_destructive_mutations_are_rejected(self):
        base = generator.generate(
            777,
            888,
            difficulty="medium",
            grid_h=10,
            grid_w=12,
            main_height=3,
            main_width=3,
            shape_kind="rect",
            has_decoy=False,
            clips_output=False,
        )
        scene = generator._analyze(base)
        target = scene["target"]
        ar, ac = scene["anchors"][0]

        mutations = []
        no_anchor = copy.deepcopy(base)
        no_anchor[ar][ac] = 0
        mutations.append(no_anchor)

        two_anchors = copy.deepcopy(base)
        spot = next(
            (r, c)
            for r, row in enumerate(two_anchors)
            for c, value in enumerate(row)
            if value == 0
        )
        two_anchors[spot[0]][spot[1]] = 1
        mutations.append(two_anchors)

        no_interior = copy.deepcopy(base)
        center = next(
            (r, c)
            for r, c in target["cells"]
            if all((r + dr, c + dc) in set(target["cells"]) for dr, dc in generator._CARDINALS)
        )
        no_interior[center[0]][center[1]] = 0
        mutations.append(no_interior)

        third_component = copy.deepcopy(base)
        zeros = [
            (r, c)
            for r, row in enumerate(third_component)
            for c, value in enumerate(row)
            if value == 0
            and all(
                not (0 <= r + dr < len(third_component) and 0 <= c + dc < len(row))
                or third_component[r + dr][c + dc] == 0
                for dr, dc in generator._CARDINALS
            )
        ]
        self.assertTrue(zeros)
        third_component[zeros[-1][0]][zeros[-1][1]] = 8
        third_component[zeros[0][0]][zeros[0][1]] = 7
        mutations.append(third_component)

        for mutation in mutations:
            self.assertTrue(generator.self_check(mutation))


if __name__ == "__main__":
    unittest.main()
