"""Generator for arc_puzzle_bank_21_set15:S15_E4.

Combinatorial axes (8): height, width, palette_kind, candidate_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_source, no_match, multi_match.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1a21a4a82b48"
VERSION = "2.1.1"  # outer reset-retry: 5th shape can wedge on easy 9x11 (_place raises, no outer reset)
TASK_ID = "1a21a4a82b48"
SUMMARY = (
    "0-bg grid (h ∈ 9-20, w ∈ 11-22, by "
    "difficulty) with: (a) ONE COLOR-2 "
    "RED SOURCE SHAPE drawn from "
    "_SHAPES bank (5 variants of 4-cell "
    "L/S/T/P shapes) — placed at a "
    "random non-overlapping position "
    "via _place (1-cell padding); "
    "(b) ONE MATCHING CANDIDATE in "
    "colors[0] (drawn from {3,4,5,6}) "
    "with the SAME shape (translation-"
    "only equivalent) placed elsewhere; "
    "(c) THREE DISTRACTOR CANDIDATES "
    "in colors[1:] (each a DIFFERENT "
    "shape from _SHAPES \\ {source}), "
    "all placed at non-overlapping "
    "positions. Rule (FIND THE "
    "CANDIDATE WHOSE NORMALIZED CELL "
    "OFFSETS MATCH THE COLOR-2 "
    "SOURCE'S, CROP TO ITS BBOX, "
    "RECOLOR TO CYAN-8, OUTPUT): "
    "FIND the unique COLOR-2 "
    "component → extract its "
    "NORMALIZED OFFSETS (subtract "
    "min row/col). FOR EACH non-2 "
    "non-bg COMPONENT: COMPUTE its "
    "normalized offsets. SELECT the "
    "unique component whose offsets "
    "EQUAL the source's offsets. "
    "CROP it to its bbox. RECOLOR "
    "every cell of that crop to "
    "COLOR 8 (cyan). OUTPUT the "
    "cyan crop. Net: same-shape "
    "matching across colors yields "
    "a cyan version of the matched "
    "candidate. Flagged intrinsic-"
    "low (uniq_out=5): 5 source "
    "shapes × cyan recolor = 5 "
    "canonical outputs."
)

# Rivals: 'output is input' refuted by demos (output is small).
# 'use the source itself' refuted by demos where source and match
# are at different positions. 'use the matching candidate's
# original color' refuted by demos (output is always 8). 'pick by
# size, not shape' refuted by demos where matching candidate is
# same size as some non-matches. 3 demos with ≥3 distractors cover.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "there is exactly one color-2 source component",
    "exactly one candidate component in colors 3..6 has the same normalized offsets",
    "all distractor candidates have different normalized offsets",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_source", "no_match", "multi_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "height":         {"type": "int", "default": "rng 10..13", "valid": "8..20"},
    "width":          {"type": "int", "default": "rng 12..15", "valid": "10..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "candidate_count": {"type": "int", "default": "4", "valid": "3..5"},
    "palette_size":   {"type": "int", "default": "5", "valid": "4..6"},
    "position_bias":  {"type": "str", "default": "source_plus_candidates",
                       "valid": "source_plus_candidates"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "4..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_source|no_match|multi_match"},
}

_SHAPES = [
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (1, 1), (1, 2)],
    [(0, 1), (1, 0), (1, 1), (1, 2)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (1, 0), (2, 0)],
]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, exactly one color-2 source shape, 3+ other colored shapes."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in ("no_source", "no_match", "multi_match"):
        return errs
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    others = {grid[r][c] for r in range(h) for c in range(w)
              if grid[r][c] not in (0, 2)}
    if not twos:
        errs.append("no color-2 source shape cells found")
    if len(others) < 1:
        errs.append("no candidate shapes (non-0, non-2) found")
    return errs


def _size(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _free_box(g, r0, c0, sh, sw, pad=1):
    h, w = len(g), len(g[0])
    if r0 < 0 or c0 < 0 or r0 + sh > h or c0 + sw > w:
        return False
    for r in range(max(0, r0 - pad), min(h, r0 + sh + pad)):
        for c in range(max(0, c0 - pad), min(w, c0 + sw + pad)):
            if g[r][c] != 0:
                return False
    return True


def _paint(g, r0, c0, shape, color):
    for dr, dc in shape:
        g[r0 + dr][c0 + dc] = color


def _place(g, rng, shape, color):
    sh, sw = _size(shape)
    h, w = len(g), len(g[0])
    for _ in range(120):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        if _free_box(g, r0, c0, sh, sw):
            _paint(g, r0, c0, shape, color)
            return
    raise ValueError("could not place component")


def _rand_blob(rng, k):
    """Connected blob of k cells, normalized to top-left (matches the rule's
    relative-offsets anchor 0)."""
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc))
            seen.add((r + dr, c + dc))
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return [(r - r0, c - c0) for r, c in cells]


def _sig(shape):
    return tuple(sorted((r, c) for r, c in shape))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("height", 9, 11)
        w = ctx.draw_int("width", 11, 13)
        k_lo, k_hi, n_dist = 4, 5, 2
    elif difficulty == "hard":
        h = ctx.draw_int("height", 15, 20)
        w = ctx.draw_int("width", 17, 22)
        k_lo, k_hi, n_dist = 6, 12, ctx.draw_int("n_dist", 3, 4)
    else:
        h = ctx.draw_int("height", 11, 14)
        w = ctx.draw_int("width", 13, 17)
        k_lo, k_hi, n_dist = 5, 8, ctx.draw_int("n_dist", 2, 3)
    rng = ctx.draw_rng("layout")
    ksrc = ctx.draw_int("src_size", k_lo, k_hi)
    # DISTINCT-LOCKED FIX: output = the source shape recolored to 8, but the old
    # gen drew the source from only 5 fixed 4-cell shapes -> distinct_out=5. Now
    # the source/target is a VARIED random blob (varied size, non-square), and the
    # distractors are verified to have a DIFFERENT normalized shape so the match
    # stays unique. Reset-and-retry the whole layout on a placement wedge.
    for _outer in range(60):
        g = full_grid(h, w, 0)
        try:
            source = _rand_blob(rng, ksrc)
            ssig = _sig(source)
            colors = ctx.draw_distinct_colors("cand_colors",
                                              n=1 + n_dist, exclude={0, 1, 2})
            _place(g, rng, source, 2)            # the unique color-2 source
            _place(g, rng, source, colors[0])    # the matching candidate (same shape)
            for color in colors[1:]:             # distractors: different shapes
                for _try in range(60):
                    d = _rand_blob(rng, rng.randint(4, max(4, ksrc + 2)))
                    if _sig(d) != ssig:
                        _place(g, rng, d, color)
                        break
                else:
                    raise ValueError("no distinct distractor shape")
            return g
        except ValueError:
            continue
    raise ValueError("could not place component")


def _draw_from_degenerate(name, rng):
    h, w = 11, 13
    g = full_grid(h, w, 0)
    if name == "no_source":
        # No color-2 source — rule has no shape to compare against.
        for dr, dc in _SHAPES[0]: g[2 + dr][2 + dc] = 3
        for dr, dc in _SHAPES[1]: g[2 + dr][7 + dc] = 4
        return g
    if name == "no_match":
        # Source present but no candidate has the same shape — rule selects nothing.
        for dr, dc in _SHAPES[0]: g[2 + dr][2 + dc] = 2
        for dr, dc in _SHAPES[1]: g[2 + dr][7 + dc] = 3
        for dr, dc in _SHAPES[2]: g[6 + dr][2 + dc] = 4
        return g
    if name == "multi_match":
        # Two candidates match the source shape — match is non-unique.
        for dr, dc in _SHAPES[0]: g[2 + dr][2 + dc] = 2
        for dr, dc in _SHAPES[0]: g[2 + dr][7 + dc] = 3
        for dr, dc in _SHAPES[0]: g[7 + dr][2 + dc] = 4
        return g
    return g
