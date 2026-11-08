from __future__ import annotations

import copy
import hashlib
from importlib import import_module
import json
from pathlib import Path
import random
import unittest

from solvers.grounded_rules import GROUNDED_RULES


ROOT = Path(__file__).resolve().parents[1]
generator = import_module(
    "puzzle_generators.per_puzzle.080523523c90.generator"
)


def canonical_row():
    for line in (
        ROOT / "data/canonical/puzzles.jsonl"
    ).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if (
            row.get("task_id") == generator.TASK_ID
            and row.get("source") == "training"
        ):
            return row
    raise RuntimeError("canonical row not found")


def canonical_pairs():
    row = canonical_row()
    return row["train"] + row["test"]


def grid_key(grid):
    return tuple(tuple(row) for row in grid)


class Generator080523523c90Tests(unittest.TestCase):
    def test_public_specs_reconstruct_every_input(self):
        for profile, pair in zip(
            generator.PUBLIC_PROFILES,
            canonical_pairs(),
        ):
            spec = generator._PUBLIC_SPECS[profile]
            actual = generator._build_scene(
                *spec["shape"],
                spec["sums"],
                spec["canonical_residue_colors"],
            )
            self.assertEqual(actual, pair["input"])

    def test_every_public_pair_is_strict_observable_and_exact(self):
        for profile, pair in zip(
            generator.PUBLIC_PROFILES,
            canonical_pairs(),
        ):
            grid = copy.deepcopy(pair["input"])
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(generator.solve_python(grid), pair["output"])
            self.assertEqual(
                generator.observe_overrides(grid),
                {"scene_profile": profile},
            )

    def test_reflected_public_line_profiles_remain_exact(self):
        for profile in generator.PUBLIC_PROFILES:
            spec = generator._PUBLIC_SPECS[profile]
            height, width = spec["shape"]
            max_sum = height + width - 2
            selected = tuple(
                sorted(max_sum - value for value in spec["sums"])
            )
            grid = generator._build_scene(
                height,
                width,
                selected,
                (5, 6, 7),
            )
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(
                generator.observe_overrides(grid),
                {"scene_profile": profile},
            )
            self.assertNotEqual(generator.solve_python(grid), grid)

    def test_every_profile_and_band_is_observable(self):
        for profile_index, profile in enumerate(generator.SCENE_PROFILES):
            for band_index, band in enumerate(("easy", "medium", "hard")):
                for index in range(30):
                    grid = generator.generate(
                        10_000 * profile_index
                        + 1_000 * band_index
                        + index,
                        index,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(
                        generator.observe_overrides(grid),
                        {"scene_profile": profile},
                    )
                    self.assertNotEqual(generator.solve_python(grid), grid)

    def test_default_prior_is_calibrated_and_complete(self):
        public = 0
        total = 0
        for band_index, band in enumerate(("easy", "medium", "hard")):
            seen = set()
            for index in range(2_000):
                grid = generator.generate(
                    500_000 + 10_000 * band_index + index,
                    index,
                    difficulty=band,
                )
                profile = generator.observe_overrides(grid)["scene_profile"]
                seen.add(profile)
                public += profile in generator.PUBLIC_PROFILES
                total += 1
            self.assertEqual(seen, set(generator.SCENE_PROFILES))
        self.assertGreater(public / total, 0.22)
        self.assertLess(public / total, 0.28)

    def test_public_profiles_are_nonliteral_and_palette_varied(self):
        literals = {grid_key(pair["input"]) for pair in canonical_pairs()}
        for profile_index, profile in enumerate(generator.PUBLIC_PROFILES):
            inputs = set()
            outputs = set()
            palettes = set()
            for index in range(1_000):
                grid = generator.generate(
                    600_000 + 10_000 * profile_index + index,
                    index,
                    scene_profile=profile,
                )
                self.assertNotIn(grid_key(grid), literals)
                inputs.add(grid_key(grid))
                outputs.add(grid_key(generator.solve_python(grid)))
                palettes.add(tuple(sorted({
                    value
                    for row in grid
                    for value in row
                    if value != 0
                })))
            self.assertGreater(len(inputs), 350)
            self.assertGreater(len(outputs), 350)
            self.assertGreater(len(palettes), 70)

    def test_extrapolations_cover_line_geometries_and_canvases(self):
        minimum_shapes = {"easy": 8, "medium": 12, "hard": 15}
        for profile_index, profile in enumerate(
            generator.EXTRAPOLATION_PROFILES
        ):
            for band_index, band in enumerate(("easy", "medium", "hard")):
                shapes = set()
                for index in range(400):
                    grid = generator.generate(
                        700_000
                        + 10_000 * profile_index
                        + 1_000 * band_index
                        + index,
                        index,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    analysis = generator._analyze(grid)
                    self.assertEqual(analysis["scene_profile"], profile)
                    shapes.add((len(grid), len(grid[0])))
                    gaps = tuple(
                        right - left
                        for left, right in zip(
                            analysis["selected_sums"],
                            analysis["selected_sums"][1:],
                        )
                    )
                    if profile == "contiguous_band":
                        self.assertEqual(gaps, (1, 1))
                    elif profile == "paired_gap":
                        self.assertIn(1, gaps)
                        self.assertNotEqual(gaps, (1, 1))
                    else:
                        self.assertGreaterEqual(min(gaps), 2)
                self.assertGreaterEqual(
                    len(shapes), minimum_shapes[band]
                )

    def test_repeated_line_profiles_are_observable_and_answer_equivalent(self):
        expected = {
            "one_residue_repeated": (4, [1, 1, 2]),
            "all_residues_repeated": (6, [2, 2, 2]),
        }
        for profile_index, (profile, (line_count, multiplicities)) in enumerate(
            expected.items()
        ):
            for band_index, band in enumerate(("easy", "medium", "hard")):
                for index in range(100):
                    grid = generator.generate(
                        750_000
                        + 10_000 * profile_index
                        + 1_000 * band_index
                        + index,
                        index,
                        difficulty=band,
                        scene_profile=profile,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    info = generator._analyze(grid)
                    self.assertEqual(info["scene_profile"], profile)
                    self.assertEqual(len(info["selected_sums"]), line_count)
                    self.assertEqual(
                        sorted(info["residue_line_counts"].values()),
                        multiplicities,
                    )
                    observables = generator.semantic_observables(grid)
                    self.assertEqual(observables["scene_profile"], profile)
                    self.assertEqual(
                        sorted(observables["residue_line_counts"]),
                        multiplicities,
                    )
                    self.assertEqual(
                        len(set(observables["residue_colors"])), 3
                    )
                    self.assertNotEqual(generator.solve_python(grid), grid)

    def test_final_grid_mutations_are_rejected(self):
        base = generator.generate(
            800_000,
            0,
            difficulty="hard",
            scene_profile="spread_lines",
        )
        analysis = generator._analyze(base)
        selected = analysis["selected_sums"]

        ragged = copy.deepcopy(base)
        ragged[0].pop()
        self.assertEqual(generator.self_check(ragged), ["ragged"])

        boolean = copy.deepcopy(base)
        boolean[0][0] = True
        self.assertEqual(
            generator.self_check(boolean), ["invalid_arc_value"]
        )

        incomplete = copy.deepcopy(base)
        target_sum = max(
            selected,
            key=lambda value: len(
                generator._line_cells(
                    len(base), len(base[0]), value
                )
            ),
        )
        row, col = generator._line_cells(
            len(base), len(base[0]), target_sum
        )[0]
        incomplete[row][col] = 0
        self.assertIn(
            "incomplete_line", generator.self_check(incomplete)
        )

        nonuniform = copy.deepcopy(base)
        row, col = generator._line_cells(
            len(base), len(base[0]), target_sum
        )[0]
        used = {value for values in base for value in values}
        nonuniform[row][col] = next(
            value for value in range(1, 10) if value not in used
        )
        self.assertIn(
            "nonuniform_line", generator.self_check(nonuniform)
        )

        extra_lines = copy.deepcopy(base)
        available_sums = [
            value
            for value in range(len(base) + len(base[0]) - 1)
            if value not in selected
        ]
        for diagonal_sum in available_sums[:2]:
            color = analysis["residue_colors"][diagonal_sum % 3]
            for row, col in generator._line_cells(
                len(base), len(base[0]), diagonal_sum
            ):
                extra_lines[row][col] = color
        self.assertIn("line_count", generator.self_check(extra_lines))

        aliased = copy.deepcopy(base)
        source_sum, target_sum = selected[:2]
        source_row, source_col = generator._line_cells(
            len(base), len(base[0]), source_sum
        )[0]
        source_color = base[source_row][source_col]
        for row, col in generator._line_cells(
            len(base), len(base[0]), target_sum
        ):
            aliased[row][col] = source_color
        self.assertIn("color_alias", generator.self_check(aliased))

        repeated = generator.generate(
            800_001,
            0,
            difficulty="hard",
            scene_profile="all_residues_repeated",
        )
        repeated_info = generator._analyze(repeated)
        same_residue = next(
            residue
            for residue, count in repeated_info[
                "residue_line_counts"
            ].items()
            if count == 2
        )
        sums = [
            value
            for value in repeated_info["selected_sums"]
            if value % 3 == same_residue
        ]
        conflict = copy.deepcopy(repeated)
        used = {value for row in repeated for value in row}
        replacement = next(
            value for value in range(1, 10) if value not in used
        )
        for row, col in generator._line_cells(
            len(conflict), len(conflict[0]), sums[1]
        ):
            conflict[row][col] = replacement
        self.assertIn(
            "residue_color_conflict", generator.self_check(conflict)
        )

    def test_broad_first_seed_oracle_is_input_pure(self):
        grid = [[0 for _ in range(7)] for _ in range(6)]
        grid[0][0] = 2
        grid[0][1] = 4
        grid[0][2] = 7
        grid[3][0] = 9
        original = copy.deepcopy(grid)
        output = generator.solve_python(grid)
        self.assertEqual(grid, original)
        self.assertNotEqual(generator.self_check(grid), [])
        for row, values in enumerate(output):
            for col, value in enumerate(values):
                self.assertEqual(value, (2, 4, 7)[(row + col) % 3])

    def test_determinism_fresh_returns_and_global_rng(self):
        state = random.getstate()
        first = generator.generate(900_000, 17, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(900_000, 17, difficulty="hard")
        self.assertEqual(first, second)
        first[0][0] = 9
        third = generator.generate(900_000, 17, difficulty="hard")
        self.assertEqual(third, second)
        self.assertEqual(random.getstate(), state)

    def test_seed_and_sample_index_change_outputs(self):
        seed_variants = {
            grid_key(generator.generate(910_000 + index, 0))
            for index in range(100)
        }
        index_variants = {
            grid_key(generator.generate(920_000, index))
            for index in range(100)
        }
        self.assertGreater(len(seed_variants), 95)
        self.assertGreater(len(index_variants), 95)

    def test_invalid_overrides_raise(self):
        with self.assertRaises(ValueError):
            generator.generate(1, 0, scene_profile="not_a_profile")
        with self.assertRaises(ValueError):
            generator.generate(1, 0, unknown_axis=True)

    def test_version_rule_hash_and_authorities_are_current(self):
        self.assertEqual(generator.VERSION, "3.1.0")
        self.assertEqual(generator.RULE_HASH, "5f07af88af10")
        source = canonical_row()["program_solution"]
        normalized = " ".join(source.split()).encode()
        self.assertTrue(
            hashlib.sha256(normalized).hexdigest().startswith(
                generator.RULE_HASH
            )
        )
        base = json.loads((
            ROOT
            / "data/base/solutions/training/"
            "05269061__080523523c90.json"
        ).read_text(encoding="utf-8"))
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)
        self.assertEqual(GROUNDED_RULES[generator.TASK_ID], source)


if __name__ == "__main__":
    unittest.main()
