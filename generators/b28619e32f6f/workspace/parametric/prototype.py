"""Constructive enclosed-region lessons with fixed or input-derived thresholds.

Labels here are claims. Native qualification/generation independently executes
the exact setting program through protected Racket before publishing them.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import math
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
MODES = ("fixed", "relative_to_largest")
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _mode(settings):
    if (type(settings) is not dict or set(settings) != {"threshold_mode"}
            or type(settings["threshold_mode"]) is not str
            or settings["threshold_mode"] not in MODES):
        raise ValueError("settings must name one declared threshold_mode")
    return settings["threshold_mode"]


def _integer(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")


def program(settings):
    name = "canonical.rkt" if _mode(settings) == "fixed" else "relative.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def regions(grid, *, diagonal=False):
    """Return zero components, including exterior, in deterministic order."""
    unseen = {(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color == 0}
    directions = CARDINAL + (((-1, -1), (-1, 1), (1, -1), (1, 1)) if diagonal else ())
    result = []
    while unseen:
        first = min(unseen)
        unseen.remove(first)
        cells, stack = {first}, [first]
        while stack:
            r, c = stack.pop()
            for dr, dc in directions:
                cell = (r + dr, c + dc)
                if cell in unseen:
                    unseen.remove(cell)
                    cells.add(cell)
                    stack.append(cell)
        result.append(cells)
    return result


def enclosed(grid, cells):
    h, w = len(grid), len(grid[0])
    return all(r not in (0, h - 1) and c not in (0, w - 1) for r, c in cells)


def area_color(n, mode, maximum):
    if mode == "fixed":
        return 8 if n <= 8 else 4 if n <= 24 else 3
    return 8 if 4 * n <= maximum else 4 if 2 * n <= maximum else 3


def mirror(grid, mode):
    inside = [cells for cells in regions(grid) if enclosed(grid, cells)]
    maximum = max(map(len, inside), default=0)
    out = deepcopy(grid)
    for cells in inside:
        color = area_color(len(cells), mode, maximum)
        for r, c in cells:
            out[r][c] = color
    return out


def _rng(seed, split, index, retry=0):
    digest = hashlib.sha256(f"b28619e32f6f-v1:{seed}:{split}:{index}:{retry}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _connected(cells):
    if not cells:
        return False
    seen = {min(cells)}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in CARDINAL:
            cell = (r + dr, c + dc)
            if cell in cells and cell not in seen:
                seen.add(cell)
                stack.append(cell)
    return seen == cells


def _room(n, rng):
    """A connected n-cell room with variable notches/holes and retained corners."""
    h = math.isqrt(n)
    if h * h < n:
        h += 1
    w = (n + h - 1) // h
    rectangle = {(r, c) for r in range(h) for c in range(w)}
    cells = set(rectangle)
    # Opposite corners preserve the bounding box and diagonal teaching contact.
    # Requiring all four would make a three-cell 2x2 L impossible to carve.
    corners = {(0, 0), (h - 1, w - 1)}
    while len(cells) > n:
        candidates = sorted(cells - corners)
        rng.shuffle(candidates)
        for cell in candidates:
            after = cells - {cell}
            removed = rectangle - after
            # A solid red 3x3 island is a nested frame in the canonical domain.
            # At most 10 cells are removed here, so this is the only possible
            # solid rectangle with both dimensions at least three.
            nested_frame = len(removed) >= 9 and any(
                all((r + dr, c + dc) in removed for dr in range(3) for dc in range(3))
                for r in range(h - 2) for c in range(w - 2))
            if not nested_frame and _connected(after):
                cells.remove(cell)
                break
        else:
            raise RuntimeError(f"cannot carve connected area {n}")
    return h, w, cells


def _frame(rows, rng, *, diagonal=False, fixed_shape=None):
    """Fill a red frame with isolated carved rooms; rows list their areas."""
    rooms = [[_room(n, rng) for n in row] for row in rows]
    placements = []
    if diagonal:
        if len(rooms) != 1 or len(rooms[0]) != 3:
            raise ValueError("diagonal teaching frame requires three rooms")
        first, second, third = rooms[0]
        placements = [(0, 0, first), (first[0], first[1], second),
                      (0, first[1] + second[1] + 1, third)]
    else:
        row_start = 0
        for row in rooms:
            row_height = max(room[0] for room in row)
            col_start = 0
            for room in row:
                placements.append((row_start + rng.randrange(row_height - room[0] + 1), col_start, room))
                col_start += room[1] + 1
            row_start += row_height + 1
    inner_h = max(r + room[0] for r, c, room in placements)
    inner_w = max(c + room[1] for r, c, room in placements)
    h, w = fixed_shape or (inner_h + 2, inner_w + 2)
    if inner_h + 2 > h or inner_w + 2 > w:
        raise ValueError("rooms do not fit the requested frame")
    dr, dc = rng.randrange(h - inner_h - 1), rng.randrange(w - inner_w - 1)
    grid = [[2] * w for _ in range(h)]
    for r0, c0, room in placements:
        for r, c in room[2]:
            grid[r + r0 + dr + 1][c + c0 + dc + 1] = 0
    return grid


def _paste(grid, frame, r0, c0):
    for r, row in enumerate(frame):
        grid[r0 + r][c0:c0 + len(row)] = row


def _orient(grid, rng):
    for _ in range(rng.randrange(4)):
        grid = [list(row) for row in zip(*grid[::-1])]
    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    return grid


def _stack(frames, rng, canvas=None):
    rng.shuffle(frames)
    content_h = sum(map(len, frames)) + len(frames) - 1
    content_w = max(len(frame[0]) for frame in frames)
    h, w = canvas or (content_h + 2, content_w + 2 + rng.randrange(2))
    if h > 30 or w > 30 or content_h > h or content_w > w:
        raise ValueError(f"scene does not fit: content {content_h}x{content_w}, canvas {h}x{w}")
    grid = [[0] * w for _ in range(h)]
    r0 = rng.randrange(h - content_h + 1)
    for frame in frames:
        _paste(grid, frame, r0, rng.randrange(w - len(frame[0]) + 1))
        r0 += len(frame) + 1
    return _orient(grid, rng)


def _teaching(index, rng):
    if index == 0:
        groups = [[7, 8, 9], [15, 16, 17], [24, 25, 32]]
    else:
        # Odd M exposes ceil/nearest rounding of the derived thresholds.
        groups = [[11, 12, 13], [23, 24], [25, 26, 51]]
    frames = []
    for i, group in enumerate(groups):
        rng.shuffle(group)
        frames.append(_frame([group], rng, diagonal=(index == 0 and i == 0)))
    return _stack(frames, rng)


def _ordinary(rng, wide=False):
    if wide:
        groups = [[rng.randint(3, 8), rng.randint(10, 16), rng.randint(30, 36)],
                  [rng.randint(21, 24), rng.randint(25, 28), rng.randint(65, 81)]]
        canvas = (24, 30)
    else:
        groups = [[rng.randint(3, 8), rng.randint(7, 9), rng.randint(10, 12)],
                  [rng.randint(17, 24), rng.randint(24, 25)]]
        canvas = (17, 20)
    frames = []
    for group in groups:
        rng.shuffle(group)
        frames.append(_frame([group], rng))
    return _stack(frames, rng, canvas)


def _stress(rng):
    """Two tall frames span all 30 rows/columns; a zero strip stays exterior."""
    left = _frame([[rng.randint(96, 120)],
                   [rng.randint(7, 9), rng.randint(21, 25)],
                   [rng.randint(17, 24), rng.randint(17, 24)]], rng, fixed_shape=(30, 14))
    right = _frame([[15, 16], [rng.randint(50, 72)], [23, 24], [7, 8]],
                   rng, fixed_shape=(30, 14))
    grid = [[0] * 30 for _ in range(30)]
    _paste(grid, left, 0, 0)
    _paste(grid, right, 0, 16)
    return _orient(grid, rng)


def _input(seed, split, index, retry=0):
    rng = _rng(seed, split, index, retry)
    if split == "train":
        return _teaching(index, rng) if index < 2 else _ordinary(rng, wide=bool(index % 2))
    if index == 0:
        return _stack([_frame([[rng.randint(7, 9)]], rng)], rng, (7, 7))
    if index == 1:
        return _ordinary(rng)
    if index == 2:
        return _ordinary(rng, wide=True)
    return _stress(rng)


def generate(seed, settings, demos=3, queries=4):
    mode = _mode(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    result = {"train": [], "test": [], "program_solution": program(settings)}
    seen = set()
    # Derive each slot independently. Counts and private mode cannot reseed inputs.
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            for retry in range(16):
                grid = _input(seed, split, index, retry)
                key = tuple(map(tuple, grid))
                if key not in seen:
                    break
            else:
                raise RuntimeError("failed to construct distinct inputs within 16 attempts")
            seen.add(key)
            result[split].append({"input": grid, "output": mirror(grid, mode)})
    return result
