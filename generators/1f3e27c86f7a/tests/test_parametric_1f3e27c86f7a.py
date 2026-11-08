"""Independent tests for the proposed task-local parametric prototype only."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType

from reviewer_support import (
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "1f3e27c86f7a"
TASK_DIR = Path(__file__).resolve().parents[1]
REPO = TASK_DIR.parents[1]
PROTOTYPE = TASK_DIR / "workspace/parametric/prototype.py"
BRANCHES = {
    "proportional", "top_align", "bottom_align",
    "left_align", "right_align", "stripe",
}


def literal_witness():
    """Two bordered rectangles; expected labels are independent literal rows."""
    grid = [[0] * 24 for _ in range(20)]
    for r in range(1, 9):
        for c in range(1, 11):
            grid[r][c] = 2
    for r, row in enumerate((
        [3, 3, 3, 4, 4, 4], [3, 3, 3, 4, 4, 4],
        [5, 5, 5, 6, 6, 6], [5, 5, 5, 6, 6, 6],
    ), start=3):
        grid[r][3:9] = row
    for r in range(12, 19):
        for c in range(11, 22):
            grid[r][c] = 2
    expected = {}
    for orientation, rows in {
        "identity": [
            [3, 3, 3, 3, 4, 4, 4],
            [5, 5, 5, 5, 6, 6, 6],
            [5, 5, 5, 5, 6, 6, 6],
        ],
        "mirror_lr": [
            [4, 4, 4, 4, 3, 3, 3],
            [6, 6, 6, 6, 5, 5, 5],
            [6, 6, 6, 6, 5, 5, 5],
        ],
    }.items():
        output = copy.deepcopy(grid)
        for r, row in enumerate(rows, start=14):
            output[r][13:20] = row
        expected[orientation] = output
    return grid, expected


class Parametric1f3e27c86f7aTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert PROTOTYPE.is_file(), f"Missing proposed feature: {PROTOTYPE}"
        spec = importlib.util.spec_from_file_location("_task_parametric_test", PROTOTYPE)
        cls.prototype = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.prototype
        spec.loader.exec_module(cls.prototype)
        cls.generator, _, _ = load_selected_generator(TASK_ID, root=REPO)
        cls.runner_context = cls.prototype.RuleRunner()
        cls.runner = cls.runner_context.__enter__()
        cls.addClassCleanup(cls.runner_context.__exit__, None, None, None)
        cls.episodes = {}

    def episode(self, demo_count=6):
        if demo_count not in self.episodes:
            self.episodes[demo_count] = self.prototype.build_episode(
                37, "mirror_lr", demo_count=demo_count,
                query_count=4, runner=self.runner,
            )
        return copy.deepcopy(self.episodes[demo_count])

    def branch(self, grid):
        return self.generator.observe_overrides(grid)["rule_branch"]

    def test_default_program_is_exact_canonical_authority(self):
        with (REPO / "shared/data/canonical/puzzles.jsonl").open() as handle:
            row = next(json.loads(line) for line in handle
                       if json.loads(line).get("task_id") == TASK_ID)
        self.assertEqual(row["program_solution"], self.prototype.canonical_program())
        self.assertEqual(row["program_solution"], self.prototype.program_for())
        self.assertEqual(row["program_solution"], self.prototype.program_for("identity"))
        self.assertNotEqual(row["program_solution"], self.prototype.program_for("mirror_lr"))

    def test_compiler_rejects_cached_parser_from_a_different_tree(self):
        # A real parser from a foreign checkout must not be reused merely
        # because its parent namespace was removed or looks local.
        source = REPO / "shared/tools/comment_solutions.py"
        saved = {name: value for name, value in sys.modules.items()
                 if name == "scripts" or name.startswith("scripts.")}
        with tempfile.TemporaryDirectory() as directory:
            foreign_path = Path(directory) / "comment_solutions.py"
            foreign_path.write_bytes(source.read_bytes())
            for parent_present in (False, True):
                with self.subTest(parent_present=parent_present):
                    try:
                        for name in list(sys.modules):
                            if name == "scripts" or name.startswith("scripts."):
                                del sys.modules[name]
                        spec = importlib.util.spec_from_file_location("scripts.comment_solutions", foreign_path)
                        foreign = importlib.util.module_from_spec(spec)
                        sys.modules[spec.name] = foreign
                        spec.loader.exec_module(foreign)
                        if parent_present:
                            parent = ModuleType("scripts")
                            parent.__path__ = [str(REPO / "shared/tools")]
                            sys.modules["scripts"] = parent
                        with self.assertRaises(ImportError):
                            self.prototype._wrapped_program(self.prototype.canonical_program())
                    finally:
                        for name in list(sys.modules):
                            if name == "scripts" or name.startswith("scripts."):
                                del sys.modules[name]
                        sys.modules.update(saved)

    def test_identity_reproduces_all_original_canonical_pairs(self):
        with (REPO / "shared/data/canonical/puzzles.jsonl").open() as handle:
            row = next(json.loads(line) for line in handle
                       if json.loads(line).get("task_id") == TASK_ID)
        for index, pair in enumerate(row["train"] + row["test"]):
            with self.subTest(index=index):
                self.assertEqual(pair["output"], self.runner.apply(pair["input"], "identity"))

    def test_literal_witness_reflects_source_before_mapping(self):
        grid, expected = literal_witness()
        pristine = copy.deepcopy(grid)
        for orientation in ("identity", "mirror_lr"):
            with self.subTest(orientation=orientation):
                self.assertEqual(expected[orientation], self.runner.apply(grid, orientation))
                self.assertEqual(pristine, grid)
        # Rounding at source index 2.5 distinguishes reflection before mapping
        # from merely reversing the already-scaled target interior.
        self.assertNotEqual(
            expected["mirror_lr"][14][13:20],
            list(reversed(expected["identity"][14][13:20])),
        )

    def test_inputs_are_deterministic_and_honor_requested_branches(self):
        for index, branch in enumerate(sorted(BRANCHES)):
            with self.subTest(branch=branch):
                first = self.prototype.generate_input(29, index, branch)
                second = self.prototype.generate_input(29, index, branch)
                self.assertEqual(first, second)
                self.assertIsNot(first, second)
                self.assertEqual([], self.generator.self_check(first))
                self.assertEqual(branch, self.branch(first))

    def test_default_episode_has_six_branches_and_four_distinct_queries(self):
        episode = self.episode()
        self.assertEqual(6, len(episode["train"]))
        self.assertEqual(4, len(episode["test"]))
        self.assertEqual(BRANCHES, {self.branch(p["input"]) for p in episode["train"]})
        inputs = [p["input"] for p in episode["train"] + episode["test"]]
        self.assertEqual(10, len({json.dumps(grid) for grid in inputs}))
        assessment = self.prototype.assess_episode(episode, self.runner)
        self.assertEqual("supported", assessment["status"])
        self.assertEqual(["mirror_lr"], assessment["parameter_candidates"])
        self.assertEqual(4, len(assessment["queries"]))
        self.assertTrue(all(row["supported"] for row in assessment["queries"]))

    def test_short_episode_restricts_queries_to_demonstrated_branches(self):
        episode = self.episode(demo_count=1)
        self.assertEqual(1, len(episode["train"]))
        self.assertEqual(4, len(episode["test"]))
        self.assertEqual("proportional", self.branch(episode["train"][0]["input"]))
        self.assertTrue(all(self.branch(p["input"]) == "proportional" for p in episode["test"]))
        self.assertEqual(5, len({json.dumps(p["input"]) for p in episode["train"] + episode["test"]}))
        self.assertEqual("supported", self.prototype.assess_episode(episode, self.runner)["status"])

    def test_count_boundaries_bands_and_seeded_parameter_are_supported(self):
        for band, demos, queries in (("easy", 1, 12), ("hard", 12, 1)):
            with self.subTest(band=band):
                episode = self.prototype.build_episode(
                    23, None, demo_count=demos, query_count=queries,
                    difficulty=band, runner=self.runner,
                )
                self.assertEqual(demos, len(episode["train"]))
                self.assertEqual(queries, len(episode["test"]))
                pairs = episode["train"] + episode["test"]
                self.assertEqual(demos + queries, len({json.dumps(p["input"]) for p in pairs}))
                chosen = episode["parameters"]["payload_orientation"]
                self.assertIn(chosen, ("identity", "mirror_lr"))
                for pair in pairs:
                    self.assertEqual(pair["output"], self.runner.apply(pair["input"], chosen))
                self.assertEqual("supported", self.prototype.assess_episode(episode, self.runner)["status"])

    def test_identifiability_does_not_read_query_answers(self):
        episode = self.episode()
        baseline = self.prototype.assess_episode(episode, self.runner)
        for pair in episode["test"]:
            pair["output"] = [[9]]
        masked = self.prototype.assess_episode(episode, self.runner)
        for pair in episode["test"]:
            del pair["output"]
        absent = self.prototype.assess_episode(episode, self.runner)
        for field in ("status", "parameter_candidates", "queries", "branch_coverage"):
            self.assertEqual(baseline[field], masked[field])
            self.assertEqual(baseline[field], absent[field])

    def test_undemonstrated_query_branch_is_unsupported(self):
        episode = self.episode(demo_count=1)
        episode["test"][-1]["input"] = self.prototype.generate_input(101, 9, "stripe")
        episode["test"][-1].pop("output", None)
        assessment = self.prototype.assess_episode(episode, self.runner)
        self.assertEqual("unsupported", assessment["status"])
        self.assertFalse(assessment["queries"][-1]["supported"])
        self.assertTrue(assessment["queries"][-1]["reasons"])

    def test_writer_uses_exact_visible_bytes_and_opaque_names(self):
        episode = self.episode()
        altered = copy.deepcopy(episode)
        altered["seed"] = 999_999
        altered["private_test_note"] = "must not affect public content or names"
        for pair in altered["test"]:
            pair["output"] = [[9]]
        name = public_challenge_id(episode)
        self.assertEqual(name, public_challenge_id(altered))
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / "first", Path(directory) / "second"
            self.prototype.write_batch([episode], first)
            self.prototype.write_batch([altered], second)
            for root in (first, second):
                public_path = root / "public" / f"{name}.json"
                self.assertEqual([public_path], list((root / "public").iterdir()))
                self.assertEqual(public_challenge_bytes(episode), public_path.read_bytes())
                visible = json.loads(public_path.read_bytes())
                self.assertEqual({"train", "test"}, set(visible))
                self.assertTrue(all(set(pair) == {"input"} for pair in visible["test"]))
                self.assertTrue((root / "private" / f"{name}.json").is_file())
                self.assertTrue((root / "private/index.json").is_file())
                self.assertTrue(list((root / "private/programs").glob("*.rkt")))

    def test_writer_rejects_duplicate_payloads_and_nonempty_destinations(self):
        episode = self.episode()
        with tempfile.TemporaryDirectory() as directory:
            duplicate = Path(directory) / "duplicates"
            with self.assertRaises(ValueError):
                self.prototype.write_batch([episode, copy.deepcopy(episode)], duplicate)
            self.assertFalse(duplicate.exists() and any(duplicate.iterdir()))
            occupied = Path(directory) / "occupied"
            occupied.mkdir()
            marker = occupied / "keep.txt"
            marker.write_text("preserve")
            with self.assertRaises(ValueError):
                self.prototype.write_batch([episode], occupied)
            self.assertEqual("preserve", marker.read_text())
            self.assertEqual([marker], list(occupied.iterdir()))

    def test_invalid_counts_and_orientation_fail_loudly(self):
        for field in ("demo_count", "query_count"):
            for value in (0, 13, True, 1.5, "2"):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    self.prototype.build_episode(1, "identity", runner=self.runner, **{field: value})
        for invalid in ("mirror_ud", "unknown", ""):
            with self.subTest(orientation=invalid), self.assertRaises(ValueError):
                self.prototype.program_for(invalid)
            with self.subTest(episode_orientation=invalid), self.assertRaises(ValueError):
                self.prototype.build_episode(1, invalid, runner=self.runner)


if __name__ == "__main__":
    unittest.main()
