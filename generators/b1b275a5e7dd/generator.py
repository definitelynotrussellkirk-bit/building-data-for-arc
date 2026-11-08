"""Generator for arc_puzzle_bank_thirteenth21:M87.

Rule: keep only the largest blob; recolor it in the smallest blob's
color. Drop all other blobs.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_largest, single_blob, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "b1b275a5e7dd"
VERSION = "1.1.1"
TASK_ID = "b1b275a5e7dd"
SUMMARY = "2-3 distinct-color blobs of strictly distinct sizes."

INVARIANTS = [
    "background is 0",
    "≥2 distinct-color blobs with strictly distinct sizes",
    "blobs don't 4-touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_largest", "single_blob", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "3", "valid": "2..3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "non_touching",
                       "valid": "non_touching"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥2 distinct non-bg blob colors; all blob sizes strictly distinct."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    visited = [[False] * w for _ in range(h)]
    blob_sizes: dict[int, list[int]] = {}
    for sr in range(h):
        for sc in range(w):
            v = grid[sr][sc]
            if v == 0 or visited[sr][sc]:
                continue
            q = [(sr, sc)]
            visited[sr][sc] = True
            count = 0
            while q:
                r, c = q.pop()
                count += 1
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and not visited[nr][nc] and grid[nr][nc] == v:
                        visited[nr][nc] = True
                        q.append((nr, nc))
            blob_sizes.setdefault(v, []).append(count)
    if len(blob_sizes) < 2:
        errs.append(f"expected ≥2 distinct blob colors; found {len(blob_sizes)}")
    all_sizes = [s for sizes in blob_sizes.values() for s in sizes]
    if len(set(all_sizes)) < len(all_sizes):
        errs.append(f"blob sizes not strictly distinct: {sorted(all_sizes)}")
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
    sizes = rng.sample(range(1, 7), 3)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 3)
    used: set[tuple[int, int]] = set()
    for size, color in zip(sizes, palette):
        cells = grow_blob(rng, h, w, used, size, max_attempts=80)
        if cells is None:
            continue
        for r, c in cells:
            g[r][c] = color
        used |= cells
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "tied_largest":
        # two blobs share max size → which to keep ambiguous
        for r, c in [(1, 1), (1, 2), (2, 1)]: g[r][c] = 3
        for r, c in [(5, 5), (5, 6), (6, 5)]: g[r][c] = 5
        for r, c in [(7, 1), (7, 2)]: g[r][c] = 7
        return g
    if name == "single_blob":
        # one blob → it's both largest and smallest, recolor to itself (identity)
        for r, c in [(3, 3), (3, 4), (4, 3)]: g[r][c] = 6
        return g
    if name == "no_blobs":
        # empty grid → no blobs to keep or recolor
        return g
    return g
