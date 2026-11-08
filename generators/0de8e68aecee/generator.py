"""Generator for d4c90558.

Rule: colored frames sorted by count of gray cells inside their bbox,
encoded as padded rows.

Combinatorial axes (8): grid_h/w, frame_count, palette_kind, gray_skew,
position_bias, anchor_corner, asymmetry_force, palette_size.
Degenerates: no_grays, all_grays, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "0de8e68aecee"
VERSION = "1.3.0"  # 1.1.0->1.2.0: vary frame count/positions/sizes + per-frame gray counts (was fixed 3 frames at fixed positions counts 1,3,5 -> shape-locked 3x5)
TASK_ID = "0de8e68aecee"
SUMMARY = "Colored frames sorted by gray-count inside bbox; encoded as padded rows."

INVARIANTS = [
    "background is color 0",
    "frame colors are nonzero and not gray",
    "each frame bbox contains one or more color-5 cells",
    "the output has one row per frame, sorted by gray-count ascending",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_grays", "all_grays", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "16", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "16", "valid": "12..22"},
    "frame_count":    {"type": "int", "default": "3", "valid": "1..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "gray_skew":      {"type": "str", "default": "ascending",
                       "valid": "ascending|descending|rng"},
    "position_bias":  {"type": "str", "default": "rng",
                       "valid": "scattered|spread|rng"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..5"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _fallback_frame_layout(h, w, pal, n_frames):
    """Deterministic exact-count layout used only if stochastic packing misses.
    The minimum difficulty bands have enough room for these 5x5 frames with a
    one-cell halo at the corners and center."""
    g = full_grid(h, w, 0)
    positions = [
        (0, 0),
        (0, w - 5),
        (h - 5, 0),
        (h - 5, w - 5),
        ((h - 5) // 2, (w - 5) // 2),
    ]
    for i, (color, (r1, c1)) in enumerate(zip(pal[:n_frames], positions), start=1):
        r2, c2 = r1 + 4, c1 + 4
        draw_frame(g, r1, c1, r2, c2, color)
        spots = [(r, c) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)]
        for r, c in spots[:min(i, len(spots))]:
            g[r][c] = 5
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 14, 18
        nf_lo, nf_hi = 2, 3
    elif difficulty == "hard":
        h_lo, h_hi = 22, 30
        nf_lo, nf_hi = 4, 5
    else:
        h_lo, h_hi = 16, 26
        nf_lo, nf_hi = 2, 4
    h = int(overrides.get("grid_h", rng.randint(h_lo, h_hi)))
    w = int(overrides.get("grid_w", rng.randint(h_lo, h_hi)))
    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind")
                    or ctx.draw_choice("palette_kind",
                                       list(PALETTE_KINDS)))
    n_frames = int(overrides.get("frame_count", rng.randint(nf_lo, nf_hi)))
    pal = _build_palette(palette_kind, n_frames, rng)
    for _layout_attempt in range(80):
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        # distinct gray counts per frame (so the sorted histogram has varied
        # row lengths); each count <= interior capacity.
        placed_frames = 0
        used_counts = set()
        for color in pal:
            placed_this = False
            for _t in range(180):
                fh = rng.randint(5, min(10, h - 2))
                fw = rng.randint(5, min(12, w - 2))
                r1 = rng.randint(0, h - fh); c1 = rng.randint(0, w - fw)
                r2 = r1 + fh - 1; c2 = c1 + fw - 1
                # clearance (1-cell halo) so frames are separate components
                clash = any(
                    occ[r][c]
                    for r in range(max(0, r1 - 1), min(h, r2 + 2))
                    for c in range(max(0, c1 - 1), min(w, c2 + 2)))
                if clash:
                    continue
                # interior cells available for grays on the checker sublattice
                interior = [(r, c) for r in range(r1 + 1, r2)
                            for c in range(c1 + 1, c2)]
                cap = sum(1 for (r, c) in interior if (r + c) % 2 == 0)
                if cap < 1:
                    continue
                # pick a distinct gray count in 1..min(cap, 9)
                choices = [k for k in range(1, min(cap, 9) + 1)
                           if k not in used_counts]
                if not choices:
                    choices = list(range(1, min(cap, 9) + 1))
                gray_count = rng.choice(choices)
                used_counts.add(gray_count)
                draw_frame(g, r1, c1, r2, c2, color)
                spots = [(r, c) for (r, c) in interior if (r + c) % 2 == 0]
                rng.shuffle(spots)
                for (r, c) in spots[:gray_count]:
                    g[r][c] = 5
                for r in range(max(0, r1 - 1), min(h, r2 + 2)):
                    for c in range(max(0, c1 - 1), min(w, c2 + 2)):
                        occ[r][c] = True
                placed_frames += 1
                placed_this = True
                break
            if not placed_this:
                break
        if placed_frames == n_frames:
            return g
    return _fallback_frame_layout(h, w, pal, n_frames)


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 6, 7, 8, 9]
    pool = [c for c in pool if c not in (0, 5)]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [1, 2, 3, 4, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def _draw_from_degenerate(name, rng):
    h, w = 16, 16
    g = full_grid(h, w, 0)
    if name == "no_grays":
        draw_frame(g, 1, 1, 5, 5, 1)
        draw_frame(g, 1, 9, 6, 14, 3)
        return g
    if name == "all_grays":
        for r in range(h):
            for c in range(w):
                g[r][c] = 5
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 1
        return g
    return g


def _components(grid, allowed=None):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v == 0 or (allowed is not None and v not in allowed) or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == v
                            and (allowed is None or grid[nr][nc] in allowed)):
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append((v, cells))
    return comps


def _bbox(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _is_frame(cells):
    r0, c0, r1, c1 = _bbox(cells)
    if r1 - r0 < 2 or c1 - c0 < 2:
        return False
    expected = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                if r in (r0, r1) or c in (c0, c1)}
    return set(cells) == expected


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(v < 0 or v > 9 for row in grid for v in row):
        errors.append("grid has non-ARC color values")
    frame_comps = _components(grid, allowed=set(range(1, 10)) - {5})
    n = len(frame_comps)
    if difficulty == "easy":
        lo, hi = 2, 3
    elif difficulty == "hard":
        lo, hi = 4, 5
    else:
        lo, hi = 2, 4
    if not (lo <= n <= hi):
        errors.append(f"expected {lo}..{hi} colored frames, got {n}")
    colors = [v for v, _ in frame_comps]
    if len(colors) != len(set(colors)):
        errors.append(f"frame colors should be distinct, got {colors}")
    for color, cells in frame_comps:
        if color == 5:
            errors.append("frame color must not be gray 5")
        if not _is_frame(cells):
            errors.append(f"component color {color} is not a rectangular frame")
            continue
        r0, c0, r1, c1 = _bbox(cells)
        gray_inside = sum(1 for r in range(r0 + 1, r1)
                          for c in range(c0 + 1, c1) if grid[r][c] == 5)
        if gray_inside < 1:
            errors.append(f"frame color {color} has no gray cells inside its bbox")
    return errors

