"""Generator for 0bb8deee.

Rule: mode-color cross + 4 quadrant shapes; rule outputs 6x6 quadrant
grid.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors,
shape_density.
Degenerates: no_cross, no_shapes, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "24ef0b5ae2e1"
VERSION = "2.0.1"
TASK_ID = "24ef0b5ae2e1"
SUMMARY = (
    "0-bg grid (h, w ~11-15) with: (a) a CROSS — full "
    "row + full col both painted in `cc` (cross color, "
    "becomes mode color); (b) 4 SHAPES (one per "
    "quadrant) in 4 distinct non-cc colors, each fitting "
    "in 3×3 with non-trivial structure (≥2 cells, "
    "anchored at corners). Rule: detect the cross (mode "
    "color, full row + col). Crop each quadrant. Assemble "
    "the 4 quadrant shapes into a 6×6 output grid "
    "arranged as TL/TR/BL/BR in the same layout as their "
    "source quadrants. Net: a 6×6 mini-grid showing the "
    "4 shapes packed at fixed corners."
)

INVARIANTS = [
    "one mode-color row and one mode-color col form the cross",
    "exactly four non-bg non-cc shapes one per quadrant",
    "each shape's bbox fits in 3x3",
    "shape colors are distinct from each other and from cc",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_cross", "no_shapes", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..15", "valid": "9..18"},
    "grid_w":         {"type": "int", "default": "rng 11..15", "valid": "9..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "5", "valid": "5"},
    "position_bias":  {"type": "str", "default": "rng", "valid": "rng"},
    "n_distinct_colors":{"type": "int", "default": "5", "valid": "5"},
    "shape_density":  {"type": "float", "default": "0.6", "valid": "0.5..0.8"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one full row AND one full column of the same color (the cross)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    # Find full rows (all same non-zero value)
    full_rows = [(r, grid[r][0]) for r in range(h)
                 if grid[r][0] != 0 and all(grid[r][c] == grid[r][0] for c in range(w))]
    # Find full cols (all same non-zero value)
    full_cols = [(c, grid[0][c]) for c in range(w)
                 if grid[0][c] != 0 and all(grid[r][c] == grid[0][c] for r in range(h))]
    if not full_rows and not full_cols:
        return errors  # degenerate no_cross — allowed
    if len(full_rows) != 1:
        errors.append(f"expected exactly 1 full cross-row; found {len(full_rows)}")
    if len(full_cols) != 1:
        errors.append(f"expected exactly 1 full cross-col; found {len(full_cols)}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 11, 12
    elif difficulty == "hard":
        h_lo, h_hi = 14, 17
    else:
        h_lo, h_hi = 11, 15
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    palette = ctx.draw_distinct_colors("palette", n=5, exclude={0})
    cc = palette[0]
    shape_palette = palette[1:]
    g = full_grid(h, w, 0)
    cr = rng.randint(h // 3, 2 * h // 3)
    cl = rng.randint(w // 3, 2 * w // 3)
    for c in range(w):
        g[cr][c] = cc
    for r in range(h):
        g[r][cl] = cc
    quadrants = [
        (0, cr - 1, 0, cl - 1),
        (0, cr - 1, cl + 1, w - 1),
        (cr + 1, h - 1, 0, cl - 1),
        (cr + 1, h - 1, cl + 1, w - 1),
    ]
    for i, (rmin, rmax, cmin, cmax) in enumerate(quadrants):
        if rmax - rmin < 2 or cmax - cmin < 2:
            return [[0]]
        sh = rng.randint(2, min(3, rmax - rmin))
        sw = rng.randint(2, min(3, cmax - cmin))
        rr = rng.randint(rmin, rmax - sh + 1)
        rcc = rng.randint(cmin, cmax - sw + 1)
        for dr in range(sh):
            for dc in range(sw):
                if rng.random() < 0.6:
                    g[rr + dr][rcc + dc] = shape_palette[i]
        g[rr][rcc] = shape_palette[i]
        g[rr + sh - 1][rcc + sw - 1] = shape_palette[i]
    return g



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify one full-row/full-column cross and one small distinct-color shape
    per quadrant.  A wrong cross color or missing quadrant collapses the 6x6
    packed-output lesson."""
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    row_axes = []
    for r in range(h):
        vals = set(grid[r])
        if len(vals) == 1 and grid[r][0] != 0:
            row_axes.append((r, grid[r][0]))
    col_axes = []
    for c in range(w):
        vals = {grid[r][c] for r in range(h)}
        if len(vals) == 1 and grid[0][c] != 0:
            col_axes.append((c, grid[0][c]))
    pairs = [(r, c, col) for r, col in row_axes for c, col2 in col_axes if col == col2]
    if len(pairs) != 1:
        errs.append(f"expected exactly one same-color full row/col cross, got rows={row_axes}, cols={col_axes}")
        return errs
    cr, cc, cross = pairs[0]
    quadrants = [
        (0, cr - 1, 0, cc - 1),
        (0, cr - 1, cc + 1, w - 1),
        (cr + 1, h - 1, 0, cc - 1),
        (cr + 1, h - 1, cc + 1, w - 1),
    ]
    shape_colors = []
    for q, (r0, r1, c0, c1) in enumerate(quadrants):
        cells = [(r, c, grid[r][c]) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1) if grid[r][c] not in (0, cross)]
        colors = sorted({v for _, _, v in cells})
        if len(colors) != 1:
            errs.append(f"quadrant {q} expected exactly one shape color, found {colors}")
            continue
        shape_colors.append(colors[0])
        coords = [(r, c) for r, c, _ in cells]
        if len(coords) < 2:
            errs.append(f"quadrant {q} shape has only {len(coords)} cells")
            continue
        rs = [r for r, _ in coords]
        cs = [c for _, c in coords]
        if max(rs) - min(rs) + 1 > 3 or max(cs) - min(cs) + 1 > 3:
            errs.append(f"quadrant {q} shape bbox exceeds 3x3")
    if len(shape_colors) == 4 and len(set(shape_colors)) != 4:
        errs.append(f"shape colors must be distinct, got {shape_colors}")
    return errs

def _draw_from_degenerate(name, rng):
    g = full_grid(13, 13, 0)
    if name == "no_cross":
        g[3][3] = 2
        return g
    if name == "no_shapes":
        for c in range(13):
            g[6][c] = 5
        for r in range(13):
            g[r][6] = 5
        return g
    if name == "full_grid":
        for r in range(13):
            for c in range(13):
                g[r][c] = 5
        return g
    return g
