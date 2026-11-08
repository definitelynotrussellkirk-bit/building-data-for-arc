from __future__ import annotations

import hashlib
import json
import random
import unittest
from collections import Counter

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK = "0b9e771d6ba5"
ROOT = find_root(__file__)
MOD, _SOURCE_PATH, _SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)
BASE_PATHS = (
    "data/base/solutions/training/52df9849__0b9e771d6ba5.json",
    "data/base/solutions/augmented/52df9849__4fbfe0768694.json",
)


def canonical_rows():
    rows = []
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK:
            rows.append(row)
    return rows


def data_path(relative):
    for candidate in (ROOT / relative, ROOT / "shared" / relative):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Missing task-bound data file {relative!r} under {ROOT}")


def pairs(row):
    return row["train"] + row["test"]


class GeneratorTests(unittest.TestCase):
    def test_all_canonical_occurrences_and_exact_public_profiles(self):
        rows = canonical_rows()
        self.assertEqual({row["source"] for row in rows}, {"training", "augmented"})
        self.assertEqual(sum(len(pairs(row)) for row in rows), 8)
        training = next(row for row in rows if row["source"] == "training")
        for profile, pair in zip(MOD.PUBLIC_PROFILES, pairs(training)):
            grid = MOD.generate(11, 29, scene_profile=profile)
            self.assertEqual(grid, pair["input"])
            self.assertEqual(MOD.rule_mirror(grid), pair["output"])
            self.assertEqual(MOD.self_check(grid), [])
            self.assertEqual(MOD.canonical_profile_signature(grid), profile)
            self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})
        expected = {(tuple(map(tuple, pair["input"])), tuple(map(tuple, pair["output"]))) for pair in pairs(training)}
        augmented = next(row for row in rows if row["source"] == "augmented")
        self.assertEqual({(tuple(map(tuple, pair["input"])), tuple(map(tuple, pair["output"]))) for pair in pairs(augmented)}, expected)

    def test_every_general_profile_in_every_band(self):
        for band in (None, "easy", "medium", "hard"):
            for profile in MOD.GENERAL_PROFILES:
                for seed in range(60):
                    grid = MOD.generate(seed, seed * 19, difficulty=band, scene_profile=profile)
                    analysis = MOD._analysis(grid)
                    self.assertEqual(analysis["errors"], [], (band, profile, seed, analysis))
                    self.assertEqual(analysis["scene_profile"], profile)
                    self.assertEqual(MOD.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MOD.rule_mirror(grid), analysis["output"])

    def test_general_scenes_have_attached_semantically_inert_density_decoys(self):
        for band in (None, "easy", "medium", "hard"):
            for profile in MOD.GENERAL_PROFILES:
                for seed in range(40):
                    grid = MOD.generate(seed, seed * 23, difficulty=band, scene_profile=profile)
                    facts = MOD._analysis(grid)["facts"]
                    inert = [entry for entry in facts["color_facts"].values() if MOD._is_inert_decoy(entry)]
                    self.assertEqual(len(inert), MOD.INERT_DECOY_COLORS, (band, profile, seed))
                    self.assertTrue(all(entry["components"] == MOD.INERT_COMPONENTS_PER_COLOR for entry in inert))
                    active_boxes = [
                        entry["bbox"] for entry in facts["color_facts"].values() if not MOD._is_inert_decoy(entry)
                    ]
                    active_paths = {
                        point
                        for entry in facts["color_facts"].values()
                        if not MOD._is_inert_decoy(entry)
                        for point in entry["line_path"]
                    }
                    for entry in inert:
                        self.assertTrue(all(not (top <= row <= bottom and left <= col <= right)
                                            for row, col in entry["cells"]
                                            for top, left, bottom, right in active_boxes))
                        self.assertTrue(active_paths.isdisjoint(entry["cells"]))
                    inert_cells = {point for entry in inert for point in entry["cells"]}
                    active_cells = {
                        point
                        for entry in facts["color_facts"].values()
                        if not MOD._is_inert_decoy(entry)
                        for point in entry["cells"]
                    }
                    self.assertTrue(any(
                        neighbor in active_cells
                        for row, col in inert_cells
                        for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
                    ))

    def test_rectangle_eligibility_and_ascending_priority(self):
        impurity = MOD._analysis(MOD.generate(7, 13, scene_profile="rect_impurity"))["facts"]
        self.assertEqual(len(impurity["rectangle_order"]), 1)
        qualifier = impurity["color_facts"][impurity["rectangle_order"][0]]
        self.assertTrue(qualifier["foreign"])
        self.assertFalse(qualifier["has_background"])

        priority = MOD._analysis(MOD.generate(7, 13, scene_profile="rect_priority"))["facts"]
        self.assertEqual(len(priority["rectangle_order"]), 2)
        winner = max(priority["rectangle_order"])
        top, left, bottom, right = priority["color_facts"][winner]["bbox"]
        self.assertTrue(all(priority["output"][row][col] == winner for row in range(top, bottom + 1) for col in range(left, right + 1)))

    def test_all_line_directions_and_original_background_gaps(self):
        expected = {
            "horizontal_bridge": "horizontal",
            "vertical_bridge": "vertical",
            "diag_down_bridge": "diag_down",
            "diag_up_bridge": "diag_up",
            "background_gap_stays": "horizontal",
        }
        for profile, kind in expected.items():
            grid = MOD.generate(17, 23, scene_profile=profile)
            facts = MOD._analysis(grid)["facts"]
            line_color = facts["line_order"][0]
            line = facts["color_facts"][line_color]
            self.assertEqual(line["line_kind"], kind)
            self.assertTrue(any(grid[row][col] != facts["background"] and grid[row][col] != line_color for row, col in line["line_path"]))
            for row, col in line["line_path"]:
                if grid[row][col] == facts["background"]:
                    self.assertEqual(facts["output"][row][col], facts["background"])

    def test_ordinary_lessons_are_colorblind_connected(self):
        intentionally_fragmented = {
            "background_gap_stays",
            "off_line_decoy_disables",
            "disconnected_bbox_blocks_fill",
        }
        for profile in set(MOD.GENERAL_PROFILES) - intentionally_fragmented:
            for seed in range(30):
                grid = MOD.generate(seed, seed * 17, scene_profile=profile)
                facts = MOD._analysis(grid)["facts"]
                cells = {
                    (row, col)
                    for row, values in enumerate(grid)
                    for col, value in enumerate(values)
                    if value != facts["background"]
                }
                components = 0
                while cells:
                    components += 1
                    stack = [cells.pop()]
                    while stack:
                        row, col = stack.pop()
                        for point in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                            if point in cells:
                                cells.remove(point)
                                stack.append(point)
                self.assertEqual(components, 1, (profile, seed))

    def test_decoys_disable_and_disconnected_bbox_does_not_fill(self):
        for profile, expected_count, expected_components in (
            ("off_line_decoy_disables", 3, 3),
            ("disconnected_bbox_blocks_fill", 8, 2),
        ):
            facts = MOD._analysis(MOD.generate(31, 47, scene_profile=profile))["facts"]
            rivals = [
                entry
                for entry in facts["color_facts"].values()
                if entry["count"] == expected_count
                and entry["components"] == expected_components
                and not MOD._is_inert_decoy(entry)
            ]
            self.assertEqual(len(rivals), 1)
            rival = rivals[0]
            self.assertIsNone(rival["line_kind"])
            self.assertFalse(rival["qualifies_rectangle"])
            self.assertTrue(rival["has_background"])
            self.assertEqual(len(facts["rectangle_order"]), 1)

    def test_line_pass_overwrites_rectangles_and_lower_lines(self):
        multi_grid = MOD.generate(37, 41, scene_profile="multiple_lines_priority")
        multi = MOD._analysis(multi_grid)["facts"]
        self.assertEqual(len(multi["line_order"]), 2)
        horizontal = next(color for color in multi["line_order"] if multi["color_facts"][color]["line_kind"] == "horizontal")
        vertical = next(color for color in multi["line_order"] if multi["color_facts"][color]["line_kind"] == "vertical")
        crossing = set(multi["color_facts"][horizontal]["line_path"]) & set(multi["color_facts"][vertical]["line_path"])
        self.assertEqual(len(crossing), 1)
        row, col = crossing.pop()
        self.assertNotEqual(multi_grid[row][col], multi["background"])
        self.assertEqual(multi["output"][row][col], max(horizontal, vertical))

        over_grid = MOD.generate(37, 41, scene_profile="line_over_restoration")
        over = MOD._analysis(over_grid)["facts"]
        rectangle_color = next(
            color for color in over["rectangle_order"] if over["color_facts"][color]["line_kind"] is None
        )
        line_color = over["line_order"][0]
        bbox = over["color_facts"][rectangle_color]["bbox"]
        targets = [(row, col) for row, col in over["color_facts"][line_color]["line_path"] if bbox[0] <= row <= bbox[2] and bbox[1] <= col <= bbox[3] and over_grid[row][col] != over["background"]]
        self.assertTrue(targets)
        self.assertTrue(all(over["output"][row][col] == line_color for row, col in targets))

    def test_distribution_is_complete_diverse_and_non_degenerate(self):
        profiles = Counter()
        inputs, outputs, general_inputs, general_outputs = set(), set(), set(), set()
        shapes, backgrounds, colors, rect_counts, line_kinds = set(), set(), set(), set(), set()
        for seed in range(4000):
            band = ("easy", "medium", "hard")[seed % 3]
            grid = MOD.generate(seed, seed * 31, difficulty=band)
            analysis = MOD._analysis(grid)
            self.assertEqual(analysis["errors"], [])
            facts = analysis["facts"]
            profile = analysis["scene_profile"]
            profiles[profile] += 1
            key_in, key_out = tuple(map(tuple, grid)), tuple(map(tuple, facts["output"]))
            inputs.add(key_in)
            outputs.add(key_out)
            if profile in MOD.GENERAL_PROFILES:
                general_inputs.add(key_in)
                general_outputs.add(key_out)
            shapes.add((len(grid), len(grid[0])))
            backgrounds.add(facts["background"])
            colors.update(facts["color_facts"])
            rect_counts.add(len(facts["rectangle_order"]))
            line_kinds.update(entry["line_kind"] for entry in facts["color_facts"].values() if entry["line_kind"])
        general_count = sum(profiles[profile] for profile in MOD.GENERAL_PROFILES)
        self.assertEqual(set(profiles), set(MOD.SCENE_PROFILES))
        self.assertGreater(len(inputs), 3600)
        self.assertGreater(len(outputs), 3600)
        self.assertGreater(len(general_inputs) / general_count, 0.99)
        self.assertGreater(len(general_outputs) / general_count, 0.99)
        self.assertGreater(len(shapes), 100)
        self.assertEqual(backgrounds, set(range(10)))
        self.assertEqual(colors, set(range(1, 10)))
        self.assertEqual(rect_counts, {0, 1, 2})
        self.assertEqual(line_kinds, {"horizontal", "vertical", "diag_down", "diag_up"})

    def test_malformed_and_semantic_impostors_fail_closed(self):
        cases = [[], [[]], [[True]], [[10]], [[1], [1, 2]], [[0] * 9 for _ in range(9)], [[1] * 9 for _ in range(9)]]
        identity = [[0] * 9 for _ in range(9)]
        for row in range(3, 6):
            for col in range(3, 6):
                identity[row][col] = 2
        cases.append(identity)
        for grid in cases:
            self.assertTrue(MOD.self_check(grid), grid)
        with self.assertRaises(ValueError):
            MOD.rule_mirror([])

    def test_determinism_unknowns_freshness_and_global_rng(self):
        for overrides in ({"scene_profile": "bad"}, {"texture": "occluded"}, {"bg": 7}):
            with self.assertRaises(ValueError):
                MOD.generate(1, 2, **overrides)
        with self.assertRaises(ValueError):
            MOD.generate(1, 2, difficulty="extreme")
        random.seed(47)
        state = random.getstate()
        first = MOD.generate(17, 23, difficulty="hard")
        self.assertEqual(state, random.getstate())
        second = MOD.generate(17, 23, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])

    def test_rule_hash_grounded_and_both_base_sources_are_synced(self):
        source = canonical_rows()[0]["program_solution"]
        self.assertTrue(all(row["program_solution"] == source for row in canonical_rows()))
        self.assertEqual(MOD.RULE_HASH, hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12])
        from solvers.grounded_rules import GROUNDED_RULES
        self.assertEqual(GROUNDED_RULES[TASK], source)
        for path in BASE_PATHS:
            base = json.loads(data_path(path).read_text())
            self.assertEqual(base["racket_target"]["raw_code"], source)
            self.assertEqual(base["racket_target"]["target_code"], source)


if __name__ == "__main__":
    unittest.main()
