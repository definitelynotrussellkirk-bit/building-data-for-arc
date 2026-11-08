"""Generator for arc_additional_puzzle_bank_volume14:E95.

Rule: extract subgrid bounded by min/max row/col of all non-bg cells
(crop-to-content via subgrid).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_objects,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: empty_grid, content_fills_grid, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.shape import normalize, rect_cells
from puzzle_generators.helpers.place import place_no_overlap

GENERATOR_ID = "13c2bb6fb5a7"
# 1.3.0: reverse-diversity / canonical-match -- placed only solid rectangles, so
# the cropped output was always a solid rect. Canonical demos crop polyomino
# shapes with interior bg in the bbox. Now mix random polyominoes (bbox holes)
# with rects; richer cropped outputs.
VERSION = "1.3.3"  # FIX: default crops now have 2D, multi-cell content; no skinny 1xN teaching rows.
TASK_ID = "13c2bb6fb5a7"
SUMMARY = "Sparse non-bg content with bg padding; rule crops to a non-trivial 2D bbox of the non-bg cells."

# Rivals: 'extract the largest object only' refuted by ≥1 demo with
# ≥2 objects (output spans both). 'pad output to canonical size'
# refuted by ≥2 demos with different bbox sizes. 'recolor on crop'
# refuted by any demo (colors preserved). 'crop with margin' refuted
# by ≥1 demo where the bbox is tight against multiple objects.
# 3 demos with varied object counts + sizes cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    ">=1 non-bg cell",
    "non-bg content has at least 1 cell of bg margin from some grid edge",
    "input grid larger than the content bbox (so cropping shrinks)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("empty_grid", "content_fills_grid", "single_cell")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..16", "valid": "6..22"},
    "grid_w":         {"type": "int", "default": "rng 9..16", "valid": "6..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_objects":      {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 2..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "interior", "valid": "interior"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..5", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: default crops are non-empty, non-identity, and non-trivial."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        errors.append("no non-bg content")
        return errors
    # Content bbox should not span the entire grid (crop would be a no-op)
    r1 = min(r for r, c in nonzero); c1 = min(c for r, c in nonzero)
    r2 = max(r for r, c in nonzero); c2 = max(c for r, c in nonzero)
    if r1 == 0 and c1 == 0 and r2 == h - 1 and c2 == w - 1:
        errors.append("content fills entire grid — no margin")
    bbox_h, bbox_w = r2 - r1 + 1, c2 - c1 + 1
    if r1 == r2 and c1 == c2:
        errors.append("single-cell content crop is a listed degenerate")
    if bbox_h < 2 or bbox_w < 2:
        errors.append(f"skinny crop bbox {bbox_h}x{bbox_w}; default demos should teach 2D cropping")
    if len(nonzero) < 4:
        errors.append(f"too few non-bg cells ({len(nonzero)}); crop target is weak for grid prediction")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 9, 11)
        n = ctx.draw_int("n_objects", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 16, 22)
        w = ctx.draw_int("grid_w", 16, 22)
        n = ctx.draw_int("n_objects", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 11, 16)
        w = ctx.draw_int("grid_w", 11, 16)
        n = ctx.draw_int("n_objects", 2, 4)
    palette_n = ctx.draw_int("fg_palette", 2, 5)
    palette = ctx.draw_distinct_colors("palette", n=palette_n, exclude={0})

    rng = ctx.draw_rng("placement")
    # Retry because independent object placement can otherwise leave only one skinny
    # horizontal/vertical crop, which satisfies parity but teaches a shortcut.
    last = None
    for _attempt in range(40):
        g = full_grid(h, w, 0)
        placed = 0
        for i in range(n):
            if rng.random() < 0.5:
                rh = rng.randint(1, max(1, h // 4))
                rw = rng.randint(1, max(1, w // 4))
                if rh * rw == 1:
                    if rng.random() < 0.5 and h >= 4:
                        rh = 2
                    elif w >= 4:
                        rw = 2
                cells = normalize(rect_cells(rh, rw))
            else:
                cells = _poly(rng, rng.randint(3, 7))
            color = palette[i % len(palette)]
            if place_no_overlap(rng, g, cells, color, bg=0, margin=1, max_tries=30):
                placed += 1
        last = g
        if placed >= 2 and not self_check(g, difficulty=difficulty):
            return g

    # Deterministic fallback: two separated 2x2-ish objects with a real 2D crop bbox.
    g = full_grid(h, w, 0)
    for rr, cc, col in ((1, 1, palette[0]), (max(3, h - 4), max(3, w - 4), palette[1 % len(palette)])):
        for dr, dc in ((0, 0), (0, 1), (1, 0)):
            if 1 <= rr + dr < h - 1 and 1 <= cc + dc < w - 1:
                g[rr + dr][cc + dc] = col
    return g if not self_check(g, difficulty=difficulty) else last


def _poly(rng, n):
    """Random connected polyomino of n cells, normalized."""
    cells = {(0, 0)}
    while len(cells) < n:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        cells.add((r + dr, c + dc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _draw_from_degenerate(name, rng):
    h, w = 12, 12
    g = full_grid(h, w, 0)
    if name == "empty_grid":
        # no non-bg cells → bbox undefined, rule output is empty/ambiguous
        return g
    if name == "content_fills_grid":
        # non-bg content already spans full grid → crop is identity
        for r in range(h):
            for c in range(w):
                g[r][c] = 1 + ((r + c) % 5)
        return g
    if name == "single_cell":
        # one non-bg cell → output is 1×1, trivial cropping
        g[6][6] = 7
        return g
    return g
