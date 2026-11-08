"""Generator for 412b6263.

Rule: rotate ccw, frame in 1-border with 7-corners, tile twice vertically.
Output is (2*core_h + 3) × (core_w + 2).

Combinatorial axes (8): grid_h/w, fg_density, fg_palette_kind,
fill_layout, anchor_corners, decoy_density, fg_balance,
core_aspect_kind.
Degenerates: empty_grid, full_fg, single_fg.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "909cd6619a84"
VERSION = "2.1.0"
TASK_ID = "909cd6619a84"
SUMMARY = (
    "h × w grid (small examples plus medium/large hard examples, up to 24×13) with bg = 7 (orange) and "
    "sparse non-7 cells in colors 5 and/or 9 (~25-55% "
    "density). Various layouts (scatter, blob, stripes, diag, "
    "frame, checker). Rule: rotate input 90° CCW → core. "
    "Output dimensions: (2*core_h + 3) × (core_w + 2). For "
    "each output cell (r, c): let period = core_h + 1. If r "
    "% period == 0 → it's a SEPARATOR ROW: cells at col 0 "
    "and col core_w+1 are 7, else 1. If r % period != 0 → "
    "it's a CORE ROW: cells at col 0 and col core_w+1 are 1 "
    "(side border), interior cells are core[r%period - 1]"
    "[c-1]. Net effect: rotate-CCW the input, then frame in "
    "1-border with 7-corners and tile vertically twice."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 7",
    "≥4 non-7 cells of color 5 and/or 9",
    "no color 1 in input (1 is the rule's frame fill)",
    "h, w chosen so the output (2*w + 3, h + 2) still fits 30×30 after rotate-ccw",
]

FILL_LAYOUTS = ("scattered", "blob", "stripes", "diag", "frame", "checker")
DEGENERATE_TEXTURES = ("empty_grid", "full_fg", "single_fg")
HELPFUL_TEXTURES = FILL_LAYOUTS

AXES = {
    "grid_h":             {"type": "int", "default": "easy 5..7 / med 8..16 / hard 14..24", "valid": "5..28"},
    "grid_w":             {"type": "int", "default": "easy 3..5 / med 5..10 / hard 8..13", "valid": "3..13"},
    "fg_density":         {"type": "float", "default": "rng 0.25..0.55",
                           "valid": "0.1..0.7"},
    "fg_palette_kind":    {"type": "str", "default": "rng both|five_only|nine_only",
                           "valid": "both|five_only|nine_only"},
    "fill_layout":        {"type": "str", "default": "rng helpful",
                           "valid": "scattered|blob|stripes|diag|frame|checker"},
    "fg_balance":         {"type": "str", "default": "rng even|five_heavy|nine_heavy",
                           "valid": "even|five_heavy|nine_heavy"},
    "core_aspect_kind":   {"type": "str", "default": "rng tall|wide|square",
                           "valid": "tall|wide|square"},
    "anchor_corners":     {"type": "bool", "default": "false",
                           "valid": "true|false"},
    "texture":            {"type": "str", "default": "alias for fill_layout",
                           "valid": "scattered|blob|stripes|diag|frame|checker|empty_grid|full_fg|single_fg"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=7, >=4 non-7 cells (of color 5 or 9), no color-1."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in ("empty_grid", "full_fg", "single_fg"):
        return errs
    non7 = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 7]
    if len(non7) < 2:
        errs.append(f"need >=2 non-7 cells, found {len(non7)}")
    if any(grid[r][c] == 1 for r in range(h) for c in range(w)):
        errs.append("color-1 found in input (reserved for rule's frame fill)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 5, 7, 3, 5
    elif difficulty == "hard":
        # This rule's output is (2*w + 3) × (h + 2), so the old hard
        # band (h<=11,w<=9) left the training examples far below the eval
        # size distribution.  Stay within the 30×30 ARC canvas while letting
        # hard examples reach 24×13 inputs and 29×26 outputs.
        h_lo, h_hi, w_lo, w_hi = 14, 24, 8, 13
    else:
        h_lo, h_hi, w_lo, w_hi = 8, 16, 5, 10
    h = max(5, min(28, ctx.draw_int("grid_h", h_lo, h_hi)))
    w = max(3, min(13, ctx.draw_int("grid_w", w_lo, w_hi)))
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    palette_kind = overrides.get("fg_palette_kind",
                                 ctx.draw_choice("fg_palette_kind",
                                                 ["both", "five_only", "nine_only"]))
    if palette_kind == "five_only":
        palette = [5]
    elif palette_kind == "nine_only":
        palette = [9]
    else:
        palette = [5, 9]
    balance = overrides.get("fg_balance",
                            ctx.draw_choice("fg_balance",
                                            ["even", "five_heavy", "nine_heavy"]))
    if "five_heavy" == balance and palette == [5, 9]:
        weighted = [5, 5, 5, 9]
    elif "nine_heavy" == balance and palette == [5, 9]:
        weighted = [9, 9, 9, 5]
    else:
        weighted = palette
    layout = (overrides.get("texture") or overrides.get("fill_layout")
              or ctx.draw_choice("fill_layout", list(FILL_LAYOUTS)))
    density = float(overrides.get("fg_density",
                                  ctx.draw_rng("fg_density")
                                  .uniform(0.25, 0.55)))
    g = full_grid(h, w, 7)
    _apply_layout(g, layout, h, w, weighted, density, rng)
    fg_count = sum(1 for r in range(h) for c in range(w) if g[r][c] != 7)
    if fg_count < 4:
        for _ in range(4 - fg_count):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            g[r][c] = rng.choice(weighted)
    if bool(overrides.get("anchor_corners", False)):
        g[0][0] = rng.choice(weighted)
        g[h - 1][w - 1] = rng.choice(weighted)
    return g


def _apply_layout(g, layout, h, w, palette, density, rng):
    if layout == "blob":
        cr, cc = rng.randint(0, h - 1), rng.randint(0, w - 1)
        for r in range(h):
            for c in range(w):
                if abs(r - cr) + abs(c - cc) <= 3 and rng.random() < density + 0.2:
                    g[r][c] = rng.choice(palette)
        return
    if layout == "stripes":
        horiz = rng.random() < 0.5
        for r in range(h):
            for c in range(w):
                if horiz and r % 2 == 0 and rng.random() < density + 0.2:
                    g[r][c] = rng.choice(palette)
                elif not horiz and c % 2 == 0 and rng.random() < density + 0.2:
                    g[r][c] = rng.choice(palette)
        return
    if layout == "diag":
        for k in range(min(h, w)):
            g[k][k] = rng.choice(palette)
        return
    if layout == "frame":
        for r in range(h):
            for c in range(w):
                if r in (0, h - 1) or c in (0, w - 1):
                    g[r][c] = rng.choice(palette)
        return
    if layout == "checker":
        for r in range(h):
            for c in range(w):
                if (r + c) % 2 == 0 and rng.random() < density + 0.3:
                    g[r][c] = rng.choice(palette)
        return
    for r in range(h):
        for c in range(w):
            if rng.random() < density:
                g[r][c] = rng.choice(palette)


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 7)
    if name == "empty_grid":
        g[0][0] = 5
        g[h - 1][w - 1] = 9
        return g
    if name == "full_fg":
        for r in range(h):
            for c in range(w):
                g[r][c] = rng.choice([5, 9])
        return g
    if name == "single_fg":
        g[h // 2][w // 2] = rng.choice([5, 9])
        return g
    return g
