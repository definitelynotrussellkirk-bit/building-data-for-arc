"""Tests for the reusable task-local semantic probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path

TASK_HOME = Path(__file__).resolve().parents[1]
PROBE_PATH = TASK_HOME / "workspace" / "reference_probe.py"


def _load_probe():
    assert PROBE_PATH.exists(), "workspace/reference_probe.py is required"
    spec = importlib.util.spec_from_file_location("projection_reference_probe", PROBE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_reports_all_declared_shortcuts_fit_canonical_and_have_counterexamples():
    probe = _load_probe()
    report = probe.run_probe(seeds=range(2), starts=range(3))
    assert report["canonical_shortcuts"]
    assert all(row["fits_all_canonical"] for row in report["canonical_shortcuts"].values())
    assert set(report["counterexample"]["rival_differences"]) == {
        "fixed_grid_center",
        "extends_to_bottom",
    }
    assert all(report["counterexample"]["rival_differences"].values())


def test_probe_exhausts_all_four_pair_rotations_for_each_requested_start():
    probe = _load_probe()
    report = probe.run_probe(seeds=range(2), starts=range(5))
    rotations = report["rotations"]
    assert rotations["lessons"] == 2 * 5 * 3
    assert rotations["rotations"] == rotations["lessons"] * 4
    assert rotations["ambiguities"] == []
    assert rotations["competitor_errors"] == []
