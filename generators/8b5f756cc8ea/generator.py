"""Generator for 52fd389e.

Rule: each 4-frame with center special color gets a layer of that color
around the frame.

Combinatorial axes (8): grid_h/w, n_frames, separation, palette_kind,
position_bias, anchor_corner, asymmetry_force, palette_size.
Degenerates: no_frames, no_centers, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect_outline

GENERATOR_ID = "8b5f756cc8ea"
VERSION = "1.1.1"
TASK_ID = "8b5f756cc8ea"
SUMMARY = "1-2 small 3x3 4-frames each with a single non-4 center color."

INVARIANTS = [
    "1-2 4-frames (3x3 outline of 4s)",
    "each frame has exactly 1 non-4 cell at its center",
    "frames have >=3 cells of buffer to all sides",
]

POSITION_BIASES = ("scattered", "spread", "stacked", "rng")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_frames", "no_centers", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 12..18", "valid": "18..28"},
    "grid_w":         {"type": "int", "default": "rng 12..18", "valid": "18..28"},
    "n_frames":       {"type": "int", "default": "rng 1..2", "valid": "1..9"},
    "separation":     {"type": "int", "default": "6", "valid": "5..10"},
    "palette_kind":   {"type": "str", "default": "rng",
                       "valid": "|".join(PALETTE_KINDS)},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..3"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: if 4-frames exist, each has exactly 1 non-4 cell at center."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    # Find all cells of color 4 (frame outlines)
    fours = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4]
    if not fours:
        return []  # no_frames degenerate — allowed
    # For each possible 3x3 frame (top-left at r0,c0):
    errs = []
    found_frames = set()
    for r0 in range(h - 2):
        for c0 in range(w - 2):
            r1, c1 = r0 + 2, c0 + 2
            # Check if this is a 3x3 frame (outline is all 4, interior single non-4 cell)
            outline = (
                [(r0, c) for c in range(c0, c1 + 1)] +
                [(r1, c) for c in range(c0, c1 + 1)] +
                [(r, c0) for r in range(r0 + 1, r1)] +
                [(r, c1) for r in range(r0 + 1, r1)]
            )
            if all(grid[r][c] == 4 for r, c in outline):
                found_frames.add((r0, c0))
                center_val = grid[r0 + 1][c0 + 1]
                if center_val == 4:
                    errs.append(f"frame at ({r0},{c0}): center is 4 (should be non-4)")
                elif center_val == 0:
                    pass  # no_centers degenerate — allowed
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 18, 22
        nf_lo, nf_hi = 4, 5
    elif difficulty == "hard":
        h_lo, h_hi = 22, 28
        nf_lo, nf_hi = 6, 9
    else:
        h_lo, h_hi = 20, 26
        nf_lo, nf_hi = 5, 7
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    g = full_grid(h, w, 0)
    n_frames = int(overrides.get("n_frames",
                                 ctx.draw_int("n_frames", nf_lo, nf_hi)))
    n_frames = max(1, min(3, n_frames))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    pal = _build_palette(palette_kind, rng)
    sep = int(overrides.get("separation", 6))
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIASES)))
    placed = []
    for _ in range(n_frames * 30):
        if len(placed) >= n_frames:
            break
        if bias == "spread":
            r0 = rng.randint(2, h - 5)
            c0 = rng.randint(2, w - 5)
        elif bias == "stacked":
            r0 = 2 + len(placed) * sep
            c0 = rng.randint(2, w - 5)
        else:
            r0 = rng.randint(2, h - 5)
            c0 = rng.randint(2, w - 5)
        if any(abs(r0 - pr) < sep and abs(c0 - pc) < sep for pr, pc in placed):
            continue
        draw_rect_outline(g, r0, c0, 3, 3, 4)
        color = rng.choice(pal)
        g[r0 + 1][c0 + 1] = color
        placed.append((r0, c0))
    return g


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 3, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3]
    else:
        pool = [1, 2, 3, 5, 6, 7, 8, 9]
    pool = [c for c in pool if c != 4]
    rng.shuffle(pool)
    return pool


def _draw_from_degenerate(name, rng):
    h, w = 14, 14
    g = full_grid(h, w, 0)
    if name == "no_frames":
        g[7][7] = 2
        return g
    if name == "no_centers":
        draw_rect_outline(g, 4, 4, 3, 3, 4)
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 4
        return g
    return g
