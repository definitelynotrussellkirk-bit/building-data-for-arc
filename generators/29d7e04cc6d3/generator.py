"""Generator for v0_original:hard_06 — two-motif overlay.

Rule: two small motifs in distinct colors at distinct positions are cropped
to their bounding boxes and overlaid at a common origin; overlapping cells
become color 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "29d7e04cc6d3"
VERSION = "2.1.0"  # canonical task has exactly two motifs; avoid ignored extra objects
TASK_ID = "29d7e04cc6d3"

SUMMARY = (
    "0-bg grid (h~7-10, w~7-11) with EXACTLY TWO separated "
    "connected motifs in distinct nonzero colors. Each motif has a "
    "small 2-3 by 2-3 bbox and 3 cells. Rule (TWO-MOTIF "
    "OVERLAY): detect the two connected objects, crop each to its "
    "bbox, align both crops at the top-left of a fresh canvas whose "
    "height/width are the max crop dimensions, copy object colors into "
    "non-overlap cells, and paint overlap cells color 8. Net: two "
    "scattered motifs become one aligned overlay mask. Normal generation "
    "never emits a third motif because the canonical rule consumes only "
    "the first two objects."
)
INVARIANTS = [
    "background is 0",
    "exactly two connected motifs in distinct non-zero colors",
    "the two motifs are separated and each has a small non-empty bbox",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 7..11", "valid": "5..16"},
    "n":              {"type": "int", "default": "2", "valid": "2"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "scattered_colored_motifs",
                       "valid": "scattered_colored_motifs"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
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


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 5, 8)
        n = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 14)
        n = 2
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 11)
        n = 2
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        colors = rng.sample([2, 3, 4, 5, 6, 7, 9], 2)
        ok = True
        for color in colors:
            cells = _build_motif(rng, 3)
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


def _components4(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == 0:
                continue
            color = grid[r][c]
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    """Verify the canonical two-object overlay input contract."""
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("cell value outside ARC palette 0..9")
    comps = _components4(grid)
    if len(comps) != 2:
        errs.append(f"expected exactly two nonzero connected motifs; got {len(comps)}")
        return errs
    colors = [color for color, _ in comps]
    if len(colors) != len(set(colors)):
        errs.append("the two motifs should use distinct colors")
    for color, cells in comps:
        if len(cells) < 3:
            errs.append(f"motif color {color} is too small ({len(cells)} cells)")
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        if max(rs) - min(rs) + 1 > 3 or max(cs) - min(cs) + 1 > 3:
            errs.append(f"motif color {color} bbox should stay small (<=3x3)")
    return errs

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
