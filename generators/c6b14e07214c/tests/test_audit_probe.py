"""Tests for the read-only audit's deliberately restricted candidate rules."""
import importlib.util
from pathlib import Path


def load():
    path = Path(__file__).parents[1] / 'workspace/audit_assigned.py'
    assert path.is_file(), 'the audit reproducer must be retained'
    spec = importlib.util.spec_from_file_location('audit_probe', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_projection_rival_handles_two_separated_column_runs():
    mod = load()
    grid = [[0] * 10 for _ in range(9)]
    for r in range(3):
        for c in range(3): grid[r][c] = 4
    for r in range(5, 9):
        for c in range(5, 9): grid[r][c] = 4
    out = mod.column_projection_rival(grid)
    assert out[1][1] == 1 and out[6][6] == 2
    assert grid[1][1] == 4 and out[0][0] == 4


def test_projection_shortcut_is_explicitly_incomplete_when_spans_overlap():
    mod = load()
    grid = mod.overlapping_rectangles()
    assert mod.column_projection_rival(grid) == grid
    assert len(mod.rect_boxes(grid)) == 2


def test_clamped_cycle_probe_is_deliberately_not_modular():
    mod = load()
    grid = mod.gh_one_two_sources()
    out = mod.clamped_cycle_rival(grid)
    assert [row[3] for row in out] == [2, 8, 8, 8, 8, 8]
    assert grid[2][3] == 0
