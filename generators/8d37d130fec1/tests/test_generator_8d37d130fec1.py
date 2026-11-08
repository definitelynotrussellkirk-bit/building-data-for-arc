from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import unittest
from collections import Counter
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "8d37d130fec1"
GENERATOR = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = find_root(__file__)
DATA_ROOT = canonical_path(ROOT).parent.parent


def canonical_rows():
    return [
        json.loads(line)
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    ]


def occurrences():
    return canonical_pairs(TASK_ID, root=ROOT)


def unique_pairs():
    result = {}
    for pair in occurrences():
        result.setdefault(tuple(map(tuple, pair["input"])), pair)
    return list(result.values())


class GeneratorTests(unittest.TestCase):
    def test_all_canonical_occurrences_match_rule(self):
        self.assertEqual(len(canonical_rows()), 2)
        self.assertEqual(len(occurrences()), 8)
        for pair in occurrences():
            self.assertEqual(
                GENERATOR.rule_mirror(pair["input"]), pair["output"]
            )

    def test_exact_public_profiles_cover_unique_inputs(self):
        pairs = unique_pairs()
        self.assertEqual(len(pairs), 4)
        for profile, pair in zip(GENERATOR.PUBLIC_PROFILES, pairs):
            self.assertEqual(
                GENERATOR.canonical_profile_signature(pair["input"]), profile
            )
            generated = GENERATOR.generate(7, 11, scene_profile=profile)
            self.assertEqual(generated, pair["input"])
            self.assertIsNot(generated, GENERATOR._PUBLIC_INPUTS[profile])

    def test_general_profiles_are_exact_and_observable(self):
        for band in ("easy", "medium", "hard"):
            for profile, spec in GENERATOR.GENERAL_SPECS.items():
                glyph_count, selected_index, selected_mask, ambiguous = spec
                for seed in range(30):
                    grid = GENERATOR.generate(
                        seed, seed * 29, difficulty=band,
                        scene_profile=profile,
                    )
                    analysis = GENERATOR._analysis(grid)
                    self.assertEqual(analysis["errors"], [])
                    self.assertEqual(len(analysis["top_glyphs"]), glyph_count)
                    self.assertEqual(analysis["selected_index"], selected_index)
                    self.assertEqual(analysis["selected_mask"], selected_mask)
                    if ambiguous:
                        self.assertGreater(len(analysis["candidate_indices"]), 1)
                    else:
                        self.assertEqual(
                            analysis["candidate_indices"], (selected_index,)
                        )
                    self.assertEqual(
                        GENERATOR.observe_overrides(grid),
                        {"scene_profile": profile},
                    )

    def test_output_is_exact_cropped_scaled_selected_glyph(self):
        for band in ("easy", "medium", "hard"):
            for profile in GENERATOR.GENERAL_PROFILES:
                grid = GENERATOR.generate(
                    43, 71, difficulty=band, scene_profile=profile
                )
                analysis = GENERATOR._analysis(grid)
                output = analysis["output"]
                frame_color = analysis["frame_color"]
                fill_color = analysis["fill_color"]
                mask = analysis["selected_mask"]
                block_h, block_w = analysis["block_shape"]
                self.assertEqual(
                    (len(output), len(output[0])),
                    tuple(value + 2 for value in analysis["inner_shape"]),
                )
                for r, row in enumerate(output):
                    for c, value in enumerate(row):
                        if r in (0, len(output) - 1) or c in (0, len(row) - 1):
                            expected = frame_color
                        elif mask[(r - 1) // block_h][(c - 1) // block_w] == "1":
                            expected = fill_color
                        else:
                            expected = 8
                        self.assertEqual(value, expected)

    def test_all_dimensions_counts_indices_scales_and_colors_occur(self):
        dimensions, counts, indices, scales, fill_colors = set(), set(), set(), set(), set()
        for band in ("easy", "medium", "hard"):
            for seed in range(1200):
                grid = GENERATOR.generate(seed, seed * 37, difficulty=band)
                analysis = GENERATOR._analysis(grid)
                if analysis["scene_profile"] in GENERATOR.PUBLIC_PROFILES:
                    continue
                mask = analysis["selected_mask"]
                dimensions.add((len(mask), len(mask[0])))
                counts.add(len(analysis["top_glyphs"]))
                indices.add(analysis["selected_index"])
                scales.add(analysis["block_shape"])
                fill_colors.add(analysis["fill_color"])
        self.assertEqual(dimensions, {(2, 2), (2, 3), (3, 2), (3, 3), (3, 4), (4, 3)})
        self.assertEqual(counts, {2, 3, 4, 5})
        self.assertEqual(indices, {0, 1, 2, 4})
        self.assertEqual(
            scales,
            {(r, c) for lo in (1, 2, 3) for r in (lo, lo + 1) for c in (lo, lo + 1)},
        )
        self.assertEqual(fill_colors, {0, 1, 2, 3, 4, 5, 6, 7, 9})

    def test_diversity_and_profile_coverage(self):
        for band in ("easy", "medium", "hard"):
            profiles = Counter()
            inputs, outputs, shapes = set(), set(), set()
            for seed in range(800):
                grid = GENERATOR.generate(seed, seed * 41, difficulty=band)
                analysis = GENERATOR._analysis(grid)
                self.assertEqual(analysis["errors"], [])
                profiles[analysis["scene_profile"]] += 1
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, analysis["output"])))
                shapes.add((len(grid), len(grid[0])))
            self.assertEqual(set(profiles), set(GENERATOR.SCENE_PROFILES))
            self.assertGreater(len(inputs), 650)
            self.assertGreater(len(outputs), 300)
            self.assertGreater(len(shapes), 8)

    def test_malformed_scenes_are_rejected(self):
        grid = GENERATOR.generate(5, 9, scene_profile="three_middle_3x2")
        cases = [[], [[8]], [[True]], [[10]]]
        ragged = copy.deepcopy(grid)
        ragged[0].pop()
        cases.append(ragged)

        broken_frame = copy.deepcopy(grid)
        r, c = next(iter(GENERATOR._analysis(grid)["frame"]["cells"]))
        broken_frame[r][c] = 8
        cases.append(broken_frame)

        no_evidence = copy.deepcopy(grid)
        analysis = GENERATOR._analysis(no_evidence)
        fr1, fc1, fr2, fc2 = analysis["frame_bbox"]
        for r in range(fr1 + 1, fr2):
            for c in range(fc1 + 1, fc2):
                if no_evidence[r][c] == analysis["fill_color"]:
                    no_evidence[r][c] = 8
        cases.append(no_evidence)

        multi_fill = copy.deepcopy(grid)
        analysis = GENERATOR._analysis(multi_fill)
        r, c = next(
            (r, c)
            for r in range(analysis["frame_bbox"][0] + 1, analysis["frame_bbox"][2])
            for c in range(analysis["frame_bbox"][1] + 1, analysis["frame_bbox"][3])
            if multi_fill[r][c] == 8
        )
        used = {value for row in multi_fill for value in row}
        multi_fill[r][c] = next(value for value in range(10) if value not in used and value != 8)
        cases.append(multi_fill)

        no_glyphs = copy.deepcopy(grid)
        analysis = GENERATOR._analysis(no_glyphs)
        frame_top = analysis["frame_bbox"][0]
        for r in range(frame_top):
            for c in range(len(no_glyphs[0])):
                no_glyphs[r][c] = 8
        cases.append(no_glyphs)

        for case in cases:
            self.assertTrue(GENERATOR.self_check(case), case)

    def test_determinism_fresh_returns_and_override_errors(self):
        for overrides in (
            {"scene_profile": "unknown"},
            {"glyph_count": 5},
            {"texture": "no_frame"},
        ):
            with self.assertRaises(ValueError):
                GENERATOR.generate(1, 2, **overrides)
        with self.assertRaises(ValueError):
            GENERATOR.generate(1, 2, difficulty="extreme")
        random.seed(37)
        state = random.getstate()
        first = GENERATOR.generate(17, 23, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = GENERATOR.generate(17, 23, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)

    def test_source_hash_and_duplicate_source_sync(self):
        rows = canonical_rows()
        source = rows[0]["program_solution"]
        self.assertTrue(all(row["program_solution"] == source for row in rows))
        digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(GENERATOR.RULE_HASH, digest)
        for relative in (
            "base/solutions/training/8a6d367c__8d37d130fec1.json",
            "base/solutions/augmented/8a6d367c__574559dce39f.json",
        ):
            base = json.loads((DATA_ROOT / relative).read_text())
            normalized = " ".join(source.split())
            self.assertEqual(" ".join(base["racket_target"]["raw_code"].split()), normalized)
            self.assertEqual(" ".join(base["racket_target"]["target_code"].split()), normalized)


if __name__ == "__main__":
    unittest.main()
