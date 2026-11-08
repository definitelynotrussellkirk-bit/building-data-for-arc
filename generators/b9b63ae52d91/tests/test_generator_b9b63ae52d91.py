"""Focused semantic regressions for generator b9b63ae52d91."""

from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import random
import unittest

from reviewer_support import canonical_path, find_root, load_selected_generator


ROOT = find_root(__file__)
TASK_ID = "b9b63ae52d91"


def _data_path(relative):
    for base in (ROOT / "data", ROOT / "shared/data"):
        path = base / relative
        if path.is_file():
            return path
    raise FileNotFoundError(relative)


BASE_PATHS = (
    _data_path("base/solutions/training/a8610ef7__b9b63ae52d91.json"),
    _data_path("base/solutions/augmented/a8610ef7__5165ad2767ee.json"),
)


def canonical_rows():
    return [
        json.loads(line)
        for line in canonical_path(ROOT).read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    ]


def normalized_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def independent_rule(grid):
    height = len(grid)
    return [
        [
            2 if value == 8 and grid[height - 1 - row][col] == 8 else
            5 if value == 8 else 0
            for col, value in enumerate(values)
        ]
        for row, values in enumerate(grid)
    ]


class GeneratorB9B63AE52D91Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module, _, _ = load_selected_generator(TASK_ID, root=ROOT)

    def test_all_canonical_pairs_and_public_profiles(self):
        rows = canonical_rows()
        self.assertEqual(
            [(row["source"], row["content_hash"]) for row in rows],
            [
                ("training", "b9b63ae52d91"),
                ("augmented", "5165ad2767ee"),
            ],
        )
        occurrences = [
            pair
            for row in rows
            for pair in row["train"] + row["test"]
        ]
        self.assertEqual(len(occurrences), 10)
        profiles = set()
        unique_inputs = set()
        for pair in occurrences:
            grid = copy.deepcopy(pair["input"])
            analysis = self.module._analyze(grid)
            self.assertEqual(analysis["errors"], [])
            self.assertEqual(analysis["facts"]["family"], "linked")
            profiles.add(analysis["facts"]["linked_profile"])
            unique_inputs.add(tuple(map(tuple, grid)))
            self.assertEqual(self.module.rule_mirror(grid), pair["output"])
            self.assertEqual(independent_rule(grid), pair["output"])
            self.assertEqual(grid, pair["input"])
        self.assertEqual(profiles, {f"public_{index}" for index in range(1, 6)})
        self.assertEqual(len(unique_inputs), 5)

    def test_rule_authorities_are_synchronized_and_pinned(self):
        rows = canonical_rows()
        canonical = rows[0]["program_solution"]
        self.assertTrue(all(row["program_solution"] == canonical for row in rows))
        self.assertEqual(normalized_hash(canonical), "46194ba2dd2d")
        self.assertEqual(self.module.RULE_HASH, normalized_hash(canonical))
        for path in BASE_PATHS:
            target = json.loads(path.read_text())["racket_target"]
            self.assertEqual(target["raw_code"], canonical)
            self.assertEqual(target["target_code"], canonical)

    def test_forced_families_are_exact_in_every_band(self):
        linked_profiles = set()
        generalized_profiles = set()
        for band in ("easy", "medium", "hard"):
            for family in ("linked", "generalized"):
                for sample_index in range(160):
                    grid = self.module.generate(
                        100_000 + sample_index,
                        sample_index * 17 + 3,
                        difficulty=band,
                        scene_family=family,
                    )
                    analysis = self.module._analyze(grid)
                    self.assertEqual(analysis["errors"], [])
                    facts = analysis["facts"]
                    self.assertEqual(facts["family"], family)
                    self.assertEqual(
                        self.module.observe_overrides(grid),
                        {"scene_family": family},
                    )
                    self.assertEqual(
                        self.module.rule_mirror(grid),
                        independent_rule(grid),
                    )
                    self.assertGreaterEqual(facts["non_axis_paired_count"], 2)
                    self.assertGreaterEqual(facts["solo_count"], 2)
                    self.assertEqual(
                        {value for row in facts["output"] for value in row},
                        {0, 2, 5},
                    )
                    if family == "linked":
                        linked_profiles.add(facts["linked_profile"])
                    else:
                        generalized_profiles.add(
                            facts["generalized_profile"]
                        )
        self.assertEqual(
            linked_profiles, {f"public_{index}" for index in range(1, 6)}
        )
        self.assertEqual(
            generalized_profiles, set(self.module._GENERAL_PROFILES)
        )

    def test_natural_prior_diversity_and_difficulty(self):
        shape_sets = {}
        for band_index, band in enumerate(("easy", "medium", "hard")):
            families = Counter()
            inputs = set()
            outputs = set()
            profiles = set()
            shapes = set()
            for sample_index in range(800):
                grid = self.module.generate(
                    200_000 + band_index,
                    sample_index,
                    difficulty=band,
                )
                facts = self.module._analyze(grid)["facts"]
                families[facts["family"]] += 1
                profiles.add(
                    facts["linked_profile"]
                    or facts["generalized_profile"]
                )
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, facts["output"])))
                shapes.add((len(grid), len(grid[0])))
            self.assertGreaterEqual(families["linked"], 180)
            self.assertGreaterEqual(families["generalized"], 480)
            self.assertGreaterEqual(len(inputs), 770)
            self.assertGreaterEqual(len(outputs), 770)
            self.assertGreaterEqual(len(profiles), 10)
            shape_sets[band] = shapes
        self.assertNotEqual(shape_sets["easy"], shape_sets["medium"])
        self.assertNotEqual(shape_sets["medium"], shape_sets["hard"])

    def test_causal_pair_solo_and_axis_mutations(self):
        grid = self.module.generate(
            333, 444, difficulty="hard", scene_family="generalized"
        )
        facts = self.module._analyze(grid)["facts"]
        row, col = next(
            cell
            for cell in facts["paired_cells"]
            if cell not in facts["axis_cells"]
        )
        mirror_row = len(grid) - 1 - row
        removed = copy.deepcopy(grid)
        removed[mirror_row][col] = 0
        self.assertEqual(independent_rule(removed)[row][col], 5)

        row, col = facts["solo_cells"][0]
        mirror_row = len(grid) - 1 - row
        added = copy.deepcopy(grid)
        added[mirror_row][col] = 8
        expected = independent_rule(added)
        self.assertEqual(expected[row][col], 2)
        self.assertEqual(expected[mirror_row][col], 2)

        odd = next(
            self.module.generate(
                555,
                index,
                difficulty="medium",
                scene_family="generalized",
            )
            for index in range(200)
            if self.module._analyze(
                self.module.generate(
                    555,
                    index,
                    difficulty="medium",
                    scene_family="generalized",
                )
            )["facts"]["axis_cells"]
        )
        odd_facts = self.module._analyze(odd)["facts"]
        odd_output = independent_rule(odd)
        self.assertTrue(odd_facts["axis_cells"])
        self.assertTrue(
            all(odd_output[row][col] == 2 for row, col in odd_facts["axis_cells"])
        )

    def test_legal_automorphisms_preserve_the_semantics(self):
        source = self.module._mask_grid(self.module._PUBLIC_MASKS[0])
        source_output = independent_rule(source)
        mapping = self.module._ROW_AUTOMORPHISMS[31]
        columns = (4, 0, 5, 2, 1, 3)
        transformed = [[0] * 6 for _ in range(6)]
        transformed_output = [[0] * 6 for _ in range(6)]
        for row in range(6):
            for col in range(6):
                transformed[mapping[row]][columns[col]] = source[row][col]
                transformed_output[mapping[row]][columns[col]] = (
                    source_output[row][col]
                )
        self.assertEqual(independent_rule(transformed), transformed_output)
        self.assertEqual(
            self.module._analyze(transformed)["facts"]["linked_profile"],
            "public_1",
        )

    def test_self_check_rejects_semantic_impostors(self):
        impostors = {
            "all_background": [[0] * 6 for _ in range(6)],
            "full_cyan": [[8] * 6 for _ in range(6)],
            "singleton": [[8 if (r, c) == (1, 1) else 0 for c in range(6)]
                          for r in range(6)],
            "solid_2x2": [[8 if r < 2 and c < 2 else 0 for c in range(6)]
                          for r in range(6)],
            "wrong_color": [[3 if (r, c) == (1, 1) else 0 for c in range(6)]
                            for r in range(6)],
            "ragged": [[0] * 6 for _ in range(5)] + [[0] * 5],
            "boolean": [[True if (r, c) == (1, 1) else 0 for c in range(6)]
                        for r in range(6)],
        }
        for name, grid in impostors.items():
            with self.subTest(name=name):
                self.assertTrue(self.module.self_check(grid))

    def test_determinism_fresh_returns_rng_purity_and_invalid_calls(self):
        random.seed(271_828)
        state = random.getstate()
        first = self.module.generate(
            777, 888, difficulty="hard", scene_family="generalized"
        )
        second = self.module.generate(
            777, 888, difficulty="hard", scene_family="generalized"
        )
        self.assertEqual(random.getstate(), state)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(
            all(left is not right for left, right in zip(first, second))
        )
        first[0][0] = 8 if first[0][0] == 0 else 0
        self.assertEqual(
            second,
            self.module.generate(
                777, 888, difficulty="hard", scene_family="generalized"
            ),
        )
        with self.assertRaisesRegex(ValueError, "unknown difficulty"):
            self.module.generate(0, 0, difficulty="extreme")
        with self.assertRaisesRegex(ValueError, "unknown override"):
            self.module.generate(0, 0, nonexistent_axis=True)
        with self.assertRaises((ValueError, KeyError)):
            self.module.generate(0, 0, scene_family="unknown")


if __name__ == "__main__":
    unittest.main()
