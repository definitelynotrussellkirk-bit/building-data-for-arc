"""Generator for arc_additional_puzzle_bank_volume5:E29.

Red singleton cells fall downward until blocked by the border or obstacles.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_reds,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_reds, no_blockers, reds_at_bottom.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b27ef5e054f4"
VERSION = "1.1.2"
TASK_ID = "b27ef5e054f4"
SUMMARY = "Red singleton cells fall downward until blocked by the border or obstacles."

INVARIANTS = [
    "background is 0",
    "red cells are isolated singletons in the input",
    "red cells have at least one empty cell below before settling",
    "non-red blockers stay fixed and stop falling red cells",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_reds", "no_blockers", "reds_at_bottom")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "5..24"},
    "grid_w":         {"type": "int", "default": "rng 7..12", "valid": "4..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_reds":         {"type": "int", "default": "rng 3..6", "valid": "1..15"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "position_bias":  {"type": "str", "default": "reds_above_blockers",
                       "valid": "reds_above_blockers"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify isolated falling reds plus fixed non-red blockers."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    red_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    blockers = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 2)]
    min_reds = 5 if difficulty == "hard" else 3
    if len(red_cells) < min_reds:
        errs.append(f"expected at least {min_reds} red singletons, found {len(red_cells)}")
    if not blockers:
        errs.append("no non-red blockers present")
    for r, c in red_cells:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 2:
                errs.append(f"red cells are 4-adjacent at ({r},{c}) and ({nr},{nc})")
                return errs
        if not (r < h - 1 and grid[r + 1][c] == 0):
            errs.append(f"red cell at ({r},{c}) has no immediate empty cell below")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 7, 9)
        n_reds = ctx.draw_int("n_reds", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 10, 12)
        n_reds = ctx.draw_int("n_reds", 5, 6)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 7, 12)
        n_reds = ctx.draw_int("n_reds", 3, 6)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    columns = rng.sample(range(w), min(n_reds, w))
    red_cells: set[tuple[int, int]] = set()
    for i, c in enumerate(columns):
        blocker_row = rng.randint(max(4, h // 2), h - 1)
        if i % 3 != 0:
            g[blocker_row][c] = rng.choice([5, 6, 7])
            max_red_row = blocker_row - 2
        else:
            max_red_row = h - 3
        for _ in range(40):
            r = rng.randint(0, max_red_row)
            if all(abs(r - rr) + abs(c - cc) > 1 for rr, cc in red_cells):
                g[r][c] = 2
                red_cells.add((r, c))
                break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_reds":
        # blockers without red cells → nothing to fall
        g[5][2] = 5
        g[5][6] = 6
        return g
    if name == "no_blockers":
        # red cells without blockers → all fall to bottom row (uniform result)
        g[1][2] = 2
        g[2][5] = 2
        g[3][7] = 2
        return g
    if name == "reds_at_bottom":
        # red already at bottom → falling is identity (no signal)
        g[h - 1][2] = 2
        g[h - 1][5] = 2
        g[h - 1][7] = 2
        return g
    return g
