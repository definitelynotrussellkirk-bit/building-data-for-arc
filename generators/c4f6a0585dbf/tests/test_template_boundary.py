"""Template-boundary regressions ported from review-4770deb62c048f82."""
from reviewer_support import find_root, load_selected_generator
gen, _, _ = load_selected_generator("c4f6a0585dbf", root=find_root(__file__))

def test_self_check_rejects_non_full_grid_without_literal_color_four_ports():
    grid = [[0 for _ in range(23)] for _ in range(23)]
    for row in range(10, 13):
        for col in range(10, 14):
            grid[row][col] = 1

    errors = gen.self_check(grid)

    assert any("missing literal color-4 ports" in error for error in errors), errors

def test_no_targets_degenerate_still_requires_two_or_three_ports():
    grid = gen.generate(0, 0, texture="no_targets")
    grid[11][12] = 1

    errors = gen.self_check(grid)

    assert any("2..3 ports" in error for error in errors), errors

def test_self_check_rejects_port_on_template_boundary():
    grid = gen.generate(0, 0, texture="no_targets")
    grid[11][11] = 1
    grid[10][11] = 4

    errors = gen.self_check(grid)

    assert any("strictly interior" in error for error in errors), errors

def test_self_check_rejects_non_port_hole_inside_template_bbox():
    grid = [[0 for _ in range(23)] for _ in range(23)]
    for row in range(9, 14):
        for col in range(9, 14):
            grid[row][col] = 1
    grid[10][10] = 4
    grid[10][12] = 4
    grid[12][11] = 0

    errors = gen.self_check(grid)

    assert any("non-port holes" in error for error in errors), errors
