"""Focused regressions for the two-panel occupancy-XOR generator."""
from __future__ import annotations

import copy
from collections import Counter, deque
import hashlib
import importlib.util
import json
import random
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "shared" / "runtime"))
GENERATOR_PATH = REPO / "generators" / "2a1d4a2b313a" / "generator.py"
CANONICAL_PATH = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"


def load_generator():
    spec = importlib.util.spec_from_file_location("generator_2a1d4a2b313a", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module




def object_count(grid):
    """Mirror defect_lint's same-color 4-connected object statistic."""
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    height, width = len(grid), len(grid[0])
    seen = set()
    count = 0
    for start_r in range(height):
        for start_c in range(width):
            if (start_r, start_c) in seen or grid[start_r][start_c] == background:
                continue
            count += 1
            color = grid[start_r][start_c]
            queue = deque([(start_r, start_c)])
            seen.add((start_r, start_c))
            while queue:
                r, c = queue.popleft()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if (nr, nc) in seen or grid[nr][nc] != color:
                        continue
                    seen.add((nr, nc))
                    queue.append((nr, nc))
    return count


def canonical_pairs():
    for line in CANONICAL_PATH.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != "2a1d4a2b313a":
            continue
        return [*row["train"], row["test"]]
    raise AssertionError("canonical task row missing")


class TwoPanelXorGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gen = load_generator()

    def test_contract_hooks_exist(self):
        for name in (
            "observe_overrides",
            "self_check",
            "strict_canonical_like",
            "lesson_identifiable",
            "SEMANTIC_WITNESSES",
            "SEMANTIC_RIVALS",
            "LESSON_COMPETITORS",
            "CANONICAL_SHORTCUTS",
        ):
            with self.subTest(name=name):
                self.assertTrue(hasattr(self.gen, name), f"missing semantic hook {name}")

    def test_unknown_override_is_rejected(self):
        with self.assertRaises(TypeError):
            self.gen.generate(0, 0, typo_axis="silently accepted")

    def test_declared_overrides_are_exactly_observable(self):
        requested = {
            "grid_h": 4,
            "half_w": 4,
            "palette_size": 4,
            "relation_profile": "balanced",
        }
        grid = self.gen.generate(17, 3, difficulty="easy", **requested)
        observer = getattr(self.gen, "observe_overrides", None)
        self.assertTrue(callable(observer), "observe_overrides must be callable")
        self.assertEqual(observer(grid), requested)
        self.assertEqual(self.gen.self_check(grid), [])

    def test_multicolor_draw_contains_every_decisive_relation(self):
        grid = self.gen.generate(
            23,
            5,
            grid_h=4,
            half_w=4,
            palette_size=4,
            relation_profile="balanced",
        )
        relation_counts = getattr(self.gen, "relation_counts", None)
        self.assertTrue(callable(relation_counts), "relation_counts must be callable")
        counts = relation_counts(grid)
        for relation in (
            "both_zero",
            "left_only",
            "right_only",
            "same_nonzero",
            "different_nonzero",
        ):
            with self.subTest(relation=relation):
                self.assertGreater(counts[relation], 0)
        intended = self.gen._authoritative_python(grid)
        self.assertNotEqual(intended, self.gen._rival_raw_inequality(grid))
        self.assertNotEqual(intended, self.gen._rival_union(grid))
        self.assertNotEqual(intended, self.gen._rival_left_only(grid))
        self.assertNotEqual(intended, self.gen._rival_right_only(grid))
        for witness, rival_names in self.gen.WITNESS_RIVALS.items():
            if not self.gen.SEMANTIC_WITNESSES[witness](grid):
                continue
            with self.subTest(witness=witness):
                self.assertTrue(
                    any(
                        self.gen.SEMANTIC_RIVALS[name](grid) != intended
                        for name in rival_names
                    )
                )

    def test_canonical_pairs_are_owned_and_mirrored(self):
        self.assertTrue(callable(getattr(self.gen, "self_check", None)))
        self.assertTrue(callable(getattr(self.gen, "_authoritative_python", None)))
        for index, pair in enumerate(canonical_pairs()):
            with self.subTest(index=index):
                grid = copy.deepcopy(pair["input"])
                self.assertEqual(self.gen.self_check(grid), [])
                self.assertEqual(self.gen.strict_canonical_like(grid), [])
                self.assertEqual(self.gen._authoritative_python(grid), pair["output"])

    def test_scheduled_lesson_refutes_named_rivals(self):
        lesson_identifiable = getattr(self.gen, "lesson_identifiable", None)
        self.assertTrue(callable(lesson_identifiable))
        for difficulty in ("easy", "medium", "hard"):
            for start in range(20):
                demos = []
                for index in range(start, start + self.gen.EXAMPLES_NEEDED):
                    grid = self.gen.generate(101, index, difficulty=difficulty)
                    demos.append({"input": grid, "output": self.gen._authoritative_python(grid)})
                query_grid = self.gen.generate(
                    101, start + self.gen.EXAMPLES_NEEDED, difficulty=difficulty
                )
                query = {
                    "input": query_grid,
                    "output": self.gen._authoritative_python(query_grid),
                }
                with self.subTest(difficulty=difficulty, start=start):
                    self.assertEqual(lesson_identifiable(demos, query), [])

    def test_pinned_profile_floor_has_exact_canonical_profile_in_every_band(self):
        for difficulty in ("easy", "medium", "hard"):
            exact = 0
            for index in range(20):
                digest = hashlib.sha256(
                    f"profile-floor:v1:2a1d4a2b313a:{difficulty}:{index}".encode()
                ).hexdigest()
                seed = int(digest[:12], 16)
                grid = self.gen.generate(
                    seed,
                    seed % 7919 + index,
                    difficulty=difficulty,
                )
                profile = (
                    len(grid),
                    len(grid[0]),
                    len({value for row in grid for value in row}),
                )
                exact += profile == (4, 9, 3)
            with self.subTest(difficulty=difficulty):
                self.assertGreater(exact, 0)

    def test_self_check_rejects_broken_divider_and_constant_answer(self):
        self.assertTrue(callable(getattr(self.gen, "self_check", None)))
        grid = self.gen.generate(
            31,
            2,
            grid_h=4,
            half_w=4,
            palette_size=3,
            relation_profile="balanced",
        )
        broken = copy.deepcopy(grid)
        broken[0][4] = 0
        self.assertTrue(any("divider" in error for error in self.gen.self_check(broken)))

        constant = [[0] * 9 for _ in range(4)]
        for row in constant:
            row[4] = 5
        self.assertTrue(self.gen.self_check(constant))


    def test_generated_object_count_stays_near_canonical_scale(self):
        counts = []
        for difficulty in ("easy", "medium", "hard"):
            for index in range(20):
                grid = self.gen.generate(12345, index, difficulty=difficulty)
                counts.append(object_count(grid))
        self.assertLessEqual(max(counts), 10, counts)

    def test_determinism_fresh_returns_and_global_rng_isolation(self):
        state = random.getstate()
        first = self.gen.generate(444, 19, difficulty="medium")
        self.assertEqual(random.getstate(), state)
        second = self.gen.generate(444, 19, difficulty="medium")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        first[0][0] = 9
        self.assertEqual(self.gen.generate(444, 19, difficulty="medium"), second)


if __name__ == "__main__":
    unittest.main()
