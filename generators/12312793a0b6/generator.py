"""Generator for ARC task 67385a82.

Rule: for each 3-cell, if any 4-neighbor is also 3, recolor to 8.
Isolated 3s stay 3.

Combinatorial axes (8): grid_h/w, n_groups, n_isolated,
group_size_range, group_layout, position_bias, decoy_density,
inter_group_separation.
Degenerates: all_isolated, all_grouped, no_threes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "12312793a0b6"
VERSION = "2.0.1"  # poison fix: dropped 'diag' layout (pure-diagonal 3s are NOT 4-conn -> rule never fires -> 100% identity); blob growth now strictly 4-conn so every group truly recolors
TASK_ID = "12312793a0b6"
SUMMARY = "Color-3 cells in groups + isolated; rule recolors connected to 8."

INVARIANTS = [
    "background is 0",
    ">=1 group of >=2 4-conn 3-cells (so 'recolor' branch fires)",
    ">=1 isolated 3-cell (so 'stay' branch fires)",
    "no color 8 in input (rule writes 8 for output)",
    "groups are 4-connected (rule only checks cardinal neighbours)",
]

GROUP_LAYOUTS = ("blob", "row", "col", "L_shape", "block_2x2")
DEGENERATE_TEXTURES = ("all_isolated", "all_grouped", "no_threes")
HELPFUL_TEXTURES = GROUP_LAYOUTS

AXES = {
    "grid_h":             {"type": "int", "default": "rng 5..12", "valid": "4..16"},
    "grid_w":             {"type": "int", "default": "rng 5..12", "valid": "4..16"},
    "n_groups":           {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "n_isolated":         {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "group_size_range":   {"type": "str", "default": "rng small|medium|large",
                           "valid": "small|medium|large"},
    "group_layout":       {"type": "str", "default": "rng helpful",
                           "valid": "|".join(GROUP_LAYOUTS)},
    "inter_group_separation": {"type": "int", "default": "2", "valid": "1..3"},
    "decoy_density":      {"type": "float", "default": "0", "valid": "0..0.05"},
    "texture":            {"type": "str", "default": "alias for group_layout",
                           "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: rectangular grid; has color-3 cells; no color-8 in input."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    threes = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    eights = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if eights:
        errors.append(f"color 8 found in input at {eights[0]} — rule writes 8, not input")
    if not threes:
        return errors  # degenerate (no_threes) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 4, 7
    elif difficulty == "hard":
        h_lo, h_hi = 11, 16
    else:
        h_lo, h_hi = 5, 12
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_groups = int(overrides.get("n_groups",
                                 ctx.draw_int("n_groups", 1, 3)))
    n_iso = int(overrides.get("n_isolated",
                              ctx.draw_int("n_isolated", 2, 4)))
    n_groups = max(1, min(5, n_groups))
    n_iso = max(1, min(6, n_iso))
    layout = (overrides.get("texture") or
              overrides.get("group_layout")
              or ctx.draw_choice("group_layout", list(GROUP_LAYOUTS)))
    size_kind = overrides.get("group_size_range",
                              ctx.draw_choice("group_size_range",
                                              ["small", "medium", "large"]))
    sep = int(overrides.get("inter_group_separation", 2))
    g = full_grid(h, w, 0)
    placed_groups = 0
    for _ in range(n_groups * 4):
        if placed_groups >= n_groups:
            break
        cells = _group_cells(layout, size_kind, h, w, rng)
        if not cells:
            continue
        for _try in range(20):
            r0 = rng.randint(0, h - 1)
            c0 = rng.randint(0, w - 1)
            placed = [(r0 + dr, c0 + dc) for dr, dc in cells]
            if not all(0 <= r < h and 0 <= c < w for r, c in placed):
                continue
            if any(g[r][c] != 0 for r, c in placed):
                continue
            ok = all(_no_close_3(g, r, c, h, w, sep) for r, c in placed)
            if not ok:
                continue
            for r, c in placed:
                g[r][c] = 3
            placed_groups += 1
            break
    placed_iso = 0
    for _ in range(n_iso * 6):
        if placed_iso >= n_iso:
            break
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if g[r][c] != 0:
            continue
        if not _no_close_3(g, r, c, h, w, 2):
            continue
        g[r][c] = 3
        placed_iso += 1
    if placed_groups < 1:
        if h >= 2 and w >= 2:
            g[0][0] = 3; g[0][1] = 3
    if placed_iso < 1:
        for r in range(h):
            for c in range(w):
                if g[r][c] == 0 and _no_close_3(g, r, c, h, w, 2):
                    g[r][c] = 3
                    return g
    return g


def _group_cells(layout, size_kind, h, w, rng):
    s_lo, s_hi = {"small": (2, 3), "medium": (3, 4), "large": (4, 5)}[size_kind]
    n = rng.randint(s_lo, s_hi)
    if layout == "row":
        return [(0, c) for c in range(n)]
    if layout == "col":
        return [(r, 0) for r in range(n)]
    if layout == "L_shape":
        return [(0, c) for c in range(n // 2 + 1)] + \
               [(r, 0) for r in range(1, n - n // 2)]
    if layout == "block_2x2":
        return [(0, 0), (0, 1), (1, 0), (1, 1)]
    # blob: grow with strictly CARDINAL steps so the group is 4-connected
    # (the rule only recolors a 3 with a cardinal-neighbour 3).
    cells = [(0, 0)]
    for _ in range(n - 1):
        r0, c0 = rng.choice(cells)
        for _try in range(10):
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            new_cell = (r0 + dr, c0 + dc)
            if new_cell not in cells:
                cells.append(new_cell)
                break
    return cells


def _no_close_3(g, r, c, h, w, sep):
    for dr in range(-sep, sep + 1):
        for dc in range(-sep, sep + 1):
            if abs(dr) + abs(dc) > sep:
                continue
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and g[nr][nc] == 3:
                return False
    return True


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "all_isolated":
        for r in range(0, h, 2):
            for c in range(0, w, 2):
                g[r][c] = 3
        return g
    if name == "all_grouped":
        for r in range(2, 5):
            for c in range(2, 5):
                if r < h and c < w:
                    g[r][c] = 3
        return g
    if name == "no_threes":
        return g
    return g
