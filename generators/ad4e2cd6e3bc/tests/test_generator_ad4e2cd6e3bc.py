from __future__ import annotations

import copy
import hashlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

from reviewer_support import (
    canonical_pairs as load_canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)

TASK = "ad4e2cd6e3bc"
ROOT = find_root(__file__)
MOD, _, _ = load_selected_generator(TASK, root=ROOT)
BASE = Path("data/base/solutions/banks/2f7d84161f6a/H8__ad4e2cd6e3bc.json")


def canonical_row():
    return next(
        json.loads(line)
        for line in canonical_path(ROOT).read_text().splitlines()
        if json.loads(line).get("task_id") == TASK
    )


def pairs():
    return load_canonical_pairs(TASK, root=ROOT)


def base_path():
    for candidate in (ROOT / BASE, ROOT / "shared" / BASE):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(BASE)


def passable_components(grid):
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] in (0, 2)}
    components = []
    while unseen:
        todo = [min(unseen)]
        cells = set()
        while todo:
            row, col = todo.pop()
            if (row, col) not in unseen:
                continue
            unseen.remove((row, col))
            cells.add((row, col))
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in unseen:
                    todo.append(neighbor)
        components.append(cells)
    return components


def largest_component_rival(grid):
    output = [list(row) for row in grid]
    component = max(passable_components(grid), key=lambda cells: (len(cells), -min(cells)[0], -min(cells)[1]))
    for row, col in component:
        if grid[row][col] == 0:
            output[row][col] = 8
    return output


def local_neighbor_rival(grid):
    height, width = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0:
                continue
            if any(
                0 <= rr < height and 0 <= cc < width and grid[rr][cc] in (0, 2)
                for rr, cc in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
            ):
                output[row][col] = 8
    return output


