"""Generator for arc_puzzle_bank_21_set12_bundle:easy_l04.

Rule: for each filled (solid) rectangle with both dims odd, paint
output cross: middle row of bbox + middle col of bbox in the obj's
color (on a fresh empty grid).

Combinatorial axes (8): grid_h, grid_w, palette_kind, rect_dims,
palette_size, position_bias, n_distinct_colors, n_rects, texture.
Degenerates: even_dim_rect, no_rects, hollow_rect.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect
from puzzle_generators.helpers.selfcheck import components, components_have_clearance

GENERATOR_ID = "e4cb0224ca42"
VERSION = "3.0.1"  # add executable self_check + align declared axes/docs with v3 multi-rect generation.
TASK_ID = "e4cb0224ca42"
SUMMARY = (
    "0-bg grid (h ∈ 7-9, w ∈ 9-11) with: "
    "1-3 SOLID RECTANGLES, each rh × rw "
    "where BOTH dimensions are ODD "
    "(rh, rw drawn from {3, 5, 7}) — so "
    "each rectangle has a well-defined "
    "CENTER ROW and CENTER COLUMN. "
    "Each rect painted in a DISTINCT "
    "non-bg color drawn from "
    "{2,3,4,5,6,7,8,9}, placed at a "
    "random non-touching position via "
    "draw_rect, with a one-cell moat "
    "between rectangles. "
    "Rule (FOR EACH SOLID ODD×ODD "
    "RECTANGLE, PROJECT A CROSS — "
    "THE MIDDLE ROW AND MIDDLE "
    "COLUMN OF THE BBOX — IN THE "
    "RECT'S COLOR, ON A FRESH "
    "SAME-SIZE EMPTY GRID): "
    "PRODUCE a fresh same-size grid "
    "of 0s. For EACH solid rect "
    "with both dims odd at "
    "bbox (rmin, cmin, rmax, "
    "cmax) with color k: COMPUTE "
    "middle row mr = (rmin + "
    "rmax) // 2 and middle col mc "
    "= (cmin + cmax) // 2. PAINT "
    "every cell in ROW mr (cols "
    "cmin..cmax) and every cell "
    "in COL mc (rows rmin..rmax) "
    "with color k. Net: each "
    "odd×odd rect becomes a "
    "color-k cross on a fresh "
    "canvas; the rest of each "
    "rect's bbox stays 0."
)

INVARIANTS = [
    "1-3 solid rectangles, each with odd width AND odd height in {3,5,7}",
    "rectangles do not touch, including diagonally",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("even_dim_rect", "no_rects", "hollow_rect")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "rect_dims":      {"type": "str", "default": "odd_3_5_or_7", "valid": "odd_3_5_or_7"},
    "palette_size":   {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "position_bias":  {"type": "str", "default": "interior", "valid": "interior"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "n_rects":        {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 11)
        n_rects = ctx.draw_int("n_rects", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 12, 16)
        n_rects = ctx.draw_int("n_rects", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 10, 13)
        n_rects = ctx.draw_int("n_rects", 1, 3)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    pal = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], n_rects)
    placed = 0
    for _ in range(400):
        if placed >= n_rects:
            break
        rh = rng.choice([d for d in (3, 5, 7) if d <= h])
        rw = rng.choice([d for d in (3, 5, 7) if d <= w])
        r0 = rng.randint(0, h - rh)
        c0 = rng.randint(0, w - rw)
        if not _free(g, r0, c0, r0 + rh - 1, c0 + rw - 1):
            continue
        draw_rect(g, r0, c0, rh, rw, pal[placed])
        placed += 1
    if placed == 0:
        draw_rect(g, 0, 0, 3, 3, pal[0])
    return g


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0:
                return False
    return True



def _is_solid_odd_rect(comp):
    cells = set(comp["cells"])
    r1, c1, r2, c2 = comp["bbox"]
    rh, rw = r2 - r1 + 1, c2 - c1 + 1
    if rh not in (3, 5, 7) or rw not in (3, 5, 7):
        return False, f"bbox dims must be odd and in {{3,5,7}}, got {rh}x{rw}"
    want = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}
    if cells != want:
        return False, "component is not a solid filled rectangle"
    return True, ""


def self_check(grid, *, difficulty=None, meta=None):
    """Executable input invariants for the normal generator path.

    The canonical rule extracts every odd×odd solid rectangle and projects its
    bbox middle row/column. These checks catch regressions that would hide the
    rule (no usable rectangles, even/hollow rectangles) or make the demos
    ambiguous (touching/overlapping rectangles or reused colors).
    """
    errs = []
    comps = components(grid, same_color=True, connectivity=8)
    if not (1 <= len(comps) <= 3):
        errs.append(f"expected 1-3 nonzero rectangle components, found {len(comps)}")
        return errs
    colors = [comp["color"] for comp in comps]
    if len(set(colors)) != len(colors):
        errs.append(f"rectangle colors must be distinct, got {colors}")
    if not components_have_clearance(grid, comps, diagonal=True):
        errs.append("rectangles touch or overlap; expected one-cell moat")
    for i, comp in enumerate(comps):
        ok, why = _is_solid_odd_rect(comp)
        if not ok:
            errs.append(f"component {i} color={comp['color']}: {why}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "even_dim_rect":
        # solid rect with an even dimension → "middle" cell is undefined
        draw_rect(g, 1, 1, 4, 4, 4)
        return g
    if name == "no_rects":
        # empty grid — no rectangles to project crosses from
        return g
    if name == "hollow_rect":
        # outline only — predicate "solid rect" fails
        for c in range(1, 6):
            g[1][c] = 4; g[3][c] = 4
        for r in range(1, 4):
            g[r][1] = 4; g[r][5] = 4
        return g
    return g
