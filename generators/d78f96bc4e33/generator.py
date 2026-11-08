"""Generator for puzzle e7639916.

Rule: collect all cyan(8) cells; their bbox perimeter becomes 1, the
8s are preserved, everything else becomes 0.

Combinatorial axes (8): grid_h/w, bbox_h, bbox_w, n_cyan_cells,
cyan_layout, position_bias, anchor_corner, asymmetry_force.
Degenerates: tiny_bbox, full_grid_bbox, line_only.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d78f96bc4e33"
VERSION = "1.1.0"
TASK_ID = "d78f96bc4e33"
SUMMARY = "Cyan cells defining a bbox; rule draws perimeter as 1."

INVARIANTS = [
    "background is 0",
    ">=3 cyan(8) cells (so bbox is well-defined)",
    "cyan cells span >=2 distinct rows AND >=2 distinct cols",
    "bbox dim >= 3x3 (so frame is visible)",
]

CYAN_LAYOUTS = ("corners_only", "two_corners_one_edge", "perimeter",
                "scattered_in_bbox", "opposite_corners_plus_extra")
DEGENERATE_TEXTURES = ("tiny_bbox", "full_grid_bbox", "line_only")
HELPFUL_TEXTURES = CYAN_LAYOUTS

AXES = {
    "grid_h":          {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "grid_w":          {"type": "int", "default": "rng 8..14", "valid": "6..18"},
    "bbox_h":          {"type": "int", "default": "rng 4..h-2", "valid": "3..h-1"},
    "bbox_w":          {"type": "int", "default": "rng 4..w-2", "valid": "3..w-1"},
    "n_cyan_cells":    {"type": "int", "default": "rng 3..5", "valid": "3..8"},
    "cyan_layout":     {"type": "str", "default": "rng helpful",
                        "valid": "|".join(CYAN_LAYOUTS)},
    "position_bias":   {"type": "str", "default": "rng spread|corner|center",
                        "valid": "spread|corner|center"},
    "anchor_corner":   {"type": "bool", "default": "false",
                        "valid": "true|false"},
    "texture":         {"type": "str", "default": "alias for cyan_layout",
                        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 6, 9
    elif difficulty == "hard":
        h_lo, h_hi = 12, 18
    else:
        h_lo, h_hi = 8, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    bbox_h = int(overrides.get("bbox_h",
                               ctx.draw_int("bbox_h", 4, max(4, h - 2))))
    bbox_w = int(overrides.get("bbox_w",
                               ctx.draw_int("bbox_w", 4, max(4, w - 2))))
    bbox_h = max(3, min(h, bbox_h))
    bbox_w = max(3, min(w, bbox_w))
    n_cyan = int(overrides.get("n_cyan_cells",
                               ctx.draw_int("n_cyan_cells", 3, 5)))
    n_cyan = max(3, min(8, n_cyan))
    layout = (overrides.get("texture") or
              overrides.get("cyan_layout")
              or ctx.draw_choice("cyan_layout", list(CYAN_LAYOUTS)))
    bias = overrides.get("position_bias",
                         ctx.draw_choice("position_bias",
                                         ["spread", "corner", "center"]))
    if bool(overrides.get("anchor_corner", False)):
        r1, c1 = 0, 0
    elif bias == "corner":
        r1 = rng.choice([0, h - bbox_h])
        c1 = rng.choice([0, w - bbox_w])
    elif bias == "center":
        r1 = (h - bbox_h) // 2
        c1 = (w - bbox_w) // 2
    else:
        r1 = rng.randint(0, h - bbox_h)
        c1 = rng.randint(0, w - bbox_w)
    r2 = r1 + bbox_h - 1
    c2 = c1 + bbox_w - 1
    g = full_grid(h, w, 0)
    cells = _layout_cells(layout, r1, c1, r2, c2, n_cyan, rng)
    rs = {r for r, _ in cells}
    cs = {c for _, c in cells}
    if len(rs) < 2:
        cells.append((r2, c1))
    if len(cs) < 2:
        cells.append((r1, c2))
    cells = [(r1, c1), (r2, c2)] + cells
    seen = set()
    for r, c in cells:
        if (r, c) in seen:
            continue
        seen.add((r, c))
        g[r][c] = 8
    return g


def _layout_cells(layout, r1, c1, r2, c2, n, rng):
    corners = [(r1, c1), (r1, c2), (r2, c1), (r2, c2)]
    perim = []
    for c in range(c1, c2 + 1):
        perim.append((r1, c)); perim.append((r2, c))
    for r in range(r1 + 1, r2):
        perim.append((r, c1)); perim.append((r, c2))
    interior = [(r, c) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)]
    if layout == "corners_only":
        return corners[:n]
    if layout == "two_corners_one_edge":
        rng.shuffle(corners)
        cells = corners[:2]
        edge = [p for p in perim if p not in cells]
        rng.shuffle(edge)
        return cells + edge[:n - 2]
    if layout == "perimeter":
        rng.shuffle(perim)
        return perim[:n]
    if layout == "scattered_in_bbox":
        all_cells = list(set(perim) | set(interior))
        rng.shuffle(all_cells)
        return all_cells[:n]
    if layout == "opposite_corners_plus_extra":
        diag = [(r1, c1), (r2, c2)] if rng.random() < 0.5 else [(r1, c2), (r2, c1)]
        extras = [p for p in perim if p not in diag]
        rng.shuffle(extras)
        return diag + extras[:n - 2]
    return corners[:n]


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "tiny_bbox":
        r1 = rng.randint(0, h - 3)
        c1 = rng.randint(0, w - 3)
        g[r1][c1] = 8; g[r1][c1 + 2] = 8; g[r1 + 2][c1] = 8
        return g
    if name == "full_grid_bbox":
        g[0][0] = 8; g[0][w - 1] = 8; g[h - 1][0] = 8; g[h - 1][w - 1] = 8
        return g
    if name == "line_only":
        # All cyan on one row → bbox has zero height; rule degenerates.
        r = h // 2
        for c in range(1, w - 1, 2):
            g[r][c] = 8
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 8]
    if len(cells) < 3:
        errs.append(f"expected at least three cyan cells, got {len(cells)}")
    if any(v not in (0, 8) for row in grid for v in row):
        errs.append("input should contain only background and cyan")
    if cells:
        rows = {r for r, _ in cells}; cols = {c for _, c in cells}
        if len(rows) < 2 or len(cols) < 2:
            errs.append("cyan cells must span at least two rows and two columns")
        if max(rows) - min(rows) + 1 < 3 or max(cols) - min(cols) + 1 < 3:
            errs.append("cyan bbox must be at least 3x3")
    return errs
