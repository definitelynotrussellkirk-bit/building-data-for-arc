"""Generator for 8886d717.

Rule: one full grid edge is maroon (9). For each cyan (8) cell, if all
in-bounds 4-neighbors are red (2) or cyan (8), it's enclosed → becomes red.
Else: it moves one step toward the maroon edge.

Combinatorial axes (8): grid_h/w, palette_kind, edge, n_cyan,
n_red_walls, palette_size, position_bias, n_distinct_colors, texture.
Degenerates: no_cyan, no_edge, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e51bd0fdbc36"
VERSION = "2.0.1"  # +self_check; WRONG-BG fix: canonical uses bg=7 (orange field) in ALL train pairs; gen drew bg=0. Rule is bg-agnostic (treats any non-{2,8,9} as passive), so bg=0 ran fine but the input DISTRIBUTION diverged from canonical (orange field). bg now 7 to match.
TASK_ID = "e51bd0fdbc36"
SUMMARY = "Orange(7) background field with one full grid edge maroon (9). Cyan (8) cells move one step toward the maroon edge each application. Cyan cells whose entire 4-neighborhood is red (2) or cyan (8) are enclosed and become red. Red and background unchanged."

# Rivals: 'output is input' refuted by any demo where cyan shifts.
# 'move all cells' refuted by any demo (only cyan moves; red stays).
# 'cyan → red unconditionally' refuted by ≥1 demo with a free-moving
# cyan not getting boxed in. 'fixed edge=top' refuted by ≥2 demos
# with different edges. 4 demos with all 4 edges cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "exactly one full grid edge is maroon (9)",
    "cyan cells use color 8",
    "red cells use color 2 and can enclose cyan clusters",
    "non-enclosed cyan cells have a clear path toward the maroon edge",
]

EDGE_KINDS = ("top", "bottom", "left", "right")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_cyan", "no_edge", "full_grid")
HELPFUL_TEXTURES = EDGE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..13", "valid": "8..18"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_cyan":         {"type": "int", "default": "rng 2..5", "valid": "1..8"},
    "n_red_walls":    {"type": "int", "default": "rng 1..3", "valid": "0..6"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "rng", "valid": "rng"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "edge":           {"type": "str", "default": "rng",
                       "valid": "top|bottom|left|right"},
    "texture":        {"type": "str", "default": "alias for edge",
                       "valid": "top|bottom|left|right|no_cyan|no_edge|full_grid"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 8, 10)
        n_cyan = ctx.draw_int("n_cyan", 1, 3)
        n_red = ctx.draw_int("n_red_walls", 0, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 13, 18)
        n_cyan = ctx.draw_int("n_cyan", 4, 7)
        n_red = ctx.draw_int("n_red_walls", 3, 6)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 10, 13)
        n_cyan = ctx.draw_int("n_cyan", 2, 5)
        n_red = ctx.draw_int("n_red_walls", 1, 3)
    edge = (overrides.get("texture") if overrides.get("texture") in EDGE_KINDS else None) or \
           overrides.get("edge") or \
           ctx.draw_choice("edge", list(EDGE_KINDS))
    g = full_grid(h, w, 7)                  # orange background field (matches canonical)
    if edge == "top":
        for c in range(w): g[0][c] = 9
    elif edge == "bottom":
        for c in range(w): g[h - 1][c] = 9
    elif edge == "left":
        for r in range(h): g[r][0] = 9
    else:  # right
        for r in range(h): g[r][w - 1] = 9
    # Cyan cells in the interior
    for _ in range(120):
        if n_cyan <= 0: break
        r = rng.randint(2, h - 3)
        c = rng.randint(2, w - 3)
        if g[r][c] != 7: continue
        g[r][c] = 8
        n_cyan -= 1
    # Red walls
    for _ in range(120):
        if n_red <= 0: break
        r = rng.randint(2, h - 3)
        c = rng.randint(2, w - 3)
        if g[r][c] != 7: continue
        g[r][c] = 2
        n_red -= 1
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate orange field, exactly one maroon edge, and movable cyan cells."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    errors: list[str] = []
    h, w = len(grid), len(grid[0])
    allowed = {2, 7, 8, 9}
    bad = sorted({v for row in grid for v in row if v not in allowed})
    if bad:
        errors.append(f"unexpected colors outside {{2,7,8,9}}: {bad}")
    edges = {
        "top": all(grid[0][c] == 9 for c in range(w)),
        "bottom": all(grid[h - 1][c] == 9 for c in range(w)),
        "left": all(grid[r][0] == 9 for r in range(h)),
        "right": all(grid[r][w - 1] == 9 for r in range(h)),
    }
    full_edges = [name for name, ok in edges.items() if ok]
    if len(full_edges) != 1:
        errors.append(f"exactly one full maroon edge is required; saw {full_edges}")
    edge_cells = set()
    if full_edges:
        edge = full_edges[0]
        if edge == "top":
            edge_cells = {(0, c) for c in range(w)}
        elif edge == "bottom":
            edge_cells = {(h - 1, c) for c in range(w)}
        elif edge == "left":
            edge_cells = {(r, 0) for r in range(h)}
        else:
            edge_cells = {(r, w - 1) for r in range(h)}
    extra_maroon = [(r, c) for r in range(h) for c in range(w)
                    if grid[r][c] == 9 and (r, c) not in edge_cells]
    if extra_maroon:
        errors.append(f"maroon cells must be confined to the command edge; extras={extra_maroon[:5]}")
    cyan = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if not cyan:
        errors.append("at least one cyan mover is required")
    for r, c in cyan:
        if r in (0, h - 1) or c in (0, w - 1):
            errors.append(f"cyan mover must start in the interior, not on edge: {(r, c)}")
            break
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 9, 7)
    if name == "no_cyan":
        for c in range(9):
            g[0][c] = 9
        return g
    if name == "no_edge":
        g[4][4] = 8
        return g
    if name == "full_grid":
        for r in range(9):
            for c in range(9):
                g[r][c] = 9
        return g
    return g
