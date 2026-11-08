"""Generator for arc_puzzle_bank_tenth21:M69.

Rule: above a separator row, each color defines a prototype shape.
Below it, a key color selects one prototype and an 8 marks where to stamp it.

Combinatorial axes (8): grid_h, grid_w, palette_kind, selected_index,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_separator, no_anchor, key_not_in_library.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e3c964448fb7"
VERSION = "3.0.3"  # fail closed instead of returning no_anchor fallback; verify selected stamp fits
TASK_ID = "e3c964448fb7"
SUMMARY = (
    "0-bg grid with one full-width color-9 separator row. Above it is a "
    "library of 3-4 distinct-color prototype polyominoes; below it is one "
    "key cell whose color selects a prototype and one color-8 anchor with "
    "room to stamp that prototype. Grid size, separator row, prototype "
    "shapes/positions, selected key, and anchor position all vary."
)

INVARIANTS = [
    "one full color-9 row separates prototype library and query",
    "prototype colors are unique",
    "the lower section has exactly one non-8 key color and one color-8 anchor",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_separator", "no_anchor", "key_not_in_library")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..14", "valid": "11..16"},
    "grid_w":         {"type": "int", "default": "rng 12..16", "valid": "12..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "selected_index": {"type": "int", "default": "rng 0..n_proto-1", "valid": "0..3"},
    "palette_size":   {"type": "int", "default": "3..4 prototypes", "valid": "3..4"},
    "position_bias":  {"type": "str", "default": "library_separator_query",
                       "valid": "library_separator_query"},
    "n_distinct_colors": {"type": "int", "default": "3..4", "valid": "3..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_SHAPES = [
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 1), (2, 1)],
    [(0, 1), (1, 0), (1, 1), (1, 2)],
]


def _paint(g, top, left, cells, color):
    for r, c in cells:
        g[top + r][left + c] = color


def _poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 12); w = ctx.draw_int("grid_w", 12, 14)
        n_proto = ctx.draw_int("n_proto", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16); w = ctx.draw_int("grid_w", 14, 18)
        n_proto = ctx.draw_int("n_proto", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 12, 16)
        n_proto = ctx.draw_int("n_proto", 3, 4)
    rng = ctx.draw_rng("layout")

    for _attempt in range(60):
        # separator row leaving >=4 rows of library above and >=4 query rows below
        sep = rng.randint(4, h - 5)
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7], n_proto)
        protos = [_poly(rng, rng.randint(3, 5)) for _ in range(n_proto)]

        # A random prototype can be taller than the sampled library band.  The
        # previous code called randint(0, sep - ph) and crashed for those seeds.
        if any((max(r for r, _ in shape) + 1) > sep or
               (max(c for _, c in shape) + 1) > w for shape in protos):
            continue

        g = full_grid(h, w, 0)
        # place prototypes in the library (rows 0..sep-1), non-overlapping (bbox+gap)
        occ = [[False] * w for _ in range(sep)]
        ok = True
        for shape, color in zip(protos, colors):
            ph = max(r for r, _ in shape) + 1; pw = max(c for _, c in shape) + 1
            spot = None
            for _ in range(80):
                r0 = rng.randint(0, sep - ph); c0 = rng.randint(0, w - pw)
                free = all(not occ[r0 + r + a][c0 + c + b]
                           for r, c in shape for a in (-1, 0, 1) for b in (-1, 0, 1)
                           if 0 <= r0 + r + a < sep and 0 <= c0 + c + b < w)
                if free:
                    spot = (r0, c0); break
            if spot is None:
                ok = False; break
            r0, c0 = spot
            _paint(g, r0, c0, shape, color)
            for r, c in shape:
                occ[r0 + r][c0 + c] = True
        if not ok:
            continue

        for c in range(w):
            g[sep][c] = 9

        # selected prototype -> its color is the key; anchor needs room to stamp it
        sel = rng.randint(0, n_proto - 1)
        key = colors[sel]
        sh = max(r for r, _ in protos[sel]) + 1
        sw = max(c for _, c in protos[sel]) + 1
        lo = sep + 1
        # place key + anchor in the query region, anchor with stamp room
        free_lower = [(r, c) for r in range(lo, h) for c in range(w)]
        rng.shuffle(free_lower)
        key_pos = free_lower[0]
        g[key_pos[0]][key_pos[1]] = key
        anchor = None
        for (r, c) in free_lower[1:]:
            if (r, c) == key_pos:
                continue
            if r + sh <= h and c + sw <= w and not (r <= key_pos[0] < r + sh and c <= key_pos[1] < c + sw):
                anchor = (r, c); break
        if anchor is None:
            continue
        g[anchor[0]][anchor[1]] = 8
        return g
    raise ValueError("could not realize library/query board")


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 14, 0)
    colors = [4, 6, 3]
    for i, (shape, color) in enumerate(zip(_SHAPES, colors)):
        _paint(g, 1, 1 + i * 4, shape, color)
    if name == "no_separator":
        # no 9-row → library/query split undefined
        g[8][2] = 4; g[8][7] = 8
        return g
    for c in range(14): g[5][c] = 9
    if name == "no_anchor":
        # key but no 8 anchor → no destination position
        g[8][2] = 4   # only the key, no 8
        return g
    if name == "key_not_in_library":
        # key color not in prototype library → lookup fails
        g[8][2] = 7   # 7 not in colors=[4, 6, 3]
        g[8][7] = 8
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    h, w = len(grid), len(grid[0])
    sep_rows = [r for r in range(h) if all(grid[r][c] == 9 for c in range(w))]
    if len(sep_rows) != 1:
        return [f"expected exactly one full-width separator row, found {sep_rows}"]
    sep = sep_rows[0]
    if sep < 3 or h - sep - 1 < 3:
        errors.append("separator must leave visible library and query regions")
    upper_colors = {grid[r][c] for r in range(sep) for c in range(w) if grid[r][c] not in (0, 9)}
    if len(upper_colors) < 3:
        errors.append(f"expected at least 3 prototype colors, found {len(upper_colors)}")
    lower = [(r, c, grid[r][c]) for r in range(sep + 1, h) for c in range(w) if grid[r][c] != 0]
    anchors = [(r, c) for r, c, v in lower if v == 8]
    keys = [(r, c, v) for r, c, v in lower if v not in (8, 9)]
    if len(anchors) != 1:
        errors.append(f"expected exactly one color-8 anchor, found {len(anchors)}")
    if len(keys) != 1:
        errors.append(f"expected exactly one lower key color, found {len(keys)}")
    elif keys[0][2] not in upper_colors:
        errors.append(f"key color {keys[0][2]} is not present in the prototype library")
    if len(anchors) == 1 and len(keys) == 1 and keys[0][2] in upper_colors:
        key = keys[0][2]
        proto = [(r, c) for r in range(sep) for c in range(w) if grid[r][c] == key]
        r0 = min(r for r, _ in proto)
        c0 = min(c for _, c in proto)
        offs = [(r - r0, c - c0) for r, c in proto]
        ar, ac = anchors[0]
        if any(not (0 <= ar + dr < h and 0 <= ac + dc < w) for dr, dc in offs):
            errors.append("selected prototype would not fit at the color-8 anchor")
        kr, kc, _ = keys[0]
        if any((ar + dr, ac + dc) == (kr, kc) for dr, dc in offs):
            errors.append("selected stamp would overwrite the lower key cell")
    return errors

