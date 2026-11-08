"""Unit tests for the independent task-local, Racket-backed coverage gate."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def load_gate():
    path = Path(__file__).with_name('alignment_gate.py')
    assert path.is_file(), 'The executable alignment coverage gate is missing'
    spec = importlib.util.spec_from_file_location('alignment_gate_under_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scene():
    grid = [[0] * 9 for _ in range(8)]
    for r in range(3, 6):
        for c in range(3, 6):
            grid[r][c] = 3
    grid[0][4] = 2
    grid[4][0] = 1
    grid[7][8] = 4  # a diagonal decoy
    return grid


def expected():
    grid = scene()
    grid[1][4] = grid[2][4] = 2
    grid[4][1] = grid[4][2] = 1
    return grid


def test_dihedral_orbit_is_eight_fresh_rectangular_grids():
    gate = load_gate()
    grid = scene()
    images = gate.dihedral_images(grid)
    assert len(images) == 8
    assert len({tuple(map(tuple, image)) for _, image in images}) == 8
    assert images[0] == ('identity', grid)
    for _, image in images:
        assert sorted(value for row in image for value in row) == sorted(value for row in grid for value in row)
        assert all(len(row) == len(image[0]) for row in image)
        assert image is not grid
        assert all(row is not source for row in image for source in grid)
    images[0][1][0][0] = 9
    assert grid[0][0] == 0


def test_independent_rivals_remove_only_the_selected_interior_axis():
    gate = load_gate()
    grid = scene()
    horizontal = gate.axis_boundary_rival(grid, 'horizontal')
    vertical = gate.axis_boundary_rival(grid, 'vertical')
    assert horizontal[1][4] == 2
    assert horizontal[4][1] == 0
    assert vertical[1][4] == 0
    assert vertical[4][1] == 1
    assert horizontal[7][8] == vertical[7][8] == 4
    assert grid == scene()
    with pytest.raises(ValueError, match='axis'):
        gate.axis_boundary_rival(grid, 'diagonal')


def test_cell_observations_detect_both_axes_and_reference_disagreement():
    gate = load_gate()
    result = gate.inspect_case(scene(), expected())
    assert result['interior_axes'] == ['horizontal', 'vertical']
    assert result['rival_agrees'] == {'horizontal_boundary_only': False, 'vertical_boundary_only': False}
    assert result['changed_cells'] == 4
    assert result['changed_colored_cells'] == 0


def test_support_gate_catches_one_axis_hole_without_requiring_all_pairs_to_differ():
    gate = load_gate()
    good = [{'difficulty': 'easy', 'sample_index': i,
             'interior_axes': ['horizontal', 'vertical'] if i == 1 else [],
             'rival_agrees': {'horizontal_boundary_only': i != 1,
                             'vertical_boundary_only': i != 1}} for i in range(4)]
    assert gate.support_failures(good, ('easy',)) == []
    bad = [{**row, 'interior_axes': ['horizontal'],
            'rival_agrees': {'horizontal_boundary_only': False,
                            'vertical_boundary_only': True}} for row in good]
    issues = gate.support_failures(bad, ('easy',))
    assert any('vertical' in issue for issue in issues)
    assert gate.support_failures([], ('easy',))


def test_report_html_escapes_diagnostics():
    gate = load_gate()
    html = gate.render_html({'task_id': '<script>bad</script>', 'status': 'FAIL',
                             'failures': ['<img src=x>'], 'bands': {}, 'witnesses': []})
    assert '<script>bad</script>' not in html
    assert '&lt;script&gt;' in html
    assert '<img src=x>' not in html
    assert '&lt;img src=x&gt;' in html
