"""Generator for arc_additional_puzzle_bank_volume19:M133 — Fill 5-frame interior with single marker color.

Rule: each closed 5-rect frame contains exactly one non-{0,5} marker
color inside; fill all 0-cells inside with that marker color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_frames,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_frames, empty_interior, multiple_markers.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.grid import draw_rect_outline

GENERATOR_ID = "b07ab22c1245"
VERSION = "2.0.2"
TASK_ID = "b07ab22c1245"
SUMMARY = (
    "0-bg grid (h ∈ 9-11, w ∈ 12-14) "
    "with: (a) TWO HOLLOW COLOR-5 "
    "(GRAY) RECTANGULAR FRAMES, each "
    "height 4-5 and width 4, drawn via "
    "draw_rect_outline at FIXED "
    "corner regions: FRAME 1 at "
    "top-left (1, 1)..(fr, fc), "
    "FRAME 2 at bottom-right "
    "(h-fr2-1, w-fc2-1)..(h-2, "
    "w-2); (b) IN EACH FRAME'S "
    "INTERIOR: ONE MARKER CELL of a "
    "distinct non-{0, 5} color "
    "drawn from {2, 3, 4, 6, 7, 8} "
    "(palette[0] for frame 1, "
    "palette[1] for frame 2), at a "
    "random interior position; "
    "(c) ONE COLOR-6 NOISE CELL at "
    "(0, w-1). Rule (FOR EACH "
    "CLOSED 5-FRAME, FILL EVERY "
    "0-CELL INSIDE THE FRAME'S "
    "INTERIOR WITH THE MARKER "
    "COLOR INSIDE THAT FRAME): "
    "EXTRACT every COLOR-5 frame "
    "outline. For EACH frame: "
    "READ the unique non-{0, 5} "
    "MARKER COLOR inside. PAINT "
    "every interior 0-cell with "
    "the marker color. The frame "
    "outline stays gray; the "
    "marker cell stays its color. "
    "Net: each frame's interior "
    "floods with its marker "
    "color; gray outlines and "
    "noise cells preserved."
)

INVARIANTS = [
    "exactly 2 closed separated 5-frames, each at least 4x4",
    "each frame interior has exactly one marker cell of distinct non-{0,5} color",
    "each frame interior also has at least one 0-cell, so the fill rule is demonstrated",
    "frames do not overlap or 4-touch into a single gray component",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "empty_interior", "multiple_markers")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..12"},
    "grid_w":         {"type": "int", "default": "rng 12..14", "valid": "10..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_frames":       {"type": "int", "default": "2", "valid": "2..2"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "two_5frames_with_marker",
                       "valid": "two_5frames_with_marker"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _components_of_value(grid, value):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != value or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp = []
            while stack:
                rr, cc = stack.pop()
                comp.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == value and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(comp)
    return comps


def _frame_bbox(comp):
    rows = [r for r, _ in comp]
    cols = [c for _, c in comp]
    return min(rows), min(cols), max(rows), max(cols)


def _outline_cells(r0, c0, r1, c1):
    cells = set()
    for c in range(c0, c1 + 1):
        cells.add((r0, c))
        cells.add((r1, c))
    for r in range(r0, r1 + 1):
        cells.add((r, c0))
        cells.add((r, c1))
    return cells


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: two separated gray frames, one interior marker each, and fillable 0-cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_frames",):
        return []
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")

    frames = []
    comps = _components_of_value(grid, 5)
    if len(comps) != 2:
        errs.append(f"expected exactly two separated color-5 frame components, found {len(comps)}")
        return errs

    marker_colors = []
    for comp in comps:
        r0, c0, r1, c1 = _frame_bbox(comp)
        fh, fw = r1 - r0 + 1, c1 - c0 + 1
        outline = _outline_cells(r0, c0, r1, c1)
        if fh < 4 or fw < 4:
            errs.append(f"frame too small: {fh}x{fw}")
        if set(comp) != outline:
            errs.append(f"color-5 component is not a clean rectangular outline: bbox={fh}x{fw}")
            continue
        interior = [(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)]
        markers = [(r, c, grid[r][c]) for r, c in interior if grid[r][c] not in (0, 5)]
        zeros = [(r, c) for r, c in interior if grid[r][c] == 0]
        if len(markers) != 1:
            errs.append(f"frame interior expected exactly one marker, found {len(markers)}")
        else:
            marker_colors.append(markers[0][2])
        if not zeros:
            errs.append("frame interior has no 0-cells to fill; rule would be hidden")
        frames.append((r0, c0, r1, c1))

    if len(marker_colors) == 2 and marker_colors[0] == marker_colors[1]:
        errs.append("frame marker colors should be distinct")
    return errs

def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 12, 13)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 13, 14)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 12, 14)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    fr = rng.randint(4, 5); fc = 4
    draw_rect_outline(g, 1, 1, fr, fc, 5)
    palette = rng.sample([2, 3, 4, 6, 7, 8], 2)
    g[1 + rng.randint(1, fr - 2)][1 + rng.randint(1, fc - 2)] = palette[0]
    fr2 = rng.randint(4, 5); fc2 = 4
    draw_rect_outline(g, h - fr2 - 1, w - fc2 - 1, fr2, fc2, 5)
    g[h - fr2 - 1 + rng.randint(1, fr2 - 2)][w - fc2 - 1 + rng.randint(1, fc2 - 2)] = palette[1]
    g[0][w - 1] = 6
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 13
    g = full_grid(h, w, 0)
    if name == "no_frames":
        # markers without 5-frames → no boundary to fill within
        g[3][3] = 4
        g[6][9] = 6
        return g
    if name == "empty_interior":
        # 5-frames with no marker → "exactly one marker" precondition fails
        draw_rect_outline(g, 1, 1, 4, 4, 5)
        draw_rect_outline(g, 5, 7, 4, 4, 5)
        return g
    if name == "multiple_markers":
        # frame interior contains 2+ different colors → ambiguous fill color
        draw_rect_outline(g, 1, 1, 4, 4, 5)
        g[2][2] = 4
        g[3][3] = 6  # both inside same frame
        draw_rect_outline(g, 5, 7, 4, 4, 5)
        g[6][8] = 7
        return g
    return g
