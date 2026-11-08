"""Prototype counts, finite lessons, and visible-only serialization regressions."""
from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

HOME = Path(__file__).resolve().parents[1] / "workspace/parametric"
sys.path.insert(0, str(HOME))

class EpisodeTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((HOME / "episodes.py").is_file(), "episode implementation is missing")
        self.e = importlib.import_module("episodes")

    def test_all_settings_exact_distinct_four_queries(self):
        from core import enumerate_settings
        for setting in enumerate_settings():
            episode = self.e.generate_episode(17, setting, 3, 4)
            self.assertEqual([len(episode[x]) for x in ("train", "test")], [3, 4])
            inputs = [json.dumps(p["input"]) for s in ("train", "test") for p in episode[s]]
            self.assertEqual(len(set(inputs)), 7)
            self.assertEqual(episode["certificate"]["setting_survivors"], [setting])
            self.assertTrue(episode["certificate"]["identifiable"])
            self.assertEqual(episode, self.e.generate_episode(17, setting, 3, 4))
            self.assertIn((30, 30), [(len(p["input"]), len(p["input"][0])) for p in episode["test"]])

    def test_counts_and_seed_are_strict_and_bounded(self):
        for kw in ({"demos": True}, {"demos": 2}, {"demos": 9}, {"queries": 0},
                   {"queries": 9}, {"queries": 4.0}, {"seed": True}, {"seed": -1}):
            args = dict(seed=0, settings=None, demos=3, queries=4); args.update(kw)
            with self.assertRaises((ValueError, TypeError)):
                self.e.generate_episode(**args)
        with self.assertRaises(self.e.SamplingError):
            self.e.generate_episode(0, None, 3, 4, max_attempts=1)

    def test_maximum_counts_and_exact_dimensions(self):
        ep = self.e.generate_episode(9, {"quarter_turns": 3, "stride": 2}, 8, 8, grid_h=6, grid_w=30)
        self.assertEqual([len(ep[x]) for x in ("train", "test")], [8, 8])
        self.assertTrue(all((len(p["input"]), len(p["input"][0])) == (6, 30)
                            for s in ("train", "test") for p in ep[s]))

    def test_certificate_uses_only_demos_and_query_inputs(self):
        ep = self.e.generate_episode(0, None, 3, 4)
        cert = self.e.lesson_certificate(ep["train"], [p["input"] for p in ep["test"]])
        changed = deepcopy(ep)
        for p in changed["test"]: p["output"] = deepcopy(p["input"])
        self.assertEqual(cert, self.e.lesson_certificate(changed["train"], [p["input"] for p in changed["test"]]))
        g = [[3, 2], [3, 3]]
        ambiguous = self.e.lesson_certificate([{"input": g, "output": [[3, 3], [3, 3]]}], [ep["train"][0]["input"]])
        self.assertEqual(len(ambiguous["setting_survivors"]), 8)
        self.assertFalse(ambiguous["identifiable"])

class ExportTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((HOME / "build.py").is_file(), "export implementation is missing")
        self.b = importlib.import_module("build")
        self.e = importlib.import_module("episodes")

    def test_public_names_ignore_hidden_metadata_and_query_answers(self):
        from reviewer_support import public_challenge_bytes
        original = self.e.generate_episode(0, None, 3, 4)
        changed = deepcopy(original)
        changed.update(seed=999, settings={"quarter_turns": 3, "stride": 2}, program_solution="private")
        for p in changed["test"]: p["output"] = deepcopy(p["input"])
        with tempfile.TemporaryDirectory() as temp:
            a, b = Path(temp)/"a", Path(temp)/"b"
            self.b.write_export([original], a)
            self.b.write_export([changed], b)
            fa, fb = next((a/"public").iterdir()), next((b/"public").iterdir())
            self.assertEqual(fa.name, fb.name)
            self.assertEqual(fa.read_bytes(), public_challenge_bytes(original))
            self.assertEqual(fa.read_bytes(), fb.read_bytes())
            public = json.loads(fa.read_bytes())
            self.assertEqual(set(public), {"train", "test"})
            self.assertTrue(all(set(p) == {"input"} for p in public["test"]))

    def test_duplicate_visible_batch_fails_before_output_creation(self):
        ep = self.e.generate_episode(0, None, 3, 4)
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)/"duplicate"
            with self.assertRaises(ValueError): self.b.write_export([ep, deepcopy(ep)], out)
            self.assertFalse(out.exists())

    def test_verifier_rejects_tampered_public_and_private_labels(self):
        ep = self.e.generate_episode(0, None, 3, 4)
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)/"export"
            self.b.write_export([ep], out)
            self.assertTrue(self.b.verify_export(out)["valid"])
            target = next((out/"public").iterdir())
            target.write_bytes(target.read_bytes()+b" ")
            with self.assertRaises(ValueError): self.b.verify_export(out)
        changed = deepcopy(ep); changed["test"][0]["output"] = deepcopy(changed["test"][0]["input"])
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)/"wrong-label"
            self.b.write_export([changed], out)
            with self.assertRaises(ValueError): self.b.verify_export(out)

if __name__ == "__main__": unittest.main()
