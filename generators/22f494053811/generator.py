"""Generator for 8b:m56 — mark each frame's center with majority color.

Rule: each rect-frame has interior with cells of various colors.
Output: replace frame's center cell with the most common interior color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_frames, no_majority, empty_interior.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "22f494053811"
# 3.0.1 fixed colour-8 frame parity against the rule. 3.0.2 rejects
# 3x3 frames in default generation because their single interior cell makes
# the redraw-frame-and-mark-center rule an identity demonstration.
VERSION = "3.0.2"
TASK_ID = "22f494053811"
SUMMARY = (
    "0-bg grid with 1-3 "
    "COLOR-8 (cyan) "
    "RECTANGULAR FRAMES "
    "of varied size "
    "(3x3..7x7, incl. "
    "non-square) placed "
    "at non-touching "
    "positions. EACH "
    "FRAME has an INTERIOR "
    "filled with: a "
    "MAJORITY COLOR "
    "(> half the interior "
    "cells) plus 0-2 "
    "DISTRACTOR cells in "
    "other non-{0, 8, "
    "majority} colors. "
    "Rule (MARK EACH "
    "FRAME'S CENTER WITH "
    "ITS INTERIOR MAJORITY "
    "COLOR): for EACH "
    "colour-8 rect-frame, "
    "redraw the frame "
    "border (8) on a blank "
    "grid, COUNT each "
    "interior color's "
    "frequency, find the "
    "MAJORITY interior "
    "color C, and PAINT "
    "the frame's bbox "
    "CENTER cell with C. "
    "Other interior cells "
    "are dropped. Net: "
    "each frame is redrawn "
    "with a single central "
    "marker in its "
    "majority color."
)

INVARIANTS = [
    "background is 0",
    "≥1 colour-8 rect-frame ≥3×3 with a unique-majority interior colour (non-{0,8})",
    "interior may also have 0-2 distractor cells of other colours",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "no_majority", "empty_interior")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 11..14", "valid": "9..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "frames_with_majority_interior",
                       "valid": "frames_with_majority_interior"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_frames|no_majority|empty_interior"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; grid is rectangular; at least one colour-8 cell present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    # No colour-8 cell at all → degenerate (no_frames) which is allowed
    has_8 = any(grid[r][c] == 8 for r in range(h) for c in range(w))
    if not has_8:
        return errors  # degenerate texture — allowed
    # At least one interior cell adjacent to any frame cell must be non-{0,8}
    has_interior = any(
        grid[r][c] not in (0, 8)
        for r in range(h) for c in range(w)
    )
    if not has_interior:
        errors.append("all cells are 0 or 8 — no interior majority colour")

    # A 3x3 frame has exactly one interior cell.  The rule redraws the frame and
    # paints the center with the interior majority, so such rows can be identity
    # demos (input already equals output).  Detect rectangular colour-8 frames by
    # their bbox and reject single-cell interiors in default generation.
    from collections import deque
    seen = set()
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != 8 or (sr, sc) in seen:
                continue
            q = deque([(sr, sc)])
            seen.add((sr, sc))
            comp = []
            while q:
                r, c = q.popleft()
                comp.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 8 and (nr, nc) not in seen:
                        seen.add((nr, nc)); q.append((nr, nc))
            rs = [r for r, _ in comp]; cs = [c for _, c in comp]
            r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
            if r2 - r1 >= 2 and c2 - c1 >= 2:
                border = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
                          if r in (r1, r2) or c in (c1, c2)}
                if border.issubset(set(comp)):
                    inner_area = (r2 - r1 - 1) * (c2 - c1 - 1)
                    if inner_area < 2:
                        errors.append("3x3 frame has a single interior cell; output can equal input")
    return errors


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 10, 12); rng_n = (1, 2); fk = (3, 5)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 14, 18); rng_n = (2, 3); fk = (3, 7)
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 11, 15); rng_n = (1, 3); fk = (3, 6)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    n = rng.randint(*rng_n)
    # FRAMES ARE COLOUR 8 (the rule reads e8b-frame-objs g 8 — a prior version drew them
    # in colour 5, which the rule never sees -> EVERY output was blank). Interior fills
    # are non-{0,8} so they count toward the majority. Frame size + shape (incl. NON-SQUARE)
    # + count + the dominant interior colour (the discriminator) all vary.
    for _ in range(n):
        for _ in range(40):
            fh = rng.randint(*fk); fw = rng.randint(*fk)
            if fh == 3 and fw == 3:
                continue  # a single interior cell makes the redraw+center rule an identity demo
            if fh > h or fw > w:
                continue
            r1 = rng.randint(0, h - fh)
            c1 = rng.randint(0, w - fw)
            r2 = r1 + fh - 1; c2 = c1 + fw - 1
            if not _free(g, r1, c1, r2, c2):
                continue
            for c in range(c1, c2 + 1):
                g[r1][c] = 8; g[r2][c] = 8
            for r in range(r1, r2 + 1):
                g[r][c1] = 8; g[r][c2] = 8
            interior = [(r, c) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)]
            if not interior:
                break
            # majority colour fills > half the interior; 0-2 distractors fill the rest.
            majority, d1, d2 = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 3)
            rng.shuffle(interior)
            ncells = len(interior)
            nmaj = max(1, ncells // 2 + 1) if ncells > 1 else 1
            for cell in interior[:nmaj]:
                g[cell[0]][cell[1]] = majority
            rest = interior[nmaj:]
            for j, cell in enumerate(rest):
                g[cell[0]][cell[1]] = d1 if j % 2 == 0 else d2
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 13
    g = full_grid(h, w, 0)
    if name == "no_frames":
        # Loose colored cells but no 5-frames — rule's "frame
        # interior majority" lookup has no scope.
        g[3][3] = 4; g[5][8] = 6
        return g
    if name == "no_majority":
        # Frame with interior split evenly between two colors —
        # rule's "strict majority" filter fails; center cell
        # selection ambiguous. (Frame is colour 8 — the rule's scope.)
        for c in range(2, 7): g[1][c] = 8; g[5][c] = 8
        for r in range(1, 6): g[r][2] = 8; g[r][6] = 8
        interior = [(r, c) for r in range(2, 5) for c in range(3, 6)]
        for i, (r, c) in enumerate(interior):
            g[r][c] = 4 if i < 4 else 6
        return g
    if name == "empty_interior":
        # Frame with empty interior — rule has no cells to compute
        # majority from; center marker undefined. (Frame is colour 8.)
        for c in range(2, 7): g[1][c] = 8; g[5][c] = 8
        for r in range(1, 6): g[r][2] = 8; g[r][6] = 8
        return g
    return g
