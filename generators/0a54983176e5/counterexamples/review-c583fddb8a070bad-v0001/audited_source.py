"""Generator for arc_puzzle_bank_21_set8_s:S8_H1 — mirror about an
8-marked axis, filling only empty cells.

Rule: the color-8 cells define the axis. All 8s in ONE column ->
vertical mirror about it; otherwise horizontal mirror about the FIRST
8-row. Every non-0/8 cell reflects, but a reflection paints ONLY onto
cells still 0 (existing content and earlier writes are preserved —
first-writer-wins). Out-of-bounds reflections clip. No 8s at all
degrades to identity (bridge-verified).

Combinatorial axes: grid_h/w, orientation, axis position, marker
count/placement, texture (plain|both_sides|clip|on_axis|dense).
Degenerates: no_content (axis only), no_axis (identity).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0a54983176e5"
VERSION = "2.0.1"
TASK_ID = "0a54983176e5"
SUMMARY = (
    "8-markers define a mirror axis; content reflects onto EMPTY "
    "cells only. both_sides boards put content on both sides "
    "(existing cells BLOCK the incoming reflection); clip boards use "
    "an off-center axis so reflections fall off-grid; on_axis boards "
    "put a non-8 cell in the axis line (self-blocked, stays single). "
    "Markers are 1-3 cells anywhere in the axis line. (Was: axis "
    "always dead-center with exactly 2 border-end markers, one-sided "
    "content only - blocking, clipping and marker freedom never "
    "shown.)"
)

# Rivals: 'mirror overwrites' refuted by both_sides (existing cells
# win). 'axis is the grid center' refuted by off-center axes. 'markers
# are 2 border dots' refuted by 1-3 mid-line markers. 3-4 demos with
# both orientations.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "vertical boards: all 8s share one column; horizontal: >=2 cols",
    "both_sides boards: >=1 reflection blocked by existing content",
    "clip boards: >=1 reflection out of bounds, >=1 visible",
]

DEGENERATE_TEXTURES = ("no_content", "no_axis")
HELPFUL_TEXTURES = ("plain", "both_sides", "clip", "on_axis", "dense")

AXES = {
    "grid_h":      {"type": "int", "default": "rng 7..12", "valid": "5..14"},
    "grid_w":      {"type": "int", "default": "rng 8..13", "valid": "7..16"},
    "orientation": {"type": "int", "default": "rng 0..1", "valid": "0..1",
                    "doc": "0 = vertical axis (column), 1 = horizontal"},
    "texture":     {"type": "str", "default": "rng helpful",
                    "valid": "plain|both_sides|clip|on_axis|dense|"
                             "no_content|no_axis",
                    "doc": "both_sides: existing cells block reflections; "
                           "clip: off-center axis, reflections spill "
                           "off-grid; on_axis: non-8 cell in the axis "
                           "line stays single."},
}

_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)


def _mirror(g):
    h, w = len(g), len(g[0])
    eights = [(r, c) for r in range(h) for c in range(w) if g[r][c] == 8]
    if not eights:
        return [row[:] for row in g]
    cols = sorted({c for _, c in eights})
    rows_ = sorted({r for r, _ in eights})
    out = [row[:] for row in g]
    if len(cols) == 1:
        b = cols[0]
        for r in range(h):
            for c in range(w):
                v = g[r][c]
                mc = 2 * b - c
                if v not in (0, 8) and 0 <= mc < w and out[r][mc] == 0:
                    out[r][mc] = v
    else:
        b = rows_[0]
        for r in range(h):
            for c in range(w):
                v = g[r][c]
                mr = 2 * b - r
                if v not in (0, 8) and 0 <= mr < h and out[mr][c] == 0:
                    out[mr][c] = v
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "both_sides",
                                              "clip", "on_axis", "dense"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 10)
        n_cells = (2, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 11, 13)
        n_cells = (5, 7)
    else:
        h = ctx.draw_int("grid_h", 7, 12)
        w = ctx.draw_int("grid_w", 8, 13)
        n_cells = (3, 6)
    rng = ctx.draw_rng("layout")
    vert = int(overrides.get("orientation",
                             ctx.draw_int("orientation", 0, 1))) == 0
    if not vert:
        # work transposed, flip back at the end
        h, w = w, h

    for _attempt in range(120):
        g = full_grid(h, w, 0)
        if texture == "clip":
            b = rng.choice([2, w - 3])
        else:
            b = rng.randint(2, w - 3)
        # markers: 1-3 8s in column b (>=2 when horizontal so the rule
        # sees >1 distinct col after transpose-back)
        n_marks = rng.randint(1 if vert else 2, 3)
        for r in rng.sample(range(h), n_marks):
            g[r][b] = 8
        n = rng.randint(*n_cells)
        if texture == "dense":
            n = rng.randint(7, 10)
        side = rng.choice([-1, 1])
        lo, hi = (0, b - 1) if side < 0 else (b + 1, w - 1)
        placed = []
        for _ in range(n):
            for _t in range(60):
                r = rng.randint(0, h - 1)
                c = rng.randint(lo, hi)
                if g[r][c] == 0:
                    g[r][c] = rng.choice(_COLORS)
                    placed.append((r, c))
                    break
        if texture == "both_sides":
            # opposite-side cells, >=1 exactly at a mirror target
            blocked = False
            for r, c in placed[:rng.randint(1, 3)]:
                mc = 2 * b - c
                if 0 <= mc < w and g[r][mc] == 0:
                    g[r][mc] = rng.choice(_COLORS)
                    blocked = True
            if not blocked:
                continue
        if texture == "on_axis":
            r = rng.choice([r for r in range(h) if g[r][b] == 0])
            g[r][b] = rng.choice(_COLORS)
        if texture == "clip":
            refl = [(r, 2 * b - c) for r, c in placed]
            if all(0 <= c < w for _, c in refl):
                continue
            if not any(0 <= c < w and g[r][c] == 0 for r, c in refl):
                continue
        out = _mirror(g)
        if out == g:
            continue
        if not vert:
            g = [list(row) for row in zip(*g)]
        return g
    raise ValueError("could not realize mirror board")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=1 color-8 cell forming a column or row axis AND >=1 non-{0,8} cell to reflect."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    eights = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    errors = []
    if not eights:
        errors.append("no color-8 cell (axis missing — rule reflects nothing)")
    else:
        non_bg_content = any(grid[r][c] not in (0, 8)
                             for r in range(h) for c in range(w))
        if not non_bg_content:
            errors.append("no non-{0,8} cell to reflect across the 8-axis")
    return errors


def _draw_from_degenerate(name, ctx):
    """no_content — markers only: nothing reflects, identity.
    no_axis — content but zero 8s: bridge-verified identity (the
    missing-axis arithmetic degrades to no writes). rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 7, 10)
    w = ctx.draw_int("grid_w", 8, 11)
    g = full_grid(h, w, 0)
    if name == "no_axis":
        for _ in range(rng.randint(2, 4)):
            g[rng.randint(0, h - 1)][rng.randint(0, w - 1)] = \
                rng.choice(_COLORS)
        return g
    b = rng.randint(2, w - 3)
    for r in rng.sample(range(h), rng.randint(2, 3)):
        g[r][b] = 8
    return g
