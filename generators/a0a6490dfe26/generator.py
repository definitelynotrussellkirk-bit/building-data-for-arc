"""Generator for arc_puzzle_bank_sixteenth_21_bundle:hard_106 — transform×recolor cross-product gallery.

Rule (verified from canonical Racket): column 0 at rows 1,3,5 holds three TRANSFORM
codes (1=id,2=cw,3=180,4=ccw,5=flip-lr,6=flip-ud,7=transpose); row 0 at cols 1,3,5
holds three COLOR codes; a 3x3 PROTOTYPE sits at rows 4-6, cols 4-6. The output is
an 11x11 grid: for each (i,j) the prototype is transformed by transform-code i and
recoloured to colour-code j, placed at (4i, 4j) — a 3x3 cross-product gallery.

The previous body was the generic scatter template; it did not lay out the codes /
prototype at the fixed positions, so the prototype was usually empty and the output
barely varied (distinct_out=2). This rewrite CONSTRUCTS the exact 7x7 layout: three
transform codes, three colour codes, and a non-empty 3x3 prototype.

Axes: the three transform codes, the three colour codes, the prototype pattern.
Degenerates: empty_proto, single_transform, single_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a0a6490dfe26"
VERSION = "2.2.0"  # shape-locked in+out: input fixed 7x7. Output is rule-intrinsic 11x11 (hardcoded empty-grid 11 11) -> out-shape blocked. Rule reads fixed cells (codes col0/row0) + subgrid rows4-6/cols4-6 and ignores the rest, so pad the input below/right with bg to lift the input shape-lock."
TASK_ID = "a0a6490dfe26"

SUMMARY = ("A 7x7 input: col 0 (rows 1,3,5) = 3 transform codes, row 0 (cols 1,3,5) = 3 colour "
           "codes, rows 4-6/cols 4-6 = a 3x3 prototype. The rule builds an 11x11 cross-product "
           "gallery (transform i x colour j of the prototype). Codes and prototype vary.")

INVARIANTS = [
    "transform codes at (1,0),(3,0),(5,0) in 1..7",
    "colour codes at (0,1),(0,3),(0,5) in 1..9",
    "a non-empty 3x3 prototype at rows 4-6, cols 4-6",
]

DEGENERATE_TEXTURES = ("empty_proto", "single_transform", "single_color")
HELPFUL_TEXTURES = ("default", "warm", "cool", "varied")

AXES = {
    "proto_k":    {"type": "int", "default": "rng 3..7 prototype cells", "valid": "1..9"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "default|warm|cool|varied"},
    "density":    {"type": "str", "default": "fixed 7x7", "valid": "fixed"},
    "texture":    {"type": "str", "default": "alias for palette_kind",
                   "valid": "default|warm|cool|varied|empty_proto|single_transform|single_color"},
}


def _layout(transforms, colors, proto_cells, proto_color):
    g = full_grid(7, 7, 0)
    for r, code in zip((1, 3, 5), transforms):
        g[r][0] = code
    for c, col in zip((1, 3, 5), colors):
        g[0][c] = col
    for (r, c) in proto_cells:               # 3x3 prototype at rows 4-6, cols 4-6
        g[4 + r][4 + c] = proto_color
    return g



def _norm_cells(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def _transform_cells(cells, code):
    pts = list(cells)
    if code == 1:
        out = pts
    elif code == 2:  # rotate cw in 3x3 frame
        out = [(c, 2 - r) for r, c in pts]
    elif code == 3:
        out = [(2 - r, 2 - c) for r, c in pts]
    elif code == 4:
        out = [(2 - c, r) for r, c in pts]
    elif code == 5:
        out = [(r, 2 - c) for r, c in pts]
    elif code == 6:
        out = [(2 - r, c) for r, c in pts]
    elif code == 7:
        out = [(c, r) for r, c in pts]
    else:
        out = pts
    return _norm_cells(out)


def _variant_signatures(proto_cells, transforms):
    return {_transform_cells(proto_cells, t) for t in transforms}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        k = ctx.draw_int("proto_k", 2, 4); pr_hi, pc_hi = 2, 2
    elif difficulty == "hard":
        k = ctx.draw_int("proto_k", 5, 7); pr_hi, pc_hi = 10, 10
    else:
        k = ctx.draw_int("proto_k", 3, 6); pr_hi, pc_hi = 0, 6
    rng = ctx.draw_rng("layout")

    # Use distinct transform codes by default.  The `single_transform` texture is
    # the explicit degenerate; leaking all-equal transform rows in normal samples
    # hides the transform axis.
    transforms = rng.sample([1, 2, 3, 4, 5, 6, 7], 3)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 3)
    spots = [(r, c) for r in range(3) for c in range(3)]
    want = max(1, min(k, 9))
    for _ in range(80):
        proto_cells = rng.sample(spots, want)
        if len(_variant_signatures(proto_cells, transforms)) >= 2:
            break
    else:
        proto_cells = [(0, 0), (1, 0), (1, 1)]
    proto_color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    g = _layout(transforms, colors, proto_cells, proto_color)
    # Output is always 11x11 (rule-intrinsic). Pad the 7x7 input below/right with
    # bg to vary the INPUT shape — the rule reads only fixed cells + subgrid
    # rows4-6/cols4-6, so the extra cells are ignored.
    er = ctx.draw_int("pad_r", 0, pr_hi); ec = ctx.draw_int("pad_c", 0, pc_hi)
    if er or ec:
        g = [row + [0] * ec for row in g] + [[0] * (7 + ec) for _ in range(er)]
    return g


def _draw_from_degenerate(name, rng):
    proto = [(0, 0), (0, 1), (1, 1), (2, 0)]
    if name == "empty_proto":
        return _layout([1, 2, 3], [4, 5, 6], [], 7)        # no prototype -> blank output
    if name == "single_transform":
        return _layout([1, 1, 1], [4, 5, 6], proto, 7)     # all rows identical transform
    return _layout([1, 2, 3], [4, 4, 4], proto, 7)         # single_color -> all cols same colour



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or len(grid) < 7 or len(grid[0]) < 7:
        return ["grid must include the 7x7 code/prototype frame"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    transforms = [grid[1][0], grid[3][0], grid[5][0]]
    colors = [grid[0][1], grid[0][3], grid[0][5]]
    if any(t not in range(1, 8) for t in transforms):
        errs.append(f"transform codes must be in 1..7, got {transforms}")
    if len(set(transforms)) < 2:
        errs.append(f"normal samples must exercise at least two transform branches, got {transforms}")
    if any(c not in range(1, 10) for c in colors):
        errs.append(f"color codes must be in 1..9, got {colors}")
    if len(set(colors)) != 3:
        errs.append(f"expected three distinct color codes, got {colors}")
    proto = [(r, c) for r in range(3) for c in range(3) if grid[4 + r][4 + c] != 0]
    if not proto:
        errs.append("prototype must be non-empty")
    elif len(_variant_signatures(proto, transforms)) < 2:
        errs.append("prototype is symmetric under the sampled transforms, hiding the transform axis")
    # Padding below/right is allowed, but it must be ignored 0-bg.
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            in_frame = r < 7 and c < 7
            if not in_frame and v != 0:
                errs.append("padding outside the canonical 7x7 frame must remain 0")
                return errs
    return errs
