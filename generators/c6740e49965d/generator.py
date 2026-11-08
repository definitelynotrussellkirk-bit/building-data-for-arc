"""Generator for arc_additional_puzzle_bank_volume6:H36.

Rule: among the non-color-8 objects that are exact rectangular FRAMES,
paint color 2 on the cells strictly inside ALL of them (the intersection
of their interiors).

This generator draws K NESTED concentric hollow frames (distinct colors,
gaps so no border crosses another) -- their interior intersection is the
innermost frame's interior, which the rule fills with 2.

Combinatorial axes: grid size, frame count, the nested frame
sizes/margins/colors, and position.
Degenerates: no_frames, single_frame, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "c6740e49965d"
VERSION = "2.0.1"  # diversity: random K nested frames + sizes/margins/colors (was fixed ~20)
TASK_ID = "c6740e49965d"
SUMMARY = (
    "0-bg grid (size varies) with K (2-4) NESTED concentric hollow FRAMES of "
    "distinct non-8 colors (gaps so no border crosses). Rule: paint color 2 "
    "on the cells strictly inside every frame -- the innermost frame's "
    "interior. The grid size, frame count, nested sizes/margins/colors and "
    "position vary freely (was a fixed nesting, ~20 distinct)."
)

INVARIANTS = [
    "every frame is an exact hollow rectangle (cells == bbox border), color != 8",
    "frames are nested with gaps so no border is broken by another",
    "the painted region is the intersection of all frame interiors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "single_frame", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "varies"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "varies"},
    "n_frames":       {"type": "int", "default": "varies", "valid": "2..4"},
    "core_size":      {"type": "int", "default": "varies", "valid": "3..6"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "nested_center", "valid": "nested_center"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_frames|single_frame|full_grid"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        kr, cr = (2, 2), (3, 4)
    elif difficulty == "hard":
        kr, cr = (3, 4), (3, 6)
    else:
        kr, cr = (2, 3), (3, 5)

    for _attempt in range(40):
        K = rng.randint(*kr)
        # innermost box (>=3 so it has an interior)
        ih = rng.randint(*cr); iw = rng.randint(*cr)
        # boxes as (r1,c1,r2,c2), innermost first; expand outward by >=2 margins
        boxes = [(0, 0, ih - 1, iw - 1)]
        for _ in range(K - 1):
            r1, c1, r2, c2 = boxes[-1]
            mt = rng.randint(2, 3); ml = rng.randint(2, 3)
            mb = rng.randint(2, 3); mr = rng.randint(2, 3)
            boxes.append((r1 - mt, c1 - ml, r2 + mb, c2 + mr))
        # normalize so the outer box starts at (0,0)
        or1 = boxes[-1][0]; oc1 = boxes[-1][1]
        boxes = [(r1 - or1, c1 - oc1, r2 - or1, c2 - oc1) for (r1, c1, r2, c2) in boxes]
        oh = boxes[-1][2] + 1; ow = boxes[-1][3] + 1

        h = rng.randint(oh + 2, oh + 6); w = rng.randint(ow + 2, ow + 6)
        if h > 30 or w > 30:
            continue
        top = rng.randint(0, h - oh); left = rng.randint(0, w - ow)

        colors = rng.sample([1, 3, 4, 5, 6, 7, 9], K)
        g = full_grid(h, w, 0)
        for (r1, c1, r2, c2), col in zip(boxes, colors):
            draw_frame(g, top + r1, left + c1, top + r2, left + c2, col)
        return g

    return g   # fallback (rare)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=2 distinct non-{0,8} frame colors present (nested frames); no color-8 cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    eights = sum(grid[r][c] == 8 for r in range(h) for c in range(w))
    if eights > 0:
        errors.append(f"found {eights} color-8 cells (frames must use non-8 colors)")
    frame_colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] not in (0, 8)}
    if len(frame_colors) < 2:
        errors.append(f"expected >=2 distinct frame colors (nested frames), found {len(frame_colors)}")
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 11, 0)
    draw_frame(g, 1, 1, 9, 9, 3)
    draw_frame(g, 3, 3, 7, 7, 4)
    if name == "no_frames":
        return full_grid(8, 8, 0)
    if name == "single_frame":
        g2 = full_grid(9, 9, 0)
        draw_frame(g2, 1, 1, 7, 7, 3)
        return g2
    if name == "full_grid":
        return full_grid(8, 8, 5)
    return g
