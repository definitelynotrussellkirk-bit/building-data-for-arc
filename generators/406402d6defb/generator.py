"""Generator for arc_puzzle_bank_eighth21:M54 — point-reflect blob around 1-anchor.

Rule: a 1-cell is the anchor. Each non-1, non-0 cell stays at (r,c) AND
also gets duplicated at (2*ar - r, 2*ac - c). Anchor stays 1.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_anchor (no 1-cell → rule's anchor selector finds
nothing, no reflection), no_blob (anchor present but no non-1,
non-0 cells → rule has nothing to reflect), point_symmetric_blob
(blob is already point-symmetric around the anchor → reflection lands
on existing cells, output equals input).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "406402d6defb"
VERSION = "2.1.0"
TASK_ID = "406402d6defb"
SUMMARY = (
    "0-bg grid (h, w~8-11) with: (a) EXACTLY ONE "
    "color-1 (blue) ANCHOR cell placed at the grid's "
    "central position (h//2, w//2); (b) ONE small "
    "connected BLOB of 2-4 cells in some non-{0, 1} "
    "color, placed in the upper-LEFT region of the "
    "grid so that the blob's POINT-REFLECTION across "
    "the anchor lands fully IN-BOUNDS in the "
    "lower-right region and does NOT overlap the "
    "original blob or the anchor itself. Rule: the "
    "color-1 cell at (ar, ac) is the ANCHOR. For "
    "every non-1 non-0 cell at (r, c) with color k, "
    "PAINT its POINT-REFLECTION at (2*ar - r, "
    "2*ac - c) with color k. The original blob stays "
    "and the anchor stays color 1. Net: the small "
    "blob sprouts a same-color mirror copy rotated "
    "180° around the blue anchor."
)

INVARIANTS = [
    "background is 0",
    "exactly one 1-cell (anchor)",
    "the (single) non-1 blob's reflected image is fully in-bounds",
    "blob and its reflection don't overlap (so output is clearly different from input)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_anchor", "no_blob", "point_symmetric_blob")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":            {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "blob_size":         {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 2..2", "valid": "2..2"},
    "position_bias":     {"type": "str", "default": "anchor_plus_blob",
                          "valid": "anchor_plus_blob"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..2", "valid": "2..2"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        target_lo, target_hi = 2, 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 10, 11)
        target_lo, target_hi = 3, 5
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 11)
        target_lo, target_hi = 2, 4
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    ar = h // 2; ac = w // 2
    g[ar][ac] = 1
    used = {(ar, ac)}
    color = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
    for _ in range(40):
        ulr = ar - 1
        ulc = ac - 1
        if ulr < 1 or ulc < 1: break
        seed_pos = (rng.randint(1, ulr), rng.randint(1, ulc))
        if seed_pos in used: continue
        cells = {seed_pos}
        frontier = [seed_pos]
        if "blob_size" in overrides and overrides.get("blob_size") is not None:
            target = ctx.draw_int("blob_size", 2, 5)
        else:
            target = rng.randint(target_lo, target_hi)
        while frontier and len(cells) < target:
            r0, c0 = frontier.pop(rng.randint(0, len(frontier) - 1))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r0 + dr, c0 + dc
                if 1 <= nr <= ulr and 1 <= nc <= ulc and (nr, nc) not in cells and (nr, nc) not in used:
                    cells.add((nr, nc))
                    frontier.append((nr, nc))
                    if len(cells) >= target: break
        if len(cells) < 2: continue
        ok = True
        for r, c in cells:
            mr = 2 * ar - r; mc = 2 * ac - c
            if not (0 <= mr < h and 0 <= mc < w):
                ok = False; break
            if (mr, mc) in cells or (mr, mc) == (ar, ac):
                ok = False; break
        if not ok: continue
        for r, c in cells:
            g[r][c] = color
        break
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    anchors = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    if len(anchors) != 1:
        errors.append(f"expected exactly one color-1 anchor, found {len(anchors)}")
        return errors
    ar, ac = anchors[0]
    blob = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 1)]
    if len(blob) < 2:
        errors.append(f"blob must have at least two cells, found {len(blob)}")
    colors = {grid[r][c] for r, c in blob}
    if len(colors) > 1:
        errors.append(f"blob should use one non-anchor color, found {sorted(colors)}")
    blob_set = set(blob)
    for r, c in blob:
        mr, mc = 2 * ar - r, 2 * ac - c
        if not (0 <= mr < h and 0 <= mc < w):
            errors.append(f"reflection of {(r, c)} lands out of bounds at {(mr, mc)}")
        if (mr, mc) in blob_set or (mr, mc) == (ar, ac):
            errors.append(f"reflection of {(r, c)} overlaps input blob/anchor at {(mr, mc)}")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_anchor":
        # No 1-cell → rule's anchor selector finds nothing; no reflection.
        g[2][2] = 4; g[2][3] = 4; g[3][2] = 4
        return g
    if name == "no_blob":
        # Anchor present but no non-1, non-0 cells — rule has nothing
        # to reflect.
        g[4][4] = 1
        return g
    if name == "point_symmetric_blob":
        # Blob is already point-symmetric around (4,4) — reflecting
        # lands on existing cells; output equals input.
        g[4][4] = 1
        g[2][2] = 6; g[6][6] = 6   # symmetric pair
        g[2][6] = 6; g[6][2] = 6   # symmetric pair
        return g
    return g
