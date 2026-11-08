from __future__ import annotations

import hashlib
import json
import random
import unittest
from pathlib import Path

from puzzle_generators import base
from puzzle_generators.per_puzzle.f38ce802fe57 import generator


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
    seeds = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value in generator._SEED_COLORS
    ]
    if not seeds:
        return [row[:] for row in grid]
    seed_row, seed_col, color = seeds[0]
    seen = {(seed_row, seed_col)}
    pending = [(seed_row, seed_col)]
    while pending:
        row, col = pending.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr = row + dr
            nc = col + dc
            if (
                0 <= nr < len(grid)
                and 0 <= nc < len(grid[0])
                and (nr, nc) not in seen
                and grid[nr][nc] == 0
            ):
                seen.add((nr, nc))
                pending.append((nr, nc))
    output = [row[:] for row in grid]
    for row, col in seen:
        if output[row][col] == 0:
            output[row][col] = color
    return output


class F38ce802fe57GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = canonical_row()
        cls.pairs = canonical_pairs()

    def test_all_public_pairs_match_rule_and_complete_profiles(self):
        self.assertEqual(len(self.pairs), 5)
        profile_indexes = set()
        for pair in self.pairs:
            grid = pair["input"]
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(independent_rule(grid), pair["output"])
            self.assertEqual(generator.rule_mirror(grid), pair["output"])
            self.assertEqual(grid, before)
            profile_indexes.add(generator.canonical_profile_index(grid))
        self.assertEqual(profile_indexes, set(range(5)))

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
                self.assertGreaterEqual(matches, 45)
                self.assertLessEqual(matches, 90)
                self.assertEqual(profiles, set(range(5)))
                self.assertGreaterEqual(len(pairs), 595)

    def test_forced_axis_boundaries_are_exact(self):
        for room_count in generator._ROOM_COUNTS:
            grid = generator.generate(
                room_count,
                room_count * 13,
                room_count=room_count,
            )
            self.assertEqual(
                generator.observe_overrides(grid)["room_count"],
                room_count,
            )
        for seed_color in generator._SEED_COLORS:
            grid = generator.generate(
                seed_color,
                seed_color * 17,
                seed_color=seed_color,
            )
            self.assertEqual(
                generator.observe_overrides(grid)["seed_color"],
                seed_color,
            )
        for room_count, seed_color in (
            (3, 2),
            (3, 8),
            (6, 2),
            (6, 8),
        ):
            for band in ("easy", "medium", "hard"):
                grid = generator.generate(
                    room_count * 31,
                    seed_color * 37,
                    difficulty=band,
                    room_count=room_count,
                    seed_color=seed_color,
                )
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(
                    generator.observe_overrides(grid),
                    {
                        "room_count": room_count,
                        "seed_color": seed_color,
                    },
                )
                _coerced, features, errors = generator._scene_analysis(grid)
                self.assertEqual(errors, [])
                self.assertGreater(len(features["residual_walls"]), 0)
                self.assertGreater(features["t_junctions"], 0)

    def test_rule_fills_only_the_seed_connected_room(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(180):
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
                changed = {
                    (row, col)
                    for row in range(len(grid))
                    for col in range(len(grid[0]))
                    if grid[row][col] != output[row][col]
                }
                self.assertEqual(
                    changed,
                    {
                        cell
                        for cell in features["seed_region"]
                        if grid[cell[0]][cell[1]] == 0
                    },
                )
                self.assertTrue(changed)
                self.assertTrue(any(
                    grid[row][col] == output[row][col] == 0
                    for region in features["regions"]
                    if region != features["seed_region"]
                    for row, col in region
                ))

    def test_d4_seed_relocation_color_metamorphism_and_nonprofile(self):
        for index, source in enumerate(generator._PROFILE_GRIDS):
            signatures = set()
            positions = set()
            colors = set()
            for shift in range(80):
                grid = generator._draw_profile(
                    source,
                    random.Random(index * 1000 + shift),
                )
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(generator.canonical_profile_index(grid), index)
                self.assertEqual(
                    generator.rule_mirror(grid),
                    independent_rule(grid),
                )
                signatures.add(generator.canonical_profile_signature(grid))
                _coerced, features, _errors = generator._scene_analysis(grid)
                positions.add(features["seed"][:2])
                colors.add(features["seed_color"])
            self.assertGreaterEqual(len(signatures), 4)
            self.assertGreaterEqual(len(positions), 3)
            self.assertEqual(colors, set(generator._SEED_COLORS))

        hybrid = generator.generate(
            83,
            97,
            room_count=6,
            seed_color=7,
        )
        self.assertEqual(generator.self_check(hybrid), [])
        self.assertIsNone(generator.canonical_profile_index(hybrid))
        transformed_input = [row[:] for row in hybrid]
        transformed_output = independent_rule(hybrid)
        _coerced, features, errors = generator._scene_analysis(hybrid)
        self.assertEqual(errors, [])
        seed_row, seed_col, old_color = features["seed"]
        transformed_input[seed_row][seed_col] = 2
        for row, col in features["seed_region"]:
            if transformed_output[row][col] == old_color:
                transformed_output[row][col] = 2
        self.assertEqual(
            generator.rule_mirror(transformed_input),
            transformed_output,
        )

    def test_removed_controls_and_strict_types(self):
        bad_calls = (
            {"difficulty": "expert"},
            {"bogus": 1},
            {"room_count": "3"},
            {"room_count": 3.0},
            {"room_count": True},
            {"room_count": 2},
            {"room_count": 7},
            {"seed_color": "2"},
            {"seed_color": 2.0},
            {"seed_color": True},
            {"seed_color": 1},
            {"seed_color": 5},
            {"seed_color": 9},
            {"rooms_r": 2},
            {"rooms_c": 3},
            {"room_h": 4},
            {"room_w": 5},
            {"density": "rooms"},
            {"texture": "warm"},
            {"texture": "no_seed"},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **kwargs)

    def test_every_return_path_records_exact_provenance(self):
        profiled = 0
        for band in ("easy", "medium", "hard"):
            for seed in range(240):
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
                for key in generator.AXES:
                    self.assertEqual(captured[-1]._drawn[key], observed[key])
                profiled += generator.is_canonical_profile(grid)
        self.assertGreater(profiled, 45)

        captured = []
        base.set_ctx_observer(captured.append)
        try:
            grid = generator.generate(
                91,
                117,
                difficulty="easy",
                room_count=6,
                seed_color=8,
            )
        finally:
            base.set_ctx_observer(None)
        self.assertEqual(
            captured[-1]._drawn,
            generator.observe_overrides(grid),
        )
        self.assertEqual(
            captured[-1]._override_used,
            {"room_count": 6, "seed_color": 8},
        )

    def test_self_check_rejects_structural_impostors(self):
        valid = generator.generate(
            1,
            2,
            difficulty="hard",
            room_count=5,
            seed_color=4,
        )
        _coerced, features, errors = generator._scene_analysis(valid)
        self.assertEqual(errors, [])
        mutations = []

        broken_border = [row[:] for row in valid]
        broken_border[0][1] = 0
        mutations.append(broken_border)

        missing_seed = [row[:] for row in valid]
        seed_row, seed_col, _seed_color = features["seed"]
        missing_seed[seed_row][seed_col] = 0
        mutations.append(missing_seed)

        duplicate_seed = [row[:] for row in valid]
        other_region = next(
            region
            for region in features["regions"]
            if region != features["seed_region"]
        )
        row, col = next(iter(other_region))
        duplicate_seed[row][col] = 2
        mutations.append(duplicate_seed)

        stray_wall = [row[:] for row in valid]
        row, col = next(
            cell
            for region in features["regions"]
            for cell in region
            if cell != features["seed"][:2]
        )
        stray_wall[row][col] = 5
        mutations.append(stray_wall)

        broken_cut = [row[:] for row in valid]
        row, col = features["residual_walls"][0]
        broken_cut[row][col] = 0
        mutations.append(broken_cut)

        ragged = [row[:] for row in valid]
        ragged[-1] = ragged[-1][:-1]
        mutations.append(ragged)

        invalid_value = [row[:] for row in valid]
        invalid_value[1][1] = 9
        mutations.append(invalid_value)

        for mutation in mutations:
            self.assertTrue(generator.self_check(mutation), mutation)

    def test_bands_cover_profiles_topologies_sizes_and_diversity(self):
        mean_areas = {}
        palette = set()
        room_counts = {}
        for band in ("easy", "medium", "hard"):
            areas = []
            pairs = set()
            profiles = set()
            counts = set()
            max_height = max_width = 0
            for seed in range(600):
                grid = generator.generate(
                    seed,
                    seed * 43 + 11,
                    difficulty=band,
                )
                output = generator.rule_mirror(grid)
                pairs.add((
                    tuple(map(tuple, grid)),
                    tuple(map(tuple, output)),
                ))
                _coerced, features, errors = generator._scene_analysis(grid)
                self.assertEqual(errors, [])
                areas.append(len(grid) * len(grid[0]))
                max_height = max(max_height, len(grid))
                max_width = max(max_width, len(grid[0]))
                palette.add(features["seed_color"])
                counts.add(features["room_count"])
                self.assertGreater(len(features["residual_walls"]), 0)
                self.assertGreater(features["t_junctions"], 0)
                profile = generator.canonical_profile_index(grid)
                if profile is not None:
                    profiles.add(profile)

            mean_areas[band] = sum(areas) / len(areas)
            room_counts[band] = counts
            self.assertGreaterEqual(len(pairs), 595)
            self.assertEqual(profiles, set(range(5)))
            if band == "hard":
                self.assertGreaterEqual(max_height, 28)
                self.assertGreaterEqual(max_width, 28)

        self.assertEqual(palette, set(generator._SEED_COLORS))
        self.assertTrue({3}.issubset(room_counts["easy"]))
        self.assertTrue({3, 4}.issubset(room_counts["medium"]))
        self.assertTrue({4, 5, 6}.issubset(room_counts["hard"]))
        self.assertLess(mean_areas["easy"], mean_areas["medium"])
        self.assertLess(mean_areas["medium"], mean_areas["hard"])

    def test_source_pin_determinism_freshness_and_global_rng(self):
        canonical = self.row["program_solution"]
        normalized = hashlib.sha256(
            " ".join(canonical.split()).encode()
        ).hexdigest()
        self.assertEqual(generator.RULE_HASH, normalized[:12])
        base_row = json.loads(
            (
                ROOT
                / "data/base/solutions/banks/3b7f019624a4"
                / "M45__f38ce802fe57.json"
            ).read_text()
        )
        self.assertEqual(
            base_row["racket_target"]["raw_code"], canonical
        )
        self.assertEqual(
            base_row["racket_target"]["target_code"], canonical
        )

        random.seed(9981)
        state = random.getstate()
        first = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))


if __name__ == "__main__":
    unittest.main()
