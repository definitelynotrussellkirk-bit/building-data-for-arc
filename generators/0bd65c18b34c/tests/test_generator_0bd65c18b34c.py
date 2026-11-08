from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

from solvers.grounded_rules import GROUNDED_RULES


generator = importlib.import_module(
    "puzzle_generators.per_puzzle.0bd65c18b34c.generator"
)
ROOT = Path(__file__).resolve().parents[1]
MODES = ("left", "right", "up", "down")


def canonical_rows():
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == generator.TASK_ID:
                rows.append(row)
    return rows


def all_canonical_pairs():
    pairs = []
    for row in canonical_rows():
        test = row["test"]
        pairs.extend(row["train"])
        pairs.extend([test] if isinstance(test, dict) else test)
    return pairs


def unique_canonical_pairs():
    pairs = []
    seen = set()
    for pair in all_canonical_pairs():
        key = tuple(map(tuple, pair["input"]))
        if key not in seen:
            seen.add(key)
            pairs.append(pair)
    return pairs


def normalized_rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def independent_squares(grid):
    height = len(grid)
    width = len(grid[0])
    return [
        (row, col)
        for row in range(height - 1)
        for col in range(width - 1)
        if all(
            grid[rr][cc] == 2
            for rr in (row, row + 1)
            for cc in (col, col + 1)
        )
    ]


def independent_dot_info(grid, squares, row, col):
    distances = []
    for square_row, square_col in squares:
        row_delta = max(
            0,
            square_row - row,
            row - square_row - 1,
        )
        col_delta = max(
            0,
            square_col - col,
            col - square_col - 1,
        )
        distances.append(max(row_delta, col_delta))
    distance = min(distances)
    nearest = distances.index(distance)
    square_row, square_col = squares[nearest]
    if square_row <= row <= square_row + 1:
        if col < square_col:
            mode = "left"
            target = row, square_col - 1
        else:
            mode = "right"
            target = row, square_col + 2
    elif square_col <= col <= square_col + 1:
        if row < square_row:
            mode = "up"
            target = square_row - 1, col
        else:
            mode = "down"
            target = square_row + 2, col
    else:
        mode = "stay"
        target = row, col
    return {
        "nearest": nearest,
        "distance": distance,
        "ties": sum(value == distance for value in distances),
        "mode": mode,
        "target": target,
    }


def independent_rule(grid):
    squares = independent_squares(grid)
    blues = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    ]
    output = [row[:] for row in grid]
    for row, col in blues:
        output[row][col] = 0
    for row, col in blues:
        info = independent_dot_info(
            grid,
            squares,
            row,
            col,
        )
        target_row, target_col = info["target"]
        output[target_row][target_col] = 1
    return output


