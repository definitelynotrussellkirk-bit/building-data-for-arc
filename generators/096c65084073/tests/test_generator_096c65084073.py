"""Focused semantic regressions for flood generator 096c65084073."""
from __future__ import annotations

from collections import deque
import copy
import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "096c65084073"
GENERATOR = importlib.import_module(
    "puzzle_generators.per_puzzle.096c65084073.generator"
)


def normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def canonical_row() -> dict:
    return next(
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )


def independent_transform(grid):
    """A deliberately independent reading-order flood implementation."""
    height, width = len(grid), len(grid[0])
    red = min(
        (row, col) for row in range(height) for col in range(width)
        if grid[row][col] == 2
    )
    reached = {red}
    queue = deque([red])
    while queue:
        row, col = queue.popleft()
        for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            nr, nc = row + dr, col + dc
            if not (0 <= nr < height and 0 <= nc < width):
                continue
            if (nr, nc) in reached or grid[nr][nc] not in (2, 5):
                continue
            reached.add((nr, nc))
            queue.append((nr, nc))
    output = copy.deepcopy(grid)
    for row, col in reached:
        if output[row][col] == 5:
            output[row][col] = 2
    return output


class FloodGeneratorTests(unittest.TestCase):
    def test_version_hash_and_axis_contract_are_current(self):
        self.assertEqual("4.0.0", GENERATOR.VERSION)
        self.assertEqual("7f320de70970", GENERATOR.RULE_HASH)
        self.assertEqual({"scene_family"}, set(GENERATOR.AXES))

    def test_authority_has_no_examples_and_generator_does_not_invent_them(self):
        row = canonical_row()
        self.assertEqual([], row["train"])
        self.assertEqual([], row["test"])
        self.assertIn("first (find-color grid 2)", row["program_solution"])
        self.assertIn("connected-region", row["program_solution"])

    def test_live_rule_sources_and_metadata_are_synchronized(self):
        row = canonical_row()
        base = json.loads(
            (ROOT / "data/base/solutions/custom/82ba1f96__096c65084073.json").read_text()
        )
        sources = {
            row["program_solution"],
            base["racket_target"]["raw_code"],
            base["racket_target"]["target_code"],
        }
        self.assertEqual(1, len(sources))
        source = sources.pop()
        self.assertEqual(GENERATOR.RULE_HASH, normalized_hash(source))
        self.assertEqual(
            ["first", "find-color", "connected-region", "fst", "snd", "filter",
             "cell-at", "second", "recolor-cells"],
            base["primitive_metadata"]["primitive_chain"],
        )

    def test_task_is_absent_from_divergence_inventories(self):
        for name in (
            "rule_source_divergence.json",
            "rule_source_divergence_semantic.json",
        ):
            rows = json.loads((ROOT / "data/derived" / name).read_text())
            self.assertNotIn(TASK_ID, {row["task_id"] for row in rows})

    def test_forced_families_are_exact_observable_and_semantic(self):
        for difficulty in ("default", "easy", "medium", "hard"):
            for family in ("authored", "generalized"):
                for seed in range(60):
                    grid = GENERATOR.generate(
                        seed, seed * 17, difficulty=difficulty, scene_family=family
                    )
                    self.assertEqual([], GENERATOR.self_check(grid))
                    self.assertEqual(
                        {"scene_family": family}, GENERATOR.observe_overrides(grid)
                    )
                    self.assertEqual(independent_transform(grid), GENERATOR.rule_mirror(grid))

    def test_generalized_family_exercises_first_red_reading_order(self):
        for seed in range(100):
            grid = GENERATOR.generate(seed, seed * 19, scene_family="generalized")
            facts = GENERATOR._analyze(grid)["facts"]
            first, second = facts["reds"]
            self.assertLess(first, second)
            self.assertIn(first, facts["reached"])
            self.assertNotIn(second, facts["reached"])
            output = GENERATOR.rule_mirror(grid)
            self.assertEqual(2, output[first[0]][first[1]])
            self.assertEqual(2, output[second[0]][second[1]])
            self.assertTrue(any(output[r][c] == 5 for r, c in facts["unreached_gray"]))

    def test_natural_prior_favors_singular_authored_description(self):
        for difficulty in ("easy", "medium", "hard"):
            counts = {"authored": 0, "generalized": 0}
            for seed in range(1000):
                grid = GENERATOR.generate(seed, seed * 23, difficulty=difficulty)
                counts[GENERATOR.canonical_profile_signature(grid)] += 1
            self.assertGreaterEqual(counts["authored"], 700)
            self.assertLessEqual(counts["authored"], 800)

    def test_difficulty_bands_scale_canvas_and_components(self):
        dimension_ranges = {
            "easy": (8, 13),
            "medium": (12, 20),
            "hard": (18, 30),
        }
        average_areas = {}
        average_floods = {}
        for difficulty, (lower, upper) in dimension_ranges.items():
            grids = [
                GENERATOR.generate(seed, seed * 29, difficulty=difficulty)
                for seed in range(300)
            ]
            self.assertTrue(all(lower <= len(grid) <= upper for grid in grids))
            self.assertTrue(all(lower <= len(grid[0]) <= upper for grid in grids))
            average_areas[difficulty] = sum(len(g) * len(g[0]) for g in grids) / len(grids)
            average_floods[difficulty] = sum(
                len(GENERATOR._analyze(g)["facts"]["reached_gray"]) for g in grids
            ) / len(grids)
        self.assertLess(average_areas["easy"], average_areas["medium"])
        self.assertLess(average_areas["medium"], average_areas["hard"])
        self.assertLess(average_floods["easy"], average_floods["medium"])
        self.assertLess(average_floods["medium"], average_floods["hard"])

    def test_generated_scenes_are_highly_diverse(self):
        for difficulty in ("easy", "medium", "hard"):
            grids = {
                tuple(map(tuple, GENERATOR.generate(seed, seed * 31, difficulty=difficulty)))
                for seed in range(500)
            }
            self.assertGreaterEqual(len(grids), 490)

    def test_seed_and_sample_index_are_both_sensitive(self):
        by_seed = {
            tuple(map(tuple, GENERATOR.generate(seed, 0))) for seed in range(100)
        }
        by_sample = {
            tuple(map(tuple, GENERATOR.generate(0, sample))) for sample in range(100)
        }
        self.assertGreaterEqual(len(by_seed), 95)
        self.assertGreaterEqual(len(by_sample), 95)

    def test_generation_is_deterministic_fresh_and_global_rng_pure(self):
        random.seed(73051)
        state = random.getstate()
        first = GENERATOR.generate(31, 47, difficulty="hard")
        snapshot = copy.deepcopy(first)
        second = GENERATOR.generate(31, 47, difficulty="hard")
        self.assertEqual(state, random.getstate())
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        first[0][0] = 9
        self.assertEqual(snapshot, GENERATOR.generate(31, 47, difficulty="hard"))

    def test_checker_mirror_and_observer_are_input_pure(self):
        grid = GENERATOR.generate(81, 12, difficulty="hard")
        snapshot = copy.deepcopy(grid)
        GENERATOR.self_check(grid)
        GENERATOR.rule_mirror(grid)
        GENERATOR.observe_overrides(grid)
        self.assertEqual(snapshot, grid)

    def test_unknown_difficulty_and_override_fail_loudly(self):
        with self.assertRaises(ValueError):
            GENERATOR.generate(0, 0, difficulty="extreme")
        with self.assertRaises(ValueError):
            GENERATOR.generate(0, 0, invented_axis=True)
        with self.assertRaises(ValueError):
            GENERATOR.generate(0, 0, scene_family="unsupported")

    def test_checker_rejects_structural_and_palette_mutations(self):
        grid = GENERATOR.generate(14, 27, scene_family="authored")
        self.assertTrue(GENERATOR.self_check([]))
        self.assertTrue(GENERATOR.self_check([[0, 2], [5]]))
        self.assertTrue(GENERATOR.self_check([[True] * 8 for _ in range(8)]))
        for old, new in ((8, 0), (5, 3), (2, 0)):
            mutation = copy.deepcopy(grid)
            for row, values in enumerate(mutation):
                for col, value in enumerate(values):
                    if value == old:
                        mutation[row][col] = new
            self.assertTrue(GENERATOR.self_check(mutation))

    def test_adding_a_later_seed_is_a_lawful_generalized_recombination(self):
        for seed in range(200):
            grid = GENERATOR.generate(seed, seed * 37, scene_family="authored")
            facts = GENERATOR._analyze(grid)["facts"]
            candidates = [pos for pos in facts["unreached_gray"] if pos > facts["first_seed"]]
            if len(candidates) < 2:
                continue
            mutation = copy.deepcopy(grid)
            row, col = candidates[-1]
            mutation[row][col] = 2
            if not GENERATOR.self_check(mutation):
                self.assertEqual(
                    {"scene_family": "generalized"}, GENERATOR.observe_overrides(mutation)
                )
                self.assertEqual(independent_transform(mutation), GENERATOR.rule_mirror(mutation))
                return
        self.fail("failed to construct a lawful later-seed recombination")


if __name__ == "__main__":
    unittest.main()
