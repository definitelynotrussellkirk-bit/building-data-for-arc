"""Generator for arc_puzzle_bank_next21:M11 — paste largest obj at color-9 marker.

Rule: find the largest non-9 component and a color-9 marker. Output places
the component's relative cells at the marker position (using bbox top-left as anchor).

Combinatorial axes (8): grid_h, grid_w, palette_kind, motif_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_marker, no_motif, marker_inside_motif.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "16a08856ef47"
VERSION = "1.2.1"  # guard marker-quadrant randint vs oversized motif span (randrange(3,3))
TASK_ID = "16a08856ef47"

SUMMARY = "1 connected motif in some non-9 color + 1 single-cell color-9 marker."

INVARIANTS = [
    "background is 0",
    "exactly one connected motif (3-5 cells) in some non-{0, 9} color",
    "exactly one color-9 single-cell marker",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "no_motif", "marker_inside_motif")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "5..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "motif_size":     {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "motif_upper_left_marker_lower_right",
                       "valid": "motif_upper_left_marker_lower_right"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_marker|no_motif|marker_inside_motif"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one color-9 marker and at least one non-{0,9} motif cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in ("no_marker", "no_motif", "marker_inside_motif"):
        return errs
    nines = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    motif = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 9)]
    if len(nines) != 1:
        errs.append(f"expected exactly one color-9 marker, got {len(nines)}")
    if not motif:
        errs.append("no motif cells (non-0, non-9)")
    return errs


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 7, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
    else:
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 7, 9)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
        cells = _build_motif(rng, rng.randint(3, 5))
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
        placed_m = False
        for _ in range(80):
            r0 = rng.randint(0, max(0, h // 2 - sh))
            c0 = rng.randint(0, max(0, w // 2 - sw))
            if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
            for r, c in cells:
                g[r0 + r - min(rs)][c0 + c - min(cs)] = color
            placed_m = True; break
        if not placed_m:
            continue
        # The marker sits in the lower-right quadrant and anchors a paste of the
        # motif, so it needs mr ∈ [h//2, h-sh] and mc ∈ [w//2, w-sw]. A motif
        # whose span sh/sw exceeds the quadrant depth (h-sh < h//2 — e.g. a 5-cell
        # vertical line on the hard h=7 grid, or sh=4 on the easy h=6 grid)
        # inverts the randint → randrange(3,3) empty-range crash BEFORE the outer
        # loop can retry. Redraw a smaller motif on the next outer attempt instead
        # of raising: the motif draw already happened, so every non-oversized seed
        # keeps the identical flow (byte-identical); only oversized-motif seeds
        # retry. Inverse-range class — object-overflows-quadrant variant.
        if h - sh < h // 2 or w - sw < w // 2:
            continue
        for _ in range(80):
            mr = rng.randint(h // 2, h - sh)
            mc = rng.randint(w // 2, w - sw)
            if g[mr][mc] != 0: continue
            ok = all(0 <= mr + r - min(rs) < h and 0 <= mc + c - min(cs) < w
                     and g[mr + r - min(rs)][mc + c - min(cs)] == 0 for r, c in cells)
            if not ok: continue
            g[mr][mc] = 9
            return g
    raise ValueError("could not realize M11 layout")


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "no_marker":
        # motif present but no 9-marker → no destination, rule has no anchor
        for (r, c) in [(1, 1), (1, 2), (2, 1)]: g[r][c] = 4
        return g
    if name == "no_motif":
        # 9-marker present but no source motif → rule has nothing to copy
        g[5][6] = 9
        return g
    if name == "marker_inside_motif":
        # 9-marker overlaps a motif cell → ambiguous, paste position equals motif position
        for (r, c) in [(2, 2), (2, 3), (3, 2)]: g[r][c] = 4
        g[2][2] = 9  # overrides motif cell
        return g
    return g
