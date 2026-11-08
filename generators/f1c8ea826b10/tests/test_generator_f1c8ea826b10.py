from __future__ import annotations

import hashlib
import json
import random
import unittest
from pathlib import Path

from reviewer_support import canonical_path, find_root
from puzzle_generators import base
from puzzle_generators.per_puzzle.f1c8ea826b10 import generator


ROOT = find_root(__file__)


def canonical_row():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == generator.TASK_ID:
                return row
    raise KeyError(generator.TASK_ID)


def canonical_pairs():
    row = canonical_row()
    test = row["test"]
    return list(row["train"]) + (
        [test] if isinstance(test, dict) else list(test)
    )


def coerce(grid):
    return [
        [int(value) for value in row]
        if isinstance(row, str)
        else list(row)
        for row in grid
    ]


def independent_rule(grid):
    grid = coerce(grid)
    height = len(grid)
    width = len(grid[0])
    output = [
        [5 if value == 5 else 0 for value in row]
        for row in grid
    ]
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 5
    }
    while remaining:
        start = next(iter(remaining))
        region = set()
        pending = [start]
        while pending:
            row, col = pending.pop()
            if (row, col) in region:
                continue
            region.add((row, col))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = row + dr, col + dc
                if neighbor in remaining and neighbor not in region:
                    pending.append(neighbor)
        remaining.difference_update(region)
        colors = sorted({
            grid[row][col]
            for row, col in region
            if grid[row][col] != 0
        })
        top = min(row for row, _col in region)
        left = min(col for _row, col in region)
        for row, col in region:
            if len(colors) == 1:
                value = colors[0]
            else:
                value = (
                    colors[0]
                    if (row - top + col - left) % 2 == 0
                    else colors[-1]
                )
            output[row][col] = value
    return output


