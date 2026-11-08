from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_tool():
    path = Path(__file__).resolve().parents[1] / "workspace" / "audit_curriculum.py"
    spec = importlib.util.spec_from_file_location("audit_curriculum_4c17a205be08", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_curriculum_audit_reports_canonical_shortcut_witnesses_and_windows():
    tool = _load_tool()
    report = tool.build_report(seed=20261002, samples=12)

    assert report["task_id"] == "4c17a205be08"
    assert report["canonical"]["pair_count"] == 5
    shortcut = report["canonical"]["shortcuts"]["observed_transform_family_only"]
    assert shortcut["matched_pairs"] == 5
    assert shortcut["total_pairs"] == 5

    generated = report["generated"]
    assert generated["sample_count"] == 12
    assert generated["invalid_count"] == 0
    assert generated["transform_counts"] == {
        "flip_lr": 2,
        "flip_ud": 2,
        "identity": 2,
        "rotate_180": 2,
        "rotate_ccw": 2,
        "rotate_cw": 2,
    }
    refuted = generated["shortcut_refutations"]["observed_transform_family_only"]
    assert refuted["disagreement_count"] == 4
    assert set(refuted["disagreement_transforms"]) == {"identity", "flip_ud"}
    assert refuted["first_witness"]["input"]
    assert refuted["first_witness"]["authoritative_output"] != refuted["first_witness"]["rival_output"]

    windows = report["lesson_windows"]
    assert windows["checked"] == 18
    assert windows["identifiable"] == 18
    assert windows["failures"] == []
