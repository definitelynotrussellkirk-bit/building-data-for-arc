"""Regression for the reusable exhaustive cyclic lesson probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parents[1]
PROBE_PATH = TASK_ROOT / "workspace" / "cyclic_lesson_probe.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("cyclic_lesson_probe", PROBE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_exhausts_requested_windows_and_axis_boundaries() -> None:
    probe = _load_probe()
    report = probe.audit(seeds=range(3), starts=range(8), check_axes=True)

    assert report["schema"] == "2ca60ab198d6-cyclic-lesson-probe-v1"
    assert report["passed"] is True
    assert report["lesson_windows"] == 3 * 8 * 3
    assert report["axis_cases"] == 432
    assert report["failures"] == []
    assert report["canonical_shortcuts_checked"] == sorted(
        report["canonical_shortcuts_fit"]
    )
    assert all(report["canonical_shortcuts_fit"].values())
    assert all(count > 0 for count in report["witness_counts"].values())
