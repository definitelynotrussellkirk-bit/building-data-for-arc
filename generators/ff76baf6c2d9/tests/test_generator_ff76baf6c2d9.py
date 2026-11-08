from __future__ import annotations

import hashlib
import json
import random
import unittest
from collections import Counter
from puzzle_generators.per_puzzle.ff76baf6c2d9 import generator
from reviewer_support import (
    canonical_pairs as reviewer_canonical_pairs,
    canonical_path,
    find_root,
)
from solvers.grounded_rules import GROUNDED_RULES


ROOT = find_root(__file__)
CANONICAL = canonical_path(ROOT)
DATA = CANONICAL.parent.parent
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
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == generator.TASK_ID:
                return row
    raise KeyError(generator.TASK_ID)


def canonical_pairs():
    return [
        {"input": pair["input"], "output": pair["output"]}
        for pair in reviewer_canonical_pairs(
            generator.TASK_ID, root=ROOT, variant=0
        )
    ]


def coerce(grid):
    return [
        [int(value) for value in row]
        if isinstance(row, str)
        else list(row)
        for row in grid
    ]


def components8(grid):
    grid = coerce(grid)
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
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
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and grid[neighbor[0]][neighbor[1]] != 0
                        and neighbor not in seen
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            components.append(tuple(sorted(component)))
    return tuple(components)


def independent_rule(grid):
    grid = coerce(grid)
    output = [row[:] for row in grid]
    components = components8(grid)
    singles = tuple(component[0] for component in components if len(component) == 1)
    sources = tuple(component for component in components if len(component) > 1)
    for source in sources:
        for anchor_color in range(1, 10):
            anchors = tuple(
                cell
                for cell in source
                if grid[cell[0]][cell[1]] == anchor_color
            )
            if len(anchors) != 1:
                continue
            anchor_row, anchor_col = anchors[0]
            targets = tuple(
                cell
                for cell in singles
                if grid[cell[0]][cell[1]] == anchor_color
            )
            for target_row, target_col in targets:
                for source_row, source_col in source:
                    delta_row = source_row - anchor_row
                    delta_col = source_col - anchor_col
                    if delta_row == 0 and delta_col == 0:
                        continue
                    output_row = target_row + delta_row
                    output_col = target_col + (
                        -delta_col if anchor_color == 2 else delta_col
                    )
                    if (
                        0 <= output_row < len(grid)
                        and 0 <= output_col < len(grid[0])
                    ):
                        output[output_row][output_col] = (
                            grid[source_row][source_col]
                        )
    return output


def independent_facts(grid):
    grid = coerce(grid)
    components = components8(grid)
    singles = tuple(component[0] for component in components if len(component) == 1)
    sources = tuple(component for component in components if len(component) > 1)
    anchor_colors = []
    source_sizes = []
    target_counts = []
    for source in sources:
        counts = Counter(grid[row][col] for row, col in source)
        unique = [color for color, count in counts.items() if count == 1]
        if len(counts) != 2 or len(unique) != 1:
            raise AssertionError((source, counts))
        if sorted(counts.values()) != [1, len(source) - 1]:
            raise AssertionError((source, counts))
        anchor_colors.append(unique[0])
        source_sizes.append(len(source))
        target_counts.append(sum(
            grid[row][col] == unique[0] for row, col in singles
        ))
    return {
        "n_sources": len(sources),
        "n_targets": len(singles),
        "anchor_colors": tuple(anchor_colors),
        "source_sizes": tuple(source_sizes),
        "target_counts": tuple(target_counts),
    }


def safe_transform(grid, transform):
    grid = coerce(grid)
    if transform & 1:
        grid = list(reversed(grid))
    if transform & 2:
        grid = [list(reversed(row)) for row in grid]
    return [list(row) for row in grid]


def normalized_rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


