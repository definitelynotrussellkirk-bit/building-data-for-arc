"""Generator for ARC task be03b35f.

Rule: `(rule! (lambda (g) (crop (rotate-cw g) 0 0 (- (quotient (rows g) 2) 1) (- (quotient (cols g) 2) 1))))`.
Rotate the grid 90° clockwise, then crop the top-left quadrant
(approximately h/2 × w/2 of the rotated grid).

Combinatorial axes:
  * side                 — odd square side (rule expects square input)
  * texture              — pattern: noise/sparse/blob/stripes/checker/...
  * palette_size         — distinct fg colors
  * fill_density         — coverage
  * cropped_kind         — what the rotated top-left quadrant looks like:
                            mixed / two_colors / palette
  * caller-opt-in degenerates: monochrome, single_pixel, all_bg
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.textures import (
    fill_texture, apply_bg_density, apply_noise_overlay,
)

GENERATOR_ID = "9a6d26c37c72"
VERSION = "1.2.0"  # all-blank fix: high bg density left the input's bottom-left quadrant (the rotate-cw top-left crop's source) empty -> all-bg output. Now guarantee >=2 fg colors in that quadrant.
TASK_ID = "9a6d26c37c72"
SUMMARY = "An odd square grid; the rule rotates 90° CW and crops the top-left quadrant."

INVARIANTS = [
    "input is an odd square (side ∈ {5, 7, 9, 11, 13})",
    "background is 0",
    "≥2 fg colors so the cropped+rotated output has variety",
]

HELPFUL_TEXTURES = (
    "noise", "sparse", "blob", "stripes",
    "gradient", "checkerboard", "frame", "ring", "plus",
)
DEGENERATE_TEXTURES = ("monochrome", "single_pixel", "all_bg")

AXES = {
    "side":          {"type": "choice", "default": "rng odd 5..13",
                      "valid": "5|7|9|11|13"},
    "texture":       {"type": "str",    "default": "rng helpful",
                      "valid": "noise|sparse|blob|stripes|gradient|checkerboard|frame|ring|plus|monochrome|single_pixel|all_bg"},
    "palette_size":  {"type": "int",    "default": "rng 2..5", "valid": "1..9"},
    "fill_density":  {"type": "float",  "default": "rng 0.3..0.7", "valid": "0.1..1.0"},
    "noise_overlay": {"type": "float",  "default": "rng 0..0.05", "valid": "0..0.3"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    # The canonical task is not a generic rotate+crop texture task.  Every
    # example is a compact 5x5 board with a zero middle row/column, a signal
    # pattern in the bottom-left 2x2 quadrant (the exact source of the
    # rotate-cw/top-left crop), and a bottom-right distractor block.  The old
    # generator sampled 7..13 boards and full-grid noise/checkers, producing
    # object-count/area drift and teaching the wrong visual family.
    rng = ctx.draw_rng("canonical_family")
    side = 5
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], side, rng)

    palette = ctx.draw_distinct_colors("palette", n=2, exclude={0})
    signal, distractor = palette[0], palette[1]
    g = full_grid(side, side, 0)

    # Bottom-right distractor: canonical examples carry a separate 2x2 block
    # of a second color that is deliberately outside the crop source.
    for r in (3, 4):
        for c in (3, 4):
            g[r][c] = distractor

    # Bottom-left source quadrant.  Keep it compact and visibly non-solid so
    # the output is not a trivial constant bar, but still canonical-scale.
    # All 2x2 binary source patterns except blank and solid.  This keeps
    # canonical scale while still giving the rule-smoke/diversity gate enough
    # distinct outputs across seeds.
    patterns = [
        tuple(tuple((mask >> (3 - (rr * 2 + cc))) & 1 for cc in range(2))
              for rr in range(2))
        for mask in range(1, 15)
        if 2 <= bin(mask).count("1") <= 3
    ]
    pat = patterns[ctx.draw_int("source_pattern", 0, len(patterns) - 1)]
    for rr, row in enumerate(pat, start=3):
        for cc, bit in enumerate(row):
            if bit:
                g[rr][cc] = signal

    # Top half: sparse same-color context/distractors, while preserving the
    # all-zero middle row/column seen in canonical.  These cells are outside
    # the rule's source quadrant and help refute "copy the bottom-left block".
    top_sites = [(0, 0), (0, 1), (1, 0), (1, 1), (0, 3), (0, 4), (1, 3), (1, 4)]
    rng.shuffle(top_sites)
    n_top = ctx.draw_int("top_context_cells", 3, 6)
    for r, c in top_sites[:n_top]:
        g[r][c] = signal
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Canonical 5x5 rotate-crop family for 9a6d26c37c72.

    The learned rule crops the top-left 2x2 of rotate-cw(grid), i.e. the
    original bottom-left 2x2.  A good training instance must therefore make
    that source quadrant visible, non-empty, and not drown it in full-grid
    texture noise.
    """
    errs: list[str] = []
    if not grid or not grid[0]:
        return ["empty grid"]
    if len(grid) != 5 or any(len(row) != 5 for row in grid):
        errs.append("input must be canonical 5x5")
        return errs
    vals = {v for row in grid for v in row}
    fg = vals - {0}
    if len(fg) != 2:
        errs.append(f"expected exactly two non-bg colors, got {sorted(fg)}")
    if any(grid[2][c] != 0 for c in range(5)) or any(grid[r][2] != 0 for r in range(5)):
        errs.append("middle row and middle column must stay zero separators")
    source = [grid[r][c] for r in (3, 4) for c in (0, 1)]
    src_fg = [v for v in source if v != 0]
    if len(src_fg) < 2:
        errs.append("bottom-left source quadrant is too sparse")
    if len(set(source)) < 2:
        errs.append("bottom-left source quadrant is solid/constant")
    # The second color should be a compact distractor outside the source.
    if len(fg) == 2:
        counts = {c: sum(v == c for row in grid for v in row) for c in fg}
        distractor = min(counts, key=counts.get)
        if any(grid[r][c] != distractor for r in (3, 4) for c in (3, 4)):
            errs.append("bottom-right 2x2 distractor block is missing")
    return errs

def _draw_from_degenerate(name, side, rng):
    """Edge-case where the rotate+crop signal is hidden.

    monochrome   — uniform input → uniform output of half-size.
    single_pixel — one fg pixel; the rotated/cropped output may be
                    blank or one-pixel depending on placement.
    all_bg       — entirely bg; output is all bg of half-size.
    """
    g = full_grid(side, side, 0)
    palette = list(range(1, 10))
    rng.shuffle(palette)
    if name == "monochrome":
        c = palette[0]
        for r in range(side):
            for cc in range(side):
                g[r][cc] = c
        return g
    if name == "single_pixel":
        rr = rng.randint(0, side - 1); rc = rng.randint(0, side - 1)
        g[rr][rc] = palette[0]
        return g
    if name == "all_bg":
        return g
    return g
