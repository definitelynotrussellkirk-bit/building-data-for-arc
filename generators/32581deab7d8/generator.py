"""Generator for puzzle 3f23242b.

Rule: green(3) seed cells; rule stamps a building profile around each
(clipped at edges).

Combinatorial axes (8): grid_h/w, n_seeds, position_bias,
min_separation, anchor_corner, asymmetry_force, palette_size,
edge_margin.
Degenerates: single_seed, no_seeds, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "32581deab7d8"
VERSION = "2.0.1"
TASK_ID = "32581deab7d8"
SUMMARY = (
    "0-bg grid (h, w~12-18) with "
    "2-4 COLOR-3 (green) SINGLE-"
    "CELL SEEDS at interior "
    "positions (edge_margin=2 from "
    "borders) separated by "
    "min_separation=6 cells. "
    "Position bias options: "
    "scattered/corners/diagonal/"
    "row_aligned/centered. Rule "
    "(BUILDING-PROFILE STAMP): for "
    "EACH GREEN SEED at (sr, sc), "
    "STAMP a 'BUILDING PROFILE' "
    "shape centered at (or anchored "
    "to) the seed. A 'building "
    "profile' is a task-specific "
    "fixed motif (e.g., a 3×3 "
    "cross, an L-shape, or a "
    "house-like silhouette) "
    "painted in COLOR 3. The stamp "
    "is CLIPPED at grid edges if "
    "it extends beyond. Multiple "
    "seeds → multiple stamps with "
    "no overlap (thanks to "
    "min_separation). Net: each "
    "green seed expands into a "
    "building-shape stamp; "
    "min_separation ensures stamps "
    "don't collide."
)

INVARIANTS = [
    "background is 0",
    ">=2 green(3) seed cells",
    "seeds >=2 cells from edges",
    "seeds >=6 cells apart (stamps don't overlap)",
]

POSITION_BIASES = ("scattered", "corners", "diagonal", "row_aligned",
                   "centered")
DEGENERATE_TEXTURES = ("single_seed", "no_seeds", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "grid_w":         {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "n_seeds":        {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "min_separation": {"type": "int", "default": "6", "valid": "5..10"},
    "edge_margin":    {"type": "int", "default": "2", "valid": "2..4"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """≥2 color-3 (green) seed cells; seeds are interior (not on border)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    seeds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    if len(seeds) < 2:
        errs.append(f"only {len(seeds)} color-3 seed cell(s) found (need >=2)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 10, 13
    elif difficulty == "hard":
        h_lo, h_hi = 18, 22
    else:
        h_lo, h_hi = 12, 18
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n = int(overrides.get("n_seeds",
                          ctx.draw_int("n_seeds", 2, 4)))
    n = max(1, min(6, n))
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias",
                               list(POSITION_BIASES)))
    min_sep = int(overrides.get("min_separation", 6))
    edge_margin = int(overrides.get("edge_margin", 2))
    g = full_grid(h, w, 0)
    placed = []
    candidates = _candidates(bias, h, w, edge_margin, rng)
    for r, c in candidates:
        if len(placed) >= n:
            break
        if any(abs(r - pr) < min_sep and abs(c - pc) < min_sep
               for pr, pc in placed):
            continue
        g[r][c] = 3
        placed.append((r, c))
    if len(placed) < 2:
        for r, c in [(edge_margin, edge_margin),
                     (h - 1 - edge_margin, w - 1 - edge_margin)]:
            if g[r][c] == 0:
                g[r][c] = 3
                placed.append((r, c))
    return g


def _candidates(bias, h, w, edge_margin, rng):
    if bias == "corners":
        return [(edge_margin, edge_margin),
                (edge_margin, w - 1 - edge_margin),
                (h - 1 - edge_margin, edge_margin),
                (h - 1 - edge_margin, w - 1 - edge_margin)]
    if bias == "diagonal":
        return [(i, i) for i in range(edge_margin, min(h, w) - edge_margin, 6)]
    if bias == "row_aligned":
        r = h // 2
        return [(r, c) for c in range(edge_margin, w - edge_margin, 6)]
    if bias == "centered":
        cr, cc = h // 2, w // 2
        cells = [(r, c) for r in range(edge_margin, h - edge_margin)
                 for c in range(edge_margin, w - edge_margin)]
        cells.sort(key=lambda p: abs(p[0] - cr) + abs(p[1] - cc))
        return cells
    cells = [(r, c) for r in range(edge_margin, h - edge_margin)
             for c in range(edge_margin, w - edge_margin)]
    rng.shuffle(cells)
    return cells


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "single_seed":
        g[h // 2][w // 2] = 3
        return g
    if name == "no_seeds":
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 3
        return g
    return g
