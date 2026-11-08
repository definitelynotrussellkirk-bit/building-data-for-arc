"""Focused tests of the proposed rotation prototype, separate from canonical repair."""
from pathlib import Path
from copy import deepcopy
import importlib.util
import json
import sys
import tempfile
import unittest

# Locate local public reviewer helpers without cwd or an adjacent checkout.
for _parent in Path(__file__).resolve().parents:
    for _runtime in (_parent / "shared/runtime", _parent):
        if (_runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(_runtime))
            break
    else:
        continue
    break
from reviewer_support import (
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

ROOT = find_root(__file__)
SOURCE = ROOT / "generators/864eaaac6503/workspace/parametric/rotation_episodes.py"
ADAPTER = ROOT / "generators/864eaaac6503/workspace/parametric/adapter.py"
PROMOTION = ROOT / "generators/864eaaac6503/workspace/parametric/promotion.json"


class PrototypeAvailability(unittest.TestCase):
    def test_prototype_exists(self):
        self.assertTrue(SOURCE.is_file(), "the requested runnable prototype is missing")


@unittest.skipUnless(SOURCE.is_file(), "prototype not implemented yet")
class ParametricRotations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("rotation_episodes", SOURCE)
        cls.mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(cls.mod)
        cls.bridge = cls.mod.open_bridge()

    @classmethod
    def tearDownClass(cls):
        cls.bridge.shutdown()

    def test_exact_original_and_alternative_programs_execute(self):
        grid = [[1, 2, 3], [4, 5, 6]]
        self.assertEqual(self.mod.PROGRAMS["ccw"], "(rule! rotate-ccw)")
        self.assertEqual(self.mod.DEFAULT_DIRECTION, "ccw")
        self.assertEqual(
            self.mod.execute(self.bridge, "ccw", [grid]),
            [[[3, 6], [2, 5], [1, 4]]],
        )
        self.assertEqual(
            self.mod.execute(self.bridge, "cw", [grid]),
            [[[4, 1], [5, 2], [6, 3]]],
        )

    def test_seed_is_reproducible_and_parameter_fixed_for_full_episode(self):
        for seed in (0, 1):
            a = self.mod.build_episode(self.bridge, seed=seed)
            b = self.mod.build_episode(self.bridge, seed=seed)
            self.assertEqual(a, b)
            self.assertEqual(len(a["train"]), 3)
            self.assertEqual(len(a["test"]), 4)
            pairs = a["train"] + a["test"]
            actual = self.mod.execute(
                self.bridge, a["direction"], [p["input"] for p in pairs]
            )
            self.assertEqual(actual, [p["output"] for p in pairs])
            self.assertEqual(a["rival_check"]["demo_survivors"], [a["direction"]])
            self.assertTrue(a["rival_check"]["identifiable_from_demos"])
            for other, verdict in a["rival_check"]["rivals"].items():
                self.assertEqual(len(verdict["query_matches"]), 4)
                self.assertEqual(
                    verdict["full_episode_consistent"], other == a["direction"]
                )
        self.assertEqual(
            {self.mod.build_episode(self.bridge, seed=s)["direction"] for s in (0, 1)},
            {"ccw", "cw"},
        )

    def test_demo_counts_two_through_six_all_keep_four_unique_queries(self):
        for direction in self.mod.PROGRAMS:
            for demos in range(2, 7):
                with self.subTest(direction=direction, demos=demos):
                    episode = self.mod.build_episode(
                        self.bridge,
                        seed=100 + demos,
                        direction=direction,
                        n_train=demos,
                        n_test=4,
                    )
                    self.assertEqual(len(episode["train"]), demos)
                    self.assertEqual(len(episode["test"]), 4)
                    inputs = [
                        pair["input"] for pair in episode["train"] + episode["test"]
                    ]
                    fingerprints = {
                        tuple(tuple(row) for row in grid) for grid in inputs
                    }
                    self.assertEqual(len(fingerprints), demos + 4)
                    self.assertEqual(
                        episode["rival_check"]["demo_survivors"], [direction]
                    )

    def test_four_query_profile_contains_substantive_exact_30x30_case(self):
        for direction in self.mod.PROGRAMS:
            episode = self.mod.build_episode(
                self.bridge, seed=404, direction=direction, n_train=3, n_test=4
            )
            queries = [pair["input"] for pair in episode["test"]]
            large = [grid for grid in queries if (len(grid), len(grid[0])) == (30, 30)]
            self.assertEqual(len(large), 1)
            grid = large[0]
            self.assertGreaterEqual(len({cell for row in grid for cell in row}), 6)
            self.assertGreaterEqual(
                sum(cell != 0 for row in grid for cell in row),
                30 * 30 // 2,
            )
            self.assertGreaterEqual(len(set(grid[0] + grid[-1])), 4)
            self.assertGreaterEqual(
                len({grid[r][0] for r in range(30)} | {grid[r][-1] for r in range(30)}),
                4,
            )

    def test_public_challenge_omits_private_information(self):
        episode = self.mod.build_episode(self.bridge, seed=0)
        challenge = self.mod.public_challenge(episode)
        self.assertEqual(set(challenge), {"train", "test"})
        self.assertTrue(
            all(set(pair) == {"input", "output"} for pair in challenge["train"])
        )
        self.assertTrue(all(set(pair) == {"input"} for pair in challenge["test"]))
        self.assertEqual(challenge["test"][0]["input"], episode["test"][0]["input"])
        challenge["train"][0]["input"][0][0] = 99
        self.assertNotEqual(
            challenge["train"][0]["input"], episode["train"][0]["input"]
        )

    def test_public_bytes_and_identifier_depend_only_on_visible_projection(self):
        episode = self.mod.build_episode(self.bridge, seed=31)
        public = self.mod.public_challenge(episode)
        raw = public_challenge_bytes(public)
        public_id = public_challenge_id(public)

        private_only = deepcopy(episode)
        private_only["seed"] = 999
        private_only["direction"] = "cw" if episode["direction"] == "ccw" else "ccw"
        private_only["program"] = "private mutation"
        private_only["test"][0]["output"] = [[9]]
        private_only["rival_check"] = {"private": True}
        self.assertEqual(public_challenge_bytes(self.mod.public_challenge(private_only)), raw)
        self.assertEqual(public_challenge_id(self.mod.public_challenge(private_only)), public_id)

        visible = deepcopy(episode)
        visible["train"][0]["output"][0][0] = (visible["train"][0]["output"][0][0] + 1) % 10
        self.assertNotEqual(public_challenge_id(self.mod.public_challenge(visible)), public_id)

        visible = deepcopy(episode)
        visible["test"][0]["input"][0][0] = (visible["test"][0]["input"][0][0] + 1) % 10
        self.assertNotEqual(public_challenge_id(self.mod.public_challenge(visible)), public_id)

    def test_sequential_projection_hides_future_queries_and_preserves_first_turn_bytes(self):
        episode = self.mod.build_episode(self.bridge, seed=37)
        first = self.mod.sequential_turn(episode, 0)
        single = self.mod.public_challenge(episode, query_indices=[0])
        self.assertEqual(first, single)
        self.assertEqual(public_challenge_bytes(first), public_challenge_bytes(single))
        self.assertEqual(len(first["test"]), 1)
        self.assertEqual(first["test"][0]["input"], episode["test"][0]["input"])
        self.assertNotIn(episode["test"][1]["input"], [p["input"] for p in first["test"]])

        later = self.mod.sequential_turn(episode, 1)
        self.assertEqual(set(later), {"test"})
        self.assertEqual(later, {"test": [{"input": episode["test"][1]["input"]}]})
        serialized = json.dumps(later, sort_keys=True)
        self.assertNotIn("count", serialized.lower())
        self.assertNotIn("direction", serialized.lower())
        self.assertNotIn("output", serialized.lower())
        for bad_index in (-1, 4, True):
            with self.subTest(bad_index=bad_index), self.assertRaises(ValueError):
                self.mod.sequential_turn(episode, bad_index)

    def test_batch_writer_uses_sorted_content_ids_and_fresh_verification(self):
        episodes = [
            self.mod.build_episode(self.bridge, seed=0, direction="ccw", n_train=2),
            self.mod.build_episode(self.bridge, seed=1, direction="cw", n_train=6),
        ]
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "batch"
            report = self.mod.write_batch(episodes, out, self.bridge)
            ids = sorted(public_challenge_id(self.mod.public_challenge(ep)) for ep in episodes)
            self.assertEqual(report["public_ids"], ids)
            self.assertEqual(
                sorted(path.name for path in (out / "public").iterdir()),
                [public_id + ".json" for public_id in ids],
            )
            for episode in episodes:
                public = self.mod.public_challenge(episode)
                public_id = public_challenge_id(public)
                self.assertEqual(
                    (out / "public" / f"{public_id}.json").read_bytes(),
                    public_challenge_bytes(public),
                )
            self.assertEqual(
                self.mod.verify_batch(out, self.bridge),
                {"verified_episodes": 2, "public_ids": ids},
            )

    def test_duplicate_visible_batch_is_rejected_before_creating_destination(self):
        episode = self.mod.build_episode(self.bridge, seed=43)
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "duplicate"
            with self.assertRaisesRegex(ValueError, "duplicate visible"):
                self.mod.write_batch([episode, deepcopy(episode)], out, self.bridge)
            self.assertFalse(out.exists())

    def test_symmetric_demos_are_reported_ambiguous_even_if_query_distinguishes(self):
        demo = [[1, 2], [2, 1]]
        query = [[1, 2, 3], [4, 5, 6]]
        outputs = self.mod.execute(self.bridge, "ccw", [demo, query])
        episode = {
            "train": [{"input": demo, "output": outputs[0]}],
            "test": [{"input": query, "output": outputs[1]}],
        }
        verdict = self.mod.assess_episode(self.bridge, episode)
        self.assertEqual(set(verdict["demo_survivors"]), {"ccw", "cw"})
        self.assertFalse(verdict["identifiable_from_demos"])
        self.assertFalse(verdict["rivals"]["cw"]["query_matches"][0])

    def test_declared_inputs_include_both_shapes_and_distinct_corners(self):
        episode = self.mod.build_episode(self.bridge, seed=17)
        grids = [pair["input"] for pair in episode["train"] + episode["test"]]
        self.assertTrue(any(len(grid) == len(grid[0]) for grid in grids))
        self.assertTrue(any(len(grid) != len(grid[0]) for grid in grids))
        for grid in grids:
            self.assertEqual(
                len({grid[0][0], grid[0][-1], grid[-1][0], grid[-1][-1]}), 4
            )

    def test_invalid_counts_and_direction_fail(self):
        bad_requests = (
            {"n_train": 1},
            {"n_train": 7},
            {"n_train": True},
            {"n_test": 1},
            {"n_test": 5},
            {"n_test": True},
            {"direction": "north"},
        )
        for kwargs in bad_requests:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.mod.build_episode(self.bridge, seed=1, **kwargs)


class PromotionAdapter(unittest.TestCase):
    def _load_adapter(self):
        self.assertTrue(ADAPTER.is_file(), "native parametric adapter is missing")
        spec = importlib.util.spec_from_file_location("rotation_parametric_adapter", ADAPTER)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    def test_promotion_contract_is_exact_and_source_bound(self):
        self.assertTrue(PROMOTION.is_file(), "promotion contract is missing")
        self.assertEqual(
            json.loads(PROMOTION.read_text()),
            {
                "schema": "arcpuzzles-parametric-adapter-v1",
                "adapter": "generators/864eaaac6503/workspace/parametric/adapter.py",
                "parameters": {"direction": ["ccw", "cw"]},
                "default": {"direction": "ccw"},
                "limits": {"demos": [2, 6], "queries": [4, 4]},
                "resources": [
                    "generators/864eaaac6503/workspace/parametric/rotation_episodes.py"
                ],
            },
        )
        adapter = self._load_adapter()
        self.assertEqual(Path(adapter._prototype.__file__).resolve(), SOURCE.resolve())

    def test_program_returns_only_the_declared_exact_racket_forms(self):
        adapter = self._load_adapter()
        self.assertEqual(adapter.program({"direction": "ccw"}), "(rule! rotate-ccw)")
        self.assertEqual(adapter.program({"direction": "cw"}), "(rule! rotate-cw)")
        for settings in (None, {}, {"direction": "north"}, {"direction": "ccw", "x": 1}):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                adapter.program(settings)

    def test_generate_claims_exact_counts_and_matches_racket_for_each_setting(self):
        adapter = self._load_adapter()
        source_spec = importlib.util.spec_from_file_location("rotation_episode_for_adapter_test", SOURCE)
        source = importlib.util.module_from_spec(source_spec)
        assert source_spec.loader is not None
        source_spec.loader.exec_module(source)
        bridge = source.open_bridge()
        try:
            generated = {}
            for direction in ("ccw", "cw"):
                episode = adapter.generate(73, {"direction": direction}, 6, 4)
                generated[direction] = episode
                self.assertEqual(len(episode["train"]), 6)
                self.assertEqual(len(episode["test"]), 4)
                self.assertEqual(episode["program_solution"], source.PROGRAMS[direction])
                pairs = episode["train"] + episode["test"]
                self.assertEqual(
                    source.execute(bridge, direction, [pair["input"] for pair in pairs]),
                    [pair["output"] for pair in pairs],
                )
            self.assertEqual(
                [pair["input"] for pair in generated["ccw"]["train"] + generated["ccw"]["test"]],
                [pair["input"] for pair in generated["cw"]["train"] + generated["cw"]["test"]],
            )
            self.assertNotEqual(
                generated["ccw"]["train"][0]["output"],
                generated["cw"]["train"][0]["output"],
            )
        finally:
            bridge.shutdown()

    def test_generate_rejects_out_of_contract_requests(self):
        adapter = self._load_adapter()
        bad = (
            (-1, {"direction": "ccw"}, 2, 4),
            (True, {"direction": "ccw"}, 2, 4),
            (0, {"direction": "ccw"}, 1, 4),
            (0, {"direction": "ccw"}, 7, 4),
            (0, {"direction": "ccw"}, True, 4),
            (0, {"direction": "ccw"}, 2, 3),
            (0, {"direction": "ccw"}, 2, True),
            (0, {"direction": "north"}, 2, 4),
        )
        for args in bad:
            with self.subTest(args=args), self.assertRaises(ValueError):
                adapter.generate(*args)


if __name__ == "__main__":
    unittest.main()
