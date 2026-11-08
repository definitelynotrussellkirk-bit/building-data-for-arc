"""Generator for arc_puzzle_bank_twelfth21:E80.

Rule: erase singleton same-colour 4-connected objects; keep larger objects.

Combinatorial axes: grid_h/w, singleton count, palette kind and texture.
Degenerates: no_singletons, all_singletons, components_touching.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7358813cf026"
VERSION = "1.3.0"
TASK_ID = "7358813cf026"
SUMMARY = "Singleton same-color objects are erased while larger objects remain."

INVARIANTS = [
    "background is 0",
    "some same-color objects have size 1",
    "some same-color objects have size at least 2",
    "objects are separated by background",
]

PALETTES = {
    "default": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (2, 4, 6, 7),
    "cool": (1, 3, 8, 9),
    "varied": (1, 2, 3, 4, 5, 6, 7, 8, 9),
}
PALETTE_KINDS = tuple(PALETTES)
DEGENERATE_TEXTURES = ("no_singletons", "all_singletons", "components_touching")
HELPFUL_TEXTURES = PALETTE_KINDS

# These bounds are the actual supported ordinary-generation domain.  Earlier
# metadata advertised 4..20/22 and several knobs that generation never used.
AXES = {
    "grid_h": {"type": "int", "default": "rng 8..11", "valid": "8..11"},
    "grid_w": {"type": "int", "default": "rng 8..12", "valid": "8..12"},
    "singletons": {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "palette_kind": {
        "type": "str",
        "default": "rng helpful",
        "valid": "|".join(PALETTE_KINDS),
    },
    "texture": {
        "type": "str",
        "default": "alias for palette_kind",
        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES),
    },
}


def _same_color_objects(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    objects = []
    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            objects.append((color, cells))
    return objects


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify canonical same-colour object semantics and a useful mixed lesson."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if h > 30 or w > 30:
        return [f"grid too large: {h}x{w}"]
    sizes = [len(cells) for _, cells in _same_color_objects(grid)]
    errs = []
    if not any(size == 1 for size in sizes):
        errs.append("no singleton same-color objects found (rule would be no-op)")
    if not any(size >= 2 for size in sizes):
        errs.append("no multi-cell same-color objects found (everything is singleton)")
    return errs


def _free(grid, cells):
    h, w = len(grid), len(grid[0])
    cells = set(cells)
    for r, c in cells:
        if not (0 <= r < h and 0 <= c < w) or grid[r][c] != 0:
            return False
        for rr in range(max(0, r - 1), min(h, r + 2)):
            for cc in range(max(0, c - 1), min(w, c + 2)):
                if (rr, cc) not in cells and grid[rr][cc] != 0:
                    return False
    return True


def _draw_axis_int(ctx, label, default_lo, default_hi, valid_lo, valid_hi):
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _place_shape(grid, shape, color, rng):
    h, w = len(grid), len(grid[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    candidates = []
    for top in range(h - sh + 1):
        for left in range(w - sw + 1):
            cells = [(top + r, left + c) for r, c in shape]
            if _free(grid, cells):
                candidates.append(cells)
    if not candidates:
        return False
    cells = rng.choice(candidates)
    for r, c in cells:
        grid[r][c] = color
    return True


def _construct_layout(h, w, singleton_count, palette, ctx):
    # Rebuild the whole sparse layout on each attempt.  This makes the declared
    # singleton endpoints real even on the smallest supported 8x8 board.
    shapes = (
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (1, 0), (2, 0)),
        ((0, 0), (0, 1)),
    )
    for attempt in range(128):
        rng = ctx.draw_rng(f"layout-{attempt}")
        grid = full_grid(h, w, 0)
        shape = shapes[attempt % len(shapes)]
        if not _place_shape(grid, shape, rng.choice(palette), rng):
            continue
        # Add a second multi-cell control when it fits, but never at the cost of
        # the exact singleton count.
        before_second = [row[:] for row in grid]
        _place_shape(grid, ((0, 0), (0, 1)), rng.choice(palette), rng)
        placed = 0
        while placed < singleton_count:
            candidates = [
                (r, c)
                for r in range(h)
                for c in range(w)
                if _free(grid, [(r, c)])
            ]
            if not candidates:
                break
            r, c = rng.choice(candidates)
            grid[r][c] = rng.choice(palette)
            placed += 1
        if placed == singleton_count and self_check(grid) == []:
            return grid
        # A second object can consume too much room on a small unlucky layout;
        # retry the same attempt with only the required first object.
        grid = before_second
        placed = 0
        while placed < singleton_count:
            candidates = [
                (r, c)
                for r in range(h)
                for c in range(w)
                if _free(grid, [(r, c)])
            ]
            if not candidates:
                break
            r, c = rng.choice(candidates)
            grid[r][c] = rng.choice(palette)
            placed += 1
        if placed == singleton_count and self_check(grid) == []:
            return grid
    raise ValueError(
        f"could not place one multi-cell object and {singleton_count} singletons on {h}x{w}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    texture = overrides.get("texture")
    if texture is not None:
        texture = ctx.draw_choice("texture", HELPFUL_TEXTURES + DEGENERATE_TEXTURES)
        if texture in DEGENERATE_TEXTURES:
            return _draw_from_degenerate(texture, ctx)
        if overrides.get("palette_kind") not in (None, texture):
            raise ValueError("helpful texture and palette_kind must agree")
        palette_kind = texture
    else:
        palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)

    if difficulty == "easy":
        h_band, w_band, n_band = (8, 9), (8, 9), (3, 4)
    elif difficulty == "hard":
        h_band, w_band, n_band = (10, 11), (11, 12), (4, 5)
    else:
        h_band, w_band, n_band = (8, 11), (8, 12), (3, 5)
    h = _draw_axis_int(ctx, "grid_h", *h_band, 8, 11)
    w = _draw_axis_int(ctx, "grid_w", *w_band, 8, 12)
    noise = _draw_axis_int(ctx, "singletons", *n_band, 3, 5)
    return _construct_layout(h, w, noise, PALETTES[palette_kind], ctx)


def _draw_from_degenerate(name, ctx):
    # Reserved dimension axes always describe the full returned grid, even on
    # explicit degenerate textures.  Direct fixture calls retain 9x10.
    if ctx is None:
        h, w = 9, 10
    else:
        h = _draw_axis_int(ctx, "grid_h", 9, 9, 8, 11)
        w = _draw_axis_int(ctx, "grid_w", 10, 10, 8, 12)
    grid = full_grid(h, w, 0)
    if name == "no_singletons":
        for r, c in [(2, 2), (2, 3), (3, 2)]:
            grid[r][c] = 4
        for r, c in [(5, 5), (5, 6), (6, 5)]:
            grid[r][c] = 6
        return grid
    if name == "all_singletons":
        for r, c, value in [(1, 1, 3), (3, 5, 4), (5, 7, 5), (7, 2, 6)]:
            grid[r][c] = value
        return grid
    if name == "components_touching":
        # Same-color orthogonal neighbours are one canonical object.
        for r, c in [(2, 2), (2, 3)]:
            grid[r][c] = 3
        return grid
    return grid
