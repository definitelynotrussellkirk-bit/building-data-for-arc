"""Generator for ARC task 6f8cd79b.

Rule: output is h × w with the border = 8 and the interior = 0.
Input contents are ignored — only h and w matter.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0b6935859da0"
VERSION = "2.0.1"
TASK_ID = "0b6935859da0"
SUMMARY = (
    "Grid (h, w~3-14) with "
    "INPUT DECORATION drawn "
    "from 5 patterns: "
    "all_zero/random (40% "
    "density)/sparse (15%)/"
    "blob (half-grid solid "
    "block)/border_decoy "
    "(non-8 colored border). "
    "Input colors are "
    "irrelevant — only h "
    "and w matter for the "
    "rule. Output uniq_out="
    "39 (intrinsic — h×w "
    "combinations only). "
    "Rule (EMIT h×w GRID "
    "WITH 0-INTERIOR AND "
    "8-BORDER): COMPUTE h "
    "and w from input dims. "
    "EMIT a FRESH h×w "
    "OUTPUT GRID where: "
    "BORDER CELLS (row 0, "
    "row h-1, col 0, col "
    "w-1) = COLOR-8 (cyan); "
    "INTERIOR CELLS = 0. "
    "Input contents IGNORED. "
    "Net: any grid → same-"
    "sized hollow 8-frame."
)

INVARIANTS = [
    "input dims fall in valid range (3..15) so border is visible",
    "input contents are ignored — only h and w matter",
]

INPUT_DECORATIONS = ("all_zero", "random", "sparse", "blob", "border_decoy")
DEGENERATE_TEXTURES = ("border_decoy_8", "max_size", "min_size")
HELPFUL_TEXTURES = INPUT_DECORATIONS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 3..14", "valid": "3..15"},
    "grid_w":            {"type": "int", "default": "rng 3..14", "valid": "3..15"},
    "input_decoration":  {"type": "str", "default": "rng helpful",
                          "valid": "all_zero|random|sparse|blob|border_decoy"},
    "decoration_palette_size": {"type": "int", "default": "rng 1..3", "valid": "1..6"},
    "texture":           {"type": "str", "default": "alias for input_decoration",
                          "valid": "all_zero|random|sparse|blob|border_decoy|"
                                   "border_decoy_8|max_size|min_size"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 3, 6
    elif difficulty == "hard":
        h_lo, h_hi = 11, 14
    else:
        h_lo, h_hi = 3, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("cells")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_palette = int(overrides.get("decoration_palette_size",
                                  ctx.draw_int("decoration_palette_size", 1, 3)))
    palette = list(ctx.draw_distinct_colors("palette", n=max(1, n_palette),
                                            exclude={0, 8}))
    decoration = (overrides.get("texture")
                  or overrides.get("input_decoration")
                  or ctx.draw_choice("input_decoration", list(INPUT_DECORATIONS)))
    g = full_grid(h, w, 0)
    if decoration == "all_zero":
        return g
    if decoration == "random":
        for r in range(h):
            for c in range(w):
                if rng.random() < 0.4:
                    g[r][c] = rng.choice(palette)
        return g
    if decoration == "sparse":
        for r in range(h):
            for c in range(w):
                if rng.random() < 0.15:
                    g[r][c] = rng.choice(palette)
        return g
    if decoration == "blob":
        bh = h // 2; bw = w // 2
        r0 = rng.randint(0, h - bh); c0 = rng.randint(0, w - bw)
        color = palette[0]
        for r in range(r0, r0 + bh):
            for c in range(c0, c0 + bw):
                g[r][c] = color
        return g
    if decoration == "border_decoy":
        # Decorate the input border with a non-8 color to mislead.
        c0 = palette[0]
        for c in range(w):
            g[0][c] = c0; g[h - 1][c] = c0
        for r in range(h):
            g[r][0] = c0; g[r][w - 1] = c0
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Input dims in valid range [3,15] × [3,15]; only h and w matter for this rule."""
    errs = []
    h, w = len(grid), len(grid[0]) if grid else 0
    if h < 3 or h > 15:
        errs.append(f"height {h} out of valid range [3, 15]")
    if w < 3 or w > 15:
        errs.append(f"width {w} out of valid range [3, 15]")
    return errs


def _draw_from_degenerate(name, h, w, rng):
    palette = [c for c in range(1, 10) if c != 8]
    rng.shuffle(palette)
    if name == "max_size":
        h, w = 15, 15
    elif name == "min_size":
        h, w = 3, 3
    g = full_grid(h, w, 0)
    if name == "border_decoy_8":
        # Input border already filled with 8 — output equals input.
        for c in range(w):
            g[0][c] = 8; g[h - 1][c] = 8
        for r in range(h):
            g[r][0] = 8; g[r][w - 1] = 8
        return g
    return g
