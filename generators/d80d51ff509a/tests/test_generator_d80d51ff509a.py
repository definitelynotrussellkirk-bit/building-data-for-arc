"""Focused regressions for the ranked-component transform generator."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "d80d51ff509a"


def generator():
    return importlib.import_module(
        "puzzle_generators.per_puzzle.d80d51ff509a.generator"
    )


def canonical_row():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"canonical task {TASK_ID} is missing")


class RankedComponentGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gen = generator()
        row = canonical_row()
        cls.pairs = [*row["train"], *row["test"]]
        cls.rule = row["program_solution"]

    def test_all_official_inputs_match_linked_profiles_and_self_check(self):
        signatures = tuple(
            self.gen.canonical_profile_signature(pair["input"])
            for pair in self.pairs
        )
        self.assertEqual(self.gen._CANONICAL_SIGNATURES, signatures)
        for pair in self.pairs:
            self.assertEqual([], self.gen.self_check(pair["input"]))
        tied = self.gen._components(self.pairs[-1]["input"])
        self.assertEqual([3, 5, 5], [component["size"] for component in tied])
        self.assertEqual(9, tied[1]["color"])

    def test_default_prior_reaches_every_complete_profile_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            counts = {name: 0 for name in self.gen._PROFILE_NAMES}
            for seed in range(600):
                grid = self.gen.generate(seed, seed * 17 + 3, difficulty=band)
                self.assertEqual([], self.gen.self_check(grid, difficulty=band))
                profile = self.gen.observe_overrides(grid)["profile_kind"]
                if profile in counts:
                    counts[profile] += 1
            with self.subTest(band=band, counts=counts):
                self.assertEqual(240, sum(counts.values()))
                self.assertTrue(all(count > 0 for count in counts.values()))

    def test_generalized_branch_is_an_explicit_non_replay_witness(self):
        for band in ("easy", "medium", "hard"):
            grid = self.gen.generate(
                19,
                41,
                difficulty=band,
                profile_kind="generalized",
                grid_h=12,
                grid_w=16,
            )
            self.assertEqual((12, 16), (len(grid), len(grid[0])))
            self.assertEqual([], self.gen.self_check(grid, difficulty=band))
            self.assertIn(len(self.gen._components(grid)), (4, 5))
            self.assertEqual(
                "generalized", self.gen.observe_overrides(grid)["profile_kind"]
            )

    def test_cross_profile_recombination_is_not_mislabeled_as_official(self):
        grid = self.gen.generate(
            7,
            9,
            profile_kind="canonical_0",
            grid_h=9,
            grid_w=14,
        )
        impostor = copy.deepcopy(grid)
        impostor[0][-1] = 7  # transform from profile 2; absent from profile 0
        self.assertEqual([], self.gen.self_check(impostor))
        self.assertEqual(
            "generalized", self.gen.observe_overrides(impostor)["profile_kind"]
        )
        self.assertNotIn(
            self.gen.canonical_profile_signature(impostor),
            self.gen._CANONICAL_SIGNATURES,
        )

    def test_exact_overrides_are_observable_or_reject_loudly(self):
        grid = self.gen.generate(
            3,
            7,
            difficulty="hard",
            profile_kind="canonical_3",
            grid_h=9,
            grid_w=15,
        )
        self.assertEqual(
            {"grid_h": 9, "grid_w": 15, "profile_kind": "canonical_3"},
            self.gen.observe_overrides(grid),
        )
        with self.assertRaisesRegex(ValueError, "override|options"):
            self.gen.generate(
                3,
                7,
                profile_kind="canonical_3",
                grid_h=10,
            )

    def test_self_check_rejects_targeted_impostors(self):
        base = self.gen.generate(
            11,
            13,
            profile_kind="canonical_1",
            grid_h=10,
            grid_w=15,
        )
        mutations = []
        crop = [row[:] for row in base[:8]]
        mutations.append(crop)
        bad_key = copy.deepcopy(base)
        bad_key[0][-1] = 3
        mutations.append(bad_key)
        dirty_header = copy.deepcopy(base)
        dirty_header[0][4] = 2
        mutations.append(dirty_header)
        reused = copy.deepcopy(base)
        component = self.gen._components(reused)[0]
        for r, c in component["cells"]:
            reused[r][c] = reused[0][0]
        mutations.append(reused)
        touching = copy.deepcopy(base)
        first, second = self.gen._components(touching)[:2]
        r, c = first["cells"][0]
        candidates = [
            (r + dr, c + dc)
            for dr, dc in self.gen._CARDINALS
            if 1 <= r + dr < len(touching)
            and 0 <= c + dc < len(touching[0])
            and touching[r + dr][c + dc] == 0
        ]
        self.assertTrue(candidates)
        nr, nc = candidates[0]
        touching[nr][nc] = second["color"]
        mutations.append(touching)
        for mutation in mutations:
            self.assertTrue(self.gen.self_check(mutation), mutation)


    def test_selected_crop_never_contains_another_component_color(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(150):
                grid = self.gen.generate(70000 + seed, 90000 + seed * 19, difficulty=band)
                components = self.gen._components(grid)
                selected = components[grid[0][0] - 1]
                r0, c0, r1, c1 = selected["bbox"]
                values = {
                    grid[r][c]
                    for r in range(r0, r1 + 1)
                    for c in range(c0, c1 + 1)
                }
                self.assertLessEqual(values, {0, selected["color"]})

    def test_rule_hash_and_selected_authority_are_pinned(self):
        normalized = " ".join(self.rule.split())
        expected = hashlib.sha256(normalized.encode()).hexdigest()[:12]
        self.assertEqual(expected, self.gen.RULE_HASH)
        bank = json.loads(
            (
                ROOT
                / "data/base/solutions/banks/037ff40eee92"
                / "hard_m07__d80d51ff509a.json"
            ).read_text()
        )
        self.assertEqual(self.rule, bank["racket_target"]["target_code"])
        self.assertEqual(
            "preserved_executable_source",
            bank["racket_target"]["canonicalization_status"],
        )

    def test_replay_is_fresh_deterministic_and_global_rng_neutral(self):
        before = random.getstate()
        first = self.gen.generate(101, 23, difficulty="medium")
        middle = self.gen.generate(202, 24, difficulty="hard")
        second = self.gen.generate(101, 23, difficulty="medium")
        after = random.getstate()
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        self.assertNotEqual(first, middle)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
