"""Focused semantic, mutation, and contract tests for 863627ccef26."""
from __future__ import annotations

from collections import Counter, deque
import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path

from puzzle_generators import base
from reviewer_support import canonical_path, find_root, load_selected_generator


ROOT = find_root(__file__)
generator, _SOURCE, _SOURCE_SHA256 = load_selected_generator(TASK_ID := "863627ccef26", root=ROOT)
BASE_FILE = next(
    path
    for path in (
        ROOT / "data/base/solutions/banks/5a410ab56119/H137__863627ccef26.json",
        ROOT / "shared/data/base/solutions/banks/5a410ab56119/H137__863627ccef26.json",
    )
    if path.is_file()
)


def canonical_row():
    with canonical_path(ROOT).open() as handle:
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
    return tuple(
        [row[left:left + 3] for row in grid]
        for left in (0, 4, 8)
    )


def independent_transform(panel, name):
    size = len(panel)
    if name == "id":
        return [row[:] for row in panel]
    if name == "r1":
        return [
            [panel[size - 1 - row][col] for row in range(size)]
            for col in range(size)
        ]
    if name == "r2":
        return [row[::-1] for row in panel[::-1]]
    if name == "r3":
        return [
            [panel[row][size - 1 - col] for row in range(size)]
            for col in range(size)
        ]
    if name == "fh":
        return [row[::-1] for row in panel]
    if name == "fv":
        return [row[:] for row in panel[::-1]]
    if name == "tr":
        return [
            [panel[row][col] for row in range(size)]
            for col in range(size)
        ]
    if name == "atr":
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
        for name in generator.ALL_TRANSFORMS
        if independent_transform(panel_a, name) == panel_b
    )


def independent_merge(query, transform):
    transformed = independent_transform(query, transform)
    return [
        [
            9
            if query[row][col] and transformed[row][col]
            else query[row][col] or transformed[row][col]
            for col in range(3)
        ]
        for row in range(3)
    ]


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


def same_color_object_count(grid):
    remaining = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    }
    objects = 0
    while remaining:
        start = next(iter(remaining))
        color = grid[start[0]][start[1]]
        queue = [start]
        seen = set()
        while queue:
            row, col = queue.pop()
            if (row, col) in seen or (row, col) not in remaining:
                continue
            if grid[row][col] != color:
                continue
            seen.add((row, col))
            queue.extend((
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ))
        remaining -= seen
        objects += 1
    return objects


