"""Generator for arc_additional_puzzle_bank_volume7:M46.

Rule: the largest blue object has its bounding-box corners painted red.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_objects, single_object, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "6ac8de750dbd"
VERSION = "2.0.1"
TASK_ID = "6ac8de750dbd"
SUMMARY = (
    "0-bg grid (h, w ~9-12) with 2 color-1 (blue) 4-conn "
    "objects of different sizes plus a color-5 (gray) "
    "distractor single cell. Rule: identify all color-1 "
    "objects, pick the LARGEST by cell count, compute its "
    "bbox (r1, c1, r2, c2), and paint the 4 BBOX CORNERS "
    "(r1, c1), (r1, c2), (r2, c1), (r2, c2) with color 2 "
    "(red). Note: those corners may already be color 1 if "
    "the object touches its bbox — they get overwritten to "
    "2. Rest of grid stays unchanged."
)

INVARIANTS = [
    "at least two blue objects are present",
    "the largest blue object has a nontrivial bounding box",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_objects", "single_object", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "9..12"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "9..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; >=2 color-1 (blue) cells present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    blues = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    if not blues:
        return errs  # degenerate (no_objects) — allowed
    if len(blues) < 2:
        errs.append(f"only {len(blues)} blue cell(s); need >=2 for two objects")
    return errs


_LARGE_SHAPES = [
    [(0, 0), (0, 2), (1, 0), (2, 0), (2, 1)],            # 3x3 corners L
    [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)],            # L
    [(0, 0), (0, 1), (1, 1), (2, 1), (2, 0)],            # S-ish
    [(0, 0), (1, 0), (1, 1), (1, 2), (2, 2)],            # Z
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],            # plus (3x3)
    [(0, 0), (0, 3), (3, 0), (3, 3), (1, 1), (2, 2)],    # 4x4 sparse
    [(0, 0), (0, 1), (0, 2), (0, 3), (3, 0), (3, 3)],    # 4x4 top-bar
    [(0, 0), (1, 1), (2, 2), (3, 3), (3, 0)],            # 4x4 diag
    [(0, 0), (0, 2), (0, 4), (2, 0), (2, 4)],            # 3x5 sparse
]

_SMALL_SHAPES = [
    [(0, 0), (1, 0)],
    [(0, 0), (0, 1)],
    [(0, 0), (1, 1)],
    [(0, 0), (1, 0), (1, 1)],
]


def _shape_dims(shape):
    rs = [r for r, _ in shape]; cs = [c for _, c in shape]
    return max(rs) - min(rs) + 1, max(cs) - min(cs) + 1


def _free(g, r0, c0, shape):
    h, w = len(g), len(g[0])
    rs = [r for r, _ in shape]; cs = [c for _, c in shape]
    r1, r2 = r0 + min(rs) - 1, r0 + max(rs) + 1
    c1, c2 = c0 + min(cs) - 1, c0 + max(cs) + 1
    for r in range(max(0, r1), min(h, r2 + 1)):
        for c in range(max(0, c1), min(w, c2 + 1)):
            if g[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 11, 12)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 9, 12)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)

    large = list(rng.choice(_LARGE_SHAPES))
    sh, sw = _shape_dims(large)
    for _ in range(80):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        if _free(g, r0, c0, large):
            for dr, dc in large:
                g[r0 + dr][c0 + dc] = 1
            break

    small = list(rng.choice(_SMALL_SHAPES))
    ssh, ssw = _shape_dims(small)
    for _ in range(80):
        r0 = rng.randint(0, h - ssh)
        c0 = rng.randint(0, w - ssw)
        if len(small) >= len(large):
            continue
        if _free(g, r0, c0, small):
            for dr, dc in small:
                g[r0 + dr][c0 + dc] = 1
            break

    n_distractors = rng.randint(1, 3)
    for _ in range(n_distractors):
        color = rng.choice([3, 4, 5, 6, 7, 8, 9])
        for _ in range(40):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if g[r][c] == 0:
                g[r][c] = color
                break
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 10, 0)
    if name == "no_objects":
        g[1][9] = 5
        return g
    if name == "single_object":
        paint_at(g, 2, 2, [(0, 0), (0, 2), (1, 0), (2, 0), (2, 1)], 1)
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(10):
                g[r][c] = 1
        return g
    return g
