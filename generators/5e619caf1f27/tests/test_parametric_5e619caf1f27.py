"""Focused contract tests for the edge-cap parametric frame family."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

for _parent in Path(__file__).resolve().parents:
    for _runtime in (_parent / "shared/runtime", _parent):
        if (_runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(_runtime))
            break
    else:
        continue
    break
from reviewer_support import (  # noqa: E402
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "5e619caf1f27"
ROOT = find_root(__file__)
SOURCE = ROOT / f"generators/{TASK_ID}/workspace/parametric/edge_cap_episodes.py"
ADAPTER = ROOT / f"generators/{TASK_ID}/workspace/parametric/adapter.py"
PROMOTION = ROOT / f"generators/{TASK_ID}/workspace/parametric/promotion.json"
GENERATOR = ROOT / f"generators/{TASK_ID}/generator.py"


def _canonical_program() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical task missing")


def _load_generator():
    spec = importlib.util.spec_from_file_location("frame_generator_for_parametric_test", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PrototypeAvailability(unittest.TestCase):
    def test_prototype_exists(self):
        self.assertTrue(SOURCE.is_file(), "edge-cap prototype is missing")


@unittest.skipUnless(SOURCE.is_file(), "prototype not implemented yet")
class ParametricEdgeCap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("edge_cap_episodes", SOURCE)
        cls.mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[spec.name] = cls.mod
        spec.loader.exec_module(cls.mod)
        cls.bridge = cls.mod.open_bridge()
        cls.generator = _load_generator()

    @classmethod
    def tearDownClass(cls):
        cls.bridge.shutdown()

    def test_default_program_is_exact_canonical_and_both_settings_execute(self):
        self.assertEqual(self.mod.PROGRAMS["capped"], _canonical_program())
        self.assertEqual(self.mod.DEFAULT_EDGE_CAP, "capped")
        grid = self.mod.sample_grid(seed=12, role="witness", index=0, height=15, width=17)
        outputs = {
            setting: self.mod.execute(self.bridge, setting, [grid])[0]
            for setting in self.mod.PROGRAMS
        }
        self.assertEqual(outputs["capped"], self.mod.python_transform(grid, "capped"))
        self.assertEqual(outputs["uncapped_inner"], self.mod.python_transform(grid, "uncapped_inner"))
        self.assertNotEqual(outputs["capped"], outputs["uncapped_inner"])

    def test_demo_counts_two_through_six_keep_four_unique_queries(self):
        for setting in self.mod.PROGRAMS:
            for demos in range(2, 7):
                with self.subTest(setting=setting, demos=demos):
                    episode = self.mod.build_episode(
                        self.bridge,
                        seed=2000 + demos,
                        edge_cap=setting,
                        n_train=demos,
                        n_test=4,
                    )
                    self.assertEqual(len(episode["train"]), demos)
                    self.assertEqual(len(episode["test"]), 4)
                    inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
                    self.assertEqual(
                        len({json.dumps(grid, separators=(",", ":")) for grid in inputs}),
                        demos + 4,
                    )
                    self.assertEqual(episode["rival_check"]["demo_survivors"], [setting])
                    self.assertTrue(episode["rival_check"]["identifiable_from_demos"])
                    self.assertTrue(
                        any(self.mod.analyze_scene(pair["input"])["edge_limited"] for pair in episode["train"])
                    )
                    for grid in inputs:
                        self.assertEqual(self.generator.strict_canonical_like(grid), [])

    def test_queries_include_substantive_30_by_30_edge_stress(self):
        episode = self.mod.build_episode(
            self.bridge, seed=909, edge_cap="capped", n_train=3, n_test=4
        )
        large = [pair["input"] for pair in episode["test"] if len(pair["input"]) == 30 and len(pair["input"][0]) == 30]
        self.assertEqual(len(large), 1)
        grid = large[0]
        analysis = self.mod.analyze_scene(grid)
        self.assertTrue(analysis["edge_limited"])
        self.assertLess(analysis["thickness"], min(analysis["inner_h"], analysis["inner_w"]))
        outputs = {setting: self.mod.execute(self.bridge, setting, [grid])[0] for setting in self.mod.PROGRAMS}
        self.assertNotEqual(outputs["capped"], outputs["uncapped_inner"])
        self.assertGreater(sum(value != 0 for row in grid for value in row), 20)

    def test_public_projection_and_sequential_turn_hide_private_data(self):
        episode = self.mod.build_episode(self.bridge, seed=17, n_train=3, n_test=4)
        public = self.mod.public_challenge(episode)
        self.assertEqual(set(public), {"train", "test"})
        self.assertTrue(all(set(pair) == {"input", "output"} for pair in public["train"]))
        self.assertTrue(all(set(pair) == {"input"} for pair in public["test"]))
        serialized = json.dumps(public, sort_keys=True)
        self.assertNotIn("edge_cap", serialized)
        self.assertNotIn("program", serialized)
        first = self.mod.sequential_turn(episode, 0)
        single = self.mod.public_challenge(episode, query_indices=[0])
        self.assertEqual(first, single)
        self.assertEqual(public_challenge_bytes(first), public_challenge_bytes(single))
        self.assertEqual(
            self.mod.sequential_turn(episode, 1),
            {"test": [{"input": episode["test"][1]["input"]}]},
        )
        later_text = json.dumps(self.mod.sequential_turn(episode, 2), sort_keys=True)
        for forbidden in ("count", "edge_cap", "program", "output"):
            self.assertNotIn(forbidden, later_text)

    def test_public_id_ignores_private_fields_but_tracks_visible_bytes(self):
        episode = self.mod.build_episode(self.bridge, seed=31, n_train=3, n_test=4)
        public_id = public_challenge_id(self.mod.public_challenge(episode))
        private = deepcopy(episode)
        private["seed"] = 999
        private["edge_cap"] = "uncapped_inner"
        private["program"] = "private mutation"
        private["test"][0]["output"] = [[9]]
        self.assertEqual(public_challenge_id(self.mod.public_challenge(private)), public_id)
        visible = deepcopy(episode)
        visible["train"][0]["output"][0][0] ^= 4
        self.assertNotEqual(public_challenge_id(self.mod.public_challenge(visible)), public_id)

    def test_fresh_verifier_rejects_corrupted_private_label(self):
        episode = self.mod.build_episode(
            self.bridge, seed=77, edge_cap="uncapped_inner", n_train=2, n_test=4
        )
        self.assertTrue(self.mod.verify_episode(episode, self.bridge))
        corrupt = deepcopy(episode)
        corrupt["test"][0]["output"][0][0] = 9
        with self.assertRaisesRegex(ValueError, "fresh Racket"):
            self.mod.verify_episode(corrupt, self.bridge)

    def test_batch_writer_binds_sorted_visible_ids(self):
        episodes = [
            self.mod.build_episode(self.bridge, seed=0, edge_cap="capped", n_train=2),
            self.mod.build_episode(self.bridge, seed=1, edge_cap="uncapped_inner", n_train=6),
        ]
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "batch"
            report = self.mod.write_batch(episodes, out, self.bridge)
            expected = sorted(public_challenge_id(self.mod.public_challenge(ep)) for ep in episodes)
            self.assertEqual(report["public_ids"], expected)
            self.assertEqual(self.mod.verify_batch(out, self.bridge)["public_ids"], expected)
            self.assertEqual(
                sorted(path.name for path in (out / "public").iterdir()),
                [value + ".json" for value in expected],
            )

    def test_adapter_and_promotion_contract_are_bounded(self):
        self.assertTrue(ADAPTER.is_file())
        self.assertEqual(
            json.loads(PROMOTION.read_text(encoding="utf-8")),
            {
                "schema": "arcpuzzles-parametric-adapter-v1",
                "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
                "parameters": {"edge_cap": ["capped", "uncapped_inner"]},
                "default": {"edge_cap": "capped"},
                "limits": {"demos": [2, 6], "queries": [4, 4]},
                "resources": [f"generators/{TASK_ID}/workspace/parametric/edge_cap_episodes.py"],
            },
        )
        spec = importlib.util.spec_from_file_location("frame_parametric_adapter", ADAPTER)
        adapter = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(adapter)
        self.assertEqual(adapter.program({"edge_cap": "capped"}), _canonical_program())
        claim = adapter.generate(5, {"edge_cap": "uncapped_inner"}, 2, 4)
        self.assertEqual(len(claim["train"]), 2)
        self.assertEqual(len(claim["test"]), 4)
        self.assertEqual(
            hashlib.sha256(claim["program_solution"].encode()).hexdigest(),
            hashlib.sha256(adapter.program({"edge_cap": "uncapped_inner"}).encode()).hexdigest(),
        )

    def test_invalid_requests_fail_without_silent_shortening(self):
        for kwargs in (
            {"seed": True, "n_train": 3, "n_test": 4},
            {"seed": 1, "n_train": 1, "n_test": 4},
            {"seed": 1, "n_train": 7, "n_test": 4},
            {"seed": 1, "n_train": 3, "n_test": 3},
            {"seed": 1, "n_train": 3, "n_test": 5},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.mod.build_claimed_episode(edge_cap="capped", **kwargs)
        with self.assertRaises(ValueError):
            self.mod.build_claimed_episode(seed=1, edge_cap="unknown", n_train=3, n_test=4)


if __name__ == "__main__":
    unittest.main()
