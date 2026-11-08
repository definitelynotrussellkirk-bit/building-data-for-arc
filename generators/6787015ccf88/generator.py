"""Generator for arc_puzzle_bank_ninth21:E62.

A top-left 2x2 prototype is stamped at separated color-7 markers.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_markers,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_proto, no_markers, marker_in_proto.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6787015ccf88"
VERSION = "1.1.1"
TASK_ID = "6787015ccf88"

SUMMARY = "A top-left 2x2 prototype is stamped at separated color-7 markers."

INVARIANTS = [
    "background is 0",
    "the 2x2 prototype sits in the top-left corner",
    "markers use color 7 and are outside the prototype",
    "each marker has room for a non-overlapping 2x2 stamp",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_proto", "no_markers", "marker_in_proto")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "4..16"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "4..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_markers":      {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "5", "valid": "5..5"},
    "position_bias":  {"type": "str", "default": "topleft_proto_with_markers",
                       "valid": "topleft_proto_with_markers"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "5..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_proto|no_markers|marker_in_proto"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: top-left 2x2 proto has non-zero cells; ≥1 color-7 marker elsewhere."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    # Check the 2x2 proto (top-left)
    proto_nonzero = any(grid[r][c] != 0 for r in range(min(2, h)) for c in range(min(2, w)))
    if not proto_nonzero:
        errs.append("top-left 2x2 prototype is all zero")
    # Check ≥1 color-7 marker
    has_7 = any(grid[r][c] == 7 for r in range(h) for c in range(w)
                if not (r < 2 and c < 2))
    if not has_7:
        errs.append("no color-7 marker cells found outside the prototype")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
        target = ctx.draw_int("markers", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        target = ctx.draw_int("markers", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 12)
        target = ctx.draw_int("markers", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    proto_colors = rng.sample([1, 2, 3, 4, 5, 6, 8, 9], 4)
    for dr in [0, 1]:
        for dc in [0, 1]:
            g[dr][dc] = proto_colors[dr * 2 + dc]
    reserved = {(0, 0), (0, 1), (1, 0), (1, 1)}
    placed = 0
    for _ in range(300):
        if placed >= target:
            break
        r = rng.randint(2, h - 2)
        c = rng.randint(0, w - 2)
        stamp = {(r + dr, c + dc) for dr in [0, 1] for dc in [0, 1]}
        guard = {
            (rr, cc)
            for sr, sc in stamp
            for rr in range(max(0, sr - 1), min(h, sr + 2))
            for cc in range(max(0, sc - 1), min(w, sc + 2))
        }
        if guard & reserved:
            continue
        g[r][c] = 7
        reserved.update(guard)
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_proto":
        # markers without prototype → no stamp template defined
        g[3][3] = 7; g[5][6] = 7
        return g
    if name == "no_markers":
        # prototype only, no markers → nothing to stamp at
        for dr in [0, 1]:
            for dc in [0, 1]:
                g[dr][dc] = (dr * 2 + dc) + 1
        return g
    if name == "marker_in_proto":
        # marker overlaps prototype area → ambiguous, breaks "outside" invariant
        for dr in [0, 1]:
            for dc in [0, 1]:
                g[dr][dc] = (dr * 2 + dc) + 1
        g[1][1] = 7  # marker inside prototype
        return g
    return g
