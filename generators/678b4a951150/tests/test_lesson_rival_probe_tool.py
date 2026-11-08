"""Portable smoke test for the task-local declared-rival probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve()
TOOL_PATH = HERE.parents[1] / "workspace" / "lesson_rival_probe.py"
SPEC = importlib.util.spec_from_file_location("lesson_rival_probe", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


def test_probe_checks_cyclic_starts_and_query_rotations() -> None:
    report = PROBE.probe(
        seeds=range(2),
        bands=("easy", "medium", "hard"),
        starts=range(4),
        rotate_query=True,
        max_examples=1,
    )
    assert report["summary"]["lesson_windows"] == 24
    assert report["summary"]["evaluated_queries"] == 120
    assert report["summary"]["ambiguous_queries"] == 0
    assert report["summary"]["hook_warning_queries"] == 0
    assert set(report["declared_rivals"]) >= {
        "equal_nonzero_gap",
        "interior_rows_only",
        "target_rows_without_six",
    }
