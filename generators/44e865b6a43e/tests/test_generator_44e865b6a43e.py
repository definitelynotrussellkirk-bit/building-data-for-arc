from __future__ import annotations

import copy
import hashlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

from puzzle_generators import base
from reviewer_support import canonical_path, find_root, load_selected_generator
from solvers.grounded_rules import GROUNDED_RULES


ROOT = find_root(__file__)
TASK_ID = "44e865b6a43e"
generator, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
BASE_PATH = canonical_path(ROOT).parent.parent / "base/solutions/training/2601afb7__44e865b6a43e.json"
EXPECTED_BASE_SHA256 = "b8656806ef5054599a4e8291a235745334114b391435075d133843577cdf617d"
EXPECTED_RULE_SHA256 = "de38c98a18568a2fc509a998ce7bc154fb797ff615dd7ec5367ae9d3178e2443"


def canonical_row():
    with canonical_path(ROOT).open() as handle:
        rows = [
            json.loads(line)
            for line in handle
            if json.loads(line).get("task_id") == TASK_ID
        ]
    if len(rows) != 1:
        raise AssertionError(f"expected one canonical row, got {len(rows)}")
    return rows[0]


def canonical_pairs():
    row = canonical_row()
    test = row["test"]
    return list(row["train"]) + ([test] if isinstance(test, dict) else list(test))


def normalized_rule(source: str) -> str:
    return " ".join(source.split())


def independent_profile(grid):
    height = len(grid)
    width = len(grid[0])
    columns = [
        col
        for col in range(width)
        if any(grid[row][col] != 7 for row in range(height))
    ]
    colors = []
    heights = []
    for col in columns:
        top = next(row for row in range(height) if grid[row][col] != 7)
        colors.append(grid[top][col])
        heights.append(height - top)
    return columns, colors, heights


def independent_rule(grid):
    height = len(grid)
    width = len(grid[0])
    columns, colors, heights = independent_profile(grid)
    output = [[7] * width for _ in range(height)]
    output_colors = [colors[-1], *colors[:-1]]
    output_heights = [*heights[1:], heights[0]]
    for col, color, bar_height in zip(columns, output_colors, output_heights):
        for row in range(height - bar_height, height):
            output[row][col] = color
    return output


