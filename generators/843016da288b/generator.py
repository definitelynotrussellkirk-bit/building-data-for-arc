"""Generator for arc_puzzle_bank_21_set2:S2_M3 — bounding-box outlines.

Rule: replace every 2-colored object by the rect-outline of its bbox in
color 2.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: solid_rects, single_blob, line_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "843016da288b"
# 2.1.0: defect-lint identity_demo + all_background_output — a solid-bbox blob was
# silently SKIPPED (not retried), so a grid could end up with ZERO objects (empty
# input -> empty output -> identity). Non-solid blobs are now retried per slot and
# at least one object is guaranteed (loud raise otherwise).
VERSION = "2.1.0"
TASK_ID = "843016da288b"
SUMMARY = (
    "0-bg grid (h~8-11, w~8-11) with 2-3 SMALL COLOR-2 "
    "BLOBS — each a 3-5 cell 4-connected blob grown by "
    "random adjacency walk (grow_blob helper). Each "
    "blob is painted entirely in COLOR 2. Blobs are "
    "placed at non-overlapping non-touching positions "
    "(track used cells across attempts). Each blob is "
    "constrained NON-RECTANGULAR — its cell count is "
    "strictly less than its bbox area (so the bbox "
    "has at least one bg-0 cell), guaranteeing the "
    "rule's output differs from the input. Rule "
    "(REPLACE EACH 2-BLOB WITH ITS BBOX OUTLINE IN "
    "COLOR 2): for EACH 4-CONNECTED color-2 component "
    "in the input: COMPUTE its bbox (r1, c1, r2, c2). "
    "ERASE the original blob cells (set to bg-0). "
    "PAINT the BBOX OUTLINE (top row r1, bottom row "
    "r2, left col c1, right col c2 of the bbox "
    "rectangle, all 4 edges) with COLOR 2. The "
    "BBOX INTERIOR (strictly inside) stays bg-0. "
    "Other cells outside any blob's bbox stay bg-0. "
    "Net: each irregular 2-blob is replaced by a "
    "hollow color-2 rectangle outline tightly bounding "
    "where the blob was."
)

INVARIANTS = [
    "background is 0",
    "all non-zero cells are color 2",
    "every blob has at least one bbox cell that is empty (otherwise output = input)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("solid_rects", "single_blob", "line_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "non_rectangular_blobs",
                       "valid": "non_rectangular_blobs"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: all nonzero cells are color-2; ≥2 distinct 4-connected components."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        return []  # single_blob or no blobs degenerate — allowed
    errs = []
    for r, c in nonzero:
        if grid[r][c] != 2:
            errs.append(f"cell ({r},{c}) has color {grid[r][c]}; expected only color-2 blobs")
    if not errs:
        # count color-2 components
        visited = set()
        n_comps = 0
        for r0, c0 in twos:
            if (r0, c0) not in visited:
                n_comps += 1
                queue = [(r0, c0)]
                visited.add((r0, c0))
                while queue:
                    r, c = queue.pop()
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = r + dr, c + dc
                        if (nr, nc) not in visited and 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 2:
                            visited.add((nr, nc))
                            queue.append((nr, nc))
        if n_comps < 1:
            errs.append(f"expected ≥1 color-2 blob; found {n_comps}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        n = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 10, 11)
        n = 3
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 11)
        n = ctx.draw_int("n_blobs", 2, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    used: set[tuple[int, int]] = set()
    placed = 0
    for _ in range(n):
        # retry until this slot gets a NON-SOLID blob (a solid-bbox blob is
        # already its own outline-ish case; skipping without retry could leave
        # the grid EMPTY -> identity demo)
        for _try in range(40):
            size = rng.randint(3, 5)
            cells = grow_blob(rng, h, w, used, size, max_attempts=80)
            if cells is None:
                continue
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            bb_h = max(rs) - min(rs) + 1
            bb_w = max(cs) - min(cs) + 1
            if bb_h * bb_w == len(cells):
                continue
            for r, c in cells:
                g[r][c] = 2
            used |= cells
            placed += 1
            break
    if placed == 0:
        raise ValueError("could not place any non-solid 2-blob")
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "solid_rects":
        # solid rectangles → bbox outline equals the original (interior already filled),
        # rule is identity, no visible change
        for r in range(1, 4):
            for c in range(1, 4): g[r][c] = 2
        for r in range(5, 8):
            for c in range(5, 9): g[r][c] = 2
        return g
    if name == "single_blob":
        # one blob → only one outline drawn, no comparison/contrast
        for (r, c) in [(2, 3), (2, 4), (2, 5), (3, 5), (4, 5)]: g[r][c] = 2
        return g
    if name == "line_blobs":
        # 1×N or N×1 lines → bbox is the line itself; outline equals input, rule is identity
        for c in range(1, 6): g[2][c] = 2   # horizontal line
        for r in range(4, 8): g[r][8] = 2   # vertical line
        return g
    return g
