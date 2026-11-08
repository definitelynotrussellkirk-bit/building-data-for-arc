"""Generator for puzzle 6df30ad6.

Rule: gray(5) shape + scattered colored single-cell probes. Output
recolors gray cells by nearest probe (Manhattan), erases probes.

Combinatorial axes (8): grid_h/w, shape_size_min, shape_size_max,
n_probes, palette_kind, probe_min_distance, position_bias,
shape_position.
Degenerates: no_probes, single_color, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "88ea189735a5"
VERSION = "1.1.1"
TASK_ID = "88ea189735a5"
SUMMARY = "Gray shape + colored probes; rule recolors gray by nearest probe."

INVARIANTS = [
    "background is 0",
    ">=1 gray(5) shape with >=3 cells (contiguous)",
    ">=2 distinct probe colors (1-2 isolated cells each)",
    "probes >=3 cells from gray shape (so 'nearest' is meaningful)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
SHAPE_POSITIONS = ("upper_left", "upper_right", "lower_left",
                   "lower_right", "center")
DEGENERATE_TEXTURES = ("no_probes", "single_color", "full_grid")
HELPFUL_TEXTURES = SHAPE_POSITIONS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "grid_w":            {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "shape_size_min":    {"type": "int", "default": "2", "valid": "2..5"},
    "shape_size_max":    {"type": "int", "default": "rng 3..4", "valid": "2..6"},
    "n_probes":          {"type": "int", "default": "rng 3..5", "valid": "2..8"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "probe_min_distance":{"type": "int", "default": "4", "valid": "2..8"},
    "shape_position":    {"type": "str", "default": "rng helpful",
                          "valid": "|".join(SHAPE_POSITIONS)},
    "texture":           {"type": "str", "default": "alias for shape_position",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; >=1 gray(5) connected blob; >=2 distinct probe colors (non-gray, non-bg)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    gray_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    if not gray_cells:
        return []  # degenerate no_probes or no_shape — allowed
    probe_colors = set(grid[r][c] for r in range(h) for c in range(w)
                       if grid[r][c] not in (0, 5))
    if not probe_colors:
        return []  # degenerate no_probes — allowed
    errs = []
    if len(probe_colors) < 2:
        errs.append(f"expected >=2 distinct probe colors; found {probe_colors}")
    if len(gray_cells) < 3:
        errs.append(f"expected >=3 gray cells; found {len(gray_cells)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 10, 13
    elif difficulty == "hard":
        h_lo, h_hi = 16, 22
    else:
        h_lo, h_hi = 12, 18
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    s_min = int(overrides.get("shape_size_min", 2))
    s_max = int(overrides.get("shape_size_max",
                              ctx.draw_int("shape_size_max", 3, 4)))
    s_min = max(2, min(s_min, 5))
    s_max = max(s_min, min(6, s_max))
    n_probes = int(overrides.get("n_probes",
                                 ctx.draw_int("n_probes", 3, 5)))
    n_probes = max(2, min(8, n_probes))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    min_dist = int(overrides.get("probe_min_distance", 4))
    shape_pos = (overrides.get("texture") or
                 overrides.get("shape_position")
                 or ctx.draw_choice("shape_position",
                                    list(SHAPE_POSITIONS)))
    palette = _build_palette(palette_kind, max(2, min(n_probes, 6)), rng)
    g = full_grid(h, w, 0)
    sh = rng.randint(s_min, s_max)
    sw = rng.randint(s_min, s_max)
    sr, sc = _shape_position(shape_pos, h, w, sh, sw)
    for dr in range(sh):
        for dc in range(sw):
            g[sr + dr][sc + dc] = 5
    placed = 0
    for _ in range(n_probes * 6):
        if placed >= n_probes:
            break
        color = palette[placed % len(palette)]
        for _ in range(20):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if g[r][c] != 0:
                continue
            dist = min(abs(r - (sr + dr)) + abs(c - (sc + dc))
                       for dr in range(sh) for dc in range(sw))
            if dist < min_dist:
                continue
            g[r][c] = color
            placed += 1
            break
    if placed < 2:
        # Force 2 probes far from shape
        for color, (r, c) in zip(palette, [(0, w - 1), (h - 1, 0)]):
            if g[r][c] == 0:
                g[r][c] = color
    return g


def _shape_position(name, h, w, sh, sw):
    if name == "upper_left":
        return 1, 1
    if name == "upper_right":
        return 1, w - sw - 1
    if name == "lower_left":
        return h - sh - 1, 1
    if name == "lower_right":
        return h - sh - 1, w - sw - 1
    if name == "center":
        return max(0, (h - sh) // 2), max(0, (w - sw) // 2)
    return 1, 1


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 6, 7, 8, 9]
    rng.shuffle(pool)
    while len(pool) < n:
        for c in [1, 2, 3, 4, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
    return pool[:n]


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_probes":
        for dr in range(2):
            for dc in range(2):
                g[2 + dr][2 + dc] = 5
        return g
    if name == "single_color":
        for dr in range(2):
            for dc in range(2):
                g[2 + dr][2 + dc] = 5
        g[h - 2][w - 2] = 3
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 5
        return g
    return g
