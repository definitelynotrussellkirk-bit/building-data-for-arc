"""Generator for arc_additional_puzzles_21_set3:M19 — Recolor 8-blobs by size rank.

Rule: sort 8-blobs by size asc; recolor 1st→2, 2nd→3, 3rd→4. Output starts
from empty grid (only the recolored blobs remain).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_sizes, single_blob, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "2c4317f69f0a"
VERSION = "2.0.1"
TASK_ID = "2c4317f69f0a"
SUMMARY = (
    "0-bg grid (h~8-12, w~8-12) with "
    "EXACTLY 3 NON-TOUCHING COLOR-8 "
    "(cyan) BLOBS at scattered "
    "positions, with STRICTLY "
    "DISTINCT SIZES (3 unique values "
    "from 2..6, sorted ascending and "
    "placed via grow_blob). Blobs are "
    "4-conn isolated. Rule (SIZE-RANK "
    "RECOLOR + ERASE OTHERS): "
    "identify the 3 COLOR-8 BLOBS. "
    "SORT them by SIZE ASCENDING. "
    "RECOLOR by rank: smallest → "
    "COLOR 2 (red), medium → COLOR 3 "
    "(green), largest → COLOR 4 "
    "(yellow). Other cells stay 0. "
    "Note: output starts from an "
    "empty grid (only the 3 "
    "recolored blobs remain in their "
    "positions). Net: 3 cyan blobs "
    "→ ranked colors (2, 3, 4) by "
    "size; bg cells stay 0."
)

INVARIANTS = [
    "exactly 3 non-touching 8-blobs",
    "all distinct sizes",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_sizes", "single_blob", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "3", "valid": "3"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "non_touching",
                       "valid": "non_touching"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly 3 color-8 blobs present with distinct sizes."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    # find color-8 cells and count connected components via BFS
    eights = set((r, c) for r in range(h) for c in range(w) if grid[r][c] == 8)
    if not eights:
        return ["no color-8 cells found"]
    visited = set()
    sizes = []
    for start in eights:
        if start in visited:
            continue
        queue = [start]
        comp = []
        while queue:
            cell = queue.pop()
            if cell in visited:
                continue
            visited.add(cell)
            comp.append(cell)
            r, c = cell
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nb = (r + dr, c + dc)
                if nb in eights and nb not in visited:
                    queue.append(nb)
        sizes.append(len(comp))
    errs = []
    if len(sizes) != 3:
        errs.append(f"expected 3 color-8 blobs, got {len(sizes)}")
    if len(set(sizes)) != len(sizes):
        errs.append(f"blob sizes are not all distinct: {sorted(sizes)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 11, 12)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 8, 12)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    sizes = list(range(2, 7)); rng.shuffle(sizes); sizes = sorted(sizes[:3])
    used = set()
    for size in sizes:
        for _ in range(15):
            blob = grow_blob(rng, h, w, used, size)
            if blob is None: continue
            used |= blob
            for r, c in blob: g[r][c] = 8
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "tied_sizes":
        # two 8-blobs same size → rank tie, which becomes 2 vs 3 ambiguous
        for r, c in [(1, 1), (2, 1)]: g[r][c] = 8
        for r, c in [(5, 5), (5, 6)]: g[r][c] = 8
        for r, c in [(7, 1), (7, 2), (8, 1)]: g[r][c] = 8
        return g
    if name == "single_blob":
        # only one 8-blob → no rank-ordering, smallest=largest
        for r, c in [(3, 3), (3, 4), (4, 3)]: g[r][c] = 8
        return g
    if name == "no_blobs":
        # empty grid → no blobs to recolor by rank
        return g
    return g
