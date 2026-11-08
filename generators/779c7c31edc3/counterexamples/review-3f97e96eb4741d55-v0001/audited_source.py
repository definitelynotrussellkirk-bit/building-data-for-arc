"""Generator for arc_puzzle_bank_seventeenth_21_bundle:easy_118_turn_filled_rectangles_into_frames.

Combinatorial axes (8): grid_h, grid_w, palette_kind, rectangles,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_rects, all_2x2, already_outline.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "779c7c31edc3"
VERSION = "2.0.1"
TASK_ID = "779c7c31edc3"

SUMMARY = (
    "0-bg grid (h~9-12, w~10-13) with 1-3 "
    "SOLID FILLED RECTANGLES of size rh × rw "
    "(rh ∈ {3, 4}, rw ∈ {3, 4, 5}) placed at "
    "non-overlapping non-touching positions "
    "(1-cell guard zone tracked in reserved "
    "set). Each rectangle is painted entirely "
    "in ONE distinct non-0 color drawn from "
    "{1..9}. Each rect has rh ≥ 3 AND rw ≥ 3 "
    "so its bbox has a strict INTERIOR (at "
    "least one cell strictly inside). "
    "Rectangles are SEPARATED by bg-0 (no two "
    "touch). Rule (REDUCE EACH FILLED "
    "RECTANGLE TO ITS BORDER OUTLINE — ERASE "
    "INTERIOR): for EACH SOLID 4-CONNECTED "
    "RECTANGULAR REGION of color C: identify "
    "its bbox (r1, c1, r2, c2). KEEP only the "
    "BORDER CELLS (top row r1, bottom row r2, "
    "left col c1, right col c2 of the bbox) in "
    "color C. CLEAR the INTERIOR cells (rows "
    "r1+1..r2-1, cols c1+1..c2-1) to bg-0. "
    "Rectangle colors and outer dimensions are "
    "preserved; only the interior is hollowed "
    "out. Net: solid blocks become hollow "
    "outlines of the same color and size."
)

# Rivals: 'erase interior of largest only' refuted by ≥1 demo with ≥2 rects
# where both lose their interior. 'recolor frame' refuted by any demo
# (rule keeps the rect's color). 3 demos with varied rect counts suffice.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "each object is a filled rectangle",
    "every rectangle has an interior cell",
    "rectangles are separated by background",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_rects", "all_2x2", "already_outline")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "6..18"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "6..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "rectangles":     {"type": "int", "default": "rng 1..3", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "filled_rects_to_frames",
                       "valid": "filled_rects_to_frames"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg 0, ≥1 connected non-bg object, all objects are solid rectangles of size ≥3×3."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        errs.append("no nonzero cells")
        return errs
    # Find connected components
    visited = [[False] * w for _ in range(h)]
    def bfs(sr, sc):
        color = grid[sr][sc]
        q = [(sr, sc)]; visited[sr][sc] = True; cells = []
        while q:
            r, c = q.pop(); cells.append((r, c))
            for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
                nr, nc = r+dr, c+dc
                if 0<=nr<h and 0<=nc<w and not visited[nr][nc] and grid[nr][nc]==color:
                    visited[nr][nc] = True; q.append((nr, nc))
        return cells
    objects = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 and not visited[r][c]:
                objects.append(bfs(r, c))
    if not objects:
        errs.append("no objects found")
        return errs
    for cells in objects:
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
        bh, bw = r2 - r1 + 1, c2 - c1 + 1
        if len(cells) != bh * bw:
            errs.append(f"object at ({r1},{c1}) is not a solid rectangle ({len(cells)} cells, bbox {bh}×{bw})")
        elif bh < 3 or bw < 3:
            errs.append(f"object at ({r1},{c1}) bbox {bh}×{bw} is too small (need ≥3×3)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
        target = ctx.draw_int("rectangles", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 12, 13)
        target = ctx.draw_int("rectangles", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 13)
        target = ctx.draw_int("rectangles", 1, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    reserved: set[tuple[int, int]] = set()
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], min(target, 9))
    placed = 0
    for _ in range(300):
        if placed >= target:
            break
        rh = rng.randint(3, 4)
        rw = rng.randint(3, 5)
        r0 = rng.randint(0, h - rh)
        c0 = rng.randint(0, w - rw)
        guard = {
            (r, c)
            for r in range(max(0, r0 - 1), min(h, r0 + rh + 1))
            for c in range(max(0, c0 - 1), min(w, c0 + rw + 1))
        }
        if guard & reserved:
            continue
        color = colors[placed % len(colors)]
        for r in range(r0, r0 + rh):
            for c in range(c0, c0 + rw):
                g[r][c] = color
        reserved.update(guard)
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "no_rects":
        # blank → no rectangles to frame
        return g
    if name == "all_2x2":
        # 2x2 rects → border IS the entire rect, no interior to clear
        for r in range(2):
            for c in range(2):
                g[1 + r][1 + c] = 4
                g[5 + r][6 + c] = 6
        return g
    if name == "already_outline":
        # rects are already hollow frames → rule is identity
        for c in range(2, 6): g[2][c] = 3; g[5][c] = 3
        for r in range(2, 6): g[r][2] = 3; g[r][5] = 3
        return g
    return g
