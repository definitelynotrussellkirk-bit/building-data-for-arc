"""Focused semantic regressions for generator 1137ac565856."""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib
import json
from pathlib import Path
import random
import unittest


TASK_ID = "1137ac565856"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SOURCE_SHA256 = (
    "25eaead4df876be4fc5214d816201b10b0af2420fc9ffee543e614189976cf26"
)


def _canonical_row():
    path = ROOT / "data/canonical/puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


def _normalized_hash(source):
    normalized = " ".join(source.split())
    return hashlib.sha256(normalized.encode()).hexdigest()[:12]


def _frame_data(grid):
    info = MODULE._analysis(grid)
    if info["errors"]:
        raise AssertionError(info["errors"])
    return info


class Generator1137ac565856Tests(unittest.TestCase):
    def test_all_canonical_pairs_and_linked_profiles(self):
        row = _canonical_row()
        pairs = [*row["train"], *row["test"]]
        expected = {
            (11, 11, ((9, 9), (5, 5))),
            (11, 12, ((9, 10), (5, 5))),
            (13, 13, ((11, 11), (7, 7), (3, 3))),
        }
        observed = set()
        self.assertEqual(len(pairs), 3)
        for pair in pairs:
            self.assertEqual(MODULE.self_check(pair["input"]), [])
            self.assertEqual(MODULE.rule_mirror(pair["input"]), pair["output"])
            signature = MODULE.canonical_profile_signature(pair["input"])
            self.assertIsNotNone(signature)
            observed.add(signature)
        self.assertEqual(observed, expected)

    def test_every_official_profile_has_default_main_and_disjoint_coverage(self):
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
            {"n_frames": 2},
            {"n_frames": 4},
            {"frame_gap": 1},
            {"frame_gap": 3},
            {"outer_margin": 0},
            {"outer_margin": 3},
            {"marker_mode": "centered"},
            {"marker_mode": "off_center"},
            {"grid_h": 11, "marker_mode": "off_center"},
            {"grid_w": 11, "marker_mode": "off_center"},
            {
                "grid_h": 11,
                "grid_w": 11,
                "n_frames": 2,
                "frame_gap": 1,
                "outer_margin": 0,
                "marker_mode": "centered",
            },
            {
                "grid_h": 30,
                "grid_w": 30,
                "n_frames": 4,
                "frame_gap": 3,
                "outer_margin": 3,
                "marker_mode": "off_center",
            },
        ]
        for band in ("easy", "medium", "hard"):
            for index, overrides in enumerate(cases):
                grid = MODULE.generate(
                    701 + index,
                    1901 + index,
                    difficulty=band,
                    **overrides,
                )
                observed = MODULE.observe_overrides(grid)
                for name, value in overrides.items():
                    self.assertEqual(
                        observed[name],
                        value,
                        (band, overrides, observed),
                    )
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
            frames = Counter()
            gaps = Counter()
            margins = Counter()
            marker_modes = Counter()
            output_shapes = Counter()
            for seed in range(400):
                grid = MODULE.generate(seed + 9000, seed, difficulty=band)
                self.assertEqual(MODULE.self_check(grid), [])
                info = _frame_data(grid)
                observed = MODULE.observe_overrides(grid)
                frames[observed["n_frames"]] += 1
                gaps[observed["frame_gap"]] += 1
                margins[observed["outer_margin"]] += 1
                marker_modes[observed["marker_mode"]] += 1
                output = MODULE.rule_mirror(grid)
                output_shapes[(len(output), len(output[0]))] += 1
                chosen = info["frames"][-1]
                self.assertTrue(all(
                    value == chosen["color"]
                    for row in output
                    for value in row
                ))
                r0, c0, r1, c1 = chosen["box"]
                self.assertEqual((len(output), len(output[0])), (r1-r0+1, c1-c0+1))
            self.assertEqual(set(frames), {2, 3, 4})
            self.assertEqual(set(gaps), {1, 2, 3})
            self.assertEqual(set(margins), {0, 1, 2, 3})
            self.assertEqual(set(marker_modes), set(MODULE.MARKER_MODES))
            self.assertGreaterEqual(len(output_shapes), 20)

    def test_negative_recombination_and_smallest_frame_shortcuts(self):
        hybrid = MODULE.generate(
            61,
            83,
            difficulty="medium",
            grid_h=11,
            grid_w=11,
            n_frames=3,
            frame_gap=1,
            outer_margin=1,
            marker_mode="centered",
        )
        self.assertEqual(MODULE.self_check(hybrid), [])
        self.assertIsNone(MODULE.canonical_profile_signature(hybrid))
        self.assertEqual(
            MODULE.profile_signature(hybrid),
            (11, 11, ((9, 9), (7, 7), (5, 5))),
        )

        info = _frame_data(hybrid)
        output = MODULE.rule_mirror(hybrid)
        outer = info["frames"][0]
        inner = info["frames"][-1]
        self.assertNotEqual(outer["color"], inner["color"])
        self.assertEqual(output[0][0], inner["color"])
        self.assertNotEqual(output[0][0], outer["color"])
        self.assertLess(len(output), outer["box"][2] - outer["box"][0] + 1)
        self.assertNotEqual(output[0][0], 2)

    def test_self_check_rejects_nearest_structural_mutations(self):
        grid = MODULE.generate(
            331,
            77,
            difficulty="hard",
            grid_h=24,
            grid_w=25,
            n_frames=3,
            frame_gap=2,
            outer_margin=1,
            marker_mode="off_center",
        )
        info = _frame_data(grid)
        marker = info["marker"]
        outer = info["frames"][0]

        mutations = []
        changed = [row[:] for row in grid]
        changed[marker[0]][marker[1]] = 0
        mutations.append(changed)

        changed = [row[:] for row in grid]
        changed[marker[0]][marker[1] + 1] = 2
        mutations.append(changed)

        changed = [row[:] for row in grid]
        r0, c0, _r1, _c1 = outer["box"]
        changed[r0][c0 + 2] = 0
        mutations.append(changed)

        changed = [row[:] for row in grid]
        changed[r0 + 2][c0 + 2] = outer["color"]
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
            {"n_frames": 1},
            {"frame_gap": 4},
            {"outer_margin": -1},
            {"marker_mode": "near_center"},
            {
                "grid_h": 11,
                "grid_w": 11,
                "n_frames": 4,
                "frame_gap": 3,
                "outer_margin": 3,
            },
        ]
        for overrides in invalid:
            with self.assertRaises(ValueError, msg=overrides):
                MODULE.generate(1, 2, difficulty="medium", **overrides)
        with self.assertRaises(ValueError):
            MODULE.generate(1, 2, difficulty="impossible")

    def test_determinism_fresh_returns_and_global_rng_isolation(self):
        kwargs = {
            "difficulty": "hard",
            "n_frames": 4,
            "frame_gap": 2,
            "outer_margin": 1,
            "marker_mode": "off_center",
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

    def test_rule_hash_and_all_live_sources_are_synchronized(self):
        canonical = _canonical_row()["program_solution"]
        bank = json.loads((
            ROOT / "data/custom_puzzles/banks/765a70430bc9/puzzles.json"
        ).read_text())
        bank_rows = bank if isinstance(bank, list) else bank["puzzles"]
        bank_row = next(row for row in bank_rows if row.get("id") == "H5")
        base = json.loads((
            ROOT / "data/base/solutions/banks/765a70430bc9/H5__1137ac565856.json"
        ).read_text())
        live_sources = (
            canonical,
            bank_row["program_solution"],
            base["racket_target"]["target_code"],
        )
        hashes = {_normalized_hash(source) for source in live_sources}
        self.assertEqual(hashes, {MODULE.RULE_HASH})
        self.assertEqual(
            _normalized_hash(base["racket_target"]["raw_code"]),
            MODULE.RULE_HASH,
        )

    def test_frozen_generator_snapshot(self):
        digest = hashlib.sha256(Path(MODULE.__file__).read_bytes()).hexdigest()
        self.assertEqual(digest, EXPECTED_SOURCE_SHA256)


if __name__ == "__main__":
    unittest.main()
