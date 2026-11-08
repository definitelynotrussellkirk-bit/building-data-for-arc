"""Generator for arc_puzzle_bank_21_set7:medium_g13 — checker-fill each bbox.

Rule: each blob → fill its bbox with a checker pattern in same color
(cells where (r-r1+c-c1)%2 == 0).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: single_cell_blobs, already_checker, blob_overlap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "e22bef4f5826"
VERSION = "2.2.0"  # add executable checker-blob self_check; clean (checker-fill each blob bbox) but small grids + n_blobs hardcoded 2-3; widen blob count (axis 1-4) and grids.
TASK_ID = "e22bef4f5826"
SUMMARY = (
    "0-bg grid (h ∈ 6-8, w ∈ 7-9) "
    "with: 2-3 NON-OVERLAPPING BLOBS, "
    "each a 2-3 cell irregular blob "
    "built via grow_blob random walk, "
    "each in a DISTINCT color drawn "
    "from {1..9}. Blobs placed with "
    "shared used-set tracking. Each "
    "blob's bbox checker-fill "
    "differs from the input (since "
    "blobs are non-rectangular or "
    "small). Rule (FOR EACH NON-BG "
    "COMPONENT, FILL ITS BBOX WITH "
    "A CHECKER PATTERN IN THE "
    "COMPONENT'S COLOR — CELLS "
    "WHERE (R - R1 + C - C1) % 2 "
    "== 0 GET THE COLOR, OTHERS "
    "STAY 0): For EACH blob with "
    "color c and bbox (r1..r2, "
    "c1..c2): For EVERY (r, c) "
    "in the bbox: IF (r - r1 + c "
    "- c1) % 2 == 0: PAINT "
    "g[r][c] = color; ELSE: "
    "PAINT 0 (overwriting the "
    "blob's interior). Net: each "
    "irregular blob expands to "
    "a checker-filled rectangle "
    "in its color."
)

INVARIANTS = [
    "background is 0",
    "blobs are non-rectangular OR small (so checker-fill differs from input)",
    "blobs don't overlap or 4-touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("single_cell_blobs", "already_checker", "blob_overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "6..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_blobs":        {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spaced_blobs",
                       "valid": "spaced_blobs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|single_cell_blobs|already_checker|blob_overlap"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 7, 9)
        n = ctx.draw_int("n_blobs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 12)
        n = ctx.draw_int("n_blobs", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 11)
        n = ctx.draw_int("n_blobs", 2, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    used: set[tuple[int, int]] = set()
    for color in palette:
        cells = grow_blob(rng, h, w, used, rng.randint(2, 3), max_attempts=80)
        if cells is None:
            continue
        for r, c in cells:
            g[r][c] = color
        used |= cells
    return g


def _components(grid):
    h = len(grid); w = len(grid[0]) if h else 0
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]; seen.add((r, c)); comp = []
            while stack:
                cr, cc = stack.pop(); comp.append((cr, cc))
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append((color, comp))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    comps = _components(grid)
    if not (2 <= len(comps) <= 4):
        errs.append(f"expected 2-4 blobs, got {len(comps)}")
    colors = [color for color, _ in comps]
    if len(colors) != len(set(colors)):
        errs.append("blob colors must be distinct")
    all_cells = {}
    for color, comp in comps:
        if not (2 <= len(comp) <= 3):
            errs.append(f"color {color} blob has {len(comp)} cells, expected 2-3")
        rows = [r for r, _ in comp]; cols = [c for _, c in comp]
        r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
        checker_cells = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                         if (r + c) % 2 == 0}
        if set(comp) == checker_cells:
            errs.append(f"color {color} blob already fills checker cells in its bbox")
        for cell in comp:
            all_cells[cell] = color
    for (r, c), color in all_cells.items():
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            other = all_cells.get((r + dr, c + dc))
            if other is not None and other != color:
                errs.append("distinct blobs 4-touch")
                return errs
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "single_cell_blobs":
        # 1x1 blobs → bbox is single cell, checker fill is trivial (same as input)
        g[1][2] = 4; g[3][5] = 6; g[5][7] = 3
        return g
    if name == "already_checker":
        # blob already has checker pattern in its bbox → rule is identity
        for (r, c) in [(1, 1), (1, 3), (2, 2), (3, 1), (3, 3)]: g[r][c] = 4
        return g
    if name == "blob_overlap":
        # two blobs share cells → "each blob's bbox" is ambiguous in overlap
        for (r, c) in [(1, 1), (1, 2), (2, 2)]: g[r][c] = 4
        for (r, c) in [(2, 2), (2, 3), (3, 3)]: g[r][c] = 6  # overlaps at (2,2)
        return g
    return g
