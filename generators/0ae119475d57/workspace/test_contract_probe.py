"""Regression tests for the independent structural part of the probe."""
from contract_probe import structural_issues


def scene():
    grid = [[0] * 4 for _ in range(11)]
    grid[5] = [5] * 4
    grid[0][0] = grid[0][1] = 1
    grid[6][0] = grid[6][2] = 2
    return grid


def test_accepts_unambiguous_valid_scene():
    assert structural_issues(scene()) == []


def test_finds_false_separator_even_if_module_validator_would_accept():
    grid = scene()
    grid[7] = [2] * 4
    assert any('separator' in reason for reason in structural_issues(grid))


def test_rejects_ragged_or_incorrect_height_without_crashing():
    assert structural_issues([[0], [0, 1]])
    assert structural_issues([[0] * 4 for _ in range(10)])


def test_rejects_disguised_boolean_colors():
    grid = scene()
    grid[0][0] = True
    assert structural_issues(grid)
