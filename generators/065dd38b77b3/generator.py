"""Generator for arc_additional_puzzles_21_set21_bundle:E143 — Reflect across uniform guide-row.

Rule: find first row that is uniformly one non-zero color. For each
non-zero cell ABOVE the guide-row, paint a copy at the reflected row
position below.

Combinatorial axes: grid_h, grid_w, n_marks, texture
(plain|clip|below_decor|multi_uniform).
Degenerates: no_marks, marks_below_guide (both identity). no_guide was
dropped — zero uniform rows crash the rule at (in-range #f).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "065dd38b77b3"
VERSION = "2.0.1"
TASK_ID = "065dd38b77b3"
SUMMARY = (
    "First uniformly-colored full row is the mirror axis; every non-"
    "zero cell ABOVE it is copy-reflected to (2*guide - r, c) (sources "
    "stay, out-of-bounds reflections vanish, destinations get over-"
    "written). Cells below the guide are preserved but never reflected. "
    "(Was: guide always mid-grid with full room, nothing below it, "
    "guide colors only {5,6,8}, no second uniform row, and a "
    "degenerate that crashed the rule.)"
)

# Rivals: 'reflection moves cells' refuted by kept sources. 'below
# cells reflect too' refuted by below_decor marks that stay. 'any
# uniform row works' refuted by multi_uniform (the FIRST/topmost row
# wins). 'reflections always fit' refuted by clip boards. 3-4 demos.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    ">=1 uniform full-width non-zero row ALWAYS (none -> the rule crashes at (in-range #f))",
    ">=2 marks above the guide on main path, >=1 reflecting in-bounds",
    "no accidental second uniform row above the intended guide",
]

DEGENERATE_TEXTURES = ("no_marks", "marks_below_guide")
HELPFUL_TEXTURES = ("plain", "clip", "below_decor", "multi_uniform")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 8..13", "valid": "6..16"},
    "grid_w":  {"type": "int", "default": "rng 6..10", "valid": "5..12"},
    "n_marks": {"type": "int", "default": "rng 3..6", "valid": "1..8"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|clip|below_decor|multi_uniform|"
                         "no_marks|marks_below_guide",
                "doc": "clip: guide low so some reflections fall off the "
                       "grid; below_decor: marks under the guide that stay "
                       "(may be overwritten by landing reflections); "
                       "multi_uniform: second uniform row below — the "
                       "topmost one is the axis."},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "clip", "below_decor", "multi_uniform"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 6, 8)
        n_marks = ctx.draw_int("n_marks", 3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 8, 10)
        n_marks = ctx.draw_int("n_marks", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 6, 10)
        n_marks = ctx.draw_int("n_marks", 3, 6)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")

    if texture == "clip":
        # guide in the lower third: high marks reflect off the grid
        guide_row = rng.randint((2 * h) // 3, h - 2)
    elif texture == "multi_uniform":
        guide_row = rng.randint(2, max(2, h // 2 - 1))
    else:
        guide_row = rng.randint(2, h - 3)
    guide_color = rng.randint(1, 9)
    for c in range(w):
        g[guide_row][c] = guide_color

    if texture == "multi_uniform":
        # a SECOND uniform row below: the rule's (first ...) ignores it
        second = rng.randint(guide_row + 2, h - 1)
        color2 = rng.randint(1, 9)
        for c in range(w):
            g[second][c] = color2

    palette = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    placed_in = placed_oob = 0
    for _ in range(150):
        if placed_in + placed_oob >= n_marks:
            break
        r = rng.randint(0, guide_row - 1)
        c = rng.randint(0, w - 1)
        if g[r][c] != 0:
            continue
        # a mark filling a row uniformly is impossible (w >= 5, sparse),
        # but a mark must not complete an accidental uniform row above
        oob = 2 * guide_row - r >= h
        if oob and texture != "clip":
            continue
        if oob and placed_oob >= 2:
            continue
        g[r][c] = rng.choice(palette)
        if oob:
            placed_oob += 1
        else:
            placed_in += 1
    if placed_in == 0:
        # always >=1 visible reflection
        for _ in range(80):
            r = rng.randint(max(0, 2 * guide_row - h + 1), guide_row - 1)
            c = rng.randint(0, w - 1)
            if g[r][c] == 0:
                g[r][c] = rng.choice(palette)
                break

    if texture == "below_decor":
        for _ in range(rng.randint(1, 3)):
            r = rng.randint(guide_row + 1, h - 1)
            c = rng.randint(0, w - 1)
            if g[r][c] == 0:
                g[r][c] = rng.choice(palette)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=1 uniform full-width non-zero row (the guide) AND >=1 non-zero cell above it."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    guide = next((r for r in range(h) if len(set(grid[r])) == 1 and grid[r][0] != 0), None)
    errors = []
    if guide is None:
        errors.append("no uniform non-zero full-width row (guide) found — rule crashes")
    else:
        marks_above = sum(1 for r in range(guide) for c in range(w) if grid[r][c] != 0)
        if marks_above == 0:
            errors.append("no non-zero marks above the guide row — rule is identity")
    return errors


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied so each board differs.

    no_marks          — guide row only: nothing reflects, identity.
    marks_below_guide — marks under the guide only: the rule scans
                        r < guide and finds nothing, identity.
    (no_guide dropped: zero uniform rows -> (first '()) = #f ->
    (in-range #f) CRASHES the rule.)
    """
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 8, 11)
    w = ctx.draw_int("grid_w", 6, 9)
    g = full_grid(h, w, 0)
    guide_row = rng.randint(2, h // 2)
    color = rng.randint(1, 9)
    for c in range(w):
        g[guide_row][c] = color
    if name == "marks_below_guide":
        for _ in range(rng.randint(2, 4)):
            r = rng.randint(guide_row + 1, h - 1)
            c = rng.randint(0, w - 1)
            g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 9])
    return g
