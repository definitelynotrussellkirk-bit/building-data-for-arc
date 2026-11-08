"""Focused semantic regressions for generator 616a5c01a7ea."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
import random
import sys
import unittest


try:
    from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator
except ModuleNotFoundError as error:
    if error.name != "reviewer_support":
        raise
    for ancestor in Path(__file__).resolve().parents:
        helper = ancestor / "shared" / "runtime" / "reviewer_support.py"
        if helper.is_file():
            sys.path.insert(0, str(helper.parent))
            break
    else:
        raise
    from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "616a5c01a7ea"
ROOT = find_root(__file__)
MODULE, _, _ = load_selected_generator(TASK_ID, root=ROOT)
DATA_ROOT = canonical_path(ROOT).parent.parent
BANDS = ("easy", "medium", "hard")


def _canonical_row():
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


def _normalized_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


class Generator616a5c01a7eaTests(unittest.TestCase):
    def test_all_canonical_pairs_are_accepted_and_solved(self):
        row = _canonical_row()
        pairs = canonical_pairs(TASK_ID, root=ROOT)
        self.assertEqual(len(pairs), 4)
        for pair in pairs:
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            self.assertEqual(MODULE.self_check(source), [])
            self.assertTrue(MODULE.strict_canonical_like(source))
            self.assertEqual(MODULE.rule_mirror(source), pair["output"])
            self.assertEqual(source, before)

    def test_rule_pin_and_selected_authority_sync(self):
        row = _canonical_row()
        canonical = row["program_solution"]
        base = json.loads((
            DATA_ROOT / "base/solutions/training/8e5a5113__616a5c01a7ea.json"
        ).read_text())
        target = base["racket_target"]
        self.assertEqual(MODULE.RULE_HASH, "79b7067ac64d")
        self.assertEqual(MODULE.RULE_HASH, _normalized_hash(canonical))
        self.assertEqual(_normalized_hash(target["target_code"]), _normalized_hash(canonical))
        self.assertEqual(target["target_code_role"], "selected_task_rule")
        self.assertEqual(target["raw_code_role"], "archival_executable_source")
        self.assertNotEqual(target["raw_code"], canonical)

    def test_boundary_overrides_are_exact_in_every_band(self):
        for band in BANDS:
            for n in (3, 7):
                for palette_size in (3, 6):
                    for fill_mode in ("dense", "sparse"):
                        for seed in range(8):
                            grid = MODULE.generate(
                                1000 + seed,
                                37 * seed + 5,
                                difficulty=band,
                                grid_n=n,
                                palette_size=palette_size,
                                fill_mode=fill_mode,
                            )
                            self.assertEqual(MODULE.self_check(grid), [])
                            self.assertEqual(
                                MODULE.observe_overrides(grid),
                                {
                                    "grid_n": n,
                                    "palette_size": palette_size,
                                    "fill_mode": fill_mode,
                                },
                            )

    def test_unknown_override_is_rejected_loudly(self):
        with self.assertRaisesRegex(ValueError, "unknown override"):
            MODULE.generate(1, 2, difficulty="easy", typo_palette_size=4)

    def test_default_strict_profile_floor_and_stability(self):
        for seed_start in (0, 100_000):
            for band in BANDS:
                strict = 0
                inputs = set()
                for offset in range(200):
                    seed = seed_start + offset
                    grid = MODULE.generate(seed, seed * 19 + 7, difficulty=band)
                    self.assertEqual(MODULE.self_check(grid), [])
                    strict += MODULE.strict_canonical_like(grid)
                    inputs.add(_freeze(grid))
                self.assertGreaterEqual(strict, 10, (seed_start, band, strict))
                self.assertGreaterEqual(len(inputs), 195, (seed_start, band, len(inputs)))

    def test_default_grid_and_palette_axes_are_not_locked(self):
        observed = []
        for band in BANDS:
            for seed in range(4):
                grid = MODULE.generate(seed, seed * 17 + 3, difficulty=band)
                values = MODULE.observe_overrides(grid)
                observed.append((values["grid_n"], values["palette_size"]))

        pairs = set(observed)
        grid_sizes = {grid_n for grid_n, _ in pairs}
        palette_sizes = {palette_size for _, palette_size in pairs}
        one_to_one_locked = (
            len(pairs) >= 3
            and len(grid_sizes) == len(palette_sizes) == len(pairs)
        )
        self.assertFalse(one_to_one_locked, sorted(pairs))
        self.assertTrue(
            any(grid_n != palette_size for grid_n, palette_size in pairs),
            sorted(pairs),
        )

    def test_every_generated_panel_distinguishes_rotations_and_fires(self):
        for band in BANDS:
            for seed in range(100):
                grid = MODULE.generate(20_000 + seed, seed * 13 + 11, difficulty=band)
                n = len(grid)
                panel = [row[:n] for row in grid]
                self.assertEqual(len(set(MODULE._rotation_signatures(panel))), 4)
                output = MODULE.rule_mirror(grid)
                self.assertNotEqual(output, grid)
                self.assertEqual(output, MODULE.rule_mirror(copy.deepcopy(grid)))
                self.assertEqual(grid, MODULE.generate(20_000 + seed, seed * 13 + 11, difficulty=band))

    def test_mutation_fixtures_are_rejected(self):
        fixtures = MODULE.mutation_fixtures()
        self.assertGreaterEqual(len(fixtures), 4)
        for name, grid in fixtures:
            with self.subTest(name=name):
                self.assertTrue(MODULE.self_check(grid), name)

    def test_determinism_fresh_returns_and_global_rng_purity(self):
        random.seed(20260724)
        state = random.getstate()
        first = MODULE.generate(9123, 4567, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MODULE.generate(9123, 4567, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))
        first[0][0] = 0
        third = MODULE.generate(9123, 4567, difficulty="hard")
        self.assertEqual(second, third)


if __name__ == "__main__":
    unittest.main()
