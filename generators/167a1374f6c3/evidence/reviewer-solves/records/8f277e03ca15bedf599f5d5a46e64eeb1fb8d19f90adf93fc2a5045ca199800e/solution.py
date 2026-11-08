"""Visible-example solution for Transform Timeline Gallery."""
from __future__ import annotations


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def _rotate_ccw(grid):
    return [list(row) for row in zip(*grid)][::-1]


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _crop_nonzero(grid):
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return [[0]]
    r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
    c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
    return [row[c1:c2 + 1] for row in grid[r1:r2 + 1]]


def _pack_top(states):
    height = max(len(state) for state in states)
    width = sum(len(state[0]) for state in states) + len(states) - 1
    out = [[0] * width for _ in range(height)]
    left = 0
    for state in states:
        for r, row in enumerate(state):
            out[r][left:left + len(row)] = row
        left += len(state[0]) + 1
    return out


def solve(grid):
    codes = []
    for value in grid[0]:
        if value == 0:
            break
        codes.append(value)

    state = _crop_nonzero(grid[1:])
    states = [state]
    transforms = {
        1: _rotate_cw,
        2: _rotate_180,
        3: _rotate_ccw,
        4: _flip_lr,
    }
    for code in codes:
        state = transforms[code](state)
        states.append(state)
    return _pack_top(states)
