"""Generator for arc_additional_puzzles_21_set21_bundle:H144 — path overlap.

Rule: for every color present (each appearing exactly twice), draw a fixed
horizontal-first L-path between the two terminals. Cells used by 2+ paths
become color 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, n_pairs, texture.
Degenerates: no_pairs, single_endpoint, no_overlap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "22b4e6220898"
VERSION = "2.1.0"
TASK_ID = "22b4e6220898"

SUMMARY = (
    "0-bg grid (h~8-12, w~"
    "9-14) with 2-4 PAIRS "
    "of ENDPOINT CELLS, "
    "each pair in a DISTINCT "
    "color from {1..9}\\{0, "
    "8}. Each pair: two "
    "cells at random "
    "positions with row "
    "delta ≥ 2 AND col "
    "delta ≥ 2 (forces non-"
    "trivial L-paths). "
    "Endpoints don't reuse "
    "cells across pairs. "
    "Rule (DRAW HORIZONTAL-"
    "FIRST L-PATH PER PAIR, "
    "MARK OVERLAPS WITH 8): "
    "For EACH ENDPOINT "
    "PAIR (ar, ac), (br, "
    "bc): DRAW an L-PATH "
    "horizontal first then "
    "vertical (or task-"
    "specific) — paint "
    "every cell along the "
    "path in the pair's "
    "color. After drawing "
    "all paths: for EACH "
    "cell visited by ≥2 "
    "paths, REPAINT in "
    "COLOR-8 (cyan). Net: "
    "L-routed paths between "
    "each endpoint pair; "
    "path intersections "
    "become cyan."
)

# Rivals: 'straight-line connect' refuted by ≥1 demo where endpoints
# aren't aligned and the L-bend is visible. 'use last-input color for
# overlap' refuted by any demo (overlap is always 8). 'fill all bg'
# refuted by ≥1 demo where bg cells off-path stay 0. 'connect only
# nearest pair' refuted by ≥1 demo with ≥3 pairs all routed.
# 4 demos with varied pair counts + at least one non-overlap and one
# multi-overlap case.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "2-3 distinct non-{0, 8} colors, each appearing exactly twice as endpoints",
    "endpoints are not 4-adjacent and have non-trivial L-paths between them",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "single_endpoint", "no_overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..12"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pairs":        {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "= n_pairs", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "scattered_l_route_pairs",
                       "valid": "scattered_l_route_pairs"},
    "n_distinct_colors": {"type": "int", "default": "= n_pairs", "valid": "2..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 10)
        n_pairs = ctx.draw_int("n_pairs", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 11, 14)
        n_pairs = ctx.draw_int("n_pairs", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 12)
        n_pairs = ctx.draw_int("n_pairs", 2, 4)
    rng = ctx.draw_rng("layout")
    # Palette includes color 1 (was missing in v1.1.0); excludes 0 (bg)
    # and 8 (reserved for path-overlap output).
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], n_pairs)

    for outer in range(60):
        g = full_grid(h, w, 0)
        used = set()

        # Seed the first two pairs with a guaranteed overlap.  Pair 0 has a
        # horizontal-first path across row rt; pair 1 has a vertical leg through
        # that row at c_mid.  Their shared cell is an interior path cell, not an
        # endpoint, so the cyan-overlap branch is always taught.
        rt = rng.randint(2, max(2, h - 4))
        bottom = rng.randint(rt + 2, h - 1)
        c_left = rng.randint(0, max(0, w // 3 - 1))
        c_right = rng.randint(max(c_left + 2, (2 * w) // 3), w - 1)
        c_mid = rng.randint(c_left + 1, c_right - 1)
        top2 = rng.randint(0, rt - 1)
        start2_choices = [c for c in range(w) if abs(c - c_mid) >= 2 and c not in (c_left, c_right)]
        rng.shuffle(start2_choices)
        if not start2_choices:
            continue
        p0 = [(rt, c_left), (bottom, c_right)]
        p1 = [(top2, start2_choices[0]), (bottom, c_mid)]
        first = p0 + p1
        if len(set(first)) != 4:
            continue
        for color, pts in zip(palette[:2], (p0, p1)):
            for ar, ac in pts:
                g[ar][ac] = color
                used.add((ar, ac))

        ok = True
        for color in palette[2:]:
            placed = False
            for _ in range(120):
                ar = rng.randint(0, h - 1); ac = rng.randint(0, w - 1)
                br = rng.randint(0, h - 1); bc = rng.randint(0, w - 1)
                if (ar, ac) in used or (br, bc) in used: continue
                if (ar, ac) == (br, bc): continue
                if abs(ar - br) < 2 or abs(ac - bc) < 2: continue
                g[ar][ac] = color
                g[br][bc] = color
                used.add((ar, ac)); used.add((br, bc))
                placed = True
                break
            if not placed:
                ok = False
                break
        if ok:
            return g
    raise ValueError("could not place {0} L-route pairs with an overlap".format(n_pairs))


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # Empty grid — rule has no endpoint pairs to L-route.
        return g
    if name == "single_endpoint":
        # Color appears only once (no second endpoint) — rule's
        # "exactly twice" filter excludes; no path to draw.
        g[2][2] = 3
        return g
    if name == "no_overlap":
        # Two color pairs whose L-paths don't intersect — rule's
        # 8-overlay step has no cells to mark; output has no 8s.
        g[1][1] = 3; g[1][6] = 3
        g[6][1] = 4; g[6][8] = 4
        return g
    return g


def _h_first_path(a, b):
    ar, ac = a
    br, bc = b
    cols = range(ac, bc + 1) if ac <= bc else range(ac, bc - 1, -1)
    cells = [(ar, c) for c in cols]
    rows = range(ar + 1, br + 1) if ar <= br else range(ar - 1, br - 1, -1)
    cells.extend((r, bc) for r in rows)
    return cells


def self_check(grid, *, difficulty=None, meta=None):
    from collections import Counter, defaultdict
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    by_color = defaultdict(list)
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v not in (0, 8):
                by_color[v].append((r, c))
    if len(by_color) < 2:
        msgs.append(f"too few endpoint colors: {len(by_color)}")
    all_path_cells = []
    for color, pts in by_color.items():
        if len(pts) != 2:
            msgs.append(f"color {color} has {len(pts)} endpoints, expected 2")
            continue
        a, b = sorted(pts)
        if abs(a[0] - b[0]) < 2 or abs(a[1] - b[1]) < 2:
            msgs.append(f"color {color} endpoints do not force a nontrivial L path")
        all_path_cells.extend(_h_first_path(a, b))
    overlaps = [p for p, n in Counter(all_path_cells).items() if n > 1]
    if not overlaps:
        msgs.append("no L-path overlap; cyan branch is hidden")
    return msgs
