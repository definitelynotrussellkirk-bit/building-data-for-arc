"""Generator for v0_original:hard_04 — slide the shape to the marker.

Rule (re-derived; the old "6 panels, find pair" summary was WRONG): there is one
single-cell MARKER and one multi-cell SHAPE. The marker lies outside the shape's
bounding box along one axis. SLIDE the shape toward the marker along that axis
until the shape is adjacent to the marker (its leading edge one cell short of the
marker). OUTPUT a blank grid holding the marker (at its original spot) and the
moved shape.

v2.1.0 drew 9-divider panels with motifs — but the rule reads color-9 dividers as
shapes/objects, so it mis-modelled the task. v3.0.0 builds exactly one shape + one
marker with a gap, and a Python mirror of the slide gates that the shape actually
moves and stays in-bounds.

Combinatorial axes: grid size, shape (size/shape/color), marker color, slide
direction and distance.
Degenerates: no_dividers, empty_panels, single_panel (kept as edge inputs).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f869ac2ae3e4"
VERSION = "3.0.0"  # match the real rule: slide the multi-cell shape to the single marker (was a wrong 'find pair across panels')
TASK_ID = "f869ac2ae3e4"

SUMMARY = (
    "0-bg grid (size varies) with ONE single-cell MARKER and ONE connected "
    "multi-cell SHAPE (distinct non-0 colors). The marker sits beyond the "
    "shape's bounding box along one axis, with a gap. Rule: locate the size-1 "
    "marker and the larger shape; SLIDE the shape toward the marker along the "
    "axis where the marker is outside the shape's bbox, until the shape's "
    "leading edge is one cell short of the marker. OUTPUT a blank grid with the "
    "marker at its original position and the shape at its slid position. Net: "
    "the shape moves to dock against the marker. (Was mis-modelled as panels.)"
)

INVARIANTS = [
    "exactly one single-cell marker and one connected multi-cell shape",
    "the marker is outside the shape's bbox along one axis, with a >=1 cell gap",
    "marker and shape use distinct non-0 colors",
    "after sliding, the shape stays in bounds and docks adjacent to the marker",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dividers", "empty_panels", "single_panel")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "8-12 easy / 11-16 med / 14-22 hard", "valid": "5..24"},
    "grid_w":         {"type": "int", "default": "8-12 easy / 11-16 med / 14-22 hard", "valid": "5..24"},
    "shape_size":     {"type": "int", "default": "2-4 easy / 3-6 med / 4-8 hard", "valid": "2..8"},
    "palette_kind":   {"type": "str", "default": "rng helpful", "valid": "|".join(PALETTE_KINDS)},
    "direction":      {"type": "str", "default": "rng up|down|left|right", "valid": "up|down|left|right"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "shape_plus_marker", "valid": "shape_plus_marker"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_CARD = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _rand_poly(rng, size, maxdim=4):
    for _ in range(40):
        cells = {(0, 0)}; frontier = [(0, 0)]
        while len(cells) < size and frontier:
            cr, cc = rng.choice(frontier)
            opts = [(cr + dr, cc + dc) for dr, dc in _CARD if (cr + dr, cc + dc) not in cells]
            if not opts:
                frontier.remove((cr, cc)); continue
            nc = rng.choice(opts); cells.add(nc); frontier.append(nc)
        mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
        norm = sorted((r - mr, c - mc) for r, c in cells)
        if (len(norm) == size and max(r for r, _ in norm) + 1 <= maxdim
                and max(c for _, c in norm) + 1 <= maxdim):
            return norm
    return [(0, 0), (0, 1)]


def _slide(cells, mr, mc):
    """Mirror of the rule: (dr, dc) to slide `cells` toward marker (mr,mc)."""
    r0 = min(r for r, _ in cells); r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells); c1 = max(c for _, c in cells)
    if mc > c1:
        dc = (mc - 1) - c1
    elif mc < c0:
        dc = (mc + 1) - c0
    else:
        dc = 0
    if dc != 0:
        dr = 0
    elif mr > r1:
        dr = (mr - 1) - r1
    elif mr < r0:
        dr = (mr + 1) - r0
    else:
        dr = 0
    return dr, dc


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        hr, wr, sr = (8, 12), (8, 12), (2, 4)
    elif difficulty == "hard":
        hr, wr, sr = (14, 22), (14, 22), (4, 8)
    else:
        hr, wr, sr = (11, 16), (11, 16), (3, 6)
    rng = ctx.draw_rng("layout")

    for _attempt in range(60):
        h = rng.randint(*hr); w = rng.randint(*wr)
        shape = _rand_poly(rng, rng.randint(*sr))
        sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
        if sh >= h - 1 or sw >= w - 1:
            continue
        # place shape with room to slide
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        cells = [(r0 + dr, c0 + dc) for dr, dc in shape]
        rr0, rr1 = r0, r0 + sh - 1
        cc0, cc1 = c0, c0 + sw - 1
        scol, mcol = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2)
        direction = overrides.get("direction") or rng.choice(["up", "down", "left", "right"])

        # marker beyond bbox in `direction` with a gap >=1
        if direction == "right":
            if cc1 + 2 > w - 1:
                continue
            mc = rng.randint(cc1 + 2, w - 1); mr = rng.randint(rr0, rr1)
        elif direction == "left":
            if cc0 - 2 < 0:
                continue
            mc = rng.randint(0, cc0 - 2); mr = rng.randint(rr0, rr1)
        elif direction == "down":
            if rr1 + 2 > h - 1:
                continue
            mr = rng.randint(rr1 + 2, h - 1); mc = rng.randint(cc0, cc1)
        else:  # up
            if rr0 - 2 < 0:
                continue
            mr = rng.randint(0, rr0 - 2); mc = rng.randint(cc0, cc1)

        if (mr, mc) in cells:
            continue
        dr, dc = _slide(cells, mr, mc)
        if (dr, dc) == (0, 0):
            continue
        moved = [(r + dr, c + dc) for r, c in cells]
        if any(not (0 <= r < h and 0 <= c < w) for r, c in moved):
            continue
        if (mr, mc) in moved:
            continue
        g = full_grid(h, w, 0)
        for r, c in cells:
            g[r][c] = scol
        g[mr][mc] = mcol
        return g

    # deterministic fallback: a 2-cell shape sliding right to a marker
    g = full_grid(8, 10, 0)
    g[3][1] = 2; g[3][2] = 2
    g[3][7] = 4
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(6, 10, 0)
    if name == "no_dividers":
        g[2][1] = 2; g[2][2] = 2; g[2][6] = 4
        return g
    if name == "empty_panels":
        g[1][1] = 4
        return g
    if name == "single_panel":
        g[2][2] = 2; g[2][3] = 2
        return g
    return g


def _sc_color_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    comps = _sc_color_components(grid)
    if len(comps) != 2:
        errors.append(f"expected exactly one shape and one marker, got {len(comps)} components")
        return errors
    singles = [(color, cells) for color, cells in comps if len(cells) == 1]
    shapes = [(color, cells) for color, cells in comps if len(cells) > 1]
    if len(singles) != 1 or len(shapes) != 1:
        errors.append("expected one singleton marker and one multi-cell shape")
        return errors
    (_mcolor, marker_cells), (_scolor, shape_cells) = singles[0], shapes[0]
    mr, mc = marker_cells[0]
    r0, r1 = min(r for r, _ in shape_cells), max(r for r, _ in shape_cells)
    c0, c1 = min(c for _, c in shape_cells), max(c for _, c in shape_cells)
    outside_h = mc < c0 - 1 or mc > c1 + 1
    outside_v = mr < r0 - 1 or mr > r1 + 1
    if outside_h == outside_v:
        errors.append("marker must be outside the shape bbox along exactly one axis with a gap")
    dr, dc = _slide(shape_cells, mr, mc)
    if (dr, dc) == (0, 0):
        errors.append("shape must slide a nonzero distance toward the marker")
    h, w = len(grid), len(grid[0])
    moved = [(r + dr, c + dc) for r, c in shape_cells]
    if any(not (0 <= r < h and 0 <= c < w) for r, c in moved):
        errors.append("slid shape must stay in bounds")
    if (mr, mc) in moved:
        errors.append("slid shape must dock next to, not overlap, the marker")
    return errors
