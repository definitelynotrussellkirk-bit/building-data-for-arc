"""Generator for arc_puzzle_bank_21_set23_s:S23_H1 — 2x3 grid of panels separated by 9-walls.

Rule: a 2-row x N-col panel lattice separated by full color-9 row/col walls.
The query = the 3rd top-row panel; rotate its occupancy CW; the output is a
1xN one-hot marking which BOTTOM-row panel's occupancy equals that rotation.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_separators, empty_panels, all_identical.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2e5bdf4f77a3"
VERSION = "3.0.1"  # distinct=1 (BROKEN): random motifs everywhere -> a candidate rarely matched the rotated query (empty-panel match -> always idx 0). Now CONSTRUCT the match: query occupancy at 3rd top panel, its CW-rotation placed at a chosen bottom index; N columns + square panels.
TASK_ID = "2e5bdf4f77a3"

SUMMARY = (
    "A 2-row x N-col (N=3-6) lattice of square p x p PANELS separated by "
    "full color-9 row/col dividers. The QUERY is the 3rd top-row panel. The "
    "match is CONSTRUCTED: one bottom-row panel (a chosen index) carries the "
    "CW-rotation of the query's occupancy; the others are random non-matching "
    "occupancies. Rule: rotate the query CW and output a 1xN one-hot of which "
    "bottom panel matches. Output is intrinsically a length-N one-hot."
)

INVARIANTS = [
    "background is 0; 2 x N panels separated by full color-9 row/col dividers",
    "exactly one bottom-row panel matches the CW-rotated query (at a varied index)",
    "the other bottom panels have non-matching occupancies",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_separators", "empty_panels", "all_identical")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_h":        {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "panel_w":        {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "2x3_panel_lattice",
                       "valid": "2x3_panel_lattice"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: has color-9 cells (panel dividers), has non-{0,9} panel cells."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    nines = sum(grid[r][c] == 9 for r in range(h) for c in range(w))
    if nines == 0:
        errs.append("no color-9 divider cells found")
    panel_cells = sum(grid[r][c] not in (0, 9) for r in range(h) for c in range(w))
    if panel_cells == 0:
        errs.append("no panel cells (non-{0,9}) found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    # Rule: query = 3rd top-row panel; target = rotate-CW its occupancy; output =
    # one-hot of which BOTTOM-row panel's occupancy equals target. Was random
    # motifs everywhere (a match was accidental -> distinct=1). Now CONSTRUCT the
    # match at a chosen index, with SQUARE panels (so rotation fits) + N columns.
    if difficulty == "easy":
        p = 3; n = rng.randint(3, 4)
    elif difficulty == "hard":
        p = rng.randint(4, 5); n = rng.randint(3, 5)
    else:
        p = rng.randint(3, 4); n = rng.randint(3, 6)   # output 1xN one-hot -> bigger N = more distinct
    H = 2 * p + 1
    W = n * p + (n - 1)
    g = full_grid(H, W, 0)
    for c in range(W):
        g[p][c] = 9                                   # full-width row divider
    for k in range(1, n):
        col = k * p + (k - 1)
        for r in range(H):
            g[r][col] = 9                             # full-height col dividers
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
    qocc = _rand_occ(rng, p)                          # query occupancy (3rd top panel)
    target = _rot_cw(qocc)                            # the rule rotates it CW
    match_idx = rng.randint(0, n - 1)

    def _paint(occ, row, jcol):
        r0 = row * (p + 1); c0 = jcol * (p + 1)
        for r in range(p):
            for c in range(p):
                if occ[r][c]:
                    g[r0 + r][c0 + c] = color
    for j in range(n):
        _paint(qocc if j == 2 else _rand_occ(rng, p), 0, j)   # top row (query at j=2)
        if j == match_idx:
            bot = target
        else:
            bot = _rand_occ(rng, p)
            tries = 0
            while bot == target and tries < 30:
                bot = _rand_occ(rng, p); tries += 1
        _paint(bot, 1, j)                              # bottom row (candidates)
    return g


def _rand_occ(rng, p):
    """Random p x p binary occupancy with 1..p*p-1 cells."""
    while True:
        occ = [[1 if rng.random() < 0.4 else 0 for _ in range(p)] for _ in range(p)]
        s = sum(sum(row) for row in occ)
        if 1 <= s <= p * p - 1:
            return occ


def _rot_cw(occ):
    """90-degree clockwise rotation of a p x p binary grid."""
    p = len(occ)
    return [[occ[p - 1 - c][r] for c in range(p)] for r in range(p)]


def _draw_from_degenerate(name, rng):
    panel_h = 3; panel_w = 3
    h = panel_h * 2 + 1
    w = panel_w * 3 + 2
    g = full_grid(h, w, 0)
    if name == "no_separators":
        # Motifs but no 9-dividers — rule's panel decomposition
        # fails.
        g[1][1] = 4; g[1][5] = 4; g[1][9] = 4
        g[5][1] = 4; g[5][5] = 4; g[5][9] = 4
        return g
    div_r = panel_h
    for c in range(w): g[div_r][c] = 9
    for k in range(1, 3):
        col = panel_w * k + (k - 1)
        for r in range(h): g[r][col] = 9
    if name == "empty_panels":
        # Separators but no motifs in any panel — rule has no
        # shapes to compare.
        return g
    if name == "all_identical":
        # All 6 panels have identical motif — rule's matching
        # selector finds no unique target.
        for pr in range(2):
            for pc in range(3):
                r0 = pr * (panel_h + 1)
                c0 = pc * (panel_w + 1)
                g[r0][c0] = 4; g[r0 + 1][c0] = 4; g[r0 + 1][c0 + 1] = 4
        return g
    return g
