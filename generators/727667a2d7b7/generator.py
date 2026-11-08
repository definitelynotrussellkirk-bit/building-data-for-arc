"""Generator for arc_additional_puzzle_bank_volume6:M40.

Rule: each blue object rotates inside its local box according to the
marker value above it (1=identity, 2=cw90, 3=180, 4=ccw90).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_objects,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_marker, marker_zero, marker_misaligned.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "727667a2d7b7"
VERSION = "2.1.0"  # identity fix: code-1 / rotation-symmetric (square, 180-sym) objects left the grid unchanged. Now simulate the rule and require >=1 object to visibly rotate; retry + guaranteed non-identity fallback.
TASK_ID = "727667a2d7b7"
SUMMARY = (
    "0-bg grid (h, w~10-22) containing 1-5 "
    "COLOR-6 (magenta) OBJECTS — each a small "
    "polyomino (3-4 cells from a shape bank: "
    "L, corner, T, S, square, L-tet, J, T-rot). "
    "Each object is placed at some interior "
    "position with sufficient padding for "
    "rotation to stay in-bounds. Each object "
    "has a SINGLE CONTROL CELL placed exactly "
    "ONE ROW ABOVE its bbox TOP-LEFT (at "
    "(r0-1, c0)) with VALUE ∈ {1, 2, 3, 4} "
    "(the rotation code: 1=identity, 2=cw90, "
    "3=180°, 4=ccw90). Objects + their "
    "controls are mutually padded. Rule: for "
    "EACH magenta object, READ its control "
    "value at (r0-1, c0). ROTATE the object's "
    "normalized shape IN PLACE within its "
    "local bbox by the control code "
    "(1=identity, 2=cw90, 3=180°, 4=ccw90). "
    "The object stays color 6; the control "
    "stays in place. Net: each magenta "
    "polyomino rotates by its overhead "
    "control's quarter-turn count."
)

# Rivals: 'identity (no rotation)' refuted by ≥2 demos with non-1
# markers. 'rotate by fixed direction' refuted by ≥2 demos with
# different markers producing different rotations. 'use marker color
# for object' refuted by any demo (object stays 6). 'erase marker'
# OK; marker is read-only.
# 4 demos with varied shapes + codes cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "blue objects are separated and have square local boxes",
    "each blue object has a control value immediately above its bbox top-left",
    "controls use values 1 through 4",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "marker_zero", "marker_misaligned")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..14", "valid": "8..24"},
    "grid_w":         {"type": "int", "default": "rng 10..14", "valid": "8..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_objects":      {"type": "int", "default": "2", "valid": "2..3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..5"},
    "position_bias":  {"type": "str", "default": "spread_corners",
                       "valid": "spread_corners"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..5"},
    "density":        {"type": "str", "default": "low", "valid": "low"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("placement")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 9, 12)
        n_objs = rng.randint(1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 15, 22)
        w = ctx.draw_int("grid_w", 15, 22)
        n_objs = rng.randint(3, 5)
    else:
        h = ctx.draw_int("grid_h", 11, 16)
        w = ctx.draw_int("grid_w", 11, 16)
        n_objs = rng.randint(2, 4)
    # The rule rotates each 6-object by its overhead code. If EVERY object's
    # rotation is a no-op (code 1, or a rotation-symmetric shape like the
    # square / 180-symmetric S) the grid is unchanged -> identity demo. Build,
    # then validate (via a faithful Python simulation of the rule) that at least
    # one object visibly rotates; retry, with a guaranteed non-identity fallback.
    for _ in range(40):
        g = full_grid(h, w, 0)
        placed_bboxes = []  # (r1, c1, r2, c2) with marker-row padding
        for _ in range(n_objs * 6):
            if len(placed_bboxes) >= n_objs:
                break
            shape = rng.choice(_SHAPES)
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            # Need at least 1 row above for the marker
            if h <= sh + 1 or w <= sw:
                continue
            r0 = rng.randint(1, h - sh)
            c0 = rng.randint(0, w - sw)
            bbox = (r0 - 2, c0 - 1, r0 + sh, c0 + sw)
            # Non-overlap (with padding)
            if any(not (b[2] < bbox[0] or b[0] > bbox[2] or
                        b[3] < bbox[1] or b[1] > bbox[3])
                   for b in placed_bboxes):
                continue
            # Marker at (r0 - 1, c0); must be in-bounds and bg.
            if g[r0 - 1][c0] != 0:
                continue
            code = rng.randint(1, 4)
            g[r0 - 1][c0] = code
            for dr, dc in shape:
                g[r0 + dr][c0 + dc] = 6
            placed_bboxes.append(bbox)
        out, ok = _apply_rule(g)
        if placed_bboxes and ok and out != g:
            return g
    return _fallback_grid(h, w)


# Random shape bank (module-level so helpers + self_check share it).
_SHAPES = [
    [(0, 0), (0, 1), (1, 0), (2, 0)],          # L
    [(0, 0), (1, 0), (1, 1)],                  # corner
    [(0, 0), (0, 1), (0, 2), (1, 1)],          # T
    [(0, 0), (1, 0), (1, 1), (2, 1)],          # S
    [(0, 0), (0, 1), (1, 0), (1, 1)],          # square
    [(0, 0), (1, 0), (2, 0), (2, 1)],          # L-tet
    [(0, 0), (0, 1), (0, 2), (1, 0)],          # J
    [(0, 1), (1, 0), (1, 1), (1, 2)],          # T-rot
]


def _normalize(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _rot(cells, code, hh, ww):
    """Match the rule: 1=identity, 2=cw90, 3=180, else(4)=ccw90."""
    if code == 1:
        out = list(cells)
    elif code == 2:
        out = [(c, hh - 1 - r) for r, c in cells]
    elif code == 3:
        out = [(hh - 1 - r, ww - 1 - c) for r, c in cells]
    else:
        out = [(ww - 1 - c, r) for r, c in cells]
    return _normalize(out)


def _apply_rule(g):
    """Faithful simulation of the canonical rule -> (output_grid, in_bounds_ok)."""
    h = len(g); w = len(g[0])
    seen = set(); comps = []
    for sr in range(h):
        for sc in range(w):
            if g[sr][sc] == 6 and (sr, sc) not in seen:
                comp = []; stack = [(sr, sc)]; seen.add((sr, sc))
                while stack:
                    r, c = stack.pop(); comp.append((r, c))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = r + dr, c + dc
                        if (0 <= nr < h and 0 <= nc < w and g[nr][nc] == 6
                                and (nr, nc) not in seen):
                            seen.add((nr, nc)); stack.append((nr, nc))
                comps.append(comp)
    out = [row[:] for row in g]
    for comp in comps:
        r0 = min(r for r, _ in comp); c0 = min(c for _, c in comp)
        code = g[r0 - 1][c0] if r0 - 1 >= 0 else 0
        norm = _normalize(comp)
        hh = max(r for r, _ in norm) + 1; ww = max(c for _, c in norm) + 1
        tshape = _rot(norm, code if code in (1, 2, 3) else 4, hh, ww)
        for (r, c) in comp:
            out[r][c] = 0
        for (pr, pc) in tshape:
            rr, cc = r0 + pr, c0 + pc
            if not (0 <= rr < h and 0 <= cc < w):
                return out, False
            out[rr][cc] = 6
    return out, True


def _fallback_grid(h, w):
    """Guaranteed non-identity instance: one L-tromino with a cw90 control."""
    g = full_grid(h, w, 0)
    g[2][3] = 2                                   # control code 2 at (r0-1, c0)
    for dr, dc in [(0, 0), (0, 1), (1, 0), (2, 0)]:
        g[3 + dr][3 + dc] = 6
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """At least one color-6 object must visibly rotate under its overhead code,
    else the rule is a no-op (identity demo)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if not any(v == 6 for row in grid for v in row):
        return ["no color-6 object to rotate"]
    out, ok = _apply_rule(grid)
    if not ok:
        return ["a rotated object falls out of bounds"]
    if out == grid:
        return ["no object visibly rotates: rule is a no-op"]
    return []


def _draw_from_degenerate(name, rng):
    h, w = 12, 12
    g = full_grid(h, w, 0)
    if name == "no_marker":
        # blue object with no control value above → rotation undefined
        for dr, dc in [(0, 0), (0, 1), (1, 0), (2, 0)]:
            g[3 + dr][2 + dc] = 6
        for dr, dc in [(0, 0), (0, 1), (1, 0), (2, 0)]:
            g[3 + dr][8 + dc] = 6
        return g
    if name == "marker_zero":
        # marker value of 0 (background) → not a valid control code
        g[2][2] = 0
        for dr, dc in [(0, 0), (0, 1), (1, 0), (2, 0)]:
            g[3 + dr][2 + dc] = 6
        return g
    if name == "marker_misaligned":
        # marker not directly above the object's bbox top-left → matching fails
        g[2][5] = 3
        for dr, dc in [(0, 0), (0, 1), (1, 0), (2, 0)]:
            g[3 + dr][2 + dc] = 6
        return g
    return g
