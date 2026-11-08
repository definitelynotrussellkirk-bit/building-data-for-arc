from __future__ import annotations

import importlib.util
from pathlib import Path

TASK_HOME = Path(__file__).resolve().parents[1]
PROBE_PATH = TASK_HOME / "workspace" / "audit_curriculum.py"
SPEC = importlib.util.spec_from_file_location("audit_curriculum_a3086dea6cff", PROBE_PATH)
assert SPEC and SPEC.loader
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


def test_independent_rule_connects_only_exact_two_aligned_cells():
    grid = [
        [1, 0, 0, 1, 0, 2],
        [0, 0, 0, 0, 0, 0],
        [3, 0, 4, 0, 0, 2],
        [0, 0, 0, 0, 0, 0],
        [3, 0, 0, 4, 0, 0],
        [5, 0, 5, 0, 5, 0],
    ]
    expected = [
        [1, 1, 1, 1, 0, 2],
        [0, 0, 0, 0, 0, 2],
        [3, 0, 4, 0, 0, 2],
        [3, 0, 0, 0, 0, 0],
        [3, 0, 0, 4, 0, 0],
        [5, 0, 5, 0, 5, 0],
    ]
    assert PROBE.intended_rule(grid) == expected


def test_selected_generator_has_complete_three_demo_curriculum():
    report = PROBE.run_probe(
        generator_path=TASK_HOME / "generator.py",
        seeds=3,
        starts=3,
    )
    assert report["failures"] == []
    assert report["summary"]["scenes_without_both_orientations"] == 0
    assert report["summary"]["incomplete_windows"] == 0
    assert all(
        result["fits_all_canonical"] and result["generated_counterexample"] is not None
        for result in report["canonical_shortcuts"].values()
    )


def test_frozen_baseline_reproduces_orientation_shortcut_window():
    report = PROBE.run_probe(
        generator_path=TASK_HOME / "workspace" / "generator-before.py",
        seeds=1,
        starts=1,
    )
    assert report["summary"]["scenes_without_both_orientations"] > 0
    assert report["summary"]["incomplete_windows"] > 0
    assert report["failures"]
