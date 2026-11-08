from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
import tempfile
import unittest

from reviewer_support import canonical_path, find_root, load_selected_generator
from shared.tools.data_quality_report import quality_error_reasons, scan
from solvers.grounded_rules import GROUNDED_RULES


ROOT = find_root(__file__)
generator, _GENERATOR_PATH, _GENERATOR_SHA256 = load_selected_generator(
    "ea8116b3e778", root=ROOT
)


def canonical_row():
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
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


class GeneratorEa8116b3e778Tests(unittest.TestCase):
    def test_compact_public_specs_reconstruct_every_pair(self):
        for profile, pair in zip(
            generator.PUBLIC_PROFILES,
            canonical_pairs(),
        ):
            self.assertEqual(generator._PUBLIC_INPUTS[profile], pair["input"])
            self.assertEqual(generator._PUBLIC_OUTPUTS[profile], pair["output"])

    def test_every_public_pair_is_strict_and_exact(self):
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

    def test_every_public_d4_variant_remains_exact(self):
        for profile, pair in zip(
            generator.PUBLIC_PROFILES,
            canonical_pairs(),
        ):
            for transform in generator.TRANSFORMS:
                grid = generator._transform(pair["input"], transform)
                expected = generator._transform(pair["output"], transform)
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(generator.solve_python(grid), expected)
                self.assertEqual(
                    generator._analyze(grid)["answer_profile"],
                    profile,
                )

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
                    self.assertEqual(
                        generator.solve_python(grid),
                        generator.solve_python(copy.deepcopy(grid)),
                    )

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

    def test_public_profiles_are_nonliteral_and_vary_nuisance(self):
        literals = {grid_key(pair["input"]) for pair in canonical_pairs()}
        for profile_index, profile in enumerate(generator.PUBLIC_PROFILES):
            inputs = set()
            outputs = set()
            shapes = set()
            for index in range(1_000):
                grid = generator.generate(
                    600_000 + 10_000 * profile_index + index,
                    index,
                    scene_profile=profile,
                )
                self.assertNotIn(grid_key(grid), literals)
                inputs.add(grid_key(grid))
                outputs.add(grid_key(generator.solve_python(grid)))
                shapes.add((len(grid), len(grid[0])))
            self.assertGreater(len(inputs), 30)
            # The 10x10 public output is itself D4-symmetric and nearly fills
            # its canvas, leaving exactly nine lawful translated outputs.
            self.assertGreater(len(outputs), 8)
            original = generator._PUBLIC_INPUTS[profile]
            self.assertEqual(
                shapes,
                {
                    (len(original), len(original[0])),
                    (len(original[0]), len(original)),
                },
            )

    def test_controls_cover_band_sizes_states_and_base_sizes(self):
        expected_ranges = {
            "easy": (4, 6),
            "medium": (6, 10),
            "hard": (8, 14),
        }
        for profile_index, profile in enumerate(
            generator.EXTRAPOLATION_PROFILES
        ):
            for band_index, band in enumerate(("easy", "medium", "hard")):
                base_sizes = set()
                shapes = set()
                for index in range(500):
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
                    self.assertTrue(analysis["strict"])
                    self.assertEqual(analysis["orbit_state"], profile)
                    base_sizes.add(analysis["base_size"])
                    shapes.add((len(grid), len(grid[0])))
                low, high = expected_ranges[band]
                self.assertEqual(base_sizes, set(range(low, high + 1)))
                legal = set(generator._CANVASES[band])
                legal |= {(width, height) for height, width in legal}
                self.assertLessEqual(shapes, legal)
                self.assertGreaterEqual(len(shapes), 5)

    def test_final_grid_mutations_are_rejected(self):
        base = generator.generate(
            800_000,
            0,
            difficulty="hard",
            scene_profile="single_quadrant",
        )
        mutations = []

        ragged = copy.deepcopy(base)
        ragged[0].pop()
        mutations.append(ragged)

        boolean = copy.deepcopy(base)
        boolean[0][0] = True
        mutations.append(boolean)

        missing_green = copy.deepcopy(base)
        for row in range(len(missing_green)):
            for col in range(len(missing_green[0])):
                if missing_green[row][col] == 3:
                    missing_green[row][col] = 0
                    break
            else:
                continue
            break
        mutations.append(missing_green)

        extra_green = copy.deepcopy(base)
        extra_green[0][0] = 3
        mutations.append(extra_green)

        wrong_palette = copy.deepcopy(base)
        wrong_palette[0][0] = 1
        mutations.append(wrong_palette)

        too_few_orbits = copy.deepcopy(base)
        red_cells = [
            (row, col)
            for row, values in enumerate(too_few_orbits)
            for col, value in enumerate(values)
            if value == 2
        ]
        for row, col in red_cells[3:]:
            too_few_orbits[row][col] = 0
        mutations.append(too_few_orbits)

        all_red = [[2 for _ in row] for row in base]
        mutations.append(all_red)

        no_background = copy.deepcopy(base)
        for row in range(len(no_background)):
            for col in range(len(no_background[0])):
                if no_background[row][col] == 0:
                    no_background[row][col] = 2
        mutations.append(no_background)

        for mutated in mutations:
            self.assertNotEqual(generator.self_check(mutated), [])

    def test_mixed_orbit_cross_recombination_is_rejected(self):
        grid = generator.generate(
            810_000,
            0,
            difficulty="hard",
            scene_profile="single_quadrant",
        )
        analysis = generator._analyze(grid)
        greens = [
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == 3
        ]
        sr = min(row for row, _ in greens) + max(row for row, _ in greens)
        sc = min(col for _, col in greens) + max(col for _, col in greens)
        red = next(
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == 2
        )
        candidates = generator._orbit(red[0], red[1], sr, sc)
        added = next(point for point in candidates if grid[point[0]][point[1]] == 0)
        hybrid = copy.deepcopy(grid)
        hybrid[added[0]][added[1]] = 2
        self.assertTrue(analysis["strict"])
        self.assertIn(
            "mixed_orbit_occupancy",
            generator.self_check(hybrid),
        )

    def test_broad_oracle_supports_off_grammar_pivots(self):
        grid = [[0 for _ in range(11)] for _ in range(9)]
        grid[4][5] = 3
        for row, col in ((1, 1), (1, 2), (2, 1), (3, 2)):
            grid[row][col] = 2
        original = copy.deepcopy(grid)
        actual = generator.solve_python(grid)
        self.assertEqual(grid, original)
        self.assertNotEqual(actual, grid)
        self.assertNotEqual(generator.self_check(grid), [])
        for row, col in ((7, 1), (7, 2), (6, 1), (5, 2)):
            self.assertEqual(actual[row][col], 2)

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
            grid_key(generator.generate(910_000 + index, 0, difficulty="hard"))
            for index in range(100)
        }
        index_variants = {
            grid_key(generator.generate(920_000, index, difficulty="hard"))
            for index in range(100)
        }
        self.assertGreater(len(seed_variants), 90)
        self.assertGreater(len(index_variants), 90)

    def test_invalid_overrides_raise(self):
        with self.assertRaises(ValueError):
            generator.generate(1, 0, scene_profile="not_a_profile")
        with self.assertRaises(ValueError):
            generator.generate(1, 0, unknown_axis=True)

    def test_version_and_rule_hash_are_current(self):
        self.assertEqual(generator.VERSION, "3.0.0")
        self.assertEqual(generator.RULE_HASH, "4e2d4d62614f")
        self.assertTrue(generator.ALLOW_IDENTITY_OUTPUT)
        source = canonical_row()["program_solution"]
        normalized = " ".join(source.split()).encode()
        self.assertTrue(
            hashlib.sha256(normalized).hexdigest().startswith(
                generator.RULE_HASH
            )
        )

    def test_data_quality_calibrates_only_the_canonical_identity_task(self):
        grid = generator._PUBLIC_INPUTS["public_train_3"]
        text = "\n".join("".join(str(value) for value in row) for row in grid)

        def row(task_id):
            return {
                "task_id": task_id,
                "messages": [
                    {"role": "user", "content": text},
                    {"role": "assistant", "content": text},
                ],
                "demo_count": 1,
                "query_count": 0,
                "source_stream": "per_puzzle",
                "generator_version": generator.VERSION,
                "source_seed": 1,
                "instance_seed": 1,
                "episode_index": 0,
            }

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.jsonl"
            path.write_text(json.dumps(row(generator.TASK_ID)) + "\n")
            result = scan(str(path), max_rows=0, task_filter=generator.TASK_ID)
            stats = result["stats"]["per_puzzle"]
            self.assertEqual(stats["A_noop"], 0)
            self.assertEqual(stats["A_canonical_noop"], 1)
            self.assertEqual(quality_error_reasons(result)[0], [])

            path.write_text(json.dumps(row("synthetic_noop_task")) + "\n")
            result = scan(
                str(path),
                max_rows=0,
                task_filter="synthetic_noop_task",
            )
            stats = result["stats"]["per_puzzle"]
            self.assertEqual(stats["A_noop"], 1)
            self.assertEqual(stats["A_canonical_noop"], 0)
            self.assertEqual(
                quality_error_reasons(result)[0],
                ["no-op output pairs=1"],
            )

    def test_rule_authorities_are_byte_identical(self):
        row = canonical_row()
        base = json.loads(
            (
                ROOT
                / "shared/data/base/solutions/training/"
                "4938f0c2__ea8116b3e778.json"
            ).read_text(encoding="utf-8")
        )
        source = row["program_solution"]
        self.assertEqual(GROUNDED_RULES[generator.TASK_ID], source)
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)


if __name__ == "__main__":
    unittest.main()