class Ff76baf6c2d9GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = canonical_row()
        cls.pairs = canonical_pairs()

    def test_all_published_pairs_and_profiles(self):
        self.assertEqual(len(self.pairs), 5)
        profiles = set()
        modes = set()
        for index, pair in enumerate(self.pairs):
            grid = pair["input"]
            before = [row[:] for row in grid]
            self.assertEqual(generator.self_check(grid), [])
            self.assertEqual(independent_rule(grid), pair["output"])
            self.assertEqual(generator.rule_mirror(grid), pair["output"])
            self.assertEqual(grid, before)
            self.assertEqual(generator.canonical_profile_index(grid), index)
            profiles.add(index)
            facts = independent_facts(grid)
            modes.add((
                2 in facts["anchor_colors"],
                any(color != 2 for color in facts["anchor_colors"]),
            ))
            self.assertTrue(all(count >= 1 for count in facts["target_counts"]))
        self.assertEqual(profiles, set(range(5)))
        self.assertIn((True, False), modes)
        self.assertIn((False, True), modes)
        self.assertIn((True, True), modes)

    def test_only_safe_symmetries_commute_and_keep_profiles(self):
        for index, pair in enumerate(self.pairs):
            for transform in range(4):
                transformed_input = safe_transform(
                    pair["input"],
                    transform,
                )
                transformed_output = safe_transform(
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
                    generator.canonical_profile_index(transformed_input),
                    index,
                )

    def test_profile_prior_is_stable_diverse_and_complete(self):
        for start in (0, 50_000):
            for band in ("easy", "medium", "hard"):
                matches = 0
                profiles = set()
                pairs_seen = set()
                for offset in range(600):
                    seed = start + offset
                    grid = generator.generate(
                        seed,
                        seed * 17 + 1,
                        difficulty=band,
                    )
                    output = independent_rule(grid)
                    pairs_seen.add((
                        tuple(map(tuple, grid)),
                        tuple(map(tuple, output)),
                    ))
                    profile = generator.canonical_profile_index(grid)
                    if profile is not None:
                        matches += 1
                        profiles.add(profile)
                self.assertGreaterEqual(matches, 130)
                self.assertLessEqual(matches, 220)
                self.assertEqual(profiles, set(range(5)))
                self.assertGreaterEqual(len(pairs_seen), 580)

    def test_every_feasible_exact_axis_cross_is_observed(self):
        for size in (13, 24):
            for n_sources in (1, 2):
                for n_targets in range(n_sources, 5):
                    expected = {
                        "grid_size": size,
                        "n_sources": n_sources,
                        "n_targets": n_targets,
                    }
                    grid = generator.generate(
                        size * 100 + n_sources * 10 + n_targets,
                        97,
                        difficulty=("easy", "medium", "hard")[
                            (size + n_sources + n_targets) % 3
                        ],
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
        with self.assertRaisesRegex(ValueError, "at least n_sources"):
            generator.generate(
                1,
                2,
                n_sources=2,
                n_targets=1,
            )

    def test_default_distribution_has_answer_bearing_roles(self):
        source_sizes = set()
        target_counts = set()
        saw_mirror = saw_preserve = saw_both = False
        for band in ("easy", "medium", "hard"):
            for seed in range(500):
                grid = generator.generate(
                    seed,
                    seed * 29 + 7,
                    difficulty=band,
                )
                self.assertEqual(generator.self_check(grid), [])
                facts = independent_facts(grid)
                self.assertTrue(all(
                    count >= 1 for count in facts["target_counts"]
                ))
                source_sizes.update(facts["source_sizes"])
                target_counts.add(facts["n_targets"])
                has_mirror = 2 in facts["anchor_colors"]
                has_preserve = any(
                    color != 2 for color in facts["anchor_colors"]
                )
                saw_mirror |= has_mirror
                saw_preserve |= has_preserve
                saw_both |= has_mirror and has_preserve
        self.assertEqual(source_sizes, {4, 5, 6})
        self.assertEqual(target_counts, {1, 2, 3, 4})
        self.assertTrue(saw_mirror)
        self.assertTrue(saw_preserve)
        self.assertTrue(saw_both)

    def test_general_recombination_is_valid_but_not_a_public_profile(self):
        grid = generator.generate(
            73,
            91,
            grid_size=13,
            n_sources=2,
            n_targets=4,
        )
        self.assertEqual(generator.self_check(grid), [])
        self.assertIsNone(generator.canonical_profile_index(grid))
        self.assertEqual(
            generator.rule_mirror(grid),
            independent_rule(grid),
        )

    def test_structural_mutations_are_rejected(self):
        base = [row[:] for row in self.pairs[0]["input"]]
        three_colors = [row[:] for row in base]
        three_colors[2][3] = 7
        no_request = [row[:] for row in base]
        no_request[8][1] = 0
        clipped = [row[:] for row in base]
        clipped[1][10] = 0
        clipped[0][12] = 2
        wrong_request = [row[:] for row in base]
        wrong_request[8][1] = 2
        merged_target = [row[:] for row in self.pairs[3]["input"]]
        merged_target[8][8] = 2
        for mutation in (
            three_colors,
            no_request,
            clipped,
            wrong_request,
            merged_target,
            [],
            [[0] * 13 for _row in range(13)],
            [[0] * 12 for _row in range(13)],
            [[0] * 25 for _row in range(25)],
            [[10] * 13 for _row in range(13)],
        ):
            self.assertTrue(generator.self_check(mutation), mutation)

    def test_canonical_authority_archival_provenance_and_rng_purity(self):
        source = self.row["program_solution"]
        base_path = (
            DATA
            / "base/solutions/training"
            / "3e980e27__ff76baf6c2d9.json"
        )
        target = json.loads(base_path.read_text())["racket_target"]
        self.assertNotEqual(target["raw_code"], source)
        self.assertNotEqual(target["target_code"], source)
        self.assertNotEqual(target["raw_code"], target["target_code"])
        self.assertEqual(
            target["canonicalization_status"],
            "preserved_executable_source",
        )
        self.assertEqual(target["target_status"], "verified_racket_available")
        self.assertEqual(
            normalized_rule_hash(GROUNDED_RULES[generator.TASK_ID]),
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
