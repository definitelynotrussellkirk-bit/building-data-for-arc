"""Generator for arc_puzzle_bank_21_set13_s:S13_H5 — duplicate-feature recolor.

Rule (same-size output): for each object compute the feature-triple
(area, holes, symmetry-class). Every object whose triple is SHARED by at
least one OTHER object is recolored to 8; objects with a unique triple are
left unchanged. So the output recolors all "non-unique-shaped" objects.

To guarantee the transformation is demonstrated (output != input), at least
two motifs are forced to share a shape (hence the same feature-triple) so a
recolor always fires; the rest are random distractors.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "71fd3c801ee1"
VERSION = "2.1.0"  # FIX identity_demo (6/18): SUMMARY falsely claimed a 'vertical gallery pack' but the rule is a SAME-SIZE duplicate-feature recolor (objects sharing (area,holes,sym) -> 8). Tiny random motifs were often all-unique -> no recolor -> output==input. Now force >=2 motifs to share a shape so a recolor always fires. + correct SUMMARY + self_check.
TASK_ID = "71fd3c801ee1"

SUMMARY = (
    "0-bg grid (h~9-11, w~11-13) with 3-4 connected MOTIFS at distinct "
    "non-touching positions, each in a DISTINCT color from {2..9} and size "
    "3-5 cells (1-cell padding). At least TWO motifs share an identical "
    "shape. Rule (DUPLICATE-FEATURE RECOLOR, same-size output): for each "
    "object compute (area, holes, symmetry-class); recolor to 8 every object "
    "whose triple is shared by another object; leave unique-triple objects "
    "unchanged."
)

INVARIANTS = [
    "background is 0",
    "3-4 connected motifs in distinct non-zero colors at distinct positions",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..16"},
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
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 13, 16)
        n = ctx.draw_int("n", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
        n = ctx.draw_int("n", 3, 4)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], n)
        # Pre-build motif shapes; force motifs[0] and motifs[1] to share an
        # identical shape so they share the (area,holes,sym) feature-triple
        # and the rule ALWAYS recolors at least one object (output != input).
        shapes = [_build_motif(rng, rng.randint(3, 5)) for _ in range(n)]
        if n >= 2:
            shapes[1] = [tuple(p) for p in shapes[0]]
        ok = True
        for color, cells in zip(colors, shapes):
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


def _norm_shape(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def self_check(grid, *, difficulty=None, meta=None):
    """>=2 motifs and at least two share an identical normalized shape (so they
    share the (area,holes,sym) feature-triple and the rule recolors -> output
    differs from input). Returns a list of violations (empty == pass)."""
    h, w = len(grid), len(grid[0])
    seen = set(); shapes = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen \
                            and grid[nr][nc] != 0:
                        seen.add((nr, nc)); stack.append((nr, nc))
            shapes.append(_norm_shape(cells))
    msgs = []
    if len(shapes) < 2:
        msgs.append(f"need >=2 motifs, got {len(shapes)}")
        return msgs
    if len({s for s in shapes if shapes.count(s) > 1}) == 0:
        msgs.append("no two motifs share a shape -> rule recolors nothing")
    return msgs


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
