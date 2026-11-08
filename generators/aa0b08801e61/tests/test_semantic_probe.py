"""Portable regression for the task-local semantic probe."""
from __future__ import annotations

import importlib.util

from reviewer_support import find_root

TASK_ID = "aa0b08801e61"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PROBE = HOME / "workspace" / "semantic_probe.py"
SPEC = importlib.util.spec_from_file_location("aa0b08801e61_semantic_probe", PROBE)
assert SPEC and SPEC.loader
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def test_semantic_probe_exhausts_public_contract_and_curriculum():
    report = probe.analyze(seed=20261012)
    assert report["status"] == "pass"
    assert report["task_id"] == "aa0b08801e61"
    assert report["canonical_shortcuts"]["canonical_mask_lookup"] == {
        "fits": 4,
        "pairs": 4,
    }
    assert report["shape_banks"] == {
        "declared_masks": 12,
        "unique_masks": 12,
        "canonical_masks": 4,
        "novel_masks": 8,
        "classes": {
            class_name: {
                "declared": 3,
                "unique": 3,
                "canonical": 1,
                "novel": 2,
                "class_matches": 3,
                "connected": 3,
            }
            for class_name in ("both", "lr", "none", "ud")
        },
        "failures": [],
    }
    assert report["joint_overrides"] == {
        "attempted": 294,
        "accepted": 294,
        "exact": 294,
        "self_check_passed": 294,
        "unique_axis_triples": 98,
        "failures": [],
    }
    assert report["schedule"]["lessons"] == 12
    assert report["schedule"]["rotations"] == 48
    assert report["schedule"]["ambiguous_lessons"] == 0
    assert report["schedule"]["ambiguous_rotations"] == 0
    assert report["counterexample"]["self_check"] == []
    assert report["counterexample"]["shortcut_disagrees"] is True


def test_retained_counterexample_is_source_bound_and_replayable():
    import json

    path = HOME / "counterexamples" / "canonical-mask-lookup" / "counterexample.json"
    case = json.loads(path.read_text())
    report = probe.analyze(seed=case["reproduction"]["seed"])
    witness = report["counterexample"]
    assert case["generator"]["sha256"] == report["generator"]["sha256"]
    assert case["racket_receipt"]["executed_rule_hash"] == report["generator"]["rule_hash"]
    assert case["input"] == witness["input"]
    assert case["python_mirror_output"] == witness["intended_output"]
    assert case["canonical_mask_lookup_output"] == witness["shortcut_output"]
    assert case["checks"]["racket_matches_python_mirror"] is True
    assert case["checks"]["shortcut_disagrees_with_racket"] is True
