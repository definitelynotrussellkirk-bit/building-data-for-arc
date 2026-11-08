"""Focused semantic and contract tests for generator 20b5e7246250."""
from __future__ import annotations

from collections import Counter, defaultdict
import copy
import hashlib
import importlib
import itertools
import json
from pathlib import Path
import random
import unittest

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "20b5e7246250"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
FULL_RULE_HASH = (
    "42dd98d10175d09a3d9b390f13b3a242c7b5c18c9f255a25d8c458afc3c5153a"
)
BASE_PATH = (
    ROOT
    / "data/base/solutions/banks/1cd6e373f225"
    / "hard_p01__20b5e7246250.json"
)


def canonical_row() -> dict:
    rows = [
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    ]
    if len(rows) != 1:
        raise AssertionError(f"expected one canonical row, found {len(rows)}")
    return rows[0]


def canonical_pairs() -> list[dict]:
    row = canonical_row()
    test = row["test"]
    return row["train"] + (test if isinstance(test, list) else [test])


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def grid_key(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


class KeyedFrameGeneratorTests(unittest.TestCase):
    def test_canonical_pairs_rule_statement_and_source_authority(self):
        row = canonical_row()
        self.assertEqual(len(row["train"]), 3)
        self.assertEqual(len(canonical_pairs()), 4)
        source = row["program_solution"]
        self.assertEqual(normalized_rule_hash(source), FULL_RULE_HASH)
        self.assertEqual(MODULE.RULE_HASH, FULL_RULE_HASH[:12])
        base = json.loads(BASE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            " ".join(base["racket_target"]["target_code"].split()),
            " ".join(source.split()),
        )
        for pair in canonical_pairs():
            before = copy.deepcopy(pair["input"])
            self.assertEqual(MODULE.self_check(pair["input"]), [])
            self.assertEqual(MODULE.rule_mirror(pair["input"]), pair["output"])
            self.assertEqual(pair["input"], before)

    def test_all_boundary_overrides_are_exact_in_every_band(self):
        cases = itertools.product(
            (12, 14),
            (16, 20),
            (3, 5),
            (3, 5),
            ("aligned", "crossed"),
        )
        for case_index, (height, width, size_a, size_b, order) in enumerate(cases):
            expected = {
                "grid_h": height,
                "grid_w": width,
                "motif_size_a": size_a,
                "motif_size_b": size_b,
                "source_order": order,
            }
            for band in ("easy", "medium", "hard"):
                for seed in range(6):
                    grid = MODULE.generate(
                        seed + 1000 * case_index,
                        seed * 17 + case_index,
                        difficulty=band,
                        **expected,
                    )
                    self.assertEqual(MODULE.self_check(grid), [], (band, seed, expected))
                    self.assertEqual(MODULE.observe_overrides(grid), expected)
                    self.assertEqual(len(grid), height)
                    self.assertEqual(len(grid[0]), width)

    def test_default_generation_mirrors_rule_and_covers_linked_semantics(self):
        inputs: set[tuple[tuple[int, ...], ...]] = set()
        outputs: set[tuple[tuple[int, ...], ...]] = set()
        dimensions = set()
        size_pairs = set()
        orders = Counter()
        layouts = Counter()
        frame_profiles = set()
        motif_profiles = set()
        key_colors = set()
        linked = defaultdict(set)
        for seed in range(1800):
            band = (None, "easy", "medium", "hard")[seed % 4]
            grid = MODULE.generate(seed, seed * 31 + 7, difficulty=band)
            analysis = MODULE._analyze(grid)
            self.assertEqual(analysis["errors"], [], (seed, analysis))
            output = MODULE.rule_mirror(grid)
            facts = analysis["facts"]
            inputs.add(grid_key(grid))
            outputs.add(grid_key(output))
            dimensions.add((facts["grid_h"], facts["grid_w"]))
            pair = (facts["motif_size_a"], facts["motif_size_b"])
            size_pairs.add(pair)
            orders[facts["source_order"]] += 1
            layouts[facts["layout_family"]] += 1
            frame_profiles.add(facts["frame_sizes"])
            motif_profiles.add(facts["motif_shapes"])
            key_colors.update(facts["key_colors"])
            linked[pair].add(facts["source_order"])
        self.assertGreater(len(inputs), 1750)
        self.assertGreater(len(outputs), 1700)
        self.assertEqual(dimensions, set(itertools.product(range(12, 15), range(16, 21))))
        self.assertEqual(size_pairs, set(itertools.product(range(3, 6), repeat=2)))
        self.assertEqual(set(orders), {"aligned", "crossed"})
        self.assertEqual(set(layouts), {"sources_above", "sources_below"})
        self.assertTrue(all(value > 250 for value in orders.values()))
        self.assertTrue(all(value > 250 for value in layouts.values()))
        self.assertTrue(all(values == {"aligned", "crossed"} for values in linked.values()))
        self.assertGreater(len(frame_profiles), 45)
        self.assertGreater(len(motif_profiles), 100)
        self.assertEqual(key_colors, {1, 2, 3, 4, 6, 7, 8, 9})

    def test_source_order_is_not_a_color_or_shape_shortcut(self):
        signatures = {"aligned": set(), "crossed": set()}
        color_pairs = {"aligned": set(), "crossed": set()}
        for order in signatures:
            for seed in range(200):
                grid = MODULE.generate(
                    seed,
                    seed * 13,
                    source_order=order,
                    motif_size_a=5,
                    motif_size_b=3,
                )
                facts = MODULE._analyze(grid)["facts"]
                self.assertEqual(facts["source_order"], order)
                signatures[order].add(facts["motif_shapes"])
                color_pairs[order].add(facts["key_colors"])
        self.assertGreater(len(signatures["aligned"] & signatures["crossed"]), 20)
        self.assertGreater(len(color_pairs["aligned"] & color_pairs["crossed"]), 20)

    def test_self_check_rejects_structural_mutations_and_negative_recombinations(self):
        grid = MODULE.generate(
            91,
            47,
            grid_h=14,
            grid_w=20,
            motif_size_a=5,
            motif_size_b=5,
            source_order="crossed",
        )
        analysis = MODULE._analyze(grid)
        self.assertEqual(analysis["errors"], [])
        frames = analysis["frames"]
        keys = analysis["keys"]
        sources = analysis["sources"]

        mutations: dict[str, list[list[int]]] = {}

        missing_key = copy.deepcopy(grid)
        missing_key[keys[0]["position"][0]][keys[0]["position"][1]] = 0
        mutations["missing_key"] = missing_key

        broken_frame = copy.deepcopy(grid)
        frame_cell = frames[0]["cells"][0]
        broken_frame[frame_cell[0]][frame_cell[1]] = 0
        mutations["broken_frame"] = broken_frame

        colored_interior = copy.deepcopy(grid)
        r1, c1, _, _ = frames[0]["bbox"]
        colored_interior[r1 + 1][c1 + 1] = keys[0]["color"]
        mutations["colored_interior"] = colored_interior

        missing_source = copy.deepcopy(grid)
        for row, col in sources[0]["cells"]:
            missing_source[row][col] = 0
        mutations["missing_source"] = missing_source

        wrong_source_color = copy.deepcopy(grid)
        for row, col in sources[1]["cells"]:
            wrong_source_color[row][col] = keys[0]["color"]
        mutations["negative_recombination_wrong_color"] = wrong_source_color

        duplicate_key = copy.deepcopy(grid)
        duplicate_key[keys[1]["position"][0]][keys[1]["position"][1]] = keys[0]["color"]
        mutations["negative_recombination_duplicate_key"] = duplicate_key

        source_inside_frame = copy.deepcopy(grid)
        for row, col in sources[0]["cells"]:
            source_inside_frame[row][col] = 0
        normalized = MODULE._normalize(sources[0]["cells"])
        for drow, dcol in normalized:
            source_inside_frame[r1 + 1 + drow][c1 + 1 + dcol] = keys[0]["color"]
        mutations["source_inside_frame"] = source_inside_frame

        oversized_source = copy.deepcopy(grid)
        source_cells = set(sources[0]["cells"])
        added = False
        for row, col in sources[0]["cells"]:
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                candidate = (row + drow, col + dcol)
                if (
                    0 <= candidate[0] < len(grid)
                    and 0 <= candidate[1] < len(grid[0])
                    and candidate not in source_cells
                    and oversized_source[candidate[0]][candidate[1]] == 0
                ):
                    oversized_source[candidate[0]][candidate[1]] = keys[0]["color"]
                    added = True
                    break
            if added:
                break
        self.assertTrue(added)
        mutations["oversized_source"] = oversized_source

        for name, mutation in mutations.items():
            self.assertTrue(MODULE.self_check(mutation), name)
            with self.assertRaises(ValueError, msg=name):
                MODULE.rule_mirror(mutation)

    def test_determinism_fresh_returns_global_rng_and_rejections(self):
        random.seed(0x20B5)
        state = random.getstate()
        first = MODULE.generate(17, 29, difficulty="hard")
        second = MODULE.generate(17, 29, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        self.assertEqual(random.getstate(), state)

        bad_calls = (
            {"texture": "warm"},
            {"palette_size": 4},
            {"grid_h": 11},
            {"grid_w": 21},
            {"motif_size_a": 2},
            {"motif_size_b": 6},
            {"source_order": "random"},
            {"grid_h": 12.5},
        )
        for overrides in bad_calls:
            with self.assertRaises(ValueError, msg=overrides):
                MODULE.generate(1, 2, **overrides)
        for difficulty in ("extreme", -0.1, 1.1, True, object()):
            with self.assertRaises(ValueError, msg=difficulty):
                MODULE.generate(1, 2, difficulty=difficulty)


if __name__ == "__main__":
    unittest.main()
