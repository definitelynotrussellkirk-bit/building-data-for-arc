"""Generator for arc_additional_puzzle_bank_volume19:E133 — fill 3x3 hollow frame interiors.

Rule: every color-4 4-connected object with bbox 3x3 AND cell-count 8
(i.e., a hollow 3x3 frame with a single interior cell) gets its 1
interior cell painted color 1. Other 4-objects (4x4 frames, 2x2 solids,
plus-shapes, etc) are unchanged.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect_outline

GENERATOR_ID = "0d863ca6dad6"
VERSION = "1.2.1"
TASK_ID = "0d863ca6dad6"
SUMMARY = (
    "Color-4 4-connected objects on a 0-bg grid: a mix of hollow 3x3 "
    "frames (8 cells, the rule's target), hollow 4x4 frames (12 cells, "
    "non-target distractors), and possibly other shapes. Rule fills "
    "the single 0-interior cell of each 3x3 frame with color 1; all "
    "other shapes (and any 0-cells outside frames) are unchanged."
)

# Rivals: 'output is input' refuted by demos with ≥1 3x3 frame.
# 'fill ALL frame interiors regardless of size' refuted by ≥1 demo
# with 4x4 frame whose interior stays 0. 'fill with color 4' refuted
# by any demo (uses 1). 'fill the frame cells too' refuted by any
# demo (only the single interior cell changes). 3 demos with mixed
# 3x3 and 4x4 frames cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥1 hollow 3x3 4-frame in color 4 (target)",
    "≥1 distractor (non-3x3 4-object)",
    "frames don't touch each other (1-cell buffer)",
]

AXES = {
    "grid_h":          {"type": "int", "default": "rng 9..13", "valid": "8..18"},
    "grid_w":          {"type": "int", "default": "rng 13..18", "valid": "12..24"},
    "n_3x3_frames":    {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "n_distractors":   {"type": "int", "default": "rng 1..2", "valid": "0..4"},
}


def _free(g, r0, c0, h, w):
    H, W = len(g), len(g[0])
    if r0 < 0 or c0 < 0 or r0 + h > H or c0 + w > W:
        return False
    for r in range(max(0, r0 - 1), min(H, r0 + h + 1)):
        for c in range(max(0, c0 - 1), min(W, c0 + w + 1)):
            if g[r][c] != 0:
                return False
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 hollow 3x3 color-4 frame (8 cells); >=1 distractor."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    # find 4-connected components of color 4
    seen: set = set()
    has_3x3_frame = False
    has_distractor = False
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 4 and (r, c) not in seen:
                stack = [(r, c)]
                comp: list = []
                seen.add((r, c))
                while stack:
                    cr, cc = stack.pop()
                    comp.append((cr, cc))
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = cr + dr, cc + dc
                        if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 4
                                and (nr, nc) not in seen):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
                rr1 = min(rr for rr, _ in comp); rr2 = max(rr for rr, _ in comp)
                cc1 = min(cc for _, cc in comp); cc2 = max(cc for _, cc in comp)
                bh, bw = rr2 - rr1 + 1, cc2 - cc1 + 1
                if bh == 3 and bw == 3 and len(comp) == 8:
                    has_3x3_frame = True
                else:
                    has_distractor = True
    if not has_3x3_frame:
        errs.append("no hollow 3x3 color-4 frame (8 cells, 3x3 bbox)")
    if not has_distractor:
        errs.append("no distractor color-4 object")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = rng.randint(8, 11); w = rng.randint(11, 15)
        n_3x3 = rng.randint(1, 2); n_distractors = rng.randint(1, 2)
    elif difficulty == "hard":
        h = rng.randint(13, 18); w = rng.randint(17, 23)
        n_3x3 = rng.randint(3, 5); n_distractors = rng.randint(2, 4)
    else:
        h = rng.randint(10, 14); w = rng.randint(13, 19)
        n_3x3 = rng.randint(2, 3); n_distractors = rng.randint(1, 3)

    g = full_grid(h, w, 0)
    # Place 3x3 frames (target shape).
    placed = 0
    for _ in range(200):
        if placed >= n_3x3:
            break
        r0 = rng.randint(0, h - 3)
        c0 = rng.randint(0, w - 3)
        if not _free(g, r0, c0, 3, 3):
            continue
        draw_rect_outline(g, r0, c0, 3, 3, 4)
        placed += 1
    # Place distractors: 4x4 hollow frames OR 2x2 solid OR 5x3 frame.
    distractor_count = 0
    for _ in range(200):
        if distractor_count >= n_distractors:
            break
        kind = rng.choice(["4x4", "5x3", "2x2", "single"])
        if kind == "4x4":
            r0 = rng.randint(0, h - 4)
            c0 = rng.randint(0, w - 4)
            if not _free(g, r0, c0, 4, 4):
                continue
            draw_rect_outline(g, r0, c0, 4, 4, 4)
        elif kind == "5x3":
            r0 = rng.randint(0, h - 5)
            c0 = rng.randint(0, w - 3)
            if not _free(g, r0, c0, 5, 3):
                continue
            draw_rect_outline(g, r0, c0, 5, 3, 4)
        elif kind == "2x2":
            r0 = rng.randint(0, h - 2)
            c0 = rng.randint(0, w - 2)
            if not _free(g, r0, c0, 2, 2):
                continue
            for rr in range(r0, r0 + 2):
                for cc in range(c0, c0 + 2):
                    g[rr][cc] = 4
        else:  # single isolated 4-cell
            r0 = rng.randint(0, h - 1)
            c0 = rng.randint(0, w - 1)
            if not _free(g, r0, c0, 1, 1):
                continue
            g[r0][c0] = 4
        distractor_count += 1
    # Optional non-4 decoy pixel
    if rng.random() < 0.5:
        for _ in range(40):
            r = rng.randint(0, h - 1)
            c = rng.randint(0, w - 1)
            if g[r][c] == 0:
                g[r][c] = rng.choice([2, 3, 5, 6, 7, 8, 9])
                break
    return g
