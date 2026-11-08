"""Generator for c6141b15 — swap a line's endpoints with glyph stamps.

Rule (verified against canonical): on a background field (bg = most common color),
there is ONE line object (the only size>1 8-connected component with exactly two
endpoints) in line-color, and several GLYPH objects in stamp-color (the other
non-bg color). Output: connect every pair of glyph CENTERS with line-color lines
(a network), and stamp the glyph shape (stamp-color) centered at each of the
line's two ENDPOINTS.

This generator places a straight/diagonal line + 2-4 same-shape glyphs on an
orange (7) field, matching the canonical distribution.

Combinatorial axes: grid size, line orientation/length/position, glyph shape,
glyph count/positions, colors.
Degenerates: no_line, no_glyphs, full_grid.
"""
from __future__ import annotations

from collections import Counter, deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e2bc70324918"
VERSION = "3.2.0"  # honor controls, broaden glyph support, and validate full endpoint stamps
TASK_ID = "e2bc70324918"
SUMMARY = (
    "Orange(7) field with ONE line (straight or diagonal, 2 endpoints) in "
    "line-color and 2-4 GLYPHS (all the same shape, including canonical X/I forms) in "
    "stamp-color, all separated. Rule: connect every pair of glyph centers with "
    "line-color lines, and stamp the glyph shape (stamp-color) centered at each "
    "of the line's two endpoints. Net: line endpoints <-> glyph stamps; glyph "
    "centers <-> a line network."
)

INVARIANTS = [
    "background is the most common color (7)",
    "exactly one size>1 line object with two endpoints (line-color)",
    "2-4 glyph objects of one stamp-color, all the same shape, separated",
    "line endpoints sit clear of the border so glyph stamps fit",
]

ORIENTATIONS = ("horizontal", "vertical", "diagonal", "anti-diagonal")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_line", "no_glyphs", "full_grid")
HELPFUL_TEXTURES = ORIENTATIONS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..16", "valid": "9..20"},
    "grid_w":         {"type": "int", "default": "rng 11..16", "valid": "9..20"},
    "line_orientation":{"type": "str", "default": "rng",
                       "valid": "|".join(ORIENTATIONS)},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_glyphs":       {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "glyph_kind":     {"type": "str", "default": "rng",
                       "valid": "single|plus|x|i5|ring|filled3"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "line_plus_glyphs",
                       "valid": "line_plus_glyphs"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for line_orientation",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_BG = 7
_GLYPHS = {
    "single": ((0, 0),),
    "plus": ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)),
    # Exact canonical nontrivial templates retained to defeat fixed-stencil rivals.
    "x": ((-1, -1), (-1, 1), (0, 0), (1, -1), (1, 1)),
    "i5": (
        (-2, -1), (-2, 0), (-2, 1),
        (-1, 0), (0, 0), (1, 0),
        (2, -1), (2, 0), (2, 1),
    ),
    "ring": (
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1), (0, 1),
        (1, -1), (1, 0), (1, 1),
    ),
    "filled3": tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)),
}
_PALETTES = {
    "warm": (2, 3, 4, 8, 9),
    "cool": (1, 5, 6, 8, 9),
    "broad": tuple(c for c in range(1, 10) if c != _BG),
    "primary": (1, 2, 4, 8),
}



