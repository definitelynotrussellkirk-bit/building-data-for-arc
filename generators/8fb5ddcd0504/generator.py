"""Generator for arc_puzzle_bank_21_set6:medium_f03 — multi-motif gallery pack.

Rule: 3-4 small motifs in distinct colors at distinct positions; output
is a vertical pack.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8fb5ddcd0504"
VERSION = "2.2.0"  # tighten normal path to canonical one-motif inputs and avoid solid-rectangle first motifs
TASK_ID = "8fb5ddcd0504"

SUMMARY = (
    "0-bg 5x6/5x7 grid with one small non-rectangular motif "
    "(3-5 cells) in a single non-bg colour. Rule: crop that motif and "
    "build a 2hx2w 4-fold KALEIDOSCOPE — top-left = motif, top-right = "
    "flip-LR, bottom-left = flip-UD, bottom-right = rotate-180."
)

INVARIANTS = [
    "background is 0",
    "exactly one connected single-color motif",
    "the single motif drives the kaleidoscope output",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "5", "valid": "5"},
    "grid_w":         {"type": "int", "default": "rng 6..7", "valid": "6..7"},
    "n":              {"type": "int", "default": "1", "valid": "1"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered_colored_motifs",
                       "valid": "scattered_colored_motifs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_motifs|single_motif|all_same_color"},
}




def _components_4(grid):
    h, w = len(grid), len(grid[0]) if grid else 0
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            colors = set()
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                colors.add(grid[rr][cc])
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] != 0:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((colors, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the motif-gallery input.

    Default instances must contain exactly one single-color, connected,
    non-rectangular motif.  A full-rectangle crop makes the kaleidoscope output
    a solid block, which is a data-quality defect for the normal path.
    """
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    comps = _components_4(grid)
    if len(comps) != 1:
        errs.append(f"expected exactly one connected motif, found {len(comps)}")
    comp_colors = []
    occupied = set()
    for colors, cells in comps:
        occupied.update(cells)
        if len(colors) != 1:
            errs.append(f"component has multiple colors: {sorted(colors)}")
            continue
        color = next(iter(colors))
        comp_colors.append(color)
        if color == 0:
            errs.append("component uses background color 0")
        if not (3 <= len(cells) <= 5):
            errs.append(f"motif color {color} has size {len(cells)} outside 3..5")
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        area = (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)
        if area == len(cells):
            errs.append("motif crop is a solid rectangle -> solid kaleidoscope output")
    if len(comp_colors) != len(set(comp_colors)):
        errs.append(f"motif colors are not distinct: {sorted(comp_colors)}")
    # The generator's _free() leaves a 1-cell halo around each motif; check that
    # no two components touch even diagonally, or scan-order first-motif cases get muddy.
    cell_to_comp = {}
    for i, (_colors, cells) in enumerate(comps):
        for cell in cells:
            cell_to_comp[cell] = i
    for (r, c), i in cell_to_comp.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                j = cell_to_comp.get((r + dr, c + dc))
                if j is not None and j != i:
                    errs.append("motifs touch within the required 1-cell isolation halo")
                    return errs
    return errs

def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # Canonical inputs are one small motif on a 5x6/5x7 canvas; distractor
    # motifs were off-distribution and sometimes made the first motif a solid
    # rectangle, yielding a single-color output block.
    h = ctx.draw_int("grid_h", 5, 5)
    w = ctx.draw_int("grid_w", 6, 7)
    n = ctx.draw_int("n", 1, 1)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], n)
        ok = True
        for color in colors:
            for _shape_try in range(80):
                cells = _build_motif(rng, rng.randint(3, 5))
                rs0 = [r for r, _ in cells]; cs0 = [c for _, c in cells]
                if (max(rs0) - min(rs0) + 1) * (max(cs0) - min(cs0) + 1) > len(cells):
                    break
            else:
                cells = [(0, 0), (1, 0), (1, 1)]
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for r, c in cells:
                    g[r0 + r - min(rs)][c0 + c - min(cs)] = color
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not realize layout")


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # Empty grid — rule has no motifs to gather.
        return g
    if name == "single_motif":
        # Only 1 motif — rule's gallery is trivial.
        for r, c in [(2, 2), (2, 3), (3, 3), (3, 4)]: g[r][c] = 4
        return g
    if name == "all_same_color":
        # All motifs share a color — rule's per-color gather treats
        # them as one big component.
        for r, c in [(1, 1), (1, 2), (2, 2)]: g[r][c] = 4
        for r, c in [(5, 6), (5, 7), (6, 7)]: g[r][c] = 4
        for r, c in [(8, 1), (8, 2), (9, 2)]: g[r][c] = 4
        return g
    return g
