"""Focused regressions for the keyed-offset generator repair."""

from __future__ import annotations

import importlib
import importlib.util
import sys
import json
import random
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = next((p for p in Path(__file__).resolve().parents
                    if (p / "shared/runtime/puzzle_generators").is_dir()), None)
TASK_ID = "17b682bce66f"


def load_generator():
    if SOURCE_ROOT is None:
        return importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
    # A source checkout and a staged runtime must exercise the same selected file.
    sys.path.insert(0, str(SOURCE_ROOT / "shared/runtime"))
    spec = importlib.util.spec_from_file_location("keyed_offset_under_test", ROOT / "generator.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _as_int_grid(grid):
    return [
        [int(value) for value in row]
        if isinstance(row, str)
        else [int(value) for value in row]
        for row in grid
    ]


def canonical_pairs():
    data = SOURCE_ROOT / "shared/data" if SOURCE_ROOT is not None else ROOT / "data"
    with (data / "canonical" / "puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            test = row["test"]
            tests = [test] if isinstance(test, dict) else test
            return [*row["train"], *tests]
    raise AssertionError(f"canonical task {TASK_ID} is missing")


class KeyedOffsetGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = load_generator()
        cls.pairs = canonical_pairs()

    def test_all_canonical_inputs_are_exact_profiles_and_rule_matches(self):
        signatures = set()
        profiles = set()
        for pair in self.pairs:
            grid = _as_int_grid(pair["input"])
            output = _as_int_grid(pair["output"])
            self.assertEqual([], self.generator.self_check(grid))
            signatures.add(self.generator.canonical_profile_signature(grid))
            profiles.add(self.generator.observe_overrides(grid)["scene_profile"])
            self.assertEqual(output, self.generator.rule_mirror(grid))

        self.assertEqual(self.generator._CANONICAL_SIGNATURES, signatures)
        self.assertEqual(set(self.generator.CANONICAL_PROFILES), profiles)

    def test_every_profile_override_is_exact_and_branch_witnesses_fire(self):
        observations = {}
        for index, profile in enumerate(self.generator.SCENE_PROFILES):
            grid = self.generator.generate(
                1000 + index,
                2000 + index,
                difficulty="hard",
                scene_profile=profile,
            )
            self.assertEqual([], self.generator.self_check(grid))
            self.assertEqual(
                {"scene_profile": profile},
                self.generator.observe_overrides(grid),
            )
            observations[profile] = self.generator.scene_observables(grid)

        self.assertEqual((2, 3, 4, 5), observations["all_rotations"]["anchor_colors"])
        self.assertGreaterEqual(observations["paint_overlap"]["overlap_pair_count"], 2)
        self.assertGreaterEqual(observations["paint_overlap"]["overlap_cell_count"], 2)
        self.assertGreaterEqual(observations["anchor_overwrite"]["anchor_hit_count"], 1)
        self.assertTrue(all(observations["edge_touch"]["edge_touch"].values()))
        self.assertEqual(0, observations["wide_nonoverlap"]["overlap_pair_count"])
        self.assertEqual(0, observations["wide_nonoverlap"]["anchor_hit_count"])

    def test_default_prior_reaches_every_profile_and_canonical_floor_per_band(self):
        for band in ("easy", "medium", "hard"):
            counts = Counter()
            for seed in range(300):
                grid = self.generator.generate(
                    seed,
                    seed * 17 + 1,
                    difficulty=band,
                )
                self.assertEqual([], self.generator.self_check(grid))
                profile = self.generator.observe_overrides(grid)["scene_profile"]
                counts[profile] += 1

            canonical = sum(counts[name] for name in self.generator.CANONICAL_PROFILES)
            with self.subTest(band=band, counts=dict(counts)):
                self.assertEqual(set(self.generator.SCENE_PROFILES), set(counts))
                self.assertGreaterEqual(canonical, 15)

    def test_lawful_recombination_is_procedural_not_canonical(self):
        grid = _as_int_grid(self.pairs[0]["input"])
        changed = [row[:] for row in grid]
        # Replace the sole color-4 anchor with color 5.  The scene remains a
        # lawful keyed-offset input and the oracle can execute it, but this
        # linked cloud/layout/color combination appears in no fixed profile.
        # It must remain noncanonical, but is now classified as procedural.
        for row, values in enumerate(changed):
            for col, value in enumerate(values):
                if value == 4:
                    changed[row][col] = 5
                    break
            else:
                continue
            break

        self.assertEqual([], self.generator.self_check(changed))
        self.assertIsNone(self.generator.canonical_profile_signature(changed))
        self.assertEqual({"scene_profile": "procedural"},
                         self.generator.observe_overrides(changed))
        output = self.generator.rule_mirror(changed)
        self.assertEqual((len(changed), len(changed[0])), (len(output), len(output[0])))

    def test_self_check_rejects_targeted_structural_impostors(self):
        base = _as_int_grid(self.pairs[0]["input"])

        missing_reference = [row[:] for row in base]
        missing_reference[1][1] = 0

        disconnected_cloud = [row[:] for row in base]
        disconnected_cloud[1][2] = 0
        disconnected_cloud[10][10] = 8

        duplicate_anchor_color = [row[:] for row in base]
        duplicate_anchor_color[8][5] = 2

        out_of_bounds_stamp = [row[:] for row in base]
        out_of_bounds_stamp[8][5] = 0
        out_of_bounds_stamp[0][0] = 4

        illegal_color = [row[:] for row in base]
        illegal_color[0][0] = 1

        for label, impostor in {
            "missing_reference": missing_reference,
            "disconnected_cloud": disconnected_cloud,
            "duplicate_anchor_color": duplicate_anchor_color,
            "out_of_bounds_stamp": out_of_bounds_stamp,
            "illegal_color": illegal_color,
        }.items():
            with self.subTest(label=label):
                self.assertTrue(self.generator.self_check(impostor))

    def test_semantic_gate_uses_exact_canonical_predicate(self):
        self.assertTrue(callable(getattr(self.generator, "strict_canonical_like", None)))
        for pair in self.pairs:
            self.assertIs(self.generator.strict_canonical_like(_as_int_grid(pair["input"])), True)
        grid = self.generator.generate(971, 23, scene_profile="procedural")
        self.assertIs(self.generator.strict_canonical_like(grid), False)

    def test_default_medium_escapes_ten_template_lookup(self):
        signatures = set()
        for seed in range(600):
            grid = self.generator.generate(seed, 17 * seed + 1, difficulty="medium")
            signatures.add(self.generator._normalized_cells(
                len(grid), len(grid[0]), self.generator._foreground_cells(grid)))
        self.assertGreaterEqual(len(signatures), 250)

    def test_procedural_morphology_and_geometry_are_not_fixed_templates(self):
        self.assertIn("procedural", self.generator.SCENE_PROFILES)
        signatures, cloud_orbits, dimensions = set(), set(), set()
        relative_positions = set()
        for seed in range(300):
            grid = self.generator.generate(seed, 17 * seed + 1,
                                           scene_profile="procedural")
            self.assertEqual([], self.generator.self_check(
                grid, meta={"overrides": {"scene_profile": "procedural"}}))
            self.assertEqual({"scene_profile": "procedural"},
                             self.generator.observe_overrides(grid))
            self.assertIsNone(self.generator.canonical_profile_signature(grid))
            obs = self.generator.scene_observables(grid)
            signatures.add(self.generator._normalized_cells(
                len(grid), len(grid[0]), self.generator._foreground_cells(grid)))
            cloud_orbits.add(min(self.generator._rotation_forms(obs["cloud_offsets"])))
            dimensions.add((len(grid), len(grid[0])))
            _, _, _, anchors = self.generator._cloud_and_anchors(grid)
            rr, rc = obs["reference"]
            if rr < min(a[0] for a in anchors): relative_positions.add("above")
            if rr > max(a[0] for a in anchors): relative_positions.add("below")
            if rc < min(a[1] for a in anchors): relative_positions.add("left")
            if rc > max(a[1] for a in anchors): relative_positions.add("right")
        self.assertEqual(300, len(signatures))
        self.assertGreaterEqual(len(cloud_orbits), 50)
        self.assertGreaterEqual(len(dimensions), 25)
        self.assertEqual({"above", "below", "left", "right"}, relative_positions)

    def test_procedural_replay_and_rejection_are_explicit(self):
        self.assertIn("procedural", self.generator.SCENE_PROFILES)
        random.seed(20261002)
        state = random.getstate()
        first = self.generator.generate(42, 73, scene_profile="procedural")
        self.assertEqual(state, random.getstate())
        self.assertEqual(first, self.generator.generate(42, 73, scene_profile="procedural"))
        with self.assertRaises(TypeError):
            self.generator.generate(0, 0, misspelled_axis=True)
        with self.assertRaises(ValueError):
            self.generator.generate(0, 0, scene_profile="not_a_profile")
        with self.assertRaises(ValueError):
            self.generator.generate(0, 0, difficulty="impossible")

    def test_replay_is_deterministic_fresh_and_global_rng_pure(self):
        random.seed(99173)
        before = random.getstate()
        first = self.generator.generate(42, 73, difficulty="medium")
        after = random.getstate()
        second = self.generator.generate(42, 73, difficulty="medium")

        self.assertEqual(before, after)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        first[0][0] = (first[0][0] + 1) % 10
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
