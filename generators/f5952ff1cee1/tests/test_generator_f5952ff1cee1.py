from __future__ import annotations

import hashlib
import json
import random
import unittest
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.f5952ff1cee1 import generator


ROOT = Path(__file__).resolve().parents[1]


def canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == generator.TASK_ID:
                return row
    raise KeyError(generator.TASK_ID)


def canonical_pairs():
    row = canonical_row()
    test = row["test"]
    return list(row["train"]) + (
        [test] if isinstance(test, dict) else list(test)
    )


def coerce(grid):
    return [
        [int(value) for value in row]
        if isinstance(row, str)
        else list(row)
        for row in grid
    ]


def independent_rule(grid):
    grid = coerce(grid)
    height = len(grid)
    width = len(grid[0])
    source = next(
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    )
    row, col = source
    if row == 0:
        dr, dc = 1, 0
    elif row == height - 1:
        dr, dc = -1, 0
    elif col == 0:
        dr, dc = 0, 1
    elif col == width - 1:
        dr, dc = 0, -1
    else:
        dr, dc = 0, 1
    output = [[0] * width for _ in range(height)]
    for _step in range(500):
        next_row = row + dr
        next_col = col + dc
        if not (
            0 <= next_row < height and 0 <= next_col < width
        ):
            break
        value = grid[next_row][next_col]
        if value == 5:
            break
        row, col = next_row, next_col
        output[row][col] = 8
        if value == 7:
            dr, dc = -dc, -dr
        elif value == 6:
            dr, dc = dc, dr
    return output


def normalized_rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


