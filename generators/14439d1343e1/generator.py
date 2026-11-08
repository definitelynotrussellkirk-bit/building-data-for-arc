"""Generator for 5117e062 -- crop the 8-marked shape, fill the 8 with its color.

Rule: find the color-8 cell; its first non-{0,8} orthogonal neighbor gives the
shape color X. Take the bbox of all X cells plus the 8, crop it, and output
the shape with the 8 cell turned into X (everything else 0).

This generator draws one color-X polyomino with a single cell replaced by 8,
plus distractor shapes of other colors.

Combinatorial axes: grid size, the shape, which cell is the 8, distractors,
colors and positions.
Degenerates: shape_only, single_cell, two_shapes.

NOTE: the output is the cropped shape, so its size is bounded; distinct
INPUTS are large and outputs track the shape variety.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "14439d1343e1"
VERSION = "2.1.1"  # diversity: color-X polyomino w/ one 8-cell + distractors (was ~32)
TASK_ID = "14439d1343e1"
SUMMARY = (
    "0-bg grid (size varies) with one color-X shape (one cell replaced by 8) "
    "and distractor shapes of other colors. Rule: crop the X-shape's bbox "
    "(including the 8) and output it with the 8 filled in as X. The grid size, "
    "shape, 8-cell, distractors and positions vary freely (was a fixed setup, "
    "~32 distinct). Output is the cropped shape, so bounded; inputs are large."
)

INVARIANTS = [
    "exactly one color-8 cell, replacing a cell of the X shape",
    "the 8 is orthogonally adjacent to an X cell (so X is recovered)",
    "the output is the X-shape cropped with the 8 filled as X",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("shape_only", "single_cell", "two_shapes")
HELPFUL_TEXTURES = PALETTE_KINDS

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_COLORS = [1, 2, 3, 4, 5, 6, 7, 9]

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..23"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..23"},
    "shape_size":     {"type": "int", "default": "varies", "valid": "4..11"},
    "n_distract":     {"type": "int", "default": "varies", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|shape_only|single_cell|two_shapes"},
}


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return _norm(cells)


def _reserve(occ, top, left, sh, sw, h, w, margin=1):
    for r in range(top - margin, top + sh + margin):
        for c in range(left - margin, left + sw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + sh):
        for c in range(left, left + sw):
            occ[r][c] = True
    return True


def _place(rng, occ, sh, sw, h, w):
    for _t in range(30):
        top = rng.randint(0, h - sh); left = rng.randint(0, w - sw)
        if _reserve(occ, top, left, sh, sw, h, w):
            return top, left
    return None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly one color-8 cell; adjacent non-bg cells exist."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    eights = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if not eights:
        return errors  # degenerate (shape_only) — allowed
    if len(eights) != 1:
        errors.append(f"expected exactly 1 color-8 cell, got {len(eights)}")
    else:
        r8, c8 = eights[0]
        # The 8 should be adjacent to an X-color cell
        nbrs = [(r8 + dr, c8 + dc) for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))]
        adj = [grid[nr][nc] for nr, nc in nbrs if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] not in (0, 8)]
        if not adj:
            errors.append("color-8 cell has no adjacent X-color neighbor")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, dr_, sr = (12, 15), (12, 16), (1, 2), (4, 7)
    elif difficulty == "hard":
        hr, wr, dr_, sr = (17, 23), (17, 23), (2, 3), (7, 11)
    else:
        hr, wr, dr_, sr = (14, 19), (14, 19), (1, 3), (5, 9)

    for _attempt in range(40):
        shape = _poly(rng, rng.randint(*sr))
        sh = max(r for r, c in shape) + 1; sw = max(c for r, c in shape) + 1
        h = rng.randint(*hr); w = rng.randint(*wr)
        occ = [[False] * w for _ in range(h)]
        pos = _place(rng, occ, sh, sw, h, w)
        if pos is None:
            continue
        top, left = pos
        x = rng.choice(_COLORS)
        g = full_grid(h, w, 0)
        cells = [(top + r, left + c) for r, c in shape]
        for (r, c) in cells:
            g[r][c] = x
        # one cell -> 8 (must keep an orthogonal X neighbor: pick a non-isolated cell)
        cellset = set(cells)
        cand = [(r, c) for (r, c) in cells
                if any((r + dr, c + dc) in cellset for dr, dc in _CARD)]
        er, ec = rng.choice(cand)
        g[er][ec] = 8

        # distractors of OTHER colors (not x, not 8), away from the shape
        for _ in range(rng.randint(*dr_)):
            d = _poly(rng, rng.randint(2, 6))
            dh = max(r for r, c in d) + 1; dw = max(c for r, c in d) + 1
            dpos = _place(rng, occ, dh, dw, h, w)
            if dpos:
                dc_ = rng.choice([col for col in _COLORS if col != x])
                for (r, c) in d:
                    g[dpos[0] + r][dpos[1] + c] = dc_
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    shape = [(0, 0), (0, 1), (1, 0), (1, 1)]
    for (r, c) in shape:
        g[2 + r][2 + c] = 3
    g[2][2] = 8
    if name == "two_shapes":
        for (r, c) in [(7, 8), (7, 9)]:
            g[r][c] = 5
    if name == "single_cell":
        g2 = full_grid(h, w, 0); g2[3][3] = 4; g2[3][4] = 8
        return g2
    return g
