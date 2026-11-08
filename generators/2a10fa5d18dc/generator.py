"""Generator for arc_additional_puzzles_21_set6:M40 — fill rectangle-frame interior with seed color.

Rule: each rectangle-perimeter object (any color) whose strict
interior contains a non-bg seed cell gets its entire interior filled
with the seed's color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_frames,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_frames, no_seeds, multi_seeds.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_frame
from puzzle_generators.helpers.palette import random_palette
from puzzle_generators.helpers.blobs import bbox_overlaps

GENERATOR_ID = "2a10fa5d18dc"
VERSION = "1.1.0"
TASK_ID = "2a10fa5d18dc"
SUMMARY = "2 rectangle frames in different colors, each with one seed cell in its interior."

INVARIANTS = [
    "background is 0",
    "exactly 2 full-perimeter rectangle frames in distinct colors (each ≥4×4)",
    "each frame's strict interior holds exactly one seed cell of a different color",
    "frames don't touch each other",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "no_seeds", "multi_seeds")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 12..16", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_frames":       {"type": "int", "default": "2", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "position_bias":  {"type": "str", "default": "two_separated_frames",
                       "valid": "two_separated_frames"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _paint_frames_with_seeds(g, placed, frame_colors, rng):
    for (r1, c1, r2, c2), fc in zip(placed, frame_colors):
        draw_frame(g, r1, c1, r2, c2, fc)
        seed_color = rng.choice(list(random_palette(rng, 4, exclude=set(frame_colors))))
        sr = rng.randint(r1 + 1, r2 - 1)
        sc = rng.randint(c1 + 1, c2 - 1)
        g[sr][sc] = seed_color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 12, 13)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 14, 17)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 12, 16)
    n_frames = ctx.draw_int("n_frames", 2, 2)
    rng = ctx.draw_rng("layout")
    frame_colors = list(random_palette(rng, n_frames))
    for _outer in range(120):
        g = full_grid(h, w, 0)
        placed: list[tuple[int, int, int, int]] = []
        candidates = []
        for rh in (4, 5):
            for rw in (4, 5):
                for r1 in range(0, h - rh + 1):
                    for c1 in range(0, w - rw + 1):
                        candidates.append((r1, c1, r1 + rh - 1, c1 + rw - 1))
        for _ in range(n_frames):
            rng.shuffle(candidates)
            for r1, c1, r2, c2 in candidates:
                bb_pad = (r1 - 1, c1 - 1, r2 + 1, c2 + 1)
                if any(bbox_overlaps(bb_pad, (p[0]-1, p[1]-1, p[2]+1, p[3]+1)) for p in placed):
                    continue
                placed.append((r1, c1, r2, c2))
                break
            else:
                break
        if len(placed) == n_frames:
            _paint_frames_with_seeds(g, placed, frame_colors, rng)
            return g
    g = full_grid(h, w, 0)
    placed = [(0, 0, 3, 3), (h - 4, w - 4, h - 1, w - 1)]
    _paint_frames_with_seeds(g, placed[:n_frames], frame_colors, rng)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 13
    g = full_grid(h, w, 0)
    if name == "no_frames":
        # Loose seeds, no frames — rule has no interior to fill.
        g[3][3] = 4; g[6][8] = 6
        return g
    if name == "no_seeds":
        # Frames present but interiors empty — no seed color, no fill.
        draw_frame(g, 1, 1, 4, 5, 3)
        draw_frame(g, 1, 7, 4, 11, 4)
        return g
    if name == "multi_seeds":
        # Multiple seeds in one frame interior — fill color is ambiguous.
        draw_frame(g, 1, 1, 5, 6, 3)
        g[2][2] = 4; g[3][4] = 6
        return g
    return g

def _self_frame_bbox(cells):
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def self_check(grid, *, difficulty=None, meta=None):
    by_color = {}
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v != 0:
                by_color.setdefault(v, []).append((r, c))
    frames = []
    for color, cells in by_color.items():
        r1, c1, r2, c2 = _self_frame_bbox(cells)
        if r2 - r1 + 1 < 4 or c2 - c1 + 1 < 4:
            continue
        perim = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
                 if r in (r1, r2) or c in (c1, c2)}
        if set(cells) == perim:
            frames.append((color, r1, c1, r2, c2))
    errs = []
    if len(frames) != 2:
        errs.append(f"expected exactly 2 rectangle frames, found {len(frames)}")
    for color, r1, c1, r2, c2 in frames:
        interior = [(r, c) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2) if grid[r][c] != 0]
        if len(interior) != 1:
            errs.append(f"frame {color} interior has {len(interior)} seeds")
        elif grid[interior[0][0]][interior[0][1]] == color:
            errs.append(f"frame {color} seed reuses frame color")
    return errs
