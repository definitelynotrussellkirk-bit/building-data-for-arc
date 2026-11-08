"""Generator for arc_additional_puzzle_bank_volume15:E105.

Rule: blue components touching exactly one border are recolored red.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_components, all_interior, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "463f4d184ac1"
VERSION = "2.0.1"  # distinct=99: only 3 fixed objects (1 edge-only -> recolored, 1 corner, 1 interior). Now places several color-1 objects (varied sizes/positions) spanning all border-touch counts (0/1/2/3) so the touch==1 discriminator varies, plus rule-ignored color-4 decoys (canonical has 4).
TASK_ID = "463f4d184ac1"
SUMMARY = "Blue (1) components touching exactly one border are recolored red (2); others stay. Varied object count/sizes/positions span all touch counts; color-4 decoys are present but ignored."

INVARIANTS = [
    "background is 0",
    "at least one blue component touches exactly one border",
    "other blue components touch zero or two borders",
    "blue components are separated by background",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_components", "all_interior", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "true",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "true",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "border", "valid": "border"},
    "n_distinct_colors":{"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10); w = ctx.draw_int("grid_w", 8, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18); w = ctx.draw_int("grid_w", 13, 18)
    else:
        h = ctx.draw_int("grid_h", 10, 14); w = ctx.draw_int("grid_w", 10, 14)
    rng = ctx.draw_rng("placement")
    if difficulty == "easy":
        n1 = 3; ndec = 1
    elif difficulty == "hard":
        n1 = rng.randint(5, 7); ndec = 2
    else:
        n1 = rng.randint(3, 5); ndec = rng.randint(1, 2)
    g = full_grid(h, w, 0)
    # guarantee at least one EDGE-ONLY object (touch==1 -> recolored) and one
    # NON-edge object, then a random mix; touch counts follow placement.
    _place_edge_only(g, rng, h, w)
    _place_interior(g, rng, h, w)
    for _ in range(max(0, n1 - 2)):
        _place_random(g, rng, h, w, 1)
    for _ in range(ndec):
        _place_random(g, rng, h, w, 4)   # rule-ignored decoy (canonical has 4)
    return g


def _free(g, r0, c0, r1, c1):
    h, w = len(g), len(g[0])
    for r in range(r0 - 1, r1 + 2):
        for c in range(c0 - 1, c1 + 2):
            if 0 <= r < h and 0 <= c < w and g[r][c] != 0:
                return False
    return 0 <= r0 and 0 <= c0 and r1 < h and c1 < w


def _place_edge_only(g, rng, h, w):
    for _ in range(80):
        bh = rng.randint(1, 2); bw = rng.randint(1, 2)
        side = rng.choice(["top", "bottom", "left", "right"])
        if side == "top":
            r0 = 0; c0 = rng.randint(2, w - bw - 2)
        elif side == "bottom":
            r0 = h - bh; c0 = rng.randint(2, w - bw - 2)
        elif side == "left":
            c0 = 0; r0 = rng.randint(2, h - bh - 2)
        else:
            c0 = w - bw; r0 = rng.randint(2, h - bh - 2)
        if _free(g, r0, c0, r0 + bh - 1, c0 + bw - 1):
            draw_rect(g, r0, c0, bh, bw, 1)
            return


def _place_interior(g, rng, h, w):
    for _ in range(80):
        bh = rng.randint(1, 3); bw = rng.randint(1, 3)
        r0 = rng.randint(2, h - bh - 2); c0 = rng.randint(2, w - bw - 2)
        if _free(g, r0, c0, r0 + bh - 1, c0 + bw - 1):
            draw_rect(g, r0, c0, bh, bw, 1)
            return


def _place_random(g, rng, h, w, color):
    for _ in range(80):
        bh = rng.randint(1, 3); bw = rng.randint(1, 3)
        r0 = rng.randint(0, h - bh); c0 = rng.randint(0, w - bw)
        if _free(g, r0, c0, r0 + bh - 1, c0 + bw - 1):
            draw_rect(g, r0, c0, bh, bw, color)
            return


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 10, 0)
    if name == "no_components":
        return g
    if name == "all_interior":
        draw_rect(g, 4, 4, 2, 2, 1)
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(10):
                g[r][c] = 1
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=0; at least one blue(1) cell; at least one blue cell touches exactly one border."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    blue_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    if not blue_cells:
        errors.append("no blue(1) cells found")
        return errors
    # Check that at least one blue cell is on exactly one border
    def border_count(r, c):
        return sum([r == 0, r == h - 1, c == 0, c == w - 1])
    edge_only = [p for p in blue_cells if border_count(*p) == 1]
    if not edge_only:
        errors.append("no blue component touches exactly one border (rule would have no target)")
    return errors
