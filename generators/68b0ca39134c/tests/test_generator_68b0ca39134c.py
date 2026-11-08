"""Focused regression tests for the largest-component teaching repair."""
from __future__ import annotations

import copy
import importlib.util
import random
import unittest
from pathlib import Path

from scripts.canonical_profile_gate import canonical_pairs

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = (
    ROOT / "puzzle_generators" / "per_puzzle" / "68b0ca39134c" / "generator.py"
)


def load_generator():
    spec = importlib.util.spec_from_file_location("generator_68b0ca39134c", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class LargestComponentGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()
        cls.canonical = canonical_pairs("68b0ca39134c")

    def test_all_canonical_inputs_are_accepted_and_match_strict_profiles(self):
        self.assertEqual(3, len(self.canonical))
        signatures = set()
        for pair in self.canonical:
            grid = pair["input"]
            self.assertEqual([], self.generator.self_check(grid))
            self.assertEqual([], self.generator.strict_canonical_like(grid))
            signatures.add(self.generator.canonical_profile_signature(grid))
        self.assertEqual(self.generator._CANONICAL_SIGNATURES, signatures)

    def test_default_schedule_reaches_every_profile_and_shortcut_witness(self):
        for band in ("easy", "medium", "hard"):
            strict = set()
            leftmost_witnesses = 0
            shared_color_witnesses = 0
            for index in range(120):
                grid = self.generator.generate(index, index, difficulty=band)
                self.assertEqual([], self.generator.self_check(grid, difficulty=band))
                sig = self.generator.canonical_profile_signature(grid)
                if sig in self.generator._CANONICAL_SIGNATURES:
                    strict.add(sig)
                leftmost_witnesses += int(
                    self.generator.SEMANTIC_WITNESSES["largest_not_leftmost"](grid)
                )
                shared_color_witnesses += int(
                    self.generator.SEMANTIC_WITNESSES["largest_color_reused"](grid)
                )
            with self.subTest(band=band):
                self.assertEqual(self.generator._CANONICAL_SIGNATURES, strict)
                self.assertGreaterEqual(leftmost_witnesses, 50)
                self.assertGreaterEqual(shared_color_witnesses, 50)

    def test_boundary_override_cartesian_product_is_exact(self):
        axes = {
            "grid_h": (8, 16),
            "grid_w": (8, 16),
            "component_count": (2, 4),
            "largest_size": (4, 6),
            "color_mode": ("distinct", "shared"),
            "largest_shape_kind": ("compact", "bent"),
        }
        import itertools

        for values in itertools.product(*(axes[name] for name in axes)):
            requested = dict(zip(axes, values))
            grid = self.generator.generate(91, 37, difficulty="easy", **requested)
            self.assertEqual(requested, self.generator.observe_overrides(grid))
            self.assertEqual([], self.generator.self_check(grid))

    def test_checker_rejects_targeted_impostors(self):
        base = self.generator.generate(7, 1, difficulty="medium")
        comps = self.generator._components_4conn(base)
        largest = max(comps, key=lambda comp: len(comp["cells"]))
        small = min(comps, key=lambda comp: len(comp["cells"]))

        single = [[0 for _ in row] for row in base]
        for r, c in largest["cells"]:
            single[r][c] = base[r][c]

        tied = copy.deepcopy(base)
        for r, c in largest["cells"][: len(small["cells"])]:
            tied[r][c] = 0

        mixed = copy.deepcopy(base)
        r, c = largest["cells"][0]
        mixed[r][c] = 9 if base[r][c] != 9 else 8

        invalid = copy.deepcopy(base)
        r, c = small["cells"][0]
        invalid[r][c] = 10

        for name, grid in {
            "single_component": single,
            "largest_tie": tied,
            "multicolor_component": mixed,
            "invalid_color": invalid,
        }.items():
            with self.subTest(name=name):
                self.assertTrue(self.generator.self_check(grid))

    def test_every_three_demo_window_kills_public_fitting_shortcuts(self):
        for band in ("easy", "medium", "hard"):
            for start in range(12):
                pairs = []
                for offset in range(4):
                    grid = self.generator.generate(
                        1000 + start,
                        start + offset,
                        difficulty=band,
                    )
                    pairs.append(
                        {
                            "input": grid,
                            "output": self.generator._authoritative_python(grid),
                        }
                    )
                self.assertEqual(
                    [],
                    self.generator.lesson_identifiable(pairs[:3], pairs[3]),
                    msg=f"band={band} start={start}",
                )

    def test_deterministic_fresh_returns_and_global_rng_isolation(self):
        random.seed(123456)
        before = random.getstate()
        first = self.generator.generate(44, 55, difficulty="hard")
        self.assertEqual(before, random.getstate())
        second = self.generator.generate(44, 55, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = 9
        self.assertNotEqual(first, second)

    def test_unknown_override_rejected_loudly(self):
        with self.assertRaises(TypeError):
            self.generator.generate(1, 2, __override_contract_unknown_axis__=1)


if __name__ == "__main__":
    unittest.main()
