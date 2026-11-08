"""Focused semantic regressions for generator 252ff772a276."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib
import json
from pathlib import Path
import random
import sys
import unittest

# Portable bootstrap: repository tree and staged task-test runtime.
for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "252ff772a276"
ROOT = find_root(__file__)
MODULE, SOURCE, _SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _canonical_row():
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


def _grid(value):
    return [[int(cell) for cell in row] if isinstance(row, str) else list(row) for row in value]


def _normalized_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


class Generator252ff772a276Tests(unittest.TestCase):
    def test_all_three_canonical_pairs_rules_and_profiles(self):
        row = _canonical_row()
        pairs = [*row["train"], *row["test"]]
        self.assertEqual(len(pairs), 3)
        seen = set()
        frame_counts = []
        seed_counts = []
        for pair in pairs:
            source, expected = _grid(pair["input"]), _grid(pair["output"])
            self.assertEqual(MODULE.self_check(source), [])
            self.assertEqual(MODULE.rule_mirror(source), expected)
            profile = MODULE.canonical_profile_signature(source)
            self.assertIn(profile, MODULE.PUBLIC_PROFILES)
            seen.add(profile)
            info = MODULE._analysis(source)
            frame_counts.append(len(info["frames"]))
            seed_counts.append([frame["seed_count"] for frame in info["frames"]])
        self.assertEqual(seen, set(MODULE.PUBLIC_PROFILES))
        self.assertEqual(frame_counts, [2, 2, 3])
        self.assertEqual(seed_counts, [[1, 3], [2, 1], [3, 1, 2]])

    def test_public_profiles_preserve_linked_frame_descriptors(self):
        for profile in MODULE.PUBLIC_PROFILES:
            seen = set()
            for seed in range(40):
                grid = MODULE.generate(seed, seed * 23 + 5, scene_profile=profile)
                self.assertEqual(MODULE.canonical_profile_signature(grid), profile)
                self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                self.assertEqual(MODULE.self_check(grid), [])
                seen.add(tuple(map(tuple, grid)))
            # The smallest public profile has only 36 possible two-seed
            # placements; this requires broad coverage without demanding all.
            self.assertGreater(len(seen), 30)

    def test_forced_scene_profiles_are_exact_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.SCENE_PROFILES:
                for seed in range(20):
                    grid = MODULE.generate(seed + 700, seed * 17 + 3, difficulty=band, scene_profile=profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(MODULE.self_check(grid, meta={"overrides": {"scene_profile": profile}}), [])

    def test_tie_profiles_use_topmost_then_leftmost(self):
        vertical = MODULE.generate(811, 923, difficulty="medium", scene_profile="vertical_tie")
        horizontal = MODULE.generate(811, 923, difficulty="medium", scene_profile="horizontal_tie")
        vi = MODULE._analysis(vertical)
        hi = MODULE._analysis(horizontal)
        vmax = max(frame["seed_count"] for frame in vi["frames"])
        hmax = max(frame["seed_count"] for frame in hi["frames"])
        vtied = [frame for frame in vi["frames"] if frame["seed_count"] == vmax]
        htied = [frame for frame in hi["frames"] if frame["seed_count"] == hmax]
        self.assertGreater(len({frame["r1"] for frame in vtied}), 1)
        self.assertEqual(vi["chosen"]["r1"], min(frame["r1"] for frame in vtied))
        self.assertEqual(len({frame["r1"] for frame in htied}), 1)
        self.assertEqual(hi["chosen"]["c1"], min(frame["c1"] for frame in htied))

    def test_general_profiles_cover_ranking_and_distractors(self):
        expected_frames = {"two_distinct": 2, "three_distinct": 3, "small_winner": 2}
        for profile in MODULE.GENERAL_PROFILES:
            grid = MODULE.generate(101, 203, difficulty="hard", scene_profile=profile)
            info = MODULE._analysis(grid)
            self.assertEqual(info["errors"], [])
            self.assertIsNone(MODULE.canonical_profile_signature(grid))
            if profile in expected_frames:
                self.assertEqual(len(info["frames"]), expected_frames[profile])
            if profile == "small_winner":
                self.assertLess(info["chosen"]["area"], min(frame["area"] for frame in info["frames"] if frame is not info["chosen"]))
            elif profile == "broken_distractor":
                self.assertEqual(len(info["invalid_one_components"]), 1)
            elif profile == "outside_seed_distractor":
                self.assertTrue(info["outside_seeds"])

    def test_default_prior_coverage_and_uniqueness(self):
        for band in ("easy", "medium", "hard"):
            profiles = Counter()
            inputs = set()
            outputs = set()
            for seed in range(800):
                grid = MODULE.generate(seed, seed * 11 + 1, difficulty=band)
                profiles[MODULE.observe_overrides(grid)["scene_profile"]] += 1
                inputs.add(tuple(map(tuple, grid)))
                outputs.add(tuple(map(tuple, MODULE.rule_mirror(grid))))
            self.assertEqual(set(profiles), set(MODULE.SCENE_PROFILES))
            strict = sum(profiles[name] for name in MODULE.PUBLIC_PROFILES)
            self.assertGreater(strict, 180)
            self.assertLess(strict, 310)
            self.assertGreater(len(inputs), 775)
            # Output crops intentionally discard global position and losing
            # frames, so their natural support is smaller than input support.
            self.assertGreater(len(outputs), 500)

    def test_python_oracle_crops_winner_and_fills_only_zero_interior(self):
        grid = MODULE.generate(301, 407, difficulty="hard", scene_profile="outside_seed_distractor")
        before = copy.deepcopy(grid)
        info = MODULE._analysis(grid)
        output = MODULE.rule_mirror(grid)
        chosen = info["chosen"]
        self.assertEqual((len(output), len(output[0])), (chosen["height"], chosen["width"]))
        self.assertTrue(all(value == 1 for value in output[0] + output[-1]))
        for row in output[1:-1]:
            self.assertEqual(row[0], 1)
            self.assertEqual(row[-1], 1)
            self.assertTrue(all(value in (2, 3) for value in row[1:-1]))
        self.assertEqual(grid, before)

    def test_self_check_rejects_nearest_impostors(self):
        base = MODULE.generate(331, 557, difficulty="medium", scene_profile="two_distinct")
        info = MODULE._analysis(base)
        broken_border = copy.deepcopy(base)
        frame = info["frames"][0]
        broken_border[frame["r1"]][frame["c1"] + 1] = 0
        unseeded = copy.deepcopy(base)
        for row, col in frame["seed_cells"]:
            unseeded[row][col] = 0
        single_frame = copy.deepcopy(base)
        second = info["frames"][1]
        for row in range(second["r1"], second["r2"] + 1):
            for col in range(second["c1"], second["c2"] + 1):
                if single_frame[row][col] in (1, 2):
                    single_frame[row][col] = 0
        ragged = copy.deepcopy(base)
        ragged[0].pop()
        invalid = copy.deepcopy(base)
        invalid[0][0] = 9
        boolean = copy.deepcopy(base)
        boolean[0][0] = True
        for mutation in (broken_border, unseeded, single_frame, ragged, invalid, boolean):
            self.assertTrue(MODULE.self_check(mutation), mutation)

    def test_invalid_override_and_determinism_contract(self):
        for overrides in ({"scene_profile": "unknown"}, {"n_frames": 4}, {"texture": "no_frames"}):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    MODULE.generate(1, 2, **overrides)
        random.seed(20260721)
        state = random.getstate()
        first = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(random.getstate(), state)
        second = MODULE.generate(97, 103, difficulty="hard")
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(left is not right for left, right in zip(first, second)))

    def test_rule_authorities_and_pin_are_synchronized(self):
        row = _canonical_row()
        candidates = [
            ROOT / "data/base/solutions/banks/e06827914c5c/H13__252ff772a276.json",
            ROOT / "shared/data/base/solutions/banks/e06827914c5c/H13__252ff772a276.json",
        ]
        base_path = next(path for path in candidates if path.is_file())
        base = json.loads(base_path.read_text())
        canonical = row["program_solution"]
        self.assertEqual(base["racket_target"]["raw_code"], canonical)
        self.assertEqual(base["racket_target"]["target_code"], canonical)
        self.assertEqual(MODULE.RULE_HASH, _normalized_hash(canonical))
        self.assertEqual(MODULE.RULE_HASH, "40bcdf750b85")


if __name__ == "__main__":
    unittest.main()
