"""Generator for arc_puzzle_bank_21_set5_e:hard_e01 — shadow cast from light source.

Rule: find the unique color-4 cell on the grid BORDER (the light
source). Its position determines the ray direction (away from the
edge). For each non-bg, non-light cell, cast a ray in that direction.
Paint each cell along the ray with color 4 (the shadow), preserving
the original object cells.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "99d5bc858270"
VERSION = "2.1.0"
TASK_ID = "99d5bc858270"

SUMMARY = (
    "0-bg grid with: (a) exactly ONE color-4 cell on the grid BORDER "
    "(left edge, right edge, top edge, or bottom edge) — the light "
    "source; (b) several (1-4) scattered non-bg, non-4 colored cells "
    "in the interior. Rule: detect the light's border edge and use "
    "the direction AWAY from that edge (light on left → rays go right; "
    "etc.). For each non-bg, non-light cell, cast a ray in the chosen "
    "direction painting every 0-cell along the ray with color 4. The "
    "original object cells are preserved. Output: shadowed cells in 4, "
    "light source CLEARED to 0."
)

# Rivals: 'output is input' refuted by demos (shadows added).
# 'shadow goes toward the light' refuted by demos showing away.
# 'use color 8 for shadow' refuted by demos showing 4. 'shadow each
# object same as its color' refuted. 'light source preserved in
# output' refuted by demos showing it cleared. 4 demos with light at
# each of the 4 edges pin the direction-from-position rule.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly ONE color-4 cell on the grid border (not corner ideally)",
    "≥1 non-bg, non-4 cell in the interior",
    "the light's edge is unambiguous (only one edge contains the 4-cell)",
    "objects don't block each other's rays (they're at different rows/cols)",
]

# Free axes the runner may override. Keys match the keyed draw_int labels in
# generate(); defaults are the medium band, valid spans easy..hard.
AXES = {
    "grid_h":    {"type": "int", "default": "rng 8..11", "valid": "6..15",
                  "doc": "Grid height (easy 6..8, medium 8..11, hard 11..15)."},
    "grid_w":    {"type": "int", "default": "rng 9..13", "valid": "7..16",
                  "doc": "Grid width (easy 7..10, medium 9..13, hard 12..16)."},
    "n_objects": {"type": "int", "default": "rng 2..5", "valid": "1..7",
                  "doc": "Scattered shadow-casting cells (easy 1..3, medium 2..5, hard 4..7)."},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 7, 10)
        n_objects = ctx.draw_int("n_objects", 1, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 15)
        w = ctx.draw_int("grid_w", 12, 16)
        n_objects = ctx.draw_int("n_objects", 4, 7)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 13)
        n_objects = ctx.draw_int("n_objects", 2, 5)
    g = full_grid(h, w, 0)
    # Place light on one of 4 edges (interior of edge, not corners)
    edge = rng.choice(["top", "bottom", "left", "right"])
    if edge == "top":
        lr, lc = 0, rng.randint(1, w - 2)
    elif edge == "bottom":
        lr, lc = h - 1, rng.randint(1, w - 2)
    elif edge == "left":
        lr, lc = rng.randint(1, h - 2), 0
    else:
        lr, lc = rng.randint(1, h - 2), w - 1
    g[lr][lc] = 4
    # Place objects in interior (with some buffer from light position)
    palette = [1, 2, 3, 5, 6, 7, 8, 9]
    placed = 0
    used_projection = set()
    for _ in range(n_objects * 40):
        if placed >= n_objects:
            break
        r = rng.randint(1, h - 2)
        c = rng.randint(1, w - 2)
        if g[r][c] != 0:
            continue
        # Keep rays pedagogically separable: left/right lights cast by row;
        # top/bottom lights cast by column.  Reusing the same projection makes
        # two objects share a ray and hides an object/shadow branch.
        projection = r if edge in ("left", "right") else c
        if projection in used_projection:
            continue
        g[r][c] = rng.choice(palette)
        used_projection.add(projection)
        placed += 1
    if placed != n_objects:
        raise ValueError("could not place shadow-casting objects with unique rays")
    return g



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    lights = [(r, c) for r in range(h) for c in range(w)
              if grid[r][c] == 4 and (r in (0, h - 1) or c in (0, w - 1))]
    if len(lights) != 1:
        return [f"expected exactly one border light cell of color 4, found {len(lights)}"]
    lr, lc = lights[0]
    if (lr in (0, h - 1)) and (lc in (0, w - 1)):
        errs.append("light should not be on a corner; edge direction would be ambiguous")
    objects = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1) if grid[r][c] not in (0, 4)]
    if not objects:
        errs.append("expected at least one interior non-light object")
    projection = [r if lc in (0, w - 1) else c for r, c in objects]
    if len(projection) != len(set(projection)):
        errs.append("two objects share a shadow ray projection, hiding a branch")
    return errs
