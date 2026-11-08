"""Focused semantic regressions for generator 548c1010ce89."""
from __future__ import annotations
from collections import Counter
import copy, hashlib, importlib, json, random, unittest
from pathlib import Path

from reviewer_support import canonical_path, find_root

TASK_ID = "548c1010ce89"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = find_root(__file__)


def _rows():
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()
            if json.loads(line).get("task_id") == TASK_ID]
    if len(rows) != 2: raise AssertionError(len(rows))
    return rows


def _hash(source): return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


class Generator548c1010ce89Tests(unittest.TestCase):
    def test_all_canonical_occurrences_and_unique_inputs(self):
        occurrences, unique = 0, set()
        for row in _rows():
            for split in ("train", "test"):
                for pair in row.get(split, []):
                    occurrences += 1; unique.add(tuple(map(tuple, pair["input"])))
                    self.assertEqual(MODULE.rule_mirror(pair["input"]), pair["output"])
                    self.assertIn(MODULE.canonical_profile_signature(pair["input"]), MODULE.PUBLIC_PROFILES)
        self.assertEqual((occurrences, len(unique)), (8, 4))

    def test_public_profiles_are_exact(self):
        expected = []
        for row in _rows():
            for split in ("train", "test"):
                for pair in row.get(split, []):
                    if pair["input"] not in expected: expected.append(pair["input"])
        self.assertEqual([MODULE.generate(1, 2, scene_profile=p) for p in MODULE.PUBLIC_PROFILES], expected)

    def test_every_profile_and_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.SCENE_PROFILES:
                for seed in range(20):
                    grid = MODULE.generate(seed, seed * 19 + 3, difficulty=band, scene_profile=profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MODULE.self_check(grid), [])
                    self.assertNotEqual(MODULE.rule_mirror(grid), grid)

    def test_rows_and_columns_are_detected_from_input_only(self):
        for profile in MODULE.SCENE_PROFILES:
            grid = MODULE.generate(101, 203, scene_profile=profile)
            info = MODULE._analysis(grid); output = MODULE.rule_mirror(grid)
            for row in range(len(grid)):
                for col in range(len(grid[0])):
                    expected = 2 if row in info["empty_rows"] or col in info["empty_cols"] else grid[row][col]
                    self.assertEqual(output[row][col], expected)

    def test_independent_row_and_column_branches(self):
        cols = MODULE._analysis(MODULE.generate(211, 307, scene_profile="columns_only"))
        rows = MODULE._analysis(MODULE.generate(223, 311, scene_profile="rows_only"))
        self.assertFalse(cols["empty_rows"]); self.assertTrue(cols["empty_cols"])
        self.assertTrue(rows["empty_rows"]); self.assertFalse(rows["empty_cols"])
        self.assertEqual(MODULE._analysis(MODULE.generate(1, 2, scene_profile="public_train_1"))["empty_rows"], ())

    def test_line_count_and_placement_lessons(self):
        names = ("single_empty_row", "single_empty_col", "multiple_empty_rows", "multiple_empty_cols",
                 "boundary_empty_lines", "adjacent_empty_lines")
        infos = {name: MODULE._analysis(MODULE.generate(229, 317, scene_profile=name)) for name in names}
        self.assertEqual(len(infos["single_empty_row"]["empty_rows"]), 1)
        self.assertEqual(len(infos["single_empty_col"]["empty_cols"]), 1)
        self.assertGreaterEqual(len(infos["multiple_empty_rows"]["empty_rows"]), 4)
        self.assertGreaterEqual(len(infos["multiple_empty_cols"]["empty_cols"]), 4)
        boundary = infos["boundary_empty_lines"]
        self.assertTrue(0 in boundary["empty_rows"] or 0 in boundary["empty_cols"])
        adjacent = infos["adjacent_empty_lines"]
        self.assertTrue(any(b == a + 1 for seq in (adjacent["empty_rows"], adjacent["empty_cols"]) for a, b in zip(seq, seq[1:])))

    def test_density_multicolor_and_existing_red(self):
        sparse = MODULE._analysis(MODULE.generate(233, 319, scene_profile="rows_and_cols_sparse"))
        dense = MODULE._analysis(MODULE.generate(239, 323, scene_profile="rows_and_cols_dense"))
        multi = MODULE._analysis(MODULE.generate(241, 327, scene_profile="multicolor_foreground"))
        red_grid = MODULE.generate(251, 331, scene_profile="red_foreground_preserved")
        red = MODULE._analysis(red_grid); output = MODULE.rule_mirror(red_grid)
        self.assertLess(sparse["active_density"], .68); self.assertGreaterEqual(dense["active_density"], .68)
        self.assertGreater(len(multi["foreground_colors"]), 1); self.assertIn(2, red["foreground_colors"])
        for row in range(len(red_grid)):
            for col in range(len(red_grid[0])):
                if red_grid[row][col] == 2 and row not in red["empty_rows"] and col not in red["empty_cols"]:
                    self.assertEqual(output[row][col], 2)

    def test_default_census_and_diversity(self):
        for band in ("easy", "medium", "hard"):
            profiles, pairs = Counter(), set()
            for seed in range(800):
                grid = MODULE.generate(seed, seed * 11 + 1, difficulty=band)
                profiles[MODULE.observe_overrides(grid)["scene_profile"]] += 1
                pairs.add((tuple(map(tuple, grid)), tuple(map(tuple, MODULE.rule_mirror(grid)))))
            self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
            public = sum(profiles[p] for p in MODULE.PUBLIC_PROFILES)
            self.assertTrue(150 < public < 260); self.assertGreater(len(pairs), 590)

    def test_self_check_rejects_minimal_and_malformed_impostors(self):
        base = MODULE.generate(401, 503, scene_profile="rows_and_cols_sparse")
        h, w = len(base), len(base[0]); empty = [[0] * w for _ in range(h)]
        singleton = copy.deepcopy(empty); singleton[1][1] = 3
        line = copy.deepcopy(empty); line[1][1:5] = [3] * 4
        block = copy.deepcopy(empty); block[1][1] = block[1][2] = block[2][1] = block[2][2] = 3
        no_empty = [[3] * w for _ in range(h)]
        ragged = copy.deepcopy(base); ragged[0].pop()
        invalid = copy.deepcopy(base); invalid[0][0] = 10
        boolean = copy.deepcopy(base); boolean[0][0] = True
        for mutation in (empty, singleton, line, block, no_empty, ragged, invalid, boolean):
            self.assertTrue(MODULE.self_check(mutation), mutation)
        self.assertTrue(MODULE.self_check(base, meta={"overrides": {"scene_profile": "columns_only"}}))

    def test_determinism_freshness_rng_and_unknown_axes(self):
        for overrides in ({"scene_profile":"unknown"},{"grid_h":12},{"fg_layout":"noise"},{"texture":"all_bg"}):
            with self.assertRaises(ValueError): MODULE.generate(1, 2, **overrides)
        random.seed(20260721); state = random.getstate()
        first = MODULE.generate(97, 103, difficulty="hard"); self.assertEqual(random.getstate(), state)
        second = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(first, second); self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))

    def test_default_schedule_refutes_axis_shortcuts_in_every_rotation(self):
        self.assertEqual(MODULE.EXAMPLES_NEEDED, 3)
        self.assertEqual(MODULE.LESSON_SCHEDULE_PERIOD, 4)
        self.assertEqual(len(MODULE.SCHEDULE_PROFILES), 4)
        for band in ("easy", "medium", "hard"):
            for seed in (0, 17, 727):
                for start in range(MODULE.LESSON_SCHEDULE_PERIOD):
                    pairs = []
                    for offset in range(4):
                        grid = MODULE.generate(seed, start + offset, difficulty=band)
                        pairs.append({"input": grid, "output": MODULE.rule_mirror(grid)})
                    for query_index, query in enumerate(pairs):
                        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                        self.assertEqual(MODULE.lesson_identifiable(demos, query), [])
                        self.assertTrue(any(MODULE._has_both_axes(pair["input"]) for pair in demos))
                        for rival in MODULE.LESSON_COMPETITORS.values():
                            self.assertFalse(all(rival(pair["input"]) == pair["output"] for pair in demos))

    def test_seed_727_reported_schedule_is_repaired(self):
        pairs = []
        for index in range(4):
            grid = MODULE.generate(727, index, difficulty="medium")
            pairs.append({"input": grid, "output": MODULE.rule_mirror(grid)})
        demos, query = pairs[:3], pairs[3]
        self.assertEqual(MODULE.lesson_identifiable(demos, query), [])
        self.assertFalse(all(
            MODULE.LESSON_COMPETITORS["columns_only"](pair["input"]) == pair["output"]
            for pair in demos
        ))

    def test_rule_sources_and_pin(self):
        canonical = _rows()[0]["program_solution"]; self.assertEqual(_rows()[1]["program_solution"], canonical)
        for path in (ROOT / "data/base/solutions/training/c1d99e64__548c1010ce89.json",
                     ROOT / "data/base/solutions/augmented/c1d99e64__b3a459ad6da0.json"):
            base = json.loads(path.read_text())
            self.assertEqual(" ".join(base["racket_target"]["raw_code"].split()), " ".join(canonical.split()))
            self.assertEqual(" ".join(base["racket_target"]["target_code"].split()), " ".join(canonical.split()))
        self.assertEqual(MODULE.RULE_HASH, _hash(canonical)); self.assertEqual(MODULE.RULE_HASH, "506bc3722b18")


if __name__ == "__main__": unittest.main()
