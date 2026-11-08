"""Generator for arc_puzzle_bank_21_set22_s:S22_E4 — copy local 8 offset between frames.

Rule: one source-frame local 8 offset is copied into a target frame.

Combinatorial axes (8): grid_h, grid_w, palette_kind, offset_choice,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_source_8, no_target_frame, both_frames_have_8.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.local_frame import choose_frame, draw_marker_frame, frame_cells, gpos

GENERATOR_ID = "1e36fd36fdb1"
VERSION = "2.0.0"
TASK_ID = "1e36fd36fdb1"
SUMMARY = (
    "0-bg grid (h~10-12, w~"
    "11-14) with: (a) ONE "
    "SOURCE MARKER FRAME "
    "drawn with COLORS {2, 3, "
    "4} (3 corner-style "
    "markers anchored at "
    "frame's local origin); "
    "(b) ONE TARGET MARKER "
    "FRAME drawn with COLORS "
    "{5, 6, 7} at non-"
    "overlapping position; "
    "(c) ONE COLOR-8 (cyan) "
    "MOTIF cell INSIDE the "
    "SOURCE frame at one of "
    "5 OFFSETS (uv ∈ {(2, 0), "
    "(0, 2), (1, 1), (2, 2), "
    "(3, 1)}) from the "
    "source's local origin. "
    "Rule (COPY 8-MOTIF OFFSET "
    "FROM SOURCE FRAME INTO "
    "TARGET FRAME): identify "
    "the SOURCE FRAME (colors "
    "{2, 3, 4}) and locate "
    "its 8-cell at offset uv. "
    "Identify the TARGET "
    "FRAME (colors {5, 6, 7}). "
    "PAINT a COLOR-8 cell at "
    "the SAME LOCAL OFFSET uv "
    "from the TARGET frame's "
    "origin. Source frame + "
    "8 stay; target frame "
    "stays + gains an 8. "
    "Net: 8-marker's relative "
    "position transfers from "
    "{2, 3, 4} frame to "
    "{5, 6, 7} frame."
)

INVARIANTS = [
    "background is 0",
    "one source frame uses colors 2,3,4",
    "one target frame uses colors 5,6,7",
    "there is exactly one source-local color-8 motif cell",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_source_8", "no_target_frame", "both_frames_have_8")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..12", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 11..14", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "offset_choice":  {"type": "int", "default": "rng 0..4", "valid": "0..4"},
    "palette_size":   {"type": "int", "default": "7", "valid": "7..7"},
    "position_bias":  {"type": "str", "default": "two_marker_frames_with_local_8",
                       "valid": "two_marker_frames_with_local_8"},
    "n_distinct_colors": {"type": "int", "default": "7", "valid": "7..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

OFFSETS = [(2, 0), (0, 2), (1, 1), (2, 2), (3, 1)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], ctx.draw_rng("degenerate"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 10)
        w = ctx.draw_int("grid_w", 11, 12)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 13, 14)
    else:
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 11, 14)
    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    uv = rng.choice(OFFSETS)
    so, svx, svy = choose_frame(rng, h, w, [uv])
    source_cells = set(frame_cells(so, svx, svy)) | {gpos(so, svx, svy, *uv)}
    to, tvx, tvy = choose_frame(rng, h, w, [uv], forbidden=source_cells)
    draw_marker_frame(grid, so, svx, svy, (2, 3, 4))
    draw_marker_frame(grid, to, tvx, tvy, (5, 6, 7))
    r, c = gpos(so, svx, svy, *uv)
    grid[r][c] = 8
    return grid


def _draw_from_degenerate(name, rng):
    # rng is a ctx.draw_rng("degenerate") handle — deterministic per (seed,
    # sample_index), so degenerate edge-coverage layouts stay reproducible
    # without a banned `import random`.
    h, w = 10, 12
    grid = full_grid(h, w, 0)
    uv = (2, 0)
    so, svx, svy = choose_frame(rng, h, w, [uv])
    source_cells = set(frame_cells(so, svx, svy)) | {gpos(so, svx, svy, *uv)}
    to, tvx, tvy = choose_frame(rng, h, w, [uv], forbidden=source_cells)
    if name == "no_source_8":
        # source frame but no 8-motif → nothing to copy
        draw_marker_frame(grid, so, svx, svy, (2, 3, 4))
        draw_marker_frame(grid, to, tvx, tvy, (5, 6, 7))
        return grid
    if name == "no_target_frame":
        # source frame + 8 but no target frame → no destination
        draw_marker_frame(grid, so, svx, svy, (2, 3, 4))
        r, c = gpos(so, svx, svy, *uv)
        grid[r][c] = 8
        return grid
    if name == "both_frames_have_8":
        # both frames already have 8 → ambiguous source/destination roles
        draw_marker_frame(grid, so, svx, svy, (2, 3, 4))
        draw_marker_frame(grid, to, tvx, tvy, (5, 6, 7))
        sr, sc = gpos(so, svx, svy, *uv)
        tr, tc = gpos(to, tvx, tvy, *uv)
        grid[sr][sc] = 8
        grid[tr][tc] = 8
        return grid
    return grid


def _pos_by_color(grid, color):
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
    return cells


def _vec(a, b):
    return b[0] - a[0], b[1] - a[1]


def _valid_basis(vx, vy):
    return (vx in ((1, 0), (-1, 0), (0, 1), (0, -1))
            and vy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            and vx[0] * vy[0] + vx[1] * vy[1] == 0)


def _lpos(origin, vx, vy, point):
    dr, dc = point[0] - origin[0], point[1] - origin[1]
    return dr * vx[0] + dc * vx[1], dr * vy[0] + dc * vy[1]


def self_check(grid, *, difficulty=None, meta=None):
    problems = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid is not a nonempty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid rows are ragged"]
    positions = {}
    for color in (2, 3, 4, 5, 6, 7, 8):
        cells = _pos_by_color(grid, color)
        if len(cells) != 1:
            problems.append(f"expected exactly one color-{color} marker, found {len(cells)}")
        elif color != 8:
            positions[color] = cells[0]
        else:
            motif = cells[0]
    if problems:
        return problems
    so = positions[2]
    svx = _vec(so, positions[3])
    svy = _vec(so, positions[4])
    to = positions[5]
    tvx = _vec(to, positions[6])
    tvy = _vec(to, positions[7])
    if not _valid_basis(svx, svy):
        problems.append("source colors 2,3,4 do not define an orthogonal unit frame")
    if not _valid_basis(tvx, tvy):
        problems.append("target colors 5,6,7 do not define an orthogonal unit frame")
    if problems:
        return problems
    uv = _lpos(so, svx, svy, motif)
    if uv not in OFFSETS:
        problems.append("source color-8 motif is not at one of the taught local offsets")
    tr, tc = gpos(to, tvx, tvy, *uv)
    if not (0 <= tr < h and 0 <= tc < w):
        problems.append("target copy offset would leave the grid")
    elif grid[tr][tc] != 0:
        problems.append("target copy offset is already occupied in the input")
    return problems
