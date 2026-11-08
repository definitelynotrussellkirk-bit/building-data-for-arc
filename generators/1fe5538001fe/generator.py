"""Generator for v1_e_m_h_keys:H6 — complete the missing mirrored quadrant.

Rule: the grid is split into 4 quadrants by a central separator row
(h//2) and column (w//2). Exactly ONE quadrant is all-zero (missing);
the rule fills it by mirroring a filled "source" quadrant (flip-ud if
their rows differ, flip-lr if their cols differ). Output: the completed
4-quadrant mirror-symmetric grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1fe5538001fe"
VERSION = "3.0.1"


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: central row and col are all-0; exactly one quadrant is all-zero."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
        return errs
    mid_r, mid_c = h // 2, w // 2
    if not all(grid[mid_r][c] == 0 for c in range(w)):
        errs.append(f"central row {mid_r} is not all-zero")
    if not all(grid[r][mid_c] == 0 for r in range(h)):
        errs.append(f"central col {mid_c} is not all-zero")
    if errs:
        return errs
    quadrants = [
        [(r, c) for r in range(mid_r) for c in range(mid_c)],
        [(r, c) for r in range(mid_r) for c in range(mid_c + 1, w)],
        [(r, c) for r in range(mid_r + 1, h) for c in range(mid_c)],
        [(r, c) for r in range(mid_r + 1, h) for c in range(mid_c + 1, w)],
    ]
    zero_quads = [i for i, q in enumerate(quadrants)
                  if q and all(grid[r][c] == 0 for r, c in q)]
    if len(zero_quads) != 1:
        errs.append(f"expected exactly 1 all-zero quadrant, got {len(zero_quads)}: {zero_quads}")
    return errs
TASK_ID = "1fe5538001fe"

SUMMARY = (
    "0-bg grid with ODD h,w (~7-13) split into 4 quadrants by a central "
    "all-0 separator row (h//2) and column (w//2). A random connected "
    "blob (2-5 cells) in one non-bg colour is placed in one quadrant and "
    "its flip-lr / flip-ud / 180 mirrors in the others, then EXACTLY ONE "
    "quadrant is erased (all-zero = 'missing'). Rule: find the missing "
    "(all-zero) quadrant and a filled source quadrant; mirror the source "
    "into the missing slot (flip-ud across the row split, flip-lr across "
    "the col split). Output: the completed mirror-symmetric grid."
)

INVARIANTS = [
    "background is 0",
    "central separator row (h//2) and column (w//2) are all 0",
    "exactly one quadrant is all-zero (the missing one); >=1 other is filled",
    "filled quadrants are mirror images of one base blob",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_missing", "all_missing", "single_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng odd 7..13", "valid": "7..15"},
    "grid_w":         {"type": "int", "default": "rng odd 7..13", "valid": "7..17"},
    "blob_size":      {"type": "int", "default": "rng 2..5", "valid": "1..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "four_quadrant_mirror",
                       "valid": "four_quadrant_mirror"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_missing|all_missing|single_filled"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_NONBG = [2, 3, 4, 5, 6, 7, 8, 9]


def _blob(rng, qh, qw, k):
    """A connected k-cell blob within a qh x qw quadrant."""
    k = max(1, min(k, qh * qw))
    start = (rng.randint(0, qh - 1), rng.randint(0, qw - 1))
    cells = [start]; seen = {start}
    tries = 0
    while len(cells) < k and tries < 200:
        tries += 1
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nr, nc = r + dr, c + dc
        if 0 <= nr < qh and 0 <= nc < qw and (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_choice("grid_h", [7, 9]); w = ctx.draw_choice("grid_w", [7, 9])
    elif difficulty == "hard":
        h = ctx.draw_choice("grid_h", [11, 13]); w = ctx.draw_choice("grid_w", [13, 15])
    else:
        h = ctx.draw_choice("grid_h", [7, 9, 11]); w = ctx.draw_choice("grid_w", [9, 11, 13])
    rng = ctx.draw_rng("layout")

    midr, midc = h // 2, w // 2
    qh, qw = midr, midc                 # quadrant dims (h,w odd -> equal halves)
    base = _blob(rng, qh, qw, rng.randint(2, 5))
    color = rng.choice(_NONBG)

    # The 4 quadrants as (top, left, transform) of the base blob.
    quads = [
        (0, 0, lambda r, c: (r, c)),                            # TL
        (0, midc + 1, lambda r, c: (r, qw - 1 - c)),            # TR = flip-lr
        (midr + 1, 0, lambda r, c: (qh - 1 - r, c)),           # BL = flip-ud
        (midr + 1, midc + 1, lambda r, c: (qh - 1 - r, qw - 1 - c)),  # BR = 180
    ]
    missing = rng.randint(0, 3)         # erase exactly one quadrant
    g = full_grid(h, w, 0)
    for i, (top, left, tf) in enumerate(quads):
        if i == missing:
            continue
        for r, c in base:
            rr, cc = tf(r, c)
            g[top + rr][left + cc] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 7
    g = full_grid(h, w, 0)
    base = [(0, 0), (0, 1), (1, 0)]
    if name == "no_missing":
        # all 4 quadrants filled -> rule finds no all-zero quadrant
        for top, left in [(0, 0), (0, 4), (4, 0), (4, 4)]:
            for r, c in base:
                g[top + r][left + c] = 3
        return g
    if name == "all_missing":
        # empty grid -> every quadrant all-zero, no source
        return g
    if name == "single_filled":
        # only one quadrant filled (3 missing) -> ambiguous missing pick
        for r, c in base:
            g[r][c] = 3
        return g
    return g
