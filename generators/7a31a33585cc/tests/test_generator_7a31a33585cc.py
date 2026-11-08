"""Focused semantic regressions for generator 7a31a33585cc."""

from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import random
import unittest

from puzzle_generators.runner import _load_generator_module


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "7a31a33585cc"
BASE_PATH = (
    ROOT
    / "data/base/solutions/banks/b64eb6bd4039/H57__7a31a33585cc.json"
)
TRANSFORMS = ("rot90", "rot180", "rot270", "flip_h", "flip_v", "transpose", "anti")


def canonical_rows():
    return [
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    ]


def canonical_pairs():
    pairs = []
    for row in canonical_rows():
        pairs.extend(row.get("train") or [])
        test = row.get("test")
        if isinstance(test, dict):
            pairs.append(test)
        elif isinstance(test, list):
            pairs.extend(test)
    return pairs


def normalized_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def transform(grid, kind):
    g = [row[:] for row in grid]
    if kind == "rot90":
        return [list(row) for row in zip(*g[::-1])]
    if kind == "rot180":
        return [row[::-1] for row in g[::-1]]
    if kind == "rot270":
        return [list(row) for row in zip(*g)][::-1]
    if kind == "flip_h":
        return [row[::-1] for row in g]
    if kind == "flip_v":
        return [row[:] for row in g[::-1]]
    if kind == "transpose":
        return [list(row) for row in zip(*g)]
    if kind == "anti":
        h, w = len(g), len(g[0])
        return [
            [g[h - 1 - c][w - 1 - r] for c in range(h)]
            for r in range(w)
        ]
    raise KeyError(kind)


def split_panels(grid):
    h = len(grid)
    return tuple(
        [row[left:left + h] for row in grid]
        for left in (0, h + 1, 2 * h + 2)
    )


def effective_matches(a, b):
    return [kind for kind in TRANSFORMS if transform(a, kind) == b]


