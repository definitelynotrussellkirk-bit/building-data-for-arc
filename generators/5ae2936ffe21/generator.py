"""Generator for puzzle 445eab21.

Rule: find largest non-bg object (by cell count); output a 2 × 2 grid
filled with its color.

Combinatorial axes: grid_h/w, n_objects, object_kind, size_progression,
placement, palette_distinctness. Degenerates: ties_for_largest,
single_object, all_same_size.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect

GENERATOR_ID = "5ae2936ffe21"
VERSION = "2.1.0"
TASK_ID = "5ae2936ffe21"
SUMMARY = (
    "0-bg grid (h, w~10-20) with 2-4 "
    "OBJECTS of strictly distinct sizes, "
    "each in a DISTINCT color drawn from "
    "1..9. Object kinds from "
    "{rect, L_shape, cross, blob, "
    "line_h, line_v}; size progression "
    "linear or exponential; placement "
    "random/corners/row/column. Object "
    "sizes ascending; LARGEST object is "
    "unique (no ties). Rule (LARGEST → "
    "2×2 COLOR OUTPUT): identify the "
    "LARGEST non-bg connected component "
    "(by cell count). EMIT a 2×2 "
    "OUTPUT GRID with every cell painted "
    "in the LARGEST OBJECT'S COLOR. "
    "Output dimensions are always 2×2; "
    "diversity is intrinsic-low (one "
    "shape per color, 9 colors total). "
    "Net: input has 2-4 differently-"
    "sized objects; output is a tiny "
    "2×2 patch of the largest one's "
    "color."
)

INVARIANTS = [
    "background is 0",
    "≥2 non-bg objects with strictly distinct sizes",
    "largest object is unique",
]

OBJECT_KINDS = ("rect", "L_shape", "cross", "blob", "line_h", "line_v")
SIZE_PROGRESSIONS = ("linear", "exponential")
PLACEMENTS = ("random", "corners", "row", "column")
DEGENERATE_TEXTURES = ("ties_for_largest", "single_object", "all_same_size")
HELPFUL_TEXTURES = OBJECT_KINDS

AXES = {
    "grid_h":           {"type": "int", "default": "rng 10..20", "valid": "8..25"},
    "grid_w":           {"type": "int", "default": "rng 10..20", "valid": "8..25"},
    "n_objects":        {"type": "int", "default": "rng 2..4", "valid": "2..6"},
    "object_kind":      {"type": "str", "default": "rng helpful",
                         "valid": "|".join(OBJECT_KINDS)},
    "size_progression": {"type": "str", "default": "rng linear|exponential",
                         "valid": "|".join(SIZE_PROGRESSIONS)},
    "placement":        {"type": "str", "default": "rng helpful",
                         "valid": "|".join(PLACEMENTS)},
    "texture":          {"type": "str", "default": "alias for object_kind",
                         "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, n_lo, n_hi = 10, 13, 2, 2
    elif difficulty == "hard":
        h_lo, h_hi, n_lo, n_hi = 17, 20, 3, 4
    else:
        h_lo, h_hi, n_lo, n_hi = 10, 20, 2, 4
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, ctx, rng)
    n_obj = int(overrides.get("n_objects", ctx.draw_int("n_objects", n_lo, n_hi)))
    n_obj = max(2, min(6, n_obj))
    kind = (overrides.get("texture") or overrides.get("object_kind")
            or ctx.draw_choice("object_kind", list(OBJECT_KINDS)))
    progression = overrides.get("size_progression",
                                ctx.draw_choice("size_progression", list(SIZE_PROGRESSIONS)))
    placement = overrides.get("placement",
                              ctx.draw_choice("placement", list(PLACEMENTS)))
    palette = list(ctx.draw_distinct_colors("palette", n=max(2, n_obj), exclude={0}))
    sizes = _make_sizes(n_obj, progression, rng)  # ascending bbox scale
    # Earlier versions drew smaller objects as rectangles but drew only the last
    # object with the selected `kind`.  For line/L/cross kinds the intended
    # largest object could therefore tie or lose by CELL COUNT to a smaller
    # rectangle (e.g. 2x2 rect area 4 vs length-4 line area 4), hiding the
    # largest-component rule.  Use one morphology across all objects so the
    # actual connected-component sizes remain strictly increasing with scale.
    for _board_attempt in range(80):
        g = full_grid(h, w, 0)
        anchors = _anchors(placement, h, w, n_obj, rng)
        placed = 0
        for i, ((ar, ac), size) in enumerate(zip(anchors, sizes)):
            for _ in range(30):
                sh = max(2, size); sw = max(2, size)
                if 0 <= ar <= h - sh and 0 <= ac <= w - sw and _check_clear(g, ar, ac, sh, sw):
                    _paint_kind(g, kind, ar, ac, sh, sw, palette[i], rng)
                    placed += 1
                    break
                ar = rng.randint(0, max(0, h - sh))
                ac = rng.randint(0, max(0, w - sw))
        if placed == n_obj:
            return g

    # Fail closed with a simple, valid two-object board instead of emitting
    # [[0]], which creates a malformed no-object training example.
    return _fallback_valid_board(max(h, 8), max(w, 8), palette[0], palette[1])


def _make_sizes(n, progression, rng):
    if progression == "linear":
        base = rng.randint(2, 3)
        return [base + i for i in range(n)]
    return [2 + 2 ** i for i in range(n)]


def _anchors(placement, h, w, n, rng):
    margin = 1
    if placement == "corners":
        cands = [(margin, margin), (margin, w - margin - 6),
                 (h - margin - 6, margin), (h - margin - 6, w - margin - 6)]
        return cands[:n]
    if placement == "row":
        gap = max(1, (w - 2 * margin) // max(1, n))
        return [(rng.randint(margin, h // 2), margin + i * gap) for i in range(n)]
    if placement == "column":
        gap = max(1, (h - 2 * margin) // max(1, n))
        return [(margin + i * gap, rng.randint(margin, w // 2)) for i in range(n)]
    return [(rng.randint(margin, max(margin, h - 7)),
             rng.randint(margin, max(margin, w - 7))) for _ in range(n)]


def _check_clear(g, rr, rc, sh, sw):
    for r in range(max(0, rr - 1), min(len(g), rr + sh + 1)):
        for c in range(max(0, rc - 1), min(len(g[0]), rc + sw + 1)):
            if g[r][c] != 0:
                return False
    return True


def _paint_kind(g, kind, rr, rc, sh, sw, color, rng):
    if kind == "rect":
        for dr in range(sh):
            for dc in range(sw):
                g[rr + dr][rc + dc] = color
    elif kind == "L_shape":
        for dr in range(sh):
            g[rr + dr][rc] = color
        for dc in range(sw):
            g[rr + sh - 1][rc + dc] = color
    elif kind == "cross":
        mr, mc = sh // 2, sw // 2
        for dc in range(sw):
            g[rr + mr][rc + dc] = color
        for dr in range(sh):
            g[rr + dr][rc + mc] = color
    elif kind == "blob":
        for dr in range(sh):
            for dc in range(sw):
                g[rr + dr][rc + dc] = color
    elif kind == "line_h":
        for dc in range(sw):
            g[rr][rc + dc] = color
    elif kind == "line_v":
        for dr in range(sh):
            g[rr + dr][rc] = color
    else:
        for dr in range(sh):
            for dc in range(sw):
                g[rr + dr][rc + dc] = color


def _fallback_valid_board(h, w, color_a, color_b):
    g = full_grid(h, w, 0)
    draw_rect(g, 1, 1, 2, 2, color_a)
    draw_rect(g, 4, 4, 3, 3, color_b)
    return g


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    colors = {v for row in grid for v in row}
    if not colors <= set(range(10)):
        errs.append("grid contains non-ARC color")
    comps = _components(grid)
    if len(comps) < 2:
        errs.append(f"expected at least two non-bg objects, got {len(comps)}")
        return errs
    comp_colors = [color for color, _cells in comps]
    if len(set(comp_colors)) != len(comp_colors):
        errs.append("object colors are not distinct")
    sizes = [len(cells) for _color, cells in comps]
    if len(set(sizes)) != len(sizes):
        errs.append(f"object sizes are not strictly distinct: {sorted(sizes)}")
    if sizes.count(max(sizes)) != 1:
        errs.append("largest object is not unique")
    return errs


def _draw_from_degenerate(name, h, w, ctx, rng):
    g = full_grid(h, w, 0)
    palette = list(ctx.draw_distinct_colors("palette", n=4, exclude={0}))
    if name == "ties_for_largest":
        s = 4
        draw_rect(g, 1, 1, s, s, palette[0])
        draw_rect(g, 1, w - s - 1, s, s, palette[1])
        draw_rect(g, h - 3, max(1, w // 2 - 1), 2, 2, palette[2])
        return g
    if name == "single_object":
        s = rng.randint(3, 6)
        draw_rect(g, 1, 1, s, s, palette[0])
        return g
    if name == "all_same_size":
        s = 3
        anchors = [(1, 1), (1, w - s - 1), (h - s - 1, 1), (h - s - 1, w - s - 1)]
        for i, (r, c) in enumerate(anchors[:4]):
            draw_rect(g, r, c, s, s, palette[i % len(palette)])
        return g
    return g
