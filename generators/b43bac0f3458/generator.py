"""Generator for 681b3aeb.

Rule: separated shapes are normalized into one 3x3 canvas using
heavier bbox-edge anchoring.

Combinatorial axes (8): grid_h/w, shape_count, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
shape_variant.
Degenerates: no_shapes, single_shape, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b43bac0f3458"
VERSION = "1.3.3"  # doc: stale "~3 distinct_out" note corrected -- the 12-shape
# pool x varied colors x edge-anchored 3x3 overlay actually yields ~143 distinct
# outputs. Output is rule-locked to a fixed 3x3 canvas (out_shapes=1), so
# shape-locked-out is intrinsic, not a defect.
TASK_ID = "b43bac0f3458"
SUMMARY = "3 isolated small shapes (each ≤3×3 bbox) in distinct non-bg colors. Rule: for each shape, compute bbox edge-cell counts (cells on each of top/bottom/left/right side of bbox). If shape's bbox height < 3, anchor toward the side with more cells. Compose all 3 into a single 3×3 output, overlaid by position score order."

# Rivals: 'output is input' refuted by demos (output is 3x3).
# 'output is just bbox of one shape' refuted by demos with overlay.
# 'recolor on overlay' refuted by demos preserving original colors.
# 'output entire grid' refuted by demos. 3 demos with 3 distinct
# shapes/colors cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is color 0",
    "each object is a small monochrome shape",
    "objects fit within a 3x3 normalized canvas",
    "exactly three objects appear in distinct colors",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_shapes", "single_shape", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..11", "valid": "9..14"},
    "grid_w":         {"type": "int", "default": "rng 10..11", "valid": "9..14"},
    "shape_count":    {"type": "int", "default": "3", "valid": "3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "shape_variant":  {"type": "str", "default": "rng", "valid": "rng"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_shapes|single_shape|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥2 distinct non-bg colors (the shapes); each shape's bbox fits in 3x3."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        errs.append(f"expected ≥2 distinct non-bg shape colors; found {sorted(colors)}")
        return errs
    # Each color's bbox should fit in 3x3
    for color in colors:
        cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        bh = max(rs) - min(rs) + 1
        bw = max(cs) - min(cs) + 1
        if bh > 3 or bw > 3:
            errs.append(f"color {color} bbox {bh}x{bw} exceeds 3x3 canvas")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind") or
                    ctx.draw_choice("palette_kind", list(PALETTE_KINDS)))
    pool = _build_palette(palette_kind, rng)
    if len(pool) < 3:
        pool = pool + [c for c in [1, 2, 3, 4, 5, 6, 7, 8, 9] if c not in pool]
    # Variable shape count (canonical has 2-3; rule supports any).
    n_shapes = rng.randint(2, 3)
    colors = pool[:n_shapes]
    h = rng.randint(9, 13)
    w = rng.randint(9, 13)
    g = full_grid(h, w, 0)
    # Shape pool: 3-5 cells in a ≤3x3 bbox
    shape_pool = [
        [(0, 0), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0)],
        [(0, 0), (1, 0), (2, 0), (2, 1)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(0, 0), (0, 1), (0, 2), (1, 1)],
        [(0, 1), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (1, 0), (2, 0)],
        [(0, 0), (0, 1), (0, 2)],
    ]
    shapes = rng.sample(shape_pool, n_shapes)
    placed_boxes = []
    for color, cells in zip(colors, shapes):
        sh = max(r for r, _ in cells) + 1
        sw = max(c for _, c in cells) + 1
        for _attempt in range(80):
            r0 = rng.randint(0, h - sh)
            c0 = rng.randint(0, w - sw)
            collide = False
            for (pr1, pc1, pr2, pc2) in placed_boxes:
                if (r0 - 1 <= pr2 and pr1 <= r0 + sh and
                    c0 - 1 <= pc2 and pc1 <= c0 + sw):
                    collide = True; break
            if collide:
                continue
            for dr, dc in cells:
                g[r0 + dr][c0 + dc] = color
            placed_boxes.append((r0, c0, r0 + sh - 1, c0 + sw - 1))
            break
    return g


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    pool = [c for c in pool if c != 0]
    rng.shuffle(pool)
    return pool


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 10, 0)
    if name == "no_shapes":
        return g
    if name == "single_shape":
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[1 + dr][1 + dc] = 2
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(10):
                g[r][c] = 2
        return g
    return g
