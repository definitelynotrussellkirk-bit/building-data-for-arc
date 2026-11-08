from __future__ import annotations

import hashlib
import importlib
import json
import random
import unittest
from collections import Counter, defaultdict
from pathlib import Path

from solvers.grounded_rules import GROUNDED_RULES


generator = importlib.import_module(
    "puzzle_generators.per_puzzle.54628ce9692d.generator"
)

ROOT = Path(__file__).resolve().parents[1]
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
KING = (
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
)


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


def normalized_rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def components8(grid, background):
    seen = set()
    components = []
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == background or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            component = []
            while stack:
                current = stack.pop()
                component.append(current)
                for delta_row, delta_col in KING:
                    neighbor = (
                        current[0] + delta_row,
                        current[1] + delta_col,
                    )
                    if (
                        0 <= neighbor[0] < len(grid)
                        and 0 <= neighbor[1] < len(grid[0])
                        and grid[neighbor[0]][neighbor[1]] != background
                        and neighbor not in seen
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            components.append(tuple(sorted(component)))
    return tuple(sorted(
        components,
        key=lambda component: (
            min(row for row, _col in component),
            min(col for _row, col in component),
        ),
    ))


def independent_port(component, local_row, local_col):
    top = min(row for row, _col in component)
    left = min(col for _row, col in component)
    bottom = max(row for row, _col in component)
    right = max(col for _row, col in component)
    cells = {(row - top, col - left) for row, col in component}
    height = bottom - top + 1
    width = right - left + 1
    best = (-1, 0, 0)
    for delta_row, delta_col in CARDINAL:
        if (
            local_row + delta_row,
            local_col + delta_col,
        ) in cells:
            continue
        score = 10 * (
            (
                local_row - delta_row,
                local_col - delta_col,
            )
            in cells
        )
        score += 5 * (
            (delta_row == -1 and local_row == 0)
            or (delta_row == 1 and local_row == height - 1)
            or (delta_col == -1 and local_col == 0)
            or (delta_col == 1 and local_col == width - 1)
        )
        if score > best[0]:
            best = (score, delta_row, delta_col)
    return best[1], best[2]


def independent_rule(grid):
    grid = [list(row) for row in grid]
    background = Counter(
        value for row in grid for value in row
    ).most_common(1)[0][0]
    components = components8(grid, background)
    markers = []
    for component_index, component in enumerate(components):
        top = min(row for row, _col in component)
        left = min(col for _row, col in component)
        for row, col in component:
            if grid[row][col] == 1:
                continue
            local_row = row - top
            local_col = col - left
            delta_row, delta_col = independent_port(
                component,
                local_row,
                local_col,
            )
            markers.append((
                grid[row][col],
                component_index,
                local_row,
                local_col,
                delta_row,
                delta_col,
            ))

    by_color = defaultdict(list)
    for marker in markers:
        by_color[marker[0]].append(marker)
    edges = [
        (color, values[0], values[1])
        for color, values in sorted(by_color.items())
        if len(values) == 2
    ]

    placements = {0: (0, 0)}
    for _step in range(3 * max(1, len(components))):
        for _color, first, second in edges:
            for source, target in ((first, second), (second, first)):
                if (
                    source[1] in placements
                    and target[1] not in placements
                ):
                    source_row, source_col = placements[source[1]]
                    placements[target[1]] = (
                        source_row + source[2] + source[4] - target[2],
                        source_col + source[3] + source[5] - target[3],
                    )

    placed = []
    for component_index, component in enumerate(components):
        origin_row, origin_col = placements.get(component_index, (0, 0))
        top = min(row for row, _col in component)
        left = min(col for _row, col in component)
        for row, col in component:
            placed.append((
                origin_row + row - top,
                origin_col + col - left,
                grid[row][col],
            ))
    top = min(row for row, _col, _value in placed)
    left = min(col for _row, col, _value in placed)
    bottom = max(row for row, _col, _value in placed)
    right = max(col for _row, col, _value in placed)
    output = [
        [background] * (right - left + 1)
        for _row in range(bottom - top + 1)
    ]
    for row, col, value in placed:
        output[row - top][col - left] = value
    return output


def transform_grid(grid, transform):
    transformed = [list(row) for row in grid]
    if transform >= 4:
        transformed = [list(reversed(row)) for row in transformed]
    for _turn in range(transform % 4):
        transformed = [
            list(row) for row in zip(*reversed(transformed))
        ]
    return transformed


class Generator54628ce9692dTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = canonical_row()
        cls.pairs = canonical_pairs()

    def test_all_published_pairs_and_profiles(self):
        self.assertEqual(len(self.pairs), 5)
        profiles = set()
        piece_counts = set()
        for index, pair in enumerate(self.pairs):
            grid = pair["input"]
            snapshot = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(independent_rule(grid), pair["output"])
            self.assertEqual(generator.rule_mirror(grid), pair["output"])
            self.assertEqual(grid, snapshot)
            self.assertEqual(
                generator.canonical_profile_index(grid),
                index,
            )
            profiles.add(index)
            piece_counts.add(
                generator.observe_overrides(grid)["n_pieces"]
            )
        self.assertEqual(profiles, set(range(5)))
        self.assertEqual(piece_counts, {2, 3, 4})

    def test_all_global_d4_symmetries_commute(self):
        for index, pair in enumerate(self.pairs):
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
                    index,
                )

    def test_every_exact_axis_cross_is_observed(self):
        for band in ("easy", "medium", "hard"):
            for n_pieces in range(2, 5):
                for background_color in range(2, 10):
                    expected = {
                        "n_pieces": n_pieces,
                        "background_color": background_color,
                    }
                    seed = (
                        10_000 * n_pieces
                        + 100 * background_color
                        + len(band)
                    )
                    grid = generator.generate(
                        seed,
                        seed * 17 + 5,
                        difficulty=band,
                        **expected,
                    )
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(
                        generator.observe_overrides(grid),
                        expected,
                    )
                    self.assertEqual(
                        generator.rule_mirror(grid),
                        independent_rule(grid),
                    )

    def test_default_distribution_is_complete_stable_and_diverse(self):
        for start in (0, 50_000):
            profiles = set()
            backgrounds = set()
            piece_counts = set()
            pairs_seen = set()
            for band_index, band in enumerate(
                ("easy", "medium", "hard")
            ):
                for offset in range(120):
                    seed = start + band_index * 10_000 + offset
                    grid = generator.generate(
                        seed,
                        seed * 29 + 7,
                        difficulty=band,
                    )
                    output = independent_rule(grid)
                    self.assertEqual(generator.self_check(grid), [])
                    self.assertEqual(generator.rule_mirror(grid), output)
                    observed = generator.observe_overrides(grid)
                    profiles.add(
                        generator.canonical_profile_index(grid)
                    )
                    backgrounds.add(observed["background_color"])
                    piece_counts.add(observed["n_pieces"])
                    pairs_seen.add((
                        tuple(map(tuple, grid)),
                        tuple(map(tuple, output)),
                    ))
            self.assertEqual(profiles, set(range(5)))
            self.assertEqual(backgrounds, set(range(2, 10)))
            self.assertEqual(piece_counts, {2, 3, 4})
            self.assertGreaterEqual(len(pairs_seen), 355)

    def test_structural_and_semantic_mutations_are_rejected(self):
        base = [row[:] for row in self.pairs[0]["input"]]
        missing_pair = [row[:] for row in base]
        missing_pair[4][4] = 1
        second_unmatched = [row[:] for row in base]
        second_unmatched[0][4] = 7
        damaged_shape = [row[:] for row in base]
        damaged_shape[2][2] = 2
        zero_background = [
            [0 if value == 2 else value for value in row]
            for row in base
        ]
        invalid_color = [row[:] for row in base]
        invalid_color[0][0] = 10
        for mutation in (
            missing_pair,
            second_unmatched,
            damaged_shape,
            zero_background,
            invalid_color,
            [],
            [[2] * 13 for _row in range(13)],
            [[2] * 12 for _row in range(13)],
            [[2] * 13 for _row in range(12)],
            [[2] * 13 for _row in range(14)],
            [[2] * 13 for _row in range(13)],
        ):
            self.assertTrue(generator.self_check(mutation), mutation)

    def test_plausible_novel_morphology_is_calibrated_out(self):
        candidate = [row[:] for row in self.pairs[1]["input"]]
        candidate[2][2] = 2
        self.assertEqual(
            generator.self_check(candidate),
            ["piece morphology/topology is not a published profile"],
        )
        # The executable oracle can assemble this one-cell shape variant,
        # but it is not evidence-backed enough to enter the default prior.
        output = independent_rule(candidate)
        self.assertTrue(output)
        with self.assertRaisesRegex(ValueError, "not a published profile"):
            generator.rule_mirror(candidate)

    def test_source_sync_hash_determinism_freshness_and_global_rng(self):
        source = self.row["program_solution"]
        for relative_path in (
            "data/base/solutions/training/"
            "e9fc42f2__54628ce9692d.json",
            "data/base/solutions/augmented/"
            "e9fc42f2__7e6dd4a69508.json",
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
        first[0][0] = 9 if first[0][0] != 9 else 0
        self.assertEqual(
            generator.generate(37, 43, difficulty="hard"),
            again,
        )


if __name__ == "__main__":
    unittest.main()
