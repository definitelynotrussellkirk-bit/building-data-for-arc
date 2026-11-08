"""Generator for 64a7c07e.

Rule: collect all 8-blobs. Group by overlapping row range. For each
blob, shift cells right by group's bbox width.

Combinatorial axes (8): grid_h/w, blob_h, blob_w, n_blobs,
distractor_color, position_bias, palette_kind, anchor_corner.
Degenerates: no_blob, blob_at_edge, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect

GENERATOR_ID = "c276ddc1b410"
VERSION = "1.2.0"  # all-blank fix: a distractor sharing a blob's row range inflated the group bbox-width so the blob shifted off-grid -> blank output. Keep the distractor >=2 rows clear of every blob; never-blank guard.
TASK_ID = "c276ddc1b410"
SUMMARY = "1-2 solid 8-blobs in left half of grid, leaving room to shift right."

INVARIANTS = [
    "1-2 solid 8-blobs in different row ranges",
    "each blob has space to shift right by its width",
]

POSITION_BIASES = ("scattered", "stacked", "row_aligned", "centered")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_blob", "blob_at_edge", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "5..12"},
    "blob_h":         {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "blob_w":         {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "n_blobs":        {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "distractor_color":{"type": "color", "default": "rng 2..7", "valid": "2..7"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "palette_kind":   {"type": "str", "default": "rng",
                       "valid": "|".join(PALETTE_KINDS)},
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
        h_lo, h_hi, w_lo, w_hi = 4, 5, 5, 7
        bh_lo, bh_hi, bw_lo, bw_hi = 2, 2, 2, 2
        nb_lo, nb_hi = 1, 1
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 8, 10, 10, 12
        bh_lo, bh_hi, bw_lo, bw_hi = 2, 4, 2, 4
        nb_lo, nb_hi = 2, 3
    else:
        h_lo, h_hi, w_lo, w_hi = 5, 7, 7, 9
        bh_lo, bh_hi, bw_lo, bw_hi = 2, 3, 2, 3
        nb_lo, nb_hi = 1, 2
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    g = full_grid(h, w, 0)
    n_blobs = int(overrides.get("n_blobs",
                                ctx.draw_int("n_blobs", nb_lo, nb_hi)))
    n_blobs = max(1, min(3, n_blobs))
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIASES)))
    placed_rows = []
    placed_bboxes = []          # (r0, r1) row ranges of placed blobs
    for _try in range(40):
        if len(placed_rows) >= n_blobs:
            break
        rh = int(overrides.get("blob_h",
                               rng.randint(bh_lo, bh_hi)))
        rw = int(overrides.get("blob_w",
                               rng.randint(bw_lo, bw_hi)))
        if bias == "stacked":
            r0 = rng.randint(0, h - rh) if not placed_rows else min(h - rh, placed_rows[-1] + 2)
        else:
            r0 = rng.randint(0, h - rh)
        c_max = max(0, w // 2 - rw)
        c0 = rng.randint(0, c_max)
        if any(abs(r0 - pr) < rh + 1 for pr in placed_rows):
            continue
        draw_rect(g, r0, c0, rh, rw, 8)
        placed_rows.append(r0)
        placed_bboxes.append((r0, r0 + rh - 1))
    if not placed_bboxes:
        # never leave a blank input (rule shifts nothing -> blank output)
        rh = min(2, h); rw = min(2, max(1, w // 2))
        draw_rect(g, 0, 0, rh, rw, 8)
        placed_bboxes.append((0, rh - 1))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    pal = _build_palette(palette_kind, rng)
    dcolor = int(overrides.get("distractor_color", rng.choice(pal)))
    # The rule groups objects by overlapping ROW RANGE and shifts each right by
    # the GROUP's bbox width. A distractor sharing a blob's row range inflates
    # that width so the blob shifts off the grid -> ALL cells drop -> blank
    # output. Keep the distractor >=2 rows clear of every blob (its own group).
    for _try in range(40):
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if g[r][c] != 0:
            continue
        if any(r1 - 1 <= r <= r2 + 1 for (r1, r2) in placed_bboxes):
            continue
        g[r][c] = dcolor
        break
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Simulate the rule (group objects by row-range, shift each right by the
    group width) and require >=1 cell to land in-bounds, else output is blank."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h = len(grid); w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    # 4-connected non-bg objects
    seen = set(); objs = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != 0 and (sr, sc) not in seen:
                comp = []; stack = [(sr, sc)]; seen.add((sr, sc))
                while stack:
                    r, c = stack.pop(); comp.append((r, c))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = r + dr, c + dc
                        if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0
                                and (nr, nc) not in seen):
                            seen.add((nr, nc)); stack.append((nr, nc))
                objs.append(comp)
    if not objs:
        return ["no objects: rule shifts nothing -> blank"]
    bboxes = [(min(r for r, _ in o), max(r for r, _ in o)) for o in objs]
    painted = 0
    for i, obj in enumerate(objs):
        r1, r2 = bboxes[i]
        group = [objs[j] for j in range(len(objs))
                 if not (bboxes[j][1] < r1 - 1 or bboxes[j][0] > r2 + 1)]
        gcells = [p for o in group for p in o]
        bw = max(c for _, c in gcells) - min(c for _, c in gcells) + 1
        for (r, c) in obj:
            if c + bw < w:
                painted += 1
    if painted == 0:
        return ["every shifted cell lands out of bounds: blank output"]
    return []


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6]
    elif kind == "cool":
        pool = [5, 7]
    elif kind == "primary":
        pool = [2, 3, 4]
    else:
        pool = [2, 3, 4, 5, 6, 7]
    pool = [c for c in pool if c != 8]
    rng.shuffle(pool)
    return pool


def _draw_from_degenerate(name, rng):
    h, w = 6, 8
    g = full_grid(h, w, 0)
    if name == "no_blob":
        g[2][2] = 3
        return g
    if name == "blob_at_edge":
        draw_rect(g, 0, w - 2, 2, 2, 8)
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 8
        return g
    return g
