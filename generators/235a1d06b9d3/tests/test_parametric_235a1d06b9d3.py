"""Focused contract tests for the source-row parametric family."""
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

TASK_ID = "235a1d06b9d3"
ROOT = find_root(__file__)
SOURCE = ROOT / f"generators/{TASK_ID}/workspace/parametric/source_row_episodes.py"
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
    spec = importlib.util.spec_from_file_location("source_row_generator_for_test", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PrototypeAvailability(unittest.TestCase):
    def test_prototype_exists(self):
        self.assertTrue(SOURCE.is_file(), "source-row prototype is missing")


@unittest.skipUnless(SOURCE.is_file(), "prototype not implemented yet")
class ParametricSourceRow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("source_row_episodes", SOURCE)
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
        self.assertEqual(self.mod.PROGRAMS["row0"], _canonical_program())
        self.assertEqual(self.mod.DEFAULT_SOURCE_ROW, "row0")
        grid = self.mod.sample_grid(seed=12, role="witness", index=0, height=8, width=11)
        outputs = {
            setting: self.mod.execute(self.bridge, setting, [grid])[0]
            for setting in self.mod.PROGRAMS
        }
        self.assertEqual(outputs["row0"], self.mod.python_transform(grid, "row0"))
        self.assertEqual(outputs["row1"], self.mod.python_transform(grid, "row1"))
        self.assertNotEqual(outputs["row0"], outputs["row1"])
        self.assertEqual(outputs["row0"][:2], grid[:2])
        self.assertEqual(outputs["row1"][:2], grid[:2])

    def test_demo_counts_two_through_six_keep_four_unique_queries(self):
        for setting in self.mod.PROGRAMS:
            for demos in range(2, 7):
                with self.subTest(setting=setting, demos=demos):
                    episode = self.mod.build_episode(
                        self.bridge,
                        seed=3000 + demos,
                        source_row=setting,
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
                    for grid in inputs:
                        self.assertEqual(self.generator.self_check(grid), [])

    def test_queries_include_substantive_30_by_30_context_stress(self):
        episode = self.mod.build_episode(
            self.bridge, seed=808, source_row="row0", n_train=3, n_test=4
        )
        large = [pair["input"] for pair in episode["test"] if len(pair["input"]) == 30 and len(pair["input"][0]) == 30]
        self.assertEqual(len(large), 1)
        grid = large[0]
        info = self.mod.analyze_scene(grid)
        self.assertNotEqual(info["row0_mask"], info["row1_mask"])
        self.assertNotEqual(grid[1][1], grid[2][1])
        self.assertGreater(sum(value != info["background"] for row in grid for value in row), 35)
        outputs = {setting: self.mod.execute(self.bridge, setting, [grid])[0] for setting in self.mod.PROGRAMS}
        self.assertTrue(all(len(output) == 3 and len(output[0]) == 30 for output in outputs.values()))
        self.assertNotEqual(outputs["row0"], outputs["row1"])

    def test_public_projection_and_sequential_turn_hide_private_data(self):
        episode = self.mod.build_episode(self.bridge, seed=17, n_train=3, n_test=4)
        public = self.mod.public_challenge(episode)
        self.assertEqual(set(public), {"train", "test"})
        self.assertTrue(all(set(pair) == {"input", "output"} for pair in public["train"]))
        self.assertTrue(all(set(pair) == {"input"} for pair in public["test"]))
        serialized = json.dumps(public, sort_keys=True)
        self.assertNotIn("source_row", serialized)
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
        for forbidden in ("count", "source_row", "program", "output"):
            self.assertNotIn(forbidden, later_text)

    def test_public_id_ignores_private_fields_but_tracks_visible_bytes(self):
        episode = self.mod.build_episode(self.bridge, seed=31, n_train=3, n_test=4)
        public_id = public_challenge_id(self.mod.public_challenge(episode))
        private = deepcopy(episode)
        private["seed"] = 999
        private["source_row"] = "row1"
        private["program"] = "private mutation"
        private["test"][0]["output"] = [[9]]
        self.assertEqual(public_challenge_id(self.mod.public_challenge(private)), public_id)
        visible = deepcopy(episode)
        visible["train"][0]["output"][0][0] ^= 4
        self.assertNotEqual(public_challenge_id(self.mod.public_challenge(visible)), public_id)

    def test_fresh_verifier_rejects_corrupted_private_label(self):
        episode = self.mod.build_episode(
            self.bridge, seed=77, source_row="row1", n_train=2, n_test=4
        )
        self.assertTrue(self.mod.verify_episode(episode, self.bridge))
        corrupt = deepcopy(episode)
        corrupt["test"][0]["output"][0][0] = 9
        with self.assertRaisesRegex(ValueError, "fresh Racket"):
            self.mod.verify_episode(corrupt, self.bridge)

    def test_batch_writer_binds_sorted_visible_ids(self):
        episodes = [
            self.mod.build_episode(self.bridge, seed=0, source_row="row0", n_train=2),
            self.mod.build_episode(self.bridge, seed=1, source_row="row1", n_train=6),
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
                "parameters": {"source_row": ["row0", "row1"]},
                "default": {"source_row": "row0"},
                "limits": {"demos": [2, 6], "queries": [4, 4]},
                "resources": [f"generators/{TASK_ID}/workspace/parametric/source_row_episodes.py"],
            },
        )
        spec = importlib.util.spec_from_file_location("source_row_parametric_adapter", ADAPTER)
        adapter = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(adapter)
        self.assertEqual(adapter.program({"source_row": "row0"}), _canonical_program())
        claim = adapter.generate(5, {"source_row": "row1"}, 2, 4)
        self.assertEqual(len(claim["train"]), 2)
        self.assertEqual(len(claim["test"]), 4)
        self.assertEqual(
            hashlib.sha256(claim["program_solution"].encode()).hexdigest(),
            hashlib.sha256(adapter.program({"source_row": "row1"}).encode()).hexdigest(),
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
                self.mod.build_claimed_episode(source_row="row0", **kwargs)
        with self.assertRaises(ValueError):
            self.mod.build_claimed_episode(seed=1, source_row="unknown", n_train=3, n_test=4)


if __name__ == "__main__":
    unittest.main()
