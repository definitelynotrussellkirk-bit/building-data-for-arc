"""Bounded adversarial regression checks; no Racket or full-corpus execution."""
from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "shared/runtime").is_dir())
HOME = ROOT / "generators/98c4483164f7/workspace/parametric"
sys.path[:0] = [str(HOME), str(ROOT / "shared/runtime")]
b = importlib.import_module("build")
e = importlib.import_module("episodes")
c = importlib.import_module("core")


class AdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = e.generate_episode(0, None, 3, 4)

    def assert_rejected_export(self, episode):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "export"
            # Serialization can reject malformed content earlier than verification.
            with self.assertRaises((TypeError, ValueError)):
                b.write_export([episode], out)
                b.verify_export(out)

    def test_duplicate_attempts_consume_finite_budget(self):
        grid = self.base["train"][0]["input"]
        with patch.object(e, "sample_input", return_value=deepcopy(grid)) as sampler:
            with self.assertRaises(e.SamplingError):
                e.generate_episode(0, None, 3, 4, max_attempts=11)
        self.assertEqual(sampler.call_count, 11)
        self.assertEqual([call.args[1] for call in sampler.call_args_list], list(range(11)))

    def test_duplicate_retry_keeps_exact_counts_and_attempts(self):
        grids = [deepcopy(p["input"]) for split in ("train", "test") for p in self.base[split]]
        sequence = grids[:1] + [deepcopy(grids[0])] + grids[1:]
        with patch.object(e, "sample_input", side_effect=sequence) as sampler:
            result = e.generate_episode(0, None, 3, 4, max_attempts=8)
        self.assertEqual(sampler.call_count, 8)
        self.assertEqual(result["sampling_attempts"], 8)
        self.assertEqual([len(result[s]) for s in ("train", "test")], [3, 4])
        self.assertEqual([p["input"] for s in ("train", "test") for p in result[s]], grids)

    def test_weak_lesson_retries_with_next_distinct_window(self):
        chosen = {"quarter_turns": 0, "stride": 1}
        weak = {"setting_survivors": [], "identifiable": False}
        strong = {"setting_survivors": [chosen], "identifiable": True}
        with patch.object(e, "lesson_certificate", side_effect=[weak, strong]) as certificate:
            result = e.generate_episode(0, chosen, 3, 4, max_attempts=8)
        self.assertEqual(certificate.call_count, 2)
        self.assertEqual(result["sampling_attempts"], 8)
        first, second = [call.args[0][0]["input"] for call in certificate.call_args_list]
        self.assertNotEqual(first, second)
        self.assertEqual(result["train"][0]["input"], second)

    def test_retry_and_dimension_type_rejections_happen_before_sampling(self):
        for kwargs in ({"max_attempts": True}, {"max_attempts": 7.0}, {"max_attempts": 4097},
                       {"grid_h": True}, {"grid_w": 6.0}, {"queries": False}):
            with self.subTest(kwargs=kwargs), patch.object(e, "sample_input") as sampler:
                with self.assertRaises((TypeError, ValueError)):
                    e.generate_episode(0, **kwargs)
                sampler.assert_not_called()

    def test_duplicate_visible_with_different_private_metadata_rejected_before_creation(self):
        changed = deepcopy(self.base)
        changed.update(seed=999, program_solution="other private claim", settings={"stride": 2})
        changed["test"][0]["output"] = deepcopy(changed["test"][0]["input"])
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "export"
            with self.assertRaises(ValueError): b.write_export([self.base, changed], out)
            self.assertFalse(out.exists())

    def test_exact_grid_and_parameter_types_rejected(self):
        for field, value in (("input", False), ("output", 0.0)):
            ep = deepcopy(self.base)
            ep["test"][0][field][0][0] = value
            with self.subTest(field=field): self.assert_rejected_export(ep)
        ep = deepcopy(self.base); ep["settings"]["quarter_turns"] = False
        self.assert_rejected_export(ep)

    def test_certificate_equal_value_wrong_types_rejected(self):
        for key, value in (("identifiable", 1), ("hypothesis_count", 48.0)):
            ep = deepcopy(self.base); ep["certificate"][key] = value
            with self.subTest(key=key): self.assert_rejected_export(ep)
        ep = deepcopy(self.base)
        ep["certificate"]["eliminated"][0]["witness_demo"] = float(ep["certificate"]["eliminated"][0]["witness_demo"])
        self.assert_rejected_export(ep)

    def test_forged_certificate_witness_or_missing_field_rejected(self):
        ep = deepcopy(self.base); ep["certificate"]["eliminated"][0]["witness_demo"] = 999
        self.assert_rejected_export(ep)
        ep = deepcopy(self.base); del ep["certificate"]["survivors"]
        self.assert_rejected_export(ep)

    def test_manifest_counts_require_exact_integers(self):
        for field, value in (("episode_count", True), ("demos", 3.0), ("queries", 4.0)):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                out = Path(temp) / "export"; b.write_export([self.base], out)
                path = out / "manifest.json"; manifest = json.loads(path.read_text())
                manifest[field] = value; path.write_text(json.dumps(manifest))
                with self.assertRaises((TypeError, ValueError)): b.verify_export(out)

    def test_episode_counts_enforce_declared_limits(self):
        cases = []
        ep = deepcopy(self.base); ep["train"] = ep["train"][:2]; cases.append(("two_demos", ep))
        ep = deepcopy(self.base); ep["test"] = []; cases.append(("zero_queries", ep))
        for split in ("train", "test"):
            ep = e.generate_episode(0, None, 8 if split == "train" else 3, 8 if split == "test" else 4)
            grid = c.sample_input(876, 31, grid_h=30, grid_w=30)
            ep[split].append({"input": grid, "output": c.transform(grid, ep["settings"])})
            cases.append(("nine_" + split, ep))
        for name, ep in cases:
            with self.subTest(name=name):
                if ep["test"]:
                    ep["certificate"] = e.lesson_certificate(ep["train"], [p["input"] for p in ep["test"]])
                    self.assertTrue(ep["certificate"]["identifiable"])
                self.assert_rejected_export(ep)


if __name__ == "__main__":
    unittest.main(verbosity=2)
