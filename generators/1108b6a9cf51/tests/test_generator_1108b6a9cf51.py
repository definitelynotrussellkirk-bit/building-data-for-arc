"""Focused semantic and contract tests for generator 1108b6a9cf51."""
from __future__ import annotations

from collections import Counter, deque
import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path

from puzzle_generators import base


ROOT = Path(__file__).resolve().parents[1]
generator = importlib.import_module(
    "puzzle_generators.per_puzzle.1108b6a9cf51.generator"
)
BASE_FILE = (
    ROOT
    / "data/base/solutions/banks/ba76b91f26f9/"
    "E106__1108b6a9cf51.json"
)
BANK_FILE = (
    ROOT
    / "data/custom_puzzles/banks/ba76b91f26f9/puzzles.json"
)


def normalized_grid(grid):
    if grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return grid


def canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for raw in handle:
            row = json.loads(raw)
            if row.get("task_id") == generator.TASK_ID:
                return row
    raise AssertionError("canonical row not found")


def canonical_pairs():
    row = canonical_row()
    test = row["test"]
    return list(row["train"]) + (
        list(test) if isinstance(test, list) else [test]
    )


def split_panels(grid):
    size = len(grid)
    return tuple(
        [row[left:right] for row in grid]
        for left, right in (
            (0, size),
            (size + 1, 2 * size + 1),
            (2 * size + 2, 3 * size + 2),
        )
    )


def independent_transform(panel, name):
    size = len(panel)
    if name == "identity":
        return [row[:] for row in panel]
    if name == "rotate_cw":
        return [
            [panel[size - 1 - row][col] for row in range(size)]
            for col in range(size)
        ]
    if name == "rotate_180":
        return [row[::-1] for row in panel[::-1]]
    if name == "rotate_ccw":
        return [
            [panel[row][size - 1 - col] for row in range(size)]
            for col in range(size)
        ]
    if name == "flip_lr":
        return [row[::-1] for row in panel]
    if name == "flip_ud":
        return [row[:] for row in panel[::-1]]
    if name == "transpose":
        return [
            [panel[col][row] for col in range(size)]
            for row in range(size)
        ]
    if name == "anti_transpose":
        return [
            [
                panel[size - 1 - col][size - 1 - row]
                for col in range(size)
            ]
            for row in range(size)
        ]
    raise AssertionError(name)


def independent_candidates(panel_a, panel_b):
    return tuple(
        name
        for name in generator.TRANSFORMS
        if independent_transform(panel_a, name) == panel_b
    )


def normalized_rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def color_is_connected(panel, color):
    cells = {
        (row, col)
        for row, values in enumerate(panel)
        for col, value in enumerate(values)
        if value == color
    }
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        row, col = queue.popleft()
        for neighbor in (
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        ):
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen == cells


