"""Generator for arc_additional_puzzles_21_set13_bundle:M86 — sort object crops by token-above value.

Rule: each non-token object gets an order from the token (value in
{1,2,3,4}) sitting directly above its bbox top-left corner; sort the
objects by that order ASC and paste their crops side by side with a
1-col gap.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_objects (no shapes → rule has nothing to sort);
no_tokens (objects present but no tokens → rule's order-key
selector finds no values, sort undefined); tied_tokens (two
objects share the same token value → sort tie-break ambiguous).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.palette import random_palette
from puzzle_generators.helpers.blobs import bbox_overlaps

GENERATOR_ID = "9c5eacd4de3e"
VERSION = "1.1.1"
TASK_ID = "9c5eacd4de3e"
SUMMARY = "2-3 colored shapes; each has a distinct token (1..4) directly above its bbox top-left."

INVARIANTS = [
    "background is 0",
    "2-3 connected non-token objects (colors 5..9)",
    "each object has a distinct token in {1, 2, 3, 4} placed directly above its bbox top-left",
    "objects + their tokens don't touch each other",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_objects", "no_tokens", "tied_tokens")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "grid_w":            {"type": "int", "default": "rng 12..16", "valid": "10..20"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "position_bias":     {"type": "str", "default": "objects_with_token_above",
                          "valid": "objects_with_token_above"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_SHAPES = [
    [(0, 0), (0, 1), (1, 0), (1, 1)],                # 2x2
    [(0, 0), (1, 0), (1, 1), (2, 1)],                # zig-zag
    [(0, 0), (0, 1), (0, 2), (1, 1)],                # T
    [(0, 0), (1, 0), (2, 0), (2, 1)],                # L (3 tall)
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2)],        # U
    [(0, 0), (0, 1), (1, 1), (1, 2)],                # S
]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 12, 13)
        n = ctx.draw_int("n_objs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 14, 16)
        n = ctx.draw_int("n_objs", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 12, 16)
        n = ctx.draw_int("n_objs", 2, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = list(random_palette(rng, n, exclude={1, 2, 3, 4}))
    tokens = rng.sample([1, 2, 3, 4], n)
    placed: list[tuple[int, int, int, int]] = []
    for color, token in zip(palette, tokens):
        shape = rng.choice(_SHAPES)
        sh = max(c[0] for c in shape) + 1
        sw = max(c[1] for c in shape) + 1
        for _ in range(80):
            r1 = rng.randint(2, h - sh - 2)
            c1 = rng.randint(2, w - sw - 2)
            r2 = r1 + sh - 1
            c2 = c1 + sw - 1
            bb_pad = (r1 - 2, c1 - 1, r2 + 1, c2 + 1)
            if any(bbox_overlaps(bb_pad, p) for p in placed): continue
            if g[r1 - 1][c1] != 0: continue
            paint_at(g, r1, c1, shape, color)
            g[r1 - 1][c1] = token
            placed.append(bb_pad)
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 13
    g = full_grid(h, w, 0)
    if name == "no_objects":
        # No shapes — rule has nothing to sort.
        return g
    if name == "no_tokens":
        # Objects present but no tokens above — order key is missing.
        for r in range(2):
            for c in range(2):
                g[3 + r][2 + c] = 5
        for r in range(2):
            for c in range(2):
                g[5 + r][8 + c] = 6
        return g
    if name == "tied_tokens":
        # Both objects have the same token value (2) — sort tie ambiguous.
        g[2][2] = 2; g[2][8] = 2
        for r in range(2):
            for c in range(2):
                g[3 + r][2 + c] = 5
        for r in range(2):
            for c in range(2):
                g[3 + r][8 + c] = 6
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: tokens in {1,2,3,4} exist; objects in non-{0,1,2,3,4} colors exist."""
    msgs = []
    h, w = len(grid), len(grid[0])
    tokens = [(r, c) for r in range(h) for c in range(w) if grid[r][c] in (1, 2, 3, 4)]
    objects = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 1, 2, 3, 4)]
    if not tokens:
        msgs.append("no token cells (colors 1-4) found")
    if not objects:
        msgs.append("no object cells (non-{0,1,2,3,4} colors) found")
    return msgs
