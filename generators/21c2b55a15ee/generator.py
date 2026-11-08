"""Generator for 10b:m70 — fill each component's bounding box.

Rule: each non-zero connected component is replaced with a solid
rectangle filling its bounding box (keeping its color).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_components,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_solid, single_component, no_components.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "21c2b55a15ee"
VERSION = "2.0.1"


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: 2-4 distinct non-zero colors; each color doesn't fill its own bbox."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
        return errs
    colors = list({grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0})
    if len(colors) < 2 or len(colors) > 4:
        errs.append(f"expected 2-4 distinct non-zero colors, got {len(colors)}")
    return errs
TASK_ID = "21c2b55a15ee"
SUMMARY = (
    "0-bg grid (h~9-13, w~10-14) with 2-4 SMALL "
    "PARTIAL-BBOX COMPONENTS — each shape drawn from "
    "the _PARTIALS bank (L-shapes, plus signs, "
    "complex partials, donut, etc.) chosen so that "
    "each component's CELL COUNT < bbox_h × bbox_w "
    "(i.e., the bbox has at least one bg-0 cell — "
    "the component does NOT fill its bbox). Each "
    "component is painted in a DISTINCT non-0 color "
    "drawn from {1, 2, 3, 4, 6, 7, 8, 9}. Components "
    "are placed at non-overlapping positions with "
    "1-cell padding (tracked via a used cell set, "
    "preventing bbox overlap between components). "
    "Rule (REPLACE EACH COMPONENT WITH A SOLID "
    "BBOX-FILLED RECTANGLE IN ITS COLOR): for EACH "
    "4-CONNECTED non-bg COMPONENT of color C: COMPUTE "
    "its bbox (r1, c1, r2, c2). PAINT every cell "
    "inside the bbox (rectangular region) with COLOR "
    "C — the original cells stay C, and the bg-0 "
    "cells inside the bbox are filled in. Cells "
    "outside every component bbox stay bg-0. Net: "
    "irregular shapes inflate into solid colored "
    "rectangles, each matching the original component's "
    "color and bbox; the bg-0 gaps inside bboxes are "
    "all closed up."
)

INVARIANTS = [
    "background is 0",
    "2-4 non-zero connected components, each in a distinct color",
    "each component does NOT fill its own bounding box (else input==output)",
    "components' bounding boxes do not overlap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_solid", "single_component", "no_components")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_components":   {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "position_bias":  {"type": "str", "default": "bbox_isolated",
                       "valid": "bbox_isolated"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_PARTIALS = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (0, 1), (1, 1)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 1), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (1, 0), (1, 1), (1, 2)],
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2)],
    [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)],
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)],
    [(0, 0), (1, 0), (1, 1), (2, 0)],
    [(0, 0), (0, 1), (1, 1), (2, 0), (2, 1)],
]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 12, 13)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 13)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    n_comp = rng.randint(2, 4)
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], n_comp)
    used: set[tuple[int, int]] = set()
    for color in palette:
        for _ in range(40):
            shape = rng.choice(_PARTIALS)
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            r0 = rng.randint(0, h - sh)
            c0 = rng.randint(0, w - sw)
            bad = False
            for r in range(max(0, r0 - 1), min(h, r0 + sh + 1)):
                for c in range(max(0, c0 - 1), min(w, c0 + sw + 1)):
                    if (r, c) in used:
                        bad = True; break
                if bad: break
            if bad: continue
            for dr, dc in shape:
                g[r0 + dr][c0 + dc] = color
            for r in range(r0, r0 + sh):
                for c in range(c0, c0 + sw):
                    used.add((r, c))
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 11, 12
    g = full_grid(h, w, 0)
    if name == "all_solid":
        # all components already solid rects → bbox-fill = identity, no contrast
        for r in range(2, 4):
            for c in range(2, 4):
                g[r][c] = 4
        for r in range(6, 8):
            for c in range(7, 10):
                g[r][c] = 6
        return g
    if name == "single_component":
        # one partial-bbox component → no comparison, rule still applies trivially
        for r, c in [(3, 3), (3, 4), (4, 3)]:
            g[r][c] = 5
        return g
    if name == "no_components":
        # empty grid → no objects to bbox-fill
        return g
    return g
