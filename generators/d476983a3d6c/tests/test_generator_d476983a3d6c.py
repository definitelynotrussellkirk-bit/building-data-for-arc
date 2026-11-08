"""Focused semantic regressions for L-path task d476983a3d6c."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import unittest
from pathlib import Path

from reviewer_support import canonical_path, find_root

TASK_ID = "d476983a3d6c"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = HOME / "generator.py"
spec = importlib.util.spec_from_file_location(f"review_generator_{TASK_ID}", GENERATOR_PATH)
assert spec is not None and spec.loader is not None
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def _canonical_task():
    path = canonical_path(ROOT)
    with path.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"canonical task {TASK_ID} not found")


def _pairs(row, split):
    value = row[split]
    return value if isinstance(value, list) else [value]


class TestCanonicalAuthority(unittest.TestCase):
    def test_rule_hash_matches_canonical_program(self):
        task = _canonical_task()
        source = task["program_solution"]
        actual = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
        self.assertEqual(gen.RULE_HASH, actual)

    def test_canonical_inputs_are_accepted_and_mirrored_exactly(self):
        task = _canonical_task()
        for split in ("train", "test"):
            for index, pair in enumerate(_pairs(task, split)):
                input_grid = [[int(v) for v in row] for row in pair["input"]]
                output_grid = [[int(v) for v in row] for row in pair["output"]]
                self.assertEqual(
                    gen.self_check(input_grid),
                    [],
                    f"canonical {split}[{index}] rejected",
                )
                self.assertEqual(
                    gen._rule_mirror(input_grid),
                    output_grid,
                    f"canonical {split}[{index}] mirror mismatch",
                )


class TestExactAxesAndProfiles(unittest.TestCase):
    def test_exact_axes_are_observable_in_every_band(self):
        for band in ("easy", "medium", "hard"):
            for scene_profile in gen.SCENE_PROFILES:
                for grid_profile in gen.GRID_PROFILES:
                    grid = gen.generate(
                        9137,
                        29,
                        difficulty=band,
                        scene_profile=scene_profile,
                        grid_profile=grid_profile,
                    )
                    self.assertEqual(gen.self_check(grid), [])
                    self.assertEqual(
                        gen.observe_overrides(grid),
                        {
                            "scene_profile": scene_profile,
                            "grid_profile": grid_profile,
                        },
                    )

    def test_generated_profiles_carry_the_teaching_features(self):
        expected = {
            "cmd1_three_pairs": {
                "command": 1,
                "pair_count": 3,
                "singleton_count": 0,
                "aligned": True,
                "overlap": True,
            },
            "cmd2_two_pairs": {
                "command": 2,
                "pair_count": 2,
                "singleton_count": 0,
                "aligned": False,
                "overlap": True,
            },
            "cmd1_two_pairs_singleton": {
                "command": 1,
                "pair_count": 2,
                "singleton_count": 1,
                "aligned": False,
                "overlap": False,
            },
            "cmd2_three_pairs_singleton": {
                "command": 2,
                "pair_count": 3,
                "singleton_count": 1,
                "aligned": True,
                "overlap": True,
            },
        }
        for profile, want in expected.items():
            for seed in range(12):
                grid = gen.generate(
                    seed,
                    seed,
                    difficulty="medium",
                    scene_profile=profile,
                    grid_profile="canonical",
                )
                analysis = gen._analyze(grid)
                self.assertEqual(analysis["errors"], [], (profile, seed))
                facts = analysis["facts"]
                self.assertEqual(facts["command"], want["command"])
                self.assertEqual(facts["pair_count"], want["pair_count"])
                self.assertEqual(facts["singleton_count"], want["singleton_count"])
                self.assertEqual(bool(facts["aligned_colors"]), want["aligned"])
                self.assertEqual(bool(facts["overlap_cells"]), want["overlap"])
                if want["overlap"]:
                    self.assertNotEqual(
                        gen._reverse_pair_priority(grid),
                        gen._rule_mirror(grid),
                    )

    def test_invalid_contract_inputs_reject_loudly(self):
        bad = (
            {"scene_profile": "cmd3_two_pairs"},
            {"grid_profile": "tiny"},
            {"unknown_axis": True},
        )
        for kwargs in bad:
            with self.assertRaises(ValueError, msg=f"did not reject {kwargs}"):
                gen.generate(1, 2, **kwargs)
        with self.assertRaises(ValueError):
            gen.generate(1, 2, difficulty="extreme")


class TestLessonIdentifiability(unittest.TestCase):
    def test_every_rotated_five_pair_window_refutes_all_named_rivals(self):
        for band in ("easy", "medium", "hard"):
            for start in range(12):
                pairs = []
                for offset in range(5):
                    sample_index = start + offset
                    grid = gen.generate(
                        70_000 + start,
                        sample_index,
                        difficulty=band,
                    )
                    pairs.append({"input": grid, "output": gen._rule_mirror(grid)})
                for held_out in range(5):
                    demos = [pair for index, pair in enumerate(pairs) if index != held_out]
                    query = pairs[held_out]["input"]
                    self.assertEqual(
                        gen.lesson_identifiable(demos, query),
                        [],
                        f"{band=} {start=} {held_out=}",
                    )


class TestSelfCheckMutations(unittest.TestCase):
    def test_rejects_targeted_impostors(self):
        valid = gen.generate(
            41,
            0,
            difficulty="medium",
            scene_profile="cmd1_three_pairs",
            grid_profile="canonical",
        )
        mutations = {}

        no_command = copy.deepcopy(valid)
        no_command[0][0] = 0
        mutations["missing command"] = no_command

        repeated_command = copy.deepcopy(valid)
        empty = next(
            (r, c)
            for r in range(1, len(repeated_command))
            for c in range(len(repeated_command[0]))
            if repeated_command[r][c] == 0
        )
        repeated_command[empty[0]][empty[1]] = repeated_command[0][0]
        mutations["repeated command color"] = repeated_command

        triple = copy.deepcopy(valid)
        facts = gen._analyze(triple)["facts"]
        color = facts["pair_colors"][0]
        empty = next(
            (r, c)
            for r in range(1, len(triple))
            for c in range(len(triple[0]))
            if triple[r][c] == 0 and (r, c) not in facts["path_cells"]
        )
        triple[empty[0]][empty[1]] = color
        mutations["three markers of one color"] = triple

        all_aligned = [[0 for _ in range(9)] for _ in range(9)]
        all_aligned[0][0] = 1
        for color, row in zip((2, 3, 4), (2, 4, 6)):
            all_aligned[row][1] = color
            all_aligned[row][7] = color
        mutations["command-invisible all-aligned scene"] = all_aligned

        for name, grid in mutations.items():
            self.assertTrue(gen.self_check(grid), f"accepted impostor: {name}")
            with self.assertRaises(ValueError, msg=f"observed impostor: {name}"):
                gen.observe_overrides(grid)


class TestDeterminism(unittest.TestCase):
    def test_replay_freshness_and_process_rng_state(self):
        random.seed(0xD476983)
        before = random.getstate()
        first = gen.generate(12345, 678, difficulty="hard")
        after = random.getstate()
        second = gen.generate(12345, 678, difficulty="hard")
        self.assertEqual(before, after)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertTrue(all(a is not b for a, b in zip(first, second)))
        snapshot = copy.deepcopy(second)
        first[0][0] = 9
        self.assertEqual(second, snapshot)


class TestWorkspaceProbe(unittest.TestCase):
    def test_profile_probe_builds_source_bound_report(self):
        path = HOME / "workspace" / "profile_probe.py"
        self.assertTrue(path.is_file(), "missing reusable profile probe")
        probe_spec = importlib.util.spec_from_file_location(
            f"profile_probe_{TASK_ID}", path
        )
        assert probe_spec is not None and probe_spec.loader is not None
        probe = importlib.util.module_from_spec(probe_spec)
        probe_spec.loader.exec_module(probe)
        report = probe.build_report(per_band=4, window_starts=4)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["task_id"], TASK_ID)
        self.assertEqual(report["draws_total"], 12)
        self.assertEqual(report["rotation_failures"], [])
        self.assertIn("drop_singletons", report["canonical_train_fitting_shortcuts"])
        self.assertIsNotNone(
            report["shortcut_counterexamples"]["drop_singletons"]
        )


if __name__ == "__main__":
    unittest.main()
