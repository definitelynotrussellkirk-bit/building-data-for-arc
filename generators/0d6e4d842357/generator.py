"""Generator for arc_puzzle_bank_sixteenth21:M106 — vector shadow copy.

Rule: 8 = src, 9 = dst. Each non-{0,8,9} cell stays AND is duplicated
at translated position (dst-src offset). Shadow copy.

Combinatorial axes (8): grid_h, grid_w, palette_kind, blob_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_src, no_dst, no_blob.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "0d6e4d842357"
VERSION = "1.2.1"  # 1.2.0: robust retry + varied delta direction + larger 1-2 color blob (was distinct=24, uniq=0.17 from empty-output fallbacks)
TASK_ID = "0d6e4d842357"
SUMMARY = "8-src + 9-dst markers + a colored blob; both blob and shadow in-bounds."

INVARIANTS = [
    "background is 0",
    "exactly one 8-cell + one 9-cell + a non-{0,8,9} blob",
    "translated cells are in-bounds",
    "blob and its shadow are disjoint",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_src", "no_dst", "no_blob")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "blob_size":      {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "src_dst_blob",
                       "valid": "src_dst_blob"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
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
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 11)
    rng = ctx.draw_rng("layout")
    blob_max = 4 if difficulty == "easy" else 7
    for _attempt in range(60):
        g = full_grid(h, w, 0)
        # grow the blob first (anywhere), then choose a delta whose
        # shadow lands in-bounds and disjoint from the blob.
        blob = grow_blob(rng, h, w, set(), rng.randint(3, blob_max),
                         max_attempts=80)
        if blob is None:
            continue
        rs = [r for r, _ in blob]; cs = [c for _, c in blob]
        bh = max(rs) - min(rs) + 1; bw = max(cs) - min(cs) + 1
        # candidate deltas keep the whole shadow in-bounds and disjoint.
        dr_lo = -min(rs); dr_hi = (h - 1) - max(rs)
        dc_lo = -min(cs); dc_hi = (w - 1) - max(cs)
        deltas = []
        for dr in range(dr_lo, dr_hi + 1):
            for dc in range(dc_lo, dc_hi + 1):
                if dr == 0 and dc == 0:
                    continue
                # disjoint if the translation exceeds the bbox extent
                if abs(dr) >= bh or abs(dc) >= bw:
                    deltas.append((dr, dc))
        if not deltas:
            continue
        dr, dc = rng.choice(deltas)
        # src anywhere free; dst = src + delta in-bounds and free
        shadow = {(r + dr, c + dc) for r, c in blob}
        free = [(r, c) for r in range(h) for c in range(w)
                if (r, c) not in blob and (r, c) not in shadow]
        if not free:
            continue
        src = rng.choice(free)
        dst_r = src[0] + dr; dst_c = src[1] + dc
        if not (0 <= dst_r < h and 0 <= dst_c < w):
            continue
        if (dst_r, dst_c) in blob or (dst_r, dst_c) in shadow or (dst_r, dst_c) == src:
            continue
        # paint blob with 1-2 colors (rule preserves each cell's color)
        n_col = rng.randint(1, 2)
        cols = rng.sample([2, 3, 4, 5, 6, 7], n_col)
        for r, c in blob:
            g[r][c] = rng.choice(cols)
        g[src[0]][src[1]] = 8
        g[dst_r][dst_c] = 9
        return g
    # fallback: minimal valid instance
    g = full_grid(h, w, 0)
    g[0][0] = 8; g[1][0] = 9
    g[0][2] = 4; g[0][3] = 4
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: exactly one 8-cell (src), exactly one 9-cell (dst), >=1
    blob cell (non-{0,8,9})."""
    msgs = []
    h, w = len(grid), len(grid[0])
    eights = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    nines = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    blob = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 8, 9)]
    if len(eights) != 1:
        msgs.append(f"expected exactly 1 color-8 (src), found {len(eights)}")
    if len(nines) != 1:
        msgs.append(f"expected exactly 1 color-9 (dst), found {len(nines)}")
    if not blob:
        msgs.append("no blob cells (non-{0,8,9}) — rule has nothing to shadow-copy")
    return msgs


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_src":
        # only dst + blob → no source to define translation vector
        g[5][7] = 9
        g[2][2] = 4; g[2][3] = 4; g[3][2] = 4
        return g
    if name == "no_dst":
        # only src + blob → no destination, vector undefined
        g[1][1] = 8
        g[3][3] = 4; g[3][4] = 4; g[4][3] = 4
        return g
    if name == "no_blob":
        # markers but no blob → no cells to translate
        g[1][1] = 8
        g[5][7] = 9
        return g
    return g

def _self_components(grid, colors=None):
    h, w = len(grid), len(grid[0]); seen = set(); out = []
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if (r, c) in seen or v == 0 or (colors is not None and v not in colors):
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == v:
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append((v, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None):
    if not grid or not grid[0]: return ["empty grid"]
    h,w=len(grid),len(grid[0]); msgs=[]
    src=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==8]
    dst=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==9]
    blob=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v not in (0,8,9)]
    if len(src)!=1 or len(dst)!=1: msgs.append("expected exactly one 8 source and one 9 destination")
    if not blob: msgs.append("expected at least one colored blob cell")
    if len(src)==1 and len(dst)==1:
        dr=dst[0][0]-src[0][0]; dc=dst[0][1]-src[0][1]
        if dr==0 and dc==0: msgs.append("translation vector must be nonzero")
        if any(not (0<=r+dr<h and 0<=c+dc<w) for r,c in blob): msgs.append("translated blob cells must stay in bounds")
        if any((r+dr,c+dc) in blob or (r+dr,c+dc) in src+dst for r,c in blob): msgs.append("shadow must be disjoint from blob and markers")
    return msgs
