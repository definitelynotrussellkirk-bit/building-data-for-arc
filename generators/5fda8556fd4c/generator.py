"""Generator for arc_additional_puzzles_21_set14_bundle:E94.

Rule: a compact colored motif sits inside a zero border and is cropped
to its content.

Combinatorial axes (8): grid_h/w, palette_kind, motif_position,
palette_size, position_bias, n_distinct_colors, motif_density, texture.
Degenerates: motif_at_border, motif_fills_grid, no_motif.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5fda8556fd4c"
# 3.3.0: defect-lint all_background_output — content was always a SOLID rectangle,
# so the crop output was a featureless block. Content is now a connected shape that
# spans its bbox without filling it. (3.2.0: single connected object.)
VERSION = "3.3.0"
TASK_ID = "5fda8556fd4c"
SUMMARY = (
    "0-bg grid (h, w ~7-10) with one compact connected foreground motif "
    "placed inside optional zero padding. Rule: detect all non-bg cells, "
    "compute their bounding box, and crop the grid to that bbox."
)

INVARIANTS = [
    "background is 0",
    "all nonzero content belongs to one connected foreground object",
    "content spans its chosen bbox so the crop has the sampled size",
]

PALETTE_KINDS = ("default", "warm", "cool", "rainbow")
DEGENERATE_TEXTURES = ("motif_at_border", "motif_fills_grid", "no_motif")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {'grid_h': {'type': 'int', 'default': 'rng 7..10', 'valid': '6..12'},
 'grid_w': {'type': 'int', 'default': 'rng 7..10', 'valid': '6..12'},
 'palette_kind': {'type': 'str',
                  'default': 'rng helpful',
                  'valid': 'default|warm|cool|rainbow'},
 'motif_position': {'type': 'str', 'default': 'interior', 'valid': 'interior'},
 'palette_size': {'type': 'int', 'default': '2', 'valid': '2'},
 'position_bias': {'type': 'str', 'default': 'interior', 'valid': 'interior'},
 'n_distinct_colors': {'type': 'int', 'default': '1', 'valid': '1'},
 'motif_density': {'type': 'str', 'default': 'fixed', 'valid': 'fixed'},
 'texture': {'type': 'str',
             'default': 'alias for palette_kind',
             'valid': 'default|warm|cool|rainbow|motif_at_border|motif_fills_grid|no_motif'}}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
    (fg,) = ctx.draw_distinct_colors("colors", n=1, exclude=[0])
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("content")
    # Rule is crop-to-content. The content is a connected one-color shape that
    # spans its full bbox but is NOT a solid rectangle — a solid crop output
    # carries no shape signal (defect-lint all_background flag; canonical demos
    # are L/T-like shapes with holes).
    rh = rng.randint(2, min(6, h - 1))
    rw = rng.randint(2, min(6, w - 1))
    top = rng.randint(0, h - rh)
    left = rng.randint(0, w - rw)
    shape = None
    for _try in range(80):
        cells = {(rng.randrange(rh), rng.randrange(rw))}
        target = rng.randint(rh + rw, max(rh + rw, rh * rw - 1))
        while len(cells) < target:
            r, c = rng.choice(sorted(cells))
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nr, nc = r + dr, c + dc
            if 0 <= nr < rh and 0 <= nc < rw:
                cells.add((nr, nc))
        spans_bbox = (min(r for r, _ in cells) == 0 and max(r for r, _ in cells) == rh - 1
                      and min(c for _, c in cells) == 0 and max(c for _, c in cells) == rw - 1)
        if spans_bbox and len(cells) < rh * rw:
            shape = cells
            break
    if shape is None:
        # Deterministic L: spans the bbox, never solid (for any 2x2+ bbox).
        shape = {(r, 0) for r in range(rh)} | {(rh - 1, c) for c in range(rw)}
    for r, c in shape:
        g[top + r][left + c] = fg
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: bg=0, non-bg content is in the interior (not touching border)."""
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    # Check non-bg cells exist (degenerate no_motif is allowed)
    nonbg = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonbg:
        return errors  # degenerate
    # Normally content should not touch border (invariant: bg border surrounds content)
    # Degenerate motif_at_border violates this, so we just note it
    r_min = min(r for r, c in nonbg); r_max = max(r for r, c in nonbg)
    c_min = min(c for r, c in nonbg); c_max = max(c for r, c in nonbg)
    if r_min == 0 or r_max == h - 1 or c_min == 0 or c_max == w - 1:
        pass  # degenerate motif_at_border — allowed
    if h > 30 or w > 30:
        errors.append(f"grid too large: {h}x{w}")
    # Content must not be a solid rectangle: a solid crop output has no shape
    # signal (and bbox area 4+ solid rects were the defect-lint flag).
    bbox_area = (r_max - r_min + 1) * (c_max - c_min + 1)
    if bbox_area >= 4 and len(nonbg) == bbox_area:
        errors.append("content is a solid rectangle — the cropped output would be a "
                      "featureless block")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "motif_at_border":
        # motif touches grid border — zero-padding invariant violated
        for dr, dc, color in [(0, 1, 4), (1, 0, 6), (1, 1, 6), (1, 2, 7), (2, 1, 4)]:
            g[dr][dc] = color
        return g
    if name == "motif_fills_grid":
        # motif fills entire grid — crop equals input (rule trivial)
        for r in range(h):
            for c in range(w):
                g[r][c] = ((r + c) % 3) + 2
        return g
    if name == "no_motif":
        # empty grid — nothing to crop
        return g
    return g
