"""Generator for arc_puzzle_bank_twentyfirst21:E146 — keep border-touching objects.

Rule: only objects that touch the grid border are kept; interior-only
objects are erased.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: all_border (every motif touches the border → rule keeps
everything, no erasure), all_interior (no motif touches the border →
rule erases everything, output is empty), single_motif (only one
motif → no candidate contrast).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "124fa5b817e7"
VERSION = "1.2.0"
TASK_ID = "124fa5b817e7"

SUMMARY = "2-4 connected motifs in distinct colors; some touch the grid border, some do not."

INVARIANTS = [
    "background is 0",
    "2-4 motifs in distinct non-zero colors",
    "at least one motif touches the grid border and at least one does not",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_border", "all_interior", "single_motif")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "grid_w":            {"type": "int", "default": "rng 6..9", "valid": "5..12"},
    "n_motifs":          {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "position_bias":     {"type": "str", "default": "border_plus_interior_motifs",
                          "valid": "border_plus_interior_motifs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
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
        h = ctx.draw_int("grid_h", 6, 6)
        w = ctx.draw_int("grid_w", 6, 7)
        n = ctx.draw_int("n_motifs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 9, 9)
        n = ctx.draw_int("n_motifs", 4, 4)
    else:
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 6, 9)
        n = ctx.draw_int("n_motifs", 2, 4)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
        touching_count = (n + 1) // 2
        ok = True
        for i, color in enumerate(colors):
            cells = _build_motif(rng, rng.randint(2, 4))
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            placed = False
            wants_border = i < touching_count
            for _ in range(120):
                if wants_border:
                    if rng.choice([True, False]):
                        r0 = rng.choice([0, h - sh])
                        c0 = rng.randint(0, w - sw)
                    else:
                        r0 = rng.randint(0, h - sh)
                        c0 = rng.choice([0, w - sw])
                else:
                    r0 = rng.randint(1, h - sh - 1) if h - sh > 1 else 0
                    c0 = rng.randint(1, w - sw - 1) if w - sw > 1 else 0
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for r, c in cells:
                    g[r0 + r - min(rs)][c0 + c - min(cs)] = color
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g

    # The random placer can paint itself into a corner on small default grids
    # (for example seed=1610 with the medium/default draw).  Do not let a
    # rare packing miss become a crashing training row; fall back to a small
    # constructive layout that still exercises both halves of the rule: border
    # components are preserved, interior components are erased.
    return _construct_fallback(h, w, n, rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n))


def _paint(g, cells, color):
    for r, c in cells:
        g[r][c] = color


def _construct_fallback(h, w, n, colors):
    h = max(h, 6)
    w = max(w, 6)
    g = full_grid(h, w, 0)
    border = [
        [(0, 1), (0, 2)],
        [(h - 1, w - 2), (h - 1, w - 1)],
    ]
    interior = [
        [(2, 1), (2, 2)],
        [(h - 3, w - 3), (h - 3, w - 2)],
        [(h // 2, w // 2), (h // 2, w // 2 + 1)],
    ]
    touching_count = (n + 1) // 2
    parts = border[:touching_count] + interior[: max(0, n - touching_count)]
    for color, cells in zip(colors, parts):
        _paint(g, cells, color)
    return g


def _components(g):
    h, w = len(g), len(g[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or g[r][c] == 0:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            colors = set()
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                colors.add(g[rr][cc])
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and g[nr][nc] != 0
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((cells, colors))
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    h, w = len(grid), len(grid[0]) if grid else 0
    comps = _components(grid)
    if not (2 <= len(comps) <= 4):
        msgs.append(f"expected 2..4 nonzero components, got {len(comps)}")
    component_colors = []
    border_touching = 0
    interior_only = 0
    for cells, colors in comps:
        if len(colors) != 1:
            msgs.append("component mixes colors; motifs should be single-color")
        else:
            component_colors.append(next(iter(colors)))
        if any(r in (0, h - 1) or c in (0, w - 1) for r, c in cells):
            border_touching += 1
        else:
            interior_only += 1
    if len(component_colors) != len(set(component_colors)):
        msgs.append("component colors are not distinct")
    if border_touching < 1:
        msgs.append("no component touches the border")
    if interior_only < 1:
        msgs.append("no interior-only component to erase")
    return msgs


def _draw_from_degenerate(name, rng):
    h, w = 7, 8
    g = full_grid(h, w, 0)
    if name == "all_border":
        # Every motif touches the border — rule keeps everything;
        # no erasure contrast.
        g[0][1] = 2; g[0][2] = 2
        g[h - 1][5] = 4; g[h - 2][5] = 4
        g[3][0] = 6; g[4][0] = 6
        return g
    if name == "all_interior":
        # No motif touches the border — rule erases everything;
        # output is empty.
        g[2][2] = 4; g[2][3] = 4
        g[4][5] = 6; g[5][5] = 6
        return g
    if name == "single_motif":
        # Only one motif — no candidate contrast.
        g[3][3] = 4; g[3][4] = 4; g[4][3] = 4
        return g
    return g
