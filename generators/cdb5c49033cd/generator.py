"""Generator for arc_puzzle_bank_21_set9_e:hard_i15.

Combinatorial axes (8): variant, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_frames, no_inserts, equal_interiors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid
from puzzle_generators.helpers.selfcheck import color_rect_frames, components, bbox

GENERATOR_ID = "cdb5c49033cd"
VERSION = "3.0.0"  # shape-locked in+out: FIXED 12x16 grid + 2 frames at fixed positions + inserts from a FIXED 6-variant bank. Rule matches each non-frame insert to the frame whose INTERIOR dims == the insert's bbox then pastes it in; size-agnostic. Now vary grid + 2-4 frames with DISTINCT random interior dims (incl non-square) + random insert shapes that exactly fill them, all at free positions. Frame colour stays 8 (canonical)."
TASK_ID = "cdb5c49033cd"
SUMMARY = (
    "Several HOLLOW color-8 frames with DISTINCT interior dimensions, plus "
    "detached inserts in distinct non-{0,8} colors; each insert's bbox matches "
    "exactly one frame's interior. Rule: move each insert into its matching "
    "frame's interior; the original insert position is cleared."
)

INVARIANTS = [
    "all hollow frames are color 8 and have distinct interior dimensions",
    "each detached insert has a bounding box matching exactly one frame interior",
    "insert components are connected non-frame shapes",
    "the output keeps the frames and moves each insert into its matching interior",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "no_inserts", "equal_interiors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 14..22", "valid": "10..28"},
    "grid_w":         {"type": "int", "default": "rng 14..22", "valid": "10..28"},
    "n_pairs":        {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "varied", "valid": "varied"},
    "position_bias":  {"type": "str", "default": "free", "valid": "free"},
    "n_distinct_colors": {"type": "int", "default": "varied", "valid": "varied"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _paint(g, top, left, cells, color):
    for r, c in cells:
        g[top + r][left + c] = color


def _norm(cells):
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _outline_set(ih, iw):
    return {(r, c) for r in range(ih) for c in range(iw)
            if r in (0, ih - 1) or c in (0, iw - 1)}


def _fit_shape(rng, ih, iw):
    """Random connected polyomino whose bbox is EXACTLY ih x iw and which is NOT
    a pure rectangle outline (so it's never mis-classified as a frame)."""
    outline = _outline_set(ih, iw)
    for _ in range(150):
        k = rng.randint(max(2, ih, iw), ih * iw)
        cells = [(0, 0)]; seen = {(0, 0)}
        while len(cells) < k:
            r, c = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            if (r + dr, c + dc) not in seen:
                cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
        nc = _norm(cells)
        bh = max(r for r, _ in nc) + 1; bw = max(c for _, c in nc) + 1
        if bh == ih and bw == iw and set(nc) != outline:
            return nc
    return [(r, c) for r in range(ih) for c in range(iw)]   # solid fallback (never an outline for >=3 dims)


def _place(g, rh, rw, draw_fn, rng):
    """Find a free (1-ring gap) rh x rw patch and run draw_fn(r0, c0). True on success.

    The old random-probe version could miss existing legal placements and then
    silently omit a frame/insert.  Shuffle all legal top-left candidates instead:
    still random, but complete for the current board.
    """
    h, w = len(g), len(g[0])
    if rh > h or rw > w:
        return False
    positions = [(r0, c0) for r0 in range(h - rh + 1) for c0 in range(w - rw + 1)]
    rng.shuffle(positions)
    for r0, c0 in positions:
        ok = True
        for r in range(max(0, r0 - 1), min(h, r0 + rh + 1)):
            for c in range(max(0, c0 - 1), min(w, c0 + rw + 1)):
                if g[r][c] != 0:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            draw_fn(r0, c0)
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        k = ctx.draw_int("n_pairs", 2, 2); h = ctx.draw_int("grid_h", 11, 15); w = ctx.draw_int("grid_w", 12, 16)
    elif difficulty == "hard":
        k = ctx.draw_int("n_pairs", 3, 4); h = ctx.draw_int("grid_h", 18, 28); w = ctx.draw_int("grid_w", 18, 28)
    else:
        k = ctx.draw_int("n_pairs", 2, 3); h = ctx.draw_int("grid_h", 14, 22); w = ctx.draw_int("grid_w", 14, 22)
    # distinct interior dims (so each insert matches exactly one frame); incl non-square
    # Both dims >= 2 and max >= 3: a non-outline bbox-exact insert only exists then.
    # 1x1 also crashed _fit_shape's randint(max(2,ih,iw), ih*iw); 1xN/2x2 inserts
    # would be solid rectangles (mis-classified as frames, which this rule avoids).
    pool = [(ih, iw) for ih in range(2, 6) for iw in range(2, 6) if max(ih, iw) >= 3]
    rng.shuffle(pool)
    dims = pool[:k]
    colors = rng.sample([2, 3, 4, 5, 6, 7, 9], k)
    # Try the requested pair count first, then degrade to the still-useful 2-pair
    # minimum when a small sampled board cannot physically fit every detached
    # insert plus a 1-cell moat around all frames.  For each target count, try
    # both the initially sampled dimensions and the smallest feasible dimensions;
    # this preserves variety on roomy boards but avoids rare raise/omission on
    # easy 11x12 boards.
    small_dims = sorted(pool, key=lambda d: (d[0] * d[1], d[0] + d[1]))
    for target_k in range(k, 1, -1):
        dim_options = []
        for option in (dims[:target_k], small_dims[:target_k]):
            if option not in dim_options:
                dim_options.append(option)
        target_colors = colors[:target_k]
        for target_dims in dim_options:
            for _board_attempt in range(80):
                g = full_grid(h, w, 0)
                placed_pairs = []
                for (ih, iw), col in zip(target_dims, target_colors):
                    fh, fw = ih + 2, iw + 2
                    ok = _place(
                        g, fh, fw,
                        lambda r0, c0, fh=fh, fw=fw: draw_frame(g, r0, c0, r0 + fh - 1, c0 + fw - 1, 8),
                        rng,
                    )
                    if not ok:
                        break
                    placed_pairs.append((ih, iw, col))
                if len(placed_pairs) != target_k:
                    continue
                inserted = 0
                # detached inserts: each bbox exactly matches one frame's interior dims
                for (ih, iw, col) in placed_pairs:
                    shape = _fit_shape(rng, ih, iw)
                    if not _place(g, ih, iw,
                                  lambda r0, c0, sh=shape, cc=col: _paint(g, r0, c0, sh, cc), rng):
                        break
                    inserted += 1
                if inserted == len(placed_pairs):
                    return g
    return _fallback_two_pair_board(h, w, colors[:2], rng)


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 16, 0)
    if name == "no_frames":
        # Inserts present but no frames — rule has nowhere to place inserts.
        for r, c in [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)]: g[8 + r][1 + c] = 4
        return g
    if name == "no_inserts":
        # Frames present but no detached inserts — rule has nothing to match.
        draw_frame(g, 1, 1, 5, 5, 8)
        draw_frame(g, 1, 9, 6, 12, 8)
        return g
    if name == "equal_interiors":
        # Both frames have the same interior size — match is ambiguous.
        draw_frame(g, 1, 1, 4, 4, 8)
        draw_frame(g, 1, 9, 4, 12, 8)
        for r, c in [(0, 0), (1, 0), (1, 1)]: g[8 + r][1 + c] = 4
        for r, c in [(0, 0), (1, 0), (1, 1)]: g[8 + r][9 + c] = 5
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for matching detached inserts to frame interiors."""
    errs: list[str] = []
    if not grid or not isinstance(grid[0], list):
        return ["grid is empty or not rectangular"]
    frames = color_rect_frames(grid, color=8, min_outer_h=4, min_outer_w=4)
    if not (2 <= len(frames) <= 4):
        errs.append(f"expected 2..4 hollow color-8 frames, got {len(frames)}")
    frame_dims = [(r2 - r1 - 1, c2 - c1 - 1) for r1, c1, r2, c2 in frames]
    if len(set(frame_dims)) != len(frame_dims):
        errs.append(f"frame interior dimensions are not distinct: {frame_dims}")
    insert_dims = []
    for comp in components(grid):
        if comp["color"] == 8:
            continue
        r1, c1, r2, c2 = comp["bbox"]
        insert_dims.append((r2 - r1 + 1, c2 - c1 + 1))
    if len(insert_dims) != len(frame_dims):
        errs.append(f"insert/frame count mismatch: inserts={insert_dims}, frames={frame_dims}")
    if sorted(insert_dims) != sorted(frame_dims):
        errs.append(f"insert bbox dims do not match frame interiors: inserts={insert_dims}, frames={frame_dims}")
    return errs


def _fallback_two_pair_board(h, w, colors, rng):
    """Last-resort constructive two-pair board for the smallest sampled grids."""
    g = full_grid(h, w, 0)
    dims = [(2, 3), (3, 2)]
    # Two compact frames in the top band, separated horizontally.
    draw_frame(g, 0, 0, dims[0][0] + 1, dims[0][1] + 1, 8)
    c2 = max(dims[0][1] + 4, w - (dims[1][1] + 2))
    draw_frame(g, 0, c2, dims[1][0] + 1, c2 + dims[1][1] + 1, 8)
    # Matching detached inserts in the bottom band; solid inserts are connected
    # and bbox-exact, and never look like color-8 frames.
    r1 = h - dims[0][0]
    for r in range(dims[0][0]):
        for c in range(dims[0][1]):
            g[r1 + r][c] = colors[0]
    r2 = h - dims[1][0]
    c_ins = w - dims[1][1]
    for r in range(dims[1][0]):
        for c in range(dims[1][1]):
            g[r2 + r][c_ins + c] = colors[1]
    return g
