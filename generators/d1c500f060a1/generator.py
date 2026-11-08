"""Reviewed generator for transform-coded motif packing.

Row 0 contains only the five transform codes actually defined by the canonical
rule.  Row 1 is blank.  A varied connected two-color motif appears below it;
the unique accent makes rotations/reflections visible instead of permitting
unseen-code or symmetric-shape shortcuts.
"""
from __future__ import annotations

from collections import Counter, deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "d1c500f060a1"
VERSION = "2.0.0"
SUMMARY = "Apply row-0 transform codes 1..5 to a base motif and pack the pieces."

PALETTES = {
    "default": ((6, 8), (7, 9), (4, 6), (3, 8)),
    "warm": ((2, 4), (6, 2), (4, 3)),
    "cool": ((1, 8), (3, 7), (8, 1)),
    "varied": ((6, 9), (4, 8), (5, 7)),
}
SHAPES = {
    "hook5": ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    "zig5": ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
    "tee5": ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    "stair6": ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2)),
    "fork7": ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1), (2, 2)),
    "block_notch8": ((0, 0), (0, 1), (0, 2), (0, 3),
                      (1, 0), (1, 1), (2, 0), (2, 1)),
}
INVARIANTS = [
    "row 0 contains 1..5 distinct transform codes from 1..5",
    "row 1 is blank",
    "rows 2 onward contain one connected two-color motif",
    "the motif has a unique accent cell so every selected transform is visible",
]
AXES = {
    "grid_h": {"type": "int", "default": "difficulty band", "valid": "6..30"},
    "grid_w": {"type": "int", "default": "difficulty band", "valid": "6..30"},
    "n_codes": {"type": "int", "default": "difficulty band", "valid": "1..5"},
    "palette_kind": {"type": "str", "default": "rng", "valid": "|".join(PALETTES)},
    "texture": {"type": "str", "default": "coverage schedule", "valid": "|".join(SHAPES)},
}
_ALLOWED_OVERRIDES = frozenset(AXES)


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise TypeError("seed must be an exact integer in 0..2**63-1")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative exact integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium or hard")
    unknown = set(overrides) - _ALLOWED_OVERRIDES
    if unknown:
        raise ValueError("unknown overrides: " + ", ".join(sorted(unknown)))


def _draw_int_axis(ctx, label, low, high, default_low, default_high, overrides):
    if label in overrides and overrides[label] is not None:
        value = overrides[label]
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{label} must be an exact integer in {low}..{high}")
        return ctx.draw_choice(label, tuple(range(low, high + 1)))
    return ctx.draw_int_strict(label, default_low, default_high)


def _draw_choice_axis(ctx, label, options, defaults, overrides):
    if label in overrides and overrides[label] is not None:
        value = overrides[label]
        if type(value) is not str or value not in options:
            raise ValueError(f"{label} must be one of {tuple(options)}")
        return ctx.draw_choice(label, tuple(options))
    return ctx.draw_choice(label, tuple(defaults))


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return _rotate_cw(_rotate_cw(grid))


def _rotate_ccw(grid):
    return _rotate_cw(_rotate_180(grid))


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid):
    return [list(row) for row in reversed(grid)]


def _transform(grid, code):
    return {1: _rotate_cw, 2: _rotate_180, 3: _rotate_ccw,
            4: _flip_lr, 5: _flip_ud}[code](grid)


def _connected(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        r, c = queue.popleft()
        for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if point in cells and point not in seen:
                seen.add(point); queue.append(point)
    return seen == cells


def analyze(grid):
    if not isinstance(grid, (list, tuple)) or len(grid) < 3:
        raise ValueError("expected at least three rows")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be exact integer ARC colors 0..9")
    if len(grid) > 30 or width > 30:
        raise ValueError("grid dimensions must be at most 30")
    codes = [value for value in grid[0] if value]
    if not 1 <= len(codes) <= 5 or any(code not in range(1, 6) for code in codes):
        raise ValueError("row 0 must contain 1..5 codes from 1..5")
    if len(set(codes)) != len(codes):
        raise ValueError("row-0 transform codes must be distinct")
    if any(grid[1]):
        raise ValueError("row 1 must be blank")
    cells = [(r, c) for r, row in enumerate(grid[2:], start=2)
             for c, value in enumerate(row) if value]
    if len(cells) < 3 or not _connected(cells):
        raise ValueError("body must contain one connected motif of at least three cells")
    counts = Counter(grid[r][c] for r, c in cells)
    if len(counts) != 2:
        raise ValueError("motif must use exactly two colors")
    if sum(count == 1 for count in counts.values()) != 1:
        raise ValueError("motif must have exactly one singleton accent")
    r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
    r1, c1 = max(r for r, _ in cells), max(c for _, c in cells)
    crop = [list(row[c0:c1 + 1]) for row in grid[r0:r1 + 1]]
    return {"codes": codes, "cells": cells, "crop": crop, "bbox": (r0, c0, r1, c1)}


def self_check(grid, *, difficulty=None, meta=None):
    try:
        analyze(grid)
        return []
    except (TypeError, ValueError) as exc:
        return [str(exc)]


def _pack(pieces):
    out_h = max(len(piece) for piece in pieces)
    out_w = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    out = full_grid(out_h, out_w, 0)
    c0 = 0
    for piece in pieces:
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                if value: out[r][c0 + c] = value
        c0 += len(piece[0]) + 1
    return out


def rule_mirror(grid):
    info = analyze(grid)
    return _pack([_transform(info["crop"], code) for code in info["codes"]])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    bands = {
        None: ((8, 16), (10, 18), (2, 4)),
        "easy": ((7, 11), (9, 14), (2, 3)),
        "medium": ((11, 18), (13, 20), (3, 4)),
        "hard": ((16, 26), (18, 28), (4, 5)),
    }
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    (hlo, hhi), (wlo, whi), (clo, chi) = bands[difficulty]
    h = _draw_int_axis(ctx, "grid_h", 6, 30, hlo, hhi, overrides)
    w = _draw_int_axis(ctx, "grid_w", 6, 30, wlo, whi, overrides)
    n_codes = _draw_int_axis(ctx, "n_codes", 1, 5, clo, chi, overrides)
    scheduled = tuple(SHAPES)[(seed + sample_index) % len(SHAPES)]
    texture = _draw_choice_axis(ctx, "texture", SHAPES, (scheduled,), overrides)
    palette_kind = _draw_choice_axis(ctx, "palette_kind", PALETTES, PALETTES, overrides)
    body, accent = ctx.draw_choice("motif_palette", PALETTES[palette_kind])

    shape = SHAPES[texture]
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    if 2 + sh > h or sw > w:
        raise ValueError("selected texture does not fit the requested grid")
    if n_codes * max(sh, sw) + (n_codes - 1) > 30:
        raise ValueError("selected motif/code count would exceed ARC output width")
    rng = ctx.draw_rng("layout")
    codes = rng.sample(range(1, 6), n_codes)
    columns = sorted(rng.sample(range(w), n_codes))
    r0 = rng.randint(2, h - sh)
    c0 = rng.randint(0, w - sw)
    grid = full_grid(h, w, 0)
    for col, code in zip(columns, codes): grid[0][col] = code
    for index, (dr, dc) in enumerate(shape):
        grid[r0 + dr][c0 + dc] = accent if index == 0 else body
    errors = self_check(grid)
    if errors:
        raise RuntimeError("constructive generator produced invalid grid: " + "; ".join(errors))
    return grid
