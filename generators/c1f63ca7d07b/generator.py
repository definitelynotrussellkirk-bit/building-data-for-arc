"""Generator for arc_puzzle_bank_21_set14_bundle:easy_n05 — singleton seed steps toward nearest border.

Each singleton seed has one uniquely nearest border. The rule keeps the seed
and paints the adjacent step toward that border.

Combinatorial axes (8): grid_h, grid_w, palette_kind, seed_count, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, equidistant_borders, blocked_step.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c1f63ca7d07b"
VERSION = "1.2.0"  # require in-bounds nearest-border step targets + self_check
TASK_ID = "c1f63ca7d07b"
SUMMARY = "Colored singleton seeds with one-step nearest-border motion."

INVARIANTS = [
    "background is 0",
    "all nonzero cells are singleton seeds",
    "each seed has a unique nearest border",
    "seed step targets are initially zero",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "equidistant_borders", "blocked_step")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "seed_count":     {"type": "int", "default": "rng 3..5", "valid": "1..7"},
    "palette_size":   {"type": "int", "default": "= seed_count", "valid": "1..7"},
    "position_bias":  {"type": "str", "default": "scattered_singletons",
                       "valid": "scattered_singletons"},
    "n_distinct_colors": {"type": "int", "default": "= seed_count", "valid": "1..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _step(h, w, r, c):
    dists = [(r, -1, 0), (h - 1 - r, 1, 0), (c, 0, -1), (w - 1 - c, 0, 1)]
    mind = min(d for d, _, _ in dists)
    if sum(1 for d, _, _ in dists if d == mind) != 1:
        return None
    _, dr, dc = min(dists, key=lambda x: x[0])
    return r + dr, c + dc


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 10)
        seed_count = ctx.draw_int("seed_count", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 12, 14)
        seed_count = ctx.draw_int("seed_count", 5, 7)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 12)
        seed_count = ctx.draw_int("seed_count", 3, 5)
    colors = ctx.draw_distinct_colors("colors", n=seed_count, exclude={0})
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    occupied = set()
    for color in colors:
        for _ in range(300):
            r = rng.randrange(h)
            c = rng.randrange(w)
            target = _step(h, w, r, c)
            if (target and 0 <= target[0] < h and 0 <= target[1] < w
                    and (r, c) not in occupied and target not in occupied):
                g[r][c] = color
                occupied.add((r, c))
                occupied.add(target)
                break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # Empty grid — rule has no seed to advance.
        return g
    if name == "equidistant_borders":
        # Seeds at the exact vertical and horizontal center — each is
        # equidistant from two opposite borders, so the rule's
        # nearest-border step is undefined.
        cr, cc = h // 2, w // 2
        g[cr][cc] = 4
        return g
    if name == "blocked_step":
        # Seeds whose intended step cell is already occupied by another
        # seed of a different color — the step lands on a non-empty cell
        # and the rule's invariant is violated.
        g[1][3] = 4
        g[0][3] = 6
        g[5][1] = 5
        g[5][0] = 7
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    h, w = len(grid), len(grid[0])
    cells = []
    counts = {}
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v != 0:
                cells.append((r, c, v)); counts[v] = counts.get(v, 0) + 1
    if len(cells) < 2:
        errs.append(f"expected at least two singleton seeds, got {len(cells)}")
    for color, cnt in sorted(counts.items()):
        if cnt != 1:
            errs.append(f"color {color} appears {cnt} times, expected singleton")
    for r, c, _v in cells:
        target = _step(h, w, r, c)
        if target is None:
            errs.append("seed does not have a unique nearest border")
            continue
        tr, tc = target
        if not (0 <= tr < h and 0 <= tc < w):
            errs.append("nearest-border step target is out of bounds")
            continue
        if grid[tr][tc] != 0:
            errs.append("nearest-border step target is already occupied")
    return errs
