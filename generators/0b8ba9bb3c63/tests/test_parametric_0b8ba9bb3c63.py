"""Finite, real-Racket checks for the unapproved beam-axes prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import tempfile
import unittest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK_ID = "0b8ba9bb3c63"
ROOT = find_root(__file__)
PROTOTYPE = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"


def ray_oracle(grid, axes):
    """Cellwise ray walk; independent of the Racket bounding-box reductions."""
    cyan = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
    top, bottom = min(r for r, _ in cyan), max(r for r, _ in cyan)
    left, right = min(c for _, c in cyan), max(c for _, c in cyan)
    result = copy.deepcopy(grid)
    starts = []
    if axes in ("both", "horizontal"):
        starts.extend((r, left - 1, 0, -1) for r in range(top, bottom + 1))
        starts.extend((r, right + 1, 0, 1) for r in range(top, bottom + 1))
    if axes in ("both", "vertical"):
        starts.extend((top - 1, c, -1, 0) for c in range(left, right + 1))
        starts.extend((bottom + 1, c, 1, 0) for c in range(left, right + 1))
    for r, c, dr, dc in starts:
        while 0 <= r < len(grid) and 0 <= c < len(grid[0]):
            if grid[r][c] not in (0, 2):
                break
            result[r][c] = 4
            r, c = r + dr, c + dc
    return result


class ParametricBeamAxesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not PROTOTYPE.is_file():
            raise AssertionError("Missing episode-level beam_axes prototype: " + str(PROTOTYPE))
        spec = importlib.util.spec_from_file_location("beam_axes_prototype", PROTOTYPE)
        cls.prototype = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(cls.prototype)
        cls.generator, cls.generator_path, cls.generator_sha = load_selected_generator(TASK_ID, root=ROOT)
        cls.bridge = RacketBridge(timeout=20.0)
        cls.addClassCleanup(cls.bridge.shutdown)

    def test_canonical_default_program_is_exact_selected_authority(self):
        sources = set()
        with canonical_path(ROOT).open(encoding="utf-8") as stream:
            for line in stream:
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    sources.add(row["program_solution"])
        self.assertEqual(len(sources), 1)
        self.assertEqual(self.prototype.DEFAULT_AXES, "both")
        self.assertEqual(self.prototype.rule_source(), sources.pop())
        self.assertEqual(self.prototype.ALLOWED_AXES, ("both", "horizontal", "vertical"))

    def test_canonical_default_executes_all_twelve_official_occurrences(self):
        pairs = canonical_pairs(TASK_ID, root=ROOT)
        self.assertEqual(len(pairs), 12)
        for pair in pairs:
            with self.subTest(variant=pair["variant"], split=pair["split"], pair=pair["pair_index"]):
                self.assertEqual(
                    self.prototype.apply_rule(self.bridge, "both", pair["input"]), pair["output"]
                )

    def test_input_construction_is_deterministic_lawful_and_parameter_independent(self):
        before = random.getstate()
        for seed in (0, 11, 47, 2**64 - 1):
            for index in range(4):
                grid = self.prototype.make_input(seed, index)
                self.assertEqual(grid, self.prototype.make_input(seed, index))
                self.assertEqual(self.generator.self_check(grid), [])
                self.assertNotIn(4, {value for row in grid for value in row})
                if index == 3:
                    self.assertEqual((len(grid), len(grid[0])), (30, 30))
        self.assertEqual(random.getstate(), before)

    def test_real_racket_variants_preserve_semantics_and_refute_each_other(self):
        for seed in (11, 47):
            grid = self.prototype.make_input(seed, 0)
            before = copy.deepcopy(grid)
            outputs = {}
            for axes in self.prototype.ALLOWED_AXES:
                output = self.prototype.apply_rule(self.bridge, axes, grid)
                outputs[axes] = output
                self.assertEqual(output, ray_oracle(grid, axes))
                self.assertTrue(any(a == 2 and b == 4 for r, row in enumerate(grid)
                                    for c, a in enumerate(row) for b in [output[r][c]]))
                self.assertTrue(any(a == b == 2 for r, row in enumerate(grid)
                                    for c, a in enumerate(row) for b in [output[r][c]]))
                for r, row in enumerate(grid):
                    for c, value in enumerate(row):
                        if value not in (0, 2):
                            self.assertEqual(output[r][c], value)
            self.assertEqual(len({json.dumps(output) for output in outputs.values()}), 3)
            self.assertEqual(grid, before)

    def test_complete_episodes_have_all_rivals_refuted_in_production_and_rotations(self):
        for axes in self.prototype.ALLOWED_AXES:
            episode = self.prototype.build_episode(29, beam_axes=axes, bridge=self.bridge)
            private = episode["private"]
            self.assertEqual(private["parameters"], {"beam_axes": axes})
            self.assertEqual(private["identifiability"]["rivals"], [a for a in self.prototype.ALLOWED_AXES if a != axes])
            self.assertEqual(private["identifiability"]["production"]["status"], "pass")
            rotations = private["identifiability"]["rotations"]
            self.assertEqual(len(rotations), 4)
            self.assertEqual([row["query_index"] for row in rotations], list(range(4)))
            for row in rotations:
                self.assertEqual(row["status"], "pass")
                for rival in row["rivals"]:
                    self.assertTrue(rival["refuting_demo_indices"])
                    self.assertNotIn(row["query_index"], rival["refuting_demo_indices"])
                    self.assertTrue(rival["query_differs"])

    def test_public_projection_contains_only_visible_arc_pairs(self):
        episode = self.prototype.build_episode(11, beam_axes="vertical", bridge=self.bridge)
        public, private = episode["public"], episode["private"]
        self.assertEqual(set(public), {"train", "test"})
        self.assertEqual(len(public["train"]), 3)
        self.assertEqual(len(public["test"]), 1)
        self.assertTrue(all(set(pair) == {"input", "output"} for pair in public["train"]))
        self.assertEqual(set(public["test"][0]), {"input"})
        self.assertEqual(private["answers"][0], ray_oracle(public["test"][0]["input"], "vertical"))
        self.assertEqual(private["rule"]["sha256"], hashlib.sha256(private["rule"]["text"].encode()).hexdigest())
        self.assertEqual(private["selected_generator_sha256"], self.generator_sha)
        self.assertEqual(private["approval_status"], "prototype_unapproved")

    def test_seed_draws_rule_once_and_reproduction_is_exact(self):
        chosen = {self.prototype.choose_axes(seed) for seed in range(100)}
        self.assertEqual(chosen, set(self.prototype.ALLOWED_AXES))
        first = self.prototype.build_episode(47, beam_axes=None, bridge=self.bridge)
        second = self.prototype.build_episode(47, beam_axes=None, bridge=self.bridge)
        self.assertEqual(first, second)
        chosen_axes = first["private"]["parameters"]["beam_axes"]
        self.assertEqual(chosen_axes, self.prototype.choose_axes(47))
        for pair in first["public"]["train"]:
            self.assertEqual(pair["output"], ray_oracle(pair["input"], chosen_axes))

    def test_invalid_controls_fail_before_execution(self):
        for axes in ("diagonal", "", True, 4):
            with self.subTest(axes=axes):
                with self.assertRaises(ValueError):
                    self.prototype.build_episode(0, beam_axes=axes, bridge=self.bridge)
        for seed in (True, -1, 2**64, 1.5, "1"):
            with self.subTest(seed=seed):
                with self.assertRaises(ValueError):
                    self.prototype.make_input(seed, 0)
        for index in (-1, 4, True):
            with self.subTest(index=index):
                with self.assertRaises(ValueError):
                    self.prototype.make_input(0, index)

    def test_export_has_real_runtime_identity_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory(prefix="beam-axes-export-") as directory:
            out = Path(directory) / "episode"
            summary = self.prototype.write_evidence(out, seeds=[11], beam_axes="horizontal")
            self.assertEqual(summary["status"], "pass")
            self.assertEqual(summary["racket_runtime"]["backend"], "racket")
            self.assertTrue(summary["racket_runtime"]["binary_sha256"])
            self.assertEqual(summary["counts"]["episodes"], 1)
            self.assertEqual(summary["counts"]["rotation_rival_checks"], 8)
            public = json.loads((out / "episode-001.challenge.json").read_text())
            private = json.loads((out / "episode-001.private.json").read_text())
            self.assertEqual(set(public["test"][0]), {"input"})
            self.assertEqual(private["answers"][0], ray_oracle(public["test"][0]["input"], "horizontal"))
            with self.assertRaises(FileExistsError):
                self.prototype.write_evidence(out, seeds=[11], beam_axes="horizontal")


if __name__ == "__main__":
    unittest.main()
