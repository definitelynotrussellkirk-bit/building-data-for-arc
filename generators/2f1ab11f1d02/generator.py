"""Generator for arc_additional_puzzles_21_set21_bundle:M144 — Cmd at (0,0) → crop+transform.

Rule: cmd = at(0,0). Set (0,0)=0; crop-to-content; apply by code:
1=identity, 2=cw, 3=180, 4=ccw, 5=flip-lr, 6=flip-ud, else=transpose.

Combinatorial axes (8): grid_h, grid_w, palette_kind, cmd,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_cmd, no_blob, square_blob.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2f1ab11f1d02"
VERSION = "2.2.1"  # v2.2.0: dense non-square, transform-visible payloads; v2.1.0 still allowed sparse/symmetric crops.
TASK_ID = "2f1ab11f1d02"
SUMMARY = (
    "0-bg grid (h ∈ 7-9, w ∈ 9-11) "
    "with: (a) ONE CMD CELL at FIXED "
    "position (0, 0) — value ∈ {1..7} "
    "selecting a TRANSFORM (1=identity, "
    "2=cw90, 3=180, 4=ccw90, 5=flip-LR, "
    "6=flip-UD, 7=transpose); (b) ONE "
    "SMALL MULTICOLOR BLOB in the "
    "LOWER-RIGHT QUADRANT — sub_h × "
    "sub_w (sub_h, sub_w ∈ 2-3 with "
    "sub_h ≠ sub_w to make transforms "
    "visible) at random position "
    "(r0 ∈ h//2..h-sub_h-1, c0 ∈ "
    "w//2..w-sub_w-1), with each cell "
    "painted (with 70% prob) in one "
    "of 2 distinct palette colors "
    "drawn from {2..9}\\{cmd}. Rule "
    "(READ THE CMD AT (0, 0), CLEAR "
    "(0, 0) TO 0, CROP THE BODY TO "
    "NON-BG CONTENT, APPLY "
    "TRANSFORM BY CODE — 1=IDENTITY, "
    "2=CW, 3=180, 4=CCW, 5=FLIP-LR, "
    "6=FLIP-UD, ELSE=TRANSPOSE — "
    "OUTPUT THE TRANSFORMED CROP): "
    "READ cmd from (0, 0). SET "
    "(0, 0) = 0. CROP the remaining "
    "grid to the bbox of non-bg "
    "cells. APPLY the cmd's "
    "TRANSFORM. OUTPUT the "
    "transformed crop. Net: corner "
    "cmd selects 1 of 7 dihedral "
    "operations on the cropped "
    "multicolor blob."
)

INVARIANTS = [
    "cmd at (0,0) ∈ 1..7",
    "blob is non-square multicolor in lower-right region",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_cmd", "no_blob", "square_blob")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..12"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "cmd":            {"type": "int", "default": "rng 1..7", "valid": "1..7"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "cmd_at_0_0_blob_LR",
                       "valid": "cmd_at_0_0_blob_LR"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """cmd at (0,0) ∈ 1..7; ≥1 non-zero non-cmd cell elsewhere (the blob)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    cmd = grid[0][0]
    if cmd not in range(1, 8):
        errs.append(f"cmd at (0,0)={cmd} not in 1..7")
    # At least one non-zero, non-cmd cell elsewhere (the blob)
    has_blob = any(
        grid[r][c] != 0 and not (r == 0 and c == 0)
        for r in range(h) for c in range(w)
    )
    if not has_blob:
        errs.append("no blob cells found (only cmd at (0,0))")
    return errs


def _rot90(g):
    return [list(row) for row in zip(*g[::-1])]

def _rot180(g):
    return [row[::-1] for row in g[::-1]]

def _rotccw(g):
    return [list(row) for row in zip(*g)][::-1]

def _flip_lr(g):
    return [row[::-1] for row in g]

def _flip_ud(g):
    return [row[:] for row in g[::-1]]

def _transpose(g):
    return [list(row) for row in zip(*g)]

def _apply_cmd(crop, cmd):
    if cmd == 1:
        return [row[:] for row in crop]
    if cmd == 2:
        return _rot90(crop)
    if cmd == 3:
        return _rot180(crop)
    if cmd == 4:
        return _rotccw(crop)
    if cmd == 5:
        return _flip_lr(crop)
    if cmd == 6:
        return _flip_ud(crop)
    return _transpose(crop)

def _visible_payload(crop, cmd):
    vals = [v for row in crop for v in row if v != 0]
    if len(vals) < 2 or len(set(vals)) < 2:
        return False
    return cmd == 1 or _apply_cmd(crop, cmd) != crop

def _payload_pattern(rng, sub_h, sub_w, colors, cmd):
    """Dense, multicolor, non-square payload whose selected transform is visible."""
    for _ in range(100):
        pat = [[rng.choice(colors) for _ in range(sub_w)] for _ in range(sub_h)]
        # Break common LR/UD/180 symmetries deterministically.  Use opposite
        # corners with opposite colors so both horizontal and vertical flips are
        # observable before the random interior/middle cells are considered.
        pat[0][0] = colors[0]
        pat[0][-1] = colors[1]
        pat[-1][0] = colors[1]
        pat[-1][-1] = colors[0]
        if _visible_payload(pat, cmd):
            return pat
    pat = [[colors[(r + c) % 2] for c in range(sub_w)] for r in range(sub_h)]
    pat[0][0] = colors[0]
    pat[0][-1] = colors[1]
    pat[-1][0] = colors[1]
    pat[-1][-1] = colors[0]
    return pat


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 7)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 9, 11)
    cmd = ctx.draw_int("cmd", 1, 7)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    g[0][0] = cmd
    sub_h, sub_w = rng.choice([(2, 3), (3, 2)])
    r0 = rng.randint(h // 2, h - sub_h - 1) if h - sub_h - 1 >= h // 2 else h // 2
    c0 = rng.randint(w // 2, w - sub_w - 1) if w - sub_w - 1 >= w // 2 else w // 2
    palette = [c for c in range(2, 10) if c != cmd]
    rng.shuffle(palette)
    pat_colors = palette[:2]
    pat = _payload_pattern(rng, sub_h, sub_w, pat_colors, cmd)
    for r in range(sub_h):
        for c in range(sub_w):
            g[r0 + r][c0 + c] = pat[r][c]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "no_cmd":
        # blob without cmd at (0,0) → no transform dispatch
        g[0][0] = 0
        for r, c in [(4, 5), (4, 6), (5, 5)]: g[r][c] = 4
        return g
    if name == "no_blob":
        # cmd alone, no payload → empty crop, undefined transform
        g[0][0] = 3
        return g
    if name == "square_blob":
        # square 2x2 blob → cw/ccw/transpose all yield same shape
        g[0][0] = 2
        for r in range(4, 6):
            for c in range(5, 7):
                g[r][c] = 4
        return g
    return g
