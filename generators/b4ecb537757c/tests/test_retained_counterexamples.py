"""Actual old-validator failures, labeled by the unchanged Racket authority."""
import json
from pathlib import Path
import pytest
from reviewer_support import find_root, load_selected_generator

ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator("b4ecb537757c", root=ROOT)
CASES = sorted((ROOT / "generators/b4ecb537757c/counterexamples").glob("*.json"))

@pytest.mark.parametrize("path", CASES, ids=lambda p: p.stem)
def test_racket_labelled_bad_domain_inputs_are_rejected(path):
    case = json.loads(path.read_text())
    assert case["baseline_self_check"] == []
    assert case["rule_hash"] == GEN.RULE_HASH
    assert GEN.self_check(case["input"]), "old accepted-domain counterexample was readmitted"

def test_all_retained_failure_fixtures_are_present():
    assert {p.stem for p in CASES} == {
        "generated_easy_s0_i5", "generated_medium_s0_i3",
        "generated_hard_s0_i1", "hand_clipping",
        "hand_bbox_contamination", "review_nested_frames",
    }
