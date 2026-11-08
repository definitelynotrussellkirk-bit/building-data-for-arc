"""Focused semantic and contract tests for generator 45922a9666b2."""
from __future__ import annotations

import hashlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

from reviewer_support import (
    canonical_pairs, canonical_path, find_root, load_selected_generator,
)


ROOT = find_root(__file__)
generator, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(
    "45922a9666b2", root=ROOT
)
DATA = canonical_path(ROOT).parent.parent
BASE_FILES = (
    DATA / "base/solutions/training/712bf12e__45922a9666b2.json",
    DATA / "base/solutions/augmented/712bf12e__ac128353ea80.json",
)


def canonical_rows():
    rows = []
    with canonical_path(ROOT).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == generator.TASK_ID:
                rows.append(row)
    return rows


def all_canonical_pairs():
    return canonical_pairs(generator.TASK_ID, root=ROOT, labeled_only=True)


def unique_canonical_pairs():
    pairs = []
    seen = set()
    for pair in all_canonical_pairs():
        key = tuple(map(tuple, pair["input"]))
        if key not in seen:
            seen.add(key)
            pairs.append(pair)
    return pairs


def normalized_rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def turn_count(cells):
    return sum(
        next_row == row and next_col == col + 1
        for (row, col), (next_row, next_col) in zip(cells, cells[1:])
    )


