from __future__ import annotations

import importlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = importlib.import_module(
    "puzzle_generators.per_puzzle.25e78410d5bb.generator"
)


def canonical_inputs():
    grids = []
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != "25e78410d5bb" or row.get("source") != "training":
            continue
        for split in ("train", "test"):
            grids.extend(pair["input"] for pair in row.get(split) or [])
    return grids


class Generator25e78410d5bbTest(unittest.TestCase):
    def test_all_canonical_inputs_are_valid_complete_profiles(self):
        inputs = canonical_inputs()
        self.assertEqual(len(inputs), 4)
        signatures = set()
        for grid in inputs:
            self.assertEqual(GENERATOR.self_check(grid), [])
            signature = GENERATOR.canonical_profile_signature(grid)
            self.assertIsNotNone(signature)
            signatures.add(signature)
        self.assertEqual(signatures, GENERATOR._CANONICAL_SIGNATURES)

    def test_every_linked_profile_is_reachable_in_every_band(self):
        for difficulty in ("easy", "medium", "hard"):
            for index, profile in enumerate(GENERATOR._CANONICAL_GRIDS):
                grid = GENERATOR.generate(
                    7100 + index,
                    9100 + index,
                    difficulty=difficulty,
                    scene_profile=profile,
                )
                self.assertEqual(GENERATOR.self_check(grid), [])
                self.assertIn(
                    GENERATOR.canonical_profile_signature(grid),
                    GENERATOR._CANONICAL_SIGNATURES,
                )

    def test_exact_lattice_overrides_are_observed(self):
        cases = (
            {"grid_h": 10, "grid_w": 10, "row_bands": 2, "col_bands": 2},
            {"grid_h": 20, "grid_w": 20, "row_bands": 4, "col_bands": 4},
            {"grid_h": 14, "grid_w": 17, "row_bands": 3, "col_bands": 4},
        )
        for index, overrides in enumerate(cases):
            grid = GENERATOR.generate(
                8000 + index,
                10000 + index,
                scene_profile="general_lattice",
                **overrides,
            )
            self.assertEqual((len(grid), len(grid[0])), (
                overrides["grid_h"], overrides["grid_w"]
            ))
            observed = GENERATOR.observe_overrides(grid)
            self.assertEqual(observed["row_bands"], overrides["row_bands"])
            self.assertEqual(observed["col_bands"], overrides["col_bands"])
            self.assertEqual(GENERATOR.self_check(grid), [])

    def test_plausible_profile_recombination_is_not_official(self):
        grid = [
            list(row)
            for row in GENERATOR._CANONICAL_GRIDS["canonical_train_1"]
        ]
        # A single marker-color choice borrowed from another canonical profile
        # leaves a lawful 2x3 majority-fill lattice but breaks the complete
        # linked marker/topology signature.
        grid[0][0] = 1
        self.assertEqual(GENERATOR.self_check(grid), [])
        self.assertIsNone(GENERATOR.canonical_profile_signature(grid))


if __name__ == "__main__":
    unittest.main()
