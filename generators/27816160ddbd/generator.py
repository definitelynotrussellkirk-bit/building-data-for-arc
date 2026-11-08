"""Generator for arc_puzzle_bank_21_set14_s:S14_E7 — largest comp's row-profile histogram.

The largest component's row profile is emitted as a compact left-justified histogram.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: tied_largest (≥2 components share max size → "largest"
is ambiguous, tie-break decides), uniform_row_profile (largest comp
is rectangular → row profile is constant, histogram is degenerate),
single_component (only one component → trivially largest, no
contrast).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "27816160ddbd"
VERSION = "2.0.0"  # distinct=3: largest object was 1 of 3 fixed _LARGEST shapes -> only 3 row-profile histograms. Now random largest polyomino (non-uniform rows, strictly > distractors) -> histogram dims+content vary.
TASK_ID = "27816160ddbd"
SUMMARY = (
    "0-bg grid (size varies) "
    "with: (a) ONE LARGEST "
    "COMPONENT — a RANDOM "
    "polyomino (5-14 cells) "
    "with a NON-UNIFORM row "
    "profile; (b) 1-4 SMALLER "
    "DISTRACTOR COMPONENTS "
    "(strictly fewer cells). "
    "All components in "
    "DISTINCT colors, non-"
    "touching with 1-cell "
    "padding. The largest is "
    "unique. Rule "
    "(ROW-PROFILE HISTOGRAM "
    "OF LARGEST): identify "
    "the LARGEST COMPONENT. "
    "For each ROW of its "
    "bbox, COUNT how many "
    "cells are non-bg "
    "(belong to the component) "
    "— this gives a row "
    "profile [n1, n2, ..., "
    "nh]. EMIT a HISTOGRAM "
    "as the output: each "
    "row of the output "
    "shows ni cells of the "
    "component's COLOR "
    "left-justified, padded "
    "with 0. Net: largest "
    "component's per-row cell "
    "count becomes a left-"
    "aligned color-bar "
    "histogram."
)

INVARIANTS = [
    "background is 0",
    "one component is strictly largest by cell count",
    "the largest component has a non-uniform row profile",
    "distractor components are smaller than the largest component",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_largest", "uniform_row_profile", "single_component")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "height":         {"type": "int", "default": "rng 10..13", "valid": "8..17"},
    "width":          {"type": "int", "default": "rng 12..15", "valid": "10..19"},
    "distractor_count": {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "largest_plus_distractors",
                       "valid": "largest_plus_distractors"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_LARGEST = [
    [(0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (3, 1)],
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (3, 0)],
    [(0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1), (2, 2)],
]
_SMALL = [
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (2, 0)],
    [(0, 0), (0, 1), (1, 1)],
]


_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nb = (r + dr, c + dc)
        if nb not in seen:
            cells.append(nb); seen.add(nb)
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _nonuniform_rows(shape):
    from collections import Counter
    prof = Counter(r for r, _ in shape)
    vals = [prof[r] for r in range(max(prof) + 1)]
    return len(set(vals)) > 1


def _size(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _free(g, r0, c0, shape, pad=1):
    h, w = len(g), len(g[0])
    sh, sw = _size(shape)
    if r0 < 0 or c0 < 0 or r0 + sh > h or c0 + sw > w:
        return False
    for r in range(max(0, r0 - pad), min(h, r0 + sh + pad)):
        for c in range(max(0, c0 - pad), min(w, c0 + sw + pad)):
            if g[r][c] != 0:
                return False
    return True


def _place(g, rng, shape, color):
    h, w = len(g), len(g[0])
    sh, sw = _size(shape)
    for _ in range(120):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        if _free(g, r0, c0, shape):
            for dr, dc in shape:
                g[r0 + dr][c0 + dc] = color
            return
    raise ValueError("could not place component")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # output = the row-profile histogram of the LARGEST object. Was 1 of 3 fixed
    # _LARGEST shapes -> distinct=3. Now a RANDOM largest polyomino (non-uniform rows)
    # strictly larger than the distractors -> the histogram (dims + content) varies.
    if difficulty == "easy":
        h = ctx.draw_int("height", 9, 12); w = ctx.draw_int("width", 11, 14)
        distractor_count = ctx.draw_int("distractor_count", 1, 2); klo, khi = 5, 8
    elif difficulty == "hard":
        h = ctx.draw_int("height", 13, 17); w = ctx.draw_int("width", 15, 19)
        distractor_count = ctx.draw_int("distractor_count", 3, 4); klo, khi = 9, 14
    else:
        h = ctx.draw_int("height", 10, 14); w = ctx.draw_int("width", 12, 16)
        distractor_count = ctx.draw_int("distractor_count", 2, 3); klo, khi = 7, 11
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 6, 7, 9], 1 + distractor_count)
    # largest: random polyomino with a non-uniform row profile, fits the grid
    k_large = rng.randint(klo, khi)
    for _ in range(60):
        big = _rand_poly(rng, k_large)
        bh, bw = _size(big)
        if bh <= h - 1 and bw <= w - 1 and _nonuniform_rows(big):
            break
    _place(g, rng, big, colors[0])
    # distractors strictly smaller than the largest (so the largest pick is clean)
    for color in colors[1:]:
        ks = rng.randint(2, min(5, k_large - 1))
        shape = _rand_poly(rng, ks)
        sh, sw = _size(shape)
        if sh > h or sw > w:
            continue
        try:
            _place(g, rng, shape, color)
        except ValueError:
            pass
    return g


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    if name == "tied_largest":
        # Two components share max size — "largest" is ambiguous;
        # tie-break decides which row profile is emitted.
        for dr, dc in _LARGEST[0]:
            g[1 + dr][2 + dc] = 2
        for dr, dc in _LARGEST[2]:
            g[6 + dr][8 + dc] = 3
        return g
    if name == "uniform_row_profile":
        # Largest component is a 3x3 square — row profile is
        # constant; histogram is degenerate (all bars equal).
        for r in range(2, 5):
            for c in range(2, 5):
                g[r][c] = 4
        for dr, dc in _SMALL[0]:
            g[8 + dr][8 + dc] = 6
        return g
    if name == "single_component":
        # Only one component — trivially largest; no candidate
        # contrast.
        for dr, dc in _LARGEST[1]:
            g[3 + dr][5 + dc] = 6
        return g
    return g
