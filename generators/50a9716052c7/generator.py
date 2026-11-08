"""Generator for 5b:m33 — extract bisymmetric component.

Rule: among the connected components, exactly one is BOTH horizontally and
vertically mirror-symmetric. Output is that component cropped to its bbox.

The old generator drew the symmetric component from a small fixed `_SYMMETRIC`
bank (distinct=40, 28% dup). Now: a RANDOM H+V-symmetric shape (built by
mirroring a quadrant into all four quadrants) of varied size, plus 1-2 verified
NON-symmetric distractors so the bisymmetric one is unique.

Combinatorial axes: the bisymmetric shape (size + pattern -> output dims), the
distractors, colors, positions, grid size.
Degenerates: no_symmetric, all_symmetric, single_component.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "50a9716052c7"
VERSION = "2.0.2"  # distinct=40/dup28%: rule extracts the unique H+V-symmetric component. Old gen used a fixed _SYMMETRIC bank. Now random bisymmetric shapes (mirror a quadrant) of varied size -> output shape + dims vary.
TASK_ID = "50a9716052c7"
SUMMARY = (
    "0-bg grid (size varies) with ONE BISYMMETRIC component (a random shape "
    "that is both horizontally and vertically mirror-symmetric, built by "
    "mirroring a random quadrant into all four quadrants, varied size) plus 1-2 "
    "verified NON-symmetric distractor shapes, all in distinct colors, placed "
    "apart. Rule: find the unique component symmetric under both H and V mirror "
    "and output it cropped to its bbox."
)

INVARIANTS = [
    "background is 0",
    "exactly one component is both H- and V-mirror symmetric",
    "every other component is non-bisymmetric",
    "components are separated (distinct connected components)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_symmetric", "all_symmetric", "single_component")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "9..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "11..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_distractors":  {"type": "int", "default": "rng 1..2", "valid": "1..2"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "varies", "valid": "2..3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _norm(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r0, c0 = min(rs), min(cs)
    return [(r - r0, c - c0) for (r, c) in cells]


def _connected(cells):
    s = set(cells)
    seen = {next(iter(s))}
    stack = [next(iter(s))]
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            p = (r + dr, c + dc)
            if p in s and p not in seen:
                seen.add(p)
                stack.append(p)
    return len(seen) == len(s)


def _is_bisym(cells):
    s = set(_norm(cells))
    maxr = max(r for r, _ in s)
    maxc = max(c for _, c in s)
    h = all((maxr - r, c) in s for (r, c) in s)
    v = all((r, maxc - c) in s for (r, c) in s)
    return h and v


def _rand_bisym(rng):
    for _ in range(80):
        qh = rng.randint(1, 3)
        qw = rng.randint(1, 3)
        center_r = rng.random() < 0.5
        center_c = rng.random() < 0.5
        H = 2 * qh - (1 if center_r else 0)
        W = 2 * qw - (1 if center_c else 0)
        quad = {(0, 0)}
        for r in range(qh):
            for c in range(qw):
                if rng.random() < 0.6:
                    quad.add((r, c))
        full = set()
        for (r, c) in quad:
            for rr in (r, H - 1 - r):
                for cc in (c, W - 1 - c):
                    full.add((rr, cc))
        cells = _norm(full)
        bbox_area = (max(r for r, _ in cells) + 1) * (max(c for _, c in cells) + 1)
        if len(cells) >= 3 and len(cells) < bbox_area and _connected(cells) and _is_bisym(cells):
            return cells
    return [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]   # plus (bisym)


def _rand_asym(rng):
    for _ in range(60):
        mh = rng.randint(2, 4)
        mw = rng.randint(2, 4)
        cells = {(rng.randint(0, mh - 1), rng.randint(0, mw - 1))}
        n = rng.randint(3, 6)
        guard = 0
        while len(cells) < n and guard < 100:
            guard += 1
            r, c = rng.choice(tuple(cells))
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nr, nc = r + dr, c + dc
            if 0 <= nr < mh and 0 <= nc < mw:
                cells.add((nr, nc))
        norm = _norm(cells)
        if len(norm) >= 3 and not _is_bisym(norm):
            return norm
    return [(0, 0), (0, 1), (1, 0)]   # L-tromino (not bisym)


def _free(g, top, left, cells):
    h, w = len(g), len(g[0])
    for dr, dc in cells:
        rr, cc = top + dr, left + dc
        if not (0 <= rr < h and 0 <= cc < w):
            return False
        for ddr in (-1, 0, 1):
            for ddc in (-1, 0, 1):
                nr, nc = rr + ddr, cc + ddc
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
                    return False
    return True


def _place(g, rng, cells, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in cells) + 1
    sw = max(c for _, c in cells) + 1
    for _ in range(120):
        top = rng.randint(0, h - sh)
        left = rng.randint(0, w - sw)
        if _free(g, top, left, cells):
            for dr, dc in cells:
                g[top + dr][left + dc] = color
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10); w = ctx.draw_int("grid_w", 11, 12); nd = 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 14, 18); nd = 2
    else:
        h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 12, 15); nd = rng.randint(1, 2)

    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 1 + nd)
    for _layout in range(100):
        g = full_grid(h, w, 0)
        if not _place(g, rng, _rand_bisym(rng), palette[0]):
            continue
        ok = True
        for ac in palette[1:]:
            if not _place(g, rng, _rand_asym(rng), ac):
                ok = False
                break
        if ok:
            return g

    # Last-resort hand layout for very tight easy canvases.
    g = full_grid(h, w, 0)
    plus = [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]
    ell = [(0, 0), (0, 1), (1, 0)]
    for dr, dc in plus:
        g[1 + dr][1 + dc] = palette[0]
    for dr, dc in ell:
        g[h - 3 + dr][w - 3 + dc] = palette[1]
    if nd == 2:
        zig = [(0, 1), (1, 0), (1, 1), (2, 0)]
        for dr, dc in zig:
            g[1 + dr][w - 4 + dc] = palette[2]
    return g


def _draw_from_degenerate(name, rng):
    rng = rng or __import__("random").Random(0)
    g = full_grid(10, 12, 0)
    plus = [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]
    el = [(0, 0), (0, 1), (1, 0)]
    if name == "no_symmetric":
        _place(g, rng, el, 2); _place(g, rng, el, 3)
        return g
    if name == "all_symmetric":
        _place(g, rng, plus, 2); _place(g, rng, plus, 3)
        return g
    if name == "single_component":
        _place(g, rng, plus, 4)
        return g
    return g


def _selfcheck_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == 0:
                continue
            color = grid[r][c]
            stack = [(r, c)]; seen.add((r, c)); comp = []
            while stack:
                rr, cc = stack.pop(); comp.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(comp)
    return comps


def _selfcheck_bisym(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    normed = {(r - mr, c - mc) for r, c in cells}
    maxr = max(r for r, _ in normed); maxc = max(c for _, c in normed)
    return (all((maxr - r, c) in normed for r, c in normed) and
            all((r, maxc - c) in normed for r, c in normed))


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    comps = _selfcheck_components(grid)
    if len(comps) < 2:
        errors.append(f"expected symmetric component plus distractor(s), found {len(comps)} components")
    bis = [comp for comp in comps if _selfcheck_bisym(comp)]
    if len(bis) != 1:
        errors.append(f"expected exactly one H+V-symmetric component, found {len(bis)}")
    else:
        comp = bis[0]
        mr = min(r for r, _ in comp); mc = min(c for _, c in comp)
        normed = {(r - mr, c - mc) for r, c in comp}
        bbox_area = (max(r for r, _ in normed) + 1) * (max(c for _, c in normed) + 1)
        if len(normed) == bbox_area and bbox_area >= 9:
            errors.append("bisymmetric target should not be a solid rectangle; it hides the shape-extraction rule")
    return errors

