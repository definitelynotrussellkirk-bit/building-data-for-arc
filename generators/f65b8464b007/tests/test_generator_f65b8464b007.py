from __future__ import annotations

import hashlib
import json
import random
import unittest
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.f65b8464b007 import generator
from reviewer_support import canonical_path, find_root


ROOT = find_root(__file__)


def canonical_row():
    with canonical_path(ROOT).open() as handle:
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


def independent_features(grid):
    grid = coerce(grid)
    height = len(grid)
    width = len(grid[0])
    n_bands = (height - 1) // 4
    n_sections = (width + 1) // 4
    colors = []
    patterns = []
    for band_index in range(n_bands):
        top = 1 + band_index * 4
        band = []
        for section_index in range(n_sections):
            left = section_index * 4
            cells = [
                grid[top + row][left + col]
                for row in range(3)
                for col in range(3)
            ]
            if band_index == 0:
                colors.append(next(value for value in cells if value))
            band.append("".join(
                "1" if value else "0" for value in cells
            ))
        patterns.append(tuple(band))
    return {
        "n_sections": n_sections,
        "n_bands": n_bands,
        "colors": tuple(colors),
        "patterns": tuple(patterns),
    }


def independent_rule(grid):
    grid = coerce(grid)
    features = independent_features(grid)
    n_sections = features["n_sections"]
    last_band = features["patterns"][-1]
    output = [[0] * len(grid[0]) for _ in range(3)]
    for section_index in range(n_sections):
        source = last_band[(section_index + 1) % n_sections]
        color = features["colors"][section_index]
        for index, occupied in enumerate(source):
            if occupied == "1":
                output[index // 3][section_index * 4 + index % 3] = color
    return output


def normalized_rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


class F65b8464b007GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = canonical_row()
        cls.pairs = canonical_pairs()

    def test_all_public_pairs_match_rule_profiles_and_sequence(self):
        self.assertEqual(len(self.pairs), 5)
        profiles = set()
        band_counts = set()
        section_counts = set()
        for pair in self.pairs:
            grid = pair["input"]
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(independent_rule(grid), pair["output"])
            self.assertEqual(generator.rule_mirror(grid), pair["output"])
            self.assertEqual(grid, before)
            profile = generator.canonical_profile_index(grid)
            self.assertIsNotNone(profile)
            profiles.add(profile)
            features = independent_features(grid)
            band_counts.add(features["n_bands"])
            section_counts.add(features["n_sections"])
            for band_index in range(1, features["n_bands"]):
                previous = features["patterns"][band_index - 1]
                expected = tuple(
                    previous[(index + 1) % features["n_sections"]]
                    for index in range(features["n_sections"])
                )
                self.assertEqual(
                    features["patterns"][band_index],
                    expected,
                )
        self.assertEqual(profiles, set(range(5)))
        self.assertEqual(band_counts, {1, 2, 3})
        self.assertEqual(section_counts, {3, 4})

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
                    profile = generator.canonical_profile_index(grid)
                    if profile is not None:
                        matches += 1
                        profiles.add(profile)
                self.assertGreaterEqual(matches, 50)
                self.assertLessEqual(matches, 100)
                self.assertEqual(profiles, set(range(5)))
                self.assertGreaterEqual(len(pairs), 590)

    def test_every_forced_axis_value_and_boundary_cross_is_exact(self):
        values = {
            "n_sections": (3, 4, 5),
            "n_bands": (1, 2, 3),
        }
        for label, domain in values.items():
            for value in domain:
                grid = generator.generate(
                    value,
                    value * 19 + 3,
                    **{label: value},
                )
                self.assertEqual(
                    generator.observe_overrides(grid)[label],
                    value,
                )

        for n_sections in (3, 5):
            for n_bands in (1, 3):
                grid = generator.generate(
                    n_sections * 31 + n_bands,
                    n_sections * 37 + n_bands,
                    difficulty="easy",
                    n_sections=n_sections,
                    n_bands=n_bands,
                )
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(
                    generator.observe_overrides(grid),
                    {
                        "n_sections": n_sections,
                        "n_bands": n_bands,
                    },
                )

    def test_default_lessons_continue_the_cyclic_sequence(self):
        section_counts = set()
        band_counts = set()
        cell_counts = set()
        for band in ("easy", "medium", "hard"):
            for seed in range(240):
                grid = generator.generate(
                    seed,
                    seed * 29 + 7,
                    difficulty=band,
                )
                before = [row[:] for row in grid]
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(
                    generator.rule_mirror(grid),
                    independent_rule(grid),
                )
                self.assertEqual(grid, before)
                features = independent_features(grid)
                section_counts.add(features["n_sections"])
                band_counts.add(features["n_bands"])
                self.assertEqual(
                    len(set(features["colors"])),
                    features["n_sections"],
                )
                self.assertEqual(
                    len(set(features["patterns"][0])),
                    features["n_sections"],
                )
                for patterns in features["patterns"]:
                    cell_counts.update(
                        mask.count("1") for mask in patterns
                    )
                for band_index in range(1, features["n_bands"]):
                    previous = features["patterns"][band_index - 1]
                    expected = tuple(
                        previous[
                            (index + 1) % features["n_sections"]
                        ]
                        for index in range(features["n_sections"])
                    )
                    self.assertEqual(
                        features["patterns"][band_index],
                        expected,
                    )
        self.assertEqual(section_counts, {3, 4, 5})
        self.assertEqual(band_counts, {1, 2, 3})
        self.assertEqual(cell_counts, {4, 5, 6, 7})

    def test_profile_metamorphisms_and_nonprofile_recombination(self):
        for index, patterns in enumerate(generator._PROFILE_PATTERNS):
            variants = generator._profile_variants(patterns)
            self.assertGreaterEqual(len(variants), 8)
            self.assertEqual(len(variants), len(set(variants)))
            for variant_index, variant in enumerate(variants):
                colors = tuple(
                    range(1, len(variant[0]) + 1)
                )
                grid = generator._build_grid(variant, colors)
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(
                    generator.canonical_profile_index(grid),
                    index,
                )
                self.assertEqual(
                    generator.rule_mirror(grid),
                    independent_rule(grid),
                )
                if variant_index == 0:
                    recolored = generator._build_grid(
                        variant,
                        tuple(reversed(colors)),
                    )
                    self.assertEqual(
                        generator.canonical_profile_index(recolored),
                        index,
                    )

        general = generator.generate(
            83,
            97,
            n_sections=5,
            n_bands=3,
        )
        self.assertEqual(generator.self_check(general), [])
        self.assertIsNone(generator.canonical_profile_index(general))

    def test_cross_band_relation_is_answer_bearing(self):
        grid = generator.generate(
            181,
            211,
            n_sections=4,
            n_bands=3,
        )
        features = independent_features(grid)
        self.assertEqual(features["n_bands"], 3)
        original_output = independent_rule(grid)

        top = 1 + 4
        first_left = 0
        second_left = 4
        mutated = [row[:] for row in grid]
        for row in range(3):
            for col in range(3):
                mutated[top + row][first_left + col], mutated[
                    top + row
                ][second_left + col] = (
                    mutated[top + row][second_left + col],
                    mutated[top + row][first_left + col],
                )
        self.assertTrue(generator.self_check(mutated))
        self.assertEqual(independent_rule(mutated), original_output)

        final_top = 1 + 8
        output_changed = [row[:] for row in grid]
        for row in range(3):
            for col in range(3):
                output_changed[final_top + row][first_left + col], (
                    output_changed[final_top + row][second_left + col]
                ) = (
                    output_changed[final_top + row][second_left + col],
                    output_changed[final_top + row][first_left + col],
                )
        self.assertTrue(generator.self_check(output_changed))
        self.assertNotEqual(
            independent_rule(output_changed),
            original_output,
        )

    def test_removed_controls_and_strict_types(self):
        bad_calls = (
            {"difficulty": "expert"},
            {"bogus": 1},
            {"n_sections": "3"},
            {"n_sections": 3.0},
            {"n_sections": True},
            {"n_sections": 2},
            {"n_sections": 6},
            {"n_bands": 0},
            {"n_bands": 4},
            {"palette_kind": "warm"},
            {"n_cells_min": 4},
            {"n_cells_max": 7},
            {"section_w": 3},
            {"n_distinct_colors": 4},
            {"texture": "full_grid"},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **kwargs)

    def test_every_return_path_records_exact_provenance(self):
        profiles = 0
        for band in ("easy", "medium", "hard"):
            for seed in range(200):
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
                for label in generator.AXES:
                    self.assertEqual(
                        captured[-1]._drawn[label],
                        observed[label],
                    )
                profiles += generator.is_canonical_profile(grid)
        self.assertGreaterEqual(profiles, 45)

        overrides = {"n_sections": 5, "n_bands": 3}
        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = generator.generate(91, 117, **overrides)
        finally:
            base.set_ctx_observer(None)
        self.assertEqual(captured[-1]._drawn, overrides)
        self.assertEqual(captured[-1]._override_used, overrides)
        self.assertEqual(generator.observe_overrides(grid), overrides)

    def test_self_check_rejects_structural_impostors(self):
        valid = generator.generate(
            1,
            2,
            n_sections=4,
            n_bands=3,
        )
        mutations = []

        broken_separator_row = [row[:] for row in valid]
        broken_separator_row[4][0] = 1
        mutations.append(broken_separator_row)

        broken_separator_col = [row[:] for row in valid]
        broken_separator_col[1][3] = 1
        mutations.append(broken_separator_col)

        duplicate_color = [row[:] for row in valid]
        features = independent_features(valid)
        old_color = features["colors"][1]
        new_color = features["colors"][0]
        duplicate_color = [
            [
                new_color if value == old_color else value
                for value in row
            ]
            for row in duplicate_color
        ]
        mutations.append(duplicate_color)

        wrong_band_color = [row[:] for row in valid]
        wrong_band_color[5][4] = (
            9 if wrong_band_color[5][4] != 9 else 8
        )
        mutations.append(wrong_band_color)

        too_sparse = [row[:] for row in valid]
        for row in range(1, 4):
            for col in range(3):
                too_sparse[row][col] = 0
        too_sparse[1][0] = features["colors"][0]
        mutations.append(too_sparse)

        foreign_color = [row[:] for row in valid]
        foreign_color[1][0] = 10
        mutations.append(foreign_color)

        mutations.append([row[:] for row in valid[:4]])
        mutations.append([row[:] for row in valid] + [[0] * len(valid[0])] * 4)
        ragged = [row[:] for row in valid]
        ragged[0].pop()
        mutations.append(ragged)

        for mutation in mutations:
            self.assertTrue(generator.self_check(mutation))
        self.assertTrue(generator.self_check([]))
        self.assertTrue(generator.self_check([[0] * 11 for _ in range(5)]))

    def test_source_sync_determinism_freshness_and_global_rng(self):
        source = self.row["program_solution"]
        base_row = json.loads((
            ROOT
            / "data/base/solutions/training"
            / "e78887d1__f65b8464b007.json"
        ).read_text())
        target = base_row["racket_target"]
        self.assertEqual(
            normalized_rule_hash(target["raw_code"]),
            normalized_rule_hash(source),
        )
        self.assertEqual(
            normalized_rule_hash(target["target_code"]),
            normalized_rule_hash(source),
        )
        self.assertEqual(
            generator.RULE_HASH,
            normalized_rule_hash(source)[:12],
        )

        kwargs = {
            "difficulty": "hard",
            "n_sections": 5,
            "n_bands": 3,
        }
        first = generator.generate(17, 23, **kwargs)
        second = generator.generate(17, 23, **kwargs)
        self.assertEqual(first, second)
        first[0][0] = 9
        third = generator.generate(17, 23, **kwargs)
        self.assertNotEqual(first, third)
        self.assertEqual(second, third)

        random.seed(777)
        expected = [random.random() for _ in range(6)]
        random.seed(777)
        generator.generate(31, 37, difficulty="medium")
        actual = [random.random() for _ in range(6)]
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
