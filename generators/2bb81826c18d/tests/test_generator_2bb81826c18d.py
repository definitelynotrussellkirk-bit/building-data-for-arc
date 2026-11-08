"""Focused semantic regressions for generator 2bb81826c18d."""
from __future__ import annotations

import copy
import hashlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

from reviewer_support import canonical_path, find_root, load_selected_generator


ROOT = find_root(__file__)
TASK_ID = "2bb81826c18d"
GENERATOR, GENERATOR_PATH, GENERATOR_HASH = load_selected_generator(TASK_ID, root=ROOT)


def canonical_rows() -> list[dict]:
    rows = []
    path = canonical_path(root=ROOT)
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            rows.append(row)
    return rows


def canonical_pairs() -> list[dict]:
    pairs = []
    for row in canonical_rows():
        pairs.extend(row.get("train") or [])
        test = row.get("test") or []
        pairs.extend(test if isinstance(test, list) else [test])
    return pairs


def normalized_rule_hash(source: str) -> str:
    normalized = " ".join(source.split())
    return hashlib.sha256(normalized.encode()).hexdigest()[:12]


def independent_rule(grid):
    """Independent color-bbox implementation of the canonical rule."""
    output = copy.deepcopy(grid)
    colors = sorted({value for row in grid for value in row if value != 0})
    for color in colors:
        cells = [
            (row, col)
            for row in range(len(grid))
            for col in range(len(grid[0]))
            if grid[row][col] == color
        ]
        top = min(row for row, _ in cells)
        bottom = max(row for row, _ in cells)
        left = min(col for _, col in cells)
        right = max(col for _, col in cells)
        for row in range(top + 1, bottom):
            for col in range(left + 1, right):
                rel_row = row - top - 1
                rel_col = col - left - 1
                if (rel_row + rel_col) % 2 == 0:
                    output[row][col] = 0
    return output


def component_areas(grid) -> list[int]:
    return sorted(
        component["area"]
        for component in GENERATOR._analyze(grid)["components"]
    )


