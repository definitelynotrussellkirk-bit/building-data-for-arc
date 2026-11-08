"""Focused regressions for the two-panel occupancy-union generator."""
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
TASK_ID = "5573cf8e2aa4"
GENERATOR_PATH = REPO / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    for line in CANONICAL_PATH.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return [*row["train"], row["test"]]
    raise AssertionError("canonical task row missing")


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


class TwoPanelUnionGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gen = load_generator()

    def test_contract_hooks_exist(self):
        for name in (
            "RULE_HASH",
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
            "grid_h": 5,
            "half_w": 5,
            "palette_size": 1,
            "relation_profile": "balanced",
        }
        grid = self.gen.generate(17, 3, difficulty="easy", **requested)
        self.assertEqual(self.gen.observe_overrides(grid), requested)
        self.assertEqual(self.gen.self_check(grid), [])

    def test_same_color_overlap_draw_refutes_all_named_rivals(self):
        grid = self.gen.generate(
            23,
            5,
            grid_h=5,
            half_w=5,
            palette_size=1,
            relation_profile="balanced",
        )
        counts = self.gen.relation_counts(grid)
        for relation in ("both_zero", "left_only", "right_only", "overlap_same"):
            with self.subTest(relation=relation):
                self.assertGreater(counts[relation], 0)
        intended = self.gen.rule_mirror(grid)
        for name, rival in self.gen.SEMANTIC_RIVALS.items():
            with self.subTest(rival=name):
                self.assertNotEqual(intended, rival(grid))
        for witness, rival_names in self.gen.WITNESS_RIVALS.items():
            if not self.gen.SEMANTIC_WITNESSES[witness](grid):
                continue
            with self.subTest(witness=witness):
                self.assertTrue(
                    any(self.gen.SEMANTIC_RIVALS[name](grid) != intended for name in rival_names)
                )

    def test_canonical_pairs_are_owned_and_mirrored(self):
        for index, pair in enumerate(canonical_pairs()):
            with self.subTest(index=index):
                grid = copy.deepcopy(pair["input"])
                self.assertEqual(self.gen.self_check(grid), [])
                self.assertEqual(self.gen.strict_canonical_like(grid), [])
                self.assertEqual(self.gen.rule_mirror(grid), pair["output"])

    def test_declared_strict_floor_matches_official_census(self):
        hits = 0
        draws = 0
        for difficulty in ("easy", "medium", "hard"):
            for index in range(200):
                digest = hashlib.sha256(
                    f"profile-floor:v1:{TASK_ID}:{difficulty}:{index}".encode()
                ).hexdigest()
                seed = int(digest[:12], 16)
                sample_index = seed % 7919 + index
                grid = self.gen.generate(seed, sample_index, difficulty=difficulty)
                hits += not self.gen.strict_canonical_like(grid)
                draws += 1
        self.assertGreaterEqual(hits / draws, self.gen.MIN_STRICT_FRAC)

    def test_scheduled_lesson_refutes_named_rivals(self):
        for difficulty in ("easy", "medium", "hard"):
            for start in range(12):
                demos = []
                for index in range(start, start + self.gen.EXAMPLES_NEEDED):
                    grid = self.gen.generate(101, index, difficulty=difficulty)
                    demos.append({"input": grid, "output": self.gen.rule_mirror(grid)})
                query_grid = self.gen.generate(
                    101, start + self.gen.EXAMPLES_NEEDED, difficulty=difficulty
                )
                query = {"input": query_grid, "output": self.gen.rule_mirror(query_grid)}
                with self.subTest(difficulty=difficulty, start=start):
                    self.assertEqual(self.gen.lesson_identifiable(demos, query), [])

    def test_pinned_profile_floor_has_exact_canonical_profile_in_every_band(self):
        for difficulty in ("easy", "medium", "hard"):
            exact = 0
            for index in range(20):
                digest = hashlib.sha256(
                    f"profile-floor:v1:{TASK_ID}:{difficulty}:{index}".encode()
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
                exact += profile == (5, 11, 4)
            with self.subTest(difficulty=difficulty):
                self.assertGreaterEqual(exact, 5)

    def test_self_check_ignores_non_axis_canonical_provenance(self):
        grid = copy.deepcopy(canonical_pairs()[0]["input"])
        meta = {
            "canonical": True,
            "split": "train",
            "row_index": 0,
            "pair_index": 0,
        }
        self.assertEqual(self.gen.self_check(grid, meta=meta), [])

    def test_self_check_rejects_broken_structure(self):
        grid = self.gen.generate(
            31,
            2,
            grid_h=5,
            half_w=5,
            palette_size=2,
            relation_profile="balanced",
        )
        broken_divider = copy.deepcopy(grid)
        broken_divider[0][5] = 0
        self.assertTrue(any("divider" in error for error in self.gen.self_check(broken_divider)))

        empty_right = copy.deepcopy(grid)
        for row in empty_right:
            row[6:] = [0] * 5
        self.assertTrue(any("right panel" in error for error in self.gen.self_check(empty_right)))

        extra_color = copy.deepcopy(grid)
        for r, row in enumerate(extra_color):
            for c in range(5):
                if row[c] == 0:
                    row[c] = 7 if 7 not in {value for rr in grid for value in rr} else 6
                    break
            else:
                continue
            break
        self.assertTrue(any("monochrome" in error for error in self.gen.self_check(extra_color)))

    def test_generated_object_count_stays_near_canonical_scale(self):
        counts = []
        for difficulty in ("easy", "medium", "hard"):
            for index in range(20):
                counts.append(object_count(self.gen.generate(12345, index, difficulty=difficulty)))
        self.assertLessEqual(max(counts), 6, counts)

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
