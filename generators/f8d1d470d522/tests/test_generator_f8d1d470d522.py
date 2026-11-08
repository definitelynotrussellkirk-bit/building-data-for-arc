from __future__ import annotations

import hashlib
import json
import random
import unittest
from collections import deque
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.f8d1d470d522 import generator
from reviewer_support import canonical_path, find_root
from review_diagnostics import search_lesson


ROOT = find_root(__file__)
CARDINAL = ((0, 1), (1, 0), (0, -1), (-1, 0))


def canonical_rows():
    rows = []
    with canonical_path(ROOT).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == generator.TASK_ID:
                rows.append(row)
    return rows


def data_path(relative):
    """Resolve a retained data file in either source or portable runtime."""
    for prefix in ("shared/data", "data"):
        candidate = ROOT / prefix / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(relative)


def row_pairs(row):
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


def independent_paths(grid, *, ignore_sevens=False):
    """Enumerate shortest paths for these deliberately small route graphs."""
    grid = coerce(grid)
    height = len(grid)
    width = len(grid[0])
    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 9
    ]
    if len(markers) != 2:
        return []
    start, goal = markers

    def allowed(row, col):
        if grid[row][col] == 9:
            return True
        if grid[row][col] != 8:
            return False
        if ignore_sevens:
            return True
        return not any(
            0 <= row + dr < height
            and 0 <= col + dc < width
            and grid[row + dr][col + dc] == 7
            for dr, dc in CARDINAL
        )

    distance = {start: 0}
    queue = deque((start,))
    while queue:
        row, col = queue.popleft()
        for dr, dc in CARDINAL:
            neighbor = row + dr, col + dc
            if (
                0 <= neighbor[0] < height
                and 0 <= neighbor[1] < width
                and allowed(*neighbor)
                and neighbor not in distance
            ):
                distance[neighbor] = distance[(row, col)] + 1
                queue.append(neighbor)
    if goal not in distance:
        return []

    paths = []

    def visit(cell, path):
        if cell == goal:
            paths.append(tuple(path))
            return
        row, col = cell
        for dr, dc in CARDINAL:
            neighbor = row + dr, col + dc
            if distance.get(neighbor) == distance[cell] + 1:
                visit(neighbor, path + [neighbor])

    visit(start, [start])
    return paths


def turns(path):
    directions = [
        (next_row - row, next_col - col)
        for (row, col), (next_row, next_col)
        in zip(path, path[1:])
    ]
    return sum(
        left != right
        for left, right in zip(directions, directions[1:])
    )


def independent_facts(grid, *, ignore_sevens=False):
    paths = independent_paths(grid, ignore_sevens=ignore_sevens)
    if not paths:
        return None
    turn_counts = [turns(path) for path in paths]
    minimum_turns = min(turn_counts)
    optimal = [
        path
        for path, count in zip(paths, turn_counts)
        if count == minimum_turns
    ]
    return {
        "paths": paths,
        "shortest_path_count": len(paths),
        "turn_counts": tuple(turn_counts),
        "fewest_turns": minimum_turns,
        "optimal": tuple(optimal),
    }


def independent_rule(grid):
    grid = coerce(grid)
    facts = independent_facts(grid)
    if facts is None or len(facts["optimal"]) != 1:
        raise ValueError("scene does not have one optimal route")
    output = [row[:] for row in grid]
    for row, col in facts["optimal"][0]:
        output[row][col] = 9
    return output


def bottommost_shortest_rule(grid):
    """Plausible positional shortcut: maximize row-sum, ignore turn count."""
    grid = coerce(grid)
    paths = independent_paths(grid)
    if not paths:
        raise ValueError("scene has no legal route")
    path = min(
        paths,
        key=lambda candidate: (
            -sum(row for row, _col in candidate),
            candidate,
        ),
    )
    output = [row[:] for row in grid]
    for row, col in path:
        output[row][col] = 9
    return output


def profile_of(grid):
    return (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )


