"""Generator for arc_puzzle_bank_fourth21:E27.

Rule: each X motif (center + 4 diagonals same color) gets its center
highlighted.

Combinatorial axes (8): grid_h, grid_w, palette_kind, motifs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_xs, partial_xs, mixed_corner_colors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7a41ac31fabf"
VERSION = "1.2.0"  # realize requested X-motif count and add executable invariants
TASK_ID = "7a41ac31fabf"
SUMMARY = "Place separated same-color X motifs whose centers are highlighted."

INVARIANTS = [
    "background is 0",
    "each active motif has a non-8 center",
    "the four diagonal neighbors around the center share the center color",
    "motif footprints are separated",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_xs", "partial_xs", "mixed_corner_colors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "motifs":         {"type": "int", "default": "rng 1..3", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 1..3", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "spaced_xs",
                       "valid": "spaced_xs"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..3", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_DIAGS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 7, 8)
        target = ctx.draw_int("motifs", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        target = ctx.draw_int("motifs", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 7, 10)
        target = ctx.draw_int("motifs", 1, 3)
    rng = ctx.draw_rng("layout")
    # The one-pass sampler could silently under-realize hard examples.  Widen
    # small canvases when multiple motifs were requested, retry whole layouts,
    # and fall back to deterministic separated corners if random placement is
    # unlucky.
    if target >= 2:
        h = max(h, 8)
        w = max(w, 9)
    if target >= 3:
        h = max(h, 9)
        w = max(w, 10)
    for _layout_attempt in range(80):
        g = full_grid(h, w, 0)
        reserved: set[tuple[int, int]] = set()
        placed = 0
        for _ in range(500):
            if placed >= target:
                break
            r = rng.randint(1, h - 2)
            c = rng.randint(1, w - 2)
            if _try_place_x(g, reserved, r, c, rng.choice([1, 2, 3, 4, 5, 6, 7, 9])):
                placed += 1
        if placed == target:
            return g
    return _fallback_layout(h, w, target, rng)


def _try_place_x(g, reserved, r, c, color):
    h, w = len(g), len(g[0])
    cells = {(r, c)} | {(r + dr, c + dc) for dr, dc in _DIAGS}
    if any(not (0 <= rr < h and 0 <= cc < w) for rr, cc in cells):
        return False
    guard = {
        (rr, cc)
        for cr, cc0 in cells
        for rr in range(max(0, cr - 1), min(h, cr + 2))
        for cc in range(max(0, cc0 - 1), min(w, cc0 + 2))
    }
    if guard & reserved:
        return False
    for rr, cc in cells:
        g[rr][cc] = color
    reserved.update(guard)
    return True


def _fallback_layout(h, w, target, rng):
    g = full_grid(h, w, 0)
    reserved: set[tuple[int, int]] = set()
    centers = [(1, 1), (1, w - 2), (h - 2, 1), (h - 2, w - 2), (h // 2, w // 2)]
    rng.shuffle(centers)
    colors = [1, 2, 3, 4, 5, 6, 7, 9]
    rng.shuffle(colors)
    placed = 0
    for (r, c), color in zip(centers, colors):
        if _try_place_x(g, reserved, r, c, color):
            placed += 1
            if placed == target:
                return g
    raise ValueError("could not realize separated X-motif layout")


def _x_motifs(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            color = grid[r][c]
            if color != 0 and color != 8 and all(grid[r + dr][c + dc] == color for dr, dc in _DIAGS):
                out.append((r, c, color))
    return out


def self_check(grid, *, difficulty=None, meta=None):
    """Verify separated same-colour X motifs and no stray cells."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    errs = []
    motifs = _x_motifs(grid)
    if difficulty == "easy":
        lo, hi = 1, 1
    elif difficulty == "hard":
        lo, hi = 2, 3
    else:
        lo, hi = 1, 3
    if not (lo <= len(motifs) <= hi):
        errs.append(f"expected {lo}..{hi} X motifs, found {len(motifs)}")
    covered = set()
    for r, c, _color in motifs:
        covered.add((r, c))
        covered.update((r + dr, c + dc) for dr, dc in _DIAGS)
    nz = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0}
    if nz != covered:
        errs.append("found nonzero cells outside the detected X motif footprints")
    centers = [(r, c) for r, c, _color in motifs]
    for i, (r1, c1) in enumerate(centers):
        for r2, c2 in centers[i + 1:]:
            if max(abs(r1 - r2), abs(c1 - c2)) < 3:
                errs.append("X motif centers are too close and can create accidental motifs")
                return errs
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_xs":
        # blank grid → no X motifs to highlight, rule is identity
        return g
    if name == "partial_xs":
        # only 3 of 4 diagonals → predicate fails, no center highlighted
        # missing top-right diagonal around (3, 3)
        for (r, c) in [(3, 3), (2, 2), (4, 2), (4, 4)]: g[r][c] = 4
        return g
    if name == "mixed_corner_colors":
        # 4 diagonals present but with mixed colors → predicate "all same color" fails
        for (r, c, col) in [(3, 3, 4), (2, 2, 4), (2, 4, 6), (4, 2, 4), (4, 4, 4)]: g[r][c] = col
        return g
    return g
