"""Generator for arc_additional_puzzles_21_set22_bundle:M148: crop largest component.

Rule: among disconnected nonzero components, the unique largest is
cropped out.

Combinatorial axes (8): grid_h, grid_w, palette_kind, large_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_largest, single_component, no_components.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.blobs import grow_blob
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "82babb933dc3"
VERSION = "2.0.1"
TASK_ID = "82babb933dc3"
SUMMARY = (
    "0-bg grid (h~9-13, w~10-15) with 2-5 "
    "DISCONNECTED CONNECTED COMPONENTS in distinct "
    "non-bg colors. One component has STRICTLY "
    "LARGEST cell-count (size 7-11 cells), and the "
    "others are strictly smaller blobs (sizes "
    "decreasing). Each component is painted "
    "UNIFORMLY in a single color so the largest "
    "component is unambiguous. Rule: identify the "
    "UNIQUE LARGEST component (by cell count). CROP "
    "it to its bounding box, preserving its color. "
    "Output: the small cropped subgrid showing just "
    "the largest blob's cells (in its original "
    "color, with 0 elsewhere inside the bbox). All "
    "smaller blobs are discarded. Net: input is a "
    "multi-blob scene; output is the bbox of the "
    "biggest blob alone."
)

# Rivals: 'crop the smallest' refuted by ≥1 demo where output matches
# the largest (visible by size compared to other components). 'crop a
# fixed-position component' refuted by ≥2 demos with the largest at
# different positions. 'recolor on crop' refuted by any demo (color
# preserved). 'crop a uniform color regardless of size' refuted by ≥1
# demo where the largest component has a unique color but other
# components together cover more cells.
# 4 demos with varied largest sizes + varied component counts.
EXAMPLES_NEEDED = 4

# v1.1.0 bug: assigned per-cell colors to the largest blob via
# `colors[(i + j) % len(colors)]`, which fragmented it into multiple
# single-color components. The "largest" invariant only holds when
# each component is a single color. v1.2.0 paints each component
# uniformly and includes colors 1-3 in the palette.
INVARIANTS = [
    "nonzero components are separated by background",
    "one component has strictly largest area",
    "component colors are preserved inside the eventual crop",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_largest", "single_component", "no_components")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..13", "valid": "7..18"},
    "grid_w":         {"type": "int", "default": "rng 10..15", "valid": "7..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "large_size":     {"type": "int", "default": "rng 7..11", "valid": "4..20"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "position_bias":  {"type": "str", "default": "spread_distinct_sizes",
                       "valid": "spread_distinct_sizes"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥2 distinct 4-connected components; one is strictly largest."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    visited = [[False] * w for _ in range(h)]
    sizes = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] != 0 and not visited[r0][c0]:
                queue = [(r0, c0)]
                visited[r0][c0] = True
                sz = 0
                while queue:
                    r, c = queue.pop()
                    sz += 1
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0 and not visited[nr][nc]:
                            visited[nr][nc] = True
                            queue.append((nr, nc))
                sizes.append(sz)
    if not sizes:
        return []  # no_components degenerate — allowed
    errs = []
    if len(sizes) < 2:
        return []  # single_component degenerate — allowed
    max_sz = max(sizes)
    if sizes.count(max_sz) > 1:
        errs.append(f"largest size {max_sz} is tied; expected unique largest")
    return errs



def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 9, 10, 10, 11
        large_lo, large_hi = 5, 7
        n_blobs_lo, n_blobs_hi = 2, 3
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 13, 16, 15, 18
        large_lo, large_hi = 10, 14
        n_blobs_lo, n_blobs_hi = 3, 5
    else:
        h_lo, h_hi, w_lo, w_hi = 10, 13, 12, 16
        large_lo, large_hi = 7, 11
        n_blobs_lo, n_blobs_hi = 3, 4
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    large_size = ctx.draw_int("large_size", large_lo, large_hi)
    n_blobs = ctx.draw_int("n_blobs", n_blobs_lo, n_blobs_hi)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    used = set()
    # Largest blob first, then smaller blobs each strictly smaller so
    # 'unique largest' invariant holds.
    sizes = [large_size]
    for i in range(1, n_blobs):
        upper = large_size - 1
        lower = max(1, large_size - 3 - i)
        sizes.append(rng.randint(lower, upper))
    # Sort smaller blobs in random order (largest stays first).
    head, rest = sizes[0], sizes[1:]
    rng.shuffle(rest)
    sizes = [head] + rest

    # Palette now includes colors 1, 2, 3 (was missing) — random sample
    # without replacement so each blob has a distinct color.
    palette_pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(palette_pool)
    colors_for_blobs = palette_pool[:n_blobs]

    for i, size in enumerate(sizes):
        cells = grow_blob(rng, h, w, used, size)
        if cells is None:
            continue
        used |= cells
        # Each blob painted in a single uniform color (fixes v1.1.0 bug
        # where the largest blob was multi-colored and thus fragmented).
        color = colors_for_blobs[i % len(colors_for_blobs)]
        for r, c in cells:
            g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 11, 12
    g = full_grid(h, w, 0)
    if name == "tied_largest":
        # two equal-size large components → "largest" ambiguous
        for (r, c) in [(1, 1), (1, 2), (2, 1), (2, 2), (1, 3)]: g[r][c] = 4
        for (r, c) in [(7, 7), (7, 8), (8, 7), (8, 8), (7, 9)]: g[r][c] = 6
        return g
    if name == "single_component":
        # one component → trivially largest, crop is just that component's bbox
        for (r, c) in [(3, 3), (3, 4), (4, 3), (4, 4), (5, 4)]: g[r][c] = 4
        return g
    if name == "no_components":
        # blank grid → no components to crop
        return g
    return g
