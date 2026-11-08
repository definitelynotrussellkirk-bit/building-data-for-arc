from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.93b9313cdd29.generator"
)
TASK_ID = "93b9313cdd29"


@lru_cache(maxsize=1)
def canonical_record():
    path = ROOT / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        record = json.loads(line)
        if record.get("task_id") == TASK_ID:
            return record
    raise AssertionError(f"missing canonical task {TASK_ID}")


def normalized_hash(source):
    normalized = " ".join(source.split())
    return hashlib.sha256(normalized.encode()).hexdigest()[:12]


def crop_nonzero(grid):
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        raise ValueError("empty body")
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    return [
        list(values[left : right + 1])
        for values in grid[top : bottom + 1]
    ]


def independent_apply(body, tokens):
    result = copy.deepcopy(body)
    for token in tokens:
        if token == 1:
            result = [list(row) for row in zip(*result[::-1])]
        elif token == 2:
            result = [list(reversed(row)) for row in reversed(result)]
        elif token == 3:
            result = [list(reversed(row)) for row in result]
        elif token == 4:
            result = [list(row) for row in zip(*result)]
    return result


def independent_rule(grid):
    tokens = [value for value in grid[0] if value in {1, 2, 3, 4}]
    body = crop_nonzero(grid[1:])
    return independent_apply(body, tokens)


def canonicalize_body(body):
    mapping = {}
    next_role = 1
    normalized = []
    for row in body:
        normalized_row = []
        for value in row:
            if value == 0:
                normalized_row.append(0)
            else:
                if value not in mapping:
                    mapping[value] = next_role
                    next_role += 1
                normalized_row.append(mapping[value])
        normalized.append(tuple(normalized_row))
    return tuple(normalized)


def independent_profile(grid):
    tokens = tuple(value for value in grid[0] if value in {1, 2, 3, 4})
    body = canonicalize_body(crop_nonzero(grid[1:]))
    for name, profile_tokens, profile_body in MODULE.PUBLIC_PROFILES:
        if tokens == profile_tokens and body == profile_body:
            return name
    return None


def make_scene(tokens, body, *, height=8, width=9):
    height = max(height, len(body) + 2)
    width = max(width, len(body[0]), len(tokens))
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for col, token in enumerate(tokens):
        grid[0][col] = token
    for row, values in enumerate(body, start=2):
        for col, value in enumerate(values, start=1):
            if col < width:
                grid[row][col] = value
    return grid


def body_components(body):
    cells = {
        (row, col)
        for row, values in enumerate(body)
        for col, value in enumerate(values)
        if value != 0
    }
    components = 0
    while cells:
        components += 1
        stack = [cells.pop()]
        while stack:
            row, col = stack.pop()
            for delta_row, delta_col in (
                (-1, 0),
                (1, 0),
                (0, -1),
                (0, 1),
            ):
                neighbor = (row + delta_row, col + delta_col)
                if neighbor in cells:
                    cells.remove(neighbor)
                    stack.append(neighbor)
    return components


