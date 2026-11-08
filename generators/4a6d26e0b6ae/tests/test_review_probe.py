import importlib.util
from pathlib import Path


def load_probe():
    path = Path(__file__).resolve().parents[1] / "workspace/verify_distribution.py"
    spec = importlib.util.spec_from_file_location("bridge_probe", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def clean_grid():
    grid = [[0]*9 for _ in range(7)]
    grid[1][1] = grid[1][3] = 4
    grid[4][5] = grid[6][5] = 7
    return grid


def test_probe_accepts_valid_complete_input():
    result = load_probe().inspect_scene(clean_grid(), expected_count=2)
    assert result["issues"] == []
    assert result["active_gaps"] == 2


def test_probe_catches_overwritten_center():
    grid = clean_grid()
    grid[5][5] = 2
    result = load_probe().inspect_scene(grid, expected_count=2)
    assert result["lost_gap"]
    assert result["count_mismatch"]


def test_probe_detects_touching_full_spans_not_just_endpoints():
    grid = [[0]*9 for _ in range(7)]
    grid[1][1] = grid[1][3] = 4
    grid[2][2] = grid[4][2] = 7
    result = load_probe().inspect_scene(grid, expected_count=2)
    assert result["touching"]
    assert not result["lost_gap"]


def test_probe_catches_silent_underfill():
    result = load_probe().inspect_scene(clean_grid(), expected_count=3)
    assert result["count_mismatch"]
    assert not result["lost_gap"]
