"""Generator for arc_additional_puzzle_bank_volume19:E132 — recolor endpoints of length-4 cyan segments.

Rule: each length-4 cyan segment has its two endpoints recolored to red.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_segments, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_segments, wrong_length, single_segment.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cd8b5598bb80"
VERSION = "1.1.1"
TASK_ID = "cd8b5598bb80"
SUMMARY = "Endpoints of exact length-4 cyan line segments are recolored red."

INVARIANTS = [
    "background is 0",
    "target cyan components are straight segments of exactly length four",
    "all cyan components are separated by background",
    "segments may be horizontal or vertical",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_segments", "wrong_length", "single_segment")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "4..20"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "4..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_segments":     {"type": "int", "default": "rng 2..5", "valid": "1..10"},
    "palette_size":   {"type": "str", "default": "1 (cyan only)", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "axis_aligned_segments",
                       "valid": "axis_aligned_segments"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; all non-zero cells are color 8 (cyan) only."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("cell value out of 0-9")
        return errs
    bad = [(r, c, grid[r][c]) for r in range(h) for c in range(w)
           if grid[r][c] not in (0, 8)]
    if bad:
        errs.append(f"non-cyan non-bg cells: {bad[:3]}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 8, 10)
        n_segments = ctx.draw_int("n_segments", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 13, 18)
        n_segments = ctx.draw_int("n_segments", 5, 8)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 8, 13)
        n_segments = ctx.draw_int("n_segments", 2, 5)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    horizontal = rng.choice([False, True])
    used: set[int] = set()
    made = 0
    for _ in range(200):
        if made >= n_segments:
            break
        if horizontal:
            choices = [r for r in range(h) if all(abs(r - rr) > 1 for rr in used)]
            if not choices:
                break
            r = rng.choice(choices)
            c = rng.randint(0, w - 4)
            for dc in range(4):
                g[r][c + dc] = 8
            used.add(r)
        else:
            choices = [c for c in range(w) if all(abs(c - cc) > 1 for cc in used)]
            if not choices:
                break
            c = rng.choice(choices)
            r = rng.randint(0, h - 4)
            for dr in range(4):
                g[r + dr][c] = 8
            used.add(c)
        made += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_segments":
        # Empty grid — no length-4 cyan to recolor.
        return g
    if name == "wrong_length":
        # Cyan segments of length 3 and 5 — neither matches the rule's length-4
        # criterion, so no endpoint gets recolored.
        for dc in range(3):
            g[1][1 + dc] = 8
        for dc in range(5):
            g[4][3 + dc] = 8
        for dr in range(3):
            g[3 + dr][10] = 8
        return g
    if name == "single_segment":
        # Only one length-4 segment — minimal evidence of the rule.
        for dc in range(4):
            g[3][3 + dc] = 8
        return g
    return g