class TransformTransferGeneratorTests(unittest.TestCase):
    def test_all_canonical_pairs_match_rule_and_profiles(self):
        pairs = canonical_pairs()
        self.assertEqual(len(pairs), 5)
        signatures = set()
        for pair in pairs:
            source = normalized_grid(pair["input"])
            expected = normalized_grid(pair["output"])
            before = [row[:] for row in source]
            panel_a, panel_b, panel_c = split_panels(source)
            candidates = independent_candidates(panel_a, panel_b)

            self.assertEqual(len(candidates), 1)
            self.assertEqual(generator.self_check(source), [])
            self.assertEqual(generator.rule_mirror(source), expected)
            self.assertEqual(
                independent_transform(panel_c, candidates[0]),
                expected,
            )
            self.assertEqual(source, before)
            signatures.add(generator.canonical_profile_signature(source))

        self.assertNotIn(None, signatures)
        self.assertEqual(signatures, generator._CANONICAL_SIGNATURES)

    def test_every_transform_is_unique_and_visible(self):
        for transform in generator.TRANSFORMS:
            grid = generator.generate(
                101,
                203,
                difficulty="medium",
                panel_size=4,
                transform=transform,
                panel_colors=4,
                a_fill_level="balanced",
                c_fill_level="dense",
            )
            panel_a, panel_b, panel_c = split_panels(grid)
            self.assertEqual(
                independent_candidates(panel_a, panel_b),
                (transform,),
            )
            query_orbit = {
                json.dumps(
                    independent_transform(panel_c, name),
                    separators=(",", ":"),
                )
                for name in generator.TRANSFORMS
            }
            self.assertEqual(len(query_orbit), 8)
            self.assertEqual(
                generator.rule_mirror(grid),
                independent_transform(panel_c, transform),
            )

    def test_exact_axis_boundaries_round_trip_in_every_band(self):
        cases = (
            {
                "panel_size": 3,
                "panel_colors": 2,
                "a_fill_level": "sparse",
                "c_fill_level": "dense",
            },
            {
                "panel_size": 6,
                "panel_colors": 6,
                "a_fill_level": "dense",
                "c_fill_level": "sparse",
            },
        )
        for band in ("easy", "medium", "hard"):
            for case_index, case in enumerate(cases):
                for transform_index, transform in enumerate(
                    generator.TRANSFORMS
                ):
                    overrides = {**case, "transform": transform}
                    captured = []
                    base.set_ctx_observer(captured.append)
                    try:
                        grid = generator.generate(
                            10_000 + case_index,
                            transform_index,
                            difficulty=band,
                            **overrides,
                        )
                    finally:
                        base.set_ctx_observer(None)
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(
                        generator.observe_overrides(grid),
                        overrides,
                    )
                    self.assertEqual(
                        {
                            name: captured[-1]._drawn[name]
                            for name in generator.AXES
                        },
                        overrides,
                    )

    def test_every_fill_level_pair_and_palette_boundary(self):
        for a_fill in generator.FILL_LEVELS:
            for c_fill in generator.FILL_LEVELS:
                for panel_colors in (2, 6):
                    grid = generator.generate(
                        301,
                        401,
                        panel_size=3,
                        transform="rotate_ccw",
                        panel_colors=panel_colors,
                        a_fill_level=a_fill,
                        c_fill_level=c_fill,
                    )
                    observed = generator.observe_overrides(grid)
                    self.assertEqual(observed["a_fill_level"], a_fill)
                    self.assertEqual(observed["c_fill_level"], c_fill)
                    self.assertEqual(
                        observed["panel_colors"],
                        panel_colors,
                    )

    def test_default_and_disjoint_censuses_cover_all_axes(self):
        for seed_start in (0, 50_000):
            transforms = Counter()
            fills = Counter()
            sizes = Counter()
            palettes = Counter()
            inputs = set()
            outputs = set()
            for band_index, band in enumerate(
                ("easy", "medium", "hard")
            ):
                for offset in range(300):
                    seed = seed_start + 1_000 * band_index + offset
                    grid = generator.generate(
                        seed,
                        seed * 17 + 3,
                        difficulty=band,
                    )
                    observed = generator.observe_overrides(grid)
                    self.assertEqual(generator.self_check(grid), [])
                    transforms[observed["transform"]] += 1
                    fills[observed["a_fill_level"]] += 1
                    fills[observed["c_fill_level"]] += 1
                    sizes[observed["panel_size"]] += 1
                    palettes[observed["panel_colors"]] += 1
                    inputs.add(json.dumps(grid, separators=(",", ":")))
                    outputs.add(json.dumps(
                        generator.rule_mirror(grid),
                        separators=(",", ":"),
                    ))

            self.assertEqual(set(transforms), set(generator.TRANSFORMS))
            self.assertEqual(set(fills), set(generator.FILL_LEVELS))
            self.assertEqual(set(sizes), {3, 4, 5, 6})
            self.assertEqual(set(palettes), {2, 3, 4, 5, 6})
            self.assertGreaterEqual(len(inputs), 890)
            self.assertGreaterEqual(len(outputs), 700)

    def test_each_nonzero_color_is_one_connected_component_per_panel(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(100):
                grid = generator.generate(
                    seed,
                    seed * 29 + 5,
                    difficulty=band,
                )
                for panel in split_panels(grid):
                    for color in {
                        value
                        for row in panel
                        for value in row
                        if value != 0
                    }:
                        self.assertTrue(color_is_connected(panel, color))

    def test_negative_recombination_and_mutations_are_rejected(self):
        grid = generator.generate(
            501,
            601,
            panel_size=4,
            transform="rotate_cw",
            panel_colors=3,
            a_fill_level="balanced",
            c_fill_level="balanced",
        )
        panel_a, _panel_b, _panel_c = split_panels(grid)
        broken = [row[:] for row in grid]
        replacement = next(
            value
            for value in range(9)
            if value != broken[0][5]
        )
        broken[0][5] = replacement
        self.assertEqual(independent_candidates(
            panel_a,
            split_panels(broken)[1],
        ), ())
        self.assertTrue(generator.self_check(broken))
        with self.assertRaises(ValueError):
            generator.rule_mirror(broken)

        no_separator = [row[:] for row in grid]
        for row in no_separator:
            row[4] = 0
        self.assertTrue(generator.self_check(no_separator))

        no_query = [row[:] for row in grid]
        for row in no_query:
            row[10:] = [0] * (len(row) - 10)
        self.assertTrue(generator.self_check(no_query))

        for malformed in (
            [[0 for _ in range(11)] for _ in range(3)],
            [[1]],
            [[2, 2], [2, 2]],
            [[1, 2, 3]],
        ):
            self.assertTrue(generator.self_check(malformed))

    def test_unknown_overrides_and_difficulty_fail_loudly(self):
        with self.assertRaises(ValueError):
            generator.generate(1, 2, bogus_axis=True)
        with self.assertRaises(ValueError):
            generator.generate(1, 2, transform="quarter_turn")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, panel_size=7)
        with self.assertRaises(ValueError):
            generator.generate(1, 2, difficulty="extreme")

    def test_deterministic_fresh_returns_and_global_rng_isolation(self):
        kwargs = {
            "difficulty": "hard",
            "panel_size": 6,
            "transform": "anti_transpose",
            "panel_colors": 6,
            "a_fill_level": "dense",
            "c_fill_level": "balanced",
        }
        random.seed(8675309)
        state = random.getstate()
        first = generator.generate(701, 809, **kwargs)
        self.assertEqual(random.getstate(), state)
        expected = [row[:] for row in first]
        first[0][0] = (first[0][0] + 1) % 9
        second = generator.generate(701, 809, **kwargs)
        self.assertEqual(second, expected)
        self.assertIsNot(first, second)
        for row_a, row_b in zip(first, second):
            self.assertIsNot(row_a, row_b)

    def test_rule_hash_and_all_authoritative_sources_are_synchronized(self):
        canonical = canonical_row()["program_solution"]
        bank_entry = json.loads(BANK_FILE.read_text())[0]
        self.assertEqual(bank_entry["id"], "E106")
        base_record = json.loads(BASE_FILE.read_text())
        target = base_record["racket_target"]

        live_sources = (
            canonical,
            bank_entry["program_solution"],
            target["target_code"],
        )
        hashes = {normalized_rule_hash(source) for source in live_sources}
        self.assertEqual(len(hashes), 1)
        self.assertEqual(generator.RULE_HASH, next(iter(hashes))[:12])
        self.assertNotEqual(
            normalized_rule_hash(target["raw_code"]),
            next(iter(hashes)),
        )

        with (ROOT / "data/canonical/puzzle_db.jsonl").open() as handle:
            metadata = next(
                json.loads(raw)
                for raw in handle
                if json.loads(raw).get("task_id") == generator.TASK_ID
            )
        self.assertIn("rotate-ccw", metadata["racket_primitives"])
        self.assertNotIn("dummy", metadata["racket_primitives"])


if __name__ == "__main__":
    unittest.main()
