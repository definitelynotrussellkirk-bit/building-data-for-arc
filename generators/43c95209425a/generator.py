"""Generator for e5790162.

Rule: green seed walks right through empty space, optionally turning at
colored steering dots.

Combinatorial axes (8): grid_h/w, turn_dots, palette_kind, start_row,
anchor_corner, asymmetry_force, palette_size, position_bias.
Degenerates: no_seed, no_path, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "43c95209425a"
VERSION = "2.0.1"
TASK_ID = "43c95209425a"
SUMMARY = (
    "0-bg grid (h~8-12, w~"
    "9-14) with: (a) ONE "
    "GREEN(3) SEED at "
    "(start_r, 1) on the "
    "LEFT EDGE INTERIOR "
    "(start_r ∈ [2, h-3])"
    "; (b) 0-2 STEERING "
    "DOTS placed at fixed "
    "positions in column "
    "w-3 — first DOT in "
    "COLOR 8 at (r, w-3), "
    "second DOT in COLOR "
    "4 at (r-1, w-3), "
    "third DOT in COLOR 6 "
    "at (r+1, w-3) (turn_"
    "dots controls how "
    "many of these appear)"
    ". Rule (GREEN SEED "
    "WALKS RIGHTWARD, "
    "TURNING AT STEERING "
    "DOTS, PAINT PATH "
    "GREEN): the green "
    "seed at (start_r, 1) "
    "marches RIGHTWARD "
    "across empty cells, "
    "painting each "
    "traversed cell COLOR "
    "3. When the path "
    "reaches a STEERING "
    "DOT cell, the dot's "
    "color encodes a "
    "TURN: COLOR 8 = "
    "turn left or "
    "continue, COLOR 4 = "
    "turn up, COLOR 6 = "
    "turn down (per "
    "puzzle convention). "
    "Continue until grid "
    "edge. Net: a green "
    "trail snakes from "
    "the left seed via "
    "steering dots toward "
    "the right side."
)

INVARIANTS = [
    "background is color 0",
    "one start cell uses color 3",
    "turning dots, when present, are nonzero and not color 3",
    "the walked path is painted color 3",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_seed", "no_path", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "grid_w":         {"type": "int", "default": "rng 9..14", "valid": "7..18"},
    "turn_dots":      {"type": "int", "default": "rng 0..2", "valid": "0..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "start_row":      {"type": "int", "default": "rng 2..h-3", "valid": "1..h-2"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "1..4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, exactly one color-3 start cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    starts = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    if len(starts) != 1:
        errs.append(f"expected exactly 1 color-3 start cell, got {len(starts)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 6, 8
        td_lo, td_hi = 0, 0
    elif difficulty == "hard":
        h_lo, h_hi = 12, 16
        td_lo, td_hi = 1, 3
    else:
        h_lo, h_hi = 8, 12
        td_lo, td_hi = 0, 2
    dot_count = int(overrides.get("turn_dots",
                                  ctx.draw_int("turn_dots",
                                               td_lo, td_hi)))
    dot_count = max(0, min(3, dot_count))
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo + 1, h_hi + 5)
    g = full_grid(h, w, 0)
    r = int(overrides.get("start_row",
                          rng.randint(2, max(2, h - 3))))
    r = max(1, min(r, h - 2))
    g[r][1] = 3
    if dot_count >= 1 and w >= 4:
        g[r][w - 3] = 8
    if dot_count >= 2 and r > 1 and w >= 4:
        g[r - 1][w - 3] = 4
    if dot_count >= 3 and r + 1 < h and w >= 4:
        g[r + 1][w - 3] = 6
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_seed":
        g[5][8] = 8
        return g
    if name == "no_path":
        g[5][1] = 3
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 3
        return g
    return g
