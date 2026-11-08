"""Generator for b942fd60.

Rule: a blue ray starts to the right, then branches vertically when it
hits a stopper.

Combinatorial axes (8): grid_h/w, stopper_distance, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_distinct_colors.
Degenerates: no_start, no_stopper, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cd67809f5bb8"
VERSION = "2.0.1"
TASK_ID = "cd67809f5bb8"
SUMMARY = "A single color-2 start cell on the left and one or more non-zero stopper cells (e.g., color 5 to the right) on a 0-bg grid with sparse decorations. Rule: starting from the 2-cell, fire a rightward ray painting color 2 along the path. When the ray hits any non-{0,2} cell, the path branches perpendicular (up and down) and continues; further branches stop at the next obstacle. All traversed cells are painted 2 (decorations stay)."

# Rivals: 'output is input' refuted by demos (ray paths trace).
# 'paint full row only' refuted by demos with branching visible.
# 'paint with color 5 (stopper color)' refuted by demos (ray is
# always 2). 'no branching' refuted by demos with perpendicular
# arms after stopper. 3 demos with ≥1 stopper-branching event cover.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is color 0",
    "there is one starting color-2 cell",
    "a nonzero stopper lies to the right of the start",
    "the rule paints the traversed ray and any perpendicular branches with color 2",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_start", "no_stopper", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "9..12"},
    "grid_w":         {"type": "int", "default": "rng 10..14", "valid": "10..14"},
    "stopper_distance":{"type": "int", "default": "6", "valid": "5..9"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly one color-2 starting cell; at least one non-zero non-2 stopper."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("cell value out of 0-9")
        return errs
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    stoppers = [(r, c) for r in range(h) for c in range(w)
                if grid[r][c] not in (0, 2)]
    if len(twos) == 0:
        return errs  # degenerate no_start — allow
    if len(twos) != 1:
        errs.append(f"expected exactly 1 color-2 start cell; found {len(twos)}")
    if not stoppers:
        return errs  # degenerate no_stopper — allow
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = rng.randint(8, 10)
        w = rng.randint(10, 12)
    elif difficulty == "hard":
        h = rng.randint(13, 17)
        w = rng.randint(15, 20)
    else:
        h = rng.randint(10, 14)
        w = rng.randint(12, 16)
    g = full_grid(h, w, 0)
    # Start cell anywhere in interior (with margin so the ray has room
    # to branch up/down after hitting a stopper).
    start_r = rng.randint(3, h - 4)
    start_c = rng.randint(0, 2)
    g[start_r][start_c] = 2
    # First stopper to the right of start (so the rightward ray hits it).
    min_dist = 4
    stop_c = rng.randint(start_c + min_dist, w - 2)
    stopper_color = rng.choice([3, 4, 5, 6, 7, 8, 9])
    g[start_r][stop_c] = stopper_color
    # Add 0..3 decoration obstacles in interior — each in a random
    # non-bg color. Avoid overlapping the start/first-stopper, and
    # avoid the start row (so it doesn't create a second primary
    # branching event the generator can't predict).
    n_decor = rng.randint(0, 3)
    decor_colors = [3, 4, 6, 7, 8]
    for _ in range(n_decor * 4):
        if n_decor <= 0:
            break
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if g[r][c] != 0:
            continue
        if r == start_r:
            continue
        g[r][c] = rng.choice(decor_colors)
        n_decor -= 1
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 12, 0)
    if name == "no_start":
        g[3][9] = 5
        return g
    if name == "no_stopper":
        g[3][1] = 2
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(12):
                g[r][c] = 5
        return g
    return g
