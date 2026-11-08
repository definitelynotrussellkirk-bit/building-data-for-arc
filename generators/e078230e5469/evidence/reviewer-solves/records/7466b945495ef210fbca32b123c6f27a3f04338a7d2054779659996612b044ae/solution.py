"""Visible-example solver for the three-panel transform analogy."""
from __future__ import annotations


def _rot90(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _transform(grid, name):
    if name == "id":
        return [list(row) for row in grid]
    if name == "rot90":
        return _rot90(grid)
    if name == "rot180":
        return _rot90(_rot90(grid))
    if name == "rot270":
        return _rot90(_rot90(_rot90(grid)))
    if name == "flip_h":
        return [list(reversed(row)) for row in grid]
    if name == "flip_v":
        return [list(row) for row in reversed(grid)]
    if name == "transpose":
        return [list(row) for row in zip(*grid)]
    if name == "anti":
        return _transform(_transform(grid, "transpose"), "rot180")
    raise ValueError(name)


def solve(grid):
    """Infer the transform from panel 1 -> panel 2, then apply it to panel 3."""
    size = len(grid)
    if not grid or any(len(row) != 3 * size + 2 for row in grid):
        raise ValueError("expected three square panels separated by two columns")
    first = [row[:size] for row in grid]
    second = [row[size + 1:2 * size + 1] for row in grid]
    third = [row[2 * size + 2:] for row in grid]
    for name in ("rot90", "rot180", "rot270", "flip_h", "flip_v", "transpose", "anti", "id"):
        if _transform(first, name) == second:
            return _transform(third, name)
    raise ValueError("no dihedral transform maps the first panel to the second")
