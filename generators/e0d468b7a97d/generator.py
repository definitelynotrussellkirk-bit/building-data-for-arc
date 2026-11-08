"""Generator for arc_additional_puzzles_21_set20_bundle:E138 -- crop inside 9 frame.

Combinatorial axes (8): grid_h, grid_w, palette_kind, frame_h,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_frame, frame_open_side, multiple_frames.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e0d468b7a97d"
VERSION = "1.3.0"  # clean (crop inside 9-frame, full + corners styles) but bounded; widen frames/grids and interior content.
TASK_ID = "e0d468b7a97d"
SUMMARY = "Color-9 markers (either 4 corners or a full rectangular frame) define a bbox. Rule outputs the INTERIOR rectangle: rows (r1+1)..(r2-1), cols (c1+1)..(c2-1), where (r1,c1,r2,c2) is the bbox of all 9-cells. The interior contains content cells; the 9-cells themselves and the cells outside the bbox are dropped."

# Rivals: 'output is input' refuted by any demo (output is small).
# 'include the 9-frame in output' refuted by any demo (output strips
# 9 border). 'output bbox excluding only outer ring' is correct but
# can be stated as crop. 'output entire grid' refuted by any demo
# with smaller crop. 'output without content' refuted by any demo
# with interior cells present. 3 demos with varied interior content
# cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "color 9 marks the full outside frame of the target crop",
    "frame interior contains nonzero content",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frame", "frame_open_side", "multiple_frames")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "8..15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "frame_h":        {"type": "int", "default": "rng 4..6", "valid": "3..8"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "interior", "valid": "interior"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = rng.randint(7, 10); w = rng.randint(8, 11)
        fh = rng.randint(4, 5); fw = rng.randint(4, 6)
        n_inner = rng.randint(2, 4)
    elif difficulty == "hard":
        h = rng.randint(14, 19); w = rng.randint(15, 22)
        fh = rng.randint(6, 11); fw = rng.randint(7, 13)
        n_inner = rng.randint(6, 14)
    else:
        h = rng.randint(9, 14); w = rng.randint(10, 16)
        fh = rng.randint(5, 8); fw = rng.randint(5, 9)
        n_inner = rng.randint(3, 8)
    if fh > h - 2: fh = h - 2
    if fw > w - 2: fw = w - 2
    inner_colors = rng.sample([c for c in range(1, 10) if c != 9], min(4, n_inner))
    g = full_grid(h, w, 0)
    top = rng.randint(1, h - fh - 1)
    left = rng.randint(1, w - fw - 1)
    # Sometimes full frame, sometimes 4 corners only
    frame_style = rng.choice(["full", "corners"])
    if frame_style == "full":
        for r in range(top, top + fh):
            g[r][left] = 9
            g[r][left + fw - 1] = 9
        for c in range(left, left + fw):
            g[top][c] = 9
            g[top + fh - 1][c] = 9
    else:
        g[top][left] = 9
        g[top][left + fw - 1] = 9
        g[top + fh - 1][left] = 9
        g[top + fh - 1][left + fw - 1] = 9
    # Fill interior with sparse content (avoid 9 to keep bbox unchanged).
    interior_cells = [(r, c) for r in range(top + 1, top + fh - 1)
                      for c in range(left + 1, left + fw - 1)]
    rng.shuffle(interior_cells)
    for (r, c) in interior_cells[:n_inner]:
        g[r][c] = rng.choice(inner_colors)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "no_frame":
        # no color-9 frame → rule has no anchor for cropping
        for r, c, v in [(2, 3, 4), (4, 5, 6), (6, 7, 4)]:
            g[r][c] = v
        return g
    if name == "frame_open_side":
        # frame is missing one side → bbox of 9-cells is fine but enclosure invariant breaks
        top, left, fh, fw = 2, 2, 5, 6
        for r in range(top, top + fh):
            g[r][left] = 9
            g[r][left + fw - 1] = 9
        for c in range(left, left + fw):
            g[top + fh - 1][c] = 9  # top side missing
        g[top + 1][left + 1] = 4
        g[top + 1][left + fw - 2] = 6
        return g
    if name == "multiple_frames":
        # two color-9 frames → ambiguous which to crop
        for top, left, fh, fw, c1 in [(1, 1, 4, 4, 4), (5, 6, 4, 4, 6)]:
            for r in range(top, top + fh):
                g[r][left] = 9
                g[r][left + fw - 1] = 9
            for c in range(left, left + fw):
                g[top][c] = 9
                g[top + fh - 1][c] = 9
            g[top + 1][left + 1] = c1
        return g
    return g



def _bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the crop-inside-9-marker task.

    The canonical rule crops the bbox of all 9-cells and strips that border.
    A valid default instance may use either a full rectangular 9-frame or only
    the four 9-corners, but it must not emit stray/interior 9s or an empty crop.
    """
    msgs: list[str] = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    markers = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    if not markers:
        return ["no color-9 crop markers"]
    r1, c1, r2, c2 = _bbox(markers)
    if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
        msgs.append("9-marker bbox too small to have a nonempty interior crop")
    marker_set = set(markers)
    corners = {(r1, c1), (r1, c2), (r2, c1), (r2, c2)}
    missing = sorted(corners - marker_set)
    if missing:
        msgs.append(f"9-marker bbox corner(s) missing: {missing[:4]}")
    perimeter = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
                 if r in (r1, r2) or c in (c1, c2)}
    if not marker_set.issubset(perimeter):
        msgs.append("color-9 marker appears inside the crop interior")
    if len(marker_set) not in (4, len(perimeter)):
        msgs.append("9-markers are neither exactly four corners nor a full rectangular frame")
    interior = [grid[r][c] for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)]
    if not any(v not in (0, 9) for v in interior):
        msgs.append("crop interior contains no content cells")
    if any(v == 9 for v in interior):
        msgs.append("crop interior contains color 9, which changes the bbox anchor")
    return msgs
