"""Generator for arc_puzzle_bank_21_set2:S2_H4.

Rule: largest gray template; colored anchors 1..4 stamp rotations.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_template, no_anchors, multiple_templates.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "250a48232c34"
VERSION = "2.1.0"  # realize requested anchors; add structural stamp-fit self_check
TASK_ID = "250a48232c34"
SUMMARY = "Color-coded anchors stamp 0/90/180/270 degree rotations of a gray template."

INVARIANTS = [
    "one gray template object is larger than any other gray object",
    "anchors use colors 1 through 4",
    "each anchor has enough room for its requested rotated template",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_template", "no_anchors", "multiple_templates")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "n_anchors":      {"type": "int", "default": "rng 2..4", "valid": "1..4"},
    "template":       {"type": "int", "default": "rng 0..2", "valid": "0..2"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "position_bias":  {"type": "str", "default": "template_with_anchors",
                       "valid": "template_with_anchors"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_TEMPLATES = [
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 2)],
    [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)],
]


def _components_of_color(grid, color):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    comps = []
    for r in range(h):
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
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def _norm_cells(cells):
    r0 = min(r for r, _c in cells)
    c0 = min(c for _r, c in cells)
    return sorted((r - r0, c - c0) for r, c in cells)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify one gray template and the expected stamp anchors, all in-bounds."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    gray_comps = _components_of_color(grid, 5)
    anchors = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if 1 <= grid[r][c] <= 4]
    if len(gray_comps) != 1:
        errors.append(f"expected exactly one gray(5) template component, found {len(gray_comps)}")
    if difficulty == "easy":
        lo, hi = 1, 2
    elif difficulty == "hard":
        lo, hi = 3, 4
    else:
        lo, hi = 2, 4
    if not (lo <= len(anchors) <= hi):
        errors.append(f"expected {lo}..{hi} anchor cells, found {len(anchors)}")
    if len({v for _r, _c, v in anchors}) != len(anchors):
        errors.append("anchor colors should be unique")
    if len(gray_comps) == 1:
        template = _norm_cells(gray_comps[0])
        if len(template) < 3:
            errors.append("gray template should contain at least three cells")
        for ar, ac, color in anchors:
            rot = _rotate_norm(template, color - 1)
            rh = max(r for r, _c in rot) + 1
            rw = max(c for _r, c in rot) + 1
            if ar + rh > h or ac + rw > w:
                errors.append(f"anchor color {color} at {(ar, ac)} cannot fit its rotated template")
    return errors


def _rotate_norm(cells, turns):
    cur = sorted(cells)
    for _ in range(turns % 4):
        max_r = max(r for r, _c in cur)
        cur = [(c, max_r - r) for r, c in cur]
        r0 = min(r for r, _c in cur)
        c0 = min(c for _r, c in cur)
        cur = sorted((r - r0, c - c0) for r, c in cur)
    return cur


def _paint(g, top, left, cells, color):
    for r, c in cells:
        g[top + r][left + c] = color



_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nb = (r + dr, c + dc)
        if nb not in seen:
            cells.append(nb); seen.add(nb)
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _validate_call(overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    # rule reads h,w: a colour-5 TEMPLATE is stamped (rotated by anchor-1) at each
    # colour-1/2/3/4 anchor. Was fixed 15x15 + fixed template/anchor positions (in=1).
    # Now grid size, a RANDOM template, and anchor positions all vary.
    if difficulty == "easy":
        n_anchors = ctx.draw_int("n_anchors", 1, 2); h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 10, 13)
    elif difficulty == "hard":
        n_anchors = ctx.draw_int("n_anchors", 3, 4); h = ctx.draw_int("grid_h", 16, 22); w = ctx.draw_int("grid_w", 16, 22)
    else:
        n_anchors = ctx.draw_int("n_anchors", 2, 4); h = ctx.draw_int("grid_h", 13, 18); w = ctx.draw_int("grid_w", 13, 18)
    for _layout_attempt in range(80):
        template = _rand_poly(rng, rng.randint(3, 7))
        th = max(r for r, _ in template) + 1
        tw = max(c for _, c in template) + 1
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        tr = rng.randint(0, max(0, h - th))
        tc = rng.randint(0, max(0, w - tw))
        _paint(g, tr, tc, template, 5)
        for r in range(tr - 1, tr + th + 1):
            for c in range(tc - 1, tc + tw + 1):
                if 0 <= r < h and 0 <= c < w:
                    occ[r][c] = True
        colors = [1, 2, 3, 4]
        rng.shuffle(colors)
        placed = 0
        for color in colors:
            if placed >= n_anchors:
                break
            rot = _rotate_norm(template, color - 1)
            rh = max(r for r, _c in rot) + 1
            rw = max(c for _r, c in rot) + 1
            for _ in range(100):
                r = rng.randint(0, h - rh)
                c = rng.randint(0, w - rw)
                # Anchor is the top-left stamp origin; reserve the rotated stamp
                # footprint plus one-cell halo, not a too-large square span.
                if any(occ[rr][cc]
                       for rr in range(max(0, r - 1), min(h, r + rh + 1))
                       for cc in range(max(0, c - 1), min(w, c + rw + 1))):
                    continue
                g[r][c] = color
                for rr in range(max(0, r - 1), min(h, r + rh + 1)):
                    for cc in range(max(0, c - 1), min(w, c + rw + 1)):
                        occ[rr][cc] = True
                placed += 1
                break
        if placed == n_anchors:
            return g
    return _fallback_stamp_layout(n_anchors)


def _fallback_stamp_layout(n_anchors):
    h = w = 18
    g = full_grid(h, w, 0)
    template = _TEMPLATES[1]
    _paint(g, 1, 1, template, 5)
    for color, (r, c) in zip([1, 2, 3, 4], [(1, 12), (12, 1), (12, 12), (8, 8)]):
        if color > n_anchors:
            break
        g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 15, 15
    g = full_grid(h, w, 0)
    if name == "no_template":
        # Anchors but no gray template — rule has no shape to
        # stamp; rule's stamp branch is undefined.
        g[7][1] = 1; g[7][8] = 2; g[11][1] = 3
        return g
    if name == "no_anchors":
        # Template but no anchors — rule has no stamp targets;
        # output equals input.
        _paint(g, 1, 1, _TEMPLATES[0], 5)
        return g
    if name == "multiple_templates":
        # Two equally-sized gray candidates — rule's "largest"
        # tie-break ambiguous; stamp source undefined.
        _paint(g, 1, 1, _TEMPLATES[0], 5)
        _paint(g, 1, 8, _TEMPLATES[0], 5)
        g[7][1] = 1; g[7][8] = 2
        return g
    return g
