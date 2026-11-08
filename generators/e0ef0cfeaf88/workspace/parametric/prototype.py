"""Matched-input edge-versus-two-step diagonal ray episodes.

The source puzzle supplies a solid monochrome 2x2 body and one or more pixels at
its diagonal corners.  The episode-fixed parameter decides whether each tail
continues to the grid edge (canonical) or for exactly two additional cells.
Inputs are sampled independently of that setting, so demonstrations must teach
extent from outputs rather than reveal it through scene statistics.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
TASK_ID = "e0ef0cfeaf88"
SETTINGS = ({"extent": "edge"}, {"extent": "two_steps"})
_TAIL_OFFSETS = ((-1, -1), (-1, 2), (2, -1), (2, 2))

# h, w, active tail indices, target body-row fraction, target body-col fraction.
# Every body has at least three free cells beyond each possible tail, making the
# two candidate rules behaviorally distinct on every retained pair.
_DEMOS = (
    (10, 10, (0,), 0.50, 0.50),
    (12, 14, (3,), 0.42, 0.58),
    (14, 16, (1, 2), 0.58, 0.42),
    (18, 20, (0, 2, 3), 0.36, 0.64),
    (22, 24, (0, 1, 2, 3), 0.62, 0.38),
    (26, 28, (0, 1, 3), 0.50, 0.50),
)
_QUERIES = (
    (11, 13, (2,), 0.55, 0.45),
    (17, 19, (0, 3), 0.40, 0.60),
    (24, 27, (0, 1, 2), 0.60, 0.40),
    (30, 30, (0, 1, 2, 3), 0.50, 0.50),
)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(settings):
    if (
        type(settings) is not dict
        or set(settings) != {"extent"}
        or type(settings["extent"]) is not str
        or settings["extent"] not in ("edge", "two_steps")
    ):
        raise ValueError("settings must be exactly {'extent': 'edge'|'two_steps'}")
    return settings["extent"]


def program(settings):
    extent = _setting(settings)
    return (HERE / ("canonical.rkt" if extent == "edge" else "two_steps.rkt")).read_text()


def _rng(seed, split, index):
    raw = json.dumps([TASK_ID, seed, split, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _body_top_left(height, width, target_r, target_c, rng):
    rows = range(4, height - 5)
    cols = range(4, width - 5)
    candidates = []
    for row in rows:
        for col in cols:
            score = (
                (row + 0.5 - target_r * (height - 1)) ** 2
                + (col + 0.5 - target_c * (width - 1)) ** 2
            )
            candidates.append((score, rng.random(), row, col))
    if not candidates:
        raise ValueError("grid is too small for the required ray margin")
    _, _, row, col = min(candidates)
    return row, col


def sample_input(seed, index, *, split):
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in ("train", "test"):
        raise ValueError("split must be train or test")
    specs = _DEMOS if split == "train" else _QUERIES
    _integer(index, 0, len(specs) - 1, "index")
    height, width, tail_indices, target_r, target_c = specs[index]
    rng = _rng(seed, split, index)
    body_r, body_c = _body_top_left(height, width, target_r, target_c, rng)
    color = 1 + rng.randrange(9)
    grid = [[0] * width for _ in range(height)]
    for dr in (0, 1):
        for dc in (0, 1):
            grid[body_r + dr][body_c + dc] = color
    for tail_index in tail_indices:
        dr, dc = _TAIL_OFFSETS[tail_index]
        grid[body_r + dr][body_c + dc] = color
    return grid


def _analyze(grid):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    cells = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    }
    colors = {grid[row][col] for row, col in cells}
    if len(colors) != 1:
        raise ValueError("scene must have one foreground color")
    bodies = []
    for row, col in sorted(cells):
        body = {(row, col), (row + 1, col), (row, col + 1), (row + 1, col + 1)}
        if body <= cells:
            bodies.append((row, col, body))
    if len(bodies) != 1:
        raise ValueError("scene must have exactly one 2x2 body")
    body_r, body_c, body = bodies[0]
    tails = cells - body
    expected = {(body_r + dr, body_c + dc) for dr, dc in _TAIL_OFFSETS}
    if not tails or not tails <= expected:
        raise ValueError("tails must occupy diagonal corner positions")
    return body_r, body_c, tails, next(iter(colors))


def claimed_output(grid, settings):
    extent = _setting(settings)
    body_r, body_c, tails, color = _analyze(grid)
    height, width = len(grid), len(grid[0])
    output = deepcopy(grid)
    center_r2 = 2 * body_r + 1
    center_c2 = 2 * body_c + 1
    for tail_r, tail_c in tails:
        dr = -1 if 2 * tail_r < center_r2 else 1
        dc = -1 if 2 * tail_c < center_c2 else 1
        row, col = tail_r + dr, tail_c + dc
        remaining = None if extent == "edge" else 2
        while 0 <= row < height and 0 <= col < width and (remaining is None or remaining > 0):
            output[row][col] = color
            row += dr
            col += dc
            if remaining is not None:
                remaining -= 1
    return output


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _setting(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    result = {"train": [], "test": [], "program_solution": program(settings)}
    seen = set()
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            grid = sample_input(seed, index, split=split)
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise ValueError(f"duplicate input at {split}[{index}]")
            seen.add(key)
            canonical = claimed_output(grid, SETTINGS[0])
            alternate = claimed_output(grid, SETTINGS[1])
            if canonical == alternate:
                raise ValueError("sample does not distinguish ray extent")
            result[split].append({"input": grid, "output": claimed_output(grid, settings)})
    result["sampling"] = {"draws": demos + queries, "duplicate_rejections": 0}
    return result
