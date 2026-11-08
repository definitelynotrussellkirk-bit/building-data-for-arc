"""Bounded independent adversarial regressions on sampler and export provenance."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / "generators/cd818a9d92d1/workspace/parametric/prototype.py"
sys.path.insert(0, str(REPO / "shared/runtime"))
sys.path.insert(0, str(REPO / "src"))


class AdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("adversarial_direction", SOURCE)
        cls.p = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.p)
        context = cls.p.RacketOracle()
        cls.oracle = context.__enter__()
        cls.addClassCleanup(context.__exit__, None, None, None)
        cls.ep = cls.p.make_episode(919, "right", demos=2, queries=4,
                                   input_seed=42, oracle=cls.oracle)

    def test_minimum_domain_and_exact_integer_boundaries(self):
        overrides = dict(grid_h=5, grid_w=6,
                         branch_profile="compact_one_bend_one_distractor")
        self.assertEqual(self.p.input_capacity(overrides), 4)
        samples = self.p.sample_inputs(83, 4, input_overrides=overrides)
        self.assertEqual(len({json.dumps(g) for g in samples}), 4)
        for grid in samples:
            self.p.validate_input(grid)
            for direction in self.p.DIRECTIONS:
                out = self.oracle.predict(grid, self.p.program(direction))
                self.assertEqual(out, self.p.predict_python(grid, direction))
                for r, row in enumerate(grid):
                    for c, value in enumerate(row):
                        if value == 5:
                            self.assertEqual(out[r][c], 5)
        for count in (True, 4.0, 0, 17):
            with self.subTest(count=count), self.assertRaises(ValueError):
                self.p.sample_inputs(83, count)
        for field, value in (("input_seed", True), ("max_attempts", True),
                             ("max_attempts", 4097), ("max_attempts", 1)):
            args = dict(input_seed=83, count=2)
            args[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.p.sample_inputs(**args)
        with self.assertRaises(self.p.SamplingLimitError):
            self.p.sample_inputs(83, 5, input_overrides=overrides)
        for name, value in (("grid_h", True), ("grid_h", 17),
                            ("grid_w", 5), ("grid_w", 18.0)):
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                self.p.sample_inputs(83, 1, input_overrides={name: value})

    def test_public_projection_sorting_and_duplicate_prevalidation(self):
        right = copy.deepcopy(self.ep)
        right["private_note"] = "ADVERSARIAL_PRIVATE_SENTINEL"
        left = self.p.make_episode(919, "left", demos=2, queries=4,
                                   input_seed=42, oracle=self.oracle)
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "batch"
            manifest = self.p.write_batch([right, left], out, self.oracle)
            ids = [row["id"] for row in manifest["public"]]
            self.assertEqual(ids, sorted(ids))
            for record in manifest["public"]:
                raw = (out / record["path"]).read_bytes()
                self.assertEqual(record["id"], hashlib.sha256(raw).hexdigest())
                self.assertNotIn(b"ADVERSARIAL_PRIVATE_SENTINEL", raw)
                visible = json.loads(raw)
                self.assertEqual(set(visible), {"train", "test"})
                self.assertTrue(all(set(pair) == {"input"} for pair in visible["test"]))
                self.assertTrue(all(set(pair) == {"input", "output"} for pair in visible["train"]))
            self.assertEqual(self.p.verify_export(out, self.oracle)["status"], "passed")
            duplicate = Path(temporary) / "duplicate"
            with self.assertRaises(ValueError):
                self.p.write_batch([right, copy.deepcopy(right)], duplicate, self.oracle)
            self.assertFalse(duplicate.exists())

    def test_saved_certificate_not_authority_and_rehashed_labels_rejected(self):
        ep = copy.deepcopy(self.ep)
        ep["certificate"] = {"survivors": ["invented"]}
        self.assertEqual(self.p.certify_episode(ep, self.oracle), self.ep["certificate"])
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "batch"
            self.p.write_batch([self.ep], out, self.oracle)
            self._mutate_private(out, lambda e: e["test"][0]["output"][0].__setitem__(0, 9))
            with self.assertRaises(ValueError):
                self.p.verify_export(out, self.oracle)

    def _mutate_private(self, out, change):
        ep = json.loads((out / "private.jsonl").read_text())
        change(ep)
        raw = (json.dumps(ep, sort_keys=True, separators=(",", ":")) + "\n").encode()
        (out / "private.jsonl").write_bytes(raw)
        manifest = json.loads((out / "manifest.json").read_text())
        manifest["private_sha256"] = hashlib.sha256(raw).hexdigest()
        (out / "manifest.json").write_text(json.dumps(manifest))

    def test_rehashed_forged_program_digest_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "batch"
            self.p.write_batch([self.ep], out, self.oracle)
            self._mutate_private(out, lambda e: e.__setitem__("program_sha256", "0" * 64))
            with self.assertRaises(ValueError):
                self.p.verify_export(out, self.oracle)

    def test_rehashed_forged_source_provenance_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "batch"
            self.p.write_batch([self.ep], out, self.oracle)
            self._mutate_private(out, lambda e: e.__setitem__("source_sha256", {"forged/generator.py": "f" * 64}))
            with self.assertRaises(ValueError):
                self.p.verify_export(out, self.oracle)


if __name__ == "__main__":
    unittest.main(verbosity=2)
