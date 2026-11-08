"""Generator for arc_puzzle_bank_twelfth_21_bundle:hard_80_select_object_by_holes_and_symmetry_scale2.

Combinatorial axes (8): holes, symmetry, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_header, no_objects, ambiguous_match.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8f49fe4fdfa8"
# 3.2.0: defect-lint all_background_output — the holes=0 combo could be a SOLID
# rectangle, so the selected object's recolored/upscaled crop was a featureless
# block. Zero-hole shapes are now rejected when they fill their bbox.
# (3.1.0: random shapes per combo.)
VERSION = "3.2.0"
TASK_ID = "8f49fe4fdfa8"
SUMMARY = (
    "Fixed 12×13 0-bg grid "
    "with: (a) ROW 0 "
    "HEADER — holes "
    "encoded as "
    "(holes+1) COLOR-1 "
    "cells at cols 0..n; "
    "(b) g[0][4] = 2 if "
    "vertical SYMMETRY "
    "required, else 3; "
    "(c) g[0][6] = "
    "TARGET COLOR. BODY "
    "contains 4 OBJECTS "
    "at FIXED POSITIONS "
    "spanning the 4 (holes"
    ", symmetry) combos "
    "in {(0, 0), (0, 1), "
    "(1, 0), (1, 1)}, "
    "each in a DISTINCT "
    "non-target color "
    "from {2..8}. Output "
    "uniq_out=25 "
    "(intrinsic — fixed "
    "object positions × "
    "4 spec combos × "
    "colors). Rule "
    "(SELECT MATCHING "
    "OBJECT, SCALE 2× + "
    "RECOLOR): READ "
    "HOLES = (count of "
    "1s in row 0 - 1); "
    "SYMMETRY = (g[0][4] "
    "== 2); TARGET_COLOR "
    "= g[0][6]. SELECT "
    "the BODY OBJECT "
    "matching (holes, "
    "symmetry). UPSCALE "
    "2× and RECOLOR to "
    "TARGET_COLOR. EMIT "
    "the result. Net: "
    "header drives "
    "object selection by "
    "(holes, sym); "
    "output is upscaled "
    "in target color."
)

INVARIANTS = [
    "row 0 encodes hole count as count-of-ones minus one",
    "row 0 column 4 encodes whether vertical symmetry is required",
    "row 0 column 6 gives the output color",
    "the body contains candidate objects spanning the hole/symmetry feature combinations",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_header", "no_objects", "ambiguous_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "holes":          {"type": "int", "default": "rng 0..1", "valid": "0..1"},
    "symmetry":       {"type": "int", "default": "rng 0..1", "valid": "0..1"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "5", "valid": "4..6"},
    "position_bias":  {"type": "str", "default": "header_row0_objects_below",
                       "valid": "header_row0_objects_below"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "4..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_OBJECTS = {
    (0, 1): [(0, 1), (1, 1), (2, 1)],
    (0, 0): [(0, 0), (1, 0), (2, 0), (2, 1)],
    (1, 1): [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)],
    (1, 0): [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2)],
}

_POSITIONS = {
    (0, 1): (2, 1),
    (0, 0): (2, 6),
    (1, 1): (7, 1),
    (1, 0): (7, 7),
}


def _paint(g, top, left, cells, color):
    for r, c in cells:
        g[top + r][left + c] = color


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    return _norm(cells)


def _norm(cells):
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return sorted((r - rmin, c - cmin) for r, c in cells)


def _vsym(cells):
    n = _norm(cells); wmax = max(c for _, c in n)
    return n == sorted((r, wmax - c) for r, c in n)


def _hole_count(cells):
    cs = set(_norm(cells))
    h = max(r for r, _ in cs) + 1; w = max(c for _, c in cs) + 1
    bg = {(r, c) for r in range(h) for c in range(w) if (r, c) not in cs}
    outside = set(); stack = [(r, c) for (r, c) in bg if r in (0, h - 1) or c in (0, w - 1)]
    outside.update(stack)
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            n = (r + dr, c + dc)
            if n in bg and n not in outside:
                outside.add(n); stack.append(n)
    enclosed = bg - outside
    regions = 0; vis = set()
    for cell in enclosed:
        if cell in vis: continue
        regions += 1; vis.add(cell); st = [cell]
        while st:
            r, c = st.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                n = (r + dr, c + dc)
                if n in enclosed and n not in vis:
                    vis.add(n); st.append(n)
    return regions


def _make_combo(rng, holes, sym):
    """Random shape with exactly `holes` enclosed holes and v-symmetry == sym."""
    for _ in range(300):
        if holes == 1:
            rh = rng.randint(3, 5); rw = rng.randint(3, 5)
            cells = [(r, c) for r in range(rh) for c in range(rw)
                     if r in (0, rh - 1) or c in (0, rw - 1)]
            if not sym:
                cells = cells + [(-1, 0)]          # bump above a corner breaks lr-sym
            cells = _norm(cells)
        else:
            base = _rand_poly(rng, rng.randint(4, 8))
            if sym:
                wmax = max(c for _, c in base)
                cells = _norm(set(base) | {(r, wmax - c) for r, c in base})
            else:
                cells = base
        bh = max(r for r, _ in cells) + 1
        bw = max(c for _, c in cells) + 1
        # a solid-bbox zero-hole shape upscales to a featureless block
        solid = (holes == 0 and len(set(cells)) == bh * bw and bh * bw >= 4)
        if bh <= 6 and bw <= 6 and not solid \
           and _hole_count(cells) == holes and _vsym(cells) == bool(sym):
            return cells
    return _OBJECTS[(holes, sym)]


def _free(g, r0, c0, sh, sw):
    h, w = len(g), len(g[0])
    if r0 < 1 or c0 < 0 or r0 + sh > h or c0 + sw > w:   # row 0 = header
        return False
    for r in range(max(0, r0 - 1), min(h, r0 + sh + 1)):
        for c in range(max(0, c0 - 1), min(w, c0 + sw + 1)):
            if g[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    holes = ctx.draw_int("holes", 0, 1)
    symmetry = ctx.draw_int("symmetry", 0, 1)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 12, 13); w = ctx.draw_int("grid_w", 13, 14)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 17); w = ctx.draw_int("grid_w", 15, 18)
    else:
        h = ctx.draw_int("grid_h", 12, 15); w = ctx.draw_int("grid_w", 13, 16)
    combos = [(0, 0), (0, 1), (1, 0), (1, 1)]
    colors = rng.sample([2, 3, 4, 5, 6, 7, 8], 4)
    # Target color lives in row 0; color 1 is reserved for the hole-count
    # run.  Reusing 1 there changes the canonical count-of-ones header.
    target_color = rng.choice([c for c in [2, 3, 4, 5, 6, 7, 8, 9] if c not in colors])
    for _outer in range(40):
        g = full_grid(h, w, 0)
        for c in range(holes + 1):
            g[0][c] = 1
        g[0][4] = 2 if symmetry else 3
        g[0][6] = target_color
        ok = True
        for (hh, ss), color in zip(combos, colors):
            shape = _make_combo(rng, hh, ss)
            sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
            placed = False
            for _ in range(80):
                r0 = rng.randint(1, h - sh); c0 = rng.randint(0, w - sw)
                if _free(g, r0, c0, sh, sw):
                    _paint(g, r0, c0, shape, color); placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    return _draw_fixed_valid_layout(holes, symmetry, target_color, colors)


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 13, 0)
    if name == "no_header":
        # Row 0 empty — no spec for which object to select.
        for color, key in zip([2, 3, 4, 5], _OBJECTS):
            top, left = _POSITIONS[key]
            _paint(g, top, left, _OBJECTS[key], color)
        return g
    if name == "no_objects":
        # Header present but body has no candidate objects — nothing to select.
        g[0][0] = 1
        g[0][4] = 2
        g[0][6] = 9
        return g
    if name == "ambiguous_match":
        # All four objects share the same (holes, symmetry) — match is non-unique.
        g[0][0] = 1
        g[0][4] = 2
        g[0][6] = 9
        same = [(0, 1), (1, 1), (2, 1)]
        _paint(g, 2, 1, same, 2)
        _paint(g, 2, 6, same, 3)
        _paint(g, 7, 1, same, 4)
        _paint(g, 7, 7, same, 5)
        return g
    return g


def _draw_fixed_valid_layout(holes, symmetry, target_color, colors):
    g = full_grid(12, 13, 0)
    for c in range(holes + 1):
        g[0][c] = 1
    g[0][4] = 2 if symmetry else 3
    g[0][6] = target_color
    for key, color in zip([(0, 1), (0, 0), (1, 1), (1, 0)], colors):
        top, left = _POSITIONS[key]
        _paint(g, top, left, _OBJECTS[key], color)
    return g


def _components_by_color(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); out = []
    for r in range(1, h):            # row 0 is header, not a body object
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                cr, cc = stack.pop(); cells.append((cr - 1, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if (1 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append((color, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid is empty or ragged"]
    if len(grid[0]) <= 6:
        return ["grid too narrow for header columns 0,4,6"]
    ones = sum(1 for v in grid[0] if v == 1)
    if ones not in (1, 2):
        errs.append(f"header encodes invalid hole count via {ones} color-1 cells")
    if grid[0][4] not in (2, 3):
        errs.append("header column 4 is not symmetry code 2/3")
    if grid[0][6] == 0:
        errs.append("header target color is zero")
    comps = _components_by_color(grid)
    if len(comps) != 4:
        errs.append(f"expected four body objects, found {len(comps)}")
    features = [(_hole_count(cells), _vsym(cells)) for _, cells in comps]
    if set(features) != {(0, False), (0, True), (1, False), (1, True)}:
        errs.append(f"body objects do not span hole/symmetry combos: {sorted(features)}")
    body_colors = [color for color, _ in comps]
    if len(set(body_colors)) != len(body_colors):
        errs.append("body object colors are not distinct")
    if grid[0][6] in body_colors:
        errs.append("target color is reused by a body object")
    return errs
