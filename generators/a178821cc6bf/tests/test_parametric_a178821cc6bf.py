"""Focused contract tests for the proposed aligned-state parametric family."""
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

TASK_ID = "a178821cc6bf"
ROOT = find_root(__file__)
SOURCE = ROOT / f"generators/{TASK_ID}/workspace/parametric/aligned_state_episodes.py"
ADAPTER = ROOT / f"generators/{TASK_ID}/workspace/parametric/adapter.py"
PROMOTION = ROOT / f"generators/{TASK_ID}/workspace/parametric/promotion.json"


def _canonical_program() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical task missing")


class PrototypeAvailability(unittest.TestCase):
    def test_prototype_exists(self):
        self.assertTrue(SOURCE.is_file(), "aligned-state prototype is missing")


@unittest.skipUnless(SOURCE.is_file(), "prototype not implemented yet")
class ParametricAlignedState(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("aligned_state_episodes", SOURCE)
        cls.mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[spec.name] = cls.mod
        spec.loader.exec_module(cls.mod)
        cls.bridge = cls.mod.open_bridge()

    @classmethod
    def tearDownClass(cls):
        cls.bridge.shutdown()

    def test_default_program_is_exact_canonical_and_both_settings_execute(self):
        self.assertEqual(self.mod.PROGRAMS["both_zero"], _canonical_program())
        self.assertEqual(self.mod.DEFAULT_MARKED_STATE, "both_zero")
        grid = [
            [0, 1, 0, 1, 0, 0, 2, 2],
            [1, 0, 1, 0, 0, 2, 2, 0],
            [0, 0, 1, 1, 2, 0, 0, 2],
        ]
        outputs = {
            setting: self.mod.execute(self.bridge, setting, [grid])[0]
            for setting in self.mod.PROGRAMS
        }
        self.assertEqual(outputs["both_zero"], self.mod.python_transform(grid, "both_zero"))
        self.assertEqual(outputs["both_nonzero"], self.mod.python_transform(grid, "both_nonzero"))
        self.assertNotEqual(outputs["both_zero"], outputs["both_nonzero"])

    def test_demo_counts_two_through_six_keep_four_unique_queries(self):
        for setting in self.mod.PROGRAMS:
            for demos in range(2, 7):
                with self.subTest(setting=setting, demos=demos):
                    episode = self.mod.build_episode(
                        self.bridge,
                        seed=1000 + demos,
                        marked_state=setting,
                        n_train=demos,
                        n_test=4,
                    )
                    self.assertEqual(len(episode["train"]), demos)
                    self.assertEqual(len(episode["test"]), 4)
                    inputs = [p["input"] for p in episode["train"] + episode["test"]]
                    self.assertEqual(
                        len({json.dumps(grid, separators=(",", ":")) for grid in inputs}),
                        demos + 4,
                    )
                    self.assertEqual(episode["rival_check"]["demo_survivors"], [setting])
                    self.assertTrue(episode["rival_check"]["identifiable_from_demos"])

    def test_large_query_is_substantive_30_by_8_without_changing_panel_width(self):
        episode = self.mod.build_episode(
            self.bridge, seed=404, marked_state="both_zero", n_train=3, n_test=4
        )
        large = [g for g in (p["input"] for p in episode["test"]) if len(g) == 30]
        self.assertEqual(len(large), 1)
        grid = large[0]
        self.assertTrue(all(len(row) == 8 for row in grid))
        states = self.mod.occupancy_counts(grid)
        self.assertTrue(all(states[name] >= 4 for name in ("00", "10", "01", "11")))
        self.assertGreater(sum(value != 0 for row in grid for value in row), 30 * 4)

    def test_public_projection_and_sequential_turn_hide_private_data(self):
        episode = self.mod.build_episode(self.bridge, seed=17, n_train=3, n_test=4)
        public = self.mod.public_challenge(episode)
        self.assertEqual(set(public), {"train", "test"})
        self.assertTrue(all(set(pair) == {"input", "output"} for pair in public["train"]))
        self.assertTrue(all(set(pair) == {"input"} for pair in public["test"]))
        serialized = json.dumps(public, sort_keys=True)
        self.assertNotIn("marked_state", serialized)
        self.assertNotIn("program", serialized)

        first = self.mod.sequential_turn(episode, 0)
        single = self.mod.public_challenge(episode, query_indices=[0])
        self.assertEqual(first, single)
        self.assertEqual(public_challenge_bytes(first), public_challenge_bytes(single))
        self.assertEqual(self.mod.sequential_turn(episode, 1), {
            "test": [{"input": episode["test"][1]["input"]}]
        })
        later_text = json.dumps(self.mod.sequential_turn(episode, 2), sort_keys=True)
        for forbidden in ("count", "marked_state", "program", "output"):
            self.assertNotIn(forbidden, later_text)

    def test_public_id_ignores_private_fields_but_tracks_visible_bytes(self):
        episode = self.mod.build_episode(self.bridge, seed=31, n_train=3, n_test=4)
        public_id = public_challenge_id(self.mod.public_challenge(episode))
        private = deepcopy(episode)
        private["seed"] = 999
        private["marked_state"] = "both_nonzero"
        private["program"] = "private mutation"
        private["test"][0]["output"] = [[9]]
        self.assertEqual(public_challenge_id(self.mod.public_challenge(private)), public_id)
        visible = deepcopy(episode)
        visible["train"][0]["output"][0][0] ^= 4
        self.assertNotEqual(public_challenge_id(self.mod.public_challenge(visible)), public_id)

    def test_fresh_verifier_rejects_corrupted_private_label(self):
        episode = self.mod.build_episode(
            self.bridge, seed=77, marked_state="both_nonzero", n_train=2, n_test=4
        )
        self.assertTrue(self.mod.verify_episode(episode, self.bridge))
        corrupt = deepcopy(episode)
        corrupt["test"][0]["output"][0][0] = 9
        with self.assertRaisesRegex(ValueError, "fresh Racket"):
            self.mod.verify_episode(corrupt, self.bridge)

    def test_batch_writer_binds_sorted_visible_ids(self):
        episodes = [
            self.mod.build_episode(self.bridge, seed=0, marked_state="both_zero", n_train=2),
            self.mod.build_episode(self.bridge, seed=1, marked_state="both_nonzero", n_train=6),
        ]
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "batch"
            report = self.mod.write_batch(episodes, out, self.bridge)
            expected = sorted(public_challenge_id(self.mod.public_challenge(ep)) for ep in episodes)
            self.assertEqual(report["public_ids"], expected)
            self.assertEqual(self.mod.verify_batch(out, self.bridge)["public_ids"], expected)
            self.assertEqual(
                sorted(p.name for p in (out / "public").iterdir()),
                [value + ".json" for value in expected],
            )

    def test_adapter_and_promotion_contract_are_bounded(self):
        self.assertTrue(ADAPTER.is_file())
        self.assertEqual(
            json.loads(PROMOTION.read_text(encoding="utf-8")),
            {
                "schema": "arcpuzzles-parametric-adapter-v1",
                "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
                "parameters": {"marked_state": ["both_zero", "both_nonzero"]},
                "default": {"marked_state": "both_zero"},
                "limits": {"demos": [2, 6], "queries": [4, 4]},
                "resources": [
                    f"generators/{TASK_ID}/workspace/parametric/aligned_state_episodes.py"
                ],
            },
        )
        spec = importlib.util.spec_from_file_location("a178_parametric_adapter", ADAPTER)
        adapter = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(adapter)
        self.assertEqual(adapter.program({"marked_state": "both_zero"}), _canonical_program())
        claim = adapter.generate(5, {"marked_state": "both_nonzero"}, 2, 4)
        self.assertEqual(len(claim["train"]), 2)
        self.assertEqual(len(claim["test"]), 4)
        self.assertEqual(
            hashlib.sha256(claim["program_solution"].encode()).hexdigest(),
            hashlib.sha256(adapter.program({"marked_state": "both_nonzero"}).encode()).hexdigest(),
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
                self.mod.build_claimed_episode(marked_state="both_zero", **kwargs)
        with self.assertRaises(ValueError):
            self.mod.build_claimed_episode(seed=1, marked_state="unknown", n_train=3, n_test=4)


if __name__ == "__main__":
    unittest.main()
