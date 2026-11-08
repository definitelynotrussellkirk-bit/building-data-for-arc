"""Generator for arc_puzzle_bank_21_set13_bundle:medium_m01 — fill the biggest frame.

Rule: of all rect-outline frames in the grid, fill the one with
greatest interior area (its inside cells become the frame's color).
Other frames stay outline-only.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_frames, single_frame, tied_areas.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import bbox, components

GENERATOR_ID = "646cc69fdf1c"
VERSION = "1.1.0"
TASK_ID = "646cc69fdf1c"
SUMMARY = "Two rect-outline frames, distinct colors, strictly different interior areas."

INVARIANTS = [
    "background is 0",
    "exactly two rect-outline frames, distinct colors",
    "frames have strictly different interior areas (so the 'biggest' is unique)",
    "frames don't overlap (1-cell padding between them)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "single_frame", "tied_areas")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 12..15", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "two_frames_distinct_size",
                       "valid": "two_frames_distinct_size"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _frame_free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 12, 13)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 15, 18)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 12, 15)
    rng = ctx.draw_rng("layout")
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2)
    sizes = [(5, 5), (4, 4)]
    for _board_attempt in range(80):
        g = full_grid(h, w, 0)
        order = list(sizes)
        rng.shuffle(order)
        placed = 0
        for (fh, fw), color in zip(order, palette):
            for _ in range(80):
                r1 = rng.randint(0, h - fh)
                c1 = rng.randint(0, w - fw)
                r2 = r1 + fh - 1
                c2 = c1 + fw - 1
                if not _frame_free(g, r1, c1, r2, c2):
                    continue
                for c in range(c1, c2 + 1):
                    g[r1][c] = color; g[r2][c] = color
                for r in range(r1, r2 + 1):
                    g[r][c1] = color; g[r][c2] = color
                placed += 1
                break
        if placed == 2:
            return g
    raise ValueError("could not place two separated frames")


def _draw_from_degenerate(name, rng):
    h, w = 10, 13
    g = full_grid(h, w, 0)
    if name == "no_frames":
        # Empty grid — rule has no frames to fill.
        return g
    if name == "single_frame":
        # Only one frame — rule's "biggest" pick is trivial; signal
        # degenerates.
        for c in range(2, 7): g[2][c] = 3; g[6][c] = 3
        for r in range(2, 7): g[r][2] = 3; g[r][6] = 3
        return g
    if name == "tied_areas":
        # Two frames with EQUAL interior area — rule's "strictly
        # biggest" tiebreak has no entry; selection ambiguous.
        for c in range(1, 5): g[1][c] = 3; g[4][c] = 3
        for r in range(1, 5): g[r][1] = 3; g[r][4] = 3
        for c in range(7, 11): g[5][c] = 4; g[8][c] = 4
        for r in range(5, 9): g[r][7] = 4; g[r][10] = 4
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for choosing and filling the largest frame."""
    errs: list[str] = []
    if not grid or not isinstance(grid[0], list):
        return ["grid is empty or not rectangular"]
    frames = []
    for comp in components(grid):
        r1, c1, r2, c2 = comp["bbox"]
        if r2 - r1 + 1 < 4 or c2 - c1 + 1 < 4:
            continue
        want = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
                if r in (r1, r2) or c in (c1, c2)}
        if set(comp["cells"]) == want:
            frames.append((r1, c1, r2, c2))
    if len(frames) != 2:
        return [f"expected exactly two rectangular outline frames, got {len(frames)}: {frames}"]
    areas = [(r2 - r1 - 1) * (c2 - c1 - 1) for r1, c1, r2, c2 in frames]
    if len(set(areas)) != 2:
        errs.append(f"frame interior areas should be distinct, got {areas}")
    colors = []
    for r1, c1, _r2, _c2 in frames:
        colors.append(grid[r1][c1])
    if len(set(colors)) != 2:
        errs.append(f"frame colors should be distinct, got {colors}")
    return errs
