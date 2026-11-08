"""Generator for 19b:m133 — select vertically-symmetric object and crop.

Rule: among the connected components, pick the first whose normalized
binary mask is left-right (vertical-axis) mirror-symmetric. Output is
that component cropped, recolored to 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_components (no shapes → rule has nothing to crop);
all_symmetric (every component is LR-symmetric → "exactly one"
precondition fails); all_asymmetric (no component is LR-symmetric
→ selector returns nothing).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "92227d482198"
VERSION = "2.1.0"  # reject solid symmetric targets + add executable self_check invariants
TASK_ID = "92227d482198"

SUMMARY = "2-3 components; exactly one is a (procedurally varied) LR-mirror symmetric shape."

INVARIANTS = [
    "background is 0",
    "2-3 isolated 4-connected components in distinct colors",
    "exactly one bbox-normalized binary shape is LR-mirror symmetric",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_components", "all_symmetric", "all_asymmetric")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "grid_w":            {"type": "int", "default": "rng 11..14", "valid": "10..16"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "sym_w":             {"type": "int", "default": "rng 3..5 symmetric width", "valid": "3..6"},
    "sym_h":             {"type": "int", "default": "rng 2..4 symmetric height", "valid": "2..5"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|no_components|all_symmetric|all_asymmetric"},
}


def _connected(cells):
    cells = set(cells)
    if not cells:
        return False
    start = next(iter(cells)); seen = {start}; stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            n = (r + dr, c + dc)
            if n in cells and n not in seen:
                seen.add(n); stack.append(n)
    return len(seen) == len(cells)


def _make_lr_sym(rng, w, h):
    """A connected, non-trivial LR-mirror-symmetric shape (random left half + mirror)."""
    half = (w + 1) // 2
    for _ in range(120):
        cells = set()
        for r in range(h):
            for c in range(half):
                if rng.random() < 0.55:
                    cells.add((r, c)); cells.add((r, w - 1 - c))
        if len(cells) < 3:
            continue
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        rmin, cmin = min(rs), min(cs)
        norm = {(r - rmin, c - cmin) for r, c in cells}
        nh = max(r for r, _ in norm) + 1
        nw = max(c for _, c in norm) + 1
        if nw < 2 or not _connected(norm):           # need a real, connected shape
            continue
        if len(norm) == nh * nw:                     # avoid a solid-rectangle crop (uninformative all-8 output)
            continue
        return sorted(norm)
    return [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)]   # fallback plus


_LR_SYM = [
    [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)],
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
    [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)],
    [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 3), (2, 0), (2, 3)],
]
_ASYM = [
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 0)],
    [(0, 0), (0, 1), (1, 1), (2, 1)],
]


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _place_or_raise(g, rng, shape, color, label):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for _ in range(60):
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = color
        return
    raise ValueError(f"could not place {label} shape after 60 attempts")


def _nonzero_components(grid):
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 or seen[sr][sc]:
                continue
            stack = [(sr, sc)]
            seen[sr][sc] = True
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and grid[nr][nc] != 0:
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def _normalize_shape(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return {(r - r0, c - c0) for r, c in cells}


def _shape_dims(shape):
    return (max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1)


def _lr_symmetric_shape(shape):
    _, w = _shape_dims(shape)
    return all((r, w - 1 - c) in shape for r, c in shape)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify default instances have one useful LR-symmetric target and
    asymmetric distractors; reject solid symmetric crops that become an
    uninformative all-8 output after the canonical rule recolors the crop."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    if any(v < 0 or v > 9 for row in grid for v in row):
        errors.append("cell value out of 0-9")
    comps = _nonzero_components(grid)
    if len(comps) not in (2, 3):
        errors.append(f"expected 2-3 isolated components, found {len(comps)}")
    colors = []
    sym_shapes = []
    for cells in comps:
        vals = {grid[r][c] for r, c in cells}
        if len(vals) != 1:
            errors.append("component mixes colors")
            continue
        colors.append(next(iter(vals)))
        shape = _normalize_shape(cells)
        if _lr_symmetric_shape(shape):
            sym_shapes.append(shape)
    if len(colors) != len(set(colors)):
        errors.append("component colors are not distinct")
    if len(sym_shapes) != 1:
        errors.append(f"expected exactly one LR-symmetric component, found {len(sym_shapes)}")
    elif len(sym_shapes[0]) == _shape_dims(sym_shapes[0])[0] * _shape_dims(sym_shapes[0])[1]:
        errors.append("LR-symmetric component is a solid rectangle; output crop would be single-color")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10); w = ctx.draw_int("grid_w", 11, 12)
        sw = ctx.draw_int("sym_w", 3, 4); sh = ctx.draw_int("sym_h", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12); w = ctx.draw_int("grid_w", 13, 15)
        sw = ctx.draw_int("sym_w", 4, 5); sh = ctx.draw_int("sym_h", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 11, 14)
        sw = ctx.draw_int("sym_w", 3, 5); sh = ctx.draw_int("sym_h", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    n_asym = rng.randint(1, 2)
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 1 + n_asym)
    _place_or_raise(g, rng, _make_lr_sym(rng, sw, sh), palette[0], "symmetric")
    for color in palette[1:]:
        _place_or_raise(g, rng, rng.choice(_ASYM), color, "asymmetric")
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_components":
        return g
    if name == "all_symmetric":
        # Every component is LR-symmetric — "exactly one" precondition fails.
        for dr, dc in [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)]:
            g[1 + dr][1 + dc] = 1
        for dr, dc in [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]:
            g[5 + dr][6 + dc] = 2
        return g
    if name == "all_asymmetric":
        # No component is LR-symmetric — selector returns nothing.
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[1 + dr][1 + dc] = 1
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[5 + dr][7 + dc] = 2
        return g
    return g
