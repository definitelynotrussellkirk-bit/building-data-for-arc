"""Generator for a48eeaf7.

Rule: gray pixels move in straight lines toward red block, stopping one
cell outside its bbox.

Combinatorial axes (8): grid_h/w, gray_count, palette_kind, block_h,
block_w, position_bias, anchor_corner, asymmetry_force.
Degenerates: no_block, no_grays, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import fill_box, full_grid

GENERATOR_ID = "6c0ec33929de"
VERSION = "2.1.0"
TASK_ID = "6c0ec33929de"
SUMMARY = (
    "0-bg grid (h, w~13-15) with: "
    "(a) ONE SOLID COLOR-2 (red) "
    "RECTANGLE of size bh×bw "
    "(bh, bw=2-4) at position "
    "(r1, c1)..(r2, c2), placed "
    "according to bias (centered/"
    "scattered/near_corner/rng); "
    "(b) 1-8 COLOR-5 (gray) PIXELS "
    "at scattered positions outside "
    "the red block (in horizontal, "
    "vertical, or diagonal "
    "directions). Rule (GRAVITATE "
    "GRAYS TO RED BLOCK): for EACH "
    "COLOR-5 GRAY PIXEL, MOVE it in "
    "a STRAIGHT LINE toward the "
    "RED BLOCK. The pixel STOPS at "
    "the cell ONE STEP OUTSIDE the "
    "block's bbox in the direction "
    "of approach. If the gray is "
    "directly aligned with the "
    "block (same row/col), move "
    "axially; if diagonal, move "
    "diagonally; if not aligned, "
    "move axially to the nearest "
    "side. Paint the new position "
    "color-5, clear the original. "
    "The red block stays. Net: "
    "gray pixels migrate to halos "
    "the red block's perimeter."
)

INVARIANTS = [
    "background is color 0",
    "red cells form one solid rectangular block",
    "gray cells lie outside the block in straight or diagonal directions",
    "the output keeps the red block and places grays on the one-cell perimeter reached from each source gray",
]

POSITION_BIASES = ("centered", "scattered", "near_corner", "rng")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_block", "no_grays", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 13..15", "valid": "10..20"},
    "grid_w":         {"type": "int", "default": "rng 13..15", "valid": "10..20"},
    "gray_count":     {"type": "int", "default": "4", "valid": "1..8"},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "block_h":        {"type": "int", "default": "2", "valid": "2..4"},
    "block_w":        {"type": "int", "default": "2", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 10, 12
        gc_lo, gc_hi = 2, 3
    elif difficulty == "hard":
        h_lo, h_hi = 16, 20
        gc_lo, gc_hi = 5, 8
    else:
        h_lo, h_hi = 13, 15
        gc_lo, gc_hi = 4, 5
    h = rng.randint(h_lo, h_hi)
    w = rng.randint(h_lo, h_hi)
    g = full_grid(h, w, 0)
    gc = ctx.draw_int("gray_count", gc_lo, gc_hi)
    gc = max(1, min(8, gc))
    bh = int(overrides.get("block_h", 2))
    bw = int(overrides.get("block_w", 2))
    bh = max(2, min(bh, 4))
    bw = max(2, min(bw, 4))
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIASES)))
    if bias == "centered":
        r1 = max(4, (h - bh) // 2)
        c1 = max(4, (w - bw) // 2)
    elif bias == "near_corner":
        r1 = rng.choice([4, max(4, h - bh - 4)])
        c1 = rng.choice([4, max(4, w - bw - 4)])
    else:
        r1 = 4 + rng.randint(0, max(0, h - bh - 7))
        c1 = 4 + rng.randint(0, max(0, w - bw - 7))
    r2 = r1 + bh - 1
    c2 = c1 + bw - 1
    fill_box(g, r1, c1, r2, c2, 2)
    # Draw enough source gray pixels for the requested difficulty.  The old
    # layout had only four hard-coded candidates, so hard mode requested 5-8
    # grays but always realized at most four.  All candidates lie on axial or
    # diagonal rays toward the red bbox, matching the canonical movement rule.
    candidates = []
    for rr in range(r1, r2 + 1):
        candidates.extend([(rr, c1 - 4), (rr, c2 + 4)])
    for cc in range(c1, c2 + 1):
        candidates.extend([(r1 - 4, cc), (r2 + 4, cc)])
    candidates.extend([
        (r1 - 3, c1 - 3), (r1 - 3, c2 + 3),
        (r2 + 3, c1 - 3), (r2 + 3, c2 + 3),
    ])
    candidates = [(r, c) for r, c in candidates
                  if 0 <= r < h and 0 <= c < w and g[r][c] == 0]
    # De-duplicate while preserving a deterministic shuffled order.
    rng.shuffle(candidates)
    seen = set(); uniq = []
    for rc in candidates:
        if rc not in seen:
            seen.add(rc); uniq.append(rc)
    for r, c in uniq[:gc]:
        g[r][c] = 5
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    reds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    grays = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    errs = []
    if not reds:
        return ["expected a red rectangle"]
    r0, r1 = min(r for r, _ in reds), max(r for r, _ in reds)
    c0, c1 = min(c for _, c in reds), max(c for _, c in reds)
    if len(reds) != (r1 - r0 + 1) * (c1 - c0 + 1):
        errs.append("red cells must form one solid rectangle")
    if any(grid[r][c] != 2 for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)):
        errs.append("red bbox contains non-red holes")
    if not grays:
        errs.append("expected at least one gray source pixel")
    if difficulty == "hard" and len(grays) < 5:
        errs.append(f"hard mode requested 5-8 gray sources but realized only {len(grays)}")
    for r, c in grays:
        if r0 <= r <= r1 and c0 <= c <= c1:
            errs.append("gray source lies inside the red block")
            break
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 14, 14
    g = full_grid(h, w, 0)
    if name == "no_block":
        for r, c in [(2, 2), (5, 8), (8, 3)]:
            g[r][c] = 5
        return g
    if name == "no_grays":
        fill_box(g, 6, 6, 7, 7, 2)
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 5
        return g
    return g