class Generator93b9313cdd29Tests(unittest.TestCase):
    def test_metadata_and_rule_hash_are_pinned(self):
        self.assertEqual(TASK_ID, MODULE.GENERATOR_ID)
        self.assertEqual(TASK_ID, MODULE.TASK_ID)
        self.assertEqual({"scene_family"}, set(MODULE.AXES))
        target = canonical_record()["program_solution"]
        self.assertEqual("9ad483dbe321", normalized_hash(target))
        self.assertEqual(normalized_hash(target), MODULE.RULE_HASH)

    def test_all_canonical_pairs_and_profiles(self):
        record = canonical_record()
        pairs = record["train"] + record["test"]
        expected_profiles = (
            "public_train_1",
            "public_train_2",
            "public_train_3",
            "public_test_1",
        )
        self.assertEqual(4, len(pairs))
        for pair, profile in zip(pairs, expected_profiles):
            with self.subTest(profile=profile):
                source = copy.deepcopy(pair["input"])
                self.assertEqual([], MODULE.self_check(source))
                self.assertEqual(profile, independent_profile(source))
                self.assertEqual(profile, MODULE.canonical_profile_signature(source))
                self.assertTrue(MODULE.is_canonical_profile(source))
                self.assertEqual(
                    {"scene_family": "public"},
                    MODULE.observe_overrides(source),
                )
                self.assertEqual(pair["output"], independent_rule(source))
                self.assertEqual(pair["output"], MODULE.rule_mirror(source))
                self.assertEqual(pair["input"], source)

    def test_public_family_reaches_every_complete_profile(self):
        seen = set()
        for band in ("easy", "medium", "hard"):
            band_seen = set()
            for sample_index in range(500):
                grid = MODULE.generate(
                    100_000 + sample_index,
                    sample_index * 17 + 5,
                    difficulty=band,
                    scene_family="public",
                )
                before = copy.deepcopy(grid)
                profile = independent_profile(grid)
                band_seen.add(profile)
                seen.add(profile)
                self.assertEqual([], MODULE.self_check(grid))
                self.assertEqual(profile, MODULE.canonical_profile_signature(grid))
                self.assertEqual(
                    {"scene_family": "public"}, MODULE.observe_overrides(grid)
                )
                self.assertEqual(independent_rule(grid), MODULE.rule_mirror(grid))
                self.assertEqual(before, grid)
            self.assertEqual(
                {
                    "public_train_1",
                    "public_train_2",
                    "public_train_3",
                    "public_test_1",
                },
                band_seen,
            )
        self.assertEqual(4, len(seen))

    def test_public_profile_is_nuisance_invariant(self):
        original = canonical_record()["train"][1]["input"]
        transformed = [[0 for _ in range(13)] for _ in range(12)]
        transformed[0][4:7] = [4, 2, 1]
        role_map = {7: 9, 8: 5}
        body = crop_nonzero(original[1:])
        for row, values in enumerate(body, start=5):
            for col, value in enumerate(values, start=3):
                transformed[row][col] = role_map.get(value, 0)
        self.assertEqual([], MODULE.self_check(transformed))
        self.assertEqual("public_train_2", independent_profile(transformed))
        self.assertEqual(
            "public_train_2", MODULE.canonical_profile_signature(transformed)
        )

    def test_generalized_family_teaches_composition_and_layout(self):
        all_tokens = set()
        scripts = set()
        saw_gap = False
        saw_decoy = False
        saw_disconnected = False
        saw_multicolor = False
        input_hashes = set()
        output_hashes = set()
        for band in ("easy", "medium", "hard"):
            for sample_index in range(450):
                grid = MODULE.generate(
                    300_000 + sample_index,
                    sample_index * 29 + 11,
                    difficulty=band,
                    scene_family="generalized",
                )
                analysis = MODULE._analyze(grid)
                self.assertEqual([], analysis["errors"])
                facts = analysis["facts"]
                self.assertIsNone(independent_profile(grid))
                self.assertIsNone(MODULE.canonical_profile_signature(grid))
                self.assertEqual(
                    {"scene_family": "generalized"},
                    MODULE.observe_overrides(grid),
                )
                self.assertEqual(independent_rule(grid), facts["output"])
                self.assertEqual(facts["output"], MODULE.rule_mirror(grid))
                self.assertNotEqual(facts["body"], facts["output"])
                all_tokens.update(facts["tokens"])
                scripts.add(facts["tokens"])
                positions = [
                    col
                    for col, value in enumerate(grid[0])
                    if value in {1, 2, 3, 4}
                ]
                saw_gap |= any(
                    right - left > 1
                    for left, right in zip(positions, positions[1:])
                )
                saw_decoy |= bool(facts["header_decoys"])
                saw_disconnected |= body_components(facts["body"]) > 1
                saw_multicolor |= len(facts["body_colors"]) > 1
                input_hashes.add(tuple(map(tuple, grid)))
                output_hashes.add(tuple(map(tuple, facts["output"])))
        self.assertEqual({1, 2, 3, 4}, all_tokens)
        self.assertTrue({(1, 3), (3, 1), (1, 4), (4, 1)}.issubset(scripts))
        self.assertTrue(any(len(script) >= 4 for script in scripts))
        self.assertTrue(saw_gap)
        self.assertTrue(saw_decoy)
        self.assertTrue(saw_disconnected)
        self.assertTrue(saw_multicolor)
        self.assertGreater(len(input_hashes), 1_300)
        self.assertGreater(len(output_hashes), 1_250)

    def test_order_is_semantically_causal(self):
        body = [
            [5, 0, 0],
            [5, 6, 6],
        ]
        first = independent_apply(body, (1, 3))
        second = independent_apply(body, (3, 1))
        self.assertNotEqual(first, second)
        self.assertEqual(first, MODULE._apply_script(body, (1, 3)))
        self.assertEqual(second, MODULE._apply_script(body, (3, 1)))

    def test_header_filtering_spacing_and_decoys(self):
        body = [
            [5, 0, 6],
            [5, 6, 6],
        ]
        compact = make_scene((1, 3), body)
        spaced = make_scene((), body, width=11)
        spaced[0][1] = 1
        spaced[0][4] = 8
        spaced[0][8] = 3
        self.assertEqual([], MODULE.self_check(compact))
        self.assertEqual([], MODULE.self_check(spaced))
        self.assertEqual(independent_rule(compact), independent_rule(spaced))
        self.assertEqual(MODULE.rule_mirror(compact), MODULE.rule_mirror(spaced))

    def test_near_miss_profile_recombinations_are_not_public(self):
        profiles = list(MODULE.PUBLIC_PROFILES)
        for token_index, (_, tokens, _) in enumerate(profiles):
            for body_index, (_, _, role_body) in enumerate(profiles):
                if token_index == body_index:
                    continue
                body = [
                    [0 if value == 0 else value + 4 for value in row]
                    for row in role_body
                ]
                grid = make_scene(tokens, body, height=10, width=12)
                self.assertIsNone(independent_profile(grid))
                self.assertIsNone(MODULE.canonical_profile_signature(grid))
                if not MODULE.self_check(grid):
                    self.assertEqual(
                        {"scene_family": "generalized"},
                        MODULE.observe_overrides(grid),
                    )

    def test_natural_prior_and_disjoint_stability(self):
        for seed_base in (700_000, 900_000):
            for band_index, band in enumerate(("easy", "medium", "hard")):
                families = Counter()
                profiles = set()
                inputs = set()
                outputs = set()
                for sample_index in range(800):
                    grid = MODULE.generate(
                        seed_base + band_index,
                        sample_index * 31 + 7,
                        difficulty=band,
                    )
                    family = MODULE.observe_overrides(grid)["scene_family"]
                    families[family] += 1
                    profile = MODULE.canonical_profile_signature(grid)
                    if profile:
                        profiles.add(profile)
                    inputs.add(tuple(map(tuple, grid)))
                    outputs.add(tuple(map(tuple, MODULE.rule_mirror(grid))))
                public_rate = families["public"] / 800
                self.assertGreaterEqual(public_rate, 0.34)
                self.assertLessEqual(public_rate, 0.46)
                self.assertEqual(4, len(profiles))
                self.assertGreaterEqual(len(inputs), 790)
                self.assertGreaterEqual(len(outputs), 450)

    def test_difficulty_changes_semantic_complexity(self):
        summaries = {}
        for band_index, band in enumerate(("easy", "medium", "hard")):
            areas = []
            occupied = []
            script_lengths = []
            for sample_index in range(500):
                grid = MODULE.generate(
                    1_100_000 + band_index,
                    sample_index * 37 + 13,
                    difficulty=band,
                    scene_family="generalized",
                )
                facts = MODULE._analyze(grid)["facts"]
                areas.append(facts["height"] * facts["width"])
                occupied.append(facts["occupied"])
                script_lengths.append(len(facts["tokens"]))
            summaries[band] = (
                sum(areas) / len(areas),
                sum(occupied) / len(occupied),
                sum(script_lengths) / len(script_lengths),
            )
        for index in range(3):
            self.assertLess(summaries["easy"][index], summaries["medium"][index])
            self.assertLess(summaries["medium"][index], summaries["hard"][index])

    def test_determinism_fresh_returns_and_global_rng_purity(self):
        random.seed(271_828)
        state = random.getstate()
        first = MODULE.generate(
            777,
            888,
            difficulty="hard",
            scene_family="generalized",
        )
        second = MODULE.generate(
            777,
            888,
            difficulty="hard",
            scene_family="generalized",
        )
        self.assertEqual(state, random.getstate())
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        second[0][0] = 9
        third = MODULE.generate(
            777,
            888,
            difficulty="hard",
            scene_family="generalized",
        )
        self.assertEqual(first, third)

    def test_overrides_are_exact_and_invalid_calls_fail_loudly(self):
        for band in ("easy", "medium", "hard"):
            for family in ("public", "generalized"):
                for seed in range(80):
                    grid = MODULE.generate(
                        seed,
                        seed * 41 + 3,
                        difficulty=band,
                        scene_family=family,
                    )
                    self.assertEqual(
                        {"scene_family": family}, MODULE.observe_overrides(grid)
                    )
        with self.assertRaises(ValueError):
            MODULE.generate(1, 2, difficulty="impossible")
        with self.assertRaises(ValueError):
            MODULE.generate(1, 2, unknown_axis="x")
        with self.assertRaises(ValueError):
            MODULE.generate(1, 2, scene_family="wrong")

    def test_self_check_rejects_targeted_semantic_impostors(self):
        impostors = {
            "all_background": [[0] * 9 for _ in range(8)],
            "full_color": [[5] * 9 for _ in range(8)],
            "singleton": make_scene((1,), [[5]]),
            "solid_2x2": make_scene((1,), [[5, 5], [5, 5]]),
            "horizontal_line": make_scene((1,), [[5, 5, 5, 5]]),
            "missing_script": make_scene((), [[5, 0], [5, 5]]),
            "reserved_body_token": make_scene((1,), [[5, 0], [5, 2]]),
            "nonblank_separator": make_scene((1,), [[5, 0], [5, 5]]),
            "identity_flip": make_scene(
                (3,),
                [
                    [5, 0, 5],
                    [0, 5, 0],
                    [5, 0, 5],
                ],
            ),
            "ragged": [[0] * 9 for _ in range(7)] + [[0] * 8],
            "boolean": make_scene((1,), [[5, 0], [5, True]]),
            "bad_value": make_scene((1,), [[5, 0], [5, 10]]),
        }
        impostors["nonblank_separator"][1][4] = 6
        for name, grid in impostors.items():
            with self.subTest(name=name):
                self.assertTrue(MODULE.self_check(grid))
                self.assertEqual({}, MODULE.observe_overrides(grid))

    def test_mutations_break_individual_obligations(self):
        valid = MODULE.generate(
            42,
            73,
            difficulty="hard",
            scene_family="generalized",
        )
        self.assertEqual([], MODULE.self_check(valid))

        no_tokens = copy.deepcopy(valid)
        no_tokens[0] = [0 for _ in no_tokens[0]]

        bad_separator = copy.deepcopy(valid)
        bad_separator[1][0] = 5

        reserved_body = copy.deepcopy(valid)
        body_cell = next(
            (row, col)
            for row in range(2, len(valid))
            for col, value in enumerate(valid[row])
            if value != 0
        )
        reserved_body[body_cell[0]][body_cell[1]] = 2

        too_many_decoys = copy.deepcopy(valid)
        too_many_decoys[0] = [0 for _ in too_many_decoys[0]]
        too_many_decoys[0][:4] = [1, 5, 6, 7]

        mutations = {
            "missing token sequence": no_tokens,
            "separator violation": bad_separator,
            "reserved body color": reserved_body,
            "too many header decoys": too_many_decoys,
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name):
                self.assertTrue(MODULE.self_check(mutation))


if __name__ == "__main__":
    unittest.main()
