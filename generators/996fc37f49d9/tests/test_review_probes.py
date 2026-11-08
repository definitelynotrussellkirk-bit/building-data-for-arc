"""Regression cases for the review tools; no Racket dependency for unit tests."""
import importlib.util
from pathlib import Path


def _load(name):
    path = Path(__file__).resolve().parents[1] / "workspace" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_translation_reference_marker_inside_crop_is_copied():
    """Racket copies the entire nonzero bbox, not only the selection cells."""
    audit = _load("audit_findings")
    grid = [[0] * 11 for _ in range(9)]
    grid[1][8], grid[3][5] = 2, 3
    for r, c in ((1, 9), (2, 8), (2, 9), (2, 10)):
        grid[r][c] = 4
    result = audit.translation_expected(grid)
    assert result[3][5] == 2, "reference marker inside template bbox must overwrite target"
    assert result[3][6] == 4
    assert result[4][5:8] == [4, 4, 4]
    assert grid[3][5] == 3, "oracle must not mutate its input"


def test_translation_partial_clipping_preserves_original():
    audit = _load("audit_findings")
    grid = [[0] * 7 for _ in range(5)]
    grid[0][0], grid[1][1] = 2, 3
    grid[3][5], grid[4][5] = 4, 6
    result = audit.translation_expected(grid)
    assert result[4][6] == 4
    assert result[4][5] == 6
    assert result[3][5] == 4


def test_maze_disconnected_cells_stay_zero_and_markers_are_preserved():
    audit = _load("audit_findings")
    grid = [[1, 0, 8, 0], [2, 2, 8, 0], [0, 0, 8, 0]]
    expected = [[1, 2, 8, 0], [2, 2, 8, 0], [1, 2, 8, 0]]
    assert audit.bfs_expected(grid) == expected
