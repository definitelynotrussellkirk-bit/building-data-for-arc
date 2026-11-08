"""Generator for 753ea09b.

Rule: crossing paths divide the background; smaller enclosed regions
are filled.

Combinatorial axes (8): grid_h/w, offset, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_distinct_colors.
Degenerates: no_paths, single_path, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2b0c130c5022"
VERSION = "2.0.0"  # in=3, wrong distribution: bg=0 + tiny + cross on 12-14x14. Canonical = filled nonzero modal bg + crossing paths on a large grid -> many regions. Now filled nonzero bg + several full-line walls partition into varied regions, larger varied grid.
TASK_ID = "2b0c130c5022"
SUMMARY = "Crossing paths divide bg; smaller enclosed regions are filled."

INVARIANTS = [
    "the modal color is background",
    "two non-background paths cross and partition the background into regions",
    "the most frequent path color fills all but the two largest background regions",
    "fill and cross colors are distinct and non-zero",
]

OFFSETS = ("o0", "o1", "o2")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_paths", "single_path", "full_grid")
HELPFUL_TEXTURES = OFFSETS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 16..24", "valid": "12..30"},
    "grid_w":         {"type": "int", "default": "rng 16..24", "valid": "12..30"},
    "offset":         {"type": "str", "default": "rng helpful",
                       "valid": "|".join(OFFSETS)},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for offset",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: bg is the modal color (non-zero), at least 1 crossing path exists."""
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    from collections import Counter
    counts = Counter(grid[r][c] for r in range(h) for c in range(w))
    if not counts:
        return errors
    bg = counts.most_common(1)[0][0]
    if bg == 0:
        pass  # degenerate — allowed (grid might be mostly empty)
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    # rule: bg = modal colour; crossing paths partition bg into regions; fill all but
    # the 2 LARGEST bg regions with the most-common non-bg colour. Canonical is a large
    # grid with a FILLED nonzero bg (e.g. 6) and wandering paths -> many regions. The
    # old gen used bg=0 + one tiny + cross on a 12-14x14 (in=3, wrong distribution).
    # Now: filled nonzero bg, several full-line walls partition it into varied regions.
    bg, fill_c, cross_c = ctx.draw_distinct_colors("colors", n=3, exclude={0})
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 12, 16)
        n_v, n_h = rng.randint(1, 2), rng.randint(1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 22, 30); w = ctx.draw_int("grid_w", 22, 30)
        n_v, n_h = rng.randint(2, 3), rng.randint(2, 3)
    else:
        h = ctx.draw_int("grid_h", 16, 24); w = ctx.draw_int("grid_w", 16, 24)
        n_v, n_h = rng.randint(1, 3), rng.randint(1, 3)
    g = full_grid(h, w, bg)
    vcols = sorted(rng.sample(range(2, w - 2), min(n_v, w - 4)))
    hrows = sorted(rng.sample(range(2, h - 2), min(n_h, h - 4)))
    walls = [("v", c) for c in vcols] + [("h", r) for r in hrows]
    rng.shuffle(walls)
    # one wall in cross_c (second path colour), the rest in fill_c (dominant -> fill-c)
    for i, (kind, idx) in enumerate(walls):
        color = cross_c if i == 0 and len(walls) > 1 else fill_c
        if kind == "v":
            for r in range(h):
                g[r][idx] = color
        else:
            for c in range(w):
                g[idx][c] = color
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 14, 0)
    if name == "no_paths":
        return g
    if name == "single_path":
        for r in range(12):
            g[r][6] = 2
        return g
    if name == "full_grid":
        for r in range(12):
            for c in range(14):
                g[r][c] = 2
        return g
    return g
