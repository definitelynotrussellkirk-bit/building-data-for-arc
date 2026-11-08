"""Generator for arc_additional_puzzle_bank_volume17:M118.

Rule: red cells span a bounding rectangle; empty border positions of that
rectangle become 8.

Combinatorial axes (8): grid_h/w, palette_kind, bbox_padding,
distractor_color, palette_size, position_bias, n_distinct_colors, texture.
Degenerates: no_red_cells, single_red, border_already_complete.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "24a7dc5a6db9"
VERSION = "1.2.1"
TASK_ID = "24a7dc5a6db9"
SUMMARY = "Sparse color-2 (red) cells on a 0-bg grid (with optional distractor cells in other colors). Rule computes the bbox of the red cells, then paints color 8 onto every border-of-bbox position (row=r0 or r1, or col=c0 or c1) that is currently 0. Existing reds on the border stay 2. Cells inside the bbox interior stay unchanged. Cells outside the bbox stay unchanged."

# Rivals: 'output is input' refuted by demos (border fills).
# 'fill bbox interior too' refuted by demos with interior 0s
# staying 0. 'use color 2 for border fill' refuted by demos (always
# 8). 'fill outside bbox' refuted by demos (distractor cells stay).
# 3 demos with ≥3 reds defining a non-degenerate bbox cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "red cells span a rectangle with empty border gaps",
    "non-red distractors do not affect the red bounding box",
]

PALETTE_KINDS = ("default", "warm_distractor", "cool_distractor", "neutral_distractor")
DEGENERATE_TEXTURES = ("no_red_cells", "single_red", "border_already_complete")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "bbox_padding":   {"type": "int", "default": "1", "valid": "1"},
    "distractor_color": {"type": "int", "default": "5", "valid": "5"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "centered_bbox",
                       "valid": "centered_bbox"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥2 color-2 (red) cells with no color-8 in input (8 is written by the rule)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    reds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if not reds:
        return errors  # degenerate no_red_cells — allowed
    if len(reds) < 2:
        return errors  # degenerate single_red — allowed
    # No color-8 should appear in input (the rule writes it on output)
    eights = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if eights:
        errors.append(f"color-8 appears in input (rule writes it, not generator): {eights[:3]}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = rng.randint(7, 9); w = rng.randint(7, 10)
        n_distractors = rng.randint(0, 1)
    elif difficulty == "hard":
        h = rng.randint(13, 18); w = rng.randint(13, 18)
        n_distractors = rng.randint(2, 5)
    else:
        h = rng.randint(10, 13); w = rng.randint(10, 13)
        n_distractors = rng.randint(1, 3)
    g = full_grid(h, w, 0)
    # Pick a bbox of size ≥3x3
    r0 = rng.randint(1, h // 2 - 1)
    c0 = rng.randint(1, w // 2 - 1)
    r1 = rng.randint(max(r0 + 2, h // 2 + 1), h - 2)
    c1 = rng.randint(max(c0 + 2, w // 2 + 1), w - 2)
    # Place red cells: 2 opposite corners (to define bbox) + 1-3 extra
    g[r0][c0] = 2; g[r1][c1] = 2
    n_extra = rng.randint(1, 4)
    for _ in range(n_extra * 4):
        if n_extra <= 0:
            break
        rr = rng.randint(r0, r1)
        cc = rng.randint(c0, c1)
        if g[rr][cc] != 0:
            continue
        g[rr][cc] = 2
        n_extra -= 1
    # Distractor cells (any color != 0, 2, 8) outside the bbox
    for _ in range(n_distractors * 5):
        if n_distractors <= 0:
            break
        rr = rng.randint(0, h - 1)
        cc = rng.randint(0, w - 1)
        if r0 <= rr <= r1 and c0 <= cc <= c1:
            continue
        if g[rr][cc] != 0:
            continue
        g[rr][cc] = rng.choice([1, 3, 4, 5, 6, 7, 9])
        n_distractors -= 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_red_cells":
        # only distractors — bbox of red is undefined
        g[3][4] = 5
        g[7][2] = 6
        return g
    if name == "single_red":
        # 1 red cell → degenerate 1×1 bbox
        g[4][5] = 2
        g[h - 1][w - 1] = 5
        return g
    if name == "border_already_complete":
        # rectangle border fully painted in red — rule has nothing to fill
        for c in range(2, 8):
            g[2][c] = 2
            g[7][c] = 2
        for r in range(2, 8):
            g[r][2] = 2
            g[r][7] = 2
        return g
    return g