class TransformSelfMergeGeneratorTests(unittest.TestCase):
    def test_all_canonical_pairs_follow_priority_ordered_rule(self):
        pairs = canonical_pairs()
        self.assertEqual(len(pairs), 3)
        signatures = set()
        candidate_sets = []
        for pair in pairs:
            source = pair["input"]
            expected = pair["output"]
            before = [row[:] for row in source]
            panel_a, panel_b, query = split_panels(source)
            candidates = independent_candidates(panel_a, panel_b)

            self.assertTrue(candidates)
            self.assertEqual(
                generator.rule_mirror(source),
                independent_merge(query, candidates[0]),
            )
            self.assertEqual(generator.rule_mirror(source), expected)
            self.assertEqual(source, before)
            signatures.add(generator.canonical_profile_signature(source))
            candidate_sets.append(candidates)

        self.assertNotIn(None, signatures)
        self.assertEqual(signatures, generator._CANONICAL_SIGNATURES)
        self.assertEqual(candidate_sets[1], ("r2", "atr"))
        self.assertNotEqual(
            independent_merge(split_panels(pairs[1]["input"])[2], "r2"),
            independent_merge(split_panels(pairs[1]["input"])[2], "atr"),
        )

    def test_every_transform_is_unique_visible_and_exercises_both_branches(self):
        for transform in generator.TRANSFORMS:
            grid = generator.generate(
                101,
                203,
                difficulty="medium",
                transform=transform,
                n_distinct_colors=4,
                exemplar_cells=5,
                query_cells=6,
            )
            panel_a, panel_b, query = split_panels(grid)
            self.assertEqual(
                independent_candidates(panel_a, panel_b),
                (transform,),
            )
            output = generator.rule_mirror(grid)
            self.assertEqual(output, independent_merge(query, transform))
            self.assertTrue(any(value == 9 for row in output for value in row))
            self.assertTrue(
                any(value not in (0, 9) for row in output for value in row)
            )

    def test_exact_axis_boundaries_round_trip_in_every_band(self):
        numeric_cases = (
            {
                "n_distinct_colors": 2,
                "exemplar_cells": 3,
                "query_cells": 3,
            },
            {
                "n_distinct_colors": 6,
                "exemplar_cells": 7,
                "query_cells": 7,
            },
        )
        for band in ("easy", "medium", "hard"):
            for case_index, case in enumerate(numeric_cases):
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

    def test_canonical_boundary_has_exactly_five_objects(self):
        for transform in generator.TRANSFORMS:
            grid = generator.generate(
                211,
                307,
                difficulty="easy",
                transform=transform,
                n_distinct_colors=2,
                exemplar_cells=3,
                query_cells=3,
            )
            self.assertEqual(same_color_object_count(grid), 5)
            self.assertEqual(generator.self_check(grid), [])

    def test_default_linked_census_and_disjoint_stability(self):
        expected_values = {
            "easy": ({2, 3}, {3, 4}),
            "medium": ({3, 4, 5}, {4, 5, 6}),
            "hard": ({5, 6}, {6, 7}),
        }
        for seed_start in (0, 50_000):
            for band_index, band in enumerate(("easy", "medium", "hard")):
                axes = {name: Counter() for name in generator.AXES}
                linked = set()
                inputs = set()
                outputs = set()
                for offset in range(300):
                    seed = seed_start + 1_000 * band_index + offset
                    grid = generator.generate(
                        seed,
                        seed * 17 + 3,
                        difficulty=band,
                    )
                    observed = generator.observe_overrides(grid)
                    output = generator.rule_mirror(grid)
                    self.assertEqual(generator.self_check(grid), [])
                    for name, value in observed.items():
                        axes[name][value] += 1
                    conflicts = sum(value == 9 for row in output for value in row)
                    carries = sum(
                        value not in (0, 9)
                        for row in output
                        for value in row
                    )
                    self.assertGreater(conflicts, 0)
                    self.assertGreater(carries, 0)
                    linked.add((
                        observed["transform"],
                        observed["n_distinct_colors"],
                        observed["exemplar_cells"],
                        observed["query_cells"],
                        conflicts,
                        carries,
                    ))
                    inputs.add(json.dumps(grid, separators=(",", ":")))
                    outputs.add(json.dumps(output, separators=(",", ":")))

                expected_colors, expected_cells = expected_values[band]
                self.assertEqual(set(axes["transform"]), set(generator.TRANSFORMS))
                self.assertEqual(
                    set(axes["n_distinct_colors"]), expected_colors
                )
                self.assertEqual(set(axes["exemplar_cells"]), expected_cells)
                self.assertEqual(set(axes["query_cells"]), expected_cells)
                self.assertGreaterEqual(len(linked), 90)
                self.assertEqual(len(inputs), 300)
                self.assertGreaterEqual(len(outputs), 230)

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

    def test_targeted_impostors_and_negative_recombination_are_rejected(self):
        for texture in generator.DEGENERATE_TEXTURES:
            impostor = generator.generate(1, 2, texture=texture)
            self.assertTrue(
                generator.self_check(impostor),
                msg=f"degenerate {texture} unexpectedly accepted",
            )

        grid = generator.generate(
            501,
            601,
            transform="r1",
            n_distinct_colors=4,
            exemplar_cells=5,
            query_cells=5,
        )
        disconnected_query = [row[:] for row in grid]
        for row in range(3):
            disconnected_query[row][8:11] = [0, 0, 0]
        disconnected_query[0][8] = 1
        disconnected_query[2][10] = 2
        self.assertTrue(generator.self_check(disconnected_query))

        broken_demo = [row[:] for row in grid]
        panel_b = split_panels(broken_demo)[1]
        changed = False
        for row in range(3):
            for col in range(3):
                if panel_b[row][col] != 0:
                    broken_demo[row][4 + col] = 7 if panel_b[row][col] != 7 else 6
                    changed = True
                    break
            if changed:
                break
        self.assertTrue(generator.self_check(broken_demo))
        with self.assertRaises(ValueError):
            generator.rule_mirror(broken_demo)

        palette_collision = [row[:] for row in grid]
        a_color = next(
            value
            for row in split_panels(grid)[0]
            for value in row
            if value != 0
        )
        for row in range(3):
            for col in range(8, 11):
                if palette_collision[row][col] != 0:
                    palette_collision[row][col] = a_color
        self.assertTrue(generator.self_check(palette_collision))

    def test_unknown_overrides_and_difficulty_fail_loudly(self):
        with self.assertRaises(ValueError):
            generator.generate(1, 2, bogus_axis=True)
        with self.assertRaises(ValueError):
            generator.generate(1, 2, transform="quarter_turn")
        with self.assertRaises(ValueError):
            generator.generate(1, 2, n_distinct_colors=7)
        with self.assertRaises(ValueError):
            generator.generate(1, 2, exemplar_cells=2)
        with self.assertRaises(ValueError):
            generator.generate(1, 2, difficulty="extreme")
        with self.assertRaises(ValueError):
            generator.generate(
                1,
                2,
                texture="empty_query",
                transform="fh",
            )

    def test_deterministic_fresh_returns_and_global_rng_isolation(self):
        kwargs = {
            "difficulty": "hard",
            "transform": "atr",
            "n_distinct_colors": 6,
            "exemplar_cells": 7,
            "query_cells": 7,
        }
        random.seed(8675309)
        state = random.getstate()
        first = generator.generate(701, 809, **kwargs)
        self.assertEqual(random.getstate(), state)
        expected = [row[:] for row in first]
        first[0][0] = (first[0][0] + 1) % 8
        second = generator.generate(701, 809, **kwargs)
        self.assertEqual(second, expected)
        self.assertIsNot(first, second)
        for row_a, row_b in zip(first, second):
            self.assertIsNot(row_a, row_b)

    def test_rule_hash_and_authoritative_sources_are_synchronized(self):
        canonical = canonical_row()["program_solution"]
        base_record = json.loads(BASE_FILE.read_text())
        target = base_record["racket_target"]
        live_sources = (canonical, target["target_code"])
        hashes = {normalized_rule_hash(source) for source in live_sources}
        self.assertEqual(len(hashes), 1)
        self.assertEqual(generator.RULE_HASH, next(iter(hashes))[:12])
        self.assertNotEqual(
            normalized_rule_hash(target["raw_code"]),
            next(iter(hashes)),
        )


if __name__ == "__main__":
    unittest.main()
