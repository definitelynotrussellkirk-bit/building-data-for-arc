"""Behavioral regressions for validation, exact controls, and rotated lessons."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


SOURCE = Path(__file__).resolve().parent.parent / "generator.py"
SPEC = importlib.util.spec_from_file_location("review_target_89ab40aedfe4", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def test_foreign_top_row_color_is_rejected_without_hanging():
    # Before repair a foreign top-row cell never advanced the marker scanner.
    program = """
import importlib.util, json, sys
s = importlib.util.spec_from_file_location('foreign_color_target', sys.argv[1])
g = importlib.util.module_from_spec(s)
sys.modules[s.name] = g
s.loader.exec_module(g)
grid = [[2,2,0,2,2,0,2,2],
        [2,2,0,2,0,0,2,0],
        [2,2,0,2,0,0,2,2]] + [[2,0,0,2,0,0,2,0] for _ in range(5)]
assert g.self_check(grid) == []
for col in range(1, len(grid[0])):
    bad = [row[:] for row in grid]
    bad[0][col] = 3
    errors = g.self_check(bad)
    assert errors and any('foreground' in e for e in errors), errors
print(json.dumps({'rejected_positions': 7}))
"""
    try:
        run = subprocess.run([sys.executable, "-c", program, str(SOURCE)],
                             text=True, capture_output=True, timeout=3)
    except subprocess.TimeoutExpired:
        pytest.fail("self_check did not return for a foreign top-row color")
    assert run.returncode == 0, run.stderr
    assert json.loads(run.stdout)["rejected_positions"] == 7


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_query_rotation_keeps_the_declared_distinctions(band):
    # A sole tie or marker witness must not become the held-out query.
    for seed in (0, 7001, 8100):
        for start in range(len(GEN.SCHEDULE_PROFILES)):
            pairs = []
            for offset in range(GEN.EXAMPLES_NEEDED + 1):
                grid = GEN.generate(seed, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            for held_out, query in enumerate(pairs):
                demos = [p for i, p in enumerate(pairs) if i != held_out]
                reasons = GEN.lesson_identifiable(demos, query)
                assert reasons == [], (band, seed, start, held_out, reasons)


@pytest.mark.parametrize("height", range(8, 17))
@pytest.mark.parametrize("slots", range(3, 7))
def test_combined_witness_is_constructible_at_joint_axis_values(height, slots):
    for spacing, color in ((3, 1), (5, 9)):
        grid = GEN.generate(41, 1, difficulty="medium", grid_h=height,
                            slot_count=slots, slot_spacing=spacing, fg_color=color)
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == {
            "grid_h": height, "slot_count": slots,
            "slot_spacing": spacing, "fg_color": color,
        }
        for name in ("population_not_first_active_row", "equal_counts_keep_source_order",
                     "marker_only_column_participates"):
            assert GEN.SEMANTIC_WITNESSES[name](grid), (height, slots, name)


@pytest.mark.parametrize("axis", ["grid_h", "slot_count", "slot_spacing", "fg_color"])
def test_none_override_preserves_the_scheduled_default(axis):
    for band in ("easy", "medium", "hard"):
        for index in range(4):
            assert GEN.generate(0, index, difficulty=band, **{axis: None}) == \
                GEN.generate(0, index, difficulty=band)


@pytest.mark.parametrize("axis,bad_value", [
    ("grid_h", 13.9), ("grid_h", "13"),
    ("slot_count", 5.9), ("slot_count", "5"),
    ("slot_spacing", 3.9), ("slot_spacing", "3"),
    ("fg_color", True), ("fg_color", 7.2), ("fg_color", "7"),
])
def test_exact_integer_axes_do_not_silently_coerce(axis, bad_value):
    with pytest.raises(TypeError, match="integer"):
        GEN.generate(1, 0, **{axis: bad_value})
