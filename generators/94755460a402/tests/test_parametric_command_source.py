from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id


TASK_ID = "94755460a402"
ROOT = find_root(__file__)
HERE = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_test_94755460a402_parametric", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        programs = {
            row["program_solution"]
            for line in handle
            if line.strip()
            for row in [json.loads(line)]
            if row.get("task_id") == TASK_ID
        }
    if len(programs) != 1:
        raise AssertionError(f"expected one canonical program, found {len(programs)}")
    return next(iter(programs))


class ParametricCommandSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = load_prototype()

    def test_default_program_is_byte_exact_canonical_authority(self):
        source = canonical_program()
        self.assertEqual(self.p.program({"command_source": "header"}), source)
        self.assertEqual((HERE / "canonical.rkt").read_text(encoding="utf-8"), source)
        self.assertNotEqual(
            self.p.program({"command_source": "selected_marker"}), source
        )

    def test_settings_and_count_contract_is_strict(self):
        for bad in (
            None,
            {},
            {"command_source": "bad"},
            {"command_source": "header", "extra": 1},
            {"command_source": True},
        ):
            with self.assertRaises(ValueError):
                self.p.program(bad)
        for args in ((-1, 2, 4), (2**63, 2, 4), (0, 1, 4), (0, 7, 4), (0, 2, 3), (0, 2, 5)):
            with self.assertRaises(ValueError):
                self.p.generate(
                    args[0], {"command_source": "header"}, demos=args[1], queries=args[2]
                )

    def test_matched_inputs_counts_determinism_and_prefixes(self):
        settings = (
            {"command_source": "header"},
            {"command_source": "selected_marker"},
        )
        for seed in (0, 17, 991):
            episodes = [self.p.generate(seed, s, demos=6, queries=4) for s in settings]
            self.assertEqual(
                [[pair["input"] for split in ("train", "test") for pair in ep[split]]
                 for ep in episodes[:1]],
                [[pair["input"] for split in ("train", "test") for pair in episodes[1][split]]],
            )
            self.assertEqual(episodes[0], self.p.generate(seed, settings[0], demos=6, queries=4))
            keys = [
                json.dumps(pair["input"], separators=(",", ":"))
                for pair in episodes[0]["train"] + episodes[0]["test"]
            ]
            self.assertEqual(len(keys), len(set(keys)))
            short = self.p.generate(seed, settings[0], demos=2, queries=4)
            self.assertEqual(short["train"], episodes[0]["train"][:2])
            self.assertEqual(short["test"], episodes[0]["test"])

    def test_minimum_demonstrations_identify_each_setting_against_declared_rivals(self):
        for seed in (0, 17, 991):
            for source in ("header", "selected_marker"):
                episode = self.p.generate(
                    seed, {"command_source": source}, demos=2, queries=4
                )
                report = self.p.teaching_check(episode)
                self.assertTrue(report["ok"], report)
                self.assertEqual(report["survivors"], [source])
                self.assertEqual(report["ambiguities"], [])
                self.assertGreaterEqual(report["rivals_tested"], 12)

    def test_minimum_demonstrations_defeat_selector_mod_shortcut_across_bounded_seed_sweep(self):
        for seed in range(64):
            for source in ("header", "selected_marker"):
                episode = self.p.generate(
                    seed, {"command_source": source}, demos=2, queries=4
                )
                report = self.p.teaching_check(episode)
                self.assertTrue(report["ok"], (seed, source, report))
                self.assertNotIn("selector_mod_five", report["survivors"])

    def test_scene_semantics_and_all_transform_branches_are_exercised(self):
        header_codes = set()
        marker_codes = set()
        for seed in range(10):
            episode = self.p.generate(
                seed, {"command_source": "selected_marker"}, demos=6, queries=4
            )
            for pair in episode["train"] + episode["test"]:
                info = self.p.analyze(pair["input"])
                self.assertIn(info["frame_count"], (2, 3, 4))
                self.assertEqual(pair["output"], self.p.solve(
                    pair["input"], {"command_source": "selected_marker"}
                ))
                header_codes.add(info["header_command"])
                marker_codes.add(info["selected_marker"])
        self.assertEqual(header_codes, {1, 2, 3, 4, 5})
        self.assertEqual(marker_codes, {1, 2, 3, 4, 5})

    def test_fourth_query_is_substantive_exact_30x30_boundary_stress(self):
        episode = self.p.generate(
            17, {"command_source": "selected_marker"}, demos=3, queries=4
        )
        grid = episode["test"][3]["input"]
        self.assertEqual((len(grid), len(grid[0])), (30, 30))
        info = self.p.analyze(grid)
        self.assertEqual(info["frame_count"], 4)
        self.assertGreater(sum(v != 0 for row in grid for v in row), 180)
        boundary = (
            any(grid[0][c] != 0 for c in range(30)),
            any(grid[29][c] != 0 for c in range(30)),
            any(grid[r][0] != 0 for r in range(30)),
            any(grid[r][29] != 0 for r in range(30)),
        )
        self.assertEqual(boundary, (True, True, True, True))
        self.assertGreaterEqual(len(info["cropped"]), 8)
        self.assertGreaterEqual(len(info["cropped"][0]), 8)

    def test_public_projection_masks_private_queries_settings_and_program(self):
        episode = self.p.generate(
            17, {"command_source": "selected_marker"}, demos=3, queries=4
        )
        public = self.p.public_challenge(episode)
        raw = public_challenge_bytes(public)
        self.assertNotIn(b"command_source", raw)
        self.assertNotIn(b"rule!", raw)
        self.assertTrue(all(set(pair) == {"input"} for pair in public["test"]))
        self.assertEqual(self.p.public_turn(episode, 0), self.p.public_turn(
            {**episode, "test": episode["test"][:1]}, 0
        ))
        mutated = copy.deepcopy(episode)
        mutated["test"][0]["output"] = [[9]]
        mutated["program_solution"] = "private changed program"
        mutated["private"] = {"command_source": "header"}
        self.assertEqual(public_challenge_id(episode), public_challenge_id(mutated))

    def test_selected_marker_has_real_skip_a_counterfactual(self):
        episode = self.p.generate(
            0, {"command_source": "selected_marker"}, demos=2, queries=4
        )
        pair = episode["train"][0]
        info = self.p.analyze(pair["input"])
        self.assertNotEqual(info["header_command"], info["selected_marker"])
        intended = self.p.solve(pair["input"], {"command_source": "selected_marker"})
        skipped = self.p.solve(pair["input"], {"command_source": "header"})
        self.assertNotEqual(intended, skipped)
        self.assertEqual(self.p.counterfactual_program("skip_a"), canonical_program())
        self.assertEqual(
            hashlib.sha256(self.p.program({"command_source": "selected_marker"}).encode()).hexdigest(),
            hashlib.sha256((HERE / "selected-marker.rkt").read_bytes()).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
