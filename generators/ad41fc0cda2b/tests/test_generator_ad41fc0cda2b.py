"""Focused semantic and harness regressions for generator ad41fc0cda2b."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
import random
import unittest


TASK_ID = "ad41fc0cda2b"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PATHS = (
    ROOT / "data/base/solutions/training/8a004b2b__ad41fc0cda2b.json",
    ROOT / "data/base/solutions/augmented/8a004b2b__5b0bda22c9c3.json",
)


def _canonical_rows():
    return [
        row
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    ]


def _canonical_pairs():
    pairs = []
    for row in _canonical_rows():
        pairs.extend(row.get("train", []))
        pairs.extend(row.get("test", []))
    return pairs


def _normalized_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


class GeneratorAd41fc0cda2bTests(unittest.TestCase):
    def test_all_canonical_source_rows_and_eight_pair_occurrences(self):
        rows = _canonical_rows()
        pairs = _canonical_pairs()
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(pairs), 8)
        witnessed = set()
        for pair in pairs:
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            self.assertEqual(MODULE.self_check(source), [])
            self.assertEqual(MODULE.rule_mirror(source), pair["output"])
            self.assertEqual(source, before)
            observed = MODULE.observe_overrides(source)
            self.assertIn(observed["scene_variant"], MODULE.VARIANT_NAMES)
            witnessed.add(observed["scene_variant"])
        self.assertEqual(witnessed, set(MODULE.VARIANT_NAMES))

    def test_exact_override_cross_product_is_observable(self):
        observed = set()
        for band in ("easy", "medium", "hard"):
            for variant in MODULE.VARIANT_NAMES:
                for palette_band in MODULE.PALETTE_KINDS:
                    for seed in range(4):
                        overrides = {
                            "scene_variant": variant,
                            "palette_band": palette_band,
                        }
                        grid = MODULE.generate(
                            2000 + seed,
                            3000 + seed,
                            difficulty=band,
                            **overrides,
                        )
                        self.assertEqual(MODULE.self_check(grid), [])
                        self.assertEqual(MODULE.observe_overrides(grid), overrides)
                        observed.add((variant, palette_band))
        self.assertEqual(
            observed,
            {(variant, palette) for variant in MODULE.VARIANT_NAMES for palette in MODULE.PALETTE_KINDS},
        )

    def test_invalid_overrides_reject_loudly(self):
        for overrides in (
            {"scene_variant": "not-a-variant"},
            {"palette_band": "middle"},
            {"unused_axis": True},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises((KeyError, TypeError, ValueError)):
                    MODULE.generate(1, 2, **overrides)

    def test_determinism_fresh_returns_and_global_rng_preservation(self):
        random.seed(20260724)
        state = random.getstate()
        first = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))
        second[0][0] = 9 if second[0][0] != 9 else 8
        self.assertNotEqual(first, second)

    def test_ordinary_schedule_covers_all_branches_and_identifies_lessons(self):
        for band in ("easy", "medium", "hard"):
            scenes = []
            for sample_index in range(24):
                grid = MODULE.generate(3100 + sample_index, sample_index, difficulty=band)
                self.assertEqual(MODULE.self_check(grid), [])
                scenes.append({"input": grid, "output": MODULE.rule_mirror(grid)})
            observed = {
                MODULE.observe_overrides(scene["input"])["scene_variant"]
                for scene in scenes
            }
            self.assertEqual(observed, set(MODULE.VARIANT_NAMES))
            for start in range(0, 20):
                demos = scenes[start : start + 3]
                query = scenes[start + 3]
                self.assertEqual(MODULE.lesson_identifiable(demos, query), [])

    def test_semantic_witnesses_have_positive_examples(self):
        grids = [
            MODULE.generate(4000 + i, i, difficulty=band)
            for band in ("easy", "medium", "hard")
            for i in range(12)
        ]
        missing = [
            name
            for name, predicate in MODULE.SEMANTIC_WITNESSES.items()
            if not any(predicate(grid) for grid in grids)
        ]
        self.assertEqual(missing, [])

    def test_self_check_rejects_targeted_nearest_impostors(self):
        base = MODULE.generate(
            5001,
            0,
            scene_variant="small_square",
            palette_band="high",
        )
        analysis, errors = MODULE._analyze(base)
        self.assertEqual(errors, [])
        self.assertIsNotNone(analysis)
        variant = analysis.variant
        role_at = MODULE._role_map(variant)
        bs = variant.block_size
        origin_r, origin_c = variant.output_origin

        missing_corner = copy.deepcopy(base)
        r, c = sorted(MODULE._corners(variant))[0]
        missing_corner[r][c] = 0

        full_frame_edge = copy.deepcopy(base)
        full_frame_edge[variant.frame_top][variant.frame_left + 1] = 4

        broken_reference = copy.deepcopy(base)
        dr, dc = variant.reference_cells[0]
        rr = variant.frame_top + origin_r + dr * bs
        cc = variant.frame_left + origin_c + dc * bs
        broken_reference[rr][cc] = 0

        broken_key_role = copy.deepcopy(base)
        dr, dc, _role = variant.key_roles[0]
        broken_key_role[variant.key_top + dr][variant.key_left + dc] = 0

        unprojected_material = copy.deepcopy(base)
        missing = next(pos for pos in role_at if pos not in set(variant.reference_cells))
        dr, dc = missing
        rr = variant.frame_top + origin_r + dr * bs
        cc = variant.frame_left + origin_c + dc * bs
        unprojected_material[rr][cc] = analysis.role_colors[role_at[missing]]

        palette_collision = copy.deepcopy(base)
        a_color = analysis.role_colors["a"]
        for dr, dc, role in variant.key_roles:
            if role == "b":
                palette_collision[variant.key_top + dr][variant.key_left + dc] = a_color
        for dr, dc in variant.reference_cells:
            if role_at[(dr, dc)] == "b":
                top = variant.frame_top + origin_r + dr * bs
                left = variant.frame_left + origin_c + dc * bs
                for r2 in range(top, top + bs):
                    for c2 in range(left, left + bs):
                        palette_collision[r2][c2] = a_color

        impostors = {
            "missing_corner": missing_corner,
            "full_frame_edge": full_frame_edge,
            "broken_reference": broken_reference,
            "broken_key_role": broken_key_role,
            "unprojected_material": unprojected_material,
            "palette_collision": palette_collision,
        }
        for name, grid in impostors.items():
            with self.subTest(name=name):
                self.assertTrue(MODULE.self_check(grid))

    def test_rule_hash_and_selected_authorities_are_synchronized(self):
        rows = _canonical_rows()
        canonical = rows[0]["program_solution"]
        self.assertTrue(all(row["program_solution"] == canonical for row in rows))
        self.assertEqual(MODULE.RULE_HASH, _normalized_hash(canonical))
        self.assertEqual(MODULE.RULE_HASH, "22b0a6e75254")
        for path in AUTHORITY_PATHS:
            authority = json.loads(path.read_text())
            self.assertEqual(authority["racket_target"]["target_code"], canonical)


if __name__ == "__main__":
    unittest.main()
