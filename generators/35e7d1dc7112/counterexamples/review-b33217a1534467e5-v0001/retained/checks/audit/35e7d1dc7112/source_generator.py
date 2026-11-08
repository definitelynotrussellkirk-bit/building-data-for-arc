"""Generator for e8dc4411 -- march-stamp a 0-shape away from a marker.

Rule: background is the mode color. The 0-cells form a SHAPE; its bbox center
is the origin. A single marker (non-bg, non-0) at offset (dr,dc) defines a
direction (the signs of dr,dc) and a step magnitude (manhattan distance minus
one). The shape is stamped in the marker's color at center + k*step for
k=1,2,... until no stamp cell is in bounds.

This generator draws a 0-shape, then one marker at manhattan distance >= 2
(so the step is non-zero and the march terminates).

Combinatorial axes: grid size, the 0-shape, the marker direction/distance,
the background and marker colors.
Degenerates: axis_only, diagonal, far_marker.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "35e7d1dc7112"
VERSION = "2.1.0"  # +self_check  # diversity: 0-shape + direction marker -> march stamp (was 28)
TASK_ID = "35e7d1dc7112"
SUMMARY = (
    "Mode-bg grid (size varies) with a 0-cell SHAPE and one marker. Rule: the "
    "marker's offset from the shape center sets a direction and step "
    "(manhattan-1); the shape is stamped in the marker's color marching away "
    "from center until off-grid. The grid size, shape, marker "
    "direction/distance and colors vary freely (was a fixed setup, ~28 "
    "distinct)."
)

INVARIANTS = [
    "background is the strict mode color; the shape is made of 0-cells",
    "exactly one marker (non-bg, non-0) at manhattan distance >= 2 from center",
    "the shape is march-stamped in the marker color until off-grid",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("axis_only", "diagonal", "far_marker")
HELPFUL_TEXTURES = PALETTE_KINDS

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "13..24"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "13..24"},
    "shape_size":     {"type": "int", "default": "varies", "valid": "2..6"},
    "marker_dist":    {"type": "int", "default": "varies", "valid": "2..6"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "center_shape", "valid": "center_shape"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|axis_only|diagonal|far_marker"},
}


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg is mode color, ≥1 shape (0-cell cluster) present, ≥1 marker cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    flat = [v for row in grid for v in row]
    if not flat:
        return ["empty grid"]
    # bg is the mode color (most frequent)
    from collections import Counter
    counts = Counter(flat)
    bg = counts.most_common(1)[0][0]
    has_shape = 0 in flat  # shape is 0-cells
    if not has_shape:
        errs.append("no zero-cells found (shape should be 0-cells on a non-zero bg)")
    non_bg_non_zero = [v for v in flat if v != bg and v != 0]
    if not non_bg_non_zero:
        errs.append("no marker cell (non-bg, non-0) found")
        return errs

    zeros = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 0]
    zrs = [r for r, _ in zeros]
    zcs = [c for _, c in zeros]
    center_r = (min(zrs) + max(zrs)) // 2
    center_c = (min(zcs) + max(zcs)) // 2
    marker = None
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v != bg and v != 0:
                marker = (r, c, v)
                break
        if marker is not None:
            break
    mr, mc, _mcolor = marker
    dr = mr - center_r
    dc = mc - center_c
    step_mag = abs(dr) + abs(dc) - 1
    step_r = step_mag * ((dr > 0) - (dr < 0))
    step_c = step_mag * ((dc > 0) - (dc < 0))
    first_stamp = [(r + step_r, c + step_c) for r, c in zeros]
    h, w = len(grid), len(grid[0])
    if not any(0 <= r < h and 0 <= c < w and (r, c) != (mr, mc)
               for r, c in first_stamp):
        errs.append("first march stamp is invisible/out of bounds")
    return errs


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return _norm(cells)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"])

    if difficulty == "easy":
        hr, wr, sr, dr_ = (13, 16), (13, 16), (2, 4), (2, 4)
    elif difficulty == "hard":
        hr, wr, sr, dr_ = (20, 24), (20, 24), (4, 6), (2, 6)
    else:
        hr, wr, sr, dr_ = (15, 20), (15, 20), (3, 5), (2, 5)

    bg = rng.randint(1, 9)
    mcolor = rng.choice([c for c in range(1, 10) if c != bg])

    for _attempt in range(40):
        h = rng.randint(*hr); w = rng.randint(*wr)
        shape = _poly(rng, rng.randint(*sr))
        sh = max(r for r, c in shape) + 1; sw = max(c for r, c in shape) + 1
        # place the shape roughly central
        top = rng.randint(2, h - sh - 2); left = rng.randint(2, w - sw - 2)
        zeros = [(top + r, left + c) for r, c in shape]
        zr = [r for r, c in zeros]; zc = [c for r, c in zeros]
        center_r = (min(zr) + max(zr)) // 2
        center_c = (min(zc) + max(zc)) // 2

        # marker offset: cardinal or diagonal, manhattan >= 2
        kind = rng.choice(["axis", "diag"])
        if kind == "axis":
            sgn = rng.choice([-1, 1]); D = rng.randint(*dr_)
            if rng.random() < 0.5:
                dr, dc = sgn * D, 0
            else:
                dr, dc = 0, sgn * D
        else:
            a = rng.randint(1, max(1, dr_[1] // 2 + 1))
            dr = rng.choice([-1, 1]) * a; dc = rng.choice([-1, 1]) * a
        if abs(dr) + abs(dc) < 2:
            continue
        mr = center_r + dr; mc = center_c + dc
        if not (0 <= mr < h and 0 <= mc < w):
            continue
        if (mr, mc) in set(zeros):
            continue

        step_mag = abs(dr) + abs(dc) - 1
        step_r = step_mag * ((dr > 0) - (dr < 0))
        step_c = step_mag * ((dc > 0) - (dc < 0))
        first_stamp = [(r + step_r, c + step_c) for r, c in zeros]
        # The first march step must demonstrate the transformation.  Otherwise
        # the canonical rule can be a no-op because the shifted shape is already
        # entirely out of bounds.
        if not any(0 <= r < h and 0 <= c < w and (r, c) != (mr, mc)
                   for r, c in first_stamp):
            continue

        g = full_grid(h, w, bg)
        for (r, c) in zeros:
            g[r][c] = 0
        g[mr][mc] = mcolor
        return g

    # Safe fallback: central 0-shape, marker far enough to create visible stamps.
    h = w = 15
    bg = 5
    mcolor = 2
    g = full_grid(h, w, bg)
    for (r, c) in [(7, 7), (7, 8), (8, 7)]:
        g[r][c] = 0
    g[7][4] = mcolor
    return g


def _draw_from_degenerate(name):
    h, w = 15, 15
    g = full_grid(h, w, 5)
    for (r, c) in [(7, 7), (7, 8), (8, 7)]:
        g[r][c] = 0
    if name == "diagonal":
        g[5][5] = 2
    elif name == "far_marker":
        g[13][7] = 2
    else:  # axis_only
        g[7][11] = 2
    return g
