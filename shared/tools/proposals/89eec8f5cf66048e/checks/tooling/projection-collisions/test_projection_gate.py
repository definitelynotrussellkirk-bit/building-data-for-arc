"""Focused tests of observed collisions, coverage accounting and provenance.

Small synthetic labels below test the program only; they are not puzzle evidence.
"""
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
import tempfile
import unittest

try:
    gate = importlib.import_module("projection_gate")
except ModuleNotFoundError as error:
    if error.name != "projection_gate":
        raise
    gate = None

HERE = Path(__file__).resolve().parent
G1 = [[2, 0], [0, 5]]
Y1 = [[2, 4], [0, 5]]
G2 = [[2, 5], [0, 5]]
Y2 = [[2, 5], [4, 5]]


def envelope(cases):
    return {
        "schema": "projection-cases-v1",
        "task_id": "fc814cec3976",
        "source": {"generator_sha256": "a" * 64},
        "rule": {"normalized_hash": "98e91a32d7ba", "callable_sha256": "b" * 64},
        "label_authority": {"kind": "python_mirror", "note": "synthetic unittest labels only"},
        "scope": "synthetic_unit_test",
        "examples": [dict(id=name, input=deepcopy(inp), output=deepcopy(out))
                     for name, inp, out in cases],
    }


class ProjectionGateTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(gate, "projection_gate implementation is required")

    def test_distinct_contexts_with_same_red_layout_produce_witness(self):
        report = gate.analyze(envelope([("a", G1, Y1), ("b", G2, Y2)]))
        self.assertEqual(report["status"], "witnessed_collision")
        self.assertEqual(report["summary"]["collision_keys"], 1)
        group = report["groups"][0]
        self.assertEqual(group["unique_inputs"], 2)
        self.assertEqual(group["distinct_contexts"], 2)
        self.assertEqual(group["distinct_targets"], 2)
        self.assertEqual(group["witness"]["case_ids"], ["a", "b"])
        self.assertFalse(report["general_learnability_certified"])
        self.assertEqual(report["label_authority"]["verification"], "declared_only")

    def test_duplicates_do_not_create_context_coverage_or_collision(self):
        report = gate.analyze(envelope([("a", G1, Y1), ("a_copy", G1, Y1)]))
        self.assertEqual(report["status"], "unknown_no_witnessed_collision")
        self.assertEqual(report["summary"]["duplicate_inputs"], 1)
        self.assertEqual(report["summary"]["duplicate_labeled_cases"], 1)
        self.assertEqual(report["groups"][0]["distinct_contexts"], 1)
        self.assertIsNone(report["groups"][0]["witness"])

    def test_distinct_contexts_with_same_target_are_unknown(self):
        same_centers = [[2, 4], [0, 5]]
        report = gate.analyze(envelope([("a", G1, Y1), ("b", G2, same_centers)]))
        self.assertEqual(report["status"], "unknown_no_witnessed_collision")
        self.assertEqual(report["groups"][0]["distinct_contexts"], 2)
        self.assertEqual(report["groups"][0]["distinct_targets"], 1)

    def test_different_red_layouts_are_different_keys(self):
        other_input = [[0, 0], [2, 5]]
        other_output = [[4, 0], [2, 5]]
        report = gate.analyze(envelope([("a", G1, Y1), ("b", other_input, other_output)]))
        self.assertEqual(report["summary"]["projection_keys"], 2)
        self.assertEqual(report["summary"]["collision_keys"], 0)

    def test_grid_shape_is_part_of_red_layout_key(self):
        report = gate.analyze(envelope([("a", [[2, 0]], [[2, 4]]),
                                       ("b", [[2], [0]], [[2], [4]])]))
        self.assertEqual(report["summary"]["projection_keys"], 2)

    def test_yellow_centers_ignore_preexisting_yellow(self):
        report = gate.analyze(envelope([("a", [[2, 4], [0, 5]], [[2, 4], [0, 5]])]))
        self.assertEqual(report["cases"][0]["target"], [])

    def test_edit_mask_uses_changed_coordinates_not_full_output(self):
        data = envelope([("a", G1, [[2, 4], [0, 5]]),
                         ("b", G2, [[2, 0], [0, 5]])])
        report = gate.analyze(data, target="edit-mask")
        self.assertEqual(report["status"], "unknown_no_witnessed_collision")
        self.assertEqual(report["cases"][0]["target"], [[0, 1]])
        self.assertEqual(report["cases"][1]["target"], [[0, 1]])

    def test_malformed_grids_are_rejected(self):
        for bad in ([], [[]], [[2], [0, 5]], [[True]], [[10]], [[-1]], [[2.0]]):
            with self.subTest(grid=bad):
                data = envelope([("bad", G1, Y1)])
                data["examples"][0]["input"] = bad
                with self.assertRaisesRegex(ValueError, "grid"):
                    gate.analyze(data)

    def test_input_and_output_shape_must_match(self):
        data = envelope([("bad", G1, [[2, 4]])])
        with self.assertRaisesRegex(ValueError, "shape"):
            gate.analyze(data)

    def test_conflicting_labels_for_identical_input_are_not_collision(self):
        data = envelope([("a", G1, Y1), ("b", G1, Y2)])
        with self.assertRaisesRegex(ValueError, "conflicting labels"):
            gate.analyze(data)

    def test_duplicate_case_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "unique"):
            gate.analyze(envelope([("a", G1, Y1), ("a", G2, Y2)]))

    def test_declared_input_and_output_hashes_are_checked(self):
        for field in ("input_sha256", "output_sha256"):
            data = envelope([("a", G1, Y1)])
            data["examples"][0][field] = "c" * 64
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "hash"):
                gate.analyze(data)

    def test_certifying_requires_complete_provenance(self):
        data = envelope([("a", G1, Y1)])
        del data["source"]
        with self.assertRaisesRegex(ValueError, "provenance"):
            gate.analyze(data, certify=True)

    def test_python_mirror_labels_cannot_certify(self):
        with self.assertRaisesRegex(ValueError, "selected_racket"):
            gate.analyze(envelope([("a", G1, Y1)]), certify=True)

    def test_certifying_binds_receipt_and_retains_off_support_scope(self):
        data = envelope([("a", G1, Y1), ("b", G2, Y2)])
        data["scope"] = "baseline_off_support_counterfactual"
        receipt = {
            "schema": "arcpuzzles-apply-v1", "task_id": data["task_id"],
            "generator_sha256": "a" * 64, "reference": "canonical",
            "executed_rule_hash": "98e91a32d7ba", "catalog_rule_hash": "98e91a32d7ba",
            "rule_hash_matches_catalog": True, "rule_text_sha256": "b" * 64,
            "results": [
                {"index": i, "input": case["input"], "output": case["output"],
                 "input_sha256": gate.json_sha256(case["input"]),
                 "output_sha256": gate.json_sha256(case["output"]),
                 "valid_output": True, "error": None,
                 "generator_domain": {"status": "valid" if i == 0 else "invalid", "errors": []}}
                for i, case in enumerate(data["examples"])
            ],
        }
        # Synthetic receipt exercises binding mechanics only; not real ARC evidence.
        with tempfile.TemporaryDirectory(prefix="unittest-", dir=HERE) as directory:
            path = Path(directory) / "receipt.json"
            raw = json.dumps(receipt).encode()
            path.write_bytes(raw)
            data["label_authority"] = {
                "kind": "selected_racket", "receipt_path": "receipt.json",
                "receipt_sha256": hashlib.sha256(raw).hexdigest(),
            }
            for i, case in enumerate(data["examples"]):
                case["receipt_result_index"] = i
            report = gate.analyze(data, certify=True, base_dir=path.parent)
            self.assertEqual(report["status"], "witnessed_collision")
            self.assertEqual(report["label_authority"]["verification"], "receipt_hash_and_cases_verified")
            self.assertEqual(report["summary"]["witnesses_with_domain_rejection"], 1)
            self.assertFalse(report["generated_support_certified"])
            data["examples"][0]["output"] = deepcopy(Y2)
            with self.assertRaisesRegex(ValueError, "receipt"):
                gate.analyze(data, certify=True, base_dir=path.parent)
            data["examples"][0]["output"] = deepcopy(Y1)
            path.write_bytes(raw + b" ")
            with self.assertRaisesRegex(ValueError, "receipt.*hash"):
                gate.analyze(data, certify=True, base_dir=path.parent)


if __name__ == "__main__":
    unittest.main()
