"""Generator for arc_additional_puzzle_bank_volume7:H45.

Rule: two maroon-anchored source shapes are XORed by relative offsets
and stamped at the cyan target anchor.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_anchors, no_shapes, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "109a03554ed3"
VERSION = "2.1.0"  # enforce nonempty, in-bounds, visible XOR stamp at the cyan anchor.
TASK_ID = "109a03554ed3"
SUMMARY = (
    "0-bg grid (h~10-15, w~"
    "12-17) with: (a) ONE "
    "RED (COLOR-2) SHAPE of "
    "2-4 cells with ONE "
    "MAROON (COLOR-9) "
    "ANCHOR cell embedded; "
    "(b) ONE BLUE (COLOR-1) "
    "SHAPE of 2-4 cells "
    "with its OWN MAROON "
    "ANCHOR; (c) ONE CYAN "
    "(COLOR-8) TARGET cell "
    "at a clear non-adjacent "
    "position. All shapes "
    "placed with 1-cell "
    "padding. Rule (XOR OF "
    "RED AND BLUE SHAPES, "
    "STAMPED AT CYAN "
    "ANCHOR, COLOR 3): "
    "identify the RED SHAPE "
    "and its 9-anchor; the "
    "BLUE SHAPE and its 9-"
    "anchor. NORMALIZE each "
    "shape by its 9-anchor "
    "(offsets relative to "
    "anchor). COMPUTE the "
    "SYMMETRIC DIFFERENCE "
    "(XOR) of the offset "
    "sets — cells in red OR "
    "blue but NOT BOTH. "
    "STAMP the XOR offsets "
    "centered at the CYAN "
    "anchor in COLOR-3 "
    "(green). Source shapes "
    "and cyan stay or are "
    "task-specific. Net: "
    "asymmetric XOR of two "
    "anchored shapes paints "
    "in green at cyan "
    "target."
)

# Rivals: 'paint the union' refuted by ≥1 demo where overlap cells are
# absent. 'paint just one shape' refuted by ≥2 demos with cells from
# both. 'use source colors' refuted by any demo (output is 3).
# 'stamp at maroon anchor instead of cyan' refuted by ≥1 demo.
# 4 demos with varied shapes + anchors cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "one red component includes a maroon anchor",
    "one blue component includes a separate maroon anchor",
    "a cyan target cell provides the new anchor",
    "the anchored symmetric difference is nonempty and in-bounds",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_anchors", "no_shapes", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..14", "valid": "8..24"},
    "grid_w":         {"type": "int", "default": "rng 12..17", "valid": "10..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "true",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "4", "valid": "4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
        shape_size_lo, shape_size_hi = 2, 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18)
        w = ctx.draw_int("grid_w", 16, 20)
        shape_size_lo, shape_size_hi = 3, 5
    else:
        h = ctx.draw_int("grid_h", 11, 15)
        w = ctx.draw_int("grid_w", 13, 17)
        shape_size_lo, shape_size_hi = 2, 4
    def make_shape(n):
        cells = [(0, 0)]; seen = {(0, 0)}
        while len(cells) < n:
            r, c = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nr, nc = r + dr, c + dc
            if (nr, nc) not in seen:
                cells.append((nr, nc)); seen.add((nr, nc))
        return cells

    def place_anchored(g, placed_bboxes, color):
        for _ in range(60):
            cells = make_shape(rng.randint(shape_size_lo, shape_size_hi))
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            if sh > h - 2 or sw > w - 2:
                continue
            r0 = rng.randint(0, h - sh)
            c0 = rng.randint(0, w - sw)
            bbox = (r0 - 1, c0 - 1, r0 + sh, c0 + sw)
            if any(not (b[2] < bbox[0] or b[0] > bbox[2] or
                        b[3] < bbox[1] or b[1] > bbox[3])
                   for b in placed_bboxes):
                continue
            anchor_r, anchor_c = rng.choice(cells)
            abs_cells = [(r0 + r - min(rs), c0 + c - min(cs)) for r, c in cells]
            anchor = (r0 + anchor_r - min(rs), c0 + anchor_c - min(cs))
            color_cells = [p for p in abs_cells if p != anchor]
            for r, c in color_cells:
                g[r][c] = color
            g[anchor[0]][anchor[1]] = 9
            placed_bboxes.append(bbox)
            offsets = {(r - anchor[0], c - anchor[1]) for r, c in color_cells}
            return offsets
        return None

    for _outer in range(80):
        g = full_grid(h, w, 0)
        placed_bboxes = []
        red_offsets = place_anchored(g, placed_bboxes, 2)
        if red_offsets is None:
            continue
        blue_offsets = place_anchored(g, placed_bboxes, 1)
        if blue_offsets is None:
            continue
        xor_offsets = red_offsets ^ blue_offsets
        if not xor_offsets:
            continue
        # Place cyan(8) anchor only where the full XOR stamp is in-bounds and
        # still empty.  Otherwise the demo hides the branch via clipping or
        # overwriting source cells.
        candidates = []
        for cr in range(h):
            for cc in range(w):
                if g[cr][cc] != 0:
                    continue
                if any(0 <= cr + dr < h and 0 <= cc + dc < w
                       and g[cr + dr][cc + dc] != 0
                       for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))):
                    continue
                targets = [(cr + dr, cc + dc) for dr, dc in xor_offsets]
                if any(not (0 <= r < h and 0 <= c < w) for r, c in targets):
                    continue
                if any(g[r][c] != 0 for r, c in targets):
                    continue
                candidates.append((cr, cc))
        if not candidates:
            continue
        cr, cc = rng.choice(candidates)
        g[cr][cc] = 8
        return g
    raise ValueError("could not realize anchored XOR-stamp layout")


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 13, 0)
    if name == "no_anchors":
        g[2][3] = 2
        g[3][2] = 2
        g[5][5] = 8
        return g
    if name == "no_shapes":
        g[2][2] = 9
        g[7][8] = 9
        g[5][5] = 8
        return g
    if name == "full_grid":
        for r in range(11):
            for c in range(13):
                g[r][c] = 8
        return g
    return g


def _positions(g, color):
    return [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == color]


def _flood_union(g, start, allowed):
    h = len(g)
    w = len(g[0]) if h else 0
    seen = {start}
    stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                    and g[nr][nc] in allowed):
                seen.add((nr, nc))
                stack.append((nr, nc))
    return seen


def _anchored_offsets(g, color):
    comps = []
    for anchor in _positions(g, 9):
        comp = _flood_union(g, anchor, {color, 9})
        if any(g[r][c] == color for r, c in comp):
            comps.append(comp)
    uniq = []
    for comp in comps:
        if comp not in uniq:
            uniq.append(comp)
    if len(uniq) != 1:
        return None
    anchors = [(r, c) for r, c in uniq[0] if g[r][c] == 9]
    if len(anchors) != 1:
        return None
    ar, ac = anchors[0]
    return {(r - ar, c - ac) for r, c in uniq[0] if g[r][c] == color}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    if len(_positions(grid, 9)) != 2:
        errors.append(f"expected two maroon anchors, found {len(_positions(grid, 9))}")
    target = _positions(grid, 8)
    if len(target) != 1:
        errors.append(f"expected one cyan target anchor, found {len(target)}")
    red = _anchored_offsets(grid, 2)
    blue = _anchored_offsets(grid, 1)
    if red is None:
        errors.append("red source is not one anchored component")
    if blue is None:
        errors.append("blue source is not one anchored component")
    if red is not None and blue is not None and len(target) == 1:
        xor_offsets = red ^ blue
        if not xor_offsets:
            errors.append("anchored red/blue symmetric difference is empty")
        tr, tc = target[0]
        for dr, dc in xor_offsets:
            rr, cc = tr + dr, tc + dc
            if not (0 <= rr < h and 0 <= cc < w):
                errors.append("XOR stamp target goes out of bounds")
                break
            if grid[rr][cc] != 0:
                errors.append("XOR stamp target is already nonzero in input")
                break
    return errors
