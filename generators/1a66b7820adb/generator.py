"""Generator for 3b:m20 — crop and pack horizontally.

Rule: sort blobs by some order, gallery-pack horizontally.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_shapes, single_blob, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "1a66b7820adb"
VERSION = "2.1.0"  # defect-lint canonical-coverage: canonical demos span 8x14..10x16
# with blobs up to ~6 cells; our dims capped at 9x11 and blobs at 4. Widened both.
TASK_ID = "1a66b7820adb"
SUMMARY = (
    "0-bg grid (h~6-9, w~8-11) "
    "with 3 BLOBS in DISTINCT "
    "non-zero colors (from 1..9) "
    "at non-touching positions "
    "(grow_blob with no shared "
    "cells). Each blob has 2-4 "
    "cells; blob shapes may "
    "vary. Rule (SORT BLOBS + "
    "HORIZONTAL GALLERY PACK): "
    "identify each BLOB as a "
    "connected component. SORT "
    "blobs by some criterion "
    "(e.g., size descending, "
    "color, or position). CROP "
    "each to its BBOX. PACK the "
    "crops HORIZONTALLY in "
    "sorted order, possibly with "
    "1-COL GAPS. Output WIDTH = "
    "sum of bbox widths + gaps; "
    "HEIGHT = MAX bbox height. "
    "Net: 3 blobs → horizontal "
    "gallery in sorted order."
)

INVARIANTS = [
    "background is 0",
    "3 distinct-color blobs",
    "blobs don't 4-touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_shapes", "single_blob", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "6-7 easy / 6-10 med / 9-12 hard", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "8-9 easy / 8-16 med / 12-16 hard", "valid": "7..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "3", "valid": "3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "non_touching",
                       "valid": "non_touching"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 8, 9)
        blob_hi = 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 12, 16)
        blob_hi = 6
    else:
        h = ctx.draw_int("grid_h", 6, 10)
        w = ctx.draw_int("grid_w", 8, 16)
        blob_hi = 5
    rng = ctx.draw_rng("layout")
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 3)
    for _layout_try in range(30):
        g = full_grid(h, w, 0)
        used: set[tuple[int, int]] = set()
        ok = True
        for color in palette:
            cells = grow_blob(rng, h, w, used, rng.randint(2, blob_hi), max_attempts=160)
            if cells is None:
                ok = False
                break
            for r, c in cells:
                g[r][c] = color
            used |= cells
        if ok:
            return g
    raise ValueError("could not place three isolated blobs")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the normal examples contain exactly three isolated blobs."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    colors = sorted({grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0})
    if len(colors) != 3:
        errs.append(f"expected exactly 3 distinct blob colors, found {len(colors)}")
    components = []
    seen = set()
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            comp = []
            while stack:
                rr, cc = stack.pop()
                comp.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            components.append((color, comp))
    if len(components) != 3:
        errs.append(f"expected exactly 3 connected blobs, found {len(components)}")
    for color, comp in components:
        if not (2 <= len(comp) <= 6):
            errs.append(f"blob color {color} has size {len(comp)}; expected 2..6")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "tied_shapes":
        # multiple blobs share identical shapes → sort key ambiguous
        for r, c in [(1, 1), (2, 1)]: g[r][c] = 3
        for r, c in [(1, 5), (2, 5)]: g[r][c] = 5
        for r, c in [(5, 7), (6, 7)]: g[r][c] = 7
        return g
    if name == "single_blob":
        # one blob → no comparison, packing trivial
        for r, c in [(3, 3), (3, 4), (4, 3)]: g[r][c] = 6
        return g
    if name == "no_blobs":
        # empty grid → nothing to crop or pack
        return g
    return g
