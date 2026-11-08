"""Behavior of the opt-in retained-apply conservation authoring check."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest
from reviewer_support import find_root


ROOT = find_root(__file__)
HOME = ROOT / "generators/7071285d78ce"
TOOL = HOME / "workspace/check_color_conservation.py"
WITNESS = HOME / "counterexamples/current_review/racket-labels.json"


def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def lawful_receipt():
    pairs = [([[1, 2, 0]], [[0], [2], [1]]),
             ([[3, 3], [9, 0]], [[9, 3, 3]]), ([[0]], [[0, 0]])]
    return {"schema": "arcpuzzles-apply-v1", "task_id": "fixture",
            "rule_task_id": "fixture", "generator_sha256": "a" * 64,
            "rule_text_sha256": "b" * 64, "executed_rule_hash": "c" * 12,
            "catalog_rule_hash": "c" * 12, "rule_hash_matches_catalog": True,
            "results": [{"index": i, "input": inp, "output": out,
                         "valid_output": True, "error": None,
                         "input_sha256": digest(inp), "output_sha256": digest(out)}
                        for i, (inp, out) in enumerate(pairs)]}


def run(tmp_path, payload=None, receipt=None):
    if receipt is None:
        receipt = tmp_path / "input.json"
        receipt.write_text(json.dumps(payload))
    output = tmp_path / "check.json"
    process = subprocess.run([sys.executable, str(TOOL), "--receipt", str(receipt),
                              "--out", str(output)], capture_output=True, text=True)
    return process, output


def test_retained_racket_witness(tmp_path):
    process, output = run(tmp_path, receipt=WITNESS)
    assert process.returncode == 1, process.stderr
    report = json.loads(output.read_text())
    assert report["status"] == "FAIL"
    assert report["receipt_sha256"] == hashlib.sha256(WITNESS.read_bytes()).hexdigest()
    original = json.loads(WITNESS.read_text())
    assert report["generator_sha256"] == original["generator_sha256"]
    assert report["executed_rule_hash"] == original["executed_rule_hash"]
    assert [row["preserved"] for row in report["results"]] == [True, True, False]
    bad = report["results"][2]
    assert bad["delta_by_color"]["2"] == -2
    assert bad["lost_cells"] == 2 and bad["gained_cells"] == 0


def test_three_lawful_pairs_allow_shape_and_background_changes(tmp_path):
    process, output = run(tmp_path, lawful_receipt())
    assert process.returncode == 0, process.stderr
    report = json.loads(output.read_text())
    assert report["status"] == "PASS" and report["checked_rows"] == 3
    assert all(row["preserved"] for row in report["results"])


def test_equal_foreground_total_still_requires_each_color(tmp_path):
    payload = lawful_receipt()
    payload["results"][0]["output"] = [[1, 3, 0]]
    payload["results"][0]["output_sha256"] = digest([[1, 3, 0]])
    process, output = run(tmp_path, payload)
    assert process.returncode == 1
    result = json.loads(output.read_text())["results"][0]
    assert result["delta_by_color"]["2"] == -1
    assert result["delta_by_color"]["3"] == 1
    assert result["lost_cells"] == result["gained_cells"] == 1


@pytest.mark.parametrize("defect", ["empty", "missing_identity", "rule_drift",
                                    "input_drift", "output_drift", "error",
                                    "invalid", "ragged", "boolean", "missing_error",
                                    "schema", "match_flag"])
def test_invalid_evidence_is_error(tmp_path, defect):
    payload = copy.deepcopy(lawful_receipt())
    row = payload["results"][0]
    if defect == "empty":
        payload["results"] = []
    elif defect == "missing_identity":
        del payload["generator_sha256"]
    elif defect == "rule_drift":
        payload["executed_rule_hash"] = "d" * 12
    elif defect == "input_drift":
        row["input"][0][0] = 9
    elif defect == "output_drift":
        row["output_sha256"] = "e" * 64
    elif defect == "error":
        row["error"] = "Racket failed"
    elif defect == "invalid":
        row["valid_output"] = False
    elif defect == "ragged":
        row["input"] = [[1], [2, 3]]
        row["input_sha256"] = digest(row["input"])
    elif defect == "boolean":
        row["output"] = [[True]]
        row["output_sha256"] = digest(row["output"])
    elif defect == "missing_error":
        del row["error"]
    elif defect == "schema":
        payload["schema"] = "unknown"
    else:
        payload["rule_hash_matches_catalog"] = False
    process, output = run(tmp_path, payload)
    assert process.returncode == 2, process.stderr
    assert json.loads(output.read_text())["status"] == "ERROR"


def test_malformed_json(tmp_path):
    receipt = tmp_path / "broken.json"
    receipt.write_text("{broken")
    process, output = run(tmp_path, receipt=receipt)
    assert process.returncode == 2
    assert json.loads(output.read_text())["status"] == "ERROR"


def test_existing_output_is_untouched(tmp_path):
    output = tmp_path / "check.json"
    output.write_text("retain me")
    process, same_output = run(tmp_path, lawful_receipt())
    assert process.returncode == 2
    assert same_output.read_text() == "retain me"
