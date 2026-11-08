"""Focused semantic and override regressions for generator 46c02325ed3b."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib
import json
import random
import unittest

from puzzle_generators import base
from reviewer_support import canonical_path, find_root


TASK_ID = "46c02325ed3b"
ROOT = find_root(__file__)
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _canonical_row():
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


def _canonical_pairs():
    row = _canonical_row()
    return [*row.get("train", []), *row.get("test", [])]


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _profile(grid):
    source = MODULE._source_and_edge(grid)
    assert source is not None
    edge = source[1]
    positions, holes = MODULE._wall_profile(grid, edge)
    transitions = [
        "aligned" if left & right else "shifted"
        for left, right in zip(holes, holes[1:])
    ]
    return edge, positions, holes, transitions


class Generator46c02325ed3bTests(unittest.TestCase):
    def test_canonical_inventory_rule_pin_and_exact_outputs(self):
        row = _canonical_row()
        pairs = _canonical_pairs()
        self.assertEqual(len(row["train"]), 3)
        self.assertEqual(len(row["test"]), 1)
        self.assertEqual(MODULE.RULE_HASH, "253f10f62a51")
        self.assertEqual(MODULE.RULE_HASH, _normalized_hash(row["program_solution"]))

        canonical_gap_counts = set()
        for pair in pairs:
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            self.assertEqual(MODULE.self_check(source), [])
            self.assertEqual(MODULE.rule_mirror(source), pair["output"])
            self.assertEqual(source, before)
            canonical_gap_counts.update(len(gaps) for gaps in _profile(source)[2])
        # Two official pairs contain a three-hole wall. The pre-repair generator
        # incorrectly documented and sampled only one or two holes.
        self.assertEqual(canonical_gap_counts, {1, 2, 3})

    def test_declared_axes_are_exact_observable_and_boundaries_work(self):
        self.assertEqual(set(MODULE.AXES), {"grid_h", "grid_w", "n_walls", "edge"})
        cases = [
            {"grid_h": 10},
            {"grid_h": 18},
            {"grid_w": 10},
            {"grid_w": 18},
            {"n_walls": 2},
            {"n_walls": 5},
            {"edge": "top"},
            {"edge": "bottom"},
            {"edge": "left"},
            {"edge": "right"},
            {"grid_h": 13, "grid_w": 10, "n_walls": 5, "edge": "top"},
            {"grid_h": 10, "grid_w": 13, "n_walls": 5, "edge": "left"},
        ]
        for band in ("easy", "medium", "hard"):
            for case in cases:
                for seed in range(6):
                    with self.subTest(band=band, case=case, seed=seed):
                        grid = MODULE.generate(
                            seed + 700,
                            seed * 23 + 5,
                            difficulty=band,
                            **case,
                        )
                        observed = MODULE.observe_overrides(grid)
                        for key, value in case.items():
                            self.assertEqual(observed[key], value)
                        self.assertEqual(MODULE.self_check(grid), [])

        for bad in (
            {"grid_h": 9},
            {"grid_h": 19},
            {"grid_w": 9},
            {"grid_w": 19},
            {"n_walls": 1},
            {"n_walls": 6},
            {"edge": "diagonal"},
            {"unknown_axis": 1},
            {"grid_h": 10, "n_walls": 5, "edge": "top"},
            {"grid_w": 10, "n_walls": 5, "edge": "left"},
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    MODULE.generate(1, 2, difficulty="easy", **bad)

    def test_ordinary_keyed_axis_values_match_returned_grid(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(80):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = MODULE.generate(
                        seed + 1300,
                        seed * 31 + 7,
                        difficulty=band,
                    )
                finally:
                    base.set_ctx_observer(None)
                self.assertEqual(len(captured), 1)
                observed = MODULE.observe_overrides(grid)
                for axis in MODULE.AXES:
                    self.assertEqual(captured[0]._drawn[axis], observed[axis])

    def test_linked_semantic_census_has_every_required_branch(self):
        expected_wall_support = {
            "easy": {3, 4},
            "medium": {4},
            "hard": {4, 5},
        }
        for band in ("easy", "medium", "hard"):
            inputs = set()
            outputs = set()
            edges = Counter()
            walls = Counter()
            gaps = Counter()
            transition_grids = Counter()
            changed_counts = []
            matches = 0
            for seed in range(240):
                grid = MODULE.generate(
                    seed + 5000,
                    seed * 37 + 11,
                    difficulty=band,
                )
                output = MODULE.rule_mirror(grid)
                edge, positions, hole_sets, transitions = _profile(grid)
                linked = (
                    MODULE.self_check(grid) == []
                    and output != grid
                    and len(positions) >= 3
                    and {len(item) for item in hole_sets} == {1, 2, 3}
                    and "aligned" in transitions
                    and "shifted" in transitions
                    and all(
                        out_value == in_value or (in_value == 0 and out_value == 2)
                        for in_row, out_row in zip(grid, output)
                        for in_value, out_value in zip(in_row, out_row)
                    )
                    and all(
                        (in_value == 8) == (out_value == 8)
                        for in_row, out_row in zip(grid, output)
                        for in_value, out_value in zip(in_row, out_row)
                    )
                )
                matches += int(linked)
                edges[edge] += 1
                walls[len(positions)] += 1
                gaps.update(len(item) for item in hole_sets)
                transition_grids.update(set(transitions))
                changed_counts.append(
                    sum(
                        a != b
                        for in_row, out_row in zip(grid, output)
                        for a, b in zip(in_row, out_row)
                    )
                )
                inputs.add(_frozen(grid))
                outputs.add(_frozen(output))

            self.assertEqual(matches, 240)
            self.assertEqual(set(edges), {"top", "bottom", "left", "right"})
            self.assertEqual(set(walls), expected_wall_support[band])
            self.assertEqual(set(gaps), {1, 2, 3})
            self.assertEqual(set(transition_grids), {"aligned", "shifted"})
            self.assertGreater(min(changed_counts), 0)
            self.assertGreaterEqual(len(inputs), 238)
            self.assertGreaterEqual(len(outputs), 238)

    def test_determinism_fresh_returns_input_purity_and_global_rng_purity(self):
        random.seed(20260723)
        state = random.getstate()
        first = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))

        before = copy.deepcopy(second)
        output = MODULE.rule_mirror(second)
        self.assertEqual(second, before)
        self.assertIsNot(output, second)
        first[0][0] = 9 if first[0][0] != 9 else 7
        self.assertNotEqual(first, second)

    def test_self_check_rejects_targeted_impostors(self):
        grid = MODULE.generate(
            2201,
            17,
            difficulty="medium",
            edge="top",
            grid_h=15,
            grid_w=14,
            n_walls=4,
        )
        (_, source_col), _ = MODULE._source_and_edge(grid)
        positions, holes = MODULE._wall_profile(grid, "top")

        duplicate_source = copy.deepcopy(grid)
        duplicate_source[0][1 if source_col != 1 else 2] = 2

        corner_source = copy.deepcopy(grid)
        corner_source[0][source_col] = 0
        corner_source[0][0] = 2

        four_hole_wall = copy.deepcopy(grid)
        first_wall = positions[0]
        extra_holes = [c for c in range(1, len(grid[0]) - 1) if c not in holes[0]][: 4 - len(holes[0])]
        for col in extra_holes:
            four_hole_wall[first_wall][col] = 0

        first_wall_unblocks_source = copy.deepcopy(grid)
        first_wall_unblocks_source[first_wall][source_col] = 0

        perpendicular_fragment = copy.deepcopy(grid)
        fragment_row = next(r for r in range(2, len(grid) - 2) if r not in positions)
        perpendicular_fragment[fragment_row][1] = 8

        for name, impostor in (
            ("duplicate_source", duplicate_source),
            ("corner_source", corner_source),
            ("four_hole_wall", four_hole_wall),
            ("first_wall_unblocks_source", first_wall_unblocks_source),
            ("perpendicular_fragment", perpendicular_fragment),
        ):
            with self.subTest(name=name):
                self.assertTrue(MODULE.self_check(impostor))

    def test_negative_recombination_is_oracle_executable_but_distribution_invalid(self):
        grid = MODULE.generate(
            3301,
            19,
            difficulty="hard",
            edge="left",
            grid_h=14,
            grid_w=17,
            n_walls=5,
        )
        _, positions, holes, _ = _profile(grid)
        first_wall = positions[0]
        mutated = copy.deepcopy(grid)
        # Introduce a four-hole wall, a replacement feature absent from every
        # remaining wall (all retain the lawful 1..3-hole profile).
        extras = [r for r in range(1, len(grid) - 1) if r not in holes[0]][: 4 - len(holes[0])]
        for row in extras:
            mutated[row][first_wall] = 0
        self.assertEqual(len(MODULE._wall_profile(mutated, "left")[1][0]), 4)
        self.assertTrue(MODULE.self_check(mutated))
        # The oracle algorithm is intentionally total on this malformed scene;
        # non-crash is not evidence that it is a valid teaching distribution.
        output = MODULE.rule_mirror(mutated)
        self.assertEqual(len(output), len(mutated))
        self.assertEqual(len(output[0]), len(mutated[0]))
        self.assertNotEqual(output, mutated)


if __name__ == "__main__":
    unittest.main()
