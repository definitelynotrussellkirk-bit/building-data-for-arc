"""Generator for arc_additional_puzzle_bank_volume12:H78.

Rule: control 1-3 selects which gray nested-frame band becomes cyan.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_frames, no_control, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "cfd3c4190aa0"
VERSION = "3.0.1"  # self-flagged HARDCODED-LOW: FIXED margin-2 concentric frames (offsets 0,2,4), control fixed at (0,0), grid 13-17 -> ~27 distinct, dup 27%. Rule only needs 3 NESTED color-5 rect-frames (sorted by area) + one 1/2/3 control anywhere. Now random per-side insets (asymmetric, non-concentric nesting), free placement, wider grid 12-28, control placed freely. Frame color stays 5 + control in {1,2,3} (rule-locked)."
TASK_ID = "cfd3c4190aa0"
SUMMARY = (
    "0-bg grid (h, w~13-17) "
    "with: (a) CONTROL "
    "CELL at (0, 0) in "
    "color ∈ {1, 2, 3} "
    "encoding a BAND "
    "INDEX; (b) THREE "
    "NESTED COLOR-5 (gray) "
    "RECTANGULAR FRAMES "
    "drawn at offsets (0, "
    "2, 4) from a centered "
    "anchor — outermost "
    "(frame 0), middle "
    "(frame 1, 2 cells "
    "inward), innermost "
    "(frame 2, 4 cells "
    "inward). Rule "
    "(CONTROL 1-3 "
    "SELECTS WHICH GRAY "
    "NESTED-FRAME BAND "
    "BECOMES CYAN): READ "
    "the CONTROL cell's "
    "color k ∈ {1, 2, 3}"
    ". The 3 nested "
    "frames define 3 "
    "BANDS: BAND-1 "
    "(ring between frame "
    "0 and 1), BAND-2 "
    "(ring between 1 and "
    "2), BAND-3 (interior "
    "inside frame 2). "
    "PAINT every bg-0 "
    "cell in the k-th "
    "BAND with COLOR 8 "
    "(cyan). Gray frames "
    "and control cell "
    "stay. Net: control "
    "color picks one "
    "nested ring to fill "
    "cyan. Flag: "
    "HARDCODED-LOW "
    "DIVERSITY — 3 "
    "controls × ~9 grid "
    "sizes → ~26 distinct."
)

INVARIANTS = [
    "background is 0",
    "three gray rectangular frames are nested",
    "one non-frame control cell has value 1, 2, or 3",
    "the selected region contains blank cells",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_frames", "no_control", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 14..22", "valid": "12..28"},
    "grid_w":         {"type": "int", "default": "rng 14..22", "valid": "12..28"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "control":        {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "inset_max":      {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "free", "valid": "free"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _nested_frames(rng, h, w, imax):
    """3 nested color-5 rect-frames with random per-side insets (>=2 so frame
    outlines stay separate 4-conn components with a bg gap ring). Inner outline
    >=3 so it has a blank interior (band-3). Returns (R0,C0,R1,C1) outer or None."""
    for _ in range(300):
        t1 = rng.randint(2, imax); b1 = rng.randint(2, imax)
        l1 = rng.randint(2, imax); r1 = rng.randint(2, imax)
        t2 = rng.randint(2, imax); b2 = rng.randint(2, imax)
        l2 = rng.randint(2, imax); r2 = rng.randint(2, imax)
        ih = rng.randint(3, 8); iw = rng.randint(3, 8)        # inner outline dims
        out_h = ih + t1 + b1 + t2 + b2
        out_w = iw + l1 + r1 + l2 + r2
        if out_h > h or out_w > w:
            continue
        R0 = rng.randint(0, h - out_h); C0 = rng.randint(0, w - out_w)
        R1 = R0 + out_h - 1; C1 = C0 + out_w - 1
        mid = (R0 + t2, C0 + l2, R1 - b2, C1 - r2)
        inner = (mid[0] + t1, mid[1] + l1, mid[2] - b1, mid[3] - r1)
        return (R0, C0, R1, C1), mid, inner
    return None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; control cell (if any) has value 1/2/3; all other non-bg cells are color 5."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("cell value out of 0-9")
        return errs
    controls = [(r, c, grid[r][c]) for r in range(h) for c in range(w)
                if grid[r][c] in (1, 2, 3)]
    bad_others = [(r, c, grid[r][c]) for r in range(h) for c in range(w)
                  if grid[r][c] not in (0, 5) and (r, c, grid[r][c]) not in controls]
    if bad_others:
        errs.append(f"unexpected non-{{0,5}} cells (besides control): {bad_others[:3]}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 12, 15); w = ctx.draw_int("grid_w", 12, 15)
        imax = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 20, 28); w = ctx.draw_int("grid_w", 20, 28)
        imax = ctx.draw_int("inset_max", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 14, 22); w = ctx.draw_int("grid_w", 14, 22)
        imax = ctx.draw_int("inset_max", 2, 4)
    g = full_grid(h, w, 0)
    nf = _nested_frames(rng, h, w, imax)
    if nf is None:                       # fallback to the old centered layout
        for offset in (0, 2, 4):
            draw_frame(g, 2 + offset, 2 + offset, h - 3 - offset, w - 3 - offset, 5)
        outer = (2, 2, h - 3, w - 3)
    else:
        outer, mid, inner = nf
        for (R0, C0, R1, C1) in (outer, mid, inner):
            draw_frame(g, R0, C0, R1, C1, 5)
    control = int(overrides.get("control", ctx.draw_int("control", 1, 3)))
    # place control on a bg cell, preferring OUTSIDE the outer frame (matches
    # canonical); the rule reads the first 1/2/3 cell and paints only v==0 cells.
    oR0, oC0, oR1, oC1 = outer
    outside = [(r, c) for r in range(h) for c in range(w)
               if g[r][c] == 0 and (r < oR0 or r > oR1 or c < oC0 or c > oC1)]
    if outside:
        cr, cc = rng.choice(outside)
    else:
        bg = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 0]
        cr, cc = rng.choice(bg)
    g[cr][cc] = control
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(14, 14, 0)
    if name == "no_frames":
        g[0][0] = 1
        return g
    if name == "no_control":
        for offset in (0, 2, 4):
            draw_frame(g, 2 + offset, 2 + offset, 11 - offset, 11 - offset, 5)
        return g
    if name == "full_grid":
        for r in range(14):
            for c in range(14):
                g[r][c] = 5
        return g
    return g
