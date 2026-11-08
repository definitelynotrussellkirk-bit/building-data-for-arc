"""Focused semantic regressions for generator ea763f9c5b1d."""
from __future__ import annotations

import copy
import hashlib
import json
import random
import unittest
from reviewer_support import canonical_path, find_root, load_selected_generator


ROOT = find_root(__file__)
TASK_ID = "ea763f9c5b1d"
GENERATOR, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def canonical_row() -> dict:
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"canonical task {TASK_ID} is missing")


def canonical_pairs() -> list[dict]:
    row = canonical_row()
    test = row.get("test") or []
    tests = test if isinstance(test, list) else [test]
    return [*(row.get("train") or []), *tests]


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


class AreaParityGeneratorTests(unittest.TestCase):
    def test_metadata_and_rule_pin_are_current(self):
        row = canonical_row()
        self.assertEqual("3.0.0", GENERATOR.VERSION)
        self.assertEqual("17fac2286cd5", GENERATOR.RULE_HASH)
        self.assertEqual(
            GENERATOR.RULE_HASH,
            normalized_rule_hash(row["program_solution"]),
        )
        self.assertEqual(
            {"grid_h", "grid_w", "n_blobs", "input_color"},
            set(GENERATOR.AXES),
        )

    def test_all_canonical_pairs_are_positive_controls_and_exact(self):
        pairs = canonical_pairs()
        self.assertEqual(5, len(pairs))
        signatures = set()
        for index, pair in enumerate(pairs):
            source = copy.deepcopy(pair["input"])
            with self.subTest(index=index):
                self.assertEqual([], GENERATOR.self_check(source))
                self.assertEqual(pair["output"], GENERATOR.rule_mirror(source))
                self.assertEqual(pair["input"], source)
                signatures.add(GENERATOR.canonical_profile_signature(source))
        self.assertEqual(GENERATOR._CANONICAL_SIGNATURES, signatures)

    def test_boundary_overrides_are_exact_and_observable_in_every_band(self):
        cases = (
            (7, 8, 2, 1),
            (7, 14, 5, 9),
            (14, 8, 5, 1),
            (14, 14, 2, 9),
        )
        for band in ("easy", "medium", "hard"):
            for seed, case in enumerate(cases, start=20):
                height, width, count, color = case
                with self.subTest(band=band, case=case):
                    grid = GENERATOR.generate(
                        seed,
                        seed * 17,
                        difficulty=band,
                        grid_h=height,
                        grid_w=width,
                        n_blobs=count,
                        input_color=color,
                    )
                    expected = {
                        "grid_h": height,
                        "grid_w": width,
                        "n_blobs": count,
                        "input_color": color,
                    }
                    self.assertEqual(expected, GENERATOR.observe_overrides(grid))
                    self.assertEqual([], GENERATOR.self_check(grid, meta=expected))

    def test_default_prior_reaches_every_linked_profile_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            counts = {signature: 0 for signature in GENERATOR._CANONICAL_SIGNATURES}
            for seed in range(900):
                grid = GENERATOR.generate(seed, seed * 13 + 1, difficulty=band)
                self.assertEqual([], GENERATOR.self_check(grid))
                signature = GENERATOR.canonical_profile_signature(grid)
                if signature in counts:
                    counts[signature] += 1
            with self.subTest(band=band, counts=counts):
                self.assertGreaterEqual(sum(counts.values()), 200)
                self.assertTrue(all(count > 0 for count in counts.values()))

    def test_all_generalized_count_and_color_values_are_reachable(self):
        counts, colors = set(), set()
        for band in ("easy", "medium", "hard"):
            for seed in range(500):
                grid = GENERATOR.generate(10000 + seed, seed * 19, difficulty=band)
                observed = GENERATOR.observe_overrides(grid)
                counts.add(observed["n_blobs"])
                colors.add(observed["input_color"])
        self.assertEqual({2, 3, 4, 5}, counts)
        self.assertEqual(set(range(1, 10)), colors)

    def test_generation_is_deterministic_fresh_and_global_rng_pure(self):
        random.seed(9173)
        state = random.getstate()
        first = GENERATOR.generate(31, 47, difficulty="hard")
        snapshot = copy.deepcopy(first)
        second = GENERATOR.generate(31, 47, difficulty="hard")
        self.assertEqual(state, random.getstate())
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        first[0][0] = 9
        self.assertEqual(snapshot, GENERATOR.generate(31, 47, difficulty="hard"))

    def test_self_check_rejects_each_minimal_impostor_class(self):
        blank = [[0] * 8 for _ in range(7)]
        singleton = copy.deepcopy(blank)
        singleton[2][2] = 6
        all_odd = copy.deepcopy(blank)
        for row, col in ((1, 1), (1, 2), (2, 1), (4, 5), (4, 6), (5, 5)):
            all_odd[row][col] = 6
        all_even = copy.deepcopy(blank)
        for row, col in ((1, 1), (1, 2), (4, 5), (4, 6)):
            all_even[row][col] = 6
        two_colors = copy.deepcopy(blank)
        for row, col in ((1, 1), (1, 2), (2, 1)):
            two_colors[row][col] = 6
        for row, col in ((4, 5), (4, 6)):
            two_colors[row][col] = 2
        oversized = copy.deepcopy(blank)
        for row, col in (
            (1, 1), (1, 2), (1, 3), (2, 1),
            (2, 2), (2, 3), (3, 1), (3, 2),
            (5, 5), (5, 6),
        ):
            oversized[row][col] = 6

        probes = {
            "all_background": blank,
            "singleton": singleton,
            "all_odd": all_odd,
            "all_even": all_even,
            "two_colors": two_colors,
            "oversized": oversized,
        }
        for name, grid in probes.items():
            with self.subTest(name=name):
                self.assertTrue(GENERATOR.self_check(grid))


if __name__ == "__main__":
    unittest.main()