class F1c8ea826b10GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = canonical_row()
        cls.pairs = canonical_pairs()

    def test_all_public_pairs_match_rule_and_complete_profiles(self):
        self.assertEqual(len(self.pairs), 5)
        profiles = set()
        for pair in self.pairs:
            grid = pair["input"]
            before = list(grid)
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(independent_rule(grid), coerce(pair["output"]))
            self.assertEqual(generator.rule_mirror(grid), coerce(pair["output"]))
            self.assertEqual(grid, before)
            signature = generator.canonical_profile_signature(grid)
            self.assertIsNotNone(signature)
            profiles.add(signature)
        self.assertEqual(
            profiles,
            generator._CANONICAL_PROFILE_SIGNATURES,
        )

    def test_complete_profile_prior_is_stable_and_diverse(self):
        for start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                matches = 0
                profiles = set()
                pairs = set()
                for offset in range(600):
                    seed = start + offset
                    grid = generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                    output = independent_rule(grid)
                    pairs.add((
                        tuple(map(tuple, grid)),
                        tuple(map(tuple, output)),
                    ))
                    signature = generator.canonical_profile_signature(grid)
                    if signature is not None:
                        matches += 1
                        profiles.add(signature)
                self.assertGreaterEqual(matches, 100)
                self.assertLessEqual(matches, 210)
                self.assertEqual(
                    profiles,
                    generator._CANONICAL_PROFILE_SIGNATURES,
                )
                self.assertGreaterEqual(len(pairs), 595)

    def test_forced_lattice_boundaries_are_exact(self):
        for lattice_rows, lattice_cols in (
            (2, 2),
            (2, 4),
            (4, 2),
            (4, 4),
        ):
            for band in ("easy", "medium", "hard"):
                grid = generator.generate(
                    lattice_rows * 31,
                    lattice_cols * 37,
                    difficulty=band,
                    lattice_rows=lattice_rows,
                    lattice_cols=lattice_cols,
                )
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(
                    generator.observe_overrides(grid),
                    {
                        "lattice_rows": lattice_rows,
                        "lattice_cols": lattice_cols,
                    },
                )
                _coerced, features, errors = generator._scene_analysis(grid)
                self.assertEqual(errors, [])
                self.assertGreaterEqual(features["solid_chambers"], 1)
                self.assertGreaterEqual(features["checker_chambers"], 1)
                if band == "hard":
                    self.assertGreaterEqual(
                        features["middle_decoy_chambers"],
                        1,
                    )

    def test_rule_is_exact_for_solid_checker_and_middle_decoy(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(180):
                grid = generator.generate(
                    seed,
                    seed * 29 + 7,
                    difficulty=band,
                )
                before = [row[:] for row in grid]
                self.assertEqual(
                    generator.rule_mirror(grid),
                    independent_rule(grid),
                )
                self.assertEqual(grid, before)
                _coerced, features, errors = generator._scene_analysis(grid)
                self.assertEqual(errors, [])
                self.assertGreaterEqual(features["checker_chambers"], 1)
                if not generator.is_canonical_profile(grid):
                    self.assertGreaterEqual(features["solid_chambers"], 1)
                    if band == "hard":
                        self.assertGreaterEqual(
                            features["middle_decoy_chambers"],
                            1,
                        )

    def test_profile_local_rank_relabeling_and_lawful_nonprofile(self):
        for index, source in enumerate(generator._PROFILE_GRIDS):
            for shift in range(8):
                grid = generator._draw_profile(
                    source,
                    random.Random(index * 100 + shift),
                )
                self.assertEqual(generator.self_check(grid), [])
                self.assertTrue(generator.is_canonical_profile(grid))
                self.assertEqual(
                    generator.rule_mirror(grid),
                    independent_rule(grid),
                )

        hybrid = generator.generate(
            83,
            97,
            lattice_rows=4,
            lattice_cols=2,
        )
        self.assertEqual(generator.self_check(hybrid), [])
        self.assertFalse(generator.is_canonical_profile(hybrid))
        self.assertEqual(
            generator.rule_mirror(hybrid),
            independent_rule(hybrid),
        )

        transformed_input = [row[:] for row in hybrid]
        transformed_output = independent_rule(hybrid)
        _coerced, features, errors = generator._scene_analysis(hybrid)
        self.assertEqual(errors, [])
        for index, chamber in enumerate(features["chambers"]):
            replacement = tuple(sorted(
                random.Random(20_000 + index).sample(
                    generator._COLORS,
                    len(chamber["colors"]),
                )
            ))
            mapping = dict(zip(chamber["colors"], replacement))
            for local_row, local_col, value in chamber["markers"]:
                transformed_input[
                    chamber["top"] + local_row
                ][chamber["left"] + local_col] = mapping[value]
            for row, col in chamber["region_cells"]:
                transformed_output[row][col] = mapping[
                    transformed_output[row][col]
                ]
        self.assertEqual(
            generator.rule_mirror(transformed_input),
            transformed_output,
        )

    def test_removed_controls_and_strict_types(self):
        bad_calls = (
            {"difficulty": "expert"},
            {"bogus": 1},
            {"lattice_rows": "2"},
            {"lattice_cols": 2.0},
            {"lattice_rows": True},
            {"lattice_rows": 1},
            {"lattice_rows": 5},
            {"rows": 2},
            {"cols": 3},
            {"ch_h": 4},
            {"ch_w": 5},
            {"two_color_prob": 0.75},
            {"density": "chambers"},
            {"texture": "warm"},
            {"texture": "no_markers"},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **kwargs)

    def test_every_return_path_records_exact_provenance(self):
        profiled = 0
        for band in ("easy", "medium", "hard"):
            for seed in range(240):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = generator.generate(
                        seed,
                        seed * 37 + 5,
                        difficulty=band,
                    )
                finally:
                    base.set_ctx_observer(None)
                observed = generator.observe_overrides(grid)
                for key in generator.AXES:
                    self.assertEqual(captured[-1]._drawn[key], observed[key])
                profiled += generator.is_canonical_profile(grid)
        self.assertGreater(profiled, 125)

        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = generator.generate(
                91,
                117,
                difficulty="easy",
                lattice_rows=4,
                lattice_cols=2,
            )
        finally:
            base.set_ctx_observer(None)
        self.assertEqual(
            captured[-1]._drawn,
            generator.observe_overrides(grid),
        )
        self.assertEqual(
            captured[-1]._override_used,
            {"lattice_rows": 4, "lattice_cols": 2},
        )

    def test_self_check_rejects_structural_impostors(self):
        valid = generator.generate(
            1,
            2,
            difficulty="hard",
            lattice_rows=3,
            lattice_cols=3,
        )
        _coerced, features, errors = generator._scene_analysis(valid)
        self.assertEqual(errors, [])
        mutations = []

        broken_wall = [row[:] for row in valid]
        broken_wall[0][1] = 0
        mutations.append(broken_wall)

        extra_wall = [row[:] for row in valid]
        chamber = features["chambers"][0]
        chamber_cells = [
            (row, col)
            for row in range(
                chamber["top"],
                chamber["top"] + chamber["height"],
            )
            for col in range(
                chamber["left"],
                chamber["left"] + chamber["width"],
            )
        ]
        for row, col in chamber_cells[:3]:
            extra_wall[row][col] = 5
        mutations.append(extra_wall)

        empty_chamber = [row[:] for row in valid]
        chamber = features["chambers"][0]
        for row in range(chamber["top"], chamber["top"] + chamber["height"]):
            for col in range(
                chamber["left"],
                chamber["left"] + chamber["width"],
            ):
                empty_chamber[row][col] = 0
        mutations.append(empty_chamber)

        duplicate_marker = [row[:] for row in valid]
        chamber = features["chambers"][0]
        marker_value = chamber["markers"][0][2]
        empty = next(
            (row, col)
            for row in range(
                chamber["top"],
                chamber["top"] + chamber["height"],
            )
            for col in range(
                chamber["left"],
                chamber["left"] + chamber["width"],
            )
            if duplicate_marker[row][col] == 0
        )
        duplicate_marker[empty[0]][empty[1]] = marker_value
        mutations.append(duplicate_marker)

        four_colors = [row[:] for row in valid]
        chamber = next(
            item
            for item in features["chambers"]
            if item["height"] * item["width"] >= 5
        )
        cells = [
            (row, col)
            for row in range(
                chamber["top"],
                chamber["top"] + chamber["height"],
            )
            for col in range(
                chamber["left"],
                chamber["left"] + chamber["width"],
            )
        ]
        for row, col in cells:
            four_colors[row][col] = 0
        for (row, col), color in zip(cells[:4], (1, 2, 3, 4)):
            four_colors[row][col] = color
        mutations.append(four_colors)

        all_singletons = [row[:] for row in valid]
        for chamber in features["chambers"]:
            keep = chamber["markers"][0]
            for row in range(
                chamber["top"],
                chamber["top"] + chamber["height"],
            ):
                for col in range(
                    chamber["left"],
                    chamber["left"] + chamber["width"],
                ):
                    all_singletons[row][col] = 0
            all_singletons[
                chamber["top"] + keep[0]
            ][chamber["left"] + keep[1]] = keep[2]
        mutations.append(all_singletons)

        ragged = [row[:] for row in valid]
        ragged[-1] = ragged[-1][:-1]
        mutations.append(ragged)

        invalid_value = [row[:] for row in valid]
        invalid_value[1][1] = 10
        mutations.append(invalid_value)

        for mutation in mutations:
            self.assertTrue(generator.self_check(mutation), mutation)

    def test_bands_cover_profiles_branches_sizes_and_diversity(self):
        mean_areas = {}
        triple_grids = {}
        palette = set()
        for band in ("easy", "medium", "hard"):
            areas = []
            pairs = set()
            profiles = set()
            solid = checker = triple = 0
            max_height = max_width = 0
            for seed in range(600):
                grid = generator.generate(
                    seed,
                    seed * 43 + 11,
                    difficulty=band,
                )
                output = generator.rule_mirror(grid)
                pairs.add((
                    tuple(map(tuple, grid)),
                    tuple(map(tuple, output)),
                ))
                _coerced, features, errors = generator._scene_analysis(grid)
                self.assertEqual(errors, [])
                areas.append(len(grid) * len(grid[0]))
                max_height = max(max_height, len(grid))
                max_width = max(max_width, len(grid[0]))
                for chamber in features["chambers"]:
                    palette.update(chamber["colors"])
                solid += features["solid_chambers"] > 0
                checker += features["checker_chambers"] > 0
                triple += features["middle_decoy_chambers"] > 0
                signature = generator.canonical_profile_signature(grid)
                if signature is not None:
                    profiles.add(signature)

            mean_areas[band] = sum(areas) / len(areas)
            triple_grids[band] = triple
            self.assertGreaterEqual(len(pairs), 595)
            self.assertGreaterEqual(solid, 400)
            self.assertEqual(checker, 600)
            self.assertEqual(
                profiles,
                generator._CANONICAL_PROFILE_SIGNATURES,
            )
            if band == "hard":
                self.assertGreaterEqual(max_height, 25)
                self.assertGreaterEqual(max_width, 25)

        self.assertEqual(palette, set(generator._COLORS))
        self.assertEqual(triple_grids["easy"], 0)
        self.assertGreater(triple_grids["medium"], 0)
        self.assertGreater(triple_grids["hard"], triple_grids["medium"])
        self.assertLess(mean_areas["easy"], mean_areas["medium"])
        self.assertLess(mean_areas["medium"], mean_areas["hard"])

    def test_source_pin_determinism_freshness_and_global_rng(self):
        canonical = self.row["program_solution"]
        normalized = hashlib.sha256(
            " ".join(canonical.split()).encode()
        ).hexdigest()
        self.assertEqual(generator.RULE_HASH, normalized[:12])
        base_row = json.loads(
            (
                ROOT
                / "data/base/solutions/banks/dc02f6f7c147"
                / "H99__f1c8ea826b10.json"
            ).read_text()
        )
        self.assertEqual(
            base_row["racket_target"]["raw_code"], canonical
        )
        self.assertEqual(
            base_row["racket_target"]["target_code"], canonical
        )

        random.seed(9981)
        state = random.getstate()
        first = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))


if __name__ == "__main__":
    unittest.main()
