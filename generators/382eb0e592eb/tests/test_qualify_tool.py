"""Regression tests for the task-local future-review qualification tool."""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

TOOL_PATH = Path(__file__).resolve().parents[1] / "workspace" / "qualify.py"
SPEC = spec_from_file_location("qualify_382eb0e592eb", TOOL_PATH)
assert SPEC and SPEC.loader
TOOL = module_from_spec(SPEC)
sys.modules[SPEC.name] = TOOL
SPEC.loader.exec_module(TOOL)


def test_report_uses_declared_registries_and_exhausts_schedule_rotations():
    report = TOOL.qualify(seed=0)
    assert report["passed"] is True
    assert report["source"]["rule_hash"] == "03fbcf596117"
    assert report["canonical_shortcuts"]["all_fit"] is True
    assert report["canonical_shortcuts"]["names"] == [
        "blank_below_only",
        "bottom_pair_upwards",
        "copy_all_nonzero_down",
        "exact_domino_only",
    ]
    assert report["schedule"]["bands"] == ["easy", "medium", "hard"]
    assert report["schedule"]["period"] == 4
    assert report["schedule"]["lesson_windows"] == 12
    assert report["schedule"]["query_rotations"] == 48
    assert report["schedule"]["ambiguous_rotations"] == []
    assert report["schedule"]["observed_profiles"] == [
        "canonical_3x6",
        "canonical_4x5",
        "semantic_3x6",
        "semantic_4x5",
    ]
