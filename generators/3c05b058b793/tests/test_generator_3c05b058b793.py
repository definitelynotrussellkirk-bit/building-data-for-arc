"""Focused semantic regression tests for generator 3c05b058b793."""
from __future__ import annotations

import copy
import importlib
import json
import random
import unittest
from collections import Counter, deque
from pathlib import Path

from scripts.coder_synth_verify import ProgramVerifier


generator = importlib.import_module(
    "puzzle_generators.per_puzzle.3c05b058b793.generator"
)
ROOT = Path(__file__).resolve().parents[1]
BASE_FILE = (
    ROOT
    / "data"
    / "base"
    / "solutions"
    / "banks"
    / "f4facb1306bd"
    / "H118__3c05b058b793.json"
)
CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def canonical_row() -> dict:
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == generator.TASK_ID:
                return row
    raise AssertionError("canonical task missing")


def canonical_pairs() -> list[dict]:
    row = canonical_row()
    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *tests]


def bfs(grid: list[list[int]], start: tuple[int, int]) -> dict[tuple[int, int], int]:
    height, width = len(grid), len(grid[0])
    distances = {start: 0}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in CARDINAL:
            nr, nc = r + dr, c + dc
            point = (nr, nc)
            if not (0 <= nr < height and 0 <= nc < width):
                continue
            if grid[nr][nc] == 5 or point in distances:
                continue
            distances[point] = distances[(r, c)] + 1
            queue.append(point)
    return distances


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    seed_a = next((r, c) for r in range(height) for c in range(width) if grid[r][c] == 2)
    seed_b = next((r, c) for r in range(height) for c in range(width) if grid[r][c] == 3)
    da, db = bfs(grid, seed_a), bfs(grid, seed_b)
    output = copy.deepcopy(grid)
    for r in range(height):
        for c in range(width):
            point = (r, c)
            if grid[r][c] != 0 or point not in da or point not in db:
                continue
            if da[point] < db[point]:
                output[r][c] = 8
            elif db[point] < da[point]:
                output[r][c] = 4
    return output


def semantic_counts(grid: list[list[int]]) -> dict[str, int]:
    output = rule_mirror(grid)
    return {
        "walls": sum(value == 5 for row in grid for value in row),
        "cyan": sum(value == 8 for row in output for value in row),
        "yellow": sum(value == 4 for row in output for value in row),
        "ties": sum(
            grid[r][c] == 0 and output[r][c] == 0
            for r in range(len(grid))
            for c in range(len(grid[0]))
        ),
    }


