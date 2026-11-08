"""Generator for arc_additional_puzzle_bank_volume8:H56 — orange shapes match legend glyphs.

Rule: a gray divider separates legend glyphs (colors 2/3/4) above and
orange-7 scene shapes below. Each scene shape is recolored to the
legend glyph it matches up to rotation.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_legend, no_scene, no_divider.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "fd745e4aa1ad"
VERSION = "2.0.0"  # random distinct glyph shapes + variable scene-object count/positions/rotations (was fixed glyphs + exactly 3)
TASK_ID = "fd745e4aa1ad"
SUMMARY = (
    "0-bg grid split by a full gray (color-5) row: ABOVE it "
    "a LEGEND of three glyphs in colors 2, 3, 4 (each a "
    "random polyomino, the three pairwise NON-rotation-"
    "equivalent so matching is unambiguous); BELOW it a "
    "SCENE of several COLOR-7 objects, each a random "
    "rotation of one of the legend glyphs, placed isolated. "
    "Rule: split on the gray divider; read each legend "
    "color's glyph shape; for each color-7 scene object, "
    "find the legend glyph it matches UP TO ROTATION and "
    "recolor that object to the legend color (legend and "
    "divider preserved)."
)

INVARIANTS = [
    "a full gray(5) divider row separates legend and scene",
    "legend has exactly one object each in colors 2, 3, 4 (pairwise non-rotation-equivalent)",
    "scene objects are color 7, isolated, each a rotation of one legend glyph",
    "each scene object matches exactly one legend shape up to rotation",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_legend", "no_scene", "no_divider")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "derived: legend + divider + scene", "valid": "13..28"},
    "grid_w":         {"type": "int", "default": "derived: fits 3 legend glyphs", "valid": "14..28"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "glyph_size":     {"type": "int", "default": "rng 3..5 cells, bbox <= 4x4", "valid": "3..6"},
    "n_scene":        {"type": "int", "default": "2-3 easy / 3-5 med / 5-8 hard", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "5 (rule-fixed: 2,3,4,5,7)", "valid": "5..5"},
    "position_bias":  {"type": "str", "default": "legend_top_scene_below",
                       "valid": "legend_top_scene_below"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "5..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _norm(cells: list[tuple[int, int]]) -> list[tuple[int, int]]:
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return sorted((r - min_r, c - min_c) for r, c in cells)


def _rot(cells: list[tuple[int, int]], turns: int) -> list[tuple[int, int]]:
    cur = _norm(cells)
    for _ in range(turns % 4):
        height = max(r for r, _ in cur) + 1
        cur = _norm([(c, height - 1 - r) for r, c in cur])
    return cur


def _rotset(cells):
    """frozenset of the 4 normalized rotations (as tuples) — the rotation class."""
    return frozenset(tuple(_rot(cells, t)) for t in range(4))


def _rand_poly(rng, size, maxdim=4):
    """Random connected polyomino of `size` cells with bbox <= maxdim x maxdim."""
    for _ in range(60):
        cells = {(0, 0)}
        frontier = [(0, 0)]
        while len(cells) < size and frontier:
            cr, cc = rng.choice(frontier)
            opts = [(cr + dr, cc + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if (cr + dr, cc + dc) not in cells]
            if not opts:
                frontier.remove((cr, cc))
                continue
            nc = rng.choice(opts)
            cells.add(nc); frontier.append(nc)
        norm = _norm(list(cells))
        if (max(r for r, _ in norm) + 1 <= maxdim
                and max(c for _, c in norm) + 1 <= maxdim and len(norm) == size):
            return norm
    return None


_FALLBACK_GLYPHS = [
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(1, 0), (1, 1), (1, 2), (0, 1)],
    [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],
]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        ns_lo, ns_hi, sh_lo, sh_hi = 2, 3, 4, 6
    elif difficulty == "hard":
        ns_lo, ns_hi, sh_lo, sh_hi = 5, 8, 8, 13
    else:
        ns_lo, ns_hi, sh_lo, sh_hi = 3, 5, 6, 9
    rng = ctx.draw_rng("layout")

    # Three glyphs whose rotation classes are disjoint (pairwise non-rotation-equivalent),
    # so every scene object matches exactly one legend color.
    glyphs, classes = [], []
    for _ in range(400):
        if len(glyphs) == 3:
            break
        gc = _rand_poly(rng, rng.randint(3, 5))
        if gc is None:
            continue
        rs = _rotset(gc)
        if any(rs & e for e in classes):
            continue
        glyphs.append(gc); classes.append(rs)
    if len(glyphs) < 3:
        glyphs = [list(map(tuple, g)) for g in _FALLBACK_GLYPHS]

    glyph_colors = [2, 3, 4]
    gw = [max(c for _, c in g) + 1 for g in glyphs]
    gh_max = max(max(r for r, _ in g) + 1 for g in glyphs)

    # Width fits the 3 legend glyphs side by side (each with a 2-col gap); height =
    # legend band + divider + scene band.
    legend_w = sum(gw) + 2 * (len(glyphs) + 1)
    w = min(28, max(14, legend_w))
    top_h = gh_max + 2
    scene_h = rng.randint(sh_lo, sh_hi)
    h = min(28, top_h + 1 + scene_h)
    g = full_grid(h, w, 0)

    # Legend (colors 2,3,4) at row 1, spaced.
    c = 2
    for gi, glyph in enumerate(glyphs):
        for dr, dc in glyph:
            g[1 + dr][c + dc] = glyph_colors[gi]
        c += gw[gi] + 2

    div = top_h
    for cc in range(w):
        g[div][cc] = 5

    # Scene: color-7 objects, each a random rotation of a random glyph, isolated.
    n_scene = rng.randint(ns_lo, ns_hi)
    placed = 0
    for _ in range(n_scene * 30):
        if placed >= n_scene:
            break
        cells0 = _rot(glyphs[rng.randrange(len(glyphs))], rng.randint(0, 3))
        oh = max(r for r, _ in cells0) + 1
        ow = max(c2 for _, c2 in cells0) + 1
        if oh > h - div - 1 or ow > w:
            continue
        r0 = rng.randint(div + 1, h - oh)
        c0 = rng.randint(0, w - ow)
        cells = [(r0 + dr, c0 + dc) for dr, dc in cells0]
        halo = [(rr, cc) for r, c2 in cells
                for rr in range(r - 1, r + 2) for cc in range(c2 - 1, c2 + 2)]
        if any(0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0 for rr, cc in halo):
            continue
        for r, c2 in cells:
            g[r][c2] = 7
        placed += 1
    if placed == 0:                       # guarantee >=1 scene object (non-trivial)
        glyph = glyphs[0]
        for dr, dc in glyph:
            if div + 1 + dr < h and dc < w:
                g[div + 1 + dr][dc] = 7
    return g


def _draw_from_degenerate(name, rng):
    h, w = 14, 16
    g = full_grid(h, w, 0)
    glyph2 = [(0, 0), (1, 0), (2, 0), (2, 1)]
    glyph3 = [(1, 0), (1, 1), (1, 2), (0, 1)]
    glyph4 = [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)]
    if name == "no_legend":
        # Scene shapes present but no legend glyphs — rule has no
        # color mapping to apply.
        for c in range(w):
            g[4][c] = 5
        paint_at(g, 6, 2, glyph2, 7)
        paint_at(g, 9, 8, glyph4, 7)
        return g
    if name == "no_scene":
        # Legend present but no orange scene shapes — rule has nothing
        # to recolor.
        paint_at(g, 1, 1, glyph2, 2)
        paint_at(g, 1, 5, glyph3, 3)
        paint_at(g, 1, 9, glyph4, 4)
        for c in range(w):
            g[4][c] = 5
        return g
    if name == "no_divider":
        # Legend + scene but no gray divider — legend/scene boundary
        # undefined, rule has no separator to ground its match logic.
        paint_at(g, 1, 1, glyph2, 2)
        paint_at(g, 1, 5, glyph3, 3)
        paint_at(g, 1, 9, glyph4, 4)
        paint_at(g, 6, 2, glyph2, 7)
        return g
    return g


def _components_of_color(grid, color, rows=None):
    h, w = len(grid), len(grid[0]) if grid else 0
    row_ok = (lambda r: True) if rows is None else (lambda r: r in rows)
    seen = set()
    comps = []
    for r in range(h):
        if not row_ok(r):
            continue
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and row_ok(nr)
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    divs = [r for r in range(h) if all(grid[r][c] == 5 for c in range(w))]
    if len(divs) != 1:
        msgs.append("expected exactly one full gray divider row")
        return msgs
    div = divs[0]
    if div <= 0 or div >= h - 1:
        msgs.append("divider should leave both legend and scene bands")
    legend_classes = []
    for color in (2, 3, 4):
        comps = _components_of_color(grid, color, rows=set(range(div)))
        if len(comps) != 1:
            msgs.append(f"legend color {color} should have exactly one object")
            continue
        legend_classes.append(_rotset([(r, c) for r, c in comps[0]]))
    for i in range(len(legend_classes)):
        for j in range(i + 1, len(legend_classes)):
            if legend_classes[i] & legend_classes[j]:
                msgs.append("legend glyphs should be pairwise non-rotation-equivalent")
    scene = _components_of_color(grid, 7, rows=set(range(div + 1, h)))
    if not scene:
        msgs.append("scene should contain at least one color-7 object")
    for cells in scene:
        cls = _rotset([(r, c) for r, c in cells])
        matches = sum(1 for legend_cls in legend_classes if cls & legend_cls)
        if matches != 1:
            msgs.append("each scene object should match exactly one legend glyph up to rotation")
            break
    return msgs
