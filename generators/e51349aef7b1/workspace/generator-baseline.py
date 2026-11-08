"""Generator for arc_additional_puzzles_21_set15_bundle:H105 — color+transform analogy.

Rule: full-col color-5 dividers split into 3 NxN panels. Each panel has a
uniform-color shape (single non-bg color). Transform t in {1..6} maps
binary(A) → binary(B); recolor maps A's single color to B's. Output is
t(C) recolored to B's color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_dividers (no color-5 columns → rule cannot split
panels); identity_transform (A == B → t = identity, output = C
recolored); no_C_content (panel C empty → rule's input to t is
empty, output empty).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e51349aef7b1"
VERSION = "2.2.0"  # require unique visible A->B transform and non-identity C transform; add self_check
TASK_ID = "e51349aef7b1"

SUMMARY = (
    "Horizontal strip of 3 panels, each n×n (n in 4..5), separated by "
    "single full-height color-5 divider columns. Panel A (leftmost) has "
    "some cells in a uniform color cA. Panel B has the same shape "
    "transformed by some t ∈ {1..6} (identity, rot-cw, rot-180, "
    "transpose, flip-lr, flip-ud), uniformly recolored to cB. Panel C "
    "has its own shape in color cC. Rule: find dividers, split into "
    "panels, crop each to non-zero bbox. Find t such that "
    "binary(t(A)) == binary(B). Apply t to C, recolor every non-zero "
    "to cB (B's color). Output is crop(t(C)) sized to C's content "
    "bbox dimensions (after applying t)."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "two full-height color-5 divider columns split the grid into three equal NxN panels",
    "panels are square so all 6 transforms apply",
    "Panel A and Panel B have the same binary shape under some transform t",
    "Panel A, B, C use distinct uniform colors (non-bg, non-5)",
    "Panel A has ≥3 non-zero cells (shape is meaningful)",
    "Panel C has ≥3 non-zero cells (so output is non-trivial)",
    "A→B transform is NOT identity (so the rule's transformation is visible)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dividers", "identity_transform", "no_C_content")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_n":           {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "transform":         {"type": "int", "default": "rng 2..6", "valid": "1..6"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 4..4", "valid": "4..4"},
    "position_bias":     {"type": "str", "default": "three_panels_with_5_dividers",
                          "valid": "three_panels_with_5_dividers"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..4", "valid": "4..4"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _xform(cells, t, n):
    if t == 1: return list(cells)
    if t == 2: return [(c, n - 1 - r) for r, c in cells]
    if t == 3: return [(n - 1 - r, n - 1 - c) for r, c in cells]
    if t == 4: return [(c, r) for r, c in cells]
    if t == 5: return [(r, n - 1 - c) for r, c in cells]
    return [(n - 1 - r, c) for r, c in cells]


def _rand_cells(rng, n, k):
    cells = [(rng.randint(0, n - 1), rng.randint(0, n - 1))]
    seen = set(cells)
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if 0 <= nr < n and 0 <= nc < n and (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        n = ctx.draw_int("panel_n", 3, 4)
    elif difficulty == "hard":
        n = ctx.draw_int("panel_n", 5, 6)
    else:
        n = ctx.draw_int("panel_n", 4, 6)
    t = ctx.draw_int("transform", 2, 6)
    rng = ctx.draw_rng("layout")
    h = n
    w = n * 3 + 2
    d1, d2 = n, 2 * n + 1
    color_a, color_b, color_c = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 3)
    kmax = max(4, n * n - 2)

    for outer in range(40):
        g = full_grid(h, w, 0)
        for r in range(h):
            g[r][d1] = 5
            g[r][d2] = 5
        ka = rng.randint(3, min(kmax, n + 3))
        cells_a = _rand_cells(rng, n, ka)
        cells_b = _xform(cells_a, t, n)
        matches = [tt for tt in range(1, 7) if set(_xform(cells_a, tt, n)) == set(cells_b)]
        if matches != [t]:
            continue
        kc = rng.randint(3, min(kmax, n + 3))
        cells_c = _rand_cells(rng, n, kc)
        if set(_xform(cells_c, t, n)) == set(cells_c):
            continue
        for r, c in cells_a:
            g[r][c] = color_a
        for r, c in cells_b:
            g[r][d1 + 1 + c] = color_b
        for r, c in cells_c:
            g[r][d2 + 1 + c] = color_c
        return g
    raise ValueError("could not realize 3-panel color-transform analogy in 40 attempts")


def _draw_from_degenerate(name, rng):
    n = 4
    h = n
    w = n * 3 + 2
    g = full_grid(h, w, 0)
    if name == "no_dividers":
        # No color-5 dividers — rule cannot split panels.
        for r in range(n):
            for c in range(n):
                if (r + c) % 2 == 0:
                    g[r][c] = 4
        return g
    if name == "identity_transform":
        # A == B same shape — t = identity.
        for r in range(h):
            g[r][n] = 5
            g[r][2 * n + 1] = 5
        for r, c in [(0, 0), (0, 1), (1, 0)]:
            g[r][c] = 4
        for r, c in [(0, 0), (0, 1), (1, 0)]:
            g[r][n + 1 + c] = 6
        for r, c in [(0, 0), (1, 0), (1, 1)]:
            g[r][2 * n + 2 + c] = 7
        return g
    if name == "no_C_content":
        # Panel C empty — rule's input to t is empty.
        for r in range(h):
            g[r][n] = 5
            g[r][2 * n + 1] = 5
        for r, c in [(0, 0), (0, 1), (1, 0)]:
            g[r][c] = 4
        for r, c in [(0, 1), (1, 0), (1, 1)]:
            g[r][n + 1 + c] = 6
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    n = len(grid)
    if len(grid[0]) != 3 * n + 2:
        return ["grid is not three square panels plus two dividers"]
    d1, d2 = n, 2 * n + 1
    if not all(row[d1] == 5 and row[d2] == 5 for row in grid):
        errors.append("divider columns are not solid color 5")
    A = {(r, c) for r in range(n) for c in range(n) if grid[r][c] not in (0, 5)}
    B = {(r, c) for r in range(n) for c in range(n) if grid[r][d1 + 1 + c] not in (0, 5)}
    C = {(r, c) for r in range(n) for c in range(n) if grid[r][d2 + 1 + c] not in (0, 5)}
    if len(A) < 3 or len(C) < 3:
        errors.append("panel A/C content has fewer than 3 cells")
    matches = [t for t in range(1, 7) if set(_xform(A, t, n)) == B]
    if len(matches) != 1 or matches[0] == 1:
        errors.append(f"A->B transform is not a unique non-identity transform: {matches}")
    elif set(_xform(C, matches[0], n)) == C:
        errors.append("selected transform is invisible on panel C")
    colors_a = {grid[r][c] for r, c in A}
    colors_b = {grid[r][d1 + 1 + c] for r, c in B}
    colors_c = {grid[r][d2 + 1 + c] for r, c in C}
    if len(colors_a) != 1 or len(colors_b) != 1 or len(colors_c) != 1:
        errors.append("each panel should use exactly one non-background color")
    if len(colors_a | colors_b | colors_c) != 3:
        errors.append("panel colors should be distinct")
    return errors
