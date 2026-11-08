"""Constructive inputs shared by both opt-in frame-completion settings.

These scenes extend only the parametric grammar with preexisting interior 7s.
The production generator and its empty-interior validator are unchanged.
"""
from __future__ import annotations

import random


PROFILES = ("bridge", "tie", "small", "transfer", "dense")
FRAME_COLORS = (1, 4, 5, 6, 8, 9)


def _motif(rng, tie):
    a, b = rng.randint(1, 3), rng.randint(1, 3)
    if tie:
        height, width = a + 11, max(b + 9, 14)
        rows, cols = {a, a + 2, a + 5}, {b, b + 4, b + 7}
        anchors = {(r, c) for r in (a, a + 2) for c in range(b + 1, b + 4)}
        anchors.update({(a + 1, b), (a + 1, b + 4), (a + 3, b + 5)})
        anchors.update((a + 7, c) for c in range(1, 13))
        anchors.update((a + 9, c) for c in range(1, 10))
        # Completed twelve-cell ring and original twelve-cell chain tie.
        # The nine-cell loser exceeds bridge's eight-cell winner: retaining
        # every component above a fixed size cannot fit both demonstrations.
        return height, width, rows, cols, anchors
    height, width = a + 9, max(b + 7, 8)
    rows, cols = {a, a + 2, a + 5}, {b, b + 2, b + 5}
    anchors = {(a, b + 1), (a + 1, b), (a + 1, b + 2), (a + 2, b + 1)}
    # This seed touches a completed corner only diagonally, so both teaching
    # profiles distinguish four-neighbor from eight-neighbor connectivity.
    anchors.add((a + 3, b + 3))
    # The original longest object loses after completion.
    anchors.update((a + 7, c) for c in range(1, 6))
    return height, width, rows, cols, anchors


def _transfer(rng):
    height, width = rng.randint(9, 20), rng.randint(10, 23)
    rows = set(rng.sample(range(1, height - 1), rng.randint(2, min(9, height - 2))))
    cols = set(rng.sample(range(1, width - 1), rng.randint(2, min(10, width - 2))))
    # A small bent scaffold plus scattered anchors, independently of markers.
    r, c = rng.randint(1, height - 4), rng.randint(1, width - 4)
    anchors = {(r, c), (r + 1, c), (r + 2, c), (r + 2, c + 1)}
    available = [(rr, cc) for rr in range(1, height - 1) for cc in range(1, width - 1)]
    anchors.update(rng.sample(available, rng.randint(4, min(24, len(available)))))
    # Guarantee some new completion cells even on dense random draws.
    anchors.discard((min(rows), min(cols)))
    return height, width, rows, cols, anchors


def _dense(rng):
    row_runs = [list(range(start, start + rng.randint(3, 6))) for start in (1, 8, 15, 22)]
    col_runs = [list(range(start, start + rng.randint(3, 6))) for start in (1, 8, 15, 22)]
    rows = {r for run in row_runs for r in run}
    cols = {c for run in col_runs for c in run}
    # Two short, separated horizontal bridges join completed blocks; the
    # remaining row bands still form distinct substantial components.
    first_bridge_row = rng.choice(row_runs[0])
    anchors = {(first_bridge_row, c) for c in range(col_runs[0][-1] + 1, col_runs[1][0])}
    bridge_row = rng.choice(row_runs[2])
    anchors.update((bridge_row, c) for c in range(col_runs[2][-1] + 1, col_runs[3][0]))
    return 30, 30, rows, cols, anchors


def sample_scene(seed: int, profile: str):
    """Return one deterministic ARC grid; no labels or settings enter sampling."""
    if profile not in PROFILES:
        raise ValueError(f"unknown scene profile {profile!r}; expected one of {PROFILES}")
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    rng = random.Random(seed)
    if profile in ("bridge", "tie"):
        height, width, rows, cols, anchors = _motif(rng, profile == "tie")
    elif profile == "small":
        height, width, rows, cols, anchors = 5, 6, {1, 3}, {1, 3}, {(1, 2), (2, 4)}
    elif profile == "transfer":
        height, width, rows, cols, anchors = _transfer(rng)
    else:
        height, width, rows, cols, anchors = _dense(rng)

    # Transform the scene specification rather than rotating marker colors:
    # row selectors always remain on the left, column selectors on the top.
    if rng.getrandbits(1):
        rows = {height - 1 - r for r in rows}
        anchors = {(height - 1 - r, c) for r, c in anchors}
    if rng.getrandbits(1):
        cols = {width - 1 - c for c in cols}
        anchors = {(r, width - 1 - c) for r, c in anchors}
    if profile != "small" and rng.getrandbits(1):
        height, width = width, height
        rows, cols = cols, rows
        anchors = {(c, r) for r, c in anchors}

    if profile in ("small", "dense"):
        top = left = bottom_pad = right_pad = 0
    else:
        top, left, bottom_pad, right_pad = (rng.randint(0, 2) for _ in range(4))
    grid = [[0] * (left + width + right_pad) for _ in range(top + height + bottom_pad)]
    color = rng.choice(FRAME_COLORS)
    for c in range(width):
        grid[top][left + c] = color
        grid[top + height - 1][left + c] = color
    for r in range(height):
        grid[top + r][left] = color
        grid[top + r][left + width - 1] = color
    for r in rows:
        grid[top + r][left] = 2
    for c in cols:
        grid[top][left + c] = 3
    for r, c in anchors:
        grid[top + r][left + c] = 7
    for c in rng.sample(range(1, width - 1), rng.randint(1, min(4, width - 2))):
        grid[top + height - 1][left + c] = 2
    for r in rng.sample(range(1, height - 1), rng.randint(1, min(4, height - 2))):
        grid[top + r][left + width - 1] = 3
    return grid
