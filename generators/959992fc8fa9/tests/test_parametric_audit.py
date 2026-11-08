"""Focused checks for the replayable finite self-audit tool."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve()
AUDIT = HERE.parents[1] / "workspace" / "parametric" / "audit.py"


def _load():
    spec = importlib.util.spec_from_file_location("_test_959992fc8fa9_audit", AUDIT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_finite_audit_covers_settings_shortcuts_matched_inputs_and_public_projection():
    audit = _load()
    report = audit.build_report(seeds=[0], demo_counts=[2], include_racket=False)
    assert report["schema"] == "959992fc8fa9-parametric-self-audit-v1"
    assert report["status"] == "passed"
    assert report["summary"] == {
        "cases": 2,
        "all_lessons_unique": True,
        "all_shortcuts_rejected": True,
        "all_inputs_setting_independent": True,
        "all_public_projections_private_invariant": True,
        "query_outputs_consulted": False,
    }
    assert report["racket_case"] is None
    assert all(case["query_shapes"][-1] == [30, 30] for case in report["cases"])
