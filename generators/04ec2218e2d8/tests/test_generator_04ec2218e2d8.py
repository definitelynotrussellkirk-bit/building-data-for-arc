from __future__ import annotations

import copy
import hashlib
from importlib import import_module
import json
import random
import unittest

from reviewer_support import canonical_pairs, canonical_path, find_root
from solvers.grounded_rules import GROUNDED_RULES


generator = import_module(
    "puzzle_generators.per_puzzle.04ec2218e2d8.generator"
)
ROOT = find_root(__file__)
DATA_ROOT = canonical_path(ROOT).parents[1]
BASE_PATHS = (
    DATA_ROOT
    / "base/solutions/augmented/"
    "639f5a19__ce15b17d228a.json",
    DATA_ROOT
    / "base/solutions/training/"
    "639f5a19__04ec2218e2d8.json",
)


def canonical_rows():
    return [
        json.loads(line)
        for line in canonical_path(ROOT).read_text().splitlines()
        if json.loads(line).get("task_id") == generator.TASK_ID
    ]


def unique_public_pairs():
    pairs = []
    seen = set()
    for pair in canonical_pairs(
        generator.TASK_ID, root=ROOT, labeled_only=True
    ):
        frozen = tuple(tuple(grid_row) for grid_row in pair["input"])
        if frozen not in seen:
            seen.add(frozen)
            pairs.append(pair)
    return pairs


