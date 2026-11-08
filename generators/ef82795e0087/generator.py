"""Generator for arc_puzzle_bank_eleventh21:M75 — point-reflect through anchor (keep 8 fixed).

Rule: 8-cell is fixed point. Each non-{0,8} cell stays AND its
reflection through the 8-cell is also painted (in same color).

Combinatorial axes (8): grid_h, grid_w, palette_kind, blob_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_anchor, multiple_anchors, blob_through_anchor.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ef82795e0087"
VERSION = "2.2.0"  # mix single cells + connected blobs (canonical has blobs); honest palette axes
TASK_ID = "ef82795e0087"
SUMMARY = (
    "0-bg grid (h, w~8-11) with EXACTLY ONE "
    "COLOR-8 (cyan) ANCHOR cell at interior "
    "position (ar, ac) (not at grid edge, so "
    "reflections fit). Plus 2-7 non-{0, 8} "
    "CELLS in various colors from {1, 2, 3, 4, "
    "5, 6, 7, 9} placed at scattered positions "
    "such that their point-reflection through "
    "the anchor lands IN-BOUNDS at currently "
    "empty cells. Rule: TREAT the COLOR-8 "
    "ANCHOR as the FIXED REFLECTION CENTER. "
    "For every non-{0, 8} cell at (r, c) with "
    "value v, COMPUTE its POINT-REFLECTION "
    "(2*ar - r, 2*ac - c). If that reflected "
    "position is in-bounds, PAINT it with the "
    "SAME COLOR v. ORIGINAL CELLS STAY. The "
    "anchor stays color 8. Net: every colored "
    "cell gets a same-color twin point-mirrored "
    "across the cyan anchor; output is input + "
    "all reflected copies."
)

# Rivals: 'output is input' refuted by demos with reflections in-
# bounds. 'reflect with color 8 (use anchor color)' refuted by demos
# preserving original colors. 'remove originals after reflecting'
# refuted by demos preserving originals. 'reflect across a different
# axis (LR/UD)' refuted by demos showing point-reflection. 'reflect
# only one color' refuted by demos with multiple colors all reflected.
# 'use anchor at grid center always' refuted by demos with anchor
# off-center. 3 demos with multiple colors + offset anchor pin the
# rule.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one color-8 anchor cell (NOT at grid edge so reflections fit)",
    "≥1 non-{0, 8} cell whose reflection lands in-bounds",
    "input + reflections don't overlap (output is non-trivially expanded)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_anchor", "multiple_anchors", "blob_through_anchor")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "7..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "blob_size":      {"type": "int", "default": "rng 1..4 per object", "valid": "1..6"},
    "n_objects":      {"type": "int", "default": "rng 2..8 by difficulty", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "varies (one color per object)", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "anchor_with_reflected_objects",
                       "valid": "anchor_with_reflected_objects"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _blob(rng, k):
    """Connected blob of k cells (normalized), bbox <= 3x3."""
    cells = {(0, 0)}
    tries = 0
    while len(cells) < k and tries < 30:
        tries += 1
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        cand = cells | {(r + dr, c + dc)}
        mr = min(x for x, _ in cand); mc = min(y for _, y in cand)
        if max(x - mr for x, _ in cand) + 1 <= 3 and max(y - mc for _, y in cand) + 1 <= 3:
            cells = cand
    mr = min(x for x, _ in cells); mc = min(y for _, y in cells)
    return [(x - mr, y - mc) for x, y in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9); w = ctx.draw_int("grid_w", 7, 9)
        n_obj = ctx.draw_int("n_objects", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 12, 16)
        n_obj = ctx.draw_int("n_objects", 5, 8)
    else:
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 9, 12)
        n_obj = ctx.draw_int("n_objects", 3, 5)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    ar = rng.randint(2, h - 3); ac = rng.randint(2, w - 3)
    g[ar][ac] = 8
    used = {(ar, ac)}                      # block anchor (and accumulates placed + reflected cells)
    colors = [1, 2, 3, 4, 5, 6, 7, 9]
    rng.shuffle(colors)

    placed = 0
    for _ in range(n_obj * 25):
        if placed >= n_obj:
            break
        # mix of single cells and small connected blobs (canonical has both)
        k = 1 if rng.random() < 0.4 else rng.randint(2, 4)
        shape = _blob(rng, k)
        bh = max(r for r, _ in shape) + 1; bw = max(c for _, c in shape) + 1
        r0 = rng.randint(0, h - bh); c0 = rng.randint(0, w - bw)
        cells = [(r0 + dr, c0 + dc) for dr, dc in shape]
        refl = [(2 * ar - r, 2 * ac - c) for r, c in cells]
        allc = cells + refl
        if any(not (0 <= r < h and 0 <= c < w) for r, c in refl):
            continue
        if any(p in used for p in allc):
            continue
        if len(set(allc)) != len(allc):    # object overlaps its own reflection
            continue
        color = colors[placed % len(colors)]
        for (r, c) in cells:
            g[r][c] = color
        used.update(allc)                  # reserve input AND reflection cells
        placed += 1
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify point-reflection demos have one anchor and non-overlapping reflected targets."""
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid is empty or ragged"]
    h, w = len(grid), len(grid[0])
    anchors = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if len(anchors) != 1:
        return [f"expected exactly one color-8 anchor, found {len(anchors)}"]
    ar, ac = anchors[0]
    if ar in (0, h - 1) or ac in (0, w - 1):
        errors.append(f"anchor at edge {(ar, ac)}")
    colored = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if grid[r][c] not in (0, 8)]
    if not colored:
        errors.append("no colored cells to reflect")
    for r, c, color in colored:
        rr, cc = 2 * ar - r, 2 * ac - c
        if not (0 <= rr < h and 0 <= cc < w):
            errors.append(f"color-{color} cell {(r, c)} reflects out of bounds to {(rr, cc)}")
            continue
        if (rr, cc) == (r, c):
            errors.append(f"color-{color} cell {(r, c)} lies on the anchor center")
        elif grid[rr][cc] != 0:
            errors.append(f"reflection target {(rr, cc)} for cell {(r, c)} is already occupied")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    ar, ac = h // 2, w // 2
    if name == "no_anchor":
        # missing 8-cell → no reflection center, rule undefined
        g[1][1] = 4; g[1][2] = 4; g[2][1] = 4
        return g
    if name == "multiple_anchors":
        # two 8-cells → ambiguous which is the reflection center
        g[2][2] = 8
        g[6][6] = 8
        g[1][1] = 4; g[1][2] = 4
        return g
    if name == "blob_through_anchor":
        # blob symmetric through anchor → reflection equals original (rule is identity)
        g[ar][ac] = 8
        # symmetric pair: (ar-1, ac) and (ar+1, ac) are reflections of each other; if both present
        g[ar - 1][ac] = 4; g[ar + 1][ac] = 4
        g[ar][ac - 1] = 6; g[ar][ac + 1] = 6
        return g
    return g