class Generator3c05b058b793Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.row = canonical_row()
        cls.pairs = canonical_pairs()

    def test_rule_authorities_are_exactly_synchronized_and_hash_is_pinned(self):
        base = json.loads(BASE_FILE.read_text(encoding="utf-8"))
        canonical = self.row["program_solution"]
        self.assertEqual(base["racket_target"]["raw_code"], canonical)
        self.assertEqual(base["racket_target"]["target_code"], canonical)
        self.assertEqual(generator.RULE_HASH, "58404f8e7c2f")

    def test_all_canonical_inputs_are_accepted_and_outputs_match(self):
        self.assertEqual(len(self.pairs), 5)
        for pair in self.pairs:
            source = copy.deepcopy(pair["input"])
            snapshot = copy.deepcopy(source)
            self.assertEqual(
                generator.self_check(source, meta={"canonical": True}),
                [],
            )
            self.assertEqual(rule_mirror(source), pair["output"])
            self.assertEqual(source, snapshot)
            self.assertEqual(len(generator.profile_signature(source)), 12)

    def test_exact_dimension_override_boundaries_and_observation(self):
        for band in ("easy", "medium", "hard"):
            for height in (5, 16):
                for width in (7, 20):
                    grid = generator.generate(
                        401,
                        503,
                        difficulty=band,
                        grid_h=height,
                        grid_w=width,
                    )
                    self.assertEqual(
                        generator.observe_overrides(grid),
                        {"grid_h": height, "grid_w": width},
                    )
                    self.assertEqual(generator.self_check(grid, difficulty=band), [])
        with self.assertRaises(ValueError):
            generator.generate(1, 1, grid_h=4)
        with self.assertRaises(ValueError):
            generator.generate(1, 1, grid_w=21)
        with self.assertRaises(TypeError):
            generator.generate(1, 1, unknown_axis=3)

    def test_200_draw_linked_semantic_census_per_band(self):
        for band_index, band in enumerate(("easy", "medium", "hard")):
            wallful = wall_sensitive = open_count = 0
            inputs = set()
            outputs = set()
            branch_totals = Counter()
            for offset in range(200):
                grid = generator.generate(
                    10_000 + band_index * 1_000 + offset,
                    offset,
                    difficulty=band,
                )
                self.assertEqual(generator.self_check(grid, difficulty=band), [])
                facts = generator._analyze_grid(grid)[1]
                counts = semantic_counts(grid)
                self.assertGreater(counts["cyan"], 0)
                self.assertGreater(counts["yellow"], 0)
                self.assertGreater(counts["ties"], 0)
                if counts["walls"]:
                    wallful += 1
                    self.assertGreater(facts["manhattan_disagreement_count"], 0)
                    wall_sensitive += facts["manhattan_disagreement_count"] > 0
                else:
                    open_count += 1
                branch_totals.update(
                    cyan=counts["cyan"],
                    yellow=counts["yellow"],
                    ties=counts["ties"],
                )
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, rule_mirror(grid))))
            with self.subTest(band=band):
                self.assertEqual(open_count, 50)
                self.assertEqual(wallful, 150)
                self.assertEqual(wall_sensitive, 150)
                self.assertGreaterEqual(len(inputs), 198)
                self.assertGreaterEqual(len(outputs), 198)
                self.assertTrue(all(branch_totals[name] > 0 for name in ("cyan", "yellow", "ties")))

    def test_any_three_consecutive_lesson_examples_rebut_manhattan(self):
        for band in ("easy", "medium", "hard"):
            for start in range(24):
                disagreement_examples = 0
                for sample_index in range(start, start + generator.EXAMPLES_NEEDED):
                    grid = generator.generate(90_000 + start, sample_index, difficulty=band)
                    facts = generator._analyze_grid(grid)[1]
                    disagreement_examples += facts["manhattan_disagreement_count"] > 0
                self.assertGreaterEqual(disagreement_examples, 2)

    def test_determinism_fresh_returns_and_global_rng_purity(self):
        random.seed(123456)
        before = random.getstate()
        first = generator.generate(77, 9, difficulty="hard")
        after = random.getstate()
        second = generator.generate(77, 9, difficulty="hard")
        self.assertEqual(before, after)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9
        self.assertNotEqual(first, second)

    def test_four_targeted_impostors_are_rejected(self):
        valid = generator.generate(111, 1, difficulty="medium")

        illegal_color = copy.deepcopy(valid)
        illegal_color[0][0] = 1

        duplicate_seed = copy.deepcopy(valid)
        target = next(
            (r, c)
            for r in range(len(valid))
            for c in range(len(valid[0]))
            if duplicate_seed[r][c] == 0
        )
        duplicate_seed[target[0]][target[1]] = 2

        adjacent_seeds = [[0] * 7 for _ in range(5)]
        adjacent_seeds[2][2] = 2
        adjacent_seeds[2][3] = 3

        disconnected = copy.deepcopy(valid)
        cell = next(
            (r, c)
            for r in range(1, len(valid) - 1)
            for c in range(1, len(valid[0]) - 1)
            if disconnected[r][c] == 0
            and all(disconnected[r + dr][c + dc] == 0 for dr, dc in CARDINAL)
        )
        for dr, dc in CARDINAL:
            disconnected[cell[0] + dr][cell[1] + dc] = 5

        for impostor in (illegal_color, duplicate_seed, adjacent_seeds, disconnected):
            self.assertTrue(generator.self_check(impostor), impostor)
            with self.assertRaises(ValueError):
                generator.observe_overrides(impostor)

    def test_wall_recombination_without_path_effect_is_distribution_invalid_but_executable(self):
        # Canonical train[2] has legal task semantics but its walls happen not to
        # change the Manhattan classification.  It remains accepted when marked
        # canonical, while the generated teaching distribution rejects the same
        # weak shortcut witness.
        weak_wall_scene = copy.deepcopy(self.pairs[2]["input"])
        self.assertEqual(
            generator.self_check(weak_wall_scene, meta={"canonical": True}),
            [],
        )
        errors = generator.self_check(weak_wall_scene)
        self.assertTrue(any("Manhattan" in error for error in errors))

        with ProgramVerifier(timeout=20) as verifier:
            output = verifier.apply(self.row["program_solution"], weak_wall_scene)
        self.assertEqual(output, self.pairs[2]["output"])

    def test_racket_is_input_pure_and_a_b_a_reentrant(self):
        program = self.row["program_solution"]
        first = generator.generate(501, 1, difficulty="hard")
        second = generator.generate(502, 2, difficulty="hard")
        first_snapshot = copy.deepcopy(first)
        second_snapshot = copy.deepcopy(second)
        with ProgramVerifier(timeout=20) as verifier:
            out_a1 = verifier.apply(program, first)
            out_b = verifier.apply(program, second)
            out_a2 = verifier.apply(program, first)
        self.assertEqual(out_a1, rule_mirror(first))
        self.assertEqual(out_b, rule_mirror(second))
        self.assertEqual(out_a1, out_a2)
        self.assertEqual(first, first_snapshot)
        self.assertEqual(second, second_snapshot)


if __name__ == "__main__":
    unittest.main()