class Generator04ec2218e2d8Tests(unittest.TestCase):
    def test_all_public_pairs_are_positive_controls(self):
        pairs = unique_public_pairs()
        self.assertEqual(len(pairs), 3)
        observed = set()
        for index, pair in enumerate(pairs):
            grid = pair["input"]
            self.assertEqual(generator.self_check(grid), [])
            axes = generator.observe_overrides(grid)
            observed.add(axes["scene_profile"])
            self.assertEqual(axes["component_style"], "solid")
            self.assertEqual(
                generator.exact_public_profile_index(grid),
                index,
            )
            self.assertEqual(
                generator.rule_mirror(grid),
                pair["output"],
            )
        self.assertEqual(
            observed,
            set(generator.SCENE_PROFILES[:3]),
        )

    def test_every_axis_value_is_constructive_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in generator.SCENE_PROFILES:
                for style in generator.COMPONENT_STYLES:
                    for seed in range(6):
                        requested = {
                            "scene_profile": profile,
                            "component_style": style,
                        }
                        grid = generator.generate(
                            1000 + seed,
                            seed * 41,
                            difficulty=band,
                            **requested,
                        )
                        self.assertEqual(
                            generator.self_check(
                                grid,
                                difficulty=band,
                                meta={"overrides": requested},
                            ),
                            [],
                        )
                        self.assertEqual(
                            generator.observe_overrides(grid),
                            requested,
                        )
                        analysis = generator._analyze_scene(grid)
                        self.assertEqual(
                            analysis["component_style"],
                            style,
                        )
                        for rectangle in analysis["rectangles"]:
                            missing = rectangle["missing"]
                            if style == "solid":
                                self.assertEqual(missing, [])
                            else:
                                self.assertEqual(len(missing), 1)
                                row, col = missing[0]
                                on_edge = (
                                    row in (rectangle["top"], rectangle["bottom"])
                                    or col in (rectangle["left"], rectangle["right"])
                                )
                                self.assertEqual(
                                    on_edge,
                                    style == "edge_notch",
                                )
                        self.assertNotEqual(
                            generator.rule_mirror(grid),
                            grid,
                        )

    def test_default_distribution_covers_profiles_styles_and_difficulty(self):
        counts = {}
        for band_index, band in enumerate(
            ("easy", "medium", "hard")
        ):
            band_counts = {
                profile: 0
                for profile in generator.SCENE_PROFILES
            }
            style_counts = {
                style: 0
                for style in generator.COMPONENT_STYLES
            }
            for seed in range(600):
                sample_index = seed * 43 + band_index
                grid = generator.generate(
                    3000 + seed,
                    sample_index,
                    difficulty=band,
                )
                observed = generator.observe_overrides(grid)
                band_counts[observed["scene_profile"]] += 1
                style_counts[observed["component_style"]] += 1
                self.assertEqual(
                    observed["component_style"],
                    generator.schedule_profile(
                        3000 + seed,
                        sample_index,
                        band,
                    ),
                )
            self.assertTrue(
                all(value >= 35 for value in band_counts.values())
            )
            self.assertEqual(set(style_counts.values()), {200})
            counts[band] = band_counts
        self.assertGreater(
            counts["easy"]["two_generalized"],
            counts["easy"]["three_generalized"],
        )
        self.assertGreater(
            counts["hard"]["three_generalized"],
            counts["hard"]["two_8x8_10x12"],
        )

    def test_three_slot_schedule_covers_every_style_in_every_window(self):
        self.assertEqual(generator.LESSON_SCHEDULE_PERIOD, 3)
        self.assertEqual(
            tuple(generator.SCHEDULE_PROFILES),
            tuple(generator.COMPONENT_STYLES),
        )
        for start in range(12):
            window = [
                generator.schedule_profile(17, start + offset, "hard")
                for offset in range(3)
            ]
            self.assertEqual(set(window), set(generator.COMPONENT_STYLES))

    def test_bbox_fill_shortcut_fits_canonical_but_witnesses_refute_it(self):
        rival_name = "paint_whole_bounding_boxes"
        rival = generator.SEMANTIC_RIVALS[rival_name]
        for pair in unique_public_pairs():
            self.assertEqual(rival(pair["input"]), pair["output"])

        for style, witness_name in (
            ("interior_hole", "interior_hole_preserves_background"),
            ("edge_notch", "edge_notch_preserves_background"),
        ):
            grid = generator.generate(
                4100,
                7,
                difficulty="medium",
                scene_profile="two_8x8_10x12",
                component_style=style,
            )
            canonical = generator.rule_mirror(grid)
            alternative = rival(grid)
            self.assertNotEqual(alternative, canonical)
            self.assertTrue(
                generator.SEMANTIC_WITNESSES[witness_name](grid)
            )
            analysis = generator._analyze_scene(grid)
            for rectangle in analysis["rectangles"]:
                row, col = rectangle["missing"][0]
                self.assertEqual(canonical[row][col], 0)
                self.assertNotEqual(alternative[row][col], 0)

    def test_semantic_contract_rejects_solid_only_ambiguity(self):
        demos = []
        for sample_index in range(generator.EXAMPLES_NEEDED):
            grid = generator.generate(
                5200,
                sample_index,
                difficulty="easy",
                component_style="solid",
            )
            demos.append({
                "input": grid,
                "output": generator.rule_mirror(grid),
            })
        query_grid = generator.generate(
            5200,
            generator.EXAMPLES_NEEDED,
            difficulty="easy",
            component_style="interior_hole",
        )
        reasons = generator.lesson_identifiable(
            demos,
            {
                "input": query_grid,
                "output": generator.rule_mirror(query_grid),
            },
        )
        self.assertTrue(
            any("paint_whole_bounding_boxes" in reason for reason in reasons),
            reasons,
        )

    def test_every_three_demo_rotation_eliminates_bbox_fill(self):
        for band in ("easy", "medium", "hard"):
            for start in range(generator.LESSON_SCHEDULE_PERIOD):
                episodes = []
                for offset in range(generator.EXAMPLES_NEEDED + 1):
                    grid = generator.generate(
                        6300 + start,
                        start + offset,
                        difficulty=band,
                    )
                    episodes.append({
                        "input": grid,
                        "output": generator.rule_mirror(grid),
                    })
                for query_index in range(len(episodes)):
                    query = episodes[query_index]
                    demos = [
                        episode
                        for index, episode in enumerate(episodes)
                        if index != query_index
                    ]
                    styles = {
                        generator.observe_overrides(demo["input"])[
                            "component_style"
                        ]
                        for demo in demos
                    }
                    self.assertTrue(
                        styles & {"interior_hole", "edge_notch"}
                    )
                    self.assertEqual(
                        generator.lesson_identifiable(demos, query),
                        [],
                    )

    def test_strict_semantic_hook_matches_self_check(self):
        for style in generator.COMPONENT_STYLES:
            grid = generator.generate(
                7100,
                11,
                component_style=style,
            )
            self.assertEqual(generator.strict_canonical_like(grid), [])
        self.assertTrue(generator.strict_canonical_like([[8]]))

    def test_counts_palette_and_literal_prior(self):
        exact = 0
        seen_counts = set()
        for profile in generator.SCENE_PROFILES[:3]:
            for seed in range(300):
                grid = generator.generate(
                    5000 + seed,
                    seed * 47,
                    difficulty=(
                        "easy",
                        "medium",
                        "hard",
                    )[seed % 3],
                    scene_profile=profile,
                )
                analysis = generator._analyze_scene(grid)
                self.assertIsNotNone(analysis)
                self.assertEqual(
                    {value for row in grid for value in row},
                    {0, 8},
                )
                seen_counts.add(len(analysis["rectangles"]))
                exact += (
                    generator.exact_public_profile_index(grid)
                    is not None
                )
        self.assertEqual(seen_counts, {2, 3})
        self.assertGreaterEqual(exact, 20)
        self.assertLessEqual(exact, 80)

    def test_task_specific_mutations_are_rejected(self):
        source = copy.deepcopy(
            unique_public_pairs()[0]["input"]
        )
        analysis = generator._analyze_scene(source)
        mutations = []

        one_rectangle = copy.deepcopy(source)
        for row, col in analysis["rectangles"][0]["cells"]:
            one_rectangle[row][col] = 0
        mutations.append(one_rectangle)

        mixed_styles = copy.deepcopy(source)
        rectangle = analysis["rectangles"][0]
        mixed_styles[
            rectangle["top"] + 1
        ][
            rectangle["left"] + 1
        ] = 0
        mutations.append(mixed_styles)

        two_cutouts = copy.deepcopy(source)
        for rectangle in analysis["rectangles"]:
            two_cutouts[
                rectangle["top"] + 1
            ][
                rectangle["left"] + 1
            ] = 0
            two_cutouts[
                rectangle["top"] + 2
            ][
                rectangle["left"] + 2
            ] = 0
        mutations.append(two_cutouts)

        corner_cutouts = copy.deepcopy(source)
        for rectangle in analysis["rectangles"]:
            corner_cutouts[
                rectangle["top"]
            ][
                rectangle["left"]
            ] = 0
        mutations.append(corner_cutouts)

        wrong_color = copy.deepcopy(source)
        wrong_color[
            rectangle["top"]
        ][
            rectangle["left"]
        ] = 7
        mutations.append(wrong_color)

        border_object = copy.deepcopy(source)
        border_object[0][0] = 8
        mutations.append(border_object)

        mutations.append([row[:-1] for row in source])
        mutations.append([[True]])
        mutations.append([[10]])
        mutations.append([[0], [0, 0]])

        for grid in mutations:
            self.assertTrue(
                generator.self_check(grid),
                msg="mutation unexpectedly passed",
            )
            self.assertEqual(
                generator.observe_overrides(grid),
                {},
            )

    def test_broad_oracle_preserves_non_cyan_objects(self):
        grid = generator.generate(
            7001,
            83,
            difficulty="hard",
            scene_profile="three_generalized",
        )
        grid[0][0] = 9
        before = copy.deepcopy(grid)
        output = generator.rule_mirror(grid)
        self.assertEqual(grid, before)
        self.assertEqual(output[0][0], 9)
        self.assertNotEqual(output, grid)

        shifted = generator.generate(
            7002,
            84,
            difficulty="medium",
            scene_profile="two_8x8_10x12",
            component_style="edge_notch",
        )
        self.assertEqual(
            generator.observe_overrides(shifted),
            {
                "scene_profile": "two_8x8_10x12",
                "component_style": "edge_notch",
            },
        )

    def test_determinism_fresh_returns_and_global_rng(self):
        before = random.getstate()
        first = generator.generate(
            8111,
            97,
            difficulty="medium",
        )
        middle = random.getstate()
        second = generator.generate(
            8111,
            97,
            difficulty="medium",
        )
        after = random.getstate()
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        self.assertEqual(before, middle)
        self.assertEqual(before, after)
        first[0][0] = 8
        self.assertNotEqual(first, second)

    def test_rejects_invalid_scalar_controls(self):
        for sample_index in (True, False, 1.0, "1", -1):
            with self.subTest(sample_index=sample_index):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(9001, sample_index)

        for seed in (True, False, 1.0, "1"):
            with self.subTest(seed=seed):
                with self.assertRaises((TypeError, ValueError)):
                    generator.generate(seed, 0)

    def test_rule_hash_and_all_sources_are_synchronized(self):
        rows = canonical_rows()
        sources = {
            row["program_solution"]
            for row in rows
        }
        self.assertEqual(len(sources), 1)
        source = next(iter(sources))
        normalized_hash = hashlib.sha256(
            " ".join(source.split()).encode()
        ).hexdigest()[:12]
        self.assertEqual(generator.RULE_HASH, normalized_hash)
        self.assertEqual(
            GROUNDED_RULES[generator.TASK_ID],
            source,
        )
        for path in BASE_PATHS:
            record = json.loads(path.read_text())
            for field in ("raw_code", "target_code"):
                self.assertEqual(
                    record["racket_target"][field],
                    source,
                )
            self.assertTrue(
                record["primitive_metadata"]["primitive_chain"]
            )
            self.assertTrue(
                record["primitive_metadata"]["family_chain"]
            )


if __name__ == "__main__":
    unittest.main()
