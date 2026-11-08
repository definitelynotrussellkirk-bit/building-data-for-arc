"""Generator for 42f14c03.

Rule: hollow 3x3 template frame has one one-cell filler whose area
exactly matches the hole.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors,
filler_color.
Degenerates: no_template, no_filler, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_frame

GENERATOR_ID = "ce7050977ab7"
VERSION = "2.1.1"  # severe mismatch: canonical is a 'pack fillers into a template object's bbox holes' rule (output=template bbox, varied/non-square), but the gen made a FIXED 7x8 with a 3x3 frame + one 1-cell filler -> output always 3x3 (dup 44%, shape-locked in+out). Output is DERIVED by running the rule, so construct real instances: a hollow FRAME template (varied dims; hole=interior) + filler solid-rectangles whose total area == the hole, placed as separate objects on varied grids. Output = template bbox (varied, non-square)."
TASK_ID = "ce7050977ab7"
SUMMARY = ("A hollow rectangular frame is the template; several smaller solid "
           "rectangles are fillers whose total area equals the frame's interior. "
           "Output is the frame's bbox with the fillers packed into the hole.")

INVARIANTS = [
    "background is the most common color (0)",
    "the largest object is a hollow rectangular frame (template)",
    "filler solid-rectangles have total area equal to the frame interior",
    "every object is separated so they are distinct components",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_template", "no_filler", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 14..20", "valid": "10..26"},
    "grid_w":         {"type": "int", "default": "rng 14..20", "valid": "10..26"},
    "frame_h":        {"type": "int", "default": "rng 4..8", "valid": "3..10"},
    "frame_w":        {"type": "int", "default": "rng 4..8", "valid": "3..10"},
    "n_fillers":      {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "varied", "valid": "varied"},
    "position_bias":  {"type": "str", "default": "free", "valid": "free"},
    "n_distinct_colors":{"type": "int", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; all values 0-9; grid is rectangular."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("cell value out of 0-9")
    return errs


def _place_rect(g, rh, rw, color, rng):
    """Place a solid rh x rw rectangle on a free patch (1-cell ring gap so it
    stays a distinct component). Returns True on success."""
    h, w = len(g), len(g[0])
    if rh > h or rw > w:
        return False
    for _ in range(300):
        r0 = rng.randint(0, h - rh); c0 = rng.randint(0, w - rw)
        ok = True
        for r in range(max(0, r0 - 1), min(h, r0 + rh + 1)):
            for c in range(max(0, c0 - 1), min(w, c0 + rw + 1)):
                if g[r][c] != 0:
                    ok = False; break
            if not ok:
                break
        if not ok:
            continue
        for r in range(r0, r0 + rh):
            for c in range(c0, c0 + rw):
                g[r][c] = color
        return True
    return False


def _place_frame(g, fh, fw, color, rng):
    """Place a hollow fh x fw frame (outline) on a free patch. Returns (r0,c0) or None."""
    h, w = len(g), len(g[0])
    for _ in range(300):
        r0 = rng.randint(0, h - fh); c0 = rng.randint(0, w - fw)
        ok = True
        for r in range(max(0, r0 - 1), min(h, r0 + fh + 1)):
            for c in range(max(0, c0 - 1), min(w, c0 + fw + 1)):
                if g[r][c] != 0:
                    ok = False; break
            if not ok:
                break
        if not ok:
            continue
        draw_frame(g, r0, c0, r0 + fh - 1, c0 + fw - 1, color)
        return (r0, c0)
    return None


def _draw_guaranteed_instance(h, w, fh, fw, bands, tmpl_color, filler_colors):
    """Place the template and every filler deterministically with no silent degradation.

    The old stochastic placement could fail to find room for a full filler band
    and degraded to a 1x1 blob, breaking the core invariant that filler area
    exactly equals the frame interior. This layout grows the canvas as needed and
    places fillers in a separated column to the right of the template.
    """
    int_w = fw - 2
    filler_h = sum(bands) + max(0, len(bands) - 1)
    h = max(h, fh + 2, filler_h + 2)
    w = max(w, fw + int_w + 4)
    g = full_grid(h, w, 0)
    draw_frame(g, 1, 1, fh, fw, tmpl_color)
    r0 = 1
    c0 = fw + 2
    for band_h, col in zip(bands, filler_colors):
        for r in range(r0, r0 + band_h):
            for c in range(c0, c0 + int_w):
                g[r][c] = col
        r0 += band_h + 1
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        fh = ctx.draw_int("frame_h", 4, 5); fw = ctx.draw_int("frame_w", 4, 6)
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 12, 16)
        nf_max = 2
    elif difficulty == "hard":
        fh = ctx.draw_int("frame_h", 6, 10); fw = ctx.draw_int("frame_w", 6, 10)
        h = ctx.draw_int("grid_h", 18, 26); w = ctx.draw_int("grid_w", 18, 26)
        nf_max = 4
    else:
        fh = ctx.draw_int("frame_h", 4, 8); fw = ctx.draw_int("frame_w", 5, 9)
        h = ctx.draw_int("grid_h", 14, 20); w = ctx.draw_int("grid_w", 14, 20)
        nf_max = 3
    int_h = fh - 2; int_w = fw - 2                # interior (hole) rectangle
    perimeter = 2 * fh + 2 * fw - 4
    # split the interior rows into bands -> each band is one solid-rect filler whose
    # area stays < perimeter (so the frame is the largest object = the template).
    nf = ctx.draw_int("n_fillers", 1, nf_max)
    nf = max(1, min(nf, int_h))
    # increase nf (smaller bands) until each band's area < perimeter, so the
    # hollow frame stays the LARGEST object (the rule's template).
    def _max_band_area(k):
        return (-(-int_h // k)) * int_w           # ceil(int_h/k) * int_w
    while nf < int_h and _max_band_area(nf) >= perimeter:
        nf += 1
    # contiguous band heights summing to int_h
    base = int_h // nf; extra = int_h % nf
    bands = [base + (1 if i < extra else 0) for i in range(nf)]
    bands = [b for b in bands if b > 0]
    colors = list(ctx.draw_distinct_colors("colors", n=1 + len(bands), exclude={0}))
    tmpl_color = colors[0]; filler_colors = colors[1:]
    return _draw_guaranteed_instance(h, w, fh, fw, bands, tmpl_color, filler_colors)


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 8, 0)
    if name == "no_template":
        g[5][5] = 4
        return g
    if name == "no_filler":
        draw_frame(g, 1, 1, 3, 3, 3)
        return g
    if name == "full_grid":
        for r in range(7):
            for c in range(8):
                g[r][c] = 3
        return g
    return g