class Generator44e865b6a43eTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = canonical_row()
        cls.pairs = canonical_pairs()

    def test_rule_hash_pins_all_authorities_and_exact_selected_alignment(self):
        self.assertEqual(
            hashlib.sha256(BASE_PATH.read_bytes()).hexdigest(),
            EXPECTED_BASE_SHA256,
        )
        base_record = json.loads(BASE_PATH.read_text())
        self.assertEqual(base_record["racket_target"]["target_code"], self.row["program_solution"])
        sources = {
            "canonical": self.row["program_solution"],
            "base_raw": base_record["racket_target"]["raw_code"],
            "base_target": base_record["racket_target"]["target_code"],
            "grounded": GROUNDED_RULES[TASK_ID],
        }
        normalized = {name: normalized_rule(source) for name, source in sources.items()}
        self.assertEqual(len(set(normalized.values())), 1, normalized.keys())
        digest = hashlib.sha256(next(iter(normalized.values())).encode()).hexdigest()
        self.assertEqual(digest, EXPECTED_RULE_SHA256)
        self.assertEqual(generator.RULE_HASH, digest[:12])

    def test_all_canonical_pairs_are_accepted_and_exact(self):
        self.assertEqual(len(self.pairs), 4)
        saw_repeated_heights = False
        saw_black = False
        for pair in self.pairs:
            grid = copy.deepcopy(pair["input"])
            before = copy.deepcopy(grid)
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(independent_rule(grid), pair["output"])
            self.assertEqual(generator.rule_mirror(grid), pair["output"])
            self.assertEqual(grid, before)
            _columns, colors, heights = independent_profile(grid)
            saw_repeated_heights |= len(set(heights)) < len(heights)
            saw_black |= 0 in colors
        self.assertTrue(saw_repeated_heights)
        self.assertTrue(saw_black)

    def test_all_axis_boundaries_and_height_families_are_exact(self):
        for band in ("easy", "medium", "hard"):
            for grid_h in (7, 12):
                for n_bars in (3, 5):
                    for pattern in generator.HEIGHT_PATTERNS:
                        grid = generator.generate(
                            grid_h * 100 + n_bars,
                            len(pattern) * 17,
                            difficulty=band,
                            grid_h=grid_h,
                            n_bars=n_bars,
                            height_pattern=pattern,
                        )
                        self.assertEqual(generator.self_check(grid), [])
                        profile = generator.bar_profile(grid)
                        self.assertEqual(profile["grid_h"], grid_h)
                        self.assertEqual(profile["grid_w"], 2 * n_bars + 1)
                        self.assertEqual(profile["n_bars"], n_bars)
                        self.assertEqual(
                            generator.observe_overrides(grid),
                            {"n_bars": n_bars, "height_pattern": pattern},
                        )
                        heights = profile["heights"]
                        if pattern == "ascending":
                            self.assertEqual(heights, sorted(heights))
                            self.assertEqual(len(set(heights)), n_bars)
                        elif pattern == "descending":
                            self.assertEqual(heights, sorted(heights, reverse=True))
                            self.assertEqual(len(set(heights)), n_bars)
                        elif pattern == "mixed":
                            self.assertEqual(len(set(heights)), n_bars)
                            self.assertNotEqual(heights, sorted(heights))
                            self.assertNotEqual(heights, sorted(heights, reverse=True))
                        else:
                            self.assertLess(len(set(heights)), n_bars)
                            self.assertGreater(len(set(heights)), 1)
                        self.assertEqual(
                            generator.rule_mirror(grid),
                            independent_rule(grid),
                        )

    def test_default_generation_is_deterministic_fresh_and_global_rng_pure(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(80):
                sample_index = seed * 31 + 9
                global_state = random.getstate()
                first = generator.generate(seed, sample_index, difficulty=band)
                self.assertEqual(random.getstate(), global_state)
                second = generator.generate(seed, sample_index, difficulty=band)
                self.assertEqual(first, second)
                self.assertIsNot(first, second)
                self.assertTrue(all(a is not b for a, b in zip(first, second)))
                self.assertEqual(generator.self_check(first), [])
                self.assertNotEqual(first, generator.rule_mirror(first))
                self.assertEqual(generator.rule_mirror(first), independent_rule(first))

    def test_keyed_provenance_and_default_distribution_cover_the_rule(self):
        distributions = {}
        saw_black = False
        for band in ("easy", "medium", "hard"):
            patterns = Counter()
            bar_counts = Counter()
            pairs = set()
            heights_seen = set()
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                first = generator.generate(90_000, 17, difficulty=band)
            finally:
                base.set_ctx_observer(None)
            self.assertEqual(len(captured), 1)
            ctx = captured[0]
            self.assertEqual(set(generator.AXES), {"grid_h", "n_bars", "height_pattern"})
            self.assertTrue(set(generator.AXES) <= set(ctx.recorded_draws()))
            self.assertEqual(ctx.axis_value("grid_h"), len(first))
            self.assertEqual(ctx.axis_value("n_bars"), generator.bar_profile(first)["n_bars"])

            for seed in range(240):
                grid = generator.generate(10_000 + seed, seed * 37 + 5, difficulty=band)
                output = generator.rule_mirror(grid)
                profile = generator.bar_profile(grid)
                heights = profile["heights"]
                if len(set(heights)) < len(heights):
                    pattern = "repeat"
                elif heights == sorted(heights):
                    pattern = "ascending"
                elif heights == sorted(heights, reverse=True):
                    pattern = "descending"
                else:
                    pattern = "mixed"
                patterns[pattern] += 1
                bar_counts[profile["n_bars"]] += 1
                heights_seen.update(heights)
                saw_black |= 0 in profile["colors"]
                pairs.add((tuple(map(tuple, grid)), tuple(map(tuple, output))))
            self.assertEqual(set(patterns), set(generator.HEIGHT_PATTERNS))
            # The old per-family count floor assumed four uniformly mixed
            # families. The new contract guarantees a repeat at all 120 odd
            # indices; the set comparison above checks general-family support.
            self.assertGreaterEqual(patterns["repeat"], 120)
            self.assertGreaterEqual(len(pairs), 235)
            self.assertTrue(all(count >= 3 for count in bar_counts))
            distributions[band] = {"bars": bar_counts, "heights": heights_seen}

        self.assertTrue(saw_black)
        self.assertLess(max(distributions["easy"]["bars"]), max(distributions["hard"]["bars"]))
        self.assertLess(max(distributions["easy"]["heights"]), max(distributions["hard"]["heights"]))

    def test_self_check_rejects_targeted_semantic_mutations(self):
        source = copy.deepcopy(self.pairs[0]["input"])
        self.assertEqual(generator.self_check(source), [])

        mutations = {}

        separator = copy.deepcopy(source)
        separator[-1][0] = 1
        mutations["foreground_in_separator"] = separator

        hole = copy.deepcopy(source)
        hole[4][5] = 7
        mutations["hole_in_bar"] = hole

        mixed_color = copy.deepcopy(source)
        original = mixed_color[-1][5]
        replacement = next(color for color in range(10) if color not in (7, original))
        mixed_color[-1][5] = replacement
        mutations["two_colors_in_one_bar"] = mixed_color

        duplicate_color = copy.deepcopy(source)
        old_color = duplicate_color[-1][3]
        new_color = duplicate_color[-1][1]
        for row in range(len(duplicate_color)):
            if duplicate_color[row][3] == old_color:
                duplicate_color[row][3] = new_color
        mutations["duplicate_bar_color"] = duplicate_color

        full_height = copy.deepcopy(source)
        full_height[0][5] = full_height[-1][5]
        mutations["full_height_bar"] = full_height

        two_bars = [row[:-4] for row in source]
        mutations["two_bar_shortcut"] = two_bars

        for name, grid in mutations.items():
            with self.subTest(name=name):
                self.assertTrue(generator.self_check(grid), name)
                self.assertEqual(generator.observe_overrides(grid), {})

    def test_invalid_requests_fail_loudly(self):
        bad_calls = (
            {"difficulty": "expert"},
            {"bogus": 1},
            {"grid_h": 6},
            {"grid_h": 13},
            {"grid_h": 7.0},
            {"grid_h": "7"},
            {"n_bars": 2},
            {"n_bars": 6},
            {"n_bars": True},
            {"height_pattern": "equal"},
            {"height_pattern": 1},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(1, 2, **kwargs)


if __name__ == "__main__":
    unittest.main()
