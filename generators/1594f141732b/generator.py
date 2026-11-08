"""Generator for arc_puzzle_bank_21_set3:S3_M2 — frame cross from inner dot.

Rule: each frame contains exactly one red dot strictly inside it. The
output draws a cross through that dot up to the frame walls.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_frame, no_dot, dot_on_frame.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "1594f141732b"
VERSION = "2.2.1"  # reverse-diversity: 1-3 dots per frame (rule paints a cross
# per interior dot in the FRAME's color); exercises multi-dot branch. Fixed
# SUMMARY (cross is the frame color, not red).
TASK_ID = "1594f141732b"

SUMMARY = (
    "0-bg grid (h~14-19, w~"
    "15-21) with 1-2 "
    "FRAMES, each a RECT-"
    "OUTLINE of size 7-9 "
    "× 7-10 in a DISTINCT "
    "color from {1, 3, 4, "
    "5, 6, 7, 8, 9}. EACH "
    "FRAME contains "
    "EXACTLY ONE COLOR-2 "
    "(red) DOT cell "
    "strictly inside (≥2-"
    "cell padding from "
    "frame borders). "
    "Frames placed non-"
    "overlapping with 1-"
    "cell padding. Rule "
    "(DRAW CROSS THROUGH "
    "EACH FRAME's INNER "
    "DOT UP TO WALLS): "
    "For EACH FRAME and "
    "its INTERIOR DOT at "
    "(dr, dc): PAINT a "
    "CROSS (horizontal + "
    "vertical line) "
    "through (dr, dc) "
    "extending in all 4 "
    "directions until "
    "hitting the FRAME's "
    "INNER WALLS. Paint "
    "in COLOR-2. Frame "
    "outlines stay. Net: "
    "each red dot "
    "becomes a red cross "
    "stretching across "
    "its frame."
)

INVARIANTS = [
    "background is 0",
    "each non-red frame is an exact rectangular outline",
    "each frame contains 1-3 singleton red dots strictly inside it (none 4-adjacent)",
    "the red dot is separated from the frame border by at least one blank cell",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frame", "no_dot", "dot_on_frame")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 14..17", "valid": "12..20"},
    "grid_w":         {"type": "int", "default": "rng 15..19", "valid": "12..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "frame_with_inner_dot",
                       "valid": "frame_with_inner_dot"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_frame|no_dot|dot_on_frame"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, at least one non-red frame outline, at least one red dot."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    reds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    frames = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 2)]
    texture = (meta or {}).get("texture", "")
    if texture not in ("no_frame",) and not frames:
        errs.append("no frame cells (non-0, non-2)")
    if texture not in ("no_dot",) and not reds:
        errs.append("no red (color-2) dot cells")
    return errs


def _clear(g, r1, c1, r2, c2) -> bool:
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 14, 14)
        w = ctx.draw_int("grid_w", 15, 15)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 17, 19)
        w = ctx.draw_int("grid_w", 19, 21)
    else:
        h = ctx.draw_int("grid_h", 14, 17)
        w = ctx.draw_int("grid_w", 15, 19)
    rng = ctx.draw_rng("layout")
    n_frames = rng.randint(1, 2)
    # Two frames are 7×7 at minimum; with the 1-cell separation _clear
    # enforces they only coexist if the grid can stack them vertically
    # (h≥17) or tile them horizontally (w≥17). The old code asked for 2 on
    # any grid and then raised "could not place a separated frame" (~41%).
    # Drop to one frame on small grids; when keeping two, cap the size along
    # the packing axis so a non-overlapping layout provably exists.
    if n_frames == 2 and h < 17 and w < 17:
        n_frames = 1
    colors = rng.sample([1, 3, 4, 5, 6, 7, 8, 9], n_frames)
    if n_frames == 2 and h >= 17:
        max_rh, max_rw = min(9, (h - 3) // 2), min(10, w - 2)
    elif n_frames == 2:
        max_rh, max_rw = min(9, h - 2), min(10, (w - 3) // 2)
    else:
        max_rh, max_rw = min(9, h - 2), min(10, w - 2)

    def _place(gg, color):
        for _ in range(120):
            rh = rng.randint(7, max_rh)
            rw = rng.randint(7, max_rw)
            r1 = rng.randint(1, h - rh - 1)
            c1 = rng.randint(1, w - rw - 1)
            r2, c2 = r1 + rh - 1, c1 + rw - 1
            if not _clear(gg, r1, c1, r2, c2):
                continue
            draw_frame(gg, r1, c1, r2, c2, color)
            # Place 1-3 interior red dots; keep each a singleton (no two dots
            # 4-adjacent, so each stays its own size-1 component) and not on a
            # cell already taken by another dot.
            interior = [(r, c) for r in range(r1 + 2, r2 - 1)
                        for c in range(c1 + 2, c2 - 1)]
            rng.shuffle(interior)
            n_dots = rng.randint(1, 3)
            placed = []
            for (r, c) in interior:
                if len(placed) >= n_dots:
                    break
                if any(abs(r - pr) + abs(c - pc) <= 1 for pr, pc in placed):
                    continue
                placed.append((r, c))
            if not placed:
                placed = [interior[0]] if interior else []
            for (r, c) in placed:
                gg[r][c] = 2
            return True
        return False

    # Greedy per-frame placement can wedge frame 1 in the middle and starve
    # frame 2; reset the whole grid and retry the full arrangement instead.
    for _outer in range(200):
        g = full_grid(h, w, 0)
        if all(_place(g, color) for color in colors):
            return g
    raise ValueError("could not place separated frames")


def _draw_from_degenerate(name, rng):
    h, w = 14, 15
    g = full_grid(h, w, 0)
    if name == "no_frame":
        # Red dots but no frame — rule has no boundary to draw cross
        # through; cross extent is undefined.
        g[5][7] = 2
        return g
    if name == "no_dot":
        # Frame but no inner dot — rule has no cross center.
        draw_frame(g, 2, 2, 8, 12, 4)
        return g
    if name == "dot_on_frame":
        # Frame + red dot but the dot is ON the frame wall (not strictly
        # inside) — rule's "inside the frame" precondition fails.
        draw_frame(g, 2, 2, 8, 12, 4)
        g[2][7] = 2
        return g
    return g
