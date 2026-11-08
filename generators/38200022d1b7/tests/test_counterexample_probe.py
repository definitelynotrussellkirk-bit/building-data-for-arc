"""Contract tests for the reusable shortcut-counterexample probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path

TASK_HOME = Path(__file__).resolve().parents[1]
PROBE_PATH = TASK_HOME / "workspace" / "counterexample_probe.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("counterexample_probe_38200022d1b7", PROBE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_emits_exact_verified_grid_center_counterexample():
    probe = _load_probe()
    report = probe.build_report(seed=38200022, sample_index=1, difficulty="medium")

    assert report["task_id"] == "38200022d1b7"
    assert report["shortcut"] == "grid_center"
    assert report["verified_disagreement"] is True
    assert report["self_check"] == []
    assert report["observed_axes"]["layout_profile"] == "quadrant_blob"
    assert (report["pivot"][0], report["pivot"][1]) != tuple(report["grid_center"])
    assert report["intended_output"] != report["shortcut_output"]
    assert report["intended_output"] == probe.GEN.rule_mirror(report["input"])
    assert report["shortcut_output"] == probe.GEN.CANONICAL_SHORTCUTS["grid_center"](
        report["input"]
    )
