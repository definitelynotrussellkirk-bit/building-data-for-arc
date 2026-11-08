from __future__ import annotations

import importlib.util
from pathlib import Path


_GENERATOR = Path(__file__).resolve().parents[1] / "generator.py"
_SPEC = importlib.util.spec_from_file_location("local_e2bc70324918_generator", _GENERATOR)
assert _SPEC is not None and _SPEC.loader is not None
gen = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(gen)


def _line_and_glyphs(grid):
    bg = 7
    comps = gen._components8(grid, bg)
    line_candidates = [
        (color, cells)
        for color, cells in comps
        if len(cells) > 1 and gen._endpoint_count(cells) == 2
    ]
    assert len(line_candidates) == 1
    line_color, line_cells = line_candidates[0]
    glyphs = [cells for color, cells in comps if color != line_color]
    return line_cells, glyphs


def _orientation(cells):
    rows = {row for row, _ in cells}
    cols = {col for _, col in cells}
    if len(rows) == 1:
        return "horizontal"
    if len(cols) == 1:
        return "vertical"
    ordered = sorted(cells)
    deltas = {(r2 - r1, c2 - c1) for (r1, c1), (r2, c2) in zip(ordered, ordered[1:])}
    if deltas == {(1, 1)}:
        return "diagonal"
    if deltas == {(1, -1)}:
        return "anti-diagonal"
    raise AssertionError(f"not a straight supported line: {cells}")


def _stamp_shape(grid):
    _, glyphs = _line_and_glyphs(grid)
    shapes = {gen._norm(cells) for cells in glyphs}
    assert len(shapes) == 1
    return next(iter(shapes))


def test_exact_orientation_and_glyph_count_overrides_are_observable():
    for orientation in gen.ORIENTATIONS:
        for count in (2, 4):
            grid = gen.generate(
                17,
                0,
                difficulty="medium",
                grid_h=16,
                grid_w=16,
                line_orientation=orientation,
                n_glyphs=count,
            )
            line, glyphs = _line_and_glyphs(grid)
            assert _orientation(line) == orientation
            assert len(glyphs) == count
            assert gen.self_check(grid, difficulty="medium") == []


def test_canonical_x_and_five_row_templates_are_selectable():
    expected = {
        "x": ((0, 0), (0, 2), (1, 1), (2, 0), (2, 2)),
        "i5": (
            (0, 0), (0, 1), (0, 2),
            (1, 1), (2, 1), (3, 1),
            (4, 0), (4, 1), (4, 2),
        ),
    }
    for name, shape in expected.items():
        grid = gen.generate(
            29,
            1,
            difficulty="hard",
            grid_h=18,
            grid_w=18,
            glyph_kind=name,
            line_orientation="horizontal",
            n_glyphs=3,
        )
        assert _stamp_shape(grid) == shape
        assert gen.self_check(grid, difficulty="hard") == []


def test_self_check_rejects_endpoint_stamp_clipping_for_tall_glyph():
    height = width = 15
    grid = [[7 for _ in range(width)] for _ in range(height)]
    i5 = (
        (-2, -1), (-2, 0), (-2, 1),
        (-1, 0), (0, 0), (1, 0),
        (2, -1), (2, 0), (2, 1),
    )
    for center_r, center_c in ((4, 4), (8, 10)):
        for dr, dc in i5:
            grid[center_r + dr][center_c + dc] = 2
    for col in range(3, 8):
        grid[13][col] = 1

    errors = gen.self_check(grid)
    assert any("clip" in error for error in errors), errors


def test_no_line_degenerate_returns_plus_glyph_without_crashing():
    grid = gen.generate(5, 0, texture="no_line")
    assert len(grid) == len(grid[0]) == 13
    cells = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    }
    assert cells == {(5, 5), (4, 5), (6, 5), (5, 4), (5, 6)}
    assert all(value in {2, 7} for row in grid for value in row)
