"""Generator for arc_additional_puzzle_bank_volume5:M29.

Rule: a marker direction slides the colored object rigidly until
blocked.

Combinatorial axes (8): grid_h, grid_w, palette_kind, marker_dir,
palette_size, position_bias, n_distinct_colors, object_kind, texture.
Degenerates: no_marker, no_object, ambiguous_marker.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d795dec5e48d"
VERSION = "1.2.0"
TASK_ID = "d795dec5e48d"
SUMMARY = "A marker direction slides the colored object rigidly until blocked."

INVARIANTS = [
    "background is 0",
    "there is exactly one marker color from 1 through 4",
    "the moving object uses color 7",
    "the moving object is a single 4-connected component of at least 3 cells",
    "the marker direction has at least one free slide step and eventually hits border/marker/blocker",
]

PALETTE_KINDS = ("default", "dir_1", "dir_2", "dir_3_4")
DEGENERATE_TEXTURES = ("no_marker", "no_object", "ambiguous_marker")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "6..24"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "6..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|dir_1|dir_2|dir_3_4"},
    "marker_dir":     {"type": "int", "default": "rng 1..4", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "corner_marker",
                       "valid": "corner_marker"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "object_kind":    {"type": "str", "default": "L_3cell", "valid": "L_3cell"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|dir_1|dir_2|dir_3_4|no_marker|no_object|ambiguous_marker"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 12, 13)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 8, 13)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    marker = rng.choice([1, 2, 3, 4])
    marker_pos = {1: (h - 1, w - 1), 2: (0, 0), 3: (0, w - 1), 4: (h - 1, 0)}[marker]
    g[marker_pos[0]][marker_pos[1]] = marker
    r = rng.randint(2, h - 4)
    c = rng.randint(2, w - 4)
    for dr, dc in [(0, 0), (0, 1), (1, 0)]:
        g[r + dr][c + dc] = 7
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_marker":
        # 7-object but no direction marker → slide direction undefined
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[3 + dr][3 + dc] = 7
        return g
    if name == "no_object":
        # marker but nothing to slide → rule is no-op
        g[h - 1][w - 1] = 1
        return g
    if name == "ambiguous_marker":
        # two direction markers (e.g. 1 and 2) → which way slides the object?
        g[h - 1][w - 1] = 1
        g[0][0] = 2
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[3 + dr][3 + dc] = 7
        return g
    return g

def _components_of_color(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp = []
            while stack:
                cr, cc = stack.pop()
                comp.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(comp)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the marker-directed slide task."""
    errs: list[str] = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    allowed = {0, 1, 2, 3, 4, 5, 7}
    bad_vals = sorted({v for row in grid for v in row if v not in allowed})
    if bad_vals:
        errs.append(f"unexpected colors: {bad_vals}")
    markers = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if 1 <= grid[r][c] <= 4]
    if len(markers) != 1:
        errs.append(f"expected exactly one 1..4 direction marker, got {len(markers)}")
        return errs
    mr, mc, marker = markers[0]
    expected_corner = {1: (h - 1, w - 1), 2: (0, 0), 3: (0, w - 1), 4: (h - 1, 0)}[marker]
    if (mr, mc) != expected_corner:
        errs.append(f"marker {marker} should sit at canonical corner {expected_corner}, got {(mr, mc)}")
    comps = _components_of_color(grid, 7)
    if len(comps) != 1:
        errs.append(f"expected exactly one color-7 moving component, got {len(comps)}")
        return errs
    cells = comps[0]
    if len(cells) < 3:
        errs.append(f"moving component should have at least 3 cells, got {len(cells)}")
    dr, dc = {1: (-1, 0), 2: (0, 1), 3: (1, 0), 4: (0, -1)}[marker]
    occ = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5 or (r, c) == (mr, mc)}

    def blocked(shifted):
        return any(not (0 <= r < h and 0 <= c < w) or (r, c) in occ for r, c in shifted)

    first_step = [(r + dr, c + dc) for r, c in cells]
    if blocked(first_step):
        errs.append("moving component has no free first slide step in marker direction")
    cur = cells
    steps = 0
    while True:
        nxt = [(r + dr, c + dc) for r, c in cur]
        if blocked(nxt):
            break
        cur = nxt
        steps += 1
        if steps > h + w:
            errs.append("slide simulation did not terminate promptly")
            break
    if steps < 1:
        errs.append("moving component should slide at least one step before settling")
    return errs