class GeneratorTests(unittest.TestCase):
    def test_all_canonical_pairs_and_exact_public_profiles(self):
        self.assertEqual(len(pairs()), 3)
        for profile, pair in zip(MOD.PUBLIC_PROFILES, pairs()):
            self.assertEqual(MOD.rule_mirror(pair["input"]), pair["output"])
            self.assertEqual(MOD.self_check(pair["input"]), [])
            generated = MOD.generate(1, 2, scene_profile=profile)
            self.assertEqual(generated, pair["input"])
            self.assertEqual(MOD.canonical_profile_signature(generated), profile)
            self.assertIsNot(generated, MOD._PUBLIC_INPUTS[profile])

    def test_default_census_meets_canonical_profile_floor(self):
        canonical_profiles = {
            (
                len(pair["input"]),
                len(pair["input"][0]),
                len({value for row in pair["input"] for value in row}),
            )
            for pair in pairs()
        }
        exact_hits = 0
        for band in ("easy", "medium", "hard"):
            for index in range(20):
                digest = hashlib.sha256(
                    f"profile-floor:v1:{TASK}:{band}:{index}".encode()
                ).hexdigest()
                seed = int(digest[:12], 16)
                grid = MOD.generate(seed, seed % 7919 + index, difficulty=band)
                profile = (
                    len(grid),
                    len(grid[0]),
                    len({value for row in grid for value in row}),
                )
                exact_hits += profile in canonical_profiles
        self.assertGreaterEqual(exact_hits, 15)

    def test_strict_semantic_contract_accepts_domain_and_rejects_invalid(self):
        for pair in pairs():
            self.assertEqual(MOD.strict_canonical_like(pair["input"]), [])
        generated = MOD.generate(5, 17, difficulty="hard", scene_profile="three_pockets")
        self.assertEqual(MOD.strict_canonical_like(generated), [])
        generated[0][0] = 0
        self.assertTrue(MOD.strict_canonical_like(generated))

    def test_declared_shortcut_witnesses_refute_canonical_fitting_rivals(self):
        names = {"largest_component", "local_neighbor"}
        self.assertEqual(set(MOD.SEMANTIC_RIVALS), names)
        self.assertEqual(set(MOD.SEMANTIC_WITNESSES), names)
        self.assertEqual(set(MOD.WITNESS_RIVALS), names)
        for pair in pairs():
            for rival in MOD.SEMANTIC_RIVALS.values():
                self.assertEqual(rival(pair["input"]), pair["output"])
        witnesses = {
            "largest_component": MOD.generate(
                0, 10, difficulty="easy", scene_profile="one_pocket"
            ),
            "local_neighbor": MOD.generate(
                3, 313, difficulty="easy", scene_profile="one_pocket"
            ),
        }
        for name, grid in witnesses.items():
            self.assertEqual(MOD.WITNESS_RIVALS[name], [name])
            self.assertTrue(MOD.SEMANTIC_WITNESSES[name](grid))
            self.assertNotEqual(MOD.rule_mirror(grid), MOD.SEMANTIC_RIVALS[name](grid))

    def test_every_pocket_profile_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MOD.GENERAL_PROFILES:
                for seed in range(35):
                    grid = MOD.generate(seed, seed * 17, difficulty=band, scene_profile=profile)
                    analysis = MOD._analysis(grid)
                    self.assertEqual(analysis["errors"], [], (band, profile, seed))
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(analysis["pocket_count"], MOD._PROFILE_POCKETS[profile])
                    self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})

    def test_generated_pocket_profiles_require_seed_location(self):
        for band in ("easy", "medium", "hard"):
            for profile in MOD.GENERAL_PROFILES[1:]:
                witnesses = []
                for seed in range(48):
                    grid = MOD.generate(seed, seed * 31 + 5, difficulty=band, scene_profile=profile)
                    actual = MOD.rule_mirror(grid)
                    rival = largest_component_rival(grid)
                    if actual != rival:
                        analysis = MOD._analysis(grid)
                        witnesses.append(
                            (seed, len(analysis["seed_region"]), max(map(len, analysis["unreachable_components"])))
                        )
                self.assertTrue(witnesses, (band, profile))
                self.assertTrue(any(seed_size < decoy_size for _, seed_size, decoy_size in witnesses))

    def test_generated_pocket_profiles_include_multicell_unreachable_chambers(self):
        for band in ("easy", "medium", "hard"):
            for profile in MOD.GENERAL_PROFILES[1:]:
                for seed in range(12):
                    grid = MOD.generate(seed, seed * 37 + 11, difficulty=band, scene_profile=profile)
                    analysis = MOD._analysis(grid)
                    self.assertTrue(
                        any(len(component) >= 2 for component in analysis["unreachable_components"]),
                        (band, profile, seed),
                    )
                    self.assertNotEqual(MOD.rule_mirror(grid), local_neighbor_rival(grid))

    def test_flood_semantics_preservation_and_purity(self):
        for profile in MOD.GENERAL_PROFILES:
            for seed in range(30):
                grid = MOD.generate(seed, seed * 23, scene_profile=profile)
                before = copy.deepcopy(grid)
                analysis = MOD._analysis(grid)
                output = MOD.rule_mirror(grid)
                self.assertEqual(grid, before)
                for row in range(len(grid)):
                    for col in range(len(grid[0])):
                        expected = 8 if (row, col) in analysis["reachable_zeros"] else grid[row][col]
                        self.assertEqual(output[row][col], expected)
                self.assertTrue(all(output[r][c] == 0 for r, c in analysis["unreachable_zeros"]))
                self.assertEqual(output[analysis["seed"][0]][analysis["seed"][1]], 2)

    def test_diagonal_contact_does_not_connect(self):
        grid = [[5] * 7 for _ in range(7)]
        for cell in ((1, 1), (1, 2), (2, 1), (2, 3), (3, 2), (3, 3)):
            grid[cell[0]][cell[1]] = 0
        grid[1][1] = 2
        analysis = MOD._analysis(grid)
        self.assertEqual(analysis["errors"], [])
        self.assertEqual(analysis["pocket_count"], 1)
        output = MOD.rule_mirror(grid)
        self.assertEqual(output[2][1], 8)
        self.assertEqual(output[3][2], 0)

    def test_broad_first_seed_and_extra_barrier_behavior(self):
        grid = MOD.generate(7, 11, scene_profile="one_pocket")
        seed = MOD._analysis(grid)["seed"]
        grid[1][1] = 2
        grid[seed[0]][seed[1]] = 2
        grid[1][2] = 4
        before = copy.deepcopy(grid)
        output = MOD.rule_mirror(grid)
        self.assertEqual(grid, before)
        self.assertEqual(output[1][1], 2)
        self.assertEqual(output[1][2], 4)
        self.assertTrue(MOD.self_check(grid))

    def test_distribution_and_branch_coverage(self):
        profiles = Counter()
        inputs, outputs, shapes, wall_counts, reachable_sizes = set(), set(), set(), set(), set()
        pocket_counts = set()
        seed_smaller = 0
        multi_unreachable = 0
        for seed in range(2400):
            band = ("easy", "medium", "hard")[seed % 3]
            grid = MOD.generate(seed, seed * 29, difficulty=band)
            analysis = MOD._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            profiles[analysis["scene_profile"]] += 1
            inputs.add(tuple(map(tuple, grid)))
            outputs.add(tuple(map(tuple, analysis["output"])))
            shapes.add((len(grid), len(grid[0])))
            wall_counts.add(analysis["wall_count"])
            reachable_sizes.add(len(analysis["reachable_zeros"]))
            pocket_counts.add(analysis["pocket_count"])
            if analysis["unreachable_components"]:
                seed_smaller += len(analysis["seed_region"]) < max(map(len, analysis["unreachable_components"]))
                multi_unreachable += any(len(component) >= 2 for component in analysis["unreachable_components"])
        self.assertEqual(set(profiles), set(MOD.SCENE_PROFILES))
        self.assertGreater(len(inputs), 1700)
        self.assertGreater(len(outputs), 1700)
        self.assertGreater(len(shapes), 60)
        self.assertGreater(len(wall_counts), 120)
        self.assertGreater(len(reachable_sizes), 90)
        self.assertEqual(pocket_counts, set(range(8)))
        self.assertGreater(seed_smaller, 40)
        self.assertGreater(multi_unreachable, 100)

    def test_malformed_and_uncalibrated_inputs(self):
        cases = [[], [[]], [[True]], [[10]], [[5] * 6 for _ in range(6)]]
        ragged = MOD.generate(3, 5, scene_profile="one_pocket")
        ragged[0].pop()
        cases.append(ragged)
        broken_border = MOD.generate(7, 9, scene_profile="two_pockets")
        broken_border[0][0] = 0
        cases.append(broken_border)
        extra_seed = MOD.generate(11, 13, scene_profile="three_pockets")
        extra_seed[1][1] = 2
        cases.append(extra_seed)
        extra_color = MOD.generate(17, 19, scene_profile="four_pockets")
        extra_color[1][1] = 4
        cases.append(extra_color)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)

    def test_override_errors_determinism_fresh_returns_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "maze"}, {"grid_h": 12}):
            with self.assertRaises(ValueError):
                MOD.generate(1, 2, **overrides)
        with self.assertRaises(ValueError):
            MOD.generate(1, 2, difficulty="extreme")
        random.seed(47)
        state = random.getstate()
        first = MOD.generate(17, 23, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MOD.generate(17, 23, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)

    def test_rule_hash_and_base_source_are_synced(self):
        source = canonical_row()["program_solution"]
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(MOD.RULE_HASH, digest)
        base = json.loads(base_path().read_text())
        self.assertEqual(base["racket_target"]["raw_code"], source)
        self.assertEqual(base["racket_target"]["target_code"], source)


if __name__ == "__main__":
    unittest.main()
