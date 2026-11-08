from __future__ import annotations

import copy
import json
import random
import unittest

from puzzle_generators.per_puzzle.b6edfc119780 import generator as gen


class LongestClosedRowGeneratorTests(unittest.TestCase):
    def _canonical_pairs(self):
        pairs = []
        with open("data/canonical/puzzles.jsonl", encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                if row.get("task_id") != gen.TASK_ID:
                    continue
                pairs.extend(row["train"])
                test = row["test"]
                pairs.extend(test if isinstance(test, list) else [test])
        return pairs

    def test_rule_hash_and_all_canonical_pairs(self):
        self.assertEqual(gen.RULE_HASH, "ec0b18e51f58")
        pairs = self._canonical_pairs()
        self.assertEqual(len(pairs), 3)
        for pair in pairs:
            self.assertEqual(gen.self_check(pair["input"]), [])
            self.assertEqual(gen.rule_mirror(pair["input"]), pair["output"])

    def test_canonical_tie_chooses_topmost_longest_row(self):
        grid = [[0] * 10 for _ in range(7)]
        for column in (1, 6):
            grid[1][column] = 2
        for column in (3, 8):
            grid[4][column] = 4
        for column in (4, 6):
            grid[6][column] = 7
        self.assertEqual(gen.self_check(grid), [])
        output = gen.rule_mirror(grid)
        self.assertEqual([r for r, row in enumerate(output) if 8 in row], [1])
        self.assertEqual(output[1][1:7], [8] * 6)

    def test_declared_axes_are_exact_and_observable(self):
        cases = (
            {
                "height": 6,
                "width": 8,
                "num_active_rows": 5,
                "winner_rank": 4,
                "tie_mode": "unique",
                "color_mode": "all_distinct",
                "marker_mode": "winner_dense",
            },
            {
                "height": 14,
                "width": 16,
                "num_active_rows": 5,
                "winner_rank": 3,
                "tie_mode": "top_tie",
                "color_mode": "winner_shared",
                "marker_mode": "loser_dense",
            },
            {
                "height": 9,
                "width": 11,
                "num_active_rows": 3,
                "winner_rank": 0,
                "tie_mode": "top_tie",
                "color_mode": "monochrome",
                "marker_mode": "endpoints_only",
            },
        )
        for index, overrides in enumerate(cases):
            grid = gen.generate(4000 + index, 80 + index, difficulty="easy", **overrides)
            self.assertEqual(gen.self_check(grid), [])
            observed = gen.observe_overrides(grid)
            self.assertEqual(observed, overrides)

    def test_single_top_tie_override_is_total(self):
        for sample_index in range(24):
            grid = gen.generate(7300, sample_index, tie_mode="top_tie")
            self.assertEqual(gen.observe_overrides(grid)["tie_mode"], "top_tie")

    def test_incompatible_tie_pair_rejects_loudly(self):
        with self.assertRaisesRegex(ValueError, "requires a lower tied row|incompatible"):
            gen.generate(
                1,
                0,
                num_active_rows=5,
                winner_rank=4,
                tie_mode="top_tie",
            )

    def test_default_schedule_covers_every_active_row_rank(self):
        support = {
            (
                gen.observe_overrides(gen.generate(9100, sample_index))["num_active_rows"],
                gen.observe_overrides(gen.generate(9100, sample_index))["winner_rank"],
            )
            for sample_index in range(12)
        }
        expected = {
            (n_rows, rank)
            for n_rows in range(3, 6)
            for rank in range(n_rows)
        }
        self.assertEqual(support, expected)

    def test_default_three_demos_identify_query(self):
        seed = 82001
        demos = []
        for sample_index in range(3):
            grid = gen.generate(seed, sample_index)
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query_grid = gen.generate(seed, 3)
        query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        self.assertEqual(gen.lesson_identifiable(demos, query), [])

    def test_self_check_rejects_targeted_impostors(self):
        all_background = [[0] * 10 for _ in range(8)]
        one_row = [[0] * 10 for _ in range(8)]
        one_row[3][1] = one_row[3][8] = 2
        three_way_tie = [[0] * 10 for _ in range(8)]
        for row, color in ((1, 2), (3, 4), (5, 6)):
            three_way_tie[row][1] = color
            three_way_tie[row][7] = color
        mixed_row = gen.generate(123, 0)
        active = gen.semantic_observables(mixed_row)["active_grid_rows"][0]
        columns = [c for c, value in enumerate(mixed_row[active]) if value]
        original = mixed_row[active][columns[0]]
        replacement = next(color for color in range(1, 10) if color != original)
        mixed_row[active][columns[0]] = replacement
        solid_2x2 = [[0] * 10 for _ in range(8)]
        for row in (2, 3):
            for column in (4, 5):
                solid_2x2[row][column] = 2

        for impostor in (all_background, one_row, three_way_tie, mixed_row, solid_2x2):
            self.assertTrue(gen.self_check(impostor))

    def test_negative_recombination_uses_absent_replacement_color(self):
        grid = gen.generate(441, 0, color_mode="all_distinct")
        used = {value for row in grid for value in row if value}
        replacement = next(color for color in range(1, 10) if color not in used)
        obs = gen.semantic_observables(grid)
        row = obs["winner_grid_row"]
        column = obs["winner_start"]
        recombined = copy.deepcopy(grid)
        recombined[row][column] = replacement
        self.assertNotIn(replacement, used)
        self.assertTrue(
            any("mixes marker colors" in reason for reason in gen.self_check(recombined))
        )

    def test_determinism_fresh_returns_and_global_rng(self):
        random.seed(20260724)
        before = random.getstate()
        first = gen.generate(999, 17, difficulty="hard")
        middle = random.getstate()
        second = gen.generate(999, 17, difficulty="hard")
        after = random.getstate()
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        self.assertEqual(before, middle)
        self.assertEqual(before, after)
        first[0][0] = 9
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
