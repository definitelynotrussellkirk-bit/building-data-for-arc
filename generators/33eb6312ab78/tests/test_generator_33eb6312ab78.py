from __future__ import annotations

import copy
import importlib
import json
import random
import unittest
from pathlib import Path

from puzzle_generators import base


generator = importlib.import_module(
    "puzzle_generators.per_puzzle.33eb6312ab78.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def canonical_pairs():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != generator.TASK_ID:
                continue
            for pair in row.get("train") or []:
                yield pair
            test = row.get("test")
            if isinstance(test, dict):
                yield test
            else:
                yield from test or []


def replace_header_count(grid, n):
    out = copy.deepcopy(grid)
    out[0] = [0] * len(out[0])
    out[0][:n] = [1] * n
    return out


class Generator33eb6312ab78Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.canonical = list(canonical_pairs())

    def test_rule_hash_and_all_canonical_pairs(self):
        self.assertEqual(generator.RULE_HASH, "282a32f858ab")
        self.assertEqual(len(self.canonical), 3)
        match_counts = []
        for pair in self.canonical:
            before = copy.deepcopy(pair["input"])
            self.assertEqual(generator.self_check(pair["input"]), [])
            self.assertEqual(generator.strict_canonical_like(pair["input"]), [])
            self.assertEqual(generator.oracle_output(pair["input"]), pair["output"])
            self.assertEqual(pair["input"], before)
            match_counts.append(len(generator._analysis(pair["input"])[2]))
        self.assertEqual(sorted(match_counts), [1, 1, 2])

    def test_canonical_tie_selects_first_row_major_match(self):
        pair = self.canonical[0]
        _n, _components, matches = generator._analysis(pair["input"])
        self.assertEqual(len(matches), 2)
        self.assertLess(min(matches[0]["cells"]), min(matches[1]["cells"]))
        self.assertEqual(generator.oracle_output(pair["input"]), generator._crop_boundary(matches[0]))
        self.assertNotEqual(generator.oracle_output(pair["input"]), generator._crop_boundary(matches[1]))

    def test_default_draws_are_exact_and_provenance_complete(self):
        for band in ("easy", "medium", "hard"):
            for offset in range(160):
                captured = []
                base.set_ctx_observer(captured.append)
                try:
                    grid = generator.generate(
                        10_000 + offset,
                        offset * 31 + 7,
                        difficulty=band,
                    )
                finally:
                    base.set_ctx_observer(None)
                self.assertEqual(generator.self_check(grid), [])
                self.assertEqual(generator.observe_overrides(grid), captured[-1].recorded_draws())
                self.assertEqual(set(captured[-1].recorded_draws()), set(generator.AXES))

    def test_override_boundaries_are_accepted_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for h in (6, 13):
                for w in (12, 18):
                    for n in (4, 10):
                        grid = generator.generate(
                            91,
                            117,
                            difficulty=band,
                            grid_h=h,
                            grid_w=w,
                            n_ones=n,
                        )
                        self.assertEqual(generator.self_check(grid), [])
                        self.assertEqual(
                            generator.observe_overrides(grid),
                            {"grid_h": h, "grid_w": w, "n_ones": n},
                        )

    def test_bad_overrides_are_rejected(self):
        bad_calls = (
            {"difficulty": "expert"},
            {"bogus": 1},
            {"grid_h": 5},
            {"grid_h": 14},
            {"grid_w": 11},
            {"grid_w": 19},
            {"n_ones": 3},
            {"n_ones": 11},
            {"n_ones": "four"},
        )
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(0, 0, **kwargs)

    def test_four_sample_schedule_covers_every_semantic_branch(self):
        expected = {
            "unique_match",
            "two_matches_first_wins",
            "selected_object_has_interior",
            "selected_object_all_boundary",
            "same_area_wrong_boundary_decoy",
            "larger_area_decoy",
        }
        for band in ("easy", "medium", "hard"):
            fired = set()
            for sample_index in range(4):
                grid = generator.generate(314159, sample_index, difficulty=band)
                fired.update(
                    name
                    for name, witness in generator.SEMANTIC_WITNESSES.items()
                    if witness(grid)
                )
            self.assertEqual(fired, expected)

    def test_four_demo_lessons_rule_out_declared_shortcuts(self):
        for band in ("easy", "medium", "hard"):
            for seed in range(60):
                demos = []
                for sample_index in range(4):
                    grid = generator.generate(seed, sample_index, difficulty=band)
                    demos.append({"input": grid, "output": generator.oracle_output(grid)})
                query_grid = generator.generate(seed, 4, difficulty=band)
                query = {"input": query_grid, "output": generator.oracle_output(query_grid)}
                self.assertEqual(generator.lesson_identifiable(demos, query), [])

    def test_target_slot_and_color_are_not_shortcuts(self):
        target_slots = set()
        target_colors = set()
        for seed in range(240):
            grid = generator.generate(seed, seed * 13 + 1, difficulty="hard")
            _n, components, matches = generator._analysis(grid)
            target_slots.add(components.index(matches[0]))
            target_colors.add(matches[0]["color"])
        self.assertEqual(target_slots, {0, 1, 2})
        self.assertGreaterEqual(len(target_colors), 7)

    def test_self_check_rejects_targeted_impostors(self):
        valid = generator.generate(777, 3, difficulty="medium")
        _n, components, _matches = generator._analysis(valid)
        mutations = {}

        missing_header = copy.deepcopy(valid)
        missing_header[0] = [0] * len(missing_header[0])
        mutations["missing_header"] = missing_header

        noncontiguous = copy.deepcopy(valid)
        n = generator.observe_overrides(valid)["n_ones"]
        noncontiguous[0] = [0] * len(noncontiguous[0])
        for c in range(n - 1):
            noncontiguous[0][c] = 1
        noncontiguous[0][n] = 1
        mutations["noncontiguous_header"] = noncontiguous

        body_marker = copy.deepcopy(valid)
        placed = False
        for r in range(1, len(body_marker)):
            for c in range(len(body_marker[0])):
                if body_marker[r][c] == 0:
                    body_marker[r][c] = 1
                    placed = True
                    break
            if placed:
                break
        mutations["body_marker"] = body_marker

        missing_component = copy.deepcopy(valid)
        for r, c in components[-1]["cells"]:
            missing_component[r][c] = 0
        mutations["only_two_components"] = missing_component

        duplicate_color = copy.deepcopy(valid)
        replacement = components[0]["color"]
        for r, c in components[1]["cells"]:
            duplicate_color[r][c] = replacement
        mutations["duplicate_component_colors"] = duplicate_color

        counts = {generator._boundary_count(obj["cells"]) for obj in components}
        absent = next(value for value in range(4, 11) if value not in counts)
        mutations["no_boundary_match"] = replace_header_count(valid, absent)

        for name, mutation in mutations.items():
            with self.subTest(name=name):
                self.assertTrue(generator.self_check(mutation), mutation)

    def test_deterministic_fresh_and_global_rng_isolated(self):
        random.seed(9981)
        state = random.getstate()
        first = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = generator.generate(19, 31, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))

    def test_two_disjoint_ranges_are_stable_and_diverse(self):
        signatures = []
        for start in (0, 50_000):
            pairs = set()
            witnesses = {name: 0 for name in generator.SEMANTIC_WITNESSES}
            n_values = set()
            for offset in range(240):
                seed = start + offset
                grid = generator.generate(seed, seed * 17 + 3, difficulty="medium")
                output = generator.oracle_output(grid)
                pairs.add((tuple(map(tuple, grid)), tuple(map(tuple, output))))
                n_values.add(generator.observe_overrides(grid)["n_ones"])
                for name, witness in generator.SEMANTIC_WITNESSES.items():
                    witnesses[name] += bool(witness(grid))
            self.assertGreaterEqual(len(pairs), 225)
            self.assertEqual(n_values, set(range(4, 11)))
            self.assertTrue(all(count > 0 for count in witnesses.values()))
            signatures.append((n_values, set(witnesses)))
        self.assertEqual(signatures[0], signatures[1])


if __name__ == "__main__":
    unittest.main()
