"""Focused semantic regressions for generator 113d9bb402d3."""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib
import json
from pathlib import Path
import random
import unittest


TASK_ID = "113d9bb402d3"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SOURCE_SHA256 = (
    "b5e965f505173cf9843556ceebe86a5c95310ea63a0dc594080177e8ff175a63"
)


def _canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


def _normalized_hash(source):
    normalized = " ".join(source.split())
    return hashlib.sha256(normalized.encode()).hexdigest()[:12]


class Generator113d9bb402d3Tests(unittest.TestCase):
    def test_all_canonical_pairs_and_linked_profiles(self):
        row = _canonical_row()
        pairs = [*row["train"], *row["test"]]
        self.assertEqual(len(pairs), 4)
        observed = set()
        for pair in pairs:
            self.assertEqual(MODULE.self_check(pair["input"]), [])
            self.assertEqual(MODULE.rule_mirror(pair["input"]), pair["output"])
            signature = MODULE.canonical_profile_signature(pair["input"])
            self.assertIsNotNone(signature)
            observed.add(signature)
        self.assertEqual(observed, set(MODULE._CANONICAL_PROFILES))

    def test_every_official_profile_has_main_and_disjoint_coverage(self):
        expected = set(MODULE._CANONICAL_PROFILES)
        for band in ("easy", "medium", "hard"):
            main = Counter()
            disjoint = Counter()
            for seed in range(600):
                grid = MODULE.generate(seed, seed, difficulty=band)
                signature = MODULE.canonical_profile_signature(grid)
                if signature is not None:
                    main[signature] += 1
                grid = MODULE.generate(
                    seed + 50_000,
                    seed * 17 + 3,
                    difficulty=band,
                )
                signature = MODULE.canonical_profile_signature(grid)
                if signature is not None:
                    disjoint[signature] += 1
            self.assertEqual(set(main), expected)
            self.assertEqual(set(disjoint), expected)
            self.assertGreater(sum(main.values()), 120)
            self.assertGreater(sum(disjoint.values()), 120)
            self.assertLess(sum(main.values()), 280)
            self.assertLess(sum(disjoint.values()), 280)

    def test_exact_axes_boundaries_modes_and_provenance(self):
        cases = [
            {"grid_h": 11},
            {"grid_h": 30},
            {"grid_w": 11},
            {"grid_w": 30},
            {"bbox_h": 3},
            {"bbox_h": 9},
            {"bbox_w": 3},
            {"bbox_w": 9},
            *({"cyan_level": value} for value in MODULE.CYAN_LEVELS),
            *({"zone_coverage": value} for value in MODULE.ZONE_COVERAGES),
            *({"outside_level": value} for value in MODULE.OUTSIDE_LEVELS),
            *({"bbox_position": value} for value in MODULE.BBOX_POSITIONS),
            {"grid_h": 11, "bbox_position": "corner"},
            {"grid_w": 11, "bbox_position": "interior"},
            {
                "grid_h": 11,
                "grid_w": 11,
                "bbox_h": 3,
                "bbox_w": 3,
                "cyan_level": "sparse",
                "zone_coverage": "complete",
                "outside_level": "sparse",
                "bbox_position": "interior",
            },
            {
                "grid_h": 30,
                "grid_w": 30,
                "bbox_h": 9,
                "bbox_w": 9,
                "cyan_level": "dense",
                "zone_coverage": "gapped",
                "outside_level": "dense",
                "bbox_position": "corner",
            },
        ]
        for band in ("easy", "medium", "hard"):
            for index, overrides in enumerate(cases):
                grid = MODULE.generate(
                    700 + index,
                    1900 + index,
                    difficulty=band,
                    **overrides,
                )
                observed = MODULE.observe_overrides(grid)
                for name, value in overrides.items():
                    self.assertEqual(observed[name], value, (band, overrides, observed))
                self.assertEqual(
                    MODULE.self_check(
                        grid,
                        difficulty=band,
                        meta={"overrides": overrides},
                    ),
                    [],
                )

    def test_default_semantic_branches_and_oracle(self):
        for band in ("easy", "medium", "hard"):
            cyan_levels = Counter()
            coverage = Counter()
            outside_levels = Counter()
            positions = Counter()
            bbox_shapes = Counter()
            for seed in range(400):
                grid = MODULE.generate(seed + 9000, seed, difficulty=band)
                self.assertEqual(MODULE.self_check(grid), [])
                observed = MODULE.observe_overrides(grid)
                cyan_levels[observed["cyan_level"]] += 1
                coverage[observed["zone_coverage"]] += 1
                outside_levels[observed["outside_level"]] += 1
                positions[observed["bbox_position"]] += 1
                bbox_shapes[(observed["bbox_h"], observed["bbox_w"])] += 1

                output = MODULE.rule_mirror(grid)
                info = MODULE._analysis(grid)
                r0, c0, r1, c1 = info["box"]
                changed = 0
                for row in range(len(grid)):
                    for col in range(len(grid[0])):
                        inside = r0 <= row <= r1 and c0 <= col <= c1
                        if inside and grid[row][col] == 1:
                            self.assertEqual(output[row][col], 3)
                            changed += 1
                        else:
                            self.assertEqual(output[row][col], grid[row][col])
                self.assertEqual(changed, info["inside_blue"])
                self.assertGreater(changed, 0)
            self.assertEqual(set(cyan_levels), set(MODULE.CYAN_LEVELS))
            self.assertEqual(set(coverage), set(MODULE.ZONE_COVERAGES))
            self.assertEqual(set(outside_levels), set(MODULE.OUTSIDE_LEVELS))
            self.assertEqual(set(positions), set(MODULE.BBOX_POSITIONS))
            self.assertGreaterEqual(len(bbox_shapes), 9)

    def test_negative_recombination_and_shortcut_rivals(self):
        hybrid = MODULE.generate(
            61,
            83,
            difficulty="medium",
            grid_h=17,
            grid_w=17,
            bbox_h=3,
            bbox_w=8,
            cyan_level="dense",
            zone_coverage="gapped",
            outside_level="dense",
            bbox_position="interior",
        )
        self.assertEqual(MODULE.self_check(hybrid), [])
        self.assertIsNone(MODULE.canonical_profile_signature(hybrid))
        info = MODULE._analysis(hybrid)
        output = MODULE.rule_mirror(hybrid)
        r0, c0, r1, c1 = info["box"]
        self.assertTrue(any(
            hybrid[row][col] == 1 and output[row][col] == 3
            for row in range(r0, r1 + 1)
            for col in range(c0, c1 + 1)
        ))
        self.assertTrue(any(
            hybrid[row][col] == 1 and output[row][col] == 1
            for row in range(len(hybrid))
            for col in range(len(hybrid[0]))
            if not (r0 <= row <= r1 and c0 <= col <= c1)
        ))
        self.assertTrue(any(
            hybrid[row][col] == 8 and output[row][col] == 8
            for row in range(r0, r1 + 1)
            for col in range(c0, c1 + 1)
        ))

    def test_self_check_rejects_nearest_structural_mutations(self):
        grid = MODULE.generate(
            331,
            77,
            difficulty="hard",
            grid_h=24,
            grid_w=25,
            bbox_h=6,
            bbox_w=7,
            cyan_level="balanced",
            zone_coverage="gapped",
            outside_level="balanced",
            bbox_position="edge",
        )
        info = MODULE._analysis(grid)
        r0, c0, r1, c1 = info["box"]
        mutations = []

        changed = [row[:] for row in grid]
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                if changed[row][col] == 1:
                    changed[row][col] = 0
        mutations.append(changed)

        changed = [row[:] for row in grid]
        for row in range(len(changed)):
            for col in range(len(changed[0])):
                if not (r0 <= row <= r1 and c0 <= col <= c1) and changed[row][col] == 1:
                    changed[row][col] = 0
        mutations.append(changed)

        changed = [row[:] for row in grid]
        for row in range(len(changed)):
            for col in range(len(changed[0])):
                if changed[row][col] == 8:
                    changed[row][col] = 0
        mutations.append(changed)

        changed = [row[:] for row in grid]
        changed[0][0] = 3
        mutations.append(changed)

        changed = [row[:] for row in grid]
        changed[0][0] = True
        mutations.append(changed)

        changed = [row[:] for row in grid]
        changed[0] = changed[0][:-1]
        mutations.append(changed)

        for changed in mutations:
            self.assertTrue(MODULE.self_check(changed), changed)

    def test_invalid_requests_fail_loudly(self):
        invalid = [
            {"unknown_axis": 1},
            {"grid_h": 10},
            {"grid_w": 31},
            {"bbox_h": 2},
            {"bbox_w": 10},
            {"cyan_level": "solid"},
            {"zone_coverage": "empty"},
            {"outside_level": "none"},
            {"bbox_position": "scattered"},
        ]
        for overrides in invalid:
            with self.assertRaises(ValueError, msg=overrides):
                MODULE.generate(1, 2, difficulty="medium", **overrides)
        with self.assertRaises(ValueError):
            MODULE.generate(1, 2, difficulty="impossible")

    def test_determinism_fresh_returns_and_global_rng_isolation(self):
        kwargs = {
            "difficulty": "hard",
            "bbox_h": 9,
            "bbox_w": 9,
            "cyan_level": "dense",
            "zone_coverage": "gapped",
            "outside_level": "dense",
            "bbox_position": "corner",
        }
        random.seed(8128)
        before = random.getstate()
        first = MODULE.generate(19, 23, **kwargs)
        after = random.getstate()
        second = MODULE.generate(19, 23, **kwargs)
        self.assertEqual(before, after)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = (first[0][0] + 1) % 10
        self.assertNotEqual(first, second)

    def test_rule_hash_and_live_target_are_synchronized(self):
        canonical = _canonical_row()["program_solution"]
        base = json.loads((
            ROOT / "data/base/solutions/training/32597951__113d9bb402d3.json"
        ).read_text())
        target = base["racket_target"]["target_code"]
        self.assertEqual(_normalized_hash(canonical), MODULE.RULE_HASH)
        self.assertEqual(_normalized_hash(target), MODULE.RULE_HASH)
        self.assertEqual(
            base["primitive_metadata"]["primitive_chain"],
            [
                "rows", "cols", "filter", "for*/list", "range", "at",
                "reduce", "first", "map", "second", "cellmap",
            ],
        )
        self.assertEqual(
            _normalized_hash(base["racket_target"]["raw_code"]),
            "49ac93d5467b",
        )

    def test_frozen_generator_snapshot(self):
        digest = hashlib.sha256(Path(MODULE.__file__).read_bytes()).hexdigest()
        self.assertEqual(digest, EXPECTED_SOURCE_SHA256)


if __name__ == "__main__":
    unittest.main()
