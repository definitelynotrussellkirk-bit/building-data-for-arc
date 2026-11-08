"""Tests of the proposed exporter and demonstration-only certificates."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    "parametric_retention", Path(__file__).resolve().parents[1] / "workspace/parametric/retain.py")
retention = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(retention)


def episode(v=1):
    return {"seed": 8, "parameters": {"mode": "private"}, "program": "private-rule",
            "train": [{"input": [[0, v]], "output": [[v, v]]}],
            "test": [{"input": [[v, 0]], "output": [[9, 9]]}]}


class PublicExportTests(unittest.TestCase):
    def test_exact_visible_bytes_determine_name_and_sorted_batch(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "public"
            rows = retention.write_public_batch([episode(2), episode(1)], out)
            self.assertEqual([r["public_id"] for r in rows], sorted(r["public_id"] for r in rows))
            for row in rows:
                path = out / (row["public_id"] + ".json")
                body = path.read_bytes()
                self.assertEqual(hashlib.sha256(body).hexdigest(), row["public_id"])
                public = json.loads(body)
                self.assertEqual(set(public), {"train", "test"})
                self.assertEqual(set(public["test"][0]), {"input"})
                self.assertEqual(set(public["train"][0]), {"input", "output"})

    def test_private_changes_leave_public_name_and_bytes_identical(self):
        before = episode()
        after = copy.deepcopy(before)
        after.update(seed=999, parameters={"different": 2}, program="other", certificate={"private": 1})
        after["test"][0]["output"] = [[0, 0]]
        self.assertEqual(retention.public_challenge_bytes(before), retention.public_challenge_bytes(after))
        self.assertEqual(retention.public_challenge_id(before), retention.public_challenge_id(after))
        after["train"][0]["output"][0][0] = 7
        self.assertNotEqual(retention.public_challenge_id(before), retention.public_challenge_id(after))

    def test_duplicate_visible_payload_rejected_before_any_output(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "public"
            other = copy.deepcopy(episode())
            other["seed"] = -7
            other["test"][0]["output"] = [[2, 2]]
            with self.assertRaisesRegex(ValueError, "duplicate"):
                retention.write_public_batch([episode(), other], out)
            self.assertFalse(out.exists())

    def test_numeric_color_impostors_rejected(self):
        for value in [True, False, 1.0, "1", -1, 10]:
            item = episode()
            item["train"][0]["input"][0][0] = value
            with tempfile.TemporaryDirectory() as d, self.subTest(value=value):
                with self.assertRaises(ValueError):
                    retention.write_public_batch([item], Path(d) / "public")


class LessonCertificateTests(unittest.TestCase):
    def test_surviving_rival_disagreement_rejected(self):
        predictions = {"chosen": {"train": [[[1]]], "test": [[[2]]]},
                       "rival": {"train": [[[1]]], "test": [[[3]]]}}
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            retention.lesson_certificate(predictions, "chosen")

    def test_demonstrations_alone_eliminate_rivals(self):
        predictions = {"chosen": {"train": [[[1]]], "test": [[[2]], [[4]]]},
                       "rival": {"train": [[[0]]], "test": [[[9]], [[9]]]}}
        cert = retention.lesson_certificate(predictions, "chosen")
        self.assertEqual(cert["survivors"], ["chosen"])
        self.assertEqual(cert["eliminated"], {"rival": [0]})
        self.assertEqual(len(cert["queries"]), 2)
        changed = copy.deepcopy(predictions)
        changed["rival"]["test"] = [[[2]], [[4]]]
        self.assertEqual(retention.lesson_certificate(changed, "chosen")["survivors"], cert["survivors"])

    def test_equivalent_survivor_is_not_false_ambiguity(self):
        predictions = {"chosen": {"train": [[[1]]], "test": [[[2]]]},
                       "equivalent": {"train": [[[1]]], "test": [[[2]]]}}
        cert = retention.lesson_certificate(predictions, "chosen")
        self.assertEqual(cert["survivors"], ["chosen", "equivalent"])
        self.assertTrue(cert["queries"][0]["identified"])

    def test_missing_or_misaligned_predictions_rejected(self):
        for predictions in [{}, {"a": {"train": [], "test": [[[2]]]}},
                            {"a": {"train": [[[1]]], "test": [[[2]]]},
                             "b": {"train": [[[1]], [[1]]], "test": [[[2]]]}}]:
            with self.subTest(predictions=predictions), self.assertRaises(ValueError):
                retention.lesson_certificate(predictions, "a")


if __name__ == "__main__":
    unittest.main()
