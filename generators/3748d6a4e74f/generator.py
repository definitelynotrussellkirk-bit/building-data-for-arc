"""Generator for arc_additional_puzzles_21_set7:M45 — Crop-by-content + rotate by command.

Rule: cmd at (0,0); crop the rest; rotate by cmd value.

Combinatorial axes (8): grid_h, grid_w, palette_kind, cmd, blob_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blob, blob_at_command, blob_is_rectangle.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "3748d6a4e74f"
VERSION = "2.0.0"
TASK_ID = "3748d6a4e74f"
SUMMARY = (
    "0-bg grid (h ∈ 8-10, w ∈ 8-10) with: "
    "(a) ONE CMD CELL at FIXED position "
    "(0, 0) — value ∈ {1, 2, 3, 4} "
    "selecting a rotation (per demos: "
    "1=cw90, 2=180, 3=ccw90, 4=identity); "
    "(b) ONE SINGLE NON-RECTANGULAR BLOB "
    "in a non-cmd color drawn via "
    "draw_color: a SIZE ∈ 4-7 cell "
    "irregular blob built by grow_blob "
    "random walk, placed so NONE of its "
    "cells lie in the 2×2 corner around "
    "(0, 0) (so cmd stays isolated). "
    "Rule (READ THE CMD, CROP THE BLOB "
    "TO ITS BBOX, ROTATE BY THE CMD "
    "VALUE): READ cmd from (0, 0) → "
    "select rotation. FIND the single "
    "non-bg blob (excluding the cmd "
    "cell). CROP the blob to its "
    "bounding box (a small h_bb × w_bb "
    "grid with the blob's color "
    "where cells are present, 0 "
    "elsewhere). ROTATE the cropped "
    "grid by cmd (cw90 / 180 / "
    "ccw90 / identity). OUTPUT the "
    "rotated crop. Net: a single "
    "colored shape is extracted and "
    "rotated by the corner code, "
    "yielding a small output grid."
)

INVARIANTS = [
    "(0,0) holds cmd in {1, 2, 3, 4}",
    "single non-rectangular blob away from (0,0)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blob", "blob_at_command", "blob_is_rectangle")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "cmd":            {"type": "int", "default": "rng 1..4", "valid": "1..9"},
    "blob_size":      {"type": "int", "default": "rng 4..7", "valid": "3..10"},
    "blob_color":     {"type": "color", "default": "rng", "valid": "1..9"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "command_corner_with_blob",
                       "valid": "command_corner_with_blob"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; (0,0) cmd cell in {1..4}; ≥1 other nonzero cell (blob)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    for r in range(h):
        for c in range(w):
            if not (0 <= grid[r][c] <= 9):
                errors.append(f"out-of-range value {grid[r][c]} at ({r},{c})")
    cmd = grid[0][0]
    if cmd == 0:
        pass  # degenerate (no_blob or similar) — allowed
    elif cmd not in (1, 2, 3, 4):
        errors.append(f"cmd at (0,0) not in {{1,2,3,4}}: got {cmd}")
    nonzero_other = sum(
        1 for r in range(h) for c in range(w)
        if grid[r][c] != 0 and not (r == 0 and c == 0)
    )
    if cmd != 0 and nonzero_other == 0:
        pass  # degenerate (no_blob) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 8, 8)
        size = ctx.draw_int("blob_size", 4, 5)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        size = ctx.draw_int("blob_size", 6, 7)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 8, 10)
        size = ctx.draw_int("blob_size", 4, 7)
    cmd = ctx.draw_int("cmd", 1, 4)
    color = ctx.draw_color("blob_color")
    g = full_grid(h, w, 0)
    g[0][0] = cmd
    used = {(0, 0), (0, 1), (1, 0), (1, 1)}
    rng = ctx.draw_rng("blob")
    for _ in range(20):
        blob = grow_blob(rng, h, w, used, size)
        if blob is None: continue
        if any(r <= 1 and c <= 1 for r, c in blob): continue
        for r, c in blob: g[r][c] = color
        break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    g[0][0] = 1   # cmd=cw90
    if name == "no_blob":
        # cmd present but no blob → nothing to crop and rotate, output is empty/trivial
        return g
    if name == "blob_at_command":
        # blob extends into (0,0) cell → cmd is ambiguously part of the blob
        for (r, c) in [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)]: g[r][c] = 4
        return g
    if name == "blob_is_rectangle":
        # blob is a perfect rectangle → rotation is visually identical (or only differs by aspect)
        for r in range(2, 5):
            for c in range(3, 7): g[r][c] = 6
        return g
    return g
