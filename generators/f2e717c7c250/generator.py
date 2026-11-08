"""Generator for f2e717c7c250 — crop the union of two key-colored blobs.

The canonical rule reads exactly two nonzero key colors from row zero, drops the
blank separator row, and crops the body to the bounding box of every cell in
those two colors.  Other colors are distractors and remain only when they fall
inside that selected bounding box.
"""
from __future__ import annotations

import hashlib

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "f2e717c7c250"
VERSION = "2.2.0"
TASK_ID = GENERATOR_ID
SUMMARY = (
    "Two distinct key-color markers occupy row zero above a blank separator. "
    "The body contains one connected blob of each key color plus non-key "
    "distractors; output is the tight crop around all key-colored body cells."
)
RULE_HASH = "6c8edaaafe66"

INVARIANTS = [
    "background is 0",
    "row 0 contains exactly two distinct nonzero key colors",
    "row 1 is a blank separator",
    "the body contains one connected component of each key color",
]

DEGENERATE_TEXTURES = ("no_keys", "no_matching_blobs", "all_distractors")
TEXTURES = ("standard", *DEGENERATE_TEXTURES)
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 7..15", "valid": "7..15"},
    "grid_w": {"type": "int", "default": "difficulty-aware 8..17", "valid": "8..17"},
    "n_keys": {"type": "int", "default": "2", "valid": "2"},
    "texture": {"type": "str", "default": "standard", "valid": "|".join(TEXTURES)},
}

_ALLOWED_OVERRIDES = frozenset(AXES)
_CARD = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _strict_axis(ctx, label: str, default_lo: int, default_hi: int, global_lo: int, global_hi: int) -> int:
    value = ctx.overrides.get(label)
    if value is not None:
        return ctx.draw_int_strict(label, global_lo, global_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _texture(overrides: dict) -> str:
    value = overrides.get("texture", "standard")
    if type(value) is not str or value not in TEXTURES:
        raise ValueError(f"texture must be one of {TEXTURES}")
    return value


def _components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in _CARD:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    stack.append(nxt)
        result.append(component)
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    texture = _texture(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    ctx.draw_int_strict("n_keys", 2, 2)

    if difficulty == "easy":
        h = _strict_axis(ctx, "grid_h", 7, 9, 7, 15)
        w = _strict_axis(ctx, "grid_w", 8, 11, 8, 17)
        key_sizes = (2, 3)
        distractor_sizes = (2, 2)
    elif difficulty == "hard":
        h = _strict_axis(ctx, "grid_h", 12, 15, 7, 15)
        w = _strict_axis(ctx, "grid_w", 13, 17, 8, 17)
        key_sizes = (4, 6)
        distractor_sizes = (3, 5)
    else:
        h = _strict_axis(ctx, "grid_h", 9, 12, 7, 15)
        w = _strict_axis(ctx, "grid_w", 10, 14, 8, 17)
        key_sizes = (3, 4)
        distractor_sizes = (2, 4)

    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, h, w)

    rng = ctx.draw_rng("layout")
    body_h = h - 2
    palette = rng.sample(range(1, 10), 5)
    keys = palette[:2]
    distractor_colors = palette[2:]
    body = full_grid(body_h, w, 0)

    # Retry a complete body layout rather than silently dropping a required key.
    for _ in range(80):
        body = full_grid(body_h, w, 0)
        used: set[tuple[int, int]] = set()
        key_blobs = []
        for color in keys:
            size = rng.randint(*key_sizes)
            blob = grow_blob(rng, body_h, w, used, size, max_attempts=120)
            if blob is None:
                break
            key_blobs.append((color, blob))
            used |= blob
        if len(key_blobs) != 2:
            continue
        distractors = []
        for index, color in enumerate(distractor_colors[:2]):
            lo, hi = distractor_sizes
            blob = grow_blob(rng, body_h, w, used, rng.randint(lo, hi), max_attempts=80)
            if blob is not None:
                distractors.append((color, blob))
                used |= blob
        if distractors:
            for color, cells in key_blobs + distractors:
                for r, c in cells:
                    body[r][c] = color
            break
    else:
        raise ValueError("could not construct two isolated key blobs and a distractor")

    grid = full_grid(h, w, 0)
    columns = sorted(rng.sample(range(w), 2))
    for column, color in zip(columns, keys):
        grid[0][column] = color
    for r, row in enumerate(body, start=2):
        grid[r] = row
    errors = self_check(grid)
    if errors:
        raise ValueError("generated invalid canonical scene: " + "; ".join(errors))
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["empty grid"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["grid is not rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be exact integers in 0..9"]
    h, w = len(grid), width
    errors = []
    if not 7 <= h <= 15 or not 8 <= w <= 17:
        errors.append(f"expected dimensions within 7..15 by 8..17; got {h}x{w}")
    keys = [value for value in grid[0] if value != 0]
    if len(keys) != 2 or len(set(keys)) != 2:
        errors.append("row 0 must contain exactly two distinct nonzero keys")
        return errors
    if len(grid) < 2 or any(grid[1]):
        errors.append("row 1 must be a blank separator")
    body = grid[2:]
    for key in keys:
        cells = {(r, c) for r, row in enumerate(body) for c, value in enumerate(row) if value == key}
        if not cells:
            errors.append(f"body is missing key color {key}")
        elif len(_components(cells)) != 1:
            errors.append(f"key color {key} must form one connected body component")
    return errors


def _draw_from_degenerate(name: str, h: int, w: int):
    grid = full_grid(h, w, 0)
    if name == "no_keys":
        grid[3][1] = grid[3][2] = 4
        grid[-2][-3] = grid[-2][-2] = 6
    elif name == "no_matching_blobs":
        grid[0][1] = 4
        grid[0][-2] = 6
        grid[3][2] = grid[3][3] = 8
        grid[-2][-3] = grid[-2][-2] = 3
    elif name == "all_distractors":
        grid[0][1] = 4
        grid[0][-2] = 6
        for r, c, color in ((3, 2, 8), (3, 3, 8), (h - 2, w - 3, 3), (h - 2, w - 2, 3)):
            grid[r][c] = color
    return grid
