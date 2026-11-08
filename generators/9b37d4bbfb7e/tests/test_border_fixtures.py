"""Focused saved-authority regressions; run explicitly from any staged task root.

These tests catch merging different colors, diagonal merging, color-wide erasure,
ignored right edges, erasing only two objects, and keeping only the largest survivor.
Legacy identity/blank-output fixtures remain data, never production textures.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root, load_selected_generator

TASK = "9b37d4bbfb7e"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)
FIXTURE_PATH = Path(__file__).resolve().parent.parent / "counterexamples/border-semantics-fixtures.json"
DATA = json.loads(FIXTURE_PATH.read_text())
CASES = {record["name"]: record for record in DATA["fixtures"]}
POSITIVE = {
    "repeated_color": [(2, 3, 4), (3, 4, 1)],
    "diagonal": [(2, 1, 2), (3, 4, 4)],
    "cardinal_different": [(3, 1, 2), (3, 2, 2)],
    "right_only": [(3, 2, 2)],
    "third_border_unequal_interior": [(5, 2, 2), (5, 2, 3), (6, 3, 4)],
}
NEGATIVE = [record["name"] for record in DATA["fixtures"] if record["kind"] == "negative"]


@pytest.mark.parametrize("name", POSITIVE)
def test_minimal_positive_witness_is_in_production_domain(name):
    assert GEN.self_check(CASES[name]["input"]) == []


@pytest.mark.parametrize("name", POSITIVE)
def test_saved_racket_label_preserves_exact_interior_components(name):
    record = CASES[name]
    assert "racket_output" in record, "Run public Racket apply and probe analyze to bind labels"
    expected = [[0] * 7 for _ in range(6)]
    for color, row, column in POSITIVE[name]:
        expected[row][column] = color
    assert record["racket_output"] == expected


@pytest.mark.parametrize("name", NEGATIVE)
def test_legacy_negative_fixture_is_rejected_by_validator(name):
    assert GEN.self_check(CASES[name]["input"])
    assert CASES[name]["ordinary_production"] is False


@pytest.mark.parametrize("name", NEGATIVE)
def test_legacy_negative_texture_cannot_enter_ordinary_generation(name):
    with pytest.raises(ValueError, match="negative fixtures are not production textures"):
        GEN.generate(0, 0, difficulty="medium", texture=name)


@pytest.mark.parametrize("name", NEGATIVE)
def test_saved_negative_labels_are_explicit_identity_or_blank(name):
    record = CASES[name]
    assert "racket_output" in record, "Run public Racket apply and probe analyze to bind labels"
    expected = record["input"] if name == "no_border_blobs" else [[0] * 9 for _ in range(8)]
    assert record["racket_output"] == expected


def test_saved_labels_identify_the_current_racket_rule():
    assert DATA["label_status"] == "public_racket_verified"
    assert DATA["executed_rule_hash"] == GEN.RULE_HASH
    assert DATA["rule_text_sha256"]


def test_minimal_witnesses_refute_every_declared_canonical_shortcut():
    assert all("racket_output" in CASES[name] for name in POSITIVE)
    for rival_name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert any(rival(CASES[name]["input"]) != CASES[name]["racket_output"]
                   for name in POSITIVE), rival_name


@pytest.mark.parametrize("corruption", ["reordered_results", "input_payload", "output_payload", "population_hash"])
def test_receipt_validation_rejects_mismatched_or_tampered_evidence(corruption):
    path = FIXTURE_PATH.parent.parent / "workspace/probe_border_semantics.py"
    spec = importlib.util.spec_from_file_location("border_receipt_probe", path)
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    # A two-case subset assembled only from the saved public-authority fields.
    records = [CASES["repeated_color"], CASES["diagonal"]]
    grids = [copy.deepcopy(record["input"]) for record in records]
    population = {"generator_sha256": DATA["generator_sha256"],
                  "cases": [{"case_index": index, "input_sha256": record["input_sha256"]}
                            for index, record in enumerate(records)]}
    receipt = {"generator_sha256": DATA["generator_sha256"],
               "executed_rule_hash": DATA["executed_rule_hash"],
               "rule_hash_matches_catalog": True, "command": DATA["racket_command"],
               "results": [{"index": index, "input": copy.deepcopy(record["input"]),
                            "output": copy.deepcopy(record["racket_output"]),
                            "input_sha256": record["input_sha256"], "output_sha256": record["output_sha256"],
                            "valid_output": True, "error": None}
                           for index, record in enumerate(records)]}
    args = (DATA["generator_sha256"], DATA["executed_rule_hash"])
    probe.validate_receipt(grids, population, receipt, *args)
    if corruption == "reordered_results":
        receipt["results"].reverse()
        for index, result in enumerate(receipt["results"]):
            result["index"] = index  # Correct numbering must not conceal changed input order.
    elif corruption == "input_payload":
        receipt["results"][0]["input"][0][1] = 8
    elif corruption == "output_payload":
        receipt["results"][0]["output"][3][4] = 0
    else:
        population["cases"][0]["input_sha256"] = "0" * 64
    with pytest.raises(AssertionError):
        probe.validate_receipt(grids, population, receipt, *args)
