"""Generator for arc_additional_puzzles_21_set12_bundle:E84 — fill largest-interior frame.

Several perfect rectangular frames are present; only the frame with
the largest interior area is filled by the canonical rule.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_frames (no rectangular frames → rule's selector finds
nothing), single_frame (only one frame → trivially largest, no
contrast), tied_largest (≥2 frames share max interior area → "largest"
is ambiguous, tie-break decides).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "963fa64ff87f"
VERSION = "1.1.1"  # add self_check
TASK_ID = "963fa64ff87f"
SUMMARY = "Two or three non-overlapping rectangular frames with a unique largest interior."

INVARIANTS = [
    "background is 0",
    "all nonzero objects are perfect rectangular frames",
    "frame interiors are zero",
    "one frame has a strictly largest interior area",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "single_frame", "tied_largest")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 9..13", "valid": "7..16"},
    "grid_w":            {"type": "int", "default": "rng 11..16", "valid": "8..18"},
    "frame_count":       {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "palette_size":      {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "position_bias":     {"type": "str", "default": "frames_distinct_interior_areas",
                          "valid": "frames_distinct_interior_areas"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|no_frames|single_frame|tied_largest"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 non-zero color with ≥8 cells (at least one valid frame perimeter)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    from collections import Counter
    counts = Counter(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if not counts:
        return ["no non-zero cells (no frames placed)"]
    big = [c for c, n in counts.items() if n >= 8]
    if not big:
        return [f"no frame color has ≥8 cells; max is {max(counts.values()) if counts else 0}"]
    return []


def _overlaps_with_margin(a, b, margin=1):
    ar1, ac1, ar2, ac2 = a
    br1, bc1, br2, bc2 = b
    return not (
        ar2 + margin < br1
        or br2 + margin < ar1
        or ac2 + margin < bc1
        or bc2 + margin < ac1
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        frame_count = ctx.draw_int("frame_count", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 15, 16)
        frame_count = ctx.draw_int("frame_count", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 11, 16)
        frame_count = ctx.draw_int("frame_count", 2, 3)
    colors = ctx.draw_distinct_colors("colors", n=frame_count, exclude={0})
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    frames = []
    used_areas = set()

    largest_h = rng.randint(6, min(9, h - 2))
    largest_w = rng.randint(6, min(10, w - 2))
    largest = (
        rng.randint(1, h - largest_h - 1),
        rng.randint(1, w - largest_w - 1),
    )
    bbox = (largest[0], largest[1], largest[0] + largest_h - 1, largest[1] + largest_w - 1)
    draw_frame(g, *bbox, colors[0])
    frames.append(bbox)
    used_areas.add((largest_h - 2) * (largest_w - 2))

    for color in colors[1:]:
        placed = False
        for _ in range(300):
            rh = rng.randint(3, min(5, h - 2))
            rw = rng.randint(3, min(6, w - 2))
            area = (rh - 2) * (rw - 2)
            if area in used_areas or area >= max(used_areas):
                continue
            r1 = rng.randint(0, h - rh)
            c1 = rng.randint(0, w - rw)
            bbox = (r1, c1, r1 + rh - 1, c1 + rw - 1)
            if all(not _overlaps_with_margin(bbox, other) for other in frames):
                draw_frame(g, *bbox, color)
                frames.append(bbox)
                used_areas.add(area)
                placed = True
                break
        if not placed:
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 11, 14
    g = full_grid(h, w, 0)
    if name == "no_frames":
        # No frames — rule's selector finds nothing.
        for r, c in [(3, 3), (3, 4), (4, 3)]: g[r][c] = 4
        return g
    if name == "single_frame":
        # Only one frame — trivially largest.
        draw_frame(g, 2, 2, 7, 9, 4)
        return g
    if name == "tied_largest":
        # Two frames share max interior area.
        draw_frame(g, 1, 1, 4, 5, 4)
        draw_frame(g, 6, 7, 9, 11, 6)   # same interior area
        return g
    return g
