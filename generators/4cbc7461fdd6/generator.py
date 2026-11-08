"""Generator for puzzle ce039d91.

Rule: `(rule! (lambda (g) (cellmap g (r c v) (if (and (= v 5) (= (at g r (- (- w 1) c)) 5)) 1 v))))`.
Every gray(5) cell whose LR mirror is also gray(5) becomes blue(1);
the asymmetric grays stay 5.

Combinatorial axes:
  * grid_h / grid_w     — outer canvas size
  * n_pairs             — LR-symmetric gray pairs to plant
  * n_solo              — asymmetric grays (no LR-mirror partner)
  * pair_layout         — random / cluster / row / column / diagonal
  * solo_layout         — random / cluster / row / column / diagonal
  * caller-opt-in degenerates: all_pairs (no asymmetric grays),
                               all_solo (no symmetric pairs),
                               only_axis_grays (cells on axis are
                               trivially symmetric — minimal signal)
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4cbc7461fdd6"
VERSION = "2.0.1"
TASK_ID = "4cbc7461fdd6"
SUMMARY = (
    "0-bg grid (h, w~6-14) "
    "with SPARSE GRAY(5) "
    "CELLS placed in a "
    "mix of two types: "
    "(a) 1-5 LR-SYMMETRIC "
    "PAIRS — each pair "
    "consists of cells at "
    "(r, c) and "
    "(r, w-1-c) (both "
    "painted 5, c ≠ "
    "w-1-c so they're "
    "distinct positions); "
    "(b) 1-5 ASYMMETRIC "
    "SOLO GRAYS — single "
    "cells at (r, c) with "
    "no partner at "
    "(r, w-1-c). Pair "
    "layout (random/"
    "cluster/row/column/"
    "diagonal) and solo "
    "layout vary "
    "independently. Rule "
    "(RECOLOR LR-SYMMETRIC "
    "GRAY PAIRS TO BLUE, "
    "LEAVE ASYMMETRIC "
    "GRAYS AS GRAY): For "
    "EACH GRAY (5) CELL "
    "at (r, c): check if "
    "the LR-MIRROR cell "
    "at (r, w-1-c) is "
    "ALSO 5. If YES (the "
    "cell has a partner)"
    ": RECOLOR (r, c) "
    "from 5 to 1 (blue). "
    "Else (no partner — "
    "asymmetric solo "
    "gray), KEEP at 5. "
    "Other cells "
    "unchanged. Net: "
    "paired grays "
    "transform to blue; "
    "solo grays survive."
)

INVARIANTS = [
    "background is 0",
    "all non-bg cells are gray(5)",
    "≥1 LR-symmetric gray pair",
    "≥1 asymmetric gray",
]

LAYOUTS = ("random", "cluster", "row", "column", "diagonal")
DEGENERATE_TEXTURES = ("all_pairs", "all_solo", "only_axis_grays")
HELPFUL_TEXTURES = LAYOUTS

AXES = {
    "grid_h":      {"type": "int", "default": "rng 6..14", "valid": "5..18"},
    "grid_w":      {"type": "int", "default": "rng 6..14", "valid": "5..18"},
    "n_pairs":     {"type": "int", "default": "rng 2..5",  "valid": "1..8"},
    "n_solo":      {"type": "int", "default": "rng 2..5",  "valid": "1..8"},
    "pair_layout": {"type": "str", "default": "rng helpful",
                    "valid": "|".join(LAYOUTS)},
    "solo_layout": {"type": "str", "default": "rng helpful",
                    "valid": "|".join(LAYOUTS)},
    "texture":     {"type": "str", "default": "alias for pair_layout",
                    "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    if difficulty == "easy":
        h_lo, h_hi, p_lo, p_hi = 6, 8, 1, 2
    elif difficulty == "hard":
        h_lo, h_hi, p_lo, p_hi = 11, 14, 4, 6
    else:
        h_lo, h_hi, p_lo, p_hi = 6, 14, 2, 5

    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")

    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)

    n_pairs = int(overrides.get("n_pairs",
                                ctx.draw_int("n_pairs", p_lo, p_hi)))
    n_solo = int(overrides.get("n_solo",
                               ctx.draw_int("n_solo", p_lo, p_hi)))
    pair_layout = (overrides.get("texture")
                   or overrides.get("pair_layout")
                   or ctx.draw_choice("pair_layout", list(LAYOUTS)))
    solo_layout = overrides.get(
        "solo_layout",
        ctx.draw_choice("solo_layout", list(LAYOUTS)))

    g = full_grid(h, w, 0)
    pair_candidates = _layout_for(pair_layout, h, w, rng, half_w=True)
    placed_pairs = 0
    for (r, c) in pair_candidates:
        if placed_pairs >= n_pairs:
            break
        mirror_c = w - 1 - c
        if c == mirror_c:
            continue
        if g[r][c] != 0 or g[r][mirror_c] != 0:
            continue
        g[r][c] = 5
        g[r][mirror_c] = 5
        placed_pairs += 1

    solo_candidates = _layout_for(solo_layout, h, w, rng, half_w=False)
    placed_solo = 0
    for (r, c) in solo_candidates:
        if placed_solo >= n_solo:
            break
        mirror_c = w - 1 - c
        if c == mirror_c:
            continue
        if g[r][c] != 0 or g[r][mirror_c] != 0:
            continue
        g[r][c] = 5
        placed_solo += 1

    if placed_pairs < 1:
        # Force at least one pair to satisfy invariant.
        for r in range(h):
            for c in range(w // 2):
                mc = w - 1 - c
                if g[r][c] == 0 and g[r][mc] == 0 and c != mc:
                    g[r][c] = 5; g[r][mc] = 5
                    break
            else:
                continue
            break
    if placed_solo < 1:
        for r in range(h):
            for c in range(w):
                mc = w - 1 - c
                if g[r][c] == 0 and g[r][mc] == 0 and c != mc:
                    g[r][c] = 5
                    return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify LR-symmetric gray pairs + solo gray invariants."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    problems = []
    flat = [v for row in grid for v in row]
    bad = [v for v in flat if v not in (0, 5)]
    if bad:
        problems.append(f"unexpected colors (not {{0,5}}): {sorted(set(bad))}")
    if 5 not in flat:
        problems.append("no color-5 gray cells found")
        return problems
    # Check at least one LR-symmetric pair and one solo
    has_pair = False
    has_solo = False
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 5:
                mc = w - 1 - c
                if c != mc and grid[r][mc] == 5:
                    has_pair = True
                elif c == mc or grid[r][mc] != 5:
                    has_solo = True
    if not has_pair:
        problems.append("no LR-symmetric gray pair found")
    if not has_solo:
        problems.append("no asymmetric solo gray found")
    return problems


def _layout_for(layout, h, w, rng, half_w):
    """Generate (r, c) candidates respecting half_w (only c < w//2 if True)."""
    cmax = w // 2 if half_w else w
    cells = [(r, c) for r in range(h) for c in range(cmax)]
    if layout == "cluster":
        cr = rng.randint(0, h - 1); cc = rng.randint(0, max(0, cmax - 1))
        cells.sort(key=lambda rc: abs(rc[0] - cr) + abs(rc[1] - cc))
    elif layout == "row":
        r = rng.randint(0, h - 1)
        cells = [(r, c) for c in range(cmax)]
        rng.shuffle(cells)
    elif layout == "column":
        c = rng.randint(0, max(0, cmax - 1))
        cells = [(r, c) for r in range(h)]
        rng.shuffle(cells)
    elif layout == "diagonal":
        cells = [(k, k) for k in range(min(h, cmax))]
        rng.shuffle(cells)
    else:
        rng.shuffle(cells)
    return cells


def _draw_from_degenerate(name, h, w, rng):
    """Edge-case where the LR-symmetry signal collapses.

    all_pairs        — every gray cell has an LR-mirror; output is all 1s
                        (rule "if both 5 → 1" applies everywhere).
    all_solo         — no LR-symmetric pair; output keeps all grays as 5.
    only_axis_grays  — grays only on the central column (which is its
                        own mirror) — these are trivially "symmetric"
                        but conceptually edge-case.
    """
    g = full_grid(h, w, 0)
    if name == "all_pairs":
        for r in range(h):
            for c in range(w // 2):
                if rng.random() < 0.4:
                    g[r][c] = 5
                    g[r][w - 1 - c] = 5
        return g
    if name == "all_solo":
        for r in range(h):
            for c in range(w):
                mc = w - 1 - c
                if c == mc:
                    continue
                if rng.random() < 0.25 and g[r][c] == 0 and g[r][mc] == 0:
                    g[r][c] = 5  # only one side
        return g
    if name == "only_axis_grays":
        if w % 2 == 0:
            return g  # no axis column
        axis = w // 2
        for r in range(h):
            if rng.random() < 0.5:
                g[r][axis] = 5
        return g
    return g
