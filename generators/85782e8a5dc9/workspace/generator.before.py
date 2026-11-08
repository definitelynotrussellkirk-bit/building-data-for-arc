"""Generator for arc_additional_puzzles_21_set16_bundle:M106 — A:B::C:? transform analogy.

Rule: split input by blank columns into 3 framed panels (5-frame).
Find the transform code that maps A's interior to B's interior, then
apply it to C's interior. Output is C transformed.

Combinatorial axes (8): interior_size, n_marks, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_panels, identity_transform, mismatched_transform.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import (
    full_grid, fill_box, transpose, rot90_cw, rot180, flip_lr, flip_ud, cmirror,
)
from puzzle_generators.helpers.selfcheck import components, components_have_clearance, color_counts, has_row_gap, interior_cells, is_full_frame_component, norm

GENERATOR_ID = "85782e8a5dc9"
VERSION = "2.0.0"
TASK_ID = "85782e8a5dc9"
SUMMARY = (
    "0-bg grid (h = panel_size, "
    "w = 3*panel_size + 2) "
    "with 3 PANELS separated "
    "by BLANK (0) COLUMNS, "
    "each panel a "
    "panel_size×panel_size "
    "COLOR-5 (gray) RECT-"
    "OUTLINE FRAME with "
    "interior of size isize×"
    "isize (isize~3-4). "
    "Interior pattern of each "
    "panel has 4-6 cells in "
    "colors {1, 2, 3, 4}: "
    "PANEL A has random "
    "PATTERN_A, PANEL B = "
    "TRANSFORM_T(PATTERN_A) "
    "where T ∈ {identity, "
    "rot90, rot180, transpose, "
    "flip_lr, flip_ud, "
    "cmirror}, PANEL C has "
    "random PATTERN_C "
    "(unrelated). Rule "
    "(SOLVE A:B::C:? "
    "ANALOGY): identify "
    "the 3 PANELS' INTERIORS. "
    "INFER the TRANSFORM T "
    "such that B = T(A). "
    "APPLY T to C's INTERIOR. "
    "EMIT the transformed C "
    "(or full output with C "
    "interior replaced). "
    "Net: A:B::C:T(C) "
    "analogy applied to the "
    "C panel."
)

INVARIANTS = [
    "exactly 3 panels separated by blank columns",
    "each panel is a full 5-color rectangle frame with a small interior pattern",
    "panel B's interior = some transform T applied to A's interior",
    "panel C's interior is unrelated; output is C transformed by the same T",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_panels", "identity_transform", "mismatched_transform")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "interior_size":  {"type": "int", "default": "rng 3..4", "valid": "3..6"},
    "n_marks":        {"type": "int", "default": "rng 4..6", "valid": "3..10"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "5", "valid": "4..6"},
    "position_bias":  {"type": "str", "default": "three_panels_blankcol_sep",
                       "valid": "three_panels_blankcol_sep"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "4..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_CODES = [2, 3, 4, 5, 6, 8]


def _apply(grid, code):
    if code == 1: return [row[:] for row in grid]
    if code == 2: return rot90_cw(grid)
    if code == 3: return rot180(grid)
    if code == 4: return transpose(grid)
    if code == 5: return flip_lr(grid)
    if code == 6: return flip_ud(grid)
    if code == 8: return cmirror(grid)
    return [row[:] for row in grid]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        isize = ctx.draw_int("interior_size", 3, 3)
        n_marks = ctx.draw_int("n_marks", 3, 4)
    elif difficulty == "hard":
        isize = ctx.draw_int("interior_size", 4, 5)
        n_marks = ctx.draw_int("n_marks", 6, 9)
    else:
        isize = ctx.draw_int("interior_size", 3, 4)
        n_marks = ctx.draw_int("n_marks", 4, 6)
    rng = ctx.draw_rng("layout")
    panel_size = isize + 2
    h = panel_size
    w = panel_size * 3 + 2
    g = full_grid(h, w, 0)
    code = rng.choice(_CODES)

    def _make_pattern():
        pat = [[0] * isize for _ in range(isize)]
        cells = [(r, c) for r in range(isize) for c in range(isize)]
        rng.shuffle(cells)
        for r, c in cells[:n_marks]:
            pat[r][c] = rng.choice([1, 2, 3, 4])
        return pat

    def _matching_codes(src, dst):
        return [c for c in _CODES if _apply(src, c) == dst]

    for _ in range(240):
        pattern_a = _make_pattern()
        pattern_b = _apply(pattern_a, code)
        if _apply(pattern_a, code) == pattern_a:
            continue
        # Avoid symmetric A patterns where several transforms explain A:B.
        if _matching_codes(pattern_a, pattern_b) != [code]:
            continue
        pattern_c = _make_pattern()
        # The query must visibly require the inferred transform too.
        if _apply(pattern_c, code) == pattern_c:
            continue
        break
    else:
        # Deterministic asymmetric witness: rot/flip/transpose all change it,
        # and the selected code is the unique non-identity map from A to B.
        pattern_a = [[1, 2, 0], [0, 3, 0], [4, 0, 0]]
        pattern_c = [[0, 1, 0], [2, 0, 3], [0, 0, 4]]
        code = 2
        pattern_b = _apply(pattern_a, code)

    for idx, pat in enumerate([pattern_a, pattern_b, pattern_c]):
        c0 = idx * (panel_size + 1)
        c1 = c0 + panel_size - 1
        for c in range(c0, c1 + 1):
            g[0][c] = 5
            g[panel_size - 1][c] = 5
        for r in range(panel_size):
            g[r][c0] = 5
            g[r][c1] = 5
        for ir in range(isize):
            for ic in range(isize):
                g[1 + ir][c0 + 1 + ic] = pat[ir][ic]
    return g


def _draw_from_degenerate(name, rng):
    isize = 3
    panel_size = isize + 2
    w = panel_size * 3 + 2
    h = panel_size
    g = full_grid(h, w, 0)
    if name == "no_panels":
        # No panels at all — rule has nothing to read.
        return g
    if name == "identity_transform":
        # B = A, C = anything — rule applies identity, output = C unchanged.
        for idx in range(3):
            c0 = idx * (panel_size + 1); c1 = c0 + panel_size - 1
            for c in range(c0, c1 + 1):
                g[0][c] = 5; g[panel_size - 1][c] = 5
            for r in range(panel_size):
                g[r][c0] = 5; g[r][c1] = 5
        # A and B identical, C different
        g[1][1] = 1; g[1][2] = 2; g[2][1] = 3
        g[1][6] = 1; g[1][7] = 2; g[2][6] = 3
        g[1][11] = 4; g[2][12] = 1
        return g
    if name == "mismatched_transform":
        # B is not any pure transform of A — rule cannot infer T uniquely.
        for idx in range(3):
            c0 = idx * (panel_size + 1); c1 = c0 + panel_size - 1
            for c in range(c0, c1 + 1):
                g[0][c] = 5; g[panel_size - 1][c] = 5
            for r in range(panel_size):
                g[r][c0] = 5; g[r][c1] = 5
        g[1][1] = 1; g[2][2] = 2
        g[1][7] = 3; g[2][6] = 4
        g[1][11] = 1
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    panel_size = len(grid)
    starts = [0, panel_size + 1, 2 * (panel_size + 1)]
    if len(grid[0]) != panel_size * 3 + 2:
        return ["input should be exactly three square panels separated by blank columns"]
    interiors = []
    for c0 in starts:
        c1 = c0 + panel_size - 1
        if any(grid[0][c] != 5 or grid[panel_size - 1][c] != 5 for c in range(c0, c1 + 1)):
            errs.append("panel top/bottom frame is incomplete")
        if any(grid[r][c0] != 5 or grid[r][c1] != 5 for r in range(panel_size)):
            errs.append("panel side frame is incomplete")
        interiors.append([row[c0 + 1:c1] for row in grid[1:-1]])
    if any(row[panel_size] != 0 or row[2 * panel_size + 1] != 0 for row in grid):
        errs.append("panel separators must be blank columns")
    a, b, c = interiors
    matches = [code for code in _CODES if _apply(a, code) == b]
    if len(matches) != 1:
        errs.append(f"A:B should identify exactly one non-identity transform, got {matches}")
    elif _apply(c, matches[0]) == c:
        errs.append("C should visibly change under the inferred transform")
    return errs
