"""Focused regressions for generator 61c0bcd32328."""
from __future__ import annotations

import copy
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import sys
import unittest

# Portable bootstrap for both the packet checkout and isolated task-test runtime.
for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_path, find_root  # noqa: E402

TASK_ID = "61c0bcd32328"
ROOT = find_root(__file__)
DEFAULT_GENERATOR = ROOT / "generators" / TASK_ID / "generator.py"
if not DEFAULT_GENERATOR.is_file():
    DEFAULT_GENERATOR = (
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    )
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", DEFAULT_GENERATOR))
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
CANONICAL_PATH = canonical_path(ROOT)
DATA_ROOT = CANONICAL_PATH.parents[1]


def rows():
    return [
        json.loads(line)
        for line in CANONICAL_PATH.read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    ]


def decode(grid):
    return [[int(value) for value in row] if isinstance(row, str) else list(row) for row in grid]


def occurrences():
    result = []
    for row in rows():
        for split in ("train", "test"):
            pairs = row[split]
            result.extend([pairs] if isinstance(pairs, dict) else pairs)
    return result


def unique_pairs():
    seen = {}
    for pair in occurrences():
        seen.setdefault(tuple(map(tuple, decode(pair["input"]))), pair)
    return list(seen.values())


class Tests(unittest.TestCase):
    def test_all_canonical_occurrences(self):
        self.assertEqual(len(occurrences()), 8)
        for pair in occurrences():
            self.assertEqual(
                MODULE.rule_mirror(decode(pair["input"])),
                decode(pair["output"]),
            )

    def test_four_unique_public_inputs(self):
        pairs = unique_pairs()
        self.assertEqual(len(pairs), 4)
        for index, pair in enumerate(pairs):
            self.assertEqual(
                MODULE.canonical_profile_signature(decode(pair["input"])),
                MODULE.PUBLIC_PROFILES[index],
            )
        self.assertEqual(
            [MODULE.generate(1, 2, scene_profile=profile) for profile in MODULE.PUBLIC_PROFILES],
            [decode(pair["input"]) for pair in pairs],
        )

    def test_every_profile_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.SCENE_PROFILES:
                for seed in range(15):
                    grid = MODULE.generate(
                        seed,
                        seed * 17 + 3,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    self.assertEqual(
                        MODULE.observe_overrides(grid), {"scene_profile": profile}
                    )
                    self.assertEqual(MODULE.self_check(grid), [])

    def test_single_tl_profile_teaches_singleton_corner_components(self):
        """Catches a corner sampler that silently excludes one-cell objects."""
        witness = None
        for seed in range(128):
            grid = MODULE.generate(
                seed,
                seed * 19 + 5,
                difficulty="easy",
                scene_profile="single_tl",
            )
            info = MODULE._analysis(grid)
            top_left_parts = [
                part for corner, part in info["corner_parts"] if corner == "tl"
            ]
            if any(len(part["cells"]) == 1 for part in top_left_parts):
                witness = grid
                break
        self.assertIsNotNone(
            witness,
            "the bounded single_tl lesson sweep never teaches a singleton corner object",
        )
        self.assertEqual(MODULE.self_check(witness), [])
        self.assertNotEqual(MODULE.rule_mirror(witness), witness)

    def test_corner_copy_preserves_dimensions_and_source_object(self):
        for profile in MODULE.SCENE_PROFILES:
            grid = MODULE.generate(101, 203, scene_profile=profile)
            output = MODULE.rule_mirror(grid)
            self.assertNotEqual(grid, output)
            self.assertEqual(len(grid), len(output))
            self.assertEqual(len(grid[0]), len(output[0]))

        # Use a one-corner scene so no different corner copy can overwrite the source.
        grid = MODULE.generate(101, 203, scene_profile="single_tl")
        output = MODULE.rule_mirror(grid)
        info = MODULE._analysis(grid)
        for corner, part in info["corner_parts"]:
            self.assertEqual(corner, "tl")
            for row_index, column_index in part["cells"]:
                self.assertEqual(output[row_index][column_index], part["color"])

    def test_default_diversity(self):
        for band in ("easy", "medium", "hard"):
            profiles = Counter()
            inputs = set()
            outputs = set()
            for seed in range(500):
                grid = MODULE.generate(seed, seed * 11 + 1, difficulty=band)
                profiles[MODULE.observe_overrides(grid)["scene_profile"]] += 1
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, MODULE.rule_mirror(grid))))
            self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
            self.assertGreater(len(inputs), 400)
            self.assertGreater(len(outputs), 400)

    def test_malformed(self):
        valid = MODULE.generate(401, 503, scene_profile="adjacent_top")
        empty = [[0 for _ in row] for row in valid]
        no_corner = [
            [MODULE._analysis(valid)["background"] for _ in row] for row in valid
        ]
        ragged = copy.deepcopy(valid)
        ragged[0].pop()
        invalid = copy.deepcopy(valid)
        invalid[0][0] = 10
        boolean = copy.deepcopy(valid)
        boolean[0][0] = True
        for grid in (empty, no_corner, ragged, invalid, boolean):
            self.assertTrue(MODULE.self_check(grid))

    def test_determinism(self):
        for overrides in (
            {"scene_profile": "x"},
            {"grid_h": 8},
            {"texture": "warm"},
        ):
            with self.assertRaises(ValueError):
                MODULE.generate(1, 2, **overrides)
        random.seed(20260721)
        state = random.getstate()
        first = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)

    def test_source_sync(self):
        source = rows()[0]["program_solution"]
        self.assertEqual(len({row["program_solution"] for row in rows()}), 1)
        for relative in (
            "base/solutions/training/bc93ec48__61c0bcd32328.json",
            "base/solutions/augmented/bc93ec48__a71106ee8661.json",
        ):
            base = json.loads((DATA_ROOT / relative).read_text())
            normalized = " ".join(source.split())
            self.assertEqual(" ".join(base["racket_target"]["raw_code"].split()), normalized)
            self.assertEqual(" ".join(base["racket_target"]["target_code"].split()), normalized)
        self.assertEqual(
            MODULE.RULE_HASH,
            hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12],
        )


if __name__ == "__main__":
    unittest.main()
