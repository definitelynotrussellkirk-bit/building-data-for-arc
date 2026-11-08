"""Prototype-only tests; these do not approve the canonical generator.

Run from the repository with its runtime and tools on PYTHONPATH.  During
isolated development, ARCPARAMETRIC_REPO may name that same packet repository.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest


TASK_ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = TASK_ROOT / "workspace" / "parametric" / "prototype.py"


def repository_root():
    explicit = os.environ.get("ARCPARAMETRIC_REPO")
    if explicit:
        return Path(explicit).resolve()
    for parent in Path(__file__).resolve().parents:
        if any((parent / relative).is_file() for relative in (
                "shared/data/canonical/puzzles.jsonl", "data/canonical/puzzles.jsonl")):
            return parent
    raise AssertionError("Cannot locate packet repository for canonical controls")


def role_fixture():
    """Hand-designed partial blockers, nearest stops, and transparent fragments."""
    grid = [[0] * 17 for _ in range(17)]
    for color, r1, c1, r2, c2 in (
        (8, 6, 6, 9, 9), (2, 5, 3, 7, 4), (3, 3, 5, 4, 7),
        (1, 6, 11, 7, 12), (1, 7, 15, 9, 15), (5, 12, 8, 13, 9),
        (2, 14, 1, 15, 2),
    ):
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                grid[row][col] = color
    return grid


class ParametricCLITests(unittest.TestCase):
    def test_runnable_command_writes_requested_episode(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "cli"
            result = subprocess.run(
                [sys.executable, str(PROTOTYPE_PATH), "--seed", "23",
                 "--transparent-color", "3", "--demos", "1", "--queries", "4",
                 "--height", "17", "--width", "17", "--out", str(destination)],
                capture_output=True, text=True, timeout=90,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = json.loads(result.stdout)
            self.assertEqual((receipt["demos"], receipt["queries"]), (1, 4))
            public = json.loads((destination / "challenge.json").read_text())
            self.assertEqual(len(public["test"]), 4)
            self.assertTrue(all(set(pair) == {"input"} for pair in public["test"]))


@unittest.skipUnless(PROTOTYPE_PATH.is_file(), "Prototype not implemented yet")
class ParametricPrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not PROTOTYPE_PATH.is_file():
            raise AssertionError("The requested parametric prototype is not implemented")
        spec = importlib.util.spec_from_file_location("beam_parametric_prototype", PROTOTYPE_PATH)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)
        from arc_repl.racket_bridge import RacketBridge
        cls.bridge = RacketBridge(timeout=15)
        cls.addClassCleanup(cls.bridge.close)
        cls.repo = repository_root()
        cls.episodes = {}

    def episode(self, color):
        if color not in self.episodes:
            self.episodes[color] = self.module.generate_episode(
                seed=17, transparent_color=color, demo_count=3, query_count=4,
                height=20, width=22, bridge=self.bridge,
            )
        return copy.deepcopy(self.episodes[color])

    def test_default_executes_the_unmodified_canonical_rule_on_all_six_inputs(self):
        relative = "base/solutions/training/6ffe8f07__0b8ba9bb3c63.json"
        path = next(path for path in (self.repo / "shared/data" / relative,
                                      self.repo / "data" / relative) if path.is_file())
        source = json.loads(path.read_text())
        canonical_rule = source["racket_target"]["raw_code"]
        pairs = source["visible_context"]["train"] + [
            {"input": query["input"], "output": output}
            for query, output in zip(source["visible_context"]["test_inputs"],
                                    source["verification"]["expected_test_outputs"])
        ]
        self.assertEqual(len(pairs), 6)
        for pair in pairs:
            with self.subTest(shape=(len(pair["input"]), len(pair["input"][0]))):
                independently_executed = self.module.execute_program(
                    canonical_rule, pair["input"], self.bridge)
                actual = self.module.execute_program(
                    self.module.materialize_rule(), pair["input"], self.bridge)
                self.assertEqual(actual, independently_executed)
                self.assertEqual(actual, pair["output"])
        self.assertEqual(self.module.materialize_rule(), canonical_rule)

    def test_parameter_changes_roles_without_erasing_off_beam_fragments(self):
        grid = role_fixture()
        before = copy.deepcopy(grid)
        red = self.module.execute_program(self.module.materialize_rule(2), grid, self.bridge)
        green = self.module.execute_program(self.module.materialize_rule(3), grid, self.bridge)
        self.assertEqual(red[6], [4, 4, 4, 4, 4, 4, 8, 8, 8, 8, 4, 1, 1, 0, 0, 0, 0])
        self.assertEqual(green[6], [0, 0, 0, 2, 2, 4, 8, 8, 8, 8, 4, 1, 1, 0, 0, 0, 0])
        self.assertEqual(red[3][5:10], [3, 3, 3, 4, 4])
        self.assertEqual(green[3][5:10], [3, 4, 4, 4, 4])
        self.assertEqual(red[5][3:5], [2, 2])
        self.assertEqual(red[14][1:3], [2, 2])
        self.assertEqual(grid, before)

    def test_rays_clip_individually_at_the_nearest_opaque_object(self):
        output = self.module.execute_program(self.module.materialize_rule(), role_fixture(), self.bridge)
        # Row 7 sees both right blockers; row 8 sees only the far one.
        self.assertEqual(output[7][10:17], [4, 1, 1, 0, 0, 1, 0])
        self.assertEqual(output[8][10:17], [4, 4, 4, 4, 4, 1, 0])
        # Only the last two columns of the vertical band hit the lower blocker.
        self.assertEqual(output[14][6:10], [4, 4, 0, 0])

    def test_both_settings_emit_four_distinct_racket_labeled_queries(self):
        for color in (2, 3):
            episode = self.episode(color)
            self.assertEqual(episode["parameters"], {"transparent_color": color})
            self.assertEqual((len(episode["train"]), len(episode["test"])), (3, 4))
            pairs = episode["train"] + episode["test"]
            self.assertEqual(len({json.dumps(pair["input"]) for pair in pairs}), 7)
            for pair in pairs:
                self.assertEqual(pair["output"], self.module.execute_program(
                    episode["rule_source"], pair["input"], self.bridge))
            self.assertEqual(episode["identifiability"]["compatible_rules"], [f"transparent-{color}"])
            self.assertEqual(len(episode["identifiability"]["query_checks"]), 4)
            self.assertTrue(all(row["identifiable"] for row in episode["identifiability"]["query_checks"]))
        left, right = self.episode(2), self.episode(3)
        for a, b in zip(left["train"] + left["test"], right["train"] + right["test"]):
            self.assertEqual(a["input"], b["input"])
            self.assertNotEqual(a["output"], b["output"])

    def test_identifiability_reads_demonstrations_and_query_inputs_only(self):
        episode = self.episode(2)
        audit = self.module.check_identifiability(
            episode["train"], [pair["input"] for pair in episode["test"]],
            self.module.declared_programs(2), self.bridge,
        )
        self.assertEqual(audit["compatible_rules"], ["transparent-2"])
        for name, witness in audit["eliminated_rules"].items():
            self.assertIn(witness["demo_index"], range(3), name)
            self.assertGreater(witness["different_cells"], 0, name)
        # With no demonstrations, the same query inputs are ambiguous.  The
        # certification API has no query-answer argument from which to learn.
        ambiguous = self.module.check_identifiability(
            [], [pair["input"] for pair in episode["test"]],
            self.module.declared_programs(2), self.bridge,
        )
        self.assertFalse(ambiguous["identified"])
        self.assertTrue(all(not row["identifiable"] for row in ambiguous["query_checks"]))

    def test_counts_are_independent_and_seed_choice_is_fixed_for_the_episode(self):
        first = self.module.generate_episode(
            seed=19, transparent_color=None, demo_count=1, query_count=4,
            height=17, width=17, bridge=self.bridge,
        )
        second = self.module.generate_episode(
            seed=19, transparent_color=None, demo_count=1, query_count=4,
            height=17, width=17, bridge=self.bridge,
        )
        self.assertEqual(first, second)
        self.assertEqual((len(first["train"]), len(first["test"])), (1, 4))
        self.assertEqual(first["rule_source"], self.module.materialize_rule(
            first["parameters"]["transparent_color"]))

    def test_boundary_scenes_are_solid_rectangles_and_keep_exact_dimensions(self):
        random.seed(44)
        global_state = random.getstate()
        for height, width in ((17, 17), (17, 30), (30, 17), (30, 30)):
            for index in range(4):
                grid = self.module.sample_input(random.Random(index), height=height, width=width)
                self.assertEqual((len(grid), len(grid[0])), (height, width))
                self.assertEqual(self.module.validate_scene(grid), [])
                self.assertEqual({v for row in grid for v in row}, {0, 1, 2, 3, 5, 8, 9})
        self.assertEqual(random.getstate(), global_state)

    def test_public_challenge_omits_parameters_programs_and_query_outputs(self):
        episode = self.episode(3)
        public = self.module.public_challenge(episode)
        self.assertEqual(set(public), {"train", "test"})
        self.assertEqual(public["train"], episode["train"])
        self.assertTrue(all(set(pair) == {"input"} for pair in public["test"]))
        public["train"][0]["input"][0][0] = 7
        self.assertNotEqual(public["train"], episode["train"])

    def test_saved_evidence_is_exact_hashed_and_does_not_overwrite(self):
        episode = self.episode(2)
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "episode"
            self.module.write_episode(episode, destination, command="test invocation")
            manifest = json.loads((destination / "manifest.json").read_text())
            self.assertEqual(manifest["command"], "test invocation")
            for relative, expected in manifest["files_sha256"].items():
                self.assertEqual(hashlib.sha256((destination / relative).read_bytes()).hexdigest(), expected)
            self.assertEqual((destination / "rule.rkt").read_text(), episode["rule_source"])
            self.assertEqual(json.loads((destination / "challenge.json").read_text()),
                             self.module.public_challenge(episode))
            self.assertEqual(json.loads((destination / "episode.private.json").read_text()), episode)
            with self.assertRaises(FileExistsError):
                self.module.write_episode(episode, destination)

    def test_invalid_parameters_counts_dimensions_and_short_sampling_fail(self):
        for color in (True, 0, 4, "2"):
            with self.subTest(color=color), self.assertRaises(ValueError):
                self.module.materialize_rule(color)
        for options in (
            {"demo_count": 0}, {"demo_count": True}, {"query_count": 0},
            {"query_count": -1}, {"height": 16}, {"width": 31},
            {"max_attempts": 0}, {"seed": True},
        ):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.module.generate_episode(seed=options.pop("seed", 17), bridge=self.bridge, **options)
        with self.assertRaisesRegex(RuntimeError, "distinct.*requested|requested.*distinct"):
            self.module.generate_episode(seed=17, demo_count=1, query_count=4,
                                         max_attempts=1, bridge=self.bridge)

    def test_invalid_grids_and_non_grid_racket_results_fail_closed(self):
        for grid in ([], [[0], [0, 1]], [[True]], [[10]], [[0] * 31]):
            with self.subTest(grid=grid), self.assertRaises(ValueError):
                self.module.execute_program(self.module.materialize_rule(), grid, self.bridge)
        with self.assertRaisesRegex(ValueError, "Racket.*grid"):
            self.module.execute_program("(rule! (lambda (g) 7))", [[0]], self.bridge)


if __name__ == "__main__":
    unittest.main()
