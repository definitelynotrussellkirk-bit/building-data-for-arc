"""Generator for arc_puzzle_bank_21_set16_s:S16_H3 — extremal-cells diamond.

Rule: ignore motif shapes; find the four extremal non-zero cells (N/S/W/E),
take CENTER = (mid of N/S rows, mid of W/E cols) and RADIUS = Manhattan dist
N->CENTER, and paint a cyan(8) Manhattan diamond of that center/radius.

Combinatorial axes (8): grid_h, grid_w, n, palette_kind, palette_size,
position_bias, n_distinct_colors, density.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bbaef38af096"
# 2.1.0: fixed the stale "vertical pack" header docstring (the rule draws an
# extremal-cells Manhattan diamond). Widened grid/motif-count ranges so the
# diamond center/radius (driven by extremal cell spread) varies more.
VERSION = "2.1.2"  # strengthen motif self_check
TASK_ID = "bbaef38af096"

SUMMARY = (
    "0-bg grid (h~9-11, w~11-13) with 3-4 SMALL MOTIFS "
    "(connected polyominoes of 3-5 cells each) "
    "scattered at distinct positions, each in a distinct "
    "non-bg color, with 4-adjacency isolation between "
    "motifs. Rule: ignore motif identity/shape and "
    "INSTEAD find the four EXTREMAL non-zero cells: "
    "NORTH (lowest row), SOUTH (highest row), WEST "
    "(leftmost col), EAST (rightmost col). Compute "
    "CENTER (cr, cc) = (midpoint of north/south rows, "
    "midpoint of west/east cols), and RADIUS = Manhattan "
    "distance from NORTH to CENTER. PAINT a blank "
    "canvas of the same dims, filling every cell whose "
    "Manhattan distance to (cr, cc) is ≤ RADIUS with "
    "color 8 (cyan). Net: the scattered colored motifs "
    "are replaced by a single cyan DIAMOND whose center "
    "and size are derived from the motifs' bounding "
    "extents."
)

INVARIANTS = [
    "background is 0",
    "2-5 connected motifs in distinct non-zero colors at distinct positions",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..18"},
    "n":              {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered_colored_motifs",
                       "valid": "scattered_colored_motifs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


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


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the scattered motif precondition: 2-5 distinct nonzero colors,
    each forming exactly one connected 3-5 cell motif."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if not (2 <= len(colors) <= 5):
        errs.append(f"expected 2-5 distinct motif colors, got {len(colors)}")
    for color in colors:
        cells = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
        seen = set(); comps = []
        for cell in list(cells):
            if cell in seen:
                continue
            stack = [cell]; seen.add(cell); comp = []
            while stack:
                r, c = stack.pop(); comp.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (nr, nc) in cells and (nr, nc) not in seen:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(comp)
        if len(comps) != 1:
            errs.append(f"color {color} should form one connected motif, found {len(comps)}")
        elif not (3 <= len(comps[0]) <= 5):
            errs.append(f"color {color} motif size should be 3-5, got {len(comps[0])}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 11, 11)
        n = ctx.draw_int("n", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16)
        w = ctx.draw_int("grid_w", 14, 18)
        n = ctx.draw_int("n", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 11, 15)
        n = ctx.draw_int("n", 3, 5)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], n)
        ok = True
        for color in colors:
            cells = _build_motif(rng, rng.randint(3, 5))
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
