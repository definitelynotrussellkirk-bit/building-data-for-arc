"""Visible-example solution for blind task 99e7ba062bec."""


def _crop_component(grid, cells, color):
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [
        [color if (r, c) in cells else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]


def _objects(grid):
    """Return monochromatic objects separated by empty columns.

    The examples place three possibly-disconnected silhouettes in horizontal
    slots.  Connectivity is therefore not the object boundary: a silhouette
    may contain gaps larger than one cell while still occupying one contiguous
    run of non-empty columns.
    """
    h = len(grid)
    w = len(grid[0]) if h else 0
    occupied = [any(grid[r][c] != 0 for r in range(h)) for c in range(w)]
    bands = []
    c = 0
    while c < w:
        if not occupied[c]:
            c += 1
            continue
        c0 = c
        while c + 1 < w and occupied[c + 1]:
            c += 1
        bands.append((c0, c))
        c += 1

    out = []
    for c0, c1 in bands:
        cells = {
            (r, c)
            for r in range(h)
            for c in range(c0, c1 + 1)
            if grid[r][c] != 0
        }
        colors = {grid[r][c] for r, c in cells}
        if len(colors) != 1:
            raise ValueError("expected each horizontal object slot to be monochromatic")
        color = next(iter(colors))
        out.append(
            {
                "color": color,
                "cells": cells,
                "min_r": min(r for r, _ in cells),
                "min_c": c0,
                "shape": _crop_component(grid, cells, color),
            }
        )
    return out


def _rot_cw(a):
    return [list(row) for row in zip(*a[::-1])]


def _flip_lr(a):
    return [row[::-1] for row in a]


def _transforms(a):
    """All eight square-grid symmetries, in a stable order."""
    r0 = [row[:] for row in a]
    r1 = _rot_cw(r0)
    r2 = _rot_cw(r1)
    r3 = _rot_cw(r2)
    f0 = _flip_lr(r0)
    f1 = _rot_cw(f0)
    f2 = _rot_cw(f1)
    f3 = _rot_cw(f2)
    return [r0, r1, r2, r3, f0, f1, f2, f3]


def _mask(a):
    return [[1 if value else 0 for value in row] for row in a]


def solve(grid):
    objects = _objects(grid)
    by_color = {}
    for obj in objects:
        by_color.setdefault(obj["color"], []).append(obj)

    repeated = [objs for objs in by_color.values() if len(objs) == 2]
    singletons = [objs[0] for objs in by_color.values() if len(objs) == 1]
    if len(repeated) != 1 or len(singletons) != 1:
        raise ValueError(
            "expected one colour with two objects and one colour with one object"
        )

    source, target = sorted(
        repeated[0], key=lambda obj: (obj["min_c"], obj["min_r"])
    )
    target_mask = _mask(target["shape"])
    transform_index = None
    for index, candidate in enumerate(_transforms(_mask(source["shape"]))):
        if candidate == target_mask:
            transform_index = index
            break
    if transform_index is None:
        raise ValueError("the two teaching objects are not related by a grid symmetry")

    return _transforms(singletons[0]["shape"])[transform_index]
