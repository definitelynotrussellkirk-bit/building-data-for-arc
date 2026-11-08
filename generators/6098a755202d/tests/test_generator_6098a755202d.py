"""Focused semantic regressions for generator 6098a755202d."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

GENERATOR_PATH = REPO_ROOT / "generators" / "6098a755202d" / "generator.py"
SPEC = importlib.util.spec_from_file_location("generator_6098a755202d", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def canonical_pairs() -> list[dict]:
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") == "6098a755202d":
                test = row["test"]
                tests = test if isinstance(test, list) else [test]
                return [*row["train"], *tests]
    raise AssertionError("canonical task 6098a755202d is missing")


def as_grid(value) -> list[list[int]]:
    return [
        [int(cell) for cell in row] if isinstance(row, str) else list(row)
        for row in value
    ]


class Generator6098a755202dTests(unittest.TestCase):
    def test_self_check_accepts_every_canonical_input(self):
        for index, pair in enumerate(canonical_pairs()):
            with self.subTest(index=index):
                self.assertEqual([], GEN.self_check(as_grid(pair["input"])))

    def test_rule_mirror_solves_every_canonical_pair(self):
        for index, pair in enumerate(canonical_pairs()):
            with self.subTest(index=index):
                self.assertEqual(
                    as_grid(pair["output"]),
                    GEN.rule_mirror(as_grid(pair["input"])),
                )

    def test_three_consecutive_lessons_refute_tie_by_seed_shortcut(self):
        grids = [GEN.generate(911, index, difficulty="medium") for index in range(3)]
        observations = [GEN.semantic_observables(grid) for grid in grids]
        self.assertEqual(set(GEN.PROFILES), {item["profile"] for item in observations})

        repeated = next(
            grid
            for grid, item in zip(grids, observations)
            if item["profile"] == "same_color_tie"
        )
        repeated_obs = GEN.semantic_observables(repeated)
        self.assertGreater(repeated_obs["same_color_tie_cells"], 0)
        self.assertNotEqual(GEN.rule_mirror(repeated), GEN._tie_by_seed_rival(repeated))

    def test_all_declared_overrides_are_observable_across_profiles(self):
        cases = (
            (0, 8, 9, 1, 1, "distinct_pair"),
            (1, 10, 12, 2, 1, "same_color_tie"),
            (17, 12, 14, 2, 2, "distinct_triple"),
        )
        for seed, height, width, top, left, profile in cases:
            with self.subTest(
                seed=seed, height=height, width=width, top=top, left=left,
                profile=profile,
            ):
                grid = GEN.generate(
                    seed,
                    0,
                    difficulty="medium",
                    grid_h=height,
                    grid_w=width,
                    frame_top=top,
                    frame_left=left,
                    profile=profile,
                )
                self.assertEqual(
                    {
                        "grid_h": height,
                        "grid_w": width,
                        "frame_top": top,
                        "frame_left": left,
                        "profile": profile,
                    },
                    GEN.observe_overrides(grid),
                )
                self.assertEqual([], GEN.self_check(grid))

    def test_unknown_override_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown override"):
            GEN.generate(0, 0, banana=1)

    def test_complete_profile_cycle_makes_same_color_query_identifiable(self):
        demos = []
        for index in range(3):
            grid = GEN.generate(911, index, difficulty="medium")
            demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
        query_grid = GEN.generate(1221, 1, difficulty="medium", profile="same_color_tie")
        self.assertEqual([], GEN.lesson_identifiable(demos, {"input": query_grid}))

    def test_shortcut_analysis_replays_canonical_ambiguity_and_counterexample(self):
        tool_path = GENERATOR_PATH.parent / "workspace" / "analyze_shortcut.py"
        tool_spec = importlib.util.spec_from_file_location(
            "analyze_shortcut_6098a755202d", tool_path
        )
        self.assertIsNotNone(tool_spec)
        self.assertIsNotNone(tool_spec.loader)
        tool = importlib.util.module_from_spec(tool_spec)
        tool_spec.loader.exec_module(tool)

        report = tool.analyze(use_racket=False)
        self.assertTrue(report["rival_fits_all_canonical_pairs"])
        self.assertEqual([[2, 4, 2, 0]], report["witness"]["differences"])
        self.assertEqual([], report["witness"]["self_check_errors"])

    def test_shortcut_tool_runs_standalone_from_generator_directory(self):
        tool_path = GENERATOR_PATH.parent / "workspace" / "analyze_shortcut.py"
        completed = subprocess.run(
            [sys.executable, str(tool_path), "--compact"],
            cwd=GENERATOR_PATH.parent,
            env={"PATH": "/usr/bin:/bin", "PYTHONPATH": ""},
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertTrue(report["rival_fits_all_canonical_pairs"])

    def test_shortcut_tool_builds_racket_application_without_runtime_scripts(self):
        tool_path = GENERATOR_PATH.parent / "workspace" / "analyze_shortcut.py"
        tool_spec = importlib.util.spec_from_file_location(
            "analyze_shortcut_racket_application", tool_path
        )
        self.assertIsNotNone(tool_spec)
        self.assertIsNotNone(tool_spec.loader)
        tool = importlib.util.module_from_spec(tool_spec)
        tool_spec.loader.exec_module(tool)

        from puzzle_generators.rule_wrap import wrap_rule

        program = "(rule! g)"
        expected = f"({wrap_rule(program)} '((1 0) (0 1)))"
        self.assertEqual(expected, tool._rule_application(program, [[1, 0], [0, 1]]))


if __name__ == "__main__":
    unittest.main()
