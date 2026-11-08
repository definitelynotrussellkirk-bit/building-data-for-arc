"""Focused regression tests for generator b2f8fcc010d5."""
from __future__ import annotations

import copy
import hashlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

from reviewer_support import canonical_path, find_root, load_selected_generator

ROOT = find_root(__file__)
TASK_ID = "b2f8fcc010d5"
GEN, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def _canonical_row():
    for line in canonical_path(ROOT).open():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical row missing")


def _norm_hash(text: str) -> str:
    return hashlib.sha256(" ".join(text.split()).encode()).hexdigest()[:12]


class GeneratorB2f8fcc010d5Tests(unittest.TestCase):
    def test_rule_hash_and_task_local_authorities_are_synced(self):
        row = _canonical_row()
        base_root = ROOT / "shared/data/base"
        if not base_root.is_dir():
            base_root = ROOT / "data/base"
        base = json.loads((base_root / "solutions/training/ca8de6ea__b2f8fcc010d5.json").read_text())
        self.assertEqual(GEN.RULE_HASH, _norm_hash(row["program_solution"]))
        raw = base["racket_target"]["raw_code"]
        target = base["racket_target"]["target_code"]
        self.assertEqual(raw, target)
        self.assertEqual(" ".join(raw.split()), " ".join(row["program_solution"].split()))
        self.assertEqual(" ".join(target.split()), " ".join(row["program_solution"].split()))

    def test_all_canonical_inputs_pass_and_mirror_exact_outputs(self):
        row = _canonical_row()
        for pair in [*row["train"], *row["test"]]:
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            self.assertEqual(GEN.self_check(source), [])
            self.assertEqual(GEN.rule_mirror(source), pair["output"])
            self.assertEqual(source, before)

    def test_every_override_boundary_is_exact_or_effective(self):
        for band in ("easy", "medium", "hard"):
            for palette_size in (5, 9):
                for kind in GEN.SAMPLED_KINDS:
                    for decoy_count in (0, 15):
                        grid = GEN.generate(
                            31,
                            17,
                            difficulty=band,
                            palette_size=palette_size,
                            sampled_kind=kind,
                            decoy_count=decoy_count,
                        )
                        self.assertEqual(GEN.self_check(grid, difficulty=band), [])
                        observed = GEN.observe_overrides(grid)
                        self.assertEqual(observed["palette_size"], palette_size)
                        self.assertEqual(observed["sampled_kind"], kind)
                        self.assertEqual(observed["decoy_count"], decoy_count)
            sparse = GEN.generate(42, 5, difficulty=band, decoy_count=0)
            dense = GEN.generate(42, 5, difficulty=band, decoy_count=15)
            sparse_decoys = sum(sparse[r][c] != 0 for r, c in GEN._DECOY_POSITIONS)
            dense_decoys = sum(dense[r][c] != 0 for r, c in GEN._DECOY_POSITIONS)
            self.assertEqual(sparse_decoys, 0)
            self.assertEqual(dense_decoys, 15)

    def test_default_distribution_has_linked_semantic_coverage(self):
        band_means = {}
        for band in ("easy", "medium", "hard"):
            kinds = Counter()
            inputs = set()
            outputs = set()
            decoys = []
            palettes = set()
            for seed in range(220):
                grid = GEN.generate(seed, seed * 37 + 11, difficulty=band)
                self.assertEqual(GEN.self_check(grid, difficulty=band), [])
                observed = GEN.observe_overrides(grid)
                kinds[observed["sampled_kind"]] += 1
                palettes.add(observed["palette_size"])
                inputs.add(json.dumps(grid, separators=(",", ":")))
                outputs.add(json.dumps(GEN.rule_mirror(grid), separators=(",", ":")))
                decoys.append(sum(grid[r][c] != 0 for r, c in GEN._DECOY_POSITIONS))
                nonzero = [value for row in grid for value in row if value != 0]
                self.assertNotEqual(nonzero[:9], [value for row in GEN.rule_mirror(grid) for value in row])
            self.assertEqual(set(kinds), set(GEN.SAMPLED_KINDS), (band, kinds))
            self.assertGreaterEqual(len(inputs), 215)
            self.assertGreaterEqual(len(outputs), 200)
            self.assertGreaterEqual(min(decoys), 2)
            self.assertGreaterEqual(len(palettes), 2)
            band_means[band] = sum(decoys) / len(decoys)
        self.assertLess(band_means["easy"], band_means["medium"])
        self.assertLess(band_means["medium"], band_means["hard"])

    def test_default_instances_rebut_nonzero_compression_shortcut(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(60):
                grid = GEN.generate(seed, seed + 1000, difficulty=band)
                nonzero = [value for row in grid for value in row if value != 0]
                output = [value for row in GEN.rule_mirror(grid) for value in row]
                self.assertGreater(len(nonzero), 9)
                self.assertNotEqual(nonzero[:9], output)

    def test_determinism_fresh_returns_and_global_rng_isolation(self):
        random.seed(8675309)
        state = random.getstate()
        first = GEN.generate(101, 9, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = GEN.generate(101, 9, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        first[0][0] = 0
        self.assertEqual(second, GEN.generate(101, 9, difficulty="hard"))

    def test_mutation_fixtures_and_minimal_impostors_reject(self):
        for name, grid in GEN.mutation_fixtures():
            with self.subTest(name=name):
                self.assertTrue(GEN.self_check(grid), name)
        minimal = {
            "all_background": [[0] * 5 for _ in range(5)],
            "full_one_color": [[1] * 5 for _ in range(5)],
            "singleton": [[1 if (r, c) == (2, 2) else 0 for c in range(5)] for r in range(5)],
            "solid_2x2": [[1 if r < 2 and c < 2 else 0 for c in range(5)] for r in range(5)],
            "short_line": [[1 if r == 2 and c < 4 else 0 for c in range(5)] for r in range(5)],
        }
        for name, grid in minimal.items():
            with self.subTest(name=name):
                self.assertTrue(GEN.self_check(grid), name)

    def test_unknown_controls_reject(self):
        with self.assertRaisesRegex(ValueError, "difficulty"):
            GEN.generate(1, 1, difficulty="extreme")
        with self.assertRaisesRegex(ValueError, "unknown override"):
            GEN.generate(1, 1, texture="noise")
        for bad in (-1, 16):
            with self.assertRaisesRegex(ValueError, "decoy_count"):
                GEN.generate(1, 1, decoy_count=bad)


if __name__ == "__main__":
    unittest.main()
