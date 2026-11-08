"""Independent Python probe for task 56bcb1d01e53.

This is reviewer tooling, not generator production code.  It mirrors the selected
Racket authority closely enough to validate canonical labels, generated inputs,
and named shortcut rivals without importing generator internals.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
from pathlib import Path
from typing import Iterable

DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIR8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)


def load_generator(path=None):
    source = Path(path) if path else Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("generator_under_test", source)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def background(grid):
    return Counter(value for row in grid for value in row).most_common(1)[0][0]


def objects8(grid, bg=None):
    if bg is None:
        bg = background(grid)
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != bg
    }
    objects = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        obj = []
        while stack:
            r, c = stack.pop()
            obj.append((r, c))
            for dr, dc in DIR8:
                point = (r + dr, c + dc)
                if point in remaining:
                    remaining.remove(point)
                    stack.append(point)
        objects.append(tuple(sorted(obj)))
    return tuple(objects)


def _bridged(first, second, grid, bg):
    second = set(second)
    for r, c in first:
        for dr, dc in DIR4:
            far = (r + 2 * dr, c + 2 * dc)
            mid = (r + dr, c + dc)
            if far in second and grid[mid[0]][mid[1]] == bg:
                return True
    return False


def merged_clusters(grid, bg=None):
    if bg is None:
        bg = background(grid)
    groups = [list(obj) for obj in objects8(grid, bg)]
    changed = True
    while changed:
        changed = False
        for i in range(len(groups)):
            partner = next(
                (j for j in range(i + 1, len(groups)) if _bridged(groups[i], groups[j], grid, bg)),
                None,
            )
            if partner is not None:
                groups[i] = groups[i] + groups[partner]
                del groups[partner]
                changed = True
                break
    return tuple(tuple(sorted(group)) for group in groups)


def cluster_facts(grid):
    bg = background(grid)
    raw = objects8(grid, bg)
    merged = merged_clusters(grid, bg)
    raw_sets = [set(obj) for obj in raw]
    facts = []
    for cluster in merged:
        cells = set(cluster)
        rs = [r for r, _ in cluster]
        cs = [c for _, c in cluster]
        facts.append(
            {
                "cells": tuple(cluster),
                "bbox": (min(rs), max(rs), min(cs), max(cs)),
                "height": max(rs) - min(rs) + 1,
                "width": max(cs) - min(cs) + 1,
                "raw_components": sum(bool(cells & obj) for obj in raw_sets),
                "colors": tuple(sorted({grid[r][c] for r, c in cluster})),
            }
        )
    return facts


def _round(value):
    # Python and Racket both use ties-to-even for exact .5 cases here.
    return int(round(value))


def _complete(
    grid,
    *,
    bridge=True,
    rectangular=True,
    even_squares=True,
    center_fill=True,
    diagonal_center=True,
    square_dihedral=False,
):
    h, w = len(grid), len(grid[0])
    bg = background(grid)
    output = deepcopy(grid)
    clusters = merged_clusters(grid, bg) if bridge else objects8(grid, bg)
    for cluster in clusters:
        rs = [r for r, _ in cluster]
        cs = [c for _, c in cluster]
        r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
        bh, bw = r2 - r1 + 1, c2 - c1 + 1
        square = bh == bw
        if square and not even_squares and bh % 2 == 0:
            continue
        cri = _round((r1 + r2) / 2.0)
        cci = _round((c1 + c2) / 2.0)
        if square or not rectangular:
            sr1, sr2, sc1, sc2 = r1, r2, c1, c2
        else:
            mdr = max(cri - r1, r2 - cri)
            mdc = max(cci - c1, c2 - cci)
            sr1, sr2 = max(0, cri - mdr), min(h - 1, cri + mdr)
            sc1, sc2 = max(0, cci - mdc), min(w - 1, cci + mdc)
        cr = (r1 + r2) / 2.0 if square else cri
        cc = (c1 + c2) / 2.0 if square else cci
        for r in range(sr1, sr2 + 1):
            for c in range(sc1, sc2 + 1):
                if output[r][c] != bg:
                    continue
                if square or not rectangular:
                    partners = (
                        (_round(cr + (c - cc)), _round(cc - (r - cr))),
                        (_round(cr - (r - cr)), _round(cc - (c - cc))),
                        (_round(cr - (c - cc)), _round(cc + (r - cr))),
                    )
                    if square and square_dihedral:
                        partners += (
                            (_round(cr - (r - cr)), _round(cc + (c - cc))),
                            (_round(cr + (r - cr)), _round(cc - (c - cc))),
                            (_round(cr + (c - cc)), _round(cc + (r - cr))),
                            (_round(cr - (c - cc)), _round(cc - (r - cr))),
                        )
                else:
                    partners = (
                        (r, _round(2 * cc - c)),
                        (_round(2 * cr - r), c),
                        (_round(2 * cr - r), _round(2 * cc - c)),
                    )
                value = next(
                    (
                        grid[rr][cc2]
                        for rr, cc2 in partners
                        if 0 <= rr < h and 0 <= cc2 < w and grid[rr][cc2] != bg
                    ),
                    None,
                )
                if value is not None:
                    output[r][c] = value
        if center_fill and square and bh % 2 == 1 and output[cri][cci] == bg:
            fill = grid[cluster[0][0]][cluster[0][1]]

            def painted(rr, cc2):
                return (
                    sr1 <= rr <= sr2
                    and sc1 <= cc2 <= sc2
                    and output[rr][cc2] == fill
                )

            cardinal = (
                cri > sr1
                and cri < sr2
                and cci > sc1
                and cci < sc2
                and painted(cri, cci - 1)
                and painted(cri, cci + 1)
                and painted(cri - 1, cci)
                and painted(cri + 1, cci)
            )
            diagonal = (
                diagonal_center
                and bh >= 7
                and bw >= 7
                and painted(cri - 1, cci - 1)
                and painted(cri - 1, cci + 1)
                and painted(cri + 1, cci - 1)
                and painted(cri + 1, cci + 1)
                and painted(sr1, cci)
                and painted(sr2, cci)
                and painted(cri, sc1)
                and painted(cri, sc2)
            )
            if cardinal or diagonal:
                output[cri][cci] = fill
    return output


def intended_output(grid):
    return _complete(grid)


def no_bridge_merge(grid):
    return _complete(grid, bridge=False)


def square_rotation_only(grid):
    return _complete(grid, rectangular=False)


def odd_squares_only(grid):
    return _complete(grid, even_squares=False)


def no_center_fill(grid):
    return _complete(grid, center_fill=False)


def cardinal_center_only(grid):
    return _complete(grid, diagonal_center=False)


def square_dihedral_closure(grid):
    return _complete(grid, square_dihedral=True)


def changed_cells(before, after):
    return [
        (r, c, before[r][c], after[r][c])
        for r in range(len(before))
        for c in range(len(before[0]))
        if before[r][c] != after[r][c]
    ]


def witness_flags(grid):
    bg = background(grid)
    flags = {
        "bridge_merge": False,
        "rectangular_expansion": False,
        "even_square": False,
        "center_completion": False,
        "diagonal_center_completion": False,
        "rotation_not_dihedral": False,
    }
    for fact in cluster_facts(grid):
        r1, r2, c1, c2 = fact["bbox"]
        flags["bridge_merge"] |= fact["raw_components"] > 1
        flags["rectangular_expansion"] |= fact["height"] != fact["width"]
        flags["even_square"] |= fact["height"] == fact["width"] and fact["height"] % 2 == 0
        if fact["height"] == fact["width"] and fact["height"] % 2 == 1:
            cr, cc = (r1 + r2) // 2, (c1 + c2) // 2
            color = fact["colors"][0]
            if grid[cr][cc] == bg and all(
                grid[cr + dr][cc + dc] == color for dr, dc in DIR4
            ):
                flags["center_completion"] = True
    selected = intended_output(grid)
    flags["diagonal_center_completion"] = selected != cardinal_center_only(grid)
    flags["rotation_not_dihedral"] = selected != square_dihedral_closure(grid)
    return flags


def pair(grid):
    return {"input": deepcopy(grid), "output": intended_output(grid)}
