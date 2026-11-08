"""Generator for 7b:m46 — scale smallest blob by 2.

Rule: pick the smallest blob, crop to bbox, upscale by 2.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_smallest, single_blob, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "bbbf48888149"
# 2.1.0: output is the SMALLEST blob upscaled 2x; with smallest sizes 2-3 the
# shape variety (hence output) was tiny -> dup-outputs(30%), uniq 0.30. Now
# the smallest blob is drawn from a wider/larger size range (4-7) and the
# others strictly larger, so the upscaled output varies widely.
VERSION = "2.1.0"
TASK_ID = "bbbf48888149"
SUMMARY = (
    "0-bg grid (h~8-11, w~9-12) with exactly 3 ISOLATED "
    "4-conn BLOBS in distinct colors with strictly distinct "
    "sizes (drawn from {2..6}). Blobs are non-touching. "
    "Rule: identify all 4-conn non-bg objects, pick the one "
    "with the SMALLEST cell count (unique by construction), "
    "crop to its bounding box, and UPSCALE by factor 2 "
    "(each cell becomes a 2×2 block of the same color). "
    "Output dimensions = (2 * bbox_h) × (2 * bbox_w)."
)

INVARIANTS = [
    "background is 0",
    "3 distinct-color blobs with strictly distinct sizes",
    "blobs don't 4-touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_smallest", "single_blob", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_blobs":        {"type": "int", "default": "3", "valid": "3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "non_touching",
                       "valid": "non_touching"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|tied_smallest|single_blob|no_blobs"},
}


def _components(grid):
    """Return 4-connected nonzero same-color components as (color, cells)."""
    from collections import deque
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            q = deque([(sr, sc)])
            seen.add((sr, sc))
            cells = []
            while q:
                r, c = q.popleft()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            out.append((color, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the smallest-component x2 task.

    The canonical output may legitimately be a large solid-color crop when the
    smallest component is rectangular/line-like, so this check focuses on the
    input contract: exactly three isolated nonzero blobs, distinct colors, and
    a unique smallest component by cell count.
    """
    errors = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular and nonempty"]
    h, w = len(grid), len(grid[0])
    if any(v < 0 or v > 9 for row in grid for v in row):
        errors.append("grid colors must be digits 0..9")
    comps = _components(grid)
    if len(comps) != 3:
        errors.append(f"expected exactly 3 nonzero components, found {len(comps)}")
    colors = [color for color, _cells in comps]
    if len(colors) != len(set(colors)):
        errors.append("component colors must be distinct")
    sizes = [len(cells) for _color, cells in comps]
    if len(sizes) != len(set(sizes)):
        errors.append(f"component sizes must be strictly distinct, found {sizes}")
    if sizes and min(sizes) < 3:
        errors.append(f"smallest blob should be nontrivial (>=3 cells), found {min(sizes)}")
    occupied = {(r, c): color for color, cells in comps for r, c in cells}
    for (r, c), color in occupied.items():
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = (r + dr, c + dc)
            if nb in occupied and occupied[nb] != color:
                errors.append("distinct-color blobs must not 4-touch")
                return errors
    if h < 8 or w < 8:
        errors.append(f"input grid unexpectedly small: {h}x{w}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 10, 12)
        smallest = rng.randint(3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 13, 14)
        smallest = rng.randint(5, 7)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 11, 14)
        smallest = rng.randint(4, 6)
    g = full_grid(h, w, 0)
    # The output is the SMALLEST blob upscaled, so give it a decent size for
    # shape variety; the other two are strictly larger.
    sizes = [smallest, smallest + rng.randint(1, 2), smallest + rng.randint(3, 4)]
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 3)
    used: set[tuple[int, int]] = set()
    for size, color in zip(sizes, palette):
        cells = grow_blob(rng, h, w, used, size, max_attempts=80)
        if cells is None: continue
        for r, c in cells: g[r][c] = color
        used |= cells
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "tied_smallest":
        # two blobs share min size → smallest is ambiguous
        for r, c in [(1, 1), (1, 2)]: g[r][c] = 3
        for r, c in [(5, 5), (5, 6)]: g[r][c] = 5
        for r, c in [(7, 1), (7, 2), (8, 1)]: g[r][c] = 7
        return g
    if name == "single_blob":
        # one blob → trivially smallest, scale-x2 trivial
        for r, c in [(3, 3), (3, 4), (4, 3)]: g[r][c] = 6
        return g
    if name == "no_blobs":
        # empty grid → no blob to scale
        return g
    return g
