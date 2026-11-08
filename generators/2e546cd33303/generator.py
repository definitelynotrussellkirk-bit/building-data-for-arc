"""Generator for arc_puzzle_bank_21_set20_bundle:medium_p02 — bbox-outline every blob.

Rule: replace each blob with rect-outline of its bbox (in the blob's color).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_rectangular, single_blob, bboxes_overlap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "2e546cd33303"
VERSION = "1.1.1"
TASK_ID = "2e546cd33303"
SUMMARY = "2-3 distinct-color blobs whose bbox-outline differs from the blob shape."

INVARIANTS = [
    "background is 0",
    "blobs are non-rectangular (so bbox-outline != input shape)",
    "blobs have distinct colors and non-overlapping bboxes",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_rectangular", "single_blob", "bboxes_overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_blobs":        {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "position_bias":  {"type": "str", "default": "bbox_isolated",
                       "valid": "bbox_isolated"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|all_rectangular|single_blob|bboxes_overlap"},
}


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def _bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Require multiple distinct-color non-rectangular blobs with disjoint bboxes."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    comps = _components(grid)
    errs: list[str] = []
    if len(comps) < 2:
        errs.append(f"expected >=2 non-bg blobs, got {len(comps)}")
    colors = [color for color, _ in comps]
    if len(set(colors)) != len(colors):
        errs.append("normal instances should use a distinct color per blob")
    boxes = []
    for color, cells in comps:
        r1, c1, r2, c2 = _bbox(cells)
        area = (r2 - r1 + 1) * (c2 - c1 + 1)
        if area == len(cells):
            errs.append(f"color {color} blob is rectangular; bbox-outline would be trivial")
        box = set((r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1))
        if any(box & prev for prev in boxes):
            errs.append("blob bounding boxes overlap")
            break
        boxes.append(box)
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 11, 12)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 12)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    used: set[tuple[int, int]] = set()
    n = rng.randint(2, 3)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    for color in palette:
        for _ in range(40):
            cells = grow_blob(rng, h, w, used, rng.randint(3, 5), max_attempts=20)
            if cells is None:
                continue
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            bb_h = max(rs) - min(rs) + 1
            bb_w = max(cs) - min(cs) + 1
            if bb_h * bb_w == len(cells):
                continue
            bbox_cells = {(r, c) for r in range(min(rs), max(rs) + 1) for c in range(min(cs), max(cs) + 1)}
            if bbox_cells & used:
                continue
            for r, c in cells:
                g[r][c] = color
            used |= bbox_cells
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "all_rectangular":
        # solid rectangles → bbox-outline is just the perimeter, but interior was already filled,
        # so output strictly differs from input only at interior cells (rule appears to "hollow out")
        for r in range(2, 5):
            for c in range(2, 5):
                g[r][c] = 4
        for r in range(6, 9):
            for c in range(6, 9):
                g[r][c] = 6
        return g
    if name == "single_blob":
        # one blob → no comparison among objects, rule still works trivially
        for r, c in [(3, 3), (3, 4), (4, 3), (5, 4), (6, 4)]:
            g[r][c] = 5
        return g
    if name == "bboxes_overlap":
        # blobs whose bboxes overlap → outlines paint over each other, ambiguous
        for r, c in [(2, 2), (2, 3), (3, 4)]:
            g[r][c] = 4
        for r, c in [(3, 5), (4, 4), (5, 3)]:
            g[r][c] = 6
        return g
    return g
