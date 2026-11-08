"""Generator for arc_additional_puzzles_21_set7:H46 — Manhattan-tie cells inside a frame.

Rule (verified from canonical Racket): find a rectangular-BORDER frame; read the
first two interior cells that are non-zero and not the frame colour (the SEEDS a
and b); redraw the frame and the two seeds on a blank grid, then mark with colour
9 every interior cell whose Manhattan distance to a equals its distance to b (the
perpendicular bisector between the seeds).

The previous body was the generic scatter template; it usually produced no
rectangular frame and/or fewer than two interior seeds, so `(first ...)` /
`(second seeds)` crashed (~3/9). This rewrite CONSTRUCTS a rectangular frame plus
exactly two interior seed cells (the only non-zero, non-frame-colour interior
cells), so the bisector is always well defined.

Axes: grid size, frame box, frame colour, the two seed positions/colours.
Degenerates: seeds_adjacent, seeds_same_row, seeds_corner.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "39abddf600eb"
VERSION = "2.2.0"  # FIX: Manhattan-equidistant set is EMPTY when the two seeds have opposite checkerboard parity (d(x,a)-d(x,b) is always odd) -> bisector empty -> output==input (identity). Now require the two seeds to share parity so the bisector is non-empty. Adds self_check.
TASK_ID = "39abddf600eb"

SUMMARY = ("A rectangular frame holds exactly two interior seed cells; the rule redraws the "
           "frame and seeds and paints colour-9 on every interior cell equidistant (Manhattan) "
           "from both seeds — the bisector. Frame box, frame colour and seed positions vary.")

INVARIANTS = [
    "exactly one rectangular-border frame (single colour)",
    "exactly two interior cells are non-zero and not the frame colour (the seeds)",
    "seeds lie strictly inside the frame (and off the grid border)",
]

DEGENERATE_TEXTURES = ("seeds_adjacent", "seeds_same_row", "seeds_corner")
HELPFUL_TEXTURES = ("default", "warm", "cool", "varied")

AXES = {
    "grid_h":     {"type": "int", "default": "rng 10..13", "valid": "8..16"},
    "grid_w":     {"type": "int", "default": "rng 11..14", "valid": "8..18"},
    "frame_color":{"type": "int", "default": "rng 2..8 (not 9)", "valid": "2..8"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "default|warm|cool|varied"},
    "density":    {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":    {"type": "str", "default": "alias for palette_kind",
                   "valid": "default|warm|cool|varied|seeds_adjacent|seeds_same_row|seeds_corner"},
}


def _draw_frame(g, r1, c1, r2, c2, color):
    for c in range(c1, c2 + 1):
        g[r1][c] = color; g[r2][c] = color
    for r in range(r1, r2 + 1):
        g[r][c1] = color; g[r][c2] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10); w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 14); w = ctx.draw_int("grid_w", 13, 16)
    else:
        h = ctx.draw_int("grid_h", 10, 12); w = ctx.draw_int("grid_w", 11, 14)
    fcolor = ctx.draw_int("frame_color", 2, 8)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    # frame box, inset >=1 from every grid edge, interior at least 3x3
    r1 = rng.randint(1, 2); c1 = rng.randint(1, 2)
    r2 = rng.randint(h - 3, h - 2); c2 = rng.randint(w - 3, w - 2)
    if r2 - r1 < 4:
        r2 = min(h - 2, r1 + 4)
    if c2 - c1 < 4:
        c2 = min(w - 2, c1 + 4)
    _draw_frame(g, r1, c1, r2, c2, fcolor)

    # two distinct interior seed cells (strictly inside the frame), non-fcolor.
    # The Manhattan-equidistant set (the rule's painted bisector) is EMPTY unless
    # the two seeds share checkerboard parity ((r+c) even/odd): otherwise
    # d(x,a)-d(x,b) is odd everywhere and never zero -> output == input. Require
    # same-parity seeds so the bisector always has at least one interior cell.
    interior = [(r, c) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)]
    a = rng.choice(interior)
    same_parity = [p for p in interior
                   if p != a and (p[0] + p[1]) % 2 == (a[0] + a[1]) % 2]
    b = rng.choice(same_parity)
    seed_colors = [col for col in (1, 2, 3, 4, 5, 6, 7, 8) if col != fcolor]
    g[a[0]][a[1]] = rng.choice(seed_colors)
    g[b[0]][b[1]] = rng.choice(seed_colors)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Exactly two interior non-frame seeds that share checkerboard parity, so the
    Manhattan-equidistant bisector the rule paints is non-empty (no identity)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    # frame color = the single color forming the rectangular border (most common
    # non-zero); seeds = interior non-zero, non-frame cells.
    from collections import Counter
    cnt = Counter(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if not cnt:
        return ["empty grid"]
    fcolor = cnt.most_common(1)[0][0]
    seeds = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)
             if grid[r][c] not in (0, fcolor)]
    errors = []
    if len(seeds) != 2:
        errors.append(f"expected exactly 2 interior seeds, found {len(seeds)}")
        return errors
    a, b = seeds
    if (a[0] + a[1]) % 2 != (b[0] + b[1]) % 2:
        errors.append("seeds have opposite parity — Manhattan bisector is empty, "
                      "output would equal input (identity)")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 11, 12
    g = full_grid(h, w, 0)
    r1, c1, r2, c2 = 1, 1, 9, 10
    _draw_frame(g, r1, c1, r2, c2, 5)
    if name == "seeds_adjacent":
        # adjacent seeds -> a thin bisector between them
        a, b = (4, 5), (4, 6)
    elif name == "seeds_same_row":
        # same row -> vertical bisector line
        a, b = (4, 3), (4, 8)
    else:  # seeds near opposite corners of the interior
        a, b = (2, 2), (8, 9)
    g[a[0]][a[1]] = 2
    g[b[0]][b[1]] = 3
    return g
