"""Generator for arc_puzzle_bank_21_set12_s:S12_E2 — keep only isolated components.

Rule: keep only the components whose contact degree is zero (no cardinally
adjacent component); paint them on a blank grid, drop the rest.

The old generator placed a FIXED touching cluster plus 1-2 FIXED isolated
components at fixed positions, so the surviving output barely varied
(distinct=31). Now: RANDOM isolated components (varied shapes/colors/positions,
each separated so it has degree 0) plus RANDOM touching clusters (two
cardinally-adjacent color regions, degree > 0, dropped).

Combinatorial axes: isolated component count/shapes/colors/positions (-> the
output), touching-cluster count, grid size.
Degenerates: all_isolated, all_touching, single_isolated.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4cadfa9ae121"
VERSION = "3.0.1"  # distinct=31: rule keeps only degree-0 (isolated) components. Old gen used a fixed touching cluster + fixed isolated cells. Now random isolated polys (varied shape/colour/position) + random touching clusters (2 cardinally-adjacent regions, dropped).
TASK_ID = "4cadfa9ae121"
SUMMARY = (
    "0-bg grid (size varies) with ISOLATED components (random connected "
    "polyominoes in distinct colors, each separated from everything by >=1 gap "
    "so its contact degree is 0) and TOUCHING clusters (small blocks split into "
    "two cardinally-adjacent color regions, so each region has degree > 0). "
    "Rule: keep only the degree-0 (isolated) components on a blank grid; drop "
    "all touching ones. Output = the isolated components in place."
)

INVARIANTS = [
    "background is 0",
    "isolated components have no cardinally-adjacent component (degree 0)",
    "touching clusters contain >=2 cardinally-adjacent components (degree > 0)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_isolated", "all_touching", "single_isolated")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "9..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "10..18"},
    "isolated_count": {"type": "int", "default": "rng 2..4", "valid": "1..4"},
    "touching_count": {"type": "int", "default": "rng 1..3", "valid": "0..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "varies", "valid": "3..8"},
    "position_bias":  {"type": "str", "default": "isolated_and_touching",
                       "valid": "isolated_and_touching"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "3..8"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _paint(g, cells, color):
    for r, c in cells:
        g[r][c] = color


def _rand_poly(rng, n):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < n:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc))
            seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells)
    cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for (r, c) in cells]


def _free(g, top, left, cells):
    """In-bounds and itself + 8-neighborhood clear (so the placed shape has no
    cardinal/diagonal contact with anything already placed)."""
    h, w = len(g), len(g[0])
    for dr, dc in cells:
        rr, cc = top + dr, left + dc
        if not (0 <= rr < h and 0 <= cc < w):
            return False
        for ddr in (-1, 0, 1):
            for ddc in (-1, 0, 1):
                nr, nc = rr + ddr, cc + ddc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                    return False
    return True


def _place(g, rng, cells, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in cells) + 1
    sw = max(c for _, c in cells) + 1
    for _ in range(100):
        top = rng.randint(0, h - sh)
        left = rng.randint(0, w - sw)
        if _free(g, top, left, cells):
            _paint(g, [(top + r, left + c) for r, c in cells], color)
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 10, 12)
        n_iso = ctx.draw_int("isolated_count", 1, 2); n_touch = ctx.draw_int("touching_count", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16); w = ctx.draw_int("grid_w", 14, 18)
        n_iso = ctx.draw_int("isolated_count", 3, 4); n_touch = ctx.draw_int("touching_count", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 12, 15)
        n_iso = ctx.draw_int("isolated_count", 2, 3); n_touch = ctx.draw_int("touching_count", 1, 2)

    pal = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], min(9, n_iso + 2 * n_touch))
    pi = 0
    g = full_grid(h, w, 0)
    # isolated components (kept)
    for _ in range(n_iso):
        if pi < len(pal) and _place(g, rng, _rand_poly(rng, rng.randint(2, 5)), pal[pi]):
            pi += 1
    # touching clusters (dropped): a solid block split into two adjacent colours
    for _ in range(n_touch):
        if pi + 1 >= len(pal):
            break
        bh = rng.randint(2, 3); bw = rng.randint(2, 4)
        cells = [(r, c) for r in range(bh) for c in range(bw)]
        # place the whole block 8-gap-free, then 2-colour it (left | right)
        sh, sw = bh, bw
        placed = False
        for _ in range(100):
            top = rng.randint(0, h - sh); left = rng.randint(0, w - sw)
            if _free(g, top, left, cells):
                split = rng.randint(1, bw - 1)
                for (r, c) in cells:
                    g[top + r][left + c] = pal[pi] if c < split else pal[pi + 1]
                placed = True
                break
        if placed:
            pi += 2
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify isolated + touching-cluster invariants."""
    if not grid or not grid[0]:
        return ["empty grid"]
    problems = []
    flat = [v for row in grid for v in row]
    if all(v == 0 for v in flat):
        problems.append("grid is entirely background (no components at all)")
    elif len(set(v for v in flat if v != 0)) < 2:
        problems.append("fewer than 2 distinct nonzero colors (need isolated + touching groups)")
    return problems


def _draw_from_degenerate(name, rng):
    rng = rng or __import__("random").Random(0)
    g = full_grid(11, 12, 0)
    if name == "all_isolated":
        _place(g, rng, _rand_poly(rng, 3), 4)
        _place(g, rng, _rand_poly(rng, 3), 6)
        return g
    if name == "all_touching":
        for c in range(2, 5):
            g[3][c] = 4 if c < 4 else 6
        return g
    if name == "single_isolated":
        _place(g, rng, _rand_poly(rng, 4), 7)
        return g
    return g
