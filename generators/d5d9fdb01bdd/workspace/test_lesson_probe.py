"""Regression test for the retained lesson probe."""
from __future__ import annotations

import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

import lesson_probe  # noqa: E402


def test_probe_covers_rotations_rivals_and_joint_overrides():
    report = lesson_probe.build_report(windows_per_band=4, seed=515_000)
    assert report["passed"] is True, report["failures"]
    assert report["canonical_shortcut_fit"] == {
        "transpose_only_tall_or_square": True
    }
    assert set(report["competitors"]) == {
        "transpose_only_tall_or_square",
        "largest_component_only",
    }
    assert report["joint_boundary_overrides"]["cases"] == 24
    assert report["joint_boundary_overrides"]["failures"] == []
    for band in ("easy", "medium", "hard"):
        summary = report["bands"][band]
        assert summary["query_rotation_failures"] == []
        assert summary["unique_inputs"] == summary["examples"] == 16
    json.dumps(report, sort_keys=True)
