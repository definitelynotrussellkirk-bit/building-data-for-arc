"""Generator for arc_puzzle_bank_twentysecond21:M148 — translate non-anchor cells by (dst-src).

Rule: find color-1 (source anchor) and color-2 (destination anchor).
Translate every non-{0,1,2} cell by (dst.r - src.r, dst.c - src.c).
Drop 1 and 2 in output. Cells that go out of bounds are silently
dropped.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6b6e3acc8a0a"
VERSION = "2.1.0"  # choose anchors and source cells jointly so at least one translated non-anchor cell is visible.
TASK_ID = "6b6e3acc8a0a"
SUMMARY = (
    "0-bg grid with: (a) exactly one color-1 cell (source anchor); "
    "(b) exactly one color-2 cell (destination anchor); (c) one or "
    "more shapes in colors other than {0, 1, 2} (e.g. one connected "
    "blob in some color, OR multiple separate cells). Rule: compute "
    "translation (dr, dc) = pos(2) - pos(1). On a FRESH 0-grid, "
    "for every non-{0,1,2} input cell at (r, c) with value v, paint "
    "(r + dr, c + dc) with v if in-bounds (else drop). The two anchor "
    "cells (1 and 2) do NOT appear in the output; only the translated "
    "non-anchor cells are kept."
)

# Rivals: 'output is input' refuted by demos (output drops the 1 and
# 2 anchors). 'preserve anchors' refuted by demos. 'translate by
# (src - dst) backwards' refuted by demos with sign-clear vectors.
# 'translate only colored blob next to the 1' refuted by demos with
# multiple non-anchor cells (all translate uniformly). 'use new
# colors in output' refuted by demos preserving the non-anchor colors.
# 'translate the anchors too' refuted by demos. 4 demos with varied
# (dr, dc) and ≥1 multi-color non-anchor input pin the rule.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one color-1 cell (source anchor)",
    "exactly one color-2 cell (destination anchor) at a different position",
    "≥1 non-anchor cell in some color ∉ {0, 1, 2}",
    "after translation, ≥1 non-anchor cell lands in-bounds",
    "translation (dr, dc) is non-zero (anchors at different positions)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("missing_1", "missing_2", "no_blob")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "n_blob_cells":   {"type": "int", "default": "rng 2..5", "valid": "1..8"},
    "blob_colors":    {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "3..6"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "3..6"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 8, 10)
        n_blob_lo, n_blob_hi = 2, 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 12, 16)
        n_blob_lo, n_blob_hi = 4, 7
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 12)
        n_blob_lo, n_blob_hi = 3, 5
    rng = ctx.draw_rng("layout")
    n_blob = rng.randint(n_blob_lo, n_blob_hi)
    blob_color_pool = [c for c in range(3, 10)]
    rng.shuffle(blob_color_pool)
    blob_colors = blob_color_pool[:rng.randint(1, 3)]
    for _outer in range(80):
        g = full_grid(h, w, 0)
        one_r = rng.randint(1, h - 2)
        one_c = rng.randint(1, w - 2)
        two_r = rng.randint(0, h - 1)
        two_c = rng.randint(0, w - 1)
        if (two_r, two_c) == (one_r, one_c):
            continue
        dr = two_r - one_r
        dc = two_c - one_c
        # Source cells are sampled from positions whose translated target
        # remains in-bounds.  This avoids blank-output episodes where the
        # anchors define a large vector but no motif cell survives it.
        valid = [
            (r, c) for r in range(h) for c in range(w)
            if (r, c) not in ((one_r, one_c), (two_r, two_c))
            and 0 <= r + dr < h and 0 <= c + dc < w
        ]
        if len(valid) < n_blob:
            continue
        rng.shuffle(valid)
        g[one_r][one_c] = 1
        g[two_r][two_c] = 2
        for r, c in valid[:n_blob]:
            g[r][c] = rng.choice(blob_colors)
        return g
    raise ValueError("could not realize non-anchor translation layout")


def _draw_from_degenerate(name, rng):
    h, w = 7, 8
    g = full_grid(h, w, 0)
    if name == "missing_1":
        # 2 + blob but no 1 → no source anchor
        for r, c in [(2, 2), (3, 2)]: g[r][c] = 5
        g[5][6] = 2
        return g
    if name == "missing_2":
        # 1 + blob but no 2 → no destination anchor
        g[2][2] = 1
        for r, c in [(2, 3), (3, 3)]: g[r][c] = 5
        return g
    if name == "no_blob":
        # 1 + 2 only — output is empty
        g[2][2] = 1
        g[5][6] = 2
        return g
    return g


def _positions(g, color):
    return [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == color]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    p1 = _positions(grid, 1)
    p2 = _positions(grid, 2)
    non_anchor = [(r, c) for r, row in enumerate(grid)
                  for c, v in enumerate(row) if v not in (0, 1, 2)]
    if len(p1) != 1:
        errors.append(f"expected exactly one source anchor, found {len(p1)}")
    if len(p2) != 1:
        errors.append(f"expected exactly one destination anchor, found {len(p2)}")
    if not non_anchor:
        errors.append("expected at least one non-anchor source cell")
    if len(p1) == 1 and len(p2) == 1:
        dr = p2[0][0] - p1[0][0]
        dc = p2[0][1] - p1[0][1]
        if (dr, dc) == (0, 0):
            errors.append("anchor translation vector is zero")
        if non_anchor and not any(0 <= r + dr < h and 0 <= c + dc < w
                                  for r, c in non_anchor):
            errors.append("no non-anchor cell lands in-bounds after translation")
    return errors
