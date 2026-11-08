"""Generator for arc_puzzle_bank_sixteenth21:M110 — transplant blob into frame.

Rule: a blob outside the frame + a 5-rect-frame. Output: empty grid +
blob moved inside the frame.

Combinatorial axes (8): grid_h, grid_w, palette_kind, blob_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_frame, no_blob, blob_inside_frame.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "dded62bb9e3a"
VERSION = "2.1.0"  # guarantee a placed blob that fits the frame interior (grow_blob could fail on small grids -> no blob -> blank solid-0 output)
TASK_ID = "dded62bb9e3a"
SUMMARY = "A color-5 rectangular hollow frame (≥4×4) and one connected blob in a non-{0,5} color, placed OUTSIDE the frame. Rule emits a FRESH same-size grid where the blob is translated so its bbox top-left aligns with (frame_r1+1, frame_c1+1) (the interior top-left). The 5-frame is DROPPED in the output; only the relocated blob remains."

# Rivals: 'output is input' refuted by demos (output drops frame).
# 'keep frame in output' refuted by demos (frame vanishes). 'blob
# centered in frame' refuted by demos showing blob anchored to
# top-left interior. 'use color 5 for blob' refuted by demos
# preserving blob color. 3 demos with varied blob shapes cover.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one rect-frame in color 5",
    "exactly one non-5 blob outside the frame",
    "blob's bbox fits inside the frame interior",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frame", "no_blob", "blob_inside_frame")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "7..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "blob_size":      {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "5frame_with_external_blob",
                       "valid": "5frame_with_external_blob"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 12, 16)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 10, 13)
    rng = ctx.draw_rng("layout")
    color = rng.choice([2, 3, 4, 6, 7, 8, 9])

    for _attempt in range(40):
        g = full_grid(h, w, 0)
        fh = rng.randint(4, 5); fw = rng.randint(4, 5)
        r1 = h - fh; c1 = w - fw
        r2 = r1 + fh - 1; c2 = c1 + fw - 1
        for c in range(c1, c2 + 1):
            g[r1][c] = 5; g[r2][c] = 5
        for r in range(r1, r2 + 1):
            g[r][c1] = 5; g[r][c2] = 5
        # Reserve ONLY the frame bbox + a 1-cell ring; the rest (full top rows / left
        # cols) is free for the blob. The previous buffer (r>=r1-1 OR c>=c1-1) wiped
        # the entire bottom+right strips, leaving small grids with no room -> no blob.
        used = set()
        for r in range(r1 - 1, r2 + 2):
            for c in range(c1 - 1, c2 + 2):
                used.add((r, c))
        int_h, int_w = fh - 2, fw - 2  # frame interior the rule must fit the blob into
        bmax = min(3, int_h * int_w)
        cells = grow_blob(rng, h, w, used, rng.randint(2, max(2, bmax)),
                          max_attempts=80)
        if cells:
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            if (max(rs) - min(rs) + 1) <= int_h and (max(cs) - min(cs) + 1) <= int_w:
                for r, c in cells:
                    g[r][c] = color
                return g
    # Fallback: a single-cell blob (always fits a >=2x2 interior) at the top-left,
    # which is guaranteed free (frame sits bottom-right).
    g = full_grid(h, w, 0)
    fh = 4; fw = 4
    r1 = h - fh; c1 = w - fw
    r2 = r1 + fh - 1; c2 = c1 + fw - 1
    for c in range(c1, c2 + 1):
        g[r1][c] = 5; g[r2][c] = 5
    for r in range(r1, r2 + 1):
        g[r][c1] = 5; g[r][c2] = 5
    g[0][0] = color
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """One color-5 frame + one non-{0,5} blob whose bbox fits the frame interior, so
    the rule (drop frame, relocate blob into interior) produces a visible non-blank
    output."""
    errs = []
    h = len(grid); w = len(grid[0]) if h else 0
    fives = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    blob = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 5)]
    if not fives:
        errs.append("no color-5 frame")
    if not blob:
        errs.append("no non-{0,5} blob — output would be blank")
        return errs
    if len({grid[r][c] for r, c in blob}) != 1:
        errs.append("blob is not a single color")
    if fives:
        fr1 = min(r for r, _ in fives); fr2 = max(r for r, _ in fives)
        fc1 = min(c for _, c in fives); fc2 = max(c for _, c in fives)
        int_h = fr2 - fr1 - 1; int_w = fc2 - fc1 - 1
        br1 = min(r for r, _ in blob); br2 = max(r for r, _ in blob)
        bc1 = min(c for _, c in blob); bc2 = max(c for _, c in blob)
        if (br2 - br1 + 1) > int_h or (bc2 - bc1 + 1) > int_w:
            errs.append("blob bbox does not fit the frame interior")
        # blob must be OUTSIDE the frame bbox
        if all(fr1 <= r <= fr2 and fc1 <= c <= fc2 for r, c in blob):
            errs.append("blob is inside the frame (precondition is 'outside')")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_frame":
        # blob without 5-frame → no destination container
        for r, c in [(1, 1), (1, 2), (2, 1)]: g[r][c] = 4
        return g
    if name == "no_blob":
        # frame only, no blob → nothing to transplant
        for c in range(4, 9): g[3][c] = 5; g[7][c] = 5
        for r in range(3, 8): g[r][4] = 5; g[r][8] = 5
        return g
    if name == "blob_inside_frame":
        # blob already inside frame → "outside" precondition fails
        for c in range(4, 9): g[3][c] = 5; g[7][c] = 5
        for r in range(3, 8): g[r][4] = 5; g[r][8] = 5
        for r, c in [(5, 6), (5, 7), (6, 6)]: g[r][c] = 4
        return g
    return g