class Generator2bb81826c18dTests(unittest.TestCase):
    def test_metadata_and_all_rule_authorities_are_synchronized(self):
        rows = canonical_rows()
        self.assertEqual(2, len(rows))
        sources = {row["program_solution"] for row in rows}
        self.assertEqual(1, len(sources))
        source = sources.pop()
        self.assertEqual(GENERATOR.RULE_HASH, normalized_rule_hash(source))
        self.assertEqual("2.1.0", GENERATOR.VERSION)
        self.assertEqual(
            {
                "grid_h",
                "grid_w",
                "n_rects",
                "size_profile",
                "palette_kind",
                "edge_touch",
            },
            set(GENERATOR.AXES),
        )

    def test_every_canonical_pair_is_a_positive_control_and_exact(self):
        pairs = canonical_pairs()
        self.assertEqual(8, len(pairs))
        self.assertEqual(
            4,
            len(
                {
                    (
                        tuple(map(tuple, pair["input"])),
                        tuple(map(tuple, pair["output"])),
                    )
                    for pair in pairs
                }
            ),
        )
        for index, pair in enumerate(pairs):
            with self.subTest(index=index):
                source = copy.deepcopy(pair["input"])
                self.assertEqual([], GENERATOR.self_check(source))
                self.assertEqual(pair["output"], independent_rule(source))
                self.assertEqual(pair["output"], GENERATOR.rule_mirror(source))
                self.assertEqual(pair["input"], source)

    def test_every_exact_override_is_observable_across_all_bands(self):
        for band in ("easy", "medium", "hard"):
            for seed, height, width, count, edge in (
                (3, 10, 10, 1, False),
                (5, 10, 24, 4, True),
                (7, 24, 10, 4, False),
                (11, 24, 24, 1, True),
            ):
                for size_profile in GENERATOR.SIZE_PROFILES:
                    for palette_kind in GENERATOR.PALETTE_KINDS:
                        with self.subTest(
                            band=band,
                            seed=seed,
                            height=height,
                            width=width,
                            count=count,
                            edge=edge,
                            size_profile=size_profile,
                            palette_kind=palette_kind,
                        ):
                            grid = GENERATOR.generate(
                                seed,
                                seed * 17 + 3,
                                difficulty=band,
                                grid_h=height,
                                grid_w=width,
                                n_rects=count,
                                edge_touch=edge,
                                size_profile=size_profile,
                                palette_kind=palette_kind,
                            )
                            self.assertEqual([], GENERATOR.self_check(grid))
                            self.assertEqual(
                                {
                                    "grid_h": height,
                                    "grid_w": width,
                                    "n_rects": count,
                                    "edge_touch": edge,
                                },
                                GENERATOR.observe_overrides(grid),
                            )
                            colors = {
                                component["color"]
                                for component in GENERATOR._analyze(grid)[
                                    "components"
                                ]
                            }
                            self.assertLessEqual(
                                colors,
                                set(GENERATOR._PALETTE_POOLS[palette_kind]),
                            )

    def test_defaults_are_deterministic_fresh_and_do_not_touch_global_rng(self):
        global_state = random.getstate()
        for band in ("easy", "medium", "hard"):
            for seed in range(50):
                first = GENERATOR.generate(seed, seed * 19 + 2, difficulty=band)
                second = GENERATOR.generate(seed, seed * 19 + 2, difficulty=band)
                pristine = copy.deepcopy(first)
                self.assertEqual(first, second)
                self.assertIsNot(first, second)
                self.assertTrue(
                    all(a is not b for a, b in zip(first, second)),
                    "rows must be fresh objects",
                )
                first[0][0] = (first[0][0] + 1) % 10
                self.assertEqual(
                    pristine,
                    GENERATOR.generate(seed, seed * 19 + 2, difficulty=band),
                )
                self.assertEqual(global_state, random.getstate())

    def test_default_distribution_covers_declared_structure_and_phase(self):
        counts = {band: Counter() for band in ("easy", "medium", "hard")}
        edge_states = {band: set() for band in counts}
        inputs = set()
        outputs = set()
        origin_parities = set()
        max_area = 0
        for band_index, band in enumerate(counts):
            for seed in range(400):
                grid = GENERATOR.generate(
                    10_000 * band_index + seed,
                    seed * 23 + 5,
                    difficulty=band,
                )
                analysis = GENERATOR._analyze(grid)
                self.assertEqual([], analysis["errors"])
                counts[band][analysis["n_rects"]] += 1
                edge_states[band].add(analysis["edge_touch"])
                inputs.add(tuple(map(tuple, grid)))
                output = GENERATOR.rule_mirror(grid)
                outputs.add(tuple(map(tuple, output)))
                self.assertNotEqual(grid, output)
                for component in analysis["components"]:
                    origin_parities.add(
                        (component["top"] + component["left"]) % 2
                    )
                    max_area = max(max_area, component["area"])
        self.assertEqual({1, 2}, set(counts["easy"]))
        self.assertEqual({1, 2, 3}, set(counts["medium"]))
        self.assertEqual({2, 3, 4}, set(counts["hard"]))
        self.assertTrue(all(states == {False, True} for states in edge_states.values()))
        self.assertEqual({0, 1}, origin_parities)
        self.assertGreaterEqual(max_area, 80)
        self.assertGreater(len(inputs), 1_150)
        self.assertEqual(len(inputs), len(outputs))

    def test_size_profiles_materially_change_component_scale(self):
        medians = {}
        for profile in GENERATOR.SIZE_PROFILES:
            areas = []
            for seed in range(120):
                grid = GENERATOR.generate(
                    30_000 + seed,
                    seed * 31,
                    difficulty="hard",
                    grid_h=24,
                    grid_w=24,
                    n_rects=2,
                    edge_touch=False,
                    size_profile=profile,
                )
                areas.extend(component_areas(grid))
            areas.sort()
            medians[profile] = areas[len(areas) // 2]
        self.assertLess(medians["compact"], medians["mixed"])
        self.assertLess(medians["mixed"], medians["large"])

    def test_self_check_rejects_minimal_and_structural_impostors(self):
        impostors = {}
        impostors["all_background"] = [[0] * 12 for _ in range(12)]
        impostors["full_one_color"] = [[3] * 12 for _ in range(12)]

        singleton = [[0] * 12 for _ in range(12)]
        singleton[4][4] = 3
        impostors["singleton"] = singleton

        solid_2x2 = [[0] * 12 for _ in range(12)]
        for row in range(3, 5):
            for col in range(3, 5):
                solid_2x2[row][col] = 4
        impostors["solid_2x2"] = solid_2x2

        short_line = [[0] * 12 for _ in range(12)]
        for col in range(2, 8):
            short_line[5][col] = 6
        impostors["short_line"] = short_line

        hollow = [[0] * 12 for _ in range(12)]
        for row in range(2, 7):
            for col in range(2, 8):
                if row in (2, 6) or col in (2, 7):
                    hollow[row][col] = 7
        impostors["hollow_rectangle"] = hollow

        l_shape = [[0] * 12 for _ in range(12)]
        for row in range(2, 8):
            l_shape[row][2] = 8
        for col in range(2, 8):
            l_shape[7][col] = 8
        impostors["l_shape"] = l_shape

        duplicate_color = [[0] * 12 for _ in range(12)]
        for top, left in ((1, 1), (7, 7)):
            for row in range(top, top + 3):
                for col in range(left, left + 3):
                    duplicate_color[row][col] = 5
        impostors["duplicate_color_components"] = duplicate_color

        touching = [[0] * 12 for _ in range(12)]
        for row in range(2, 6):
            for col in range(1, 5):
                touching[row][col] = 2
            for col in range(5, 9):
                touching[row][col] = 4
        impostors["touching_rectangles"] = touching

        for name, grid in impostors.items():
            with self.subTest(name=name):
                self.assertTrue(GENERATOR.self_check(grid), name)

    def test_rectangle_relative_phase_falsifies_global_parity_shortcut(self):
        witness = None
        for seed in range(500):
            grid = GENERATOR.generate(
                50_000 + seed,
                seed * 37,
                difficulty="medium",
                n_rects=1,
                edge_touch=False,
                size_profile="large",
            )
            component = GENERATOR._analyze(grid)["components"][0]
            if (component["top"] + component["left"]) % 2 == 1:
                witness = grid
                break
        self.assertIsNotNone(witness)
        expected = GENERATOR.rule_mirror(witness)
        global_parity = copy.deepcopy(witness)
        component = GENERATOR._analyze(witness)["components"][0]
        for row in range(component["top"] + 1, component["bottom"]):
            for col in range(component["left"] + 1, component["right"]):
                if (row + col) % 2 == 0:
                    global_parity[row][col] = 0
        self.assertNotEqual(expected, global_parity)

    def test_invalid_calls_reject_loudly(self):
        bad_calls = (
            {"difficulty": "expert"},
            {"grid_h": 9},
            {"grid_w": 25},
            {"n_rects": 0},
            {"n_rects": True},
            {"edge_touch": 1},
            {"size_profile": "tiny"},
            {"palette_kind": "neon"},
            {"texture": "single_rect"},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    difficulty = kwargs.pop("difficulty", None)
                    try:
                        GENERATOR.generate(1, 2, difficulty=difficulty, **kwargs)
                    finally:
                        if difficulty is not None:
                            kwargs["difficulty"] = difficulty


if __name__ == "__main__":
    unittest.main()
