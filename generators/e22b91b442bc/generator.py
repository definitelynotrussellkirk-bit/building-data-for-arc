"""Generator for arc_additional_puzzles_21_set21_bundle:H146 — hole-count packing.

Rule: each connected component is cropped to its bbox; hole-count is the
number of enclosed-zero regions inside the crop. Sort components by
(hole_count asc, area asc, color asc); pack crops left-to-right with one
blank column between them.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: tied_holes, all_solid, single_component.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e22b91b442bc"
VERSION = "2.1.1"  # add executable self_check for distinct 0/1/2-hole packing inputs  # clean (hole-count packing, distinct holes 0/1/2) but small; widen grids for more positions/out_shapes.
TASK_ID = "e22b91b442bc"

SUMMARY = (
    "0-bg grid (h~11-14, w~"
    "14-18) with 3 ISOLATED "
    "COMPONENTS each in a "
    "DISTINCT color from "
    "{1..9}\\{0}, each with "
    "a DISTINCT HOLE COUNT "
    "from {0, 1, 2}: (a) "
    "SOLID rect (0 holes); "
    "(b) HOLLOW RING (1 "
    "hole); (c) DOUBLE-"
    "RING with 2 holes. "
    "Components placed non-"
    "touching with 1-cell "
    "padding. Rule (SORT "
    "BY (HOLE_COUNT ASC, "
    "AREA ASC, COLOR ASC),"
    " PACK CROPS LEFT-TO-"
    "RIGHT WITH 1-COL "
    "GAPS): identify all "
    "4-conn COMPONENTS. "
    "For EACH: CROP to "
    "BBOX, COUNT enclosed-"
    "zero holes (regions "
    "of 0 inside the bbox "
    "that don't touch "
    "the rim). SORT by "
    "(hole_count asc, "
    "area asc, color asc). "
    "HCONCAT the cropped "
    "components left-to-"
    "right with 1-COL "
    "GAPS in sorted order. "
    "Net: components "
    "rearranged by hole "
    "complexity, packed "
    "horizontally."
)

INVARIANTS = [
    "background is 0",
    "exactly 3 isolated 4-connected components",
    "each component has a distinct enclosed-hole count drawn from {0, 1, 2}",
    "component colors are sampled distinctly from {1..9}",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_holes", "all_solid", "single_component")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 11..14", "valid": "10..16"},
    "grid_w":            {"type": "int", "default": "rng 14..18", "valid": "12..20"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "palette_size":      {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "position_bias":     {"type": "str", "default": "components_with_distinct_holes",
                          "valid": "components_with_distinct_holes"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|tied_holes|all_solid|single_component"},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _solid(rng, color):
    sh, sw = rng.choice([(2, 2), (2, 3), (3, 2)])
    return [(r, c, color) for r in range(sh) for c in range(sw)], sh, sw


def _ring(rng, color):
    sh, sw = rng.choice([(3, 3), (3, 4), (4, 3)])
    cells = []
    for r in range(sh):
        for c in range(sw):
            if r in (0, sh - 1) or c in (0, sw - 1):
                cells.append((r, c, color))
    return cells, sh, sw


def _double_ring(rng, color):
    sh, sw = rng.choice([(3, 5), (3, 6)])
    cells = []
    if sw == 5:
        holes = {(1, 1), (1, 3)}
    else:
        holes = {(1, 1), (1, 4)}
    for r in range(sh):
        for c in range(sw):
            is_perim = (r in (0, sh - 1) or c in (0, sw - 1))
            middle = (r == 1 and 0 < c < sw - 1)
            if is_perim or (middle and (r, c) not in holes):
                cells.append((r, c, color))
    return cells, sh, sw


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 14, 15)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16)
        w = ctx.draw_int("grid_w", 17, 20)
    else:
        h = ctx.draw_int("grid_h", 11, 15)
        w = ctx.draw_int("grid_w", 14, 19)
    rng = ctx.draw_rng("layout")

    builders = [_solid, _ring, _double_ring]
    rng.shuffle(builders)
    colors = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 3)

    for outer in range(40):
        g = full_grid(h, w, 0)
        ok = True
        for builder, color in zip(builders, colors):
            cells, sh, sw = builder(rng, color)
            placed = False
            for _ in range(80):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for dr, dc, cc in cells:
                    g[r0 + dr][c0 + dc] = cc
                placed = True
                break
            if not placed:
                ok = False
                break
        if ok:
            return g
    raise ValueError("could not place 3 isolated components in 40 attempts")


def _nonzero_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def _hole_count_for_component(cells):
    cellset = set(cells)
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
    zeros = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
             if (r, c) not in cellset}
    seen = set(); holes = 0
    for start in list(zeros):
        if start in seen:
            continue
        stack = [start]; seen.add(start); touches_rim = False
        while stack:
            r, c = stack.pop()
            if r in (r1, r2) or c in (c1, c2):
                touches_rim = True
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (r + dr, c + dc)
                if nb in zeros and nb not in seen:
                    seen.add(nb); stack.append(nb)
        if not touches_rim:
            holes += 1
    return holes


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the hole-count crop-packing generator."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    if not (11 <= h <= 16 and 14 <= w <= 20):
        errors.append(f"normal grid should be within 11..16 by 14..20, got {h}x{w}")
    comps = _nonzero_components(grid)
    if len(comps) != 3:
        errors.append(f"expected exactly 3 isolated components, found {len(comps)}")
    colors = [color for color, _cells in comps]
    if len(colors) != len(set(colors)):
        errors.append(f"component colors must be distinct, found {colors}")
    holes = [_hole_count_for_component(cells) for _color, cells in comps]
    if sorted(holes) != [0, 1, 2]:
        errors.append(f"component hole counts should be exactly {{0,1,2}}, found {sorted(holes)}")
    # The placer reserves a 1-cell halo.  Check 8-neighbor separation between different components.
    owner = {}
    for idx, (_color, cells) in enumerate(comps):
        for cell in cells:
            owner[cell] = idx
    for idx, (_color, cells) in enumerate(comps):
        for r, c in cells:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nb = (r + dr, c + dc)
                    if nb in owner and owner[nb] != idx:
                        errors.append("components must have at least a 1-cell separating halo")
                        return errors
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 12, 16
    g = full_grid(h, w, 0)
    if name == "tied_holes":
        for c in range(1, 4): g[1][c] = 4; g[3][c] = 4
        g[2][1] = 4; g[2][3] = 4
        for c in range(8, 11): g[1][c] = 6; g[3][c] = 6
        g[2][8] = 6; g[2][10] = 6
        for r, c in [(7, 1), (7, 2), (8, 1), (8, 2)]: g[r][c] = 8
        return g
    if name == "all_solid":
        for r, c in [(2, 1), (2, 2), (3, 1)]: g[r][c] = 4
        for r, c in [(2, 8), (2, 9), (3, 8), (3, 9)]: g[r][c] = 6
        for r, c in [(7, 5), (7, 6), (8, 5)]: g[r][c] = 8
        return g
    if name == "single_component":
        for c in range(2, 5): g[2][c] = 4; g[4][c] = 4
        g[3][2] = 4; g[3][4] = 4
        return g
    return g
