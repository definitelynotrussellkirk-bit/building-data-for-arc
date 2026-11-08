"""Focused semantic and contract regressions for generator fe54bfae4cee."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib
import json

from reviewer_support import canonical_path, find_root
import random
import unittest


TASK_ID = "fe54bfae4cee"
ROOT = find_root(__file__)
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _canonical_row():
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


def _canonical_pairs():
    row = _canonical_row()
    test = row.get("test")
    test_pairs = test if isinstance(test, list) else ([test] if test else [])
    return [*row.get("train", []), *test_pairs]


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _nonzero_components(grid):
    unseen = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    count = 0
    while unseen:
        count += 1
        stack = [unseen.pop()]
        while stack:
            r, c = stack.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    stack.append(neighbor)
    return count


def _near_kind(grid):
    pairs = MODULE._fillable_pairs(grid)
    if len(pairs) == 2:
        return "none"
    target = pairs[0]
    positions = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                positions.setdefault(value, []).append((r, c))
    if len(positions[target.color]) == 3:
        return "blocked"
    decoy_color = next(color for color in positions if color != target.color)
    (r1, c1), (r2, c2) = positions[decoy_color]
    if abs(r1 - r2) == abs(c1 - c2) == 2:
        return "diagonal"
    return "longspan"


class GeneratorFe54bfae4ceeTests(unittest.TestCase):
    def test_canonical_inventory_semantics_and_rule_pin(self):
        row = _canonical_row()
        pairs = _canonical_pairs()
        self.assertEqual(len(row["train"]), 2)
        self.assertEqual(len(pairs), 3)
        self.assertEqual(MODULE.RULE_HASH, "92b2f2721622")
        self.assertEqual(MODULE.RULE_HASH, _normalized_hash(row["program_solution"]))

        profiles = []
        for pair in pairs:
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            self.assertEqual(MODULE.self_check(source), [])
            self.assertEqual(MODULE.rule_mirror(source), pair["output"])
            self.assertEqual(source, before)
            active = MODULE._fillable_pairs(source)
            profiles.append(
                (
                    len(active),
                    tuple(sorted(witness.orientation for witness in active)),
                    _near_kind(source),
                )
            )
        self.assertEqual(
            profiles,
            [
                (2, ("horizontal", "vertical"), "none"),
                (2, ("horizontal", "vertical"), "none"),
                (1, ("vertical",), "longspan"),
            ],
        )

    def test_declared_axes_are_minimal_exact_and_observable(self):
        self.assertEqual(set(MODULE.AXES), {"grid_h", "grid_w", "pairs"})
        for band in ("easy", "medium", "hard"):
            for h in (7, 12):
                for w in (7, 12):
                    for pair_count in (1, 2):
                        for seed in range(4):
                            grid = MODULE.generate(
                                seed,
                                seed * 17 + 3,
                                difficulty=band,
                                grid_h=h,
                                grid_w=w,
                                pairs=pair_count,
                            )
                            self.assertEqual(
                                MODULE.observe_overrides(grid),
                                {"grid_h": h, "grid_w": w, "pairs": pair_count},
                            )
                            self.assertEqual(MODULE.self_check(grid), [])

    def test_invalid_axis_values_reject_loudly(self):
        for overrides in (
            {"grid_h": 6},
            {"grid_h": 13},
            {"grid_w": 6},
            {"grid_w": 13},
            {"pairs": 0},
            {"pairs": 3},
            {"unknown_axis": 1},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    MODULE.generate(1, 2, **overrides)

    def test_default_linked_profiles_cover_positive_and_negative_branches(self):
        expected_near = {
            "easy": {"none", "longspan"},
            "medium": {"none", "longspan", "diagonal"},
            "hard": {"none", "longspan", "diagonal", "blocked"},
        }
        for band in ("easy", "medium", "hard"):
            inputs = set()
            outputs = set()
            pair_counts = Counter()
            target_orientations = Counter()
            near_kinds = Counter()
            object_counts = Counter()
            for seed in range(240):
                grid = MODULE.generate(seed + 1000, seed * 29 + 7, difficulty=band)
                self.assertEqual(MODULE.self_check(grid), [])
                witnesses = MODULE._fillable_pairs(grid)
                pair_counts[len(witnesses)] += 1
                target_orientations.update(w.orientation for w in witnesses)
                near_kinds[_near_kind(grid)] += 1
                object_counts[_nonzero_components(grid)] += 1
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, MODULE.rule_mirror(grid))))
            self.assertEqual(set(pair_counts), {1, 2})
            self.assertEqual(set(target_orientations), {"horizontal", "vertical"})
            self.assertEqual(set(near_kinds), expected_near[band])
            if band == "hard":
                self.assertEqual(set(object_counts), {3, 4})
                self.assertEqual(object_counts[3], near_kinds["blocked"])
                self.assertGreater(object_counts[4], object_counts[3])
            else:
                self.assertEqual(object_counts, Counter({4: 240}))
            self.assertGreaterEqual(len(inputs), 238)
            self.assertGreaterEqual(len(outputs), 238)

    def test_rule_mirror_changes_exact_midpoints_and_preserves_input(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(60):
                grid = MODULE.generate(seed + 3000, seed * 31 + 11, difficulty=band)
                before = copy.deepcopy(grid)
                output = MODULE.rule_mirror(grid)
                self.assertEqual(grid, before)
                changed = {
                    (r, c)
                    for r, row in enumerate(grid)
                    for c, value in enumerate(row)
                    if output[r][c] != value
                }
                self.assertEqual(changed, MODULE._rule_fills(grid))
                for witness in MODULE._fillable_pairs(grid):
                    r, c = witness.midpoint
                    self.assertEqual(output[r][c], witness.color)

    def test_determinism_fresh_returns_and_global_rng_purity(self):
        random.seed(20260723)
        state = random.getstate()
        first = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))
        first[0][0] = 9 if first[0][0] != 9 else 8
        self.assertNotEqual(first, second)

    def test_self_check_rejects_targeted_impostors(self):
        all_zero = [[0] * 7 for _ in range(7)]

        one_color = MODULE.generate(11, 13, difficulty="medium")
        one_color = [[1 if value else 0 for value in row] for row in one_color]

        third_color = MODULE.generate(17, 19, difficulty="medium")
        third_color = copy.deepcopy(third_color)
        third_color[0][0] = next(
            color
            for color in range(1, 10)
            if color not in {value for row in third_color for value in row}
        )

        two_horizontal = [[0] * 7 for _ in range(7)]
        two_horizontal[1][1] = two_horizontal[1][3] = 2
        two_horizontal[5][2] = two_horizontal[5][4] = 6

        same_axis_near_miss = [[0] * 7 for _ in range(7)]
        same_axis_near_miss[1][1] = same_axis_near_miss[1][3] = 2
        same_axis_near_miss[5][1] = same_axis_near_miss[5][4] = 6

        count_only_recombination = [[0] * 7 for _ in range(7)]
        count_only_recombination[1][1] = count_only_recombination[1][3] = 2
        count_only_recombination[4][4] = count_only_recombination[6][4] = 2
        count_only_recombination[0][6] = 6

        ragged = [[0] * 7 for _ in range(7)]
        ragged[0].pop()
        invalid_color = [[0] * 7 for _ in range(7)]
        invalid_color[1][1] = 10
        boolean_color = [[0] * 7 for _ in range(7)]
        boolean_color[1][1] = True

        for mutation in (
            all_zero,
            one_color,
            third_color,
            two_horizontal,
            same_axis_near_miss,
            count_only_recombination,
            ragged,
            invalid_color,
            boolean_color,
        ):
            with self.subTest(mutation=mutation):
                self.assertTrue(MODULE.self_check(mutation), mutation)

    def test_local_mutations_of_accepted_scenes_are_rejected(self):
        for pair_count in (1, 2):
            base = MODULE.generate(
                451,
                919,
                difficulty="hard",
                grid_h=9,
                grid_w=10,
                pairs=pair_count,
            )
            endpoints = [
                (r, c)
                for r, row in enumerate(base)
                for c, value in enumerate(row)
                if value != 0
            ]

            delete_endpoint = copy.deepcopy(base)
            r, c = endpoints[0]
            delete_endpoint[r][c] = 0

            add_noise = copy.deepcopy(base)
            used = {value for row in base for value in row}
            new_color = next(color for color in range(1, 10) if color not in used)
            add_noise[0][0] = new_color

            stomp_colors = [[1 if value else 0 for value in row] for row in base]

            duplicate_endpoint = copy.deepcopy(base)
            r, c = endpoints[-1]
            destination = next(
                (rr, cc)
                for rr, row in enumerate(base)
                for cc, value in enumerate(row)
                if value == 0 and (rr, cc) not in MODULE._rule_fills(base)
            )
            duplicate_endpoint[destination[0]][destination[1]] = base[r][c]

            for mutation in (
                delete_endpoint,
                add_noise,
                stomp_colors,
                duplicate_endpoint,
            ):
                self.assertTrue(MODULE.self_check(mutation), mutation)

    def test_negative_recombination_can_fire_rule_but_is_out_of_distribution(self):
        # Two horizontal pairs satisfy a count-only shortcut and both fire the
        # broad transformation, but omit the canonical horizontal+vertical link.
        grid = [[0] * 7 for _ in range(7)]
        grid[1][1] = grid[1][3] = 2
        grid[5][2] = grid[5][4] = 6
        self.assertEqual(len(MODULE._fillable_pairs(grid)), 2)
        self.assertNotEqual(MODULE.rule_mirror(grid), grid)
        self.assertTrue(MODULE.self_check(grid))


if __name__ == "__main__":
    unittest.main()