def _free(occ, cells, halo=1):
    h, w = len(occ), len(occ[0])
    for r, c in cells:
        if not (0 <= r < h and 0 <= c < w):
            return False
        for dr in range(-halo, halo + 1):
            for dc in range(-halo, halo + 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and occ[nr][nc]:
                    return False
    return True


def _line_cells(orient, r, c, L):
    if orient == "horizontal":
        return [(r, c + i) for i in range(L)]
    if orient == "vertical":
        return [(r + i, c) for i in range(L)]
    if orient == "diagonal":
        return [(r + i, c + i) for i in range(L)]
    return [(r + i, c - i) for i in range(L)]   # anti-diagonal


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                      task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
        return _draw_from_degenerate(overrides["texture"], ctx.draw_rng("layout"))
    for name, expected in (
        ("palette_size", 2),
        ("n_distinct_colors", 2),
        ("position_bias", "line_plus_glyphs"),
    ):
        if name in overrides and overrides[name] != expected:
            raise ValueError(f"{name} override must be {expected!r}")
    texture = overrides.get("texture")
    if texture is not None and texture not in ORIENTATIONS:
        raise ValueError(f"texture override must be one of {HELPFUL_TEXTURES + DEGENERATE_TEXTURES}")
    if texture is not None and "line_orientation" in overrides and overrides["line_orientation"] != texture:
        raise ValueError("texture and line_orientation overrides disagree")
    effective = dict(overrides)
    if texture is not None:
        effective["line_orientation"] = texture

    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=effective)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 12); w = ctx.draw_int("grid_w", 11, 12)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18); w = ctx.draw_int("grid_w", 14, 18)
    else:
        h = ctx.draw_int("grid_h", 11, 16); w = ctx.draw_int("grid_w", 11, 16)

    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    palette = list(_PALETTES[palette_kind])
    line_color, stamp_color = rng.sample(palette, 2)
    gname = ctx.draw_choice("glyph_kind", tuple(_GLYPHS))
    gcells = _GLYPHS[gname]
    radius = max(max(abs(dr), abs(dc)) for dr, dc in gcells)
    orient = ctx.draw_choice("line_orientation", ORIENTATIONS)
    n_glyphs = ctx.draw_int("n_glyphs", 2, 4)

    for _attempt in range(240):
        g = full_grid(h, w, _BG)
        occ = [[False] * w for _ in range(h)]
        margin = radius + 1
        max_length = min(9, h - 2 * margin, w - 2 * margin)
        if max_length < 4:
            continue
        length = rng.randint(4, max_length)
        placed_line = None
        for _ in range(80):
            if orient == "horizontal":
                r = rng.randint(margin, h - 1 - margin)
                c = rng.randint(margin, w - length - margin)
            elif orient == "vertical":
                r = rng.randint(margin, h - length - margin)
                c = rng.randint(margin, w - 1 - margin)
            elif orient == "diagonal":
                r = rng.randint(margin, h - length - margin)
                c = rng.randint(margin, w - length - margin)
            else:
                r = rng.randint(margin, h - length - margin)
                c = rng.randint(length - 1 + margin, w - 1 - margin)
            cells = _line_cells(orient, r, c, length)
            if _free(occ, cells):
                placed_line = cells
                break
        if placed_line is None:
            continue
        for r, c in placed_line:
            g[r][c] = line_color
            occ[r][c] = True

        placed = 0
        for _ in range(320):
            if placed == n_glyphs:
                break
            gr = rng.randint(radius, h - 1 - radius)
            gc = rng.randint(radius, w - 1 - radius)
            cells = [(gr + dr, gc + dc) for dr, dc in gcells]
            if _free(occ, cells):
                for r, c in cells:
                    g[r][c] = stamp_color
                    occ[r][c] = True
                placed += 1
        if placed != n_glyphs:
            continue
        errors = self_check(g, difficulty=difficulty)
        if not errors:
            return g
    raise ValueError("could not realize line-plus-glyph board")



def _draw_from_degenerate(name, rng):
    g = full_grid(13, 13, _BG)
    if name == "no_line":
        for dr, dc in _GLYPHS["plus"]:
            g[5 + dr][5 + dc] = 2
        return g
    if name == "no_glyphs":
        for c in range(2, 7):
            g[6][c] = 1
        return g
    if name == "full_grid":
        for r in range(13):
            for c in range(13):
                g[r][c] = 2
        return g
    return g


def _components8(grid, bg):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == bg:
                continue
            color = grid[r][c]
            q = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if not (dr or dc):
                            continue
                        nr, nc = rr + dr, cc + dc
                        if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                                and grid[nr][nc] == color):
                            seen.add((nr, nc))
                            q.append((nr, nc))
            out.append((color, cells))
    return out


def _norm(cells):
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def _endpoint_count(cells):
    s = set(cells)
    return sum(
        sum((r + dr, c + dc) in s for dr in (-1, 0, 1) for dc in (-1, 0, 1)
            if dr or dc) == 1
        for r, c in cells
    )


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be a non-empty rectangle"]
    h, w = len(grid), len(grid[0])
    counts = Counter(v for row in grid for v in row)
    bg = counts.most_common(1)[0][0]
    if bg != _BG:
        errs.append(f"expected modal background {_BG}, got {bg}")
    comps = _components8(grid, bg)
    colors = {color for color, _ in comps}
    if len(colors) != 2:
        errs.append(f"expected exactly two non-background colors, got {sorted(colors)}")
        return errs
    line_candidates = [(color, cells) for color, cells in comps
                       if len(cells) > 1 and _endpoint_count(cells) == 2]
    if len(line_candidates) != 1:
        errs.append(f"expected exactly one size>1 line component with two endpoints, found {len(line_candidates)}")
        return errs
    line_color, line_cells = line_candidates[0]
    stamp_color = next(c for c in colors if c != line_color)
    stamp_objs = [cells for color, cells in comps if color == stamp_color]
    if not (2 <= len(stamp_objs) <= 4):
        errs.append(f"expected 2-4 glyph objects, found {len(stamp_objs)}")
    shapes = {_norm(cells) for cells in stamp_objs}
    if len(shapes) > 1:
        errs.append(f"glyph objects should all have one normalized shape, got {len(shapes)}")
    if stamp_objs and len(shapes) == 1:
        normalized = next(iter(shapes))
        max_row = max(r for r, _ in normalized)
        max_col = max(c for _, c in normalized)
        center_row = max_row // 2
        center_col = max_col // 2
        line_set = set(line_cells)
        endpoints = [
            (r, c)
            for r, c in line_cells
            if sum(
                (r + dr, c + dc) in line_set
                for dr in (-1, 0, 1)
                for dc in (-1, 0, 1)
                if dr or dc
            ) == 1
        ]
        for endpoint_r, endpoint_c in endpoints:
            translated = [
                (endpoint_r + r - center_row, endpoint_c + c - center_col)
                for r, c in normalized
            ]
            if any(not (0 <= r < h and 0 <= c < w) for r, c in translated):
                errs.append("line endpoint stamp would clip outside the grid")
                break
    return errs
