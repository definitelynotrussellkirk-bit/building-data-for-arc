"""Visible-example solution for the exposed 155cf6b30713 episode."""
from __future__ import annotations


def _transform(grid, code):
    h = len(grid)
    w = len(grid[0])
    if code == "r1":
        return [[grid[h - 1 - r][c] for r in range(h)] for c in range(w)]
    if code == "r2":
        return [[grid[h - 1 - r][w - 1 - c] for c in range(w)] for r in range(h)]
    if code == "r3":
        return [[grid[r][w - 1 - c] for r in range(h)] for c in range(w)]
    if code == "fh":
        return [row[::-1] for row in grid]
    if code == "fv":
        return [row[:] for row in grid[::-1]]
    if code == "tr":
        return [[grid[r][c] for r in range(h)] for c in range(w)]
    if code == "atr":
        return [[grid[h - 1 - c][w - 1 - r] for c in range(h)] for r in range(w)]
    raise ValueError(code)


def _support(grid):
    return [[value != 0 for value in row] for row in grid]


def _split(grid):
    h = len(grid)
    w = len(grid[0])
    separators = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(separators) != 2:
        raise ValueError(f"expected two full color-5 separators, got {separators}")
    starts = [0, separators[0] + 1, separators[1] + 1]
    ends = [separators[0], separators[1], w]
    panels = [[row[start:end] for row in grid] for start, end in zip(starts, ends)]
    if any(len(panel) != len(panel[0]) for panel in panels):
        raise ValueError("expected three square panels")
    return panels


def solve(grid):
    example_in, example_out, query = _split(grid)
    for code in ("r1", "r2", "r3", "fh", "fv", "tr", "atr"):
        transformed = _transform(example_in, code)
        if _support(transformed) != _support(example_out):
            continue
        mapping = {}
        valid = True
        for source_row, target_row in zip(transformed, example_out):
            for source, target in zip(source_row, target_row):
                if source == 0:
                    if target != 0:
                        valid = False
                        break
                    continue
                if target == 0 or (source in mapping and mapping[source] != target):
                    valid = False
                    break
                mapping[source] = target
            if not valid:
                break
        if not valid:
            continue
        transformed_query = _transform(query, code)
        return [
            [0 if value == 0 else mapping.get(value, value) for value in row]
            for row in transformed_query
        ]
    raise ValueError("no consistent non-identity panel transform and color map")
