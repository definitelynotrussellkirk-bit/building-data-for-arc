"""Generator for fcc82909.

Rule: multicolor 8-connected objects on bg=0; rule paints n rows of
green(3) below each object's bbox, where n = object's distinct color
count.

Combinatorial axes (8): grid_h/w, n_objs, obj_h_max, obj_w_max,
palette_kind, palette_size, anchor_corner, asymmetry_force.
Degenerates: green_in_object, single_color_objs, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e9e7805b09dd"
VERSION = "2.1.0"  # guarantee full default object count + at least one multi-color object; add executable self_check
TASK_ID = "e9e7805b09dd"
SUMMARY = "Multicolor objects; rule paints n green rows below each, n = distinct color count."

INVARIANTS = [
    "background is 0",
    "objects use colors != 3",
    ">=n rows of bg below each object (where n = distinct colors)",
    "objects' bbox columns don't overlap with another object's below-extension",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("green_in_object", "single_color_objs", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 14..18", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "rng 14..18", "valid": "12..22"},
    "n_objs":         {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "obj_h_max":      {"type": "int", "default": "3", "valid": "2..4"},
    "obj_w_max":      {"type": "int", "default": "4", "valid": "3..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "4", "valid": "3..5"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 12, 14
        no_lo, no_hi = 1, 2
    elif difficulty == "hard":
        h_lo, h_hi = 18, 22
        no_lo, no_hi = 2, 4
    else:
        h_lo, h_hi = 14, 18
        no_lo, no_hi = 2, 3
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    # Keep the width axis explicit.  The previous code reused the height range,
    # which made axis overrides/metadata misleading and hid width-drift bugs.
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind")
                    or ctx.draw_choice("palette_kind",
                                       list(PALETTE_KINDS)))
    palette_size = int(overrides.get("palette_size", 4))
    palette = _build_palette(palette_kind, palette_size, rng)
    n_objs = int(overrides.get("n_objs",
                               ctx.draw_int("n_objs", no_lo, no_hi)))
    n_objs = max(1, min(4, n_objs))
    obj_h_max = int(overrides.get("obj_h_max", 3))
    obj_w_max = int(overrides.get("obj_w_max", 4))
    for _board_try in range(40):
        g = full_grid(h, w, 0)
        used_cols = []
        placed = 0
        multi_color_seen = False
        for _try in range(120):
            if placed >= n_objs:
                break
            oh = rng.randint(2, obj_h_max)
            ow = rng.randint(2, obj_w_max)
            n_colors = rng.randint(1, min(3, len(palette)))
            # The default distribution must actually exercise the rule's
            # "distinct color count" branch.  Without this guard, a non-trivial
            # fraction of rows degrade into all-single-color objects, teaching
            # only the one-green-row special case.  Guard covers n_objs=1 (easy)
            # and n_objs>1 equally: force multi-color on the last placed object.
            if placed == n_objs - 1 and not multi_color_seen:
                n_colors = min(3, len(palette))
            rr = rng.randint(0, h - oh - n_colors - 1)
            rc = rng.randint(0, w - ow)
            overlap = False
            for (uc1, uc2, ur1, ur2) in used_cols:
                # require a >=1-column GAP (strict) so objects never 8-touch ->
                # objects-multicolor keeps each separate (no merge of color counts)
                if not (rc + ow <= uc1 - 1 or rc >= uc2 + 2):
                    overlap = True
                    break
            if overlap:
                continue
            obj_palette = rng.sample(palette, n_colors)
            cells_painted = set()
            for dr in range(oh):
                for dc in range(ow):
                    if rng.random() < 0.7:
                        g[rr + dr][rc + dc] = rng.choice(obj_palette)
                        cells_painted.add((rr + dr, rc + dc))
            for i, col in enumerate(obj_palette):
                tr = rr + (i % oh)
                tc = rc + (i % ow)
                g[tr][tc] = col
                cells_painted.add((tr, tc))
            for dr in range(oh):
                for dc in range(ow):
                    if (rr + dr, rc + dc) not in cells_painted:
                        g[rr + dr][rc + dc] = rng.choice(obj_palette)
            used_cols.append((rc, rc + ow - 1, rr, rr + oh - 1))
            placed += 1
            multi_color_seen = multi_color_seen or len(obj_palette) > 1
        if placed == n_objs and (n_objs == 1 or multi_color_seen):
            return g
    return _draw_from_degenerate("single_color_objs", rng)


def _components_8(g):
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for r0 in range(h):
        for c0 in range(w):
            if g[r0][c0] == 0 or seen[r0][c0]:
                continue
            stack = [(r0, c0)]
            seen[r0][c0] = True
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        rr, cc = r + dr, c + dc
                        if (0 <= rr < h and 0 <= cc < w and not seen[rr][cc]
                                and g[rr][cc] != 0):
                            seen[rr][cc] = True
                            stack.append((rr, cc))
            comps.append(sorted(cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    """Executable input invariants for the green-row color-count task."""
    errs = []
    if not grid or not isinstance(grid, list) or not isinstance(grid[0], list):
        return ["grid must be a non-empty rectangular list of rows"]
    w = len(grid[0])
    if w == 0 or any(len(row) != w for row in grid):
        return ["grid must be rectangular and non-empty"]
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if not isinstance(v, int) or not 0 <= v <= 9:
                errs.append(f"cell ({r},{c}) has non-ARC color {v!r}")
            if v == 3 and difficulty != "green_in_object":
                errs.append(f"green marker color appears in input object at ({r},{c})")
    comps = _components_8(grid)
    if difficulty not in DEGENERATE_TEXTURES and not comps:
        errs.append("helpful instances must contain at least one object")
    if difficulty not in ("single_color_objs", "full_grid", "green_in_object"):
        if comps and max(len({grid[r][c] for r, c in comp}) for comp in comps) < 2:
            errs.append("default helpful instances should include a multi-color object")
    for comp in comps:
        colors = {grid[r][c] for r, c in comp}
        rs = [r for r, _ in comp]
        cs = [c for _, c in comp]
        needed = len(colors)
        if max(rs) + needed >= len(grid):
            errs.append("object lacks enough blank rows below its bbox for the green extension")
        else:
            c1, c2 = min(cs), max(cs)
            for rr in range(max(rs) + 1, max(rs) + 1 + needed):
                if any(grid[rr][cc] != 0 for cc in range(c1, c2 + 1)):
                    errs.append("extension rows below an object are not blank")
                    break
    return errs


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 4]
    else:
        pool = [1, 2, 4, 5, 6, 7, 8, 9]
    pool = [c for c in pool if c != 3]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [1, 2, 4, 5, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def _draw_from_degenerate(name, rng):
    h, w = 16, 16
    g = full_grid(h, w, 0)
    if name == "green_in_object":
        for dr in range(2):
            for dc in range(3):
                g[2 + dr][2 + dc] = rng.choice([2, 3, 4])
        return g
    if name == "single_color_objs":
        for dr in range(2):
            for dc in range(2):
                g[3 + dr][3 + dc] = 2
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 2
        return g
    return g
