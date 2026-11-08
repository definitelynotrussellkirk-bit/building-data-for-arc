"""Focused promotion-adapter contracts; this does not qualify or accept variants."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

REPO = Path(__file__).resolve().parents[3]
PARAMETRIC = REPO / "generators/cd818a9d92d1/workspace/parametric"
sys.path.insert(0, str(REPO / "shared/runtime"))
sys.path.insert(0, str(REPO / "src"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert (PARAMETRIC / "adapter.py").is_file(), "Promotion adapter not implemented yet"
        cls.adapter = load("tested_direction_adapter", PARAMETRIC / "adapter.py")
        cls.prototype = load("adapter_test_direction_prototype", PARAMETRIC / "prototype.py")
        context = cls.prototype.RacketOracle()
        cls.oracle = context.__enter__()
        cls.addClassCleanup(context.__exit__, None, None, None)

    def test_promotion_contract_binds_default_limits_and_resource(self):
        config = json.loads((PARAMETRIC / "promotion.json").read_text())
        prefix = "generators/cd818a9d92d1/workspace/parametric/"
        self.assertEqual(config, {
            "schema": "arcpuzzles-parametric-adapter-v1",
            "adapter": prefix + "adapter.py",
            "parameters": {"bend_direction": ["right", "left"]},
            "default": {"bend_direction": "right"},
            "limits": {"demos": [1, 8], "queries": [1, 8]},
            "resources": [prefix + "prototype.py"],
        })
        self.assertTrue((REPO / config["adapter"]).is_file())
        self.assertTrue(all((REPO / path).is_file() for path in config["resources"]))

    def test_default_program_is_exact_registered_canonical(self):
        canonical = {
            json.loads(line)["program_solution"]
            for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
            if json.loads(line).get("task_id") == "cd818a9d92d1"
        }
        self.assertEqual(len(canonical), 1)
        self.assertEqual(self.adapter.program({"bend_direction": "right"}), canonical.pop())
        self.assertNotEqual(self.adapter.program({"bend_direction": "left"}),
                            self.adapter.program({"bend_direction": "right"}))

    def test_settings_reject_missing_extra_and_wrong_typed_values(self):
        settings = [None, {}, [], {"bend_direction": "up"}, {"bend_direction": True},
                    {"bend_direction": 1}, {"bend_direction": "right", "extra": 0}]
        for value in settings:
            with self.subTest(settings=value), self.assertRaises(ValueError):
                self.adapter.program(value)
            with self.subTest(generate_settings=value), self.assertRaises(ValueError):
                self.adapter.generate(19, value, 2, 4)

    def test_counts_are_independent_strict_and_bounded(self):
        settings = {"bend_direction": "right"}
        for value in (True, 2.0, 0, -1, 9):
            for demos, queries in ((value, 4), (2, value)):
                with self.subTest(demos=demos, queries=queries), self.assertRaises(ValueError):
                    self.adapter.generate(19, settings, demos, queries)
        for seed in (True, 2.0, "19"):
            with self.subTest(seed=seed), self.assertRaises(ValueError):
                self.adapter.generate(seed, settings, 2, 4)
        for demos, queries in ((1, 4), (3, 1), (8, 8)):
            episode = self.adapter.generate(19, settings, demos, queries)
            self.assertEqual((len(episode["train"]), len(episode["test"])), (demos, queries))
            inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
            self.assertEqual(len({json.dumps(grid) for grid in inputs}), demos + queries)

    def test_shared_inputs_deterministic_replay_and_real_racket_labels(self):
        episodes = {}
        for direction in ("right", "left"):
            settings = {"bend_direction": direction}
            episode = self.adapter.generate(2718, settings, 2, 4)
            self.assertEqual(episode, self.adapter.generate(2718, settings, 2, 4))
            self.assertEqual(episode["program_solution"], self.adapter.program(settings))
            self.assertEqual(len(episode["train"]), 2)
            self.assertEqual(len(episode["test"]), 4)
            pairs = episode["train"] + episode["test"]
            self.assertEqual(len({json.dumps(pair["input"]) for pair in pairs}), 6)
            for pair in pairs:
                self.prototype.validate_input(pair["input"])
                self.assertEqual(pair["output"],
                                 self.oracle.predict(pair["input"], episode["program_solution"]))
                self.assertTrue(all(type(cell) is int and 0 <= cell <= 9
                                    for row in pair["output"] for cell in row))
            episodes[direction] = episode
        self.assertEqual(
            [p["input"] for p in episodes["right"]["train"] + episodes["right"]["test"]],
            [p["input"] for p in episodes["left"]["train"] + episodes["left"]["test"]])
        self.assertNotEqual(episodes["right"]["train"][0]["output"],
                            episodes["left"]["train"][0]["output"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
