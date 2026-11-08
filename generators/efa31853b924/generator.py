"""Generator for arc_puzzle_bank_21_set22_s:S22_E5 — copy 8-motif from source to target frame.

Rule: a small source-frame local 8 motif is copied into a target frame.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_offsets,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_source_frame, no_target_frame, no_motif.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.local_frame import choose_frame, draw_marker_frame, frame_cells, gpos

GENERATOR_ID = "efa31853b924"
VERSION = "2.0.0"  # full radius-3 offset pool (all quadrants, incl negative) + wider grids (was 6 fixed positive offsets)
TASK_ID = "efa31853b924"
SUMMARY = (
    "0-bg grid with a SOURCE local frame (L-marker colors 2,3,4 defining an "
    "origin + 2 perpendicular cardinal axes) carrying a color-8 motif in "
    "frame-LOCAL coordinates, and a TARGET frame (colors 5,6,7) with its own "
    "orientation. Rule: read the 8-motif in source-local coords (radius<=3) and "
    "paint it into the target frame -> the copy is rotated/reflected by the "
    "target's orientation. Motif cells span all four local quadrants (incl. "
    "negative offsets), counts/positions/orientations and grid size vary."
)

INVARIANTS = [
    "background is 0",
    "one source frame uses colors 2,3,4",
    "one target frame uses colors 5,6,7",
    "all motif points fit in both local frames",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_source_frame", "no_target_frame", "no_motif")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..12", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 11..14", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_offsets":      {"type": "int", "default": "rng 2..7", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "7", "valid": "7..7"},
    "position_bias":  {"type": "str", "default": "two_local_frames",
                       "valid": "two_local_frames"},
    "n_distinct_colors": {"type": "int", "default": "7", "valid": "7..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

# full local neighborhood within the rule's radius (3), all four quadrants,
# excluding the three marker positions (0,0)/(1,0)/(0,1)
OFFSETS = [(u, v) for u in range(-3, 4) for v in range(-3, 4)
           if (u, v) not in {(0, 0), (1, 0), (0, 1)}]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 10, 13)
        nlo, nhi = 2, 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 14, 18)
        nlo, nhi = 4, 7
    else:
        h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 12, 16)
        nlo, nhi = 3, 5
    rng = ctx.draw_rng("layout")

    # retry: two frames carrying the offset set must both fit (else fewer offsets)
    for _attempt in range(30):
        n = max(1, min(len(OFFSETS), ctx.draw_int("n_offsets", nlo, nhi)
                       if _attempt == 0 else rng.randint(2, max(2, nhi))))
        offsets = rng.sample(OFFSETS, n)
        try:
            so, svx, svy = choose_frame(rng, h, w, offsets)
            source_cells = (set(frame_cells(so, svx, svy))
                            | {gpos(so, svx, svy, *uv) for uv in offsets})
            to, tvx, tvy = choose_frame(rng, h, w, offsets, forbidden=source_cells)
        except ValueError:
            continue
        grid = full_grid(h, w, 0)
        draw_marker_frame(grid, so, svx, svy, (2, 3, 4))
        draw_marker_frame(grid, to, tvx, tvy, (5, 6, 7))
        for uv in offsets:
            r, c = gpos(so, svx, svy, *uv)
            grid[r][c] = 8
        return grid

    # robust fallback: minimal motif that always fits
    offsets = [(2, 0), (0, 2)]
    grid = full_grid(h, w, 0)
    so, svx, svy = choose_frame(rng, h, w, offsets)
    source_cells = (set(frame_cells(so, svx, svy))
                    | {gpos(so, svx, svy, *uv) for uv in offsets})
    to, tvx, tvy = choose_frame(rng, h, w, offsets, forbidden=source_cells)
    draw_marker_frame(grid, so, svx, svy, (2, 3, 4))
    draw_marker_frame(grid, to, tvx, tvy, (5, 6, 7))
    for uv in offsets:
        r, c = gpos(so, svx, svy, *uv)
        grid[r][c] = 8
    return grid


def _draw_from_degenerate(name, rng):
    h, w = 11, 12
    g = full_grid(h, w, 0)
    if name == "no_source_frame":
        # only target frame markers + 8-motif → no source frame to lift motif from
        g[2][8] = 5; g[3][8] = 6; g[2][9] = 7
        g[1][1] = 8; g[2][2] = 8
        return g
    if name == "no_target_frame":
        # source frame + motif but no target frame → nowhere to copy to
        g[1][1] = 2; g[2][1] = 3; g[1][2] = 4
        g[3][3] = 8; g[4][4] = 8
        return g
    if name == "no_motif":
        # both frames present but no 8-cells → nothing to copy
        g[1][1] = 2; g[2][1] = 3; g[1][2] = 4
        g[6][7] = 5; g[7][7] = 6; g[6][8] = 7
        return g
    return g
