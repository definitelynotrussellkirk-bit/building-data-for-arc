"""Generator for puzzle eb3fb5b2.

Rule: 4-connected components in bg=0; recolor each based on whether
its bbox touches the grid border. Border-touching → 2, interior → 8.

Combinatorial axes (8): grid_h/w, n_border_objs, n_interior_objs,
blob_size_min, blob_size_max, blob_shape, palette_size, position_bias.
Degenerates: all_border, all_interior, single_object.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "04c98e3e35bb_2"
VERSION = "1.1.2"
TASK_ID = "04c98e3e35bb_2"
SUMMARY = "Multi-color blobs on bg=0; rule recolors by border-touching status."

INVARIANTS = [
    "background is 0",
    ">=2 4-connected non-touching blobs",
    ">=1 blob touches grid border",
    ">=1 blob is strictly interior",
    "blobs use distinct colors (rule recolors all)",
]

BLOB_SHAPES = ("compact", "snake", "L", "rect", "single", "thin_line")
DEGENERATE_TEXTURES = ("all_border", "all_interior", "single_object")
HELPFUL_TEXTURES = BLOB_SHAPES

AXES = {
    "grid_h":           {"type": "int", "default": "rng 7..12", "valid": "5..16"},
    "grid_w":           {"type": "int", "default": "rng 7..12", "valid": "5..16"},
    "n_border_objs":    {"type": "int", "default": "rng 1..3", "valid": "0..4"},
    "n_interior_objs":  {"type": "int", "default": "rng 1..3", "valid": "0..4"},
    "blob_size_min":    {"type": "int", "default": "2", "valid": "1..4"},
    "blob_size_max":    {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "blob_shape":       {"type": "str", "default": "rng helpful",
                         "valid": "compact|snake|L|rect|single|thin_line"},
    "palette_size":     {"type": "int", "default": "rng 3..6", "valid": "2..9"},
    "texture":          {"type": "str", "default": "alias for blob_shape",
                         "valid": "compact|snake|L|rect|single|thin_line|"
                                  "all_border|all_interior|single_object"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 5, 8
    elif difficulty == "hard":
        h_lo, h_hi = 12, 16
    else:
        h_lo, h_hi = 7, 12
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_border = int(overrides.get("n_border_objs",
                                 ctx.draw_int("n_border_objs", 1, 3)))
    n_interior = int(overrides.get("n_interior_objs",
                                   ctx.draw_int("n_interior_objs", 1, 3)))
    n_palette = int(overrides.get("palette_size",
                                  ctx.draw_int("palette_size", 3, 6)))
    s_min = int(overrides.get("blob_size_min", 2))
    s_max = int(overrides.get("blob_size_max",
                              ctx.draw_int("blob_size_max", 3, 5)))
    s_min = max(1, min(s_min, 4))
    s_max = max(s_min, min(6, s_max))
    shape = (overrides.get("texture") or
             overrides.get("blob_shape")
             or ctx.draw_choice("blob_shape", list(BLOB_SHAPES)))
    g = full_grid(h, w, 0)
    colors = list(range(1, 10))
    rng.shuffle(colors)
    palette = colors[:max(2, min(9, n_palette))]
    used = set()
    placed_b = 0
    placed_i = 0
    color_idx = 0
    for _ in range(40):
        if placed_b >= n_border and placed_i >= n_interior:
            break
        size = rng.randint(s_min, s_max)
        if shape == "single":
            size = 1
        elif shape == "thin_line":
            size = max(2, size)
        blob = _grow_with_shape(rng, h, w, used, size, shape)
        if blob is None:
            continue
        on_border = any(r == 0 or r == h - 1 or c == 0 or c == w - 1
                        for r, c in blob)
        if on_border and placed_b >= n_border:
            continue
        if not on_border and placed_i >= n_interior:
            continue
        used |= blob
        c = palette[color_idx % len(palette)]
        color_idx += 1
        for r, cc in blob:
            g[r][cc] = c
        if on_border:
            placed_b += 1
        else:
            placed_i += 1
    if placed_b == 0:
        if g[0][0] == 0:
            g[0][0] = palette[0]
    if placed_i == 0:
        cr, cc = h // 2, w // 2
        if 1 <= cr < h - 1 and 1 <= cc < w - 1 and g[cr][cc] == 0:
            g[cr][cc] = palette[-1]
    return g


def _grow_with_shape(rng, h, w, used, size, shape):
    if shape == "rect":
        rh = max(1, min(h - 2, rng.randint(1, max(1, size // 2))))
        rw = max(1, min(w - 2, rng.randint(1, max(1, size // 2))))
        for _ in range(20):
            r0 = rng.randint(0, h - rh)
            c0 = rng.randint(0, w - rw)
            cells = {(r0 + dr, c0 + dc) for dr in range(rh) for dc in range(rw)}
            ok = all(_no_neighbor(used, r, c) for r, c in cells)
            if ok:
                return cells
        return None
    if shape == "thin_line":
        n = max(2, size)
        for _ in range(20):
            horizontal = rng.random() < 0.5
            if horizontal:
                r0 = rng.randint(0, h - 1)
                c0 = rng.randint(0, w - n)
                cells = {(r0, c0 + i) for i in range(n)}
            else:
                r0 = rng.randint(0, h - n)
                c0 = rng.randint(0, w - 1)
                cells = {(r0 + i, c0) for i in range(n)}
            if all(_no_neighbor(used, r, c) for r, c in cells):
                return cells
        return None
    if shape == "L":
        n = max(2, size // 2 + 1)
        for _ in range(20):
            r0 = rng.randint(0, h - n)
            c0 = rng.randint(0, w - n)
            cells = {(r0, c0 + i) for i in range(n)} | \
                    {(r0 + i, c0) for i in range(n)}
            if all(_no_neighbor(used, r, c) for r, c in cells):
                return cells
        return None
    return grow_blob(rng, h, w, used, size)


def _no_neighbor(used, r, c):
    if (r, c) in used:
        return False
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        if (r + dr, c + dc) in used:
            return False
    return True


_CARD4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=0; >=1 non-zero cell; at least one blob touches the border and
    (for non-easy difficulty) at least one is strictly interior."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    seen = set()
    blobs = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            comp = []
            while stack:
                r, c = stack.pop()
                comp.append((r, c))
                for dr, dc in _CARD4:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            blobs.append(comp)
    if not blobs:
        errors.append("no non-zero cells found")
        return errors
    border_touching = [any(r == 0 or r == h - 1 or c == 0 or c == w - 1
                           for r, c in b) for b in blobs]
    if not any(border_touching):
        errors.append("no blob touches the grid border")
    # only require an interior blob when the grid is large enough to support one
    if len(blobs) >= 2 and difficulty not in ("easy",) and all(border_touching):
        errors.append("all blobs touch the border; need >=1 strictly interior")
    return errors


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    palette = [3, 4, 6, 7, 9]
    rng.shuffle(palette)
    if name == "all_border":
        positions = [(0, 0), (0, w - 1), (h - 1, w - 1), (h - 1, 0)]
        for i, (r, c) in enumerate(positions):
            g[r][c] = palette[i % len(palette)]
        return g
    if name == "all_interior":
        for i, (r, c) in enumerate([(2, 2), (h // 2, w // 2),
                                     (h - 3, w - 3)]):
            if 1 <= r < h - 1 and 1 <= c < w - 1:
                g[r][c] = palette[i % len(palette)]
        return g
    if name == "single_object":
        cr, cc = h // 2, w // 2
        if 1 <= cr < h - 1 and 1 <= cc < w - 1:
            g[cr][cc] = palette[0]
            if cr + 1 < h - 1:
                g[cr + 1][cc] = palette[0]
        return g
    return g
