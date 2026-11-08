"""Focused semantic regressions for generator 2534c7164e36."""

from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
import random
import unittest



from reviewer_support import canonical_path, find_root, load_selected_generator


ROOT = find_root(__file__)
DATA_ROOT = canonical_path(ROOT).parents[1]
TASK_ID = "2534c7164e36"
BASE_PATHS = (
    DATA_ROOT / "base/solutions/training/cf98881b__2534c7164e36.json",
    DATA_ROOT / "base/solutions/augmented/cf98881b__032517865590.json",
)


def canonical_rows():
    return [
        json.loads(line)
        for line in canonical_path(ROOT).read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    ]


def unique_pairs():
    pairs = []
    seen = set()
    for row in canonical_rows():
        for pair in row["train"] + row["test"]:
            frozen = tuple(tuple(values) for values in pair["input"])
            if frozen not in seen:
                seen.add(frozen)
                pairs.append(pair)
    return pairs


def normalized_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def independent_rule(grid):
    return [
        [
            next(
                (
                    grid[row][col + offset]
                    for offset in (0, 5, 10)
                    if grid[row][col + offset] != 0
                ),
                0,
            )
            for col in range(4)
        ]
        for row in range(4)
    ]


class Generator2534c7164e36Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module, _, _ = load_selected_generator(TASK_ID, root=ROOT)

    def test_all_six_unique_canonical_pairs(self):
        rows = canonical_rows()
        self.assertEqual([(row["source"], len(row["train"]), len(row["test"])) for row in rows],
                         [("training", 5, 1), ("augmented", 6, 0)])
        pairs = unique_pairs()
        self.assertEqual(len(pairs), 6)
        for pair in pairs:
            grid = copy.deepcopy(pair["input"])
            self.assertEqual(self.module.self_check(grid), [])
            self.assertEqual(self.module.canonical_profile_signature(grid), "linked")
            self.assertEqual(self.module.rule_mirror(grid), pair["output"])
            self.assertEqual(independent_rule(grid), pair["output"])

    def test_rule_authorities_are_identical_and_pinned(self):
        rows = canonical_rows()
        canonical = rows[0]["program_solution"]
        self.assertTrue(all(row["program_solution"] == canonical for row in rows))
        expected = normalized_hash(canonical)
        self.assertEqual(expected[:12], "3d9402d2c7a5")
        self.assertEqual(self.module.RULE_HASH, expected[:12])
        for path in BASE_PATHS:
            target = json.loads(path.read_text())["racket_target"]
            self.assertEqual(target["raw_code"], canonical)
            self.assertEqual(target["target_code"], canonical)

    def test_forced_families_are_exact_and_semantic(self):
        for band in ("easy", "medium", "hard"):
            for family in ("linked", "generalized"):
                for sample_index in range(100):
                    grid = self.module.generate(
                        10_000 + sample_index,
                        sample_index * 31 + 7,
                        difficulty=band,
                        scene_family=family,
                    )
                    before = copy.deepcopy(grid)
                    self.assertEqual(self.module.self_check(grid), [])
                    self.assertEqual(
                        self.module.observe_overrides(grid),
                        {"scene_family": family},
                    )
                    self.assertEqual(self.module.rule_mirror(grid), independent_rule(grid))
                    self.assertEqual(grid, before)
                    if family == "generalized":
                        facts = self.module._analyze(grid)["facts"]
                        self.assertEqual(len(facts["state_counts"]), 8)
                        self.assertEqual(
                            set(facts["output_values"]),
                            {0, *facts["panel_colors"]},
                        )

    def test_natural_linked_prior_diversity_and_band_effect(self):
        generalized_state_histograms = {}
        for band_index, band in enumerate(("easy", "medium", "hard")):
            families = Counter()
            inputs = set()
            outputs = set()
            state_histogram = Counter()
            for sample_index in range(1_200):
                grid = self.module.generate(
                    20_000 + band_index,
                    sample_index,
                    difficulty=band,
                )
                facts = self.module._analyze(grid)["facts"]
                families[facts["family"]] += 1
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, facts["output"])))
                if facts["family"] == "generalized":
                    state_histogram.update(facts["state_counts"])
            self.assertGreaterEqual(families["linked"], 280)
            self.assertLessEqual(families["linked"], 440)
            self.assertGreaterEqual(len(inputs), 1_050)
            self.assertGreaterEqual(len(outputs), 1_000)
            generalized_state_histograms[band] = state_histogram
        self.assertNotEqual(generalized_state_histograms["easy"],
                            generalized_state_histograms["medium"])
        self.assertNotEqual(generalized_state_histograms["medium"],
                            generalized_state_histograms["hard"])

    def test_complete_truth_table_and_priority_witnesses(self):
        for band in ("easy", "medium", "hard"):
            grid = self.module.generate(
                31,
                47,
                difficulty=band,
                scene_family="generalized",
            )
            facts = self.module._analyze(grid)["facts"]
            self.assertEqual(set(facts["states"]), {
                (False, False, False),
                (False, False, True),
                (False, True, False),
                (False, True, True),
                (True, False, False),
                (True, False, True),
                (True, True, False),
                (True, True, True),
            })
            q1, q2, q3 = facts["panel_colors"]
            for index, state in enumerate(facts["states"]):
                row, col = divmod(index, 4)
                expected = q1 if state[0] else q2 if state[1] else q3 if state[2] else 0
                self.assertEqual(facts["output"][row][col], expected)

    def test_linked_masks_are_not_independently_recombined(self):
        masks = (
            self.module._PUBLIC_MASK_TRIPLES[0][0],
            self.module._PUBLIC_MASK_TRIPLES[1][1],
            self.module._PUBLIC_MASK_TRIPLES[2][2],
        )
        grid = self.module._paint_scene(masks, 2, (4, 9, 1))
        self.assertEqual(self.module.canonical_profile_signature(grid), "generalized")
        self.assertNotIn(masks, self.module._LINKED_MASK_TRIPLES)

    def test_self_check_rejects_structural_impostors(self):
        linked = self.module.generate(71, 73, scene_family="linked")
        generalized = self.module.generate(79, 83, scene_family="generalized")

        zero_divider = copy.deepcopy(linked)
        for row in range(4):
            zero_divider[row][4] = zero_divider[row][9] = 0
        unequal_dividers = copy.deepcopy(linked)
        replacement = next(
            color for color in range(1, 10)
            if color not in {value for row in linked for value in row}
        )
        for row in range(4):
            unequal_dividers[row][9] = replacement
        empty_panel = copy.deepcopy(linked)
        for row in range(4):
            for col in range(4):
                empty_panel[row][col] = 0
        duplicate_role_color = copy.deepcopy(linked)
        facts = self.module._analyze(linked)["facts"]
        q1_color, q2_color, _ = facts["panel_colors"]
        for row in range(4):
            for col in range(5, 9):
                if duplicate_role_color[row][col] == q2_color:
                    duplicate_role_color[row][col] = q1_color
        missing_truth_state = copy.deepcopy(generalized)
        generalized_facts = self.module._analyze(generalized)["facts"]
        unique_state = next(
            state for state, count in generalized_facts["state_counts"].items()
            if count == 1
        )
        index = generalized_facts["states"].index(unique_state)
        row, col = divmod(index, 4)
        for offset in (0, 5, 10):
            missing_truth_state[row][col + offset] = 0
        ragged = copy.deepcopy(linked)
        ragged[0].pop()
        boolean_cell = copy.deepcopy(linked)
        boolean_cell[0][0] = True
        out_of_range = copy.deepcopy(linked)
        out_of_range[0][0] = 10

        for name, mutation in (
            ("zero_divider", zero_divider),
            ("unequal_dividers", unequal_dividers),
            ("empty_panel", empty_panel),
            ("duplicate_role_color", duplicate_role_color),
            ("missing_truth_state", missing_truth_state),
            ("ragged", ragged),
            ("boolean_cell", boolean_cell),
            ("out_of_range", out_of_range),
        ):
            with self.subTest(name=name):
                self.assertTrue(self.module.self_check(mutation))

    def test_determinism_fresh_returns_rng_purity_and_invalid_calls(self):
        random.seed(271_828)
        state = random.getstate()
        first = self.module.generate(
            89,
            97,
            difficulty="hard",
            scene_family="generalized",
        )
        self.assertEqual(random.getstate(), state)
        second = self.module.generate(
            89,
            97,
            difficulty="hard",
            scene_family="generalized",
        )
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))
        first[0][0] = 9
        self.assertEqual(
            second,
            self.module.generate(
                89,
                97,
                difficulty="hard",
                scene_family="generalized",
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
