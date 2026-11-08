"""Generator for arc_additional_puzzle_bank_volume7:M44 — Fill 4-frame interior with 8 if width = count of 2s.

Rule: k = count of 2-cells. For each 4-frame (hollow rect), if its width
== k, paint interior cells with 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, k,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_2s, no_matching_frame, all_frames_match.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "98f448f4ed98"
VERSION = "2.1.0"  # strengthen frame-width self_check
TASK_ID = "98f448f4ed98"
SUMMARY = (
    "0-bg grid (h~9-11, w~"
    "13-15) with: (a) ROW "
    "0 holds k COLOR-2 "
    "(red) CELLS (k=4-5) "
    "at random distinct "
    "columns; (b) TWO "
    "HOLLOW COLOR-4 "
    "(yellow) RECT-OUTLINE "
    "FRAMES — FRAME A at "
    "(1..5, 1..k) with "
    "WIDTH = k (matches); "
    "FRAME B at (2..6, "
    "w-other_k-1..w-2) "
    "with WIDTH = k+1 or "
    "k-1 (mismatches). "
    "Rule (FILL 4-FRAME "
    "INTERIOR WITH 8 IF "
    "FRAME WIDTH EQUALS k)"
    ": COUNT k = number of "
    "COLOR-2 cells in row "
    "0. For EACH COLOR-4 "
    "FRAME: if frame WIDTH "
    "equals k, FILL its "
    "INTERIOR cells with "
    "COLOR-8 (cyan). "
    "Non-matching frames "
    "stay empty. Frame "
    "outlines stay 4. "
    "Net: only the frame "
    "whose width matches "
    "the red count fills "
    "with cyan."
)

INVARIANTS = [
    "row 0 has between 2 and 5 cells of color 2",
    "2 closed 4-frames with widths k and !=k",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_2s", "no_matching_frame", "all_frames_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 13..15", "valid": "11..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "k":              {"type": "int", "default": "rng 4..5", "valid": "3..6"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "row0_2s_with_2_4frames",
                       "valid": "row0_2s_with_2_4frames"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_2s|no_matching_frame|all_frames_match"},
}




def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify exactly one frame width matches the row-0 count of 2s."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    count2_row0 = sum(1 for v in grid[0] if v == 2)
    errs: list[str] = []
    if count2_row0 > 0 and not (2 <= count2_row0 <= 5):
        errs.append(f"row 0 has {count2_row0} color-2 cells (expected 2-5 or 0 for degenerate)")
    seen: set[tuple[int, int]] = set()
    frame_widths: list[int] = []
    for r0 in range(h):
        for c0 in range(w):
            if (r0, c0) in seen or grid[r0][c0] != 4:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == 4:
                        seen.add((nr, nc)); stack.append((nr, nc))
            rs = [r for r, _ in cells]
            cs = [c for _, c in cells]
            rr0, rr1, cc0, cc1 = min(rs), max(rs), min(cs), max(cs)
            border = {(r, c) for r in range(rr0, rr1 + 1) for c in range(cc0, cc1 + 1)
                      if r in (rr0, rr1) or c in (cc0, cc1)}
            if set(cells) != border or rr1 - rr0 + 1 < 3 or cc1 - cc0 + 1 < 3:
                errs.append(f"color-4 component at {(rr0, cc0, rr1, cc1)} is not a hollow frame")
            frame_widths.append(cc1 - cc0 + 1)
    if count2_row0 > 0:
        matches = sum(1 for fw in frame_widths if fw == count2_row0)
        if matches != 1:
            errs.append(f"expected exactly one frame width to match k={count2_row0}, found {matches}")
        if len(frame_widths) != 2:
            errs.append(f"expected exactly two color-4 frames, found {len(frame_widths)}")
    return sorted(set(errs))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 13, 14)
        k = ctx.draw_int("k", 4, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 14, 15)
        k = ctx.draw_int("k", 5, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 13, 15)
        k = ctx.draw_int("k", 4, 5)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    cols = list(range(w)); rng.shuffle(cols)
    for c in cols[:k]:
        g[0][c] = 2
    # Frame width k (matching)
    draw_frame(g, 1, 1, 5, 1 + k - 1, 4)
    # Frame width different (k+1 or k-1)
    other_k = k + 1 if k < 5 else k - 1
    draw_frame(g, 2, w - other_k - 1, 6, w - 2, 4)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 14
    g = full_grid(h, w, 0)
    if name == "no_2s":
        # row 0 has no 2-cells → k=0, no frame matches width 0
        draw_frame(g, 1, 1, 5, 4, 4)
        draw_frame(g, 2, w - 6, 6, w - 2, 4)
        return g
    if name == "no_matching_frame":
        # k=4 but neither frame is width-4 → rule never fires
        for c in range(4): g[0][c] = 2   # k = 4
        draw_frame(g, 1, 1, 5, 3, 4)              # width 3
        draw_frame(g, 2, w - 7, 6, w - 2, 4)      # width 6
        return g
    if name == "all_frames_match":
        # both frames have width = k → both interiors get filled
        for c in range(4): g[0][c] = 2   # k = 4
        draw_frame(g, 1, 1, 5, 4, 4)              # width 4
        draw_frame(g, 2, w - 5, 6, w - 2, 4)      # width 4
        return g
    return g