def independent_facts(grid):
    squares = independent_squares(grid)
    infos = [
        independent_dot_info(grid, squares, row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    ]
    modes = Counter(info["mode"] for info in infos)
    nearest = sorted(
        Counter(info["nearest"] for info in infos).values()
    )
    signature = (
        tuple(sorted((len(grid), len(grid[0])))),
        len(squares),
        len(infos),
        modes["stay"],
        tuple(sorted(modes[mode] for mode in MODES)),
        tuple(nearest),
        sum(info["ties"] == 2 for info in infos),
    )
    profiles = {
        (
            (30, 30),
            2,
            11,
            4,
            (1, 2, 2, 2),
            (4, 7),
            0,
        ): "large_two",
        (
            (30, 30),
            4,
            14,
            2,
            (3, 3, 3, 3),
            (2, 3, 4, 5),
            2,
        ): "large_four_balanced",
        (
            (10, 13),
            2,
            3,
            1,
            (0, 0, 1, 1),
            (1, 2),
            0,
        ): "compact_two",
        (
            (30, 30),
            4,
            15,
            5,
            (1, 3, 3, 3),
            (2, 4, 4, 5),
            0,
        ): "large_four_stay",
    }
    targets = [info["target"] for info in infos]
    return {
        "profile": profiles.get(signature),
        "squares": squares,
        "infos": infos,
        "modes": modes,
        "targets": targets,
    }


def transform_grid(grid, transform):
    transformed = [row[:] for row in grid]
    if transform >= 4:
        transformed = [
            list(reversed(row)) for row in transformed
        ]
    for _turn in range(transform % 4):
        transformed = [
            list(row) for row in zip(*reversed(transformed))
        ]
    return transformed


class Generator0bd65c18b34cTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = canonical_rows()
        cls.all_pairs = all_canonical_pairs()
        cls.pairs = unique_canonical_pairs()

    def test_all_canonical_rows_pairs_profiles_and_rule(self):
        self.assertEqual(len(self.rows), 2)
        self.assertEqual(len(self.all_pairs), 8)
        self.assertEqual(len(self.pairs), 4)
        profiles = []
        for index, pair in enumerate(self.pairs):
            grid = pair["input"]
            snapshot = [row[:] for row in grid]
            facts = independent_facts(grid)
            profiles.append(facts["profile"])
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(independent_rule(grid), pair["output"])
            self.assertEqual(generator.rule_mirror(grid), pair["output"])
            self.assertEqual(grid, snapshot)
            self.assertEqual(
                generator.canonical_profile_index(grid),
                index,
            )
            self.assertEqual(
                len(facts["targets"]),
                len(set(facts["targets"])),
            )
        self.assertEqual(
            profiles,
            list(generator.SCENE_PROFILES),
        )

    def test_d4_metamorphism_and_tie_order_boundary(self):
        for pair_index in (0, 2, 3):
            pair = self.pairs[pair_index]
            for transform in range(8):
                transformed_input = transform_grid(
                    pair["input"],
                    transform,
                )
                transformed_output = transform_grid(
                    pair["output"],
                    transform,
                )
                self.assertEqual(
                    independent_rule(transformed_input),
                    transformed_output,
                )
                self.assertEqual(
                    generator.rule_mirror(transformed_input),
                    transformed_output,
                )
                self.assertEqual(
                    generator.canonical_profile_index(
                        transformed_input
                    ),
                    pair_index,
                )

        tied_pair = self.pairs[1]
        noncommuting = 0
        for transform in range(8):
            transformed_input = transform_grid(
                tied_pair["input"],
                transform,
            )
            expected = independent_rule(transformed_input)
            self.assertEqual(
                generator.rule_mirror(transformed_input),
                expected,
            )
            noncommuting += expected != transform_grid(
                tied_pair["output"],
                transform,
            )
        self.assertGreater(noncommuting, 0)

    def test_every_exact_profile_axis_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile_index, profile in enumerate(
                generator.SCENE_PROFILES
            ):
                seed = 10_000 + 100 * profile_index + len(band)
                grid = generator.generate(
                    seed,
                    seed * 19 + 3,
                    difficulty=band,
                    scene_profile=profile,
                )
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(
                    generator.observe_overrides(grid),
                    {"scene_profile": profile},
                )
                self.assertEqual(
                    generator.rule_mirror(grid),
                    independent_rule(grid),
                )

    def test_distribution_is_complete_stable_and_diverse(self):
        for start in (0, 50_000):
            for band_index, band in enumerate(
                ("easy", "medium", "hard")
            ):
                profiles = set()
                shapes = set()
                pairs = set()
                for offset in range(120):
                    seed = start + band_index * 10_000 + offset
                    grid = generator.generate(
                        seed,
                        seed * 29 + 7,
                        difficulty=band,
                    )
                    output = independent_rule(grid)
                    facts = independent_facts(grid)
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(generator.rule_mirror(grid), output)
                    profiles.add(facts["profile"])
                    shapes.add((len(grid), len(grid[0])))
                    pairs.add((
                        tuple(map(tuple, grid)),
                        tuple(map(tuple, output)),
                    ))
                self.assertEqual(
                    profiles,
                    set(generator.SCENE_PROFILES),
                )
                self.assertTrue((30, 30) in shapes)
                self.assertTrue(
                    (10, 13) in shapes or (13, 10) in shapes
                )
                self.assertGreaterEqual(len(pairs), 119)

    def test_structural_and_semantic_mutations_are_rejected(self):
        compact = [row[:] for row in self.pairs[2]["input"]]
        broken_square = [row[:] for row in compact]
        broken_square[3][1] = 0
        too_many_red = [row[:] for row in compact]
        too_many_red[2][1] = 2
        missing_dot = [row[:] for row in compact]
        missing_dot[8][4] = 0
        invalid_color = [row[:] for row in compact]
        invalid_color[0][0] = 9
        for mutation in (
            broken_square,
            too_many_red,
            missing_dot,
            invalid_color,
            [],
            [[0] * 13 for _row in range(9)],
            [[0] * 12 for _row in range(10)],
            [[0] * 13 for _row in range(11)],
        ):
            self.assertTrue(generator.self_check(mutation), mutation)

    def test_lawful_unpublished_recombination_is_calibrated_out(self):
        candidate = [row[:] for row in self.pairs[2]["input"]]
        candidate[0][0] = 1
        self.assertEqual(
            generator.self_check(candidate),
            [
                "returned scene must match a complete published "
                "movement profile"
            ],
        )
        self.assertEqual(
            generator.rule_mirror(candidate),
            independent_rule(candidate),
        )

    def test_source_sync_hash_determinism_freshness_and_global_rng(self):
        sources = {row["program_solution"] for row in self.rows}
        self.assertEqual(len(sources), 1)
        source = next(iter(sources))
        for relative_path in (
            "data/base/solutions/training/"
            "e1d2900e__0bd65c18b34c.json",
            "data/base/solutions/augmented/"
            "e1d2900e__2beaebe8e3d0.json",
        ):
            target = json.loads(
                (ROOT / relative_path).read_text()
            )["racket_target"]
            self.assertEqual(target["raw_code"], source)
            self.assertEqual(target["target_code"], source)
        self.assertEqual(
            normalized_rule_hash(
                GROUNDED_RULES[generator.TASK_ID]
            ),
            normalized_rule_hash(source),
        )
        self.assertEqual(
            generator.RULE_HASH,
            normalized_rule_hash(source)[:12],
        )

        state = random.getstate()
        first = generator.generate(37, 43, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        snapshot = [row[:] for row in first]
        generator.generate(91, 97, difficulty="easy")
        self.assertEqual(first, snapshot)
        again = generator.generate(37, 43, difficulty="hard")
        self.assertEqual(first, again)
        self.assertIsNot(first, again)
        self.assertTrue(all(
            old_row is not new_row
            for old_row, new_row in zip(first, again)
        ))
        first[0][0] = 1 if first[0][0] != 1 else 0
        self.assertEqual(
            generator.generate(37, 43, difficulty="hard"),
            again,
        )


if __name__ == "__main__":
    unittest.main()
