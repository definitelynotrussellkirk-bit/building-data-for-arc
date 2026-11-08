"""Canonical reflection and a proposed, state-dependent component selection."""
from pathlib import Path

SELECTIONS = ("all", "largest", "smallest")


def settings_value(settings):
    if type(settings) is not dict or set(settings) != {"selection"}:
        raise ValueError("settings must contain exactly selection")
    value = settings["selection"]
    if type(value) is not str or value not in SELECTIONS:
        raise ValueError("selection must be all, largest, or smallest")
    return value


def integer(value, name, lo, hi):
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not lo <= value <= hi:
        raise ValueError(f"{name} must be in {lo}..{hi}")
    return value


def validate_grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must be a square list with side 1..30")
    n = len(grid)
    if any(type(row) is not list or len(row) != n for row in grid):
        raise ValueError("grid rows must be equal square lists")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("cells must be exact integer colors 0..9")
    if not any(v == 0 for row in grid for v in row):
        raise ValueError("background 0 must be present")
    if any(grid[r][c] and grid[c][r] and grid[r][c] != grid[c][r]
           for r in range(n) for c in range(r + 1, n)):
        raise ValueError("occupied mirror partners must have the same color")
    if not any(bool(grid[r][c]) != bool(grid[c][r])
               for r in range(n) for c in range(r + 1, n)):
        raise ValueError("at least one off-diagonal partner must need completion")


def complete(grid):
    """Exact overlay/transpose formula; callers validate the admitted domain."""
    return [[grid[c][r] or grid[r][c] for c in range(len(grid))]
            for r in range(len(grid))]


def components(grid, connectivity=4, multicolor=False):
    """Row-major components; the intended rule uses same-color four-neighbors."""
    h, w = len(grid), len(grid[0])
    steps = ((-1,0),(0,-1),(0,1),(1,0))
    if connectivity == 8:
        steps += ((-1,-1),(-1,1),(1,-1),(1,1))
    elif connectivity != 4:
        raise ValueError("connectivity must be 4 or 8")
    seen, result = set(), []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if not color or (r,c) in seen:
                continue
            seen.add((r,c))
            todo, cells = [(r,c)], []
            while todo:
                x,y = todo.pop()
                cells.append((x,y))
                for dr,dc in steps:
                    nr,nc = x+dr,y+dc
                    if (0 <= nr < h and 0 <= nc < w and (nr,nc) not in seen
                            and grid[nr][nc] and (multicolor or grid[nr][nc] == color)):
                        seen.add((nr,nc))
                        todo.append((nr,nc))
            cells.sort()
            rs, cs = zip(*cells)
            result.append({"color": color, "cells": cells, "size": len(cells),
                           "bbox": [min(rs), min(cs), max(rs), max(cs)]})
    return result


def solve(grid, settings):
    selection = settings_value(settings)
    validate_grid(grid)
    completed = complete(grid)
    if selection == "all":
        return completed
    parts = components(completed)
    target = (max if selection == "largest" else min)(p["size"] for p in parts)
    out = [[0] * len(grid) for _ in grid]
    for part in parts:
        if part["size"] == target:
            for r,c in part["cells"]:
                out[r][c] = completed[r][c]
    return out


def program(settings):
    selection = settings_value(settings)
    if selection == "all":
        return Path(__file__).with_name("canonical.rkt").read_bytes().decode("utf-8")
    extreme = "max" if selection == "largest" else "min"
    return f"""(rule!
 (lambda (g)
  (let* ([completed (overlay g (transpose g))]
         [parts (objects completed 0)]
         [blank (empty-grid (rows completed) (cols completed) 0)])
    (if (empty? parts)
        blank
        (let ([target (apply {extreme} (map obj-size parts))])
          (for/fold ([out blank]) ([part (in-list parts)])
            (if (= (obj-size part) target)
                (paint-cells out (obj-cells part) (obj-color part))
                out)))))))"""
