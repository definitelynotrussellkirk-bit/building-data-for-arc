"""Generator for arc_puzzle_bank_21_set23_bundle:easy_p06.

Combinatorial axes (8): grid_h, grid_w, palette_kind, seed_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, seed_at_border, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "12c0011674a7"
VERSION = "1.2.0"
TASK_ID = "12c0011674a7"
SUMMARY = "Isolated seeds stamp their color at all eight knight offsets."

INVARIANTS = [
    "background is 0",
    "each seed is 8-neighbor isolated in the input",
    "seed knight neighborhoods do not overlap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "seed_at_border", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "5..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "seed_count":     {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "isolated_knight_seeds",
                       "valid": "isolated_knight_seeds"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

KNIGHT = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
          (1, -2), (1, 2), (2, -1), (2, 1)]


def _footprint(r: int, c: int) -> set[tuple[int, int]]:
    cells = {(r, c)}
    cells |= {(r + dr, c + dc) for dr, dc in KNIGHT}
    cells |= {(r + dr, c + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
    return cells


def _choose_disjoint_centers(positions, count, rng):
    positions = list(positions)
    rng.shuffle(positions)
    footprints = {pos: _footprint(*pos) for pos in positions}

    def rec(start, chosen, occupied):
        if len(chosen) >= count:
            return chosen
        if len(chosen) + (len(positions) - start) < count:
            return None
        for idx in range(start, len(positions)):
            pos = positions[idx]
            fp = footprints[pos]
            if fp & occupied:
                continue
            out = rec(idx + 1, chosen + [pos], occupied | fp)
            if out is not None:
                return out
        return None

    return rec(0, [], set())


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        seed_count = ctx.draw_int("seed_count", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 12, 13)
        seed_count = ctx.draw_int("seed_count", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 13)
        seed_count = ctx.draw_int("seed_count", 2, 4)
    rng = ctx.draw_rng("layout")
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], min(seed_count, 9))
    base_positions = [(r, c) for r in range(2, h - 2) for c in range(2, w - 2)]

    # The feasible centers are sparse because we reserve both the seed's
    # 8-neighborhood and its knight destinations.  A single greedy pass often
    # stopped after one seed even when the difficulty promised two or more.
    # Use a randomized backtracking search and, for medium cases whose sampled
    # canvas is too small for four seeds, grow within the declared valid range
    # instead of emitting a weakened example.
    for _grow_attempt in range(8):
        base_positions = [(r, c) for r in range(2, h - 2) for c in range(2, w - 2)]
        centers = _choose_disjoint_centers(base_positions, seed_count, rng)
        if centers is not None:
            grid = full_grid(h, w, 0)
            for idx, (r, c) in enumerate(centers):
                grid[r][c] = colors[idx % len(colors)]
            return grid
        if h <= w and h < 16:
            h += 1
        elif w < 18:
            w += 1
        elif h < 16:
            h += 1
        else:
            break
    raise ValueError("could not realize isolated knight-seed layout")


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # blank → no seeds to stamp, identity
        return g
    if name == "seed_at_border":
        # seeds within 2 of border → knight stamps would extend OOB
        g[0][3] = 4
        g[1][1] = 6
        return g
    if name == "all_same_color":
        # all seeds same color → stamps merge ambiguously when adjacent
        g[3][3] = 4
        g[3][8] = 4
        g[6][5] = 4
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(v not in range(10) for row in grid for v in row):
        errors.append("grid values must be digits 0..9")
    seeds = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    lo, hi = (2, 2) if difficulty == "easy" else ((3, 4) if difficulty == "hard" else (2, 4))
    if not (lo <= len(seeds) <= hi):
        errors.append(f"expected {lo}..{hi} isolated knight seeds, got {len(seeds)}")
    occupied = []
    for r, c, _v in seeds:
        if not (2 <= r < len(grid) - 2 and 2 <= c < len(grid[0]) - 2):
            errors.append("all normal seeds must be at least two cells from the border")
        occupied.append(_footprint(r, c))
    for i in range(len(occupied)):
        for j in range(i + 1, len(occupied)):
            if occupied[i] & occupied[j]:
                errors.append("seed neighborhoods and knight stamps must be disjoint")
                return errors
    return errors
