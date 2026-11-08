"""Stdlib contract tests for the opt-in parametric proposal.

Run without writing bytecode: python3 -B -m unittest discover -s
generators/4512012999bb/tests -p 'test_parametric_4512012999bb.py' -v
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import random
import tempfile
import unittest


HERE = Path(__file__).resolve().parents[1] / "workspace" / "parametric"
SPEC = importlib.util.spec_from_file_location("parametric_4512012999bb", HERE / "prototype.py")
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


class ParametricContracts(unittest.TestCase):
    def test_program_default_is_byte_exact_and_ambiguous_selector_fails_closed(self):
        canonical = "(rule! (lambda (g) (let ((flip? (> (score #t) (score #f)))) g)))\n"
        programs = P.programs_from(canonical)
        self.assertEqual(programs["direct"].encode(), canonical.encode())
        self.assertEqual(
            programs["mirror"],
            "(rule! (lambda (g) (let ((flip? (>= (score #t) (score #f)))) g)))\n",
        )
        with self.assertRaises(ValueError):
            P.programs_from(canonical + canonical)
        with self.assertRaises(ValueError):
            P.programs_from("(rule! (lambda (g) g))")

    def test_side_score_ignores_odd_center_and_non_side_colors(self):
        self.assertEqual(P.side_scores([[2, 9, 1], [1, 1, 2]], 2, 1), (2, 2))
        self.assertEqual(P.side_scores([[2, 2, 8, 1], [0, 2, 1, 1]], 2, 1), (6, 0))

    def test_generation_is_deterministic_distinct_and_does_not_touch_global_rng(self):
        random.seed(993)
        before = random.getstate()
        first = P.sample_inputs(17, 3, 4, stream="direct")
        self.assertEqual(random.getstate(), before)
        self.assertEqual(first, P.sample_inputs(17, 3, 4, stream="direct"))
        keys = [json.dumps(scene["input"]) for split in ("train", "test") for scene in first[split]]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual((len(first["train"]), len(first["test"])), (3, 4))
        larger = P.sample_inputs(17, 5, 2, stream="direct")
        self.assertEqual((len(larger["train"]), len(larger["test"])), (5, 2))
        self.assertEqual(first["train"], larger["train"][:3])
        self.assertEqual(first["test"][:2], larger["test"])

    def test_teaching_has_positive_asymmetric_tie_and_both_strict_branches(self):
        scenes = P.sample_inputs(23, 3, 4, stream="direct")
        self.assertEqual([s["meta"]["kind"] for s in scenes["train"]], ["tie", "direct", "mirror"])
        for split in ("train", "test"):
            for scene in scenes[split]:
                meta = scene["meta"]
                self.assertEqual(len(P.find_candidates(scene["input"])), 1)
                self.assertTrue(meta["asymmetric"])
                direct, mirrored = meta["scores"]
                if meta["kind"] == "tie":
                    self.assertGreater(direct, 0)
                    self.assertEqual(direct, mirrored)
                elif meta["kind"] == "direct":
                    self.assertGreater(direct, mirrored)
                else:
                    self.assertGreater(mirrored, direct)
        max_demo_area = max(s["meta"]["crop_area"] for s in scenes["train"])
        for query in scenes["test"]:
            self.assertGreater(query["meta"]["crop_area"], max_demo_area)
            self.assertGreater(len(set(query["meta"]["left_wall"][1:-1])), 1)
        self.assertEqual([s["meta"]["kind"] for s in scenes["test"]], ["tie", "direct", "mirror", "tie"])

    def test_counts_and_attempt_limit_reject_invalid_requests(self):
        for train, test, attempts in ((2, 4, 64), (3, 0, 64), (3, 4, 0), (True, 4, 64)):
            with self.assertRaises(ValueError):
                P.sample_inputs(17, train, test, max_attempts=attempts)
        first = P.sample_inputs(17, 3, 1, max_attempts=1)
        forbidden = {P.grid_key(first["train"][0]["input"])}
        with self.assertRaisesRegex(RuntimeError, "attempt"):
            P.sample_inputs(17, 3, 1, max_attempts=1, forbidden=forbidden)

    def test_query_answers_cannot_resolve_demo_ambiguity(self):
        demos = [{"input": [[9]], "output": [[1]]}]
        predictions = {
            "direct": {"train": [[[1]]], "test": [[[2]]]},
            "mirror": {"train": [[[1]]], "test": [[[3]]]},
            "always-direct": {"train": [[[4]]], "test": [[[2]]]},
        }
        certificate = P.identify_from_demos(demos, predictions)
        self.assertEqual(certificate["survivors"], ["direct", "mirror"])
        self.assertFalse(certificate["queries"][0]["identifiable"])
        self.assertEqual(certificate["eliminated"]["always-direct"], [0])
        predictions["mirror"]["test"] = [[[2]]]
        certificate = P.identify_from_demos(demos, predictions)
        self.assertEqual(certificate["survivors"], ["direct", "mirror"])
        self.assertTrue(certificate["queries"][0]["identifiable"])

    def test_public_writer_uses_only_visible_bytes_and_refuses_overwrite(self):
        challenge = {
            "train": [{"input": [[1]], "output": [[2]]}],
            "test": [{"input": [[3]], "output": [[9]], "private": "secret"}],
            "setting": "secret",
        }
        episode = {"setting": "direct", "challenge": challenge, "query_answers": [[[9]]], "certificate": {}}
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "batch"
            result = P.write_batch(out, [episode], {"direct": "(rule! identity)"}, {"private": "secret"})
            public_files = list((out / "public").iterdir())
            self.assertEqual(len(public_files), 1)
            data = public_files[0].read_bytes()
            self.assertEqual(public_files[0].stem, hashlib.sha256(data).hexdigest())
            self.assertEqual(json.loads(data), {
                "train": [{"input": [[1]], "output": [[2]]}],
                "test": [{"input": [[3]]}],
            })
            self.assertEqual(result["public_ids"], sorted(result["public_ids"]))
            private = json.loads((out / "private" / "manifest.json").read_text())
            self.assertEqual(private["episodes"][0]["query_answers"], [[[9]]])
            self.assertTrue((out / "private" / "programs" / "direct.rkt").is_file())
            with self.assertRaises(FileExistsError):
                P.write_batch(out, [episode], {}, {})

    def test_evidence_rejects_changed_source_before_starting_a_runtime(self):
        spec = importlib.util.spec_from_file_location("parametric_evidence", HERE / "evidence.py")
        evidence = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(evidence)
        with tempfile.TemporaryDirectory() as temp:
            batch = Path(temp)
            (batch / "private").mkdir()
            (batch / "private/manifest.json").write_text(json.dumps({
                "schema": "4512012999bb-parametric-proposal-v1",
                "provenance": {"prototype_sha256": "0" * 64},
            }))
            with self.assertRaisesRegex(ValueError, "source"):
                evidence.audit_batch(batch)


if __name__ == "__main__":
    unittest.main()
