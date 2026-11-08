"""Regression tests for the reusable pinned-lesson shortcut probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path


PROBE_PATH = Path(__file__).resolve().parents[1] / "workspace" / "lesson_probe.py"


def _load_probe():
    assert PROBE_PATH.is_file(), "workspace/lesson_probe.py must exist"
    spec = importlib.util.spec_from_file_location("lesson_probe_8c6fbfbe20d4", PROBE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_mirror_probe_refutes_every_declared_rival_in_each_band() -> None:
    probe = _load_probe()
    report = probe.run_probe(lessons_per_band=2, mode="mirror")

    assert report["status"] == "pass"
    assert report["requested_per_band"] == {"easy": 2, "medium": 2, "hard": 2}
    assert report["materialization_errors"] == []
    assert report["hook_errors"] == []
    assert report["unidentifiable_lessons"] == 0
    assert all(
        count == 0
        for count in report["competitor_survivor_counts"].values()
    )
    assert (
        report["competitor_survivor_counts"]
        ["erase_body_colors_absent_from_headers"]
        == 0
    )
