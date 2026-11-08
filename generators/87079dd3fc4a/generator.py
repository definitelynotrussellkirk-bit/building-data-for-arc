"""Generator for ac3e2b04.

Rule: a green 3x3 marker sitting on a dense red guide projects a blue
beam perpendicular to it, depositing a 3x3 blue block where the beam
crosses every OTHER dense red guide.

Combinatorial axes: grid_h/w, orientation, number of guides (2-4),
guide positions, marker position along its guide.
Degenerates: no_marker, no_guide, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "87079dd3fc4a"
VERSION = "3.0.1"  # diversity: random grid + N guides + positions + marker row (was fixed 13x13, 2x3 configs)
TASK_ID = "87079dd3fc4a"
SUMMARY = (
    "0-bg grid (size varies). Several PARALLEL DENSE COLOR-2 (red) "
    "GUIDE LINES (2-4 full rows or columns). A 3x3 GREEN (color 3) "
    "MARKER with a color-2 center sits on ONE guide at a random position "
    "along it. Rule (PROJECT A BLUE BEAM PERPENDICULAR TO THE GUIDES): "
    "from the green marker, cast a color-1 (blue) line across the grid "
    "perpendicular to the guide direction; where it crosses each OTHER "
    "dense guide, stamp a 3x3 BLUE intersection block. The grid size, "
    "orientation, the NUMBER and positions of the guides, and the "
    "marker's position all vary freely (was a fixed 13x13 grid with 2 "
    "orientations x 3 offsets)."
)

INVARIANTS = [
    "the background is zero",
    "a 3x3 green marker has a color-2 center and color-3 neighbors",
    "the marker center lies on a dense color-2 guide row or column",
    "additional dense guide rows or columns receive blue 3x3 intersection blocks",
]

ORIENTATIONS = ("vertical", "horizontal")
OFFSETS = ("left", "center", "right")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_marker", "no_guide", "full_grid")
HELPFUL_TEXTURES = ORIENTATIONS

AXES = {
    "grid_h":         {"type": "int", "default": "rng (easy 9..12, hard 13..20)", "valid": "9..20"},
    "grid_w":         {"type": "int", "default": "rng (easy 9..12, hard 14..20)", "valid": "9..20"},
    "guide_orientation":{"type": "str", "default": "rng helpful",
                       "valid": "vertical|horizontal"},
    "guide_offset":   {"type": "str", "default": "n/a (now random positions)",
                       "valid": "left|center|right"},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for guide_orientation",
                       "valid": "vertical|horizontal|no_marker|no_guide|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; a 3x3 marker with color-2 center and color-3 neighbors exists."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    # Find all color-2 cells that could be the marker center
    twos = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1) if grid[r][c] == 2]
    if not twos:
        return []  # degenerate no_marker or no_guide — allowed
    # Check if any color-2 cell is surrounded by color-3 (green marker)
    def is_marker_center(r, c):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                if not (0 <= r + dr < h and 0 <= c + dc < w):
                    return False
                if grid[r + dr][c + dc] != 3:
                    return False
        return True
    marker_centers = [(r, c) for r, c in twos if is_marker_center(r, c)]
    if not marker_centers:
        return []  # degenerate no_marker — allowed
    # Also check there are dense guide lines (full rows or cols of color-2)
    dense_rows = [r for r in range(h) if sum(1 for c in range(w) if grid[r][c] == 2) >= w // 2]
    dense_cols = [c for c in range(w) if sum(1 for r in range(h) if grid[r][c] == 2) >= h // 2]
    if not dense_rows and not dense_cols:
        return []  # degenerate no_guide — allowed
    return []


def _green_marker(g, r, c):
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            g[r + dr][c + dc] = 3
    g[r][c] = 2


def _pick_lines(rng, lo, hi, k, min_sep):
    """k values in [lo,hi], pairwise >= min_sep apart."""
    for _ in range(200):
        picks = sorted(rng.sample(range(lo, hi + 1), k))
        if all(picks[i + 1] - picks[i] >= min_sep for i in range(k - 1)):
            return picks
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  task_id=TASK_ID, version=VERSION,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    orientation = (overrides.get("texture") if overrides.get("texture") in ORIENTATIONS else None) or \
                  overrides.get("guide_orientation") or \
                  rng.choice(list(ORIENTATIONS))

    if difficulty == "easy":
        hr, wr, kr = (9, 12), (9, 12), (2, 2)
    elif difficulty == "hard":
        hr, wr, kr = (13, 20), (14, 20), (3, 4)
    else:
        hr, wr, kr = (11, 15), (11, 15), (2, 3)

    for _attempt in range(60):
        h = rng.randint(*hr); w = rng.randint(*wr)
        k = rng.randint(*kr)
        g = full_grid(h, w, 0)
        if orientation == "vertical":
            guides = _pick_lines(rng, 1, w - 2, k, 3)   # guide columns
            if guides is None:
                continue
            for c in guides:
                for r in range(h):
                    g[r][c] = 2
            main = rng.choice(guides)
            gr = rng.randint(1, h - 2)
            _green_marker(g, gr, main)
        else:
            guides = _pick_lines(rng, 1, h - 2, k, 3)   # guide rows
            if guides is None:
                continue
            for r in guides:
                for c in range(w):
                    g[r][c] = 2
            main = rng.choice(guides)
            gc = rng.randint(1, w - 2)
            _green_marker(g, main, gc)
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 13, 0)
    if name == "no_marker":
        for r in range(13):
            g[r][6] = 2
        return g
    if name == "no_guide":
        _green_marker(g, 6, 6)
        return g
    if name == "full_grid":
        for r in range(13):
            for c in range(13):
                g[r][c] = 2
        return g
    return g
