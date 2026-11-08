"""Regression tests for the task-local source-bound census."""
import importlib.util
from pathlib import Path


PROBE = Path(__file__).resolve().parents[1] / "workspace" / "review_probe.py"
spec = importlib.util.spec_from_file_location("review_probe_under_test", PROBE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def test_inspect_grid_selects_unique_largest_green_reference():
    grid = [[0] * 10 for _ in range(8)]
    grid[0][8] = 3
    grid[1][1] = grid[2][1] = grid[2][2] = 3
    grid[5][5] = 1

    metrics, detail = probe.inspect_grid(grid)

    assert detail["shape"] == [(0, 0), (1, 0), (1, 1)]
    assert detail["reference"] == [(1, 1), (2, 1), (2, 2)]
    assert detail["green_distractors"] == [[(0, 8)]]
    assert metrics["green_component_count"] == 2
    assert metrics["multiple_green_components"] is True
    assert metrics["ambiguous_green_reference"] is False
    assert metrics["reference_overlap"] is False
