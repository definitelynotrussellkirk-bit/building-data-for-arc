"""Generator for 13b:m85 — scale keyed object 2x.

Rule: a single-cell marker names a color C. The multi-cell shape of
color C gets cropped and upscaled 2x. Output is that.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_shapes,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_marker, marker_color_missing, multiple_keyed_shapes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a70a4fc336b9"
VERSION = "1.2.2"
TASK_ID = "a70a4fc336b9"
SUMMARY = "1 single-cell marker (color C) + 2-3 multi-cell shapes, one matching C."

INVARIANTS = [
    "background is 0",
    "exactly one isolated single-cell marker",
    "2-3 multi-cell shapes, distinct colors; one matches marker color",
    "the keyed shape is non-rectangular, so the 2x crop is not a solid bar",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "marker_color_missing", "multiple_keyed_shapes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..14", "valid": "10..18"},
    "grid_w":         {"type": "int", "default": "rng 11..14", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_shapes":       {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..7"},
    "position_bias":  {"type": "str", "default": "marker_with_shapes",
                       "valid": "marker_with_shapes"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_SHAPES = [
    [(0, 0), (0, 1), (0, 2), (1, 1)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (1, 0), (1, 1), (1, 2)],
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (1, 1), (1, 2)],
    [(0, 0), (0, 1), (0, 2), (1, 0)],
    [(0, 0), (1, 0), (1, 1)],
]


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _place(g, rng, shape, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for _ in range(40):
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = color
        return True
    return False


def _components_of_color(grid, color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    comps: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                comp.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(comp)
    return comps


def _bbox_dims(cells: list[tuple[int, int]]) -> tuple[int, int]:
    return (max(r for r, _ in cells) - min(r for r, _ in cells) + 1,
            max(c for _, c in cells) - min(c for _, c in cells) + 1)


def _is_solid_bbox(cells: list[tuple[int, int]]) -> bool:
    bh, bw = _bbox_dims(cells)
    return len(set(cells)) == bh * bw


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the executable task contract for default samples."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs: list[str] = []
    if any(not isinstance(v, int) or not 0 <= v <= 9 for row in grid for v in row):
        errs.append("cells must be ARC colours 0..9")
    key = grid[0][0]
    if key == 0:
        errs.append("top-left marker must name a non-background colour")
        return errs
    if (w > 1 and grid[0][1] == key) or (h > 1 and grid[1][0] == key):
        errs.append("top-left marker must be an isolated single cell")
    colors = sorted({v for row in grid for v in row if v != 0})
    if len(colors) < 2:
        errs.append(f"expected keyed object plus distractor colour; got colours {colors}")

    key_comps = _components_of_color(grid, key)
    marker_comps = [comp for comp in key_comps if comp == [(0, 0)]]
    shape_comps = [comp for comp in key_comps if comp != [(0, 0)]]
    if len(marker_comps) != 1:
        errs.append("expected exactly one keyed marker component at (0, 0)")
    if len(shape_comps) != 1:
        errs.append(f"expected exactly one multi-cell keyed object; got {len(shape_comps)}")
    elif len(shape_comps[0]) < 3:
        errs.append("keyed object must have at least three cells")
    else:
        bh, bw = _bbox_dims(shape_comps[0])
        if bh < 2 or bw < 2:
            errs.append(f"keyed object crop must be two-dimensional, got bbox {bh}x{bw}")
        if _is_solid_bbox(shape_comps[0]):
            errs.append("keyed object crop should not be a solid rectangle/bar")

    other_multicell = False
    for color in colors:
        if color == key:
            continue
        if any(len(comp) >= 3 for comp in _components_of_color(grid, color)):
            other_multicell = True
            break
    if not other_multicell:
        errs.append("expected at least one non-key distractor shape")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 11, 12)
        n_shapes = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 14)
        w = ctx.draw_int("grid_w", 13, 14)
        n_shapes = 3
    else:
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 11, 14)
        n_shapes = None
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    if n_shapes is None:
        n_shapes = rng.randint(2, 3)
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], n_shapes)
    keyed_color = palette[0]
    g[0][0] = keyed_color
    # Rule: crop the keyed-color object and upscale 2x -> output. v1.x drew from a
    # fixed 7-shape bank -> few outputs (distinct 49). Use random polyominoes so
    # the keyed shape (the output) varies widely.
    for color in palette:
        is_keyed = color == keyed_color
        placed = False
        for _ in range(20):
            k = rng.randint(4, 7) if is_keyed else rng.randint(3, 7)
            shape = _rand_poly(rng, k, require_non_solid=is_keyed)
            if _place(g, rng, shape, color):
                placed = True
                break
        if is_keyed and not placed:
            _force_place(g, [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)], color)
    return g


def _normalise_shape(cells):
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in sorted(set(cells))]


def _rand_poly(rng, k, *, require_non_solid: bool = False):
    # Default generations should teach the crop-and-scale rule.  A straight bar or
    # filled rectangle upscales to a solid output and hides the object-shape signal,
    # so retry the keyed shape until its bounding box contains at least one hole.
    for _ in range(80):
        cells = [(0, 0)]; seen = {(0, 0)}
        while len(cells) < k:
            r, c = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            if (r + dr, c + dc) not in seen:
                cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
        shape = _normalise_shape(cells)
        if not require_non_solid:
            return shape
        bh, bw = _bbox_dims(shape)
        if bh >= 2 and bw >= 2 and not _is_solid_bbox(shape):
            return shape
    return [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)]


def _force_place(g, shape, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for r0 in range(2, h - sh + 1):
        for c0 in range(2, w - sw + 1):
            if _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
                for dr, dc in shape:
                    g[r0 + dr][c0 + dc] = color
                return True
    return False


def _draw_from_degenerate(name, rng):
    h, w = 12, 12
    g = full_grid(h, w, 0)
    if name == "no_marker":
        # no marker at corner → rule has no key color, undefined behavior
        _place(g, type("R", (), {"randint": lambda *a: 3, "choice": lambda x, y=None: y or x})(), _SHAPES[0], 4)
        for (dr, dc) in _SHAPES[0]: g[3 + dr][3 + dc] = 4
        for (dr, dc) in _SHAPES[1]: g[7 + dr][7 + dc] = 6
        return g
    if name == "marker_color_missing":
        # marker present but no shape of that color → rule has nothing to scale
        g[0][0] = 4   # key=4
        for (dr, dc) in _SHAPES[0]: g[3 + dr][3 + dc] = 6   # only 6-shape
        for (dr, dc) in _SHAPES[1]: g[7 + dr][7 + dc] = 8
        return g
    if name == "multiple_keyed_shapes":
        # multiple shapes share the keyed color → which one to scale?
        g[0][0] = 4   # key=4
        for (dr, dc) in _SHAPES[0]: g[3 + dr][3 + dc] = 4
        for (dr, dc) in _SHAPES[1]: g[7 + dr][7 + dc] = 4   # also 4
        return g
    return g
