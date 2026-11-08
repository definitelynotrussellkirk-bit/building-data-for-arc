"""Generator for arc_puzzle_bank_21_set23_bundle:hard_p03 — adjacency matrix via clear line-of-sight.

Rule: connected components sorted top-left. Output N×N: diagonal = 1, off-diagonal = 8 if two components
have clear row/column line-of-sight through at least one background cell,
else 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: all_far (no pair has clear line-of-sight → output diagonal-only,
hides the off-diagonal "8" branch); all_close (every pair has clear
line-of-sight → output is full off-diagonal 8s, hides far branch);
single_component (rule's N×N output is just a 1×1 diagonal — no
adjacency information visible).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "532a2148b8f4"
VERSION = "2.1.0"
TASK_ID = "532a2148b8f4"

SUMMARY = (
    "0-bg grid (h~9-11, w~12-14) with 3-4 ISOLATED 4-conn "
    "COMPONENTS (1-3 cells each) in distinct non-bg "
    "colors, mixed near/far so some pairs share clear row/column line-of-sight while others do not. Rule: extract "
    "all 4-conn non-bg components, sort by top-left "
    "(r1, c1) ascending. For each pair, scan horizontally/vertically from every cell; if the first non-bg object seen after at least one 0-cell is the other component, they are adjacent. Output is an N×N matrix where N = number of components: diagonal[i][i] = 1 (blue); off-diagonal[i][j] = 8 (cyan) if line-of-sight holds, else 0. Net: a visibility matrix."
)

INVARIANTS = [
    "background is 0",
    "3-4 isolated 4-conn components in distinct colors",
    "some components share clear line-of-sight, others do not",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_far", "all_close", "single_component")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..20"},
    "grid_w":         {"type": "int", "default": "rng 12..14", "valid": "10..22"},
    "n_components":   {"type": "int", "default": "rng 3..4", "valid": "3..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "position_bias":  {"type": "str", "default": "mixed_visible_hidden",
                       "valid": "mixed_visible_hidden"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _spaced(rng, size, k):
    """k positions in [0, size) that are pairwise >= 2 apart."""
    for _ in range(50):
        pts = sorted(rng.sample(range(size), k))
        if all(pts[i + 1] - pts[i] >= 2 for i in range(len(pts) - 1)):
            return pts
    step = max(2, size // max(1, k))
    return [min(size - 1, i * step) for i in range(k)]


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _components(g):
    h, w = len(g), len(g[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if g[r][c] == 0 or (r, c) in seen:
                continue
            color = g[r][c]
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nb = (rr + dr, cc + dc)
                    if (0 <= nb[0] < h and 0 <= nb[1] < w and nb not in seen
                            and g[nb[0]][nb[1]] == color):
                        seen.add(nb); stack.append(nb)
            comps.append({"color": color, "cells": cells})
    return comps


def _visible(g, a, b):
    h, w = len(g), len(g[0])
    b_cells = set(b["cells"])
    for r, c in a["cells"]:
        for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            rr, cc = r + dr, c + dc
            seen_zero = False
            while 0 <= rr < h and 0 <= cc < w:
                if g[rr][cc] == 0:
                    seen_zero = True
                    rr += dr; cc += dc
                    continue
                if seen_zero and (rr, cc) in b_cells:
                    return True
                break
    return False


def _visibility_mix(g):
    comps = _components(g)
    vis = hidden = 0
    for i in range(len(comps)):
        for j in range(i + 1, len(comps)):
            if _visible(g, comps[i], comps[j]) or _visible(g, comps[j], comps[i]):
                vis += 1
            else:
                hidden += 1
    return comps, vis, hidden


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the intended mixed line-of-sight adjacency episode."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    comps, visible_pairs, hidden_pairs = _visibility_mix(grid)
    if not (3 <= len(comps) <= 6):
        errors.append(f"expected 3..6 components, found {len(comps)}")
    colors = [c["color"] for c in comps]
    if len(colors) != len(set(colors)):
        errors.append("component colors are not distinct")
    if visible_pairs == 0:
        errors.append("no component pair has clear line-of-sight; off-diagonal 8 branch hidden")
    if hidden_pairs == 0 and len(comps) > 1:
        errors.append("every component pair has line-of-sight; off-diagonal 0 branch hidden")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # output is the NxN line-of-sight adjacency matrix (N = #components); widen
    # N -> output size + adjacency patterns scale (was 3-5, out=2, distinct=31).
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
        n = ctx.draw_int("n_components", 3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 20)
        w = ctx.draw_int("grid_w", 16, 22)
        n = ctx.draw_int("n_components", 5, 6)
    else:
        h = ctx.draw_int("grid_h", 11, 15)
        w = ctx.draw_int("grid_w", 13, 17)
        n = ctx.draw_int("n_components", 4, 5)
    rng = ctx.draw_rng("layout")
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], n)

    # Widened N (3-6) + random scattered small components.  Seed the layout with
    # a likely clear row line-of-sight pair for the off-diagonal 8 branch, then
    # reject layouts unless both the 8 and 0 off-diagonal branches are present.
    shapes = [
        [(0, 0), (0, 1)],
        [(0, 0), (1, 0)],
        [(0, 0), (0, 1), (1, 0)],
        [(0, 0), (0, 1), (1, 1)],
        [(0, 0)],
    ]
    for _outer in range(80):
        g = full_grid(h, w, 0)
        row = rng.randint(1, h - 2)
        c1 = rng.randint(1, max(1, w // 3))
        c2 = rng.randint(min(w - 2, c1 + 3), w - 2)
        if c2 - c1 < 3:
            c1, c2 = 1, min(w - 2, 5)
        g[row][c1] = palette[0]
        g[row][c2] = palette[1]
        ok = True
        for color in palette[2:]:
            shape = rng.choice(shapes)
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
                    continue
                for dr, dc in shape:
                    g[r0 + dr][c0 + dc] = color
                placed = True
                break
            if not placed:
                ok = False
                break
        if ok:
            _comps, vis, hidden = _visibility_mix(g)
            if vis > 0 and hidden > 0:
                return g
    raise ValueError("could not place {0} mixed-visibility components".format(n))


def _draw_from_degenerate(name, rng):
    h, w = 10, 14
    g = full_grid(h, w, 0)
    if name == "all_far":
        # Three components arranged with no clear row/column visibility;
        # output's off-diagonal is all 0,
        # hiding the "8" branch.
        for cells, color, base in [([(0, 0), (0, 1)], 1, (1, 1)),
                                   ([(0, 0), (0, 1)], 2, (5, 8)),
                                   ([(0, 0), (1, 0)], 3, (8, 2))]:
            for dr, dc in cells:
                g[base[0] + dr][base[1] + dc] = color
        return g
    if name == "all_close":
        # Three components placed on one row so every pair has clear
        # line-of-sight → output is N×N with 8 everywhere off-diagonal,
        # hiding the "no overlap → 0" branch.
        for cells, color, base in [([(0, 0)], 1, (3, 3)),
                                   ([(0, 0)], 2, (3, 5)),
                                   ([(0, 0)], 3, (3, 7))]:
            for dr, dc in cells:
                g[base[0] + dr][base[1] + dc] = color
        return g
    if name == "single_component":
        # Only one component → rule's N×N output is 1×1 (just the
        # diagonal); no adjacency information to convey.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[3 + dr][6 + dc] = 4
        return g
    return g
