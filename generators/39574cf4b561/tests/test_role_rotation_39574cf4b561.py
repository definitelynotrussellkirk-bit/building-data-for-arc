"""Regression tests for color-role shortcut resistance."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

GENERATOR_PATH = ROOT / "generators" / "39574cf4b561" / "generator.py"
SPEC = importlib.util.spec_from_file_location(
    "generator_role_rotation_39574cf4b561", GENERATOR_PATH
)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def canonical_pairs():
    with (ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == GEN.TASK_ID:
                return row["train"] + row["test"]
    raise AssertionError("canonical task row not found")


def never_complete_color_9(grid):
    """Plausible wrong rule: color 9 is always the irrelevant marker."""
    analysis = GEN._analyze(grid)
    if analysis["errors"]:
        raise ValueError(analysis["errors"])
    out = [list(row) for row in grid]
    for rectangle in analysis["rectangles"]:
        if rectangle["color"] == 9:
            continue
        row, col = rectangle["missing"]
        out[row][col] = rectangle["color"]
    return out


def test_default_distribution_refutes_never_complete_color_9_shortcut():
    assert all(
        never_complete_color_9(pair["input"]) == pair["output"]
        for pair in canonical_pairs()
    ), "the proposed rival must genuinely fit every canonical demonstration"

    counterexamples = []
    for sample_index in range(40):
        grid = GEN.generate(271_828, sample_index, difficulty="medium")
        if never_complete_color_9(grid) != GEN.rule_mirror(grid):
            counterexamples.append(sample_index)

    assert counterexamples, (
        "default generation must emit active-color-9 cases that falsify the "
        "canonical-fitting 'never complete color 9' shortcut"
    )


def test_lesson_shortcut_audit_checks_sliding_windows_and_saves_counterexample():
    tool_path = (
        ROOT
        / "generators"
        / "39574cf4b561"
        / "workspace"
        / "lesson_shortcut_audit.py"
    )
    assert tool_path.exists(), "lesson shortcut audit tool has not been built"
    spec = importlib.util.spec_from_file_location(
        "lesson_shortcut_audit_39574cf4b561", tool_path
    )
    assert spec and spec.loader
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)

    report = tool.audit(period=20, seed=610_000)
    assert report["status"] == "PASS"
    assert report["canonical_shortcuts"]["never_complete_color_9"]["fits_all"]
    assert report["counterexample"]["shortcut"] == "never_complete_color_9"
    assert report["counterexample"]["active_color_9"] is True
    assert report["schedule_period_basis"].endswith("color_role=3)")
    assert all(
        band["unidentifiable_windows"] == 0
        and band["never_complete_color_9_survivors"] == 0
        for band in report["bands"].values()
    )
