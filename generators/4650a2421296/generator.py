"""Generator for arc_additional_puzzle_bank_volume16:M108.

Rule: the gray-wall chamber with the most red seeds is filled cyan.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_chambers,
palette_size, position_bias, n_distinct_colors, seed_distribution, texture.
Degenerates: no_seeds, no_walls, tied_seed_counts.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4650a2421296"
VERSION = "2.0.1"  # distinct=92: only ever 2 chambers (1 vertical wall) and the LEFT chamber always won (3 fixed seeds vs 1). Now 1-2 vertical + 0-2 horizontal internal walls -> 2-9 chambers, with a RANDOM winning chamber (strictly max red seeds) at varied positions and varied per-chamber seed counts -> the filled region varies far more.
TASK_ID = "4650a2421296"
SUMMARY = "Gray (5) walls partition the bordered board into chambers; the chamber with strictly the most red (2) seeds is filled cyan (8). Wall layout, chamber count, the winning chamber, and seed counts/positions all vary."

INVARIANTS = [
    "background is 0",
    "gray walls partition the board into chambers",
    "one chamber has strictly more red seeds than all others",
    "selected chamber contains blank cells to fill",
]

PALETTE_KINDS = ("default", "left_winner", "right_winner", "balanced_close")
DEGENERATE_TEXTURES = ("no_seeds", "no_walls", "tied_seed_counts")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "6..24"},
    "grid_w":         {"type": "int", "default": "rng 10..15", "valid": "8..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_chambers":     {"type": "int", "default": "2..9", "valid": "2..9"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "chamber", "valid": "chamber"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "seed_distribution": {"type": "str", "default": "skewed", "valid": "skewed"},
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
        h = ctx.draw_int("grid_h", 8, 10); w = ctx.draw_int("grid_w", 10, 12)
        nv_hi, nh_hi = 1, 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 20); w = ctx.draw_int("grid_w", 14, 22)
        nv_hi, nh_hi = 2, 2
    else:
        h = ctx.draw_int("grid_h", 10, 16); w = ctx.draw_int("grid_w", 12, 18)
        nv_hi, nh_hi = 2, 1
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    for r in range(h):
        g[r][0] = 5; g[r][w - 1] = 5
    for c in range(w):
        g[0][c] = 5; g[h - 1][c] = 5
    # internal full walls -> a grid of rectangular chambers
    vwalls = _walls(rng, 1, w - 2, rng.randint(1, nv_hi))
    hwalls = _walls(rng, 1, h - 2, rng.randint(0, nh_hi))
    for c in vwalls:
        for r in range(1, h - 1):
            g[r][c] = 5
    for r in hwalls:
        for c in range(1, w - 1):
            g[r][c] = 5
    col_bands = _bands(vwalls, 1, w - 2)
    row_bands = _bands(hwalls, 1, h - 2)
    chambers = [(rb, cb) for rb in row_bands for cb in col_bands]
    # assign per-chamber seed counts with a strict, randomly-chosen winner
    counts = [rng.randint(0, 2) for _ in chambers]
    win = rng.randrange(len(chambers))
    counts[win] = max(counts) + rng.randint(1, 3)
    for (rb, cb), k in zip(chambers, counts):
        free = [(r, c) for r in range(rb[0], rb[1] + 1)
                for c in range(cb[0], cb[1] + 1) if g[r][c] == 0]
        rng.shuffle(free)
        for (r, c) in free[:min(k, max(0, len(free) - 1))]:  # leave >=1 blank
            g[r][c] = 2
    return g


def _walls(rng, lo, hi, k):
    """k wall positions in [lo, hi], pairwise >= 3 apart (chambers >= 2 wide),
    and >= 2 from the borders so each side band has room."""
    for _ in range(60):
        ps = sorted(rng.sample(range(lo + 1, hi), k)) if k and hi - lo > 2 else []
        if (not ps or (ps[0] - lo >= 2 and hi - ps[-1] >= 2
                       and all(ps[i + 1] - ps[i] >= 3 for i in range(len(ps) - 1)))):
            return ps
    return []


def _bands(walls, lo, hi):
    bands = []
    start = lo
    for wpos in walls:
        if start <= wpos - 1:
            bands.append((start, wpos - 1))
        start = wpos + 1
    if start <= hi:
        bands.append((start, hi))
    return bands


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # walls + chambers but no red seeds → no chamber to fill
        for r in range(h):
            g[r][0] = 5; g[r][w - 1] = 5
        for c in range(w):
            g[0][c] = 5; g[h - 1][c] = 5
        for r in range(1, h - 1):
            g[r][5] = 5
        return g
    if name == "no_walls":
        # red seeds but no gray walls → no chamber boundary
        for r, c in [(1, 1), (2, 2), (4, 6), (5, 8)]:
            g[r][c] = 2
        return g
    if name == "tied_seed_counts":
        # both chambers have the same number of red seeds → "most" is undefined
        for r in range(h):
            g[r][0] = 5; g[r][w - 1] = 5
        for c in range(w):
            g[0][c] = 5; g[h - 1][c] = 5
        for r in range(1, h - 1):
            g[r][5] = 5
        for r, c in [(1, 1), (2, 2)]:
            g[r][c] = 2
        for r, c in [(1, 8), (2, 9)]:
            g[r][c] = 2
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=0; border fully color-5; at least one red(2) seed inside."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    # full border must be 5
    border_ok = (all(grid[0][c] == 5 for c in range(w)) and
                 all(grid[h - 1][c] == 5 for c in range(w)) and
                 all(grid[r][0] == 5 for r in range(h)) and
                 all(grid[r][w - 1] == 5 for r in range(h)))
    if not border_ok:
        errors.append("border is not fully color-5 walls")
    seeds = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1) if grid[r][c] == 2]
    if not seeds:
        errors.append("no red(2) seeds found inside the border")
    return errors