def pinned_profile_seed(task_id, band, index):
    digest = hashlib.sha256(
        f"profile-floor:v1:{task_id}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def normalized_rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


class F8d1d470d522GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = canonical_rows()
        cls.all_pairs = [
            pair for row in cls.rows for pair in row_pairs(row)
        ]
        cls.unique_pairs = {}
        for pair in cls.all_pairs:
            cls.unique_pairs.setdefault(
                tuple(map(tuple, pair["input"])),
                pair,
            )

    def test_every_canonical_pair_and_complete_profiles(self):
        self.assertEqual(len(self.rows), 2)
        self.assertEqual(
            {row["source"] for row in self.rows},
            {"training", "augmented"},
        )
        self.assertEqual(len(self.all_pairs), 8)
        self.assertEqual(len(self.unique_pairs), 4)
        profiles = set()
        modes = set()
        for pair in self.all_pairs:
            grid = pair["input"]
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(independent_rule(grid), pair["output"])
            self.assertEqual(generator.rule_mirror(grid), pair["output"])
            self.assertEqual(grid, before)
            profile = generator.canonical_profile_index(grid)
            self.assertIsNotNone(profile)
            profiles.add(profile)
            facts = independent_facts(grid)
            mode = (
                "unique_shortest"
                if facts["shortest_path_count"] == 1
                else "fewest_turns"
            )
            modes.add(mode)
            self.assertEqual(
                generator.observe_overrides(grid)["selection_mode"],
                mode,
            )
            self.assertEqual(len(facts["optimal"]), 1)
        self.assertEqual(profiles, set(range(4)))
        self.assertEqual(modes, set(generator._SELECTION_MODES))

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
                self.assertGreaterEqual(matches, 230)
                self.assertLessEqual(matches, 250)
                self.assertEqual(profiles, set(range(4)))
                self.assertGreaterEqual(len(pairs), 400)

    def test_pinned_profile_floor_anchors_every_band(self):
        canonical_profiles = {
            profile_of(pair["input"])
            for pair in self.all_pairs
        }
        heights = [height for height, _width, _palette in canonical_profiles]
        widths = [width for _height, width, _palette in canonical_profiles]
        palettes = [palette for _height, _width, palette in canonical_profiles]
        total_exact = 0
        total_envelope = 0
        for band in ("easy", "medium", "hard"):
            band_exact = 0
            for index in range(20):
                seed = pinned_profile_seed(generator.TASK_ID, band, index)
                sample_index = seed % 7919 + index
                grid = generator.generate(
                    seed,
                    sample_index,
                    difficulty=band,
                )
                profile = profile_of(grid)
                band_exact += profile in canonical_profiles
                total_envelope += (
                    min(heights) <= profile[0] <= max(heights)
                    and min(widths) <= profile[1] <= max(widths)
                    and min(palettes) <= profile[2] <= max(palettes)
                )
            self.assertGreaterEqual(band_exact, 1, band)
            total_exact += band_exact
        self.assertGreaterEqual(total_exact, 3)
        self.assertGreaterEqual(total_envelope, 15)

    def test_every_forced_axis_value_is_exact(self):
        for index, mode in enumerate(generator._SELECTION_MODES):
            for seed in range(60):
                grid = generator.generate(
                    seed + index * 1_000,
                    seed * 19 + 3,
                    difficulty=("easy", "medium", "hard")[seed % 3],
                    selection_mode=mode,
                )
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(
                    generator.observe_overrides(grid),
                    {"selection_mode": mode},
                )
                self.assertIsNone(
                    generator.canonical_profile_index(grid)
                )

    def test_default_lessons_cover_both_real_decisions(self):
        modes = set()
        blocked_counts = set()
        unused_counts = set()
        for band in ("easy", "medium", "hard"):
            band_modes = set()
            for seed in range(240):
                grid = generator.generate(
                    seed,
                    seed * 29 + 7,
                    difficulty=band,
                )
                before = [row[:] for row in grid]
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(
                    generator.rule_mirror(grid),
                    independent_rule(grid),
                )
                self.assertEqual(grid, before)
                _coerced, features, errors = (
                    generator._scene_analysis(grid)
                )
                self.assertEqual(errors, [])
                modes.add(features["selection_mode"])
                band_modes.add(features["selection_mode"])
                blocked_counts.add(features["blocked_count"])
                unused_counts.add(features["unused_count"])
                self.assertGreater(features["blocked_count"], 0)
                self.assertGreater(features["unused_count"], 0)
                if not generator.is_canonical_profile(grid):
                    self.assertTrue(features["obstacle_causal"])
            self.assertEqual(
                band_modes,
                set(generator._SELECTION_MODES),
            )
        self.assertEqual(modes, set(generator._SELECTION_MODES))
        self.assertGreaterEqual(len(blocked_counts), 4)
        self.assertGreaterEqual(len(unused_counts), 5)

    def test_profiles_and_general_scenes_are_d4_padding_equivariant(self):
        for index, source in enumerate(generator._PROFILE_GRIDS):
            for transform, variant in enumerate(
                generator._d4_variants(source)
            ):
                self.assertEqual(generator.self_check(variant), [])
                self.assertEqual(
                    generator.canonical_profile_index(variant),
                    index,
                )
                self.assertEqual(
                    generator.rule_mirror(variant),
                    independent_rule(variant),
                )
                padded = (
                    [[0] * (len(variant[0]) + 3)]
                    + [[0] + row[:] + [0, 0] for row in variant]
                    + [[0] * (len(variant[0]) + 3)] * 2
                )
                self.assertEqual(generator.self_check(padded), [])
                self.assertEqual(
                    generator.canonical_profile_index(padded),
                    index,
                )
                self.assertEqual(
                    generator.rule_mirror(padded),
                    independent_rule(padded),
                    msg=f"profile={index}, transform={transform}",
                )

        source = generator.generate(
            83,
            97,
            selection_mode="fewest_turns",
        )
        for variant in generator._d4_variants(source):
            self.assertEqual(generator.self_check(variant), [])
            self.assertEqual(
                generator.rule_mirror(variant),
                independent_rule(variant),
            )

    def test_obstacles_are_causal_in_every_general_lesson(self):
        for mode in generator._SELECTION_MODES:
            for seed in range(100):
                grid = generator.generate(
                    seed,
                    seed * 31 + 11,
                    selection_mode=mode,
                )
                blocked = independent_facts(grid)
                relaxed = independent_facts(
                    grid,
                    ignore_sevens=True,
                )
                self.assertIsNotNone(blocked)
                self.assertIsNotNone(relaxed)
                self.assertEqual(len(blocked["optimal"]), 1)
                self.assertEqual(len(relaxed["optimal"]), 1)
                self.assertNotEqual(
                    blocked["optimal"][0],
                    relaxed["optimal"][0],
                )

    def test_fewest_turn_lessons_have_a_real_tie_to_break(self):
        for seed in range(100):
            grid = generator.generate(
                seed,
                seed * 37 + 13,
                selection_mode="fewest_turns",
            )
            facts = independent_facts(grid)
            self.assertGreaterEqual(facts["shortest_path_count"], 2)
            self.assertEqual(len(facts["optimal"]), 1)
            self.assertGreater(
                max(facts["turn_counts"]),
                facts["fewest_turns"],
            )

    def test_removed_controls_and_strict_types(self):
        bad_calls = (
            {"difficulty": "expert"},
            {"bogus": 1},
            {"selection_mode": 1},
            {"selection_mode": True},
            {"selection_mode": "corridor"},
            {"grid_h": 10},
            {"grid_w": 10},
            {"path_len": 8},
            {"n_obstacles": 2},
            {"palette_size": 4},
            {"position_bias": "corridor"},
            {"texture": "no_path"},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **kwargs)

        for seed in (True, 1.5, "1", None):
            with self.subTest(seed=seed):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(seed, 0)
        for sample_index in (True, 1.5, "1", None, -1):
            with self.subTest(sample_index=sample_index):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, sample_index)

    def test_semantic_contract_names_and_refutes_plausible_rivals(self):
        expected_rivals = {
            "ignore_obstacles",
            "most_turns_shortest",
            "bottommost_shortest",
        }
        self.assertEqual(
            set(generator.SEMANTIC_RIVALS),
            expected_rivals,
        )
        self.assertEqual(
            set(generator.LESSON_COMPETITORS),
            expected_rivals,
        )
        self.assertEqual(
            set(generator.CANONICAL_SHORTCUTS),
            {"bottommost_shortest"},
        )
        for pair in self.all_pairs:
            self.assertEqual(generator.strict_canonical_like(pair["input"]), [])
            self.assertEqual(
                bottommost_shortest_rule(pair["input"]),
                pair["output"],
            )
            self.assertEqual(
                generator.CANONICAL_SHORTCUTS["bottommost_shortest"](
                    pair["input"]
                ),
                pair["output"],
            )

        for band_index, band in enumerate(("easy", "medium", "hard")):
            shortcut_counterexamples = 0
            for seed in range(120):
                grid = generator.generate(
                    seed + band_index * 10_000,
                    seed * 43 + 17,
                    difficulty=band,
                )
                intended = generator.rule_mirror(grid)
                shortcut_counterexamples += (
                    generator.CANONICAL_SHORTCUTS[
                        "bottommost_shortest"
                    ](grid)
                    != intended
                )
            self.assertGreater(shortcut_counterexamples, 0, band)

        for seed in range(20):
            tied = generator.generate(
                seed,
                seed * 47 + 19,
                selection_mode="fewest_turns",
            )
            self.assertNotEqual(
                generator.SEMANTIC_RIVALS["most_turns_shortest"](tied),
                generator.rule_mirror(tied),
            )
            causal = generator.generate(
                seed,
                seed * 53 + 23,
                selection_mode="unique_shortest",
            )
            self.assertNotEqual(
                generator.SEMANTIC_RIVALS["ignore_obstacles"](causal),
                generator.rule_mirror(causal),
            )

    def test_five_demo_schedule_survives_every_query_rotation(self):
        self.assertEqual(generator.EXAMPLES_NEEDED, 5)
        self.assertEqual(generator.LESSON_SCHEDULE_PERIOD, 5)
        self.assertEqual(
            set(generator.SCHEDULE_PROFILES),
            {
                "semantic_anchor_a",
                "canonical_profile_a",
                "semantic_anchor_b",
                "canonical_profile_b",
                "general",
            },
        )
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for start in range(5):
                pairs = []
                seed = 700 + band_index * 100 + start
                for offset in range(6):
                    sample_index = start + offset
                    grid = generator.generate(
                        seed,
                        sample_index,
                        difficulty=band,
                    )
                    pairs.append({
                        "input": grid,
                        "output": generator.rule_mirror(grid),
                    })
                for query_index in range(6):
                    query = pairs[query_index]
                    demos = [
                        pair
                        for index, pair in enumerate(pairs)
                        if index != query_index
                    ]
                    with self.subTest(
                        band=band,
                        start=start,
                        query_index=query_index,
                    ):
                        self.assertEqual(
                            generator.lesson_identifiable(demos, query),
                            [],
                        )
                        for name, rival in (
                            generator.LESSON_COMPETITORS.items()
                        ):
                            self.assertTrue(
                                any(
                                    rival(pair["input"]) != pair["output"]
                                    for pair in demos
                                ),
                                name,
                            )

    def test_schedule_refutes_shared_generic_spatial_mutations_under_rotation(self):
        # These exact replays were retained by the shared semantic gate when a
        # single held-out pair made a measured spatial-attribution mutation
        # ambiguous.  Every query rotation must now leave at least one public
        # demonstration that refutes every searched generic candidate.
        replays = (
            ("easy", 15234900522558, 0),
            ("medium", 86337568925178, 22),
        )
        for band, seed, start in replays:
            pairs = []
            for offset in range(generator.EXAMPLES_NEEDED + 1):
                grid = generator.generate(
                    seed,
                    start + offset,
                    difficulty=band,
                )
                pairs.append({
                    "input": grid,
                    "output": generator.rule_mirror(grid),
                })
            for query_index, query in enumerate(pairs):
                instance = {
                    "train": [
                        pair
                        for index, pair in enumerate(pairs)
                        if index != query_index
                    ],
                    "test": [query],
                }
                report = search_lesson(generator, instance)
                with self.subTest(
                    band=band,
                    seed=seed,
                    start=start,
                    query_index=query_index,
                ):
                    self.assertFalse(
                        report["ambiguous"],
                        {
                            name: row
                            for name, row in report["candidates"].items()
                            if row.get("status") == "ambiguous"
                        },
                    )

    def test_every_return_path_records_exact_provenance(self):
        profiles = 0
        for band in ("easy", "medium", "hard"):
            for seed in range(200):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = generator.generate(
                        seed,
                        seed * 41 + 5,
                        difficulty=band,
                    )
                finally:
                    base.set_ctx_observer(None)
                observed = generator.observe_overrides(grid)
                self.assertEqual(
                    captured[-1].recorded_draws()["selection_mode"],
                    observed["selection_mode"],
                )
                profiles += generator.is_canonical_profile(grid)
        self.assertGreaterEqual(profiles, 45)

        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = generator.generate(
                91,
                117,
                selection_mode="fewest_turns",
            )
        finally:
            base.set_ctx_observer(None)
        expected = {"selection_mode": "fewest_turns"}
        self.assertEqual(captured[-1].recorded_draws(), expected)
        self.assertEqual(captured[-1].overrides_used(), expected)
        self.assertEqual(generator.observe_overrides(grid), expected)

    def test_self_check_rejects_structural_impostors(self):
        valid = generator.generate(
            1,
            2,
            selection_mode="unique_shortest",
        )
        mutations = []

        no_markers = [
            [8 if value == 9 else value for value in row]
            for row in valid
        ]
        mutations.append(no_markers)

        one_marker = [row[:] for row in valid]
        marker = next(
            (row, col)
            for row in range(len(one_marker))
            for col in range(len(one_marker[0]))
            if one_marker[row][col] == 9
        )
        one_marker[marker[0]][marker[1]] = 8
        mutations.append(one_marker)

        three_markers = [row[:] for row in valid]
        extra = next(
            (row, col)
            for row in range(len(three_markers))
            for col in range(len(three_markers[0]))
            if three_markers[row][col] == 8
        )
        three_markers[extra[0]][extra[1]] = 9
        mutations.append(three_markers)

        no_obstacle = [
            [0 if value == 7 else value for value in row]
            for row in valid
        ]
        mutations.append(no_obstacle)

        too_many_obstacles = [row[:] for row in valid]
        zeros = [
            (row, col)
            for row in range(len(valid))
            for col in range(len(valid[0]))
            if valid[row][col] == 0
        ]
        for row, col in zeros[:3]:
            too_many_obstacles[row][col] = 7
        mutations.append(too_many_obstacles)

        foreign_color = [row[:] for row in valid]
        foreign_color[0][0] = 10
        mutations.append(foreign_color)

        too_sparse = [[0] * 9 for _row in range(7)]
        too_sparse[3][0] = 9
        too_sparse[3][8] = 9
        too_sparse[2][4] = 7
        for col in range(9):
            too_sparse[3][col] = 8
        too_sparse[3][0] = too_sparse[3][8] = 9
        mutations.append(too_sparse)

        disconnected = [[0] * 9 for _row in range(7)]
        disconnected[1][1] = 9
        disconnected[5][7] = 9
        disconnected[3][4] = 7
        for row in range(1, 6):
            for col in range(1, 8):
                if (row + col) % 2 == 0:
                    disconnected[row][col] = 8
        disconnected[1][1] = disconnected[5][7] = 9
        mutations.append(disconnected)

        ragged = [row[:] for row in valid]
        ragged[0].pop()
        mutations.append(ragged)
        mutations.append([])
        mutations.append([[0] * 4 for _row in range(4)])
        mutations.append([[0] * 26 for _row in range(26)])

        for mutation in mutations:
            self.assertTrue(generator.self_check(mutation))

        ambiguous = None
        obstacles = [
            (row, col)
            for row in range(len(valid))
            for col in range(len(valid[0]))
            if valid[row][col] == 7
        ]
        for obstacle in obstacles:
            candidate = [row[:] for row in valid]
            candidate[obstacle[0]][obstacle[1]] = 0
            facts = independent_facts(candidate)
            if facts and len(facts["optimal"]) > 1:
                ambiguous = candidate
                break
        self.assertIsNotNone(ambiguous)
        self.assertTrue(generator.self_check(ambiguous))

    def test_source_sync_determinism_freshness_and_global_rng(self):
        sources = {row["program_solution"] for row in self.rows}
        self.assertEqual(len(sources), 1)
        source = sources.pop()
        for relative in (
            "base/solutions/training/"
            "cc9053aa__f8d1d470d522.json",
            "base/solutions/augmented/"
            "cc9053aa__5d750b933294.json",
        ):
            base_row = json.loads(data_path(relative).read_text())
            target = base_row["racket_target"]
            self.assertTrue(target["raw_code"].strip())
            self.assertEqual(target["target_code"], source)
        self.assertEqual(
            generator.RULE_HASH,
            normalized_rule_hash(source)[:12],
        )

        kwargs = {
            "difficulty": "hard",
            "selection_mode": "fewest_turns",
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