class Generator45922a9666b2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = canonical_rows()
        cls.all_pairs = all_canonical_pairs()
        cls.pairs = unique_canonical_pairs()

    def test_all_linked_rows_pairs_profiles_and_rule(self):
        self.assertEqual(len(self.rows), 2)
        self.assertEqual(len(self.all_pairs), 8)
        self.assertEqual(len(self.pairs), 4)
        expected = (
            ((13, 14), (2, 5, 10), (15, 5, 16), (2, 0, 3),
             ("top", "boxed", "top"), 35),
            ((12, 13), (2, 5, 9), (13, 11, 13), (1, 1, 1),
             ("top", "boxed", "top"), 25),
            ((13, 15), (3, 7, 9), (15, 15, 16), (2, 2, 3),
             ("top", "top", "top"), 45),
            ((13, 13), (3, 7, 9), (14, 6, 11), (1, 1, 3),
             ("top", "boxed", "right_edge"), 46),
        )
        for index, (profile, pair) in enumerate(
            zip(generator.SCENE_PROFILES, self.pairs)
        ):
            source = pair["input"]
            snapshot = [row[:] for row in source]
            self.assertEqual(source, generator._profile_grid(profile))
            self.assertEqual(generator.self_check(source), [])
            self.assertEqual(generator.canonical_profile_index(source), index)
            self.assertEqual(
                generator.observe_overrides(source),
                {
                    "scene_profile": profile,
                    "route_layout": "canonical",
                },
            )
            height, width, _reds, starts, paths, gray_count = (
                generator._path_signature(source)
            )
            self.assertEqual((height, width), expected[index][0])
            self.assertEqual(starts, expected[index][1])
            self.assertEqual(
                tuple(len(cells) for cells, _stop in paths),
                expected[index][2],
            )
            self.assertEqual(
                tuple(turn_count(cells) for cells, _stop in paths),
                expected[index][3],
            )
            self.assertEqual(
                tuple(stop for _cells, stop in paths),
                expected[index][4],
            )
            self.assertEqual(gray_count, expected[index][5])
            self.assertEqual(generator.rule_mirror(source), pair["output"])
            self.assertEqual(source, snapshot)
        for pair in self.all_pairs:
            self.assertEqual(
                generator.rule_mirror(pair["input"]),
                pair["output"],
            )

    def test_every_exact_axis_combination_and_constructive_constraints(self):
        for band in ("easy", "medium", "hard"):
            for profile_index, profile in enumerate(
                generator.SCENE_PROFILES
            ):
                for layout_index, layout in enumerate(
                    generator.ROUTE_LAYOUTS
                ):
                    seed = (
                        10_000
                        + 1_000 * profile_index
                        + 100 * layout_index
                        + len(band)
                    )
                    grid = generator.generate(
                        seed,
                        seed * 17 + 3,
                        difficulty=band,
                        scene_profile=profile,
                        route_layout=layout,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(
                        generator.observe_overrides(grid),
                        {
                            "scene_profile": profile,
                            "route_layout": layout,
                        },
                    )
                    self.assertEqual(
                        generator._role_signature(
                            len(grid),
                            len(grid[0]),
                            generator._path_signature(grid)[4],
                            generator._path_signature(grid)[5],
                        ),
                        generator._profile_role_signature(profile),
                    )
                    self.assertNotEqual(grid, generator.rule_mirror(grid))
                    if layout == "canonical":
                        self.assertEqual(
                            generator._path_signature(grid)[4],
                            generator._profile_signature(profile)[4],
                        )
                    else:
                        self.assertNotEqual(
                            generator._path_signature(grid)[4],
                            generator._profile_signature(profile)[4],
                        )
                        constraints = generator._constraints_for_paths(
                            generator._path_signature(grid)[4]
                        )
                        self.assertIsNotNone(constraints)
                        open_cells, critical_gray = constraints
                        self.assertTrue(
                            all(grid[row][col] != 5
                                for row, col in open_cells)
                        )
                        self.assertTrue(
                            all(grid[row][col] == 5
                                for row, col in critical_gray)
                        )

    def test_main_and_disjoint_distributions_are_complete_and_diverse(self):
        for start in (0, 50_000):
            for band_index, band in enumerate(
                ("easy", "medium", "hard")
            ):
                profiles = Counter()
                layouts = Counter()
                route_geometries = set()
                inputs = set()
                outputs = set()
                for offset in range(300):
                    seed = start + 10_000 * band_index + offset
                    grid = generator.generate(
                        seed,
                        seed * 29 + 7,
                        difficulty=band,
                    )
                    output = generator.rule_mirror(grid)
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertNotEqual(grid, output)
                    observed = generator.observe_overrides(grid)
                    profiles[observed["scene_profile"]] += 1
                    layouts[observed["route_layout"]] += 1
                    if observed["route_layout"] == "procedural":
                        route_geometries.add(
                            generator._path_signature(grid)[3:5]
                        )
                    inputs.add(json.dumps(grid, separators=(",", ":")))
                    outputs.add(json.dumps(output, separators=(",", ":")))
                self.assertEqual(set(profiles), set(generator.SCENE_PROFILES))
                self.assertEqual(set(layouts), set(generator.ROUTE_LAYOUTS))
                self.assertGreaterEqual(len(route_geometries), 200)
                self.assertGreaterEqual(len(inputs), 295)
                self.assertGreaterEqual(len(outputs), 295)

    def test_strict_checker_rejects_answer_bearing_recombinations(self):
        profile = "profile_13x14_mixed"
        canonical = generator._profile_grid(profile)
        (
            open_cells,
            critical_gray,
            candidates,
            canonical_nuisance,
        ) = generator._profile_constraints(profile)
        path_zero = next(
            cell
            for cell in open_cells
            if canonical[cell[0]][cell[1]] == 0
        )
        nuisance_gray = min(canonical_nuisance)
        unused_candidate = next(
            cell
            for cell in candidates
            if canonical[cell[0]][cell[1]] == 0
        )
        critical = min(critical_gray)
        mutations = []

        moved_critical = [row[:] for row in canonical]
        moved_critical[critical[0]][critical[1]] = 0
        moved_critical[unused_candidate[0]][unused_candidate[1]] = 5
        mutations.append(moved_critical)

        blocked_path = [row[:] for row in canonical]
        blocked_path[path_zero[0]][path_zero[1]] = 5
        blocked_path[nuisance_gray[0]][nuisance_gray[1]] = 0
        mutations.append(blocked_path)

        moved_start = [row[:] for row in canonical]
        moved_start[-1][2] = 0
        moved_start[-1][1] = 2
        mutations.append(moved_start)

        extra_red = [row[:] for row in canonical]
        extra_red[0][0] = 2
        mutations.append(extra_red)

        wrong_gray_count = [row[:] for row in canonical]
        wrong_gray_count[nuisance_gray[0]][nuisance_gray[1]] = 0
        mutations.append(wrong_gray_count)

        cropped = [row[:-1] for row in canonical]
        mutations.append(cropped)

        for mutation in mutations:
            self.assertTrue(generator.self_check(mutation))
            self.assertEqual(generator.observe_overrides(mutation), {})

        invalid_grids = (
            [],
            [[0] * 31],
            [[False, 2], [5, 0]],
            [[10, 2], [5, 0]],
        )
        for invalid in invalid_grids:
            self.assertTrue(generator.self_check(invalid))

    def test_rule_mirror_remains_broad_and_input_pure(self):
        grid = [
            [0, 0, 0, 0, 0, 0],
            [0, 0, 2, 0, 0, 0],
            [0, 5, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 2, 0, 0, 0, 0],
        ]
        expected = [
            [0, 0, 2, 0, 0, 0],
            [0, 0, 2, 0, 0, 0],
            [0, 5, 2, 0, 0, 0],
            [0, 2, 2, 0, 0, 0],
            [0, 2, 0, 0, 0, 0],
        ]
        snapshot = [row[:] for row in grid]
        self.assertEqual(generator.rule_mirror(grid), expected)
        self.assertEqual(grid, snapshot)
        self.assertTrue(generator.self_check(grid))

    def test_selected_authority_sync_and_archival_preservation(self):
        source = self.rows[0]["program_solution"]
        self.assertTrue(all(row["program_solution"] == source for row in self.rows))
        expected_hash = normalized_rule_hash(source)[:12]
        self.assertEqual(generator.RULE_HASH, expected_hash)
        for path in BASE_FILES:
            row = json.loads(path.read_text())
            self.assertEqual(row["racket_target"]["target_code"], source)
            self.assertEqual(
                row["primitive_metadata"]["primitive_chain"],
                ["rows", "cols", "filter", "at", "range", "reduce",
                 "first", "second", "third", "fourth", "map", "cellmap"],
            )
            # raw_code is an archival authority and must not be rewritten to
            # make a selected-authority synchronization test pass.
            self.assertEqual(
                hashlib.sha256(row["racket_target"]["raw_code"].encode()).hexdigest(),
                "a77991e0359e6569981b9f0b544a2c35136128bde226541e18e9b0bdf6fefcac",
            )

    def test_determinism_fresh_returns_global_rng_and_invalid_calls(self):
        before = random.getstate()
        first = generator.generate(321, 654, difficulty="hard")
        after = random.getstate()
        second = generator.generate(321, 654, difficulty="hard")
        self.assertEqual(before, after)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = (first[0][0] + 1) % 10
        third = generator.generate(321, 654, difficulty="hard")
        self.assertEqual(second, third)

        with self.assertRaises(ValueError):
            generator.generate(1, 2, difficulty="impossible")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, unknown_axis="x")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, scene_profile="missing")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, route_layout="missing")


if __name__ == "__main__":
    unittest.main()
