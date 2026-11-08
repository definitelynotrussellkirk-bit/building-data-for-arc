"""Focused semantic regressions for generator 235a1d06b9d3."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import unittest


TASK_ID = "235a1d06b9d3"
for _parent in Path(__file__).resolve().parents:
    for _runtime in (_parent / "shared/runtime", _parent):
        if (_runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(_runtime))
            break
    else:
        continue
    break
from reviewer_support import canonical_path, find_root  # noqa: E402

ROOT = find_root(__file__)
_SOURCE = ROOT / f"generators/{TASK_ID}/generator.py"
_SPEC = importlib.util.spec_from_file_location(f"task_{TASK_ID}_generator", _SOURCE)
assert _SPEC is not None and _SPEC.loader is not None
MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = MODULE
_SPEC.loader.exec_module(MODULE)


def _canonical_row():
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


def _normalized_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


class Generator235a1d06b9d3Tests(unittest.TestCase):
    def test_all_five_canonical_pairs_rules_and_profiles(self):
        row = _canonical_row()
        pairs = [*row["train"], *row["test"]]
        self.assertEqual(len(pairs), 5)
        seen = set()
        relations = []
        for pair in pairs:
            source, expected = pair["input"], pair["output"]
            self.assertEqual(MODULE.self_check(source), [])
            self.assertEqual(MODULE.rule_mirror(source), expected)
            profile = MODULE.canonical_profile_signature(source)
            self.assertIn(profile, MODULE.PUBLIC_PROFILES)
            seen.add(profile)
            relations.append(MODULE._analysis(source)["cue_relation"])
        self.assertEqual(seen, set(MODULE.PUBLIC_PROFILES))
        self.assertEqual(relations, ["same_signal", "distinct_cue", "magenta_cue", "distinct_cue", "distinct_cue"])

    def test_public_profiles_preserve_complete_linked_morphology(self):
        for profile in MODULE.PUBLIC_PROFILES:
            seen = set()
            for seed in range(40):
                grid = MODULE.generate(seed, seed * 23 + 5, scene_profile=profile)
                self.assertEqual(MODULE.canonical_profile_signature(grid), profile)
                self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                self.assertEqual(MODULE.self_check(grid), [])
                seen.add(tuple(map(tuple, grid)))
            self.assertGreater(len(seen), 35)

    def test_forced_scene_profiles_are_exact_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for profile in MODULE.SCENE_PROFILES:
                for seed in range(20):
                    grid = MODULE.generate(seed + 700, seed * 17 + 3, difficulty=band, scene_profile=profile)
                    self.assertEqual(MODULE.observe_overrides(grid), {"scene_profile": profile})
                    self.assertEqual(
                        MODULE.self_check(grid, meta={"overrides": {"scene_profile": profile}}),
                        [],
                    )

    def test_general_profiles_cover_all_color_relationships(self):
        for profile in MODULE.GENERAL_PROFILES[:8]:
            grid = MODULE.generate(811, 923, difficulty="medium", scene_profile=profile)
            info = MODULE._analysis(grid)
            self.assertEqual(info["errors"], [])
            self.assertIsNone(MODULE.canonical_profile_signature(grid))
            self.assertEqual(info["background"] == 0, profile.endswith("_zero"))
            if profile.startswith("same_signal"):
                self.assertEqual(info["cue"], info["signal"])
            elif profile.startswith("distinct_cue"):
                self.assertNotIn(info["cue"], {info["background"], info["signal"], 6})
            elif profile.startswith("magenta_cue"):
                self.assertEqual(info["cue"], 6)
                self.assertNotEqual(info["signal"], 6)
            else:
                self.assertEqual(info["signal"], 6)
                self.assertNotEqual(info["cue"], 6)

    def test_boundary_profiles_cover_height_and_width_extremes(self):
        for band in ("easy", "medium", "hard"):
            minimal = MODULE.generate(31, 43, difficulty=band, scene_profile="minimal_height")
            tall = MODULE.generate(31, 43, difficulty=band, scene_profile="tall_stripe")
            wide = MODULE.generate(31, 43, difficulty=band, scene_profile="wide_stripe")
            self.assertEqual(len(minimal), 3)
            self.assertGreaterEqual(len(tall), 15)
            self.assertGreaterEqual(len(wide[0]), 16)
            self.assertEqual(MODULE.observe_overrides(minimal)["scene_profile"], "minimal_height")
            self.assertEqual(MODULE.observe_overrides(tall)["scene_profile"], "tall_stripe")
            self.assertEqual(MODULE.observe_overrides(wide)["scene_profile"], "wide_stripe")

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
            self.assertGreater(strict, 190)
            self.assertLess(strict, 310)
            self.assertGreater(len(inputs), 730)
            self.assertGreater(len(outputs), 700)

    def test_python_oracle_copies_two_rows_and_uses_anchor_background(self):
        grid = MODULE.generate(101, 203, difficulty="hard", scene_profile="magenta_signal_color")
        before = copy.deepcopy(grid)
        output = MODULE.rule_mirror(grid)
        background = grid[2][1]
        self.assertEqual(output[0], grid[0])
        self.assertEqual(output[1], grid[1])
        self.assertEqual(output[2], [background if value == background else 6 for value in grid[0]])
        self.assertEqual(grid, before)

    def test_self_check_rejects_nearest_impostors(self):
        base = MODULE.generate(331, 557, difficulty="medium", scene_profile="distinct_cue_color")
        info = MODULE._analysis(base)
        third = next(color for color in range(10) if color not in {info["background"], info["signal"], info["cue"], 6})
        two_signals = copy.deepcopy(base)
        signal_col = next(col for col, value in enumerate(two_signals[0]) if value == info["signal"])
        two_signals[0][signal_col] = third
        no_background = copy.deepcopy(base)
        no_background[0] = [info["signal"]] * len(no_background[0])
        one_signal = copy.deepcopy(base)
        one_signal[0] = [info["background"]] * len(one_signal[0])
        one_signal[0][0] = info["signal"]
        wrong_stripe = copy.deepcopy(base)
        wrong_stripe[2][0] = info["cue"]
        lower_decoy = copy.deepcopy(base)
        lower_decoy[2][2] = info["signal"]
        ragged = copy.deepcopy(base)
        ragged[0].pop()
        boolean = copy.deepcopy(base)
        boolean[0][0] = True
        for mutation in (two_signals, no_background, one_signal, wrong_stripe, lower_decoy, ragged, boolean):
            self.assertTrue(MODULE.self_check(mutation), mutation)

    def test_invalid_override_and_determinism_contract(self):
        for overrides in (
            {"scene_profile": "unknown"},
            {"grid_h": 20},
            {"texture": "row0_all_bg"},
        ):
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

    def test_all_rule_authorities_and_pin_are_synchronized(self):
        from solvers.grounded_rules import GROUNDED_RULES

        row = _canonical_row()
        base_path = next(
            path
            for path in (
                ROOT / "data/base/solutions/training/7e4d4f7c__235a1d06b9d3.json",
                ROOT / "shared/data/base/solutions/training/7e4d4f7c__235a1d06b9d3.json",
            )
            if path.is_file()
        )
        base = json.loads(base_path.read_text(encoding="utf-8"))
        canonical = row["program_solution"]
        self.assertEqual(_normalized_hash(base["racket_target"]["raw_code"]), _normalized_hash(canonical))
        self.assertEqual(_normalized_hash(base["racket_target"]["target_code"]), _normalized_hash(canonical))
        self.assertEqual(_normalized_hash(GROUNDED_RULES[TASK_ID]), "0df093c037e1")
        self.assertEqual(MODULE.RULE_HASH, _normalized_hash(canonical))
        self.assertEqual(MODULE.RULE_HASH, "0df093c037e1")


if __name__ == "__main__":
    unittest.main()
