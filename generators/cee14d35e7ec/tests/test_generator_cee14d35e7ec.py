"""Focused distribution and rival-rule tests for generator cee14d35e7ec."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "shared/runtime"))
MODULE_PATH = REPO / "generators/cee14d35e7ec/generator.py"
SPEC = importlib.util.spec_from_file_location("generator_cee14d35e7ec", MODULE_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

EXPECTED_PROFILES = (
    "canonical_upper",
    "canonical_lower",
    "mixed_sides",
    "diagonal_context",
    "occupied_pairs",
)


def pair_stats(grid):
    n = len(grid)
    one_sided = []
    occupied_same = []
    occupied_different = []
    for r in range(n):
        for c in range(r + 1, n):
            upper, lower = grid[r][c], grid[c][r]
            if bool(upper) ^ bool(lower):
                one_sided.append(
                    {
                        "pair": (r, c),
                        "side": "upper" if upper else "lower",
                        "color": upper or lower,
                        "distance": c - r,
                    }
                )
            elif upper and lower:
                target = occupied_same if upper == lower else occupied_different
                target.append(((r, c), upper, lower))
    diagonal = [(i, grid[i][i]) for i in range(n) if grid[i][i]]
    return {
        "one_sided": one_sided,
        "occupied_same": occupied_same,
        "occupied_different": occupied_different,
        "diagonal": diagonal,
    }


def conditional_transpose_fill(grid):
    """Independent executable statement of the canonical Racket rule."""
    n = len(grid)
    return [
        [grid[c][r] if grid[r][c] == 0 and grid[c][r] != 0 else grid[r][c]
         for c in range(n)]
        for r in range(n)
    ]


class GeneratorCee14d35e7ecTests(unittest.TestCase):
    def test_explicit_profiles_cover_semantically_distinct_rule_branches(self):
        self.assertEqual(tuple(GEN.SCENE_PROFILES), EXPECTED_PROFILES)
        rendered = {}
        for index, profile in enumerate(EXPECTED_PROFILES):
            kwargs = {
                "difficulty": "medium",
                "grid_size": 8,
                "source_pairs": 5,
                "scene_profile": profile,
            }
            grid = GEN.generate(700 + index, 91, **kwargs)
            self.assertEqual(grid, GEN.generate(700 + index, 91, **kwargs))
            self.assertEqual(GEN.self_check(grid), [])
            self.assertEqual(
                GEN.observe_overrides(grid),
                {
                    "grid_size": 8,
                    "source_pairs": 5,
                    "scene_profile": profile,
                },
            )
            stats = pair_stats(grid)
            self.assertEqual(len(stats["one_sided"]), 5)
            self.assertIn(1, {item["distance"] for item in stats["one_sided"]})
            self.assertTrue(
                any(item["distance"] >= 4 for item in stats["one_sided"]),
                profile,
            )
            self.assertTrue(
                any(r == 0 or c == 7 for r, c in
                    (item["pair"] for item in stats["one_sided"])),
                profile,
            )
            transformed = conditional_transpose_fill(grid)
            self.assertNotEqual(transformed, grid)
            rendered[profile] = stats

        self.assertEqual(
            {item["side"] for item in rendered["canonical_upper"]["one_sided"]},
            {"upper"},
        )
        self.assertEqual(
            {item["side"] for item in rendered["canonical_lower"]["one_sided"]},
            {"lower"},
        )
        for profile in ("mixed_sides", "diagonal_context", "occupied_pairs"):
            self.assertEqual(
                {item["side"] for item in rendered[profile]["one_sided"]},
                {"upper", "lower"},
                profile,
            )
        self.assertEqual(len(rendered["diagonal_context"]["diagonal"]), 2)
        self.assertFalse(rendered["diagonal_context"]["occupied_same"])
        self.assertFalse(rendered["diagonal_context"]["occupied_different"])
        self.assertTrue(rendered["occupied_pairs"]["occupied_same"])
        self.assertTrue(rendered["occupied_pairs"]["occupied_different"])
        self.assertFalse(rendered["occupied_pairs"]["diagonal"])

    def test_default_cohort_varies_counts_positions_sides_and_profiles(self):
        profiles = set()
        one_sided_counts = set()
        nonzero_counts = set()
        occupied_different_seen = False
        all_inputs = set()
        all_pairs = set()
        for seed in range(120):
            difficulty = ("easy", "medium", "hard")[seed % 3]
            grid = GEN.generate(seed, seed * 17 + 5, difficulty=difficulty)
            self.assertEqual(GEN.self_check(grid), [])
            observed = GEN.observe_overrides(grid)
            profiles.add(observed["scene_profile"])
            stats = pair_stats(grid)
            one_sided_counts.add(len(stats["one_sided"]))
            nonzero_counts.add(sum(cell != 0 for row in grid for cell in row))
            occupied_different_seen |= bool(stats["occupied_different"])
            all_pairs.update(item["pair"] for item in stats["one_sided"])
            all_inputs.add(tuple(tuple(row) for row in grid))
        self.assertEqual(profiles, set(EXPECTED_PROFILES))
        self.assertGreaterEqual(len(one_sided_counts), 4)
        self.assertGreaterEqual(len(nonzero_counts), 6)
        self.assertTrue(occupied_different_seen)
        self.assertGreaterEqual(len(all_pairs), 30)
        self.assertGreaterEqual(len(all_inputs), 115)

    def test_four_demo_schedule_falsifies_named_shortcuts(self):
        self.assertEqual(GEN.RULE_HASH, "5d70cc8bc723")
        expected_rivals = {
            "transpose_only",
            "upper_only_completion",
            "lower_only_completion",
            "prefer_upper_on_conflict",
            "prefer_lower_on_conflict",
        }
        self.assertEqual(set(GEN.SEMANTIC_RIVALS), expected_rivals)
        self.assertEqual(GEN.EXAMPLES_NEEDED, 4)

        for start in range(len(GEN.SCHEDULE_PROFILES)):
            lesson = []
            for offset in range(5):
                grid = GEN.generate(8800 + start, start + offset)
                lesson.append(
                    {"input": grid, "output": conditional_transpose_fill(grid)}
                )
            demos, query = lesson[:4], lesson[4]
            self.assertEqual(GEN.lesson_identifiable(demos, query), [], start)
            for name, rival in GEN.SEMANTIC_RIVALS.items():
                self.assertTrue(
                    any(rival(pair["input"]) != pair["output"] for pair in demos),
                    f"{name} survives schedule window {start}",
                )

        probe = GEN.generate(42, 0, scene_profile="canonical_upper")
        self.assertEqual(GEN.rule_mirror(probe), conditional_transpose_fill(probe))
        self.assertNotEqual(GEN.self_check(conditional_transpose_fill(probe)), [])

    def test_override_contract_and_invalid_inputs_are_loud(self):
        for profile in EXPECTED_PROFILES:
            grid = GEN.generate(
                3,
                4,
                grid_size=6,
                source_pairs=3,
                scene_profile=profile,
            )
            self.assertEqual(
                GEN.observe_overrides(grid),
                {
                    "grid_size": 6,
                    "source_pairs": 3,
                    "scene_profile": profile,
                },
            )
        with self.assertRaises((TypeError, ValueError)):
            GEN.generate(1, 2, bogus_axis=1)
        with self.assertRaises((TypeError, ValueError)):
            GEN.generate(1, 2, scene_profile="unknown")
        with self.assertRaises((TypeError, ValueError)):
            GEN.generate(1, 2, grid_size=5)
        with self.assertRaises((TypeError, ValueError)):
            GEN.generate(1, 2, source_pairs=7)
        with self.assertRaises((TypeError, ValueError)):
            GEN.generate(1, 2, difficulty="extreme")


if __name__ == "__main__":
    unittest.main()