class F5952ff1cee1GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = canonical_row()
        cls.pairs = canonical_pairs()

    def test_all_public_pairs_match_rule_and_complete_profiles(self):
        self.assertEqual(len(self.pairs), 5)
        profiles = set()
        turn_counts = set()
        edges = set()
        for pair in self.pairs:
            grid = pair["input"]
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(independent_rule(grid), pair["output"])
            self.assertEqual(generator.rule_mirror(grid), pair["output"])
            self.assertEqual(grid, before)
            profiles.add(generator.canonical_profile_index(grid))
            observed = generator.observe_overrides(grid)
            turn_counts.add(observed["turn_count"])
            edges.add(observed["edge"])
        self.assertEqual(profiles, set(range(5)))
        self.assertEqual(turn_counts, {1, 2, 3})
        self.assertEqual(edges, set(generator._EDGES))

    def test_complete_profile_prior_is_stable_and_diverse(self):
        for start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                matches = 0
                profiles = set()
                pairs = set()
                for offset in range(600):
                    seed = start + offset
                    grid = generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                    output = independent_rule(grid)
                    pairs.add((
                        tuple(map(tuple, grid)),
                        tuple(map(tuple, output)),
                    ))
                    profile = generator.canonical_profile_index(grid)
                    if profile is not None:
                        matches += 1
                        profiles.add(profile)
                self.assertGreaterEqual(matches, 40)
                self.assertLessEqual(matches, 85)
                self.assertEqual(profiles, set(range(5)))
                self.assertGreaterEqual(len(pairs), 590)

    def test_every_forced_axis_value_and_boundary_cross_is_exact(self):
        values = {
            "edge": generator._EDGES,
            "turn_count": (1, 2, 3),
            "termination": generator._TERMINATIONS,
        }
        for label, domain in values.items():
            for value in domain:
                grid = generator.generate(
                    len(str(value)),
                    len(str(value)) * 19 + 3,
                    **{label: value},
                )
                self.assertEqual(
                    generator.observe_overrides(grid)[label],
                    value,
                )

        for edge in generator._EDGES:
            for turn_count in (1, 3):
                for termination in generator._TERMINATIONS:
                    grid = generator.generate(
                        len(edge) * 31 + turn_count,
                        len(termination) * 37 + turn_count,
                        difficulty="hard",
                        edge=edge,
                        turn_count=turn_count,
                        termination=termination,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(
                        generator.observe_overrides(grid),
                        {
                            "edge": edge,
                            "turn_count": turn_count,
                            "termination": termination,
                        },
                    )

    def test_every_default_ray_turns_and_all_semantic_branches_appear(self):
        turns = set()
        terminations = set()
        decoy_counts = set()
        edges = set()
        for band in ("easy", "medium", "hard"):
            for seed in range(240):
                grid = generator.generate(
                    seed,
                    seed * 29 + 7,
                    difficulty=band,
                )
                before = [row[:] for row in grid]
                output = generator.rule_mirror(grid)
                self.assertEqual(output, independent_rule(grid))
                self.assertEqual(grid, before)
                _coerced, features, errors = generator._scene_analysis(grid)
                self.assertEqual(errors, [])
                self.assertGreaterEqual(features["turn_count"], 1)
                self.assertEqual(
                    {
                        (row, col)
                        for row, values in enumerate(output)
                        for col, value in enumerate(values)
                        if value == 8
                    },
                    set(features["path"]),
                )
                turns.add(features["turn_count"])
                terminations.add(features["termination"])
                decoy_counts.add(features["decoy_count"])
                edges.add(features["edge"])
        self.assertEqual(turns, {1, 2, 3})
        self.assertEqual(terminations, set(generator._TERMINATIONS))
        self.assertEqual(decoy_counts, {0, 1, 2, 3})
        self.assertEqual(edges, set(generator._EDGES))

    def test_d4_transforms_preserve_profiles_and_oracle(self):
        for index, source in enumerate(generator._PROFILE_GRIDS):
            variants = generator._d4_scenes(source)
            self.assertGreaterEqual(len({
                tuple(map(tuple, variant)) for variant in variants
            }), 4)
            for variant in variants:
                self.assertEqual(generator.self_check(variant), [])
                self.assertEqual(
                    generator.canonical_profile_index(variant),
                    index,
                )
                self.assertEqual(
                    generator.rule_mirror(variant),
                    independent_rule(variant),
                )

        hybrid = generator._construct_route(
            20,
            8,
            "left",
            3,
            "stopper",
            3,
            random.Random(83),
        )
        self.assertEqual(generator.self_check(hybrid), [])
        self.assertIsNone(generator.canonical_profile_index(hybrid))

    def test_off_route_decoys_are_true_nuisance_cells(self):
        grid = generator._construct_route(
            14,
            15,
            "right",
            3,
            "boundary",
            3,
            random.Random(181),
        )
        _coerced, features, errors = generator._scene_analysis(grid)
        self.assertEqual(errors, [])
        original_output = independent_rule(grid)
        recolored = [row[:] for row in grid]
        for row, col, value in features["decoys"]:
            recolored[row][col] = {5: 6, 6: 7, 7: 5}[value]
        self.assertEqual(generator.self_check(recolored), [])
        self.assertEqual(independent_rule(recolored), original_output)

        stopper_grid = generator.generate(
            229,
            257,
            termination="stopper",
            turn_count=2,
        )
        _grid, stopper_features, stopper_errors = (
            generator._scene_analysis(stopper_grid)
        )
        self.assertEqual(stopper_errors, [])
        self.assertIsNotNone(stopper_features["stopper"])
        stop_row, stop_col = stopper_features["stopper"]
        self.assertEqual(
            independent_rule(stopper_grid)[stop_row][stop_col],
            0,
        )

    def test_removed_controls_and_strict_types(self):
        bad_calls = (
            {"difficulty": "expert"},
            {"bogus": 1},
            {"grid_h": "8"},
            {"grid_h": 8.0},
            {"grid_h": True},
            {"grid_h": 7},
            {"grid_h": 21},
            {"grid_w": 7},
            {"grid_w": 21},
            {"edge": "diagonal"},
            {"edge": 1},
            {"turn_count": 0},
            {"turn_count": 4},
            {"termination": "fuel"},
            {"decoy_count": -1},
            {"decoy_count": 4},
            {"n_mirrors": 2},
            {"n_stoppers": 1},
            {"n_distinct_colors": 5},
            {"density": "sparse"},
            {"texture": "default"},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **kwargs)

    def test_every_return_path_records_exact_provenance(self):
        profiles = 0
        for band in ("easy", "medium", "hard"):
            for seed in range(200):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = generator.generate(
                        seed,
                        seed * 37 + 5,
                        difficulty=band,
                    )
                finally:
                    base.set_ctx_observer(None)
                observed = generator.observe_overrides(grid)
                for label in generator.AXES:
                    self.assertEqual(
                        captured[-1]._drawn[label],
                        observed[label],
                    )
                profiles += generator.is_canonical_profile(grid)
        self.assertGreaterEqual(profiles, 35)

        overrides = {
            "edge": "bottom",
            "turn_count": 3,
            "termination": "stopper",
        }
        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = generator.generate(91, 117, **overrides)
        finally:
            base.set_ctx_observer(None)
        self.assertEqual(captured[-1]._drawn, overrides)
        self.assertEqual(captured[-1]._override_used, overrides)
        self.assertEqual(generator.observe_overrides(grid), overrides)

    def test_self_check_rejects_structural_impostors(self):
        valid = generator._construct_route(
            12,
            13,
            "top",
            1,
            "boundary",
            3,
            random.Random(1),
        )
        _coerced, features, errors = generator._scene_analysis(valid)
        self.assertEqual(errors, [])
        mutations = []

        missing_source = [row[:] for row in valid]
        source_row, source_col = features["source"]
        missing_source[source_row][source_col] = 0
        mutations.append(missing_source)

        duplicate_source = [row[:] for row in valid]
        duplicate_source[-1][1] = 2
        mutations.append(duplicate_source)

        corner_source = [row[:] for row in valid]
        corner_source[source_row][source_col] = 0
        corner_source[0][0] = 2
        mutations.append(corner_source)

        no_active_mirror = [row[:] for row in valid]
        mirror_row, mirror_col, _color = features["active_mirrors"][0]
        no_active_mirror[mirror_row][mirror_col] = 0
        mutations.append(no_active_mirror)

        too_many_decoys = [row[:] for row in valid]
        occupied = {
            (row, col)
            for row, values in enumerate(valid)
            for col, value in enumerate(values)
            if value != 0
        }
        occupied.update(features["path"])
        extra = next(
            (row, col)
            for row in range(len(valid))
            for col in range(len(valid[0]))
            if (row, col) not in occupied
        )
        too_many_decoys[extra[0]][extra[1]] = 5
        mutations.append(too_many_decoys)

        foreign_color = [row[:] for row in valid]
        foreign_color[1][1] = 9
        mutations.append(foreign_color)

        mutations.append([row[:] for row in valid[:-5]])
        mutations.append([row[:] for row in valid] + [[0] * len(valid[0])] * 9)
        ragged = [row[:] for row in valid]
        ragged[0].pop()
        mutations.append(ragged)

        for mutation in mutations:
            self.assertTrue(generator.self_check(mutation))
        self.assertTrue(generator.self_check([]))
        self.assertTrue(generator.self_check([[0] * 8 for _ in range(8)]))

    def test_source_sync_determinism_freshness_and_global_rng(self):
        source = self.row["program_solution"]
        base_row = json.loads((
            ROOT
            / "data/base/solutions/banks/53ccebf2a36f"
            / "H124__f5952ff1cee1.json"
        ).read_text())
        target = base_row["racket_target"]
        self.assertEqual(target["raw_code"], source)
        self.assertEqual(target["target_code"], source)
        self.assertEqual(
            generator.RULE_HASH,
            normalized_rule_hash(source)[:12],
        )

        kwargs = {
            "difficulty": "hard",
            "edge": "left",
            "turn_count": 3,
            "termination": "stopper",
        }
        first = generator.generate(17, 23, **kwargs)
        second = generator.generate(17, 23, **kwargs)
        self.assertEqual(first, second)
        first[0][0] = 9
        third = generator.generate(17, 23, **kwargs)
        self.assertNotEqual(first, third)
        self.assertEqual(second, third)

        random.seed(777)
        expected = [random.random() for _ in range(6)]
        random.seed(777)
        generator.generate(31, 37, difficulty="medium")
        actual = [random.random() for _ in range(6)]
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
