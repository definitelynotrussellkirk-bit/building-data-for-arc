"""Exact, independent fixtures keep the reusable audit's assumptions testable."""
import pytest
from topology_probe import (breach, eight_neighbors, fixtures, holes, oracle,
                            rectangular_only, bounding_boxes, shape_key)


@pytest.mark.parametrize('name,area', [('diagonal_contact',1), ('concave_L',3),
    ('closed_frame',1),('one_cell_breach',0),('border_zero_not_hole',0),
    ('all_zero',0),('all_wall',0),('wall_island',8),('three_holes',3)])
def test_fixture_exact_area(name,area):
    assert sum(map(sum,oracle(fixtures()[name]))) == area * 8


def test_concavity_separates_two_rectangular_shortcuts():
    grid = fixtures()['concave_L']
    assert rectangular_only(grid) != oracle(grid)
    assert bounding_boxes(grid) != oracle(grid)


def test_diagonal_contact_is_not_a_cardinal_escape():
    grid = fixtures()['diagonal_contact']
    assert sum(map(sum,oracle(grid))) == 8
    assert sum(map(sum,eight_neighbors(grid))) == 0


def test_one_wall_breach_removes_hole():
    grid = fixtures()['closed_frame']
    assert holes(breach(grid)) == []


def test_shape_key_ignores_orientation_and_translation():
    a = {(0,0),(1,0),(1,1)}
    b = {(10,20),(10,21),(11,20)}
    assert shape_key(a) == shape_key(b)


@pytest.mark.parametrize('bad', [[], [[]], [[0],[0,0]]])
def test_invalid_grid_shape_fails_loudly(bad):
    with pytest.raises(ValueError):
        oracle(bad)
