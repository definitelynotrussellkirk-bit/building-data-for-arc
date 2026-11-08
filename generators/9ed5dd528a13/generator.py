"""Generator for arc_puzzle_bank_21_set9_e:hard_i16 — last-row transform program over a template.

Rule (verified from canonical Racket): rows 0..h-2 hold a single TEMPLATE shape
(bbox-cropped). The LAST ROW is a left-to-right sequence of TRANSFORM-CODE
markers: 1=identity, 2=rotate-CW, 3=rotate-180, else=flip-LR. Output: the
template rendered in each marker's orientation, hstacked with 1-col gaps.

The previous body was the generic scatter template (its own docstring admitted
"NOT yet matched by this generator"): scattered motifs left the last row empty,
so `markers` was empty and the rule crashed (`(apply max (map rows '()))` -> max
arity, ~3/6). This rewrite CONSTRUCTS valid inputs: a template in rows 0..h-2 and
N transform-code markers in the last row.

Axes: grid size, template shape/colour, marker count, transform codes.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9ed5dd528a13"
VERSION = "2.1.1"  # FIX: was generic scatter (admittedly mismatched) -> empty last-row markers crashed rule (max arity). Now template + last-row transform codes.
TASK_ID = "9ed5dd528a13"

SUMMARY = (
    "Rows 0..h-2 hold one TEMPLATE shape; the LAST ROW is a sequence of "
    "transform-code markers (1=identity, 2=rotate-CW, 3=rotate-180, else=flip-LR). "
    "Rule: render the template in each marker's orientation, hstacked with 1-col "
    "gaps. Template shape/colour, marker count and codes vary."
)

INVARIANTS = [
    "rows 0..h-2 contain one connected template shape",
    "the last row holds >=1 transform-code marker (values 1-4)",
    "the template fits within h-1 rows",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n":              {"type": "int", "default": "2-3 easy / 3-4 med / 4-5 hard markers", "valid": "1..6"},
    "position_bias":  {"type": "str", "default": "template_above_marker_row",
                       "valid": "template_above_marker_row"},
    "n_distinct_colors": {"type": "int", "default": "1 (template)", "valid": "1..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_motifs|single_motif|all_same_color"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """rows 0..h-2 have template cells; last row has >=1 transform-code marker (1-4)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h = len(grid)
    if h < 2:
        return [f"grid height {h} < 2 (need template + marker row)"]
    errs = []
    # Last row must have at least one non-zero cell (transform marker)
    last_row = grid[h - 1]
    if not any(v != 0 for v in last_row):
        errs.append("last row has no transform-code marker (all zeros)")
    # Body (rows 0..h-2) must have at least one non-zero cell (template)
    if not any(grid[r][c] != 0 for r in range(h - 1) for c in range(len(grid[0]))):
        errs.append("template body (rows 0..h-2) has no non-zero cells")
    return errs


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 11, 11)
        n = ctx.draw_int("n", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 13, 16)
        n = ctx.draw_int("n", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
        n = ctx.draw_int("n", 3, 4)
    rng = ctx.draw_rng("layout")
    n_markers = min(n, w)   # markers occupy distinct columns in the last row

    g = full_grid(h, w, 0)
    # TEMPLATE: one connected shape in rows 0..h-2 (the body), single colour
    body_h = h - 1
    cells = _build_motif(rng, rng.randint(3, 6))
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
    sh = min(sh, body_h); sw = min(sw, w)
    color = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
    tr = rng.randint(0, max(0, body_h - sh)); tc = rng.randint(0, max(0, w - sw))
    for r, c in cells:
        rr, cc = tr + r - min(rs), tc + c - min(cs)
        if rr < body_h and cc < w:
            g[rr][cc] = color
    # LAST ROW: transform-code markers (1=identity,2=cw,3=180,4=flip-lr)
    marker_cols = sorted(rng.sample(range(w), n_markers))
    for mc in marker_cols:
        g[h - 1][mc] = rng.choice([1, 2, 3, 4])
    return g
    raise ValueError("could not realize layout")


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # Empty grid — rule has no motifs to gather.
        return g
    if name == "single_motif":
        # Only 1 motif — rule's gallery is trivial.
        for r, c in [(2, 2), (2, 3), (3, 3), (3, 4)]: g[r][c] = 4
        return g
    if name == "all_same_color":
        # All motifs share a color — rule's per-color gather treats
        # them as one big component.
        for r, c in [(1, 1), (1, 2), (2, 2)]: g[r][c] = 4
        for r, c in [(5, 6), (5, 7), (6, 7)]: g[r][c] = 4
        for r, c in [(8, 1), (8, 2), (9, 2)]: g[r][c] = 4
        return g
    return g
