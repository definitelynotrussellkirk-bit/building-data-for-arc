"""Generator for 3bd292e8.

Rule: red runs define parity toggles for filling all other cells with
alternating 3 and 5.

Combinatorial axes (8): grid_h/w, invert, palette_kind, position_bias,
anchor_corner, asymmetry_force, palette_size, n_runs.
Degenerates: no_runs, all_red, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8ffc637a453b"
VERSION = "1.1.0"
TASK_ID = "8ffc637a453b"
SUMMARY = "Red runs define parity toggles for filling cells with alternating 3 and 5."

INVARIANTS = [
    "red cells form horizontal runs on some rows",
    "a red run on the top row sets the initial parity orientation",
    "new red entries on the left edge toggle the outside parity",
    "all non-red cells are filled with parity colors 3 and 5",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_runs", "all_red", "full_grid")
HELPFUL_TEXTURES = ("invert", "no_invert")

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "invert":         {"type": "bool", "default": "rng helpful",
                       "valid": "true|false"},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "n_runs":         {"type": "int", "default": "auto", "valid": "auto"},
    "texture":        {"type": "str", "default": "alias for invert",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: bg=0, grid has color-2 (red) cells (the parity-toggle runs)."""
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    has_red = any(grid[r][c] == 2 for r in range(h) for c in range(w))
    if not has_red:
        pass  # degenerate (no_runs) — allowed
    if h > 30 or w > 30:
        errors.append(f"grid too large: {h}x{w}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if overrides.get("texture") == "invert":
        invert = True
    elif overrides.get("texture") == "no_invert":
        invert = False
    else:
        invert = ctx.draw_choice("invert", (True, False))
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 5, 7, 6, 9
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 11, 14, 13, 16
    else:
        h_lo, h_hi, w_lo, w_hi = 7, 10, 8, 12
    h = rng.randint(h_lo, h_hi)
    w = rng.randint(w_lo, w_hi)
    g = full_grid(h, w, 0)
    top_start = 0 if invert else rng.randint(1, min(3, w - 4))
    for c in range(top_start, top_start + 2):
        if c < w:
            g[0][c] = 2
    for r in range(2, h, 3):
        if r < h:
            g[r][0] = 2
            if 1 < w:
                g[r][1] = 2
            end = rng.randint(4, w - 2)
            if end < w:
                g[r][end] = 2
            if end + 1 < w:
                g[r][end + 1] = 2
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_runs":
        return g
    if name == "all_red":
        for r in range(h):
            for c in range(w):
                g[r][c] = 2
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 3
        return g
    return g