class Generator7A31A33585CCTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = _load_generator_module(TASK_ID)

    def test_all_canonical_pairs_are_accepted_and_answer_unique(self):
        pairs = canonical_pairs()
        self.assertEqual(len(canonical_rows()), 1)
        self.assertEqual(len(pairs), 3)
        for index, pair in enumerate(pairs):
            with self.subTest(pair=index):
                grid = copy.deepcopy(pair["input"])
                self.assertEqual(self.module.self_check(grid), [])
                a, b, c = split_panels(grid)
                candidates = effective_matches(a, b)
                self.assertEqual(len(candidates), 1)
                self.assertEqual(transform(c, candidates[0]), pair["output"])
                self.assertEqual(grid, pair["input"])

    def test_rule_hash_and_task_local_target_are_pinned_to_canonical(self):
        rows = canonical_rows()
        canonical = rows[0]["program_solution"]
        base = json.loads(BASE_PATH.read_text())
        target = base["racket_target"]["target_code"]
        self.assertEqual(normalized_hash(canonical), "dc0383bfad5f")
        self.assertEqual(self.module.RULE_HASH, normalized_hash(canonical))
        self.assertEqual(target, canonical)

    def test_every_declared_axis_boundary_and_transform_branch(self):
        observed_transforms = set()
        for h in (5, 7):
            for count in (2, 3):
                for profile in self.module.COMPONENT_PROFILES:
                    for kind in self.module.TRANSFORMS:
                        with self.subTest(h=h, count=count, profile=profile, kind=kind):
                            grid = self.module.generate(
                                410_000 + h * 100 + count,
                                73 + len(observed_transforms),
                                difficulty="medium",
                                grid_h=h,
                                objects_per_panel=count,
                                transform=kind,
                                component_profile=profile,
                            )
                            observed = self.module.observe_overrides(grid)
                            self.assertEqual(
                                observed,
                                {
                                    "grid_h": h,
                                    "objects_per_panel": count,
                                    "transform": kind,
                                    "component_profile": profile,
                                },
                            )
                            self.assertEqual(self.module.self_check(grid), [])
                            a, b, c = split_panels(grid)
                            self.assertEqual(effective_matches(a, b), [kind])
                            self.assertNotEqual(transform(c, kind), c)
                            observed_transforms.add(kind)
        self.assertEqual(observed_transforms, set(TRANSFORMS))

    def test_default_prior_is_structurally_valid_and_varied_in_all_bands(self):
        all_branches = set()
        all_profiles = set()
        for band_index, band in enumerate(("easy", "medium", "hard")):
            inputs = set()
            outputs = set()
            branch_counts = Counter()
            for index in range(120):
                grid = self.module.generate(
                    520_000 + band_index * 10_000 + index,
                    index * 31 + band_index,
                    difficulty=band,
                )
                analysis = self.module._analysis(grid)
                self.assertEqual(analysis["errors"], [])
                observed = self.module.observe_overrides(grid)
                branch_counts[observed["transform"]] += 1
                all_branches.add(observed["transform"])
                all_profiles.add(observed["component_profile"])
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, analysis["facts"]["output"])))
            self.assertGreaterEqual(len(inputs), 118)
            self.assertGreaterEqual(len(outputs), 116)
            self.assertEqual(set(branch_counts), set(TRANSFORMS))
        self.assertEqual(all_branches, set(TRANSFORMS))
        self.assertEqual(all_profiles, set(self.module.COMPONENT_PROFILES))

    def test_self_check_rejects_targeted_semantic_impostors(self):
        base = self.module.generate(
            610_001,
            77,
            difficulty="hard",
            grid_h=7,
            objects_per_panel=3,
            transform="rot90",
            component_profile="canonical_mixed",
        )
        h = len(base)
        a, b, c = split_panels(base)

        broken_separator = copy.deepcopy(base)
        broken_separator[0][h] = 0

        identity_demo = self.module._compose_panels((a, a, c))

        novel_b = copy.deepcopy(b)
        present = {value for row in base for value in row}
        novel_color = next(color for color in range(1, 9) if color not in present)
        br, bc = next(
            (r, col)
            for r, row in enumerate(novel_b)
            for col, value in enumerate(row)
            if value != 0
        )
        novel_b[br][bc] = novel_color
        palette_mismatch = self.module._compose_panels((a, novel_b, c))

        overlap_c = copy.deepcopy(c)
        a_color = next(value for row in a for value in row if value != 0)
        c_color = next(value for row in c for value in row if value != 0)
        overlap_c = [
            [a_color if value == c_color else value for value in row]
            for row in overlap_c
        ]
        palette_overlap = self.module._compose_panels((a, b, overlap_c))

        empty_query = self.module._compose_panels(
            (a, b, [[0] * h for _ in range(h)])
        )

        impostors = {
            "broken_separator": broken_separator,
            "identity_demo": identity_demo,
            "novel_B_palette": palette_mismatch,
            "AB_C_palette_overlap": palette_overlap,
            "empty_query": empty_query,
        }
        for name, grid in impostors.items():
            with self.subTest(name=name):
                self.assertTrue(self.module.self_check(grid))

    def test_negative_recombination_is_rejected_without_hiding_the_transform(self):
        lesson = self.module.generate(
            720_001,
            9,
            difficulty="easy",
            grid_h=5,
            objects_per_panel=2,
            transform="flip_v",
            component_profile="canonical_mixed",
        )
        donor = self.module.generate(
            720_002,
            10,
            difficulty="medium",
            grid_h=5,
            objects_per_panel=3,
            transform="rot180",
            component_profile="canonical_mixed",
        )
        a, b, _ = split_panels(lesson)
        _, _, donor_c = split_panels(donor)
        remaining_colors = {value for panel in (a, b) for row in panel for value in row if value}
        donor_colors = sorted({value for row in donor_c for value in row if value})
        replacement_colors = [color for color in range(1, 9) if color not in remaining_colors][:3]
        recolor = dict(zip(donor_colors, replacement_colors))
        replacement_c = [
            [recolor.get(value, value) for value in row]
            for row in donor_c
        ]
        recombined = self.module._compose_panels((a, b, replacement_c))

        replacement_palette = {value for row in replacement_c for value in row if value}
        self.assertFalse(replacement_palette & remaining_colors)
        errors = self.module.self_check(recombined)
        self.assertTrue(any("object counts" in error for error in errors))
        self.assertEqual(effective_matches(a, b), ["flip_v"])
        self.assertEqual(
            self.module._analysis(recombined)["facts"]["output"],
            transform(replacement_c, "flip_v"),
        )

    def test_determinism_fresh_returns_global_rng_and_invalid_calls(self):
        random.seed(314_159)
        state = random.getstate()
        kwargs = {
            "difficulty": "hard",
            "grid_h": 7,
            "objects_per_panel": 3,
            "transform": "anti",
            "component_profile": "polyomino",
        }
        first = self.module.generate(830_001, 901, **kwargs)
        second = self.module.generate(830_001, 901, **kwargs)
        self.assertEqual(random.getstate(), state)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))
        first[0][0] = 8 if first[0][0] == 0 else 0
        self.assertEqual(second, self.module.generate(830_001, 901, **kwargs))
        with self.assertRaisesRegex(ValueError, "unknown difficulty"):
            self.module.generate(0, 0, difficulty="extreme")
        with self.assertRaisesRegex(ValueError, "unknown override"):
            self.module.generate(0, 0, nonexistent_axis=True)
        with self.assertRaises(ValueError):
            self.module.generate(0, 0, grid_h=4)
        with self.assertRaises(ValueError):
            self.module.generate(0, 0, transform="identity")


if __name__ == "__main__":
    unittest.main()
