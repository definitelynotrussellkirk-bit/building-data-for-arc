"""Generator for arc_puzzle_bank_21_set9_e:easy_i07.

Rule: copy upper half into lower half by vertical mirroring.

Combinatorial axes: grid_h, grid_w, top_marks, texture
(plain|dense_top|scatter_noise).
Degenerates: empty_top (lower wiped), top_already_mirrors_bottom
(identity), odd_height (bridge-degraded, non-crashing).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "08b346c559d6"
VERSION = "3.0.1"
TASK_ID = "08b346c559d6"
SUMMARY = (
    "0-bg grid (h EVEN ~6-8, w~6-9). UPPER HALF "
    "(rows 0..h/2-1) contains 3-6 SOURCE MARKER cells "
    "scattered at random positions in various non-bg "
    "colors. LOWER HALF (rows h/2..h-1) often "
    "contains DISTRACTOR rows — each row painted in "
    "a single solid color from 1..9 with ~75% "
    "probability — that will be OVERWRITTEN by the "
    "rule. Rule: COPY the UPPER HALF into the LOWER "
    "HALF using a VERTICAL MIRROR — for each cell "
    "(r, c) in the upper half (r < h/2), PAINT "
    "(h-1-r, c) with the value of (r, c). The "
    "distractors in the lower half are OVERWRITTEN. "
    "Net: input has an upper-half pattern + random "
    "lower-half noise; output is the grid with "
    "vertical mirror symmetry about the horizontal "
    "midline."
)

INVARIANTS = [
    "background is 0",
    "height is even",
    "upper half is the source pattern",
    "lower half may contain distractors that are overwritten",
]

# Rivals: 'lower half is preserved where non-empty' refuted by every
# noise kind being overwritten (solid rows, scatter, blobs). 'copy
# without mirroring' refuted by asymmetric top patterns. 3 demos with
# different noise kinds.
EXAMPLES_NEEDED = 3

DEGENERATE_TEXTURES = ("empty_top", "top_already_mirrors_bottom",
                       "odd_height")
HELPFUL_TEXTURES = ("plain", "dense_top", "scatter_noise")

AXES = {
    "grid_h":    {"type": "int", "default": "rng even 6..10", "valid": "4..14"},
    "grid_w":    {"type": "int", "default": "rng 6..10", "valid": "4..16"},
    "top_marks": {"type": "int", "default": "rng 3..8", "valid": "1..20"},
    "texture":   {"type": "str", "default": "rng helpful",
                  "valid": "plain|dense_top|scatter_noise|"
                           "empty_top|top_already_mirrors_bottom|odd_height",
                  "doc": "scatter_noise: lower-half noise is scattered "
                         "cells instead of solid rows (all overwritten); "
                         "odd_height: bridge-degraded but non-crashing."},
}

_COLORS = (1, 2, 3, 4, 5, 6, 7, 8, 9)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "dense_top", "scatter_noise"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 6)
        w = ctx.draw_int("grid_w", 6, 7)
        marks = ctx.draw_int("top_marks", 3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 8, 10)
        marks = ctx.draw_int("top_marks", 6, 8)
    else:
        h = ctx.draw_int("grid_h", 6, 10)
        w = ctx.draw_int("grid_w", 6, 10)
        marks = ctx.draw_int("top_marks", 3, 7)
    if h % 2:
        h += 1
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    half = h // 2

    if texture == "dense_top":
        # a connected blob + scatter: richer source pattern
        r0, c0 = rng.randrange(half), rng.randrange(w)
        cells = {(r0, c0)}
        for _ in range(40):
            if len(cells) >= marks:
                break
            r, c = list(cells)[rng.randrange(len(cells))]
            dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
            if 0 <= r + dr < half and 0 <= c + dc < w:
                cells.add((r + dr, c + dc))
        color = rng.choice(_COLORS)
        for r, c in cells:
            g[r][c] = color
        for _ in range(rng.randint(1, 3)):
            g[rng.randrange(half)][rng.randrange(w)] = rng.choice(_COLORS)
    else:
        top_cells = [(r, c) for r in range(half) for c in range(w)]
        for r, c in rng.sample(top_cells, min(marks, len(top_cells))):
            g[r][c] = rng.choice(_COLORS)

    if texture == "scatter_noise":
        for _ in range(rng.randint(3, 8)):
            g[rng.randint(half, h - 1)][rng.randrange(w)] = rng.choice(_COLORS)
    else:
        for r in range(half, h):
            if rng.random() < 0.75:
                color = rng.choice(_COLORS)
                g[r] = [color for _ in range(w)]
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Height must be even AND upper half must contain >=1 non-zero cell."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    if h % 2 != 0:
        errors.append(f"height {h} is odd (rule's row mapping is undefined)")
    else:
        half = h // 2
        upper_marks = sum(1 for r in range(half) for c in range(w) if grid[r][c] != 0)
        if upper_marks == 0:
            errors.append("upper half is blank — rule copies nothing (degenerate)")
    return errors


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied so each board differs.

    empty_top                  — blank top: lower half wiped to zeros.
    top_already_mirrors_bottom — symmetric input: identity.
    odd_height                 — odd h: the row map runs to index -1,
                                 which the bridge tolerates (degraded
                                 but non-crashing, verified).
    """
    rng = ctx.draw_rng("degenerate_layout")
    w = ctx.draw_int("grid_w", 6, 9)
    if name == "odd_height":
        h = ctx.draw_int("grid_h", 7, 7)
        g = full_grid(h, w, 0)
        for _ in range(rng.randint(3, 5)):
            g[rng.randrange(3)][rng.randrange(w)] = rng.choice(_COLORS)
        return g
    h = ctx.draw_int("grid_h", 6, 8)
    if h % 2:
        h += 1
    g = full_grid(h, w, 0)
    half = h // 2
    if name == "empty_top":
        for r in range(half, h):
            if rng.random() < 0.7:
                color = rng.choice(_COLORS)
                g[r] = [color for _ in range(w)]
        return g
    for _ in range(rng.randint(2, 4)):
        r = rng.randrange(half)
        c = rng.randrange(w)
        color = rng.choice(_COLORS)
        g[r][c] = color
        g[h - 1 - r][c] = color
    return g
