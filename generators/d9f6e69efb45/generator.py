"""Generator for arc_puzzle_bank_21_set10_s:S10_M2 — flood 5-frame interior with single seed color.

Rule: each 5-color rectangle frame whose strict interior contains
exactly one non-0/non-5 color value gets its entire interior filled
with that color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, n_frames, texture.
Degenerates: no_frames, no_marker, multiple_marker_colors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_frame
from puzzle_generators.helpers.palette import random_palette
from puzzle_generators.helpers.blobs import bbox_overlaps

GENERATOR_ID = "d9f6e69efb45"
VERSION = "2.0.0"
TASK_ID = "d9f6e69efb45"
SUMMARY = (
    "0-bg grid (h~8-11, w~11-14) with "
    "1-3 (default 2) HOLLOW COLOR-5 "
    "(gray) RECTANGULAR FRAMES "
    "(4-5 × 4-5) at non-overlapping "
    "positions. INSIDE EACH frame's "
    "STRICT INTERIOR (rows r1+1.."
    "r2-1, cols c1+1..c2-1), place "
    "EXACTLY ONE MARKER CELL in a "
    "DISTINCT non-{0, 5} color. "
    "Rule (FLOOD FRAME INTERIOR "
    "WITH MARKER COLOR): for EACH "
    "color-5 RECTANGULAR FRAME, "
    "identify its INTERIOR cells. "
    "If the interior contains "
    "EXACTLY ONE non-{0, 5} marker "
    "color, FILL the entire frame's "
    "INTERIOR (all 0-cells inside) "
    "with that color. The marker "
    "stays. Frame walls stay color "
    "5. Net: each gray frame's "
    "interior gets flooded with "
    "its marker color."
)

INVARIANTS = [
    "background is 0",
    "exactly 2 full-perimeter 5-color rectangle frames (each ≥4×4)",
    "each frame's strict interior holds exactly one non-0, non-5 marker cell",
    "frames don't touch each other",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "no_marker", "multiple_marker_colors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 11..14", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_frames":       {"type": "int", "default": "2", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "two_5_frames_with_marker",
                       "valid": "two_5_frames_with_marker"},
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
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 11, 12)
        n_frames = ctx.draw_int("n_frames", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 14, 17)
        n_frames = ctx.draw_int("n_frames", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 11, 14)
        n_frames = ctx.draw_int("n_frames", 2, 2)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    placed: list[tuple[int, int, int, int]] = []
    for _ in range(80):
        if len(placed) >= n_frames: break
        rh = rng.randint(4, 5)
        rw = rng.randint(4, 5)
        r1 = rng.randint(0, h - rh)
        c1 = rng.randint(0, w - rw)
        r2 = r1 + rh - 1
        c2 = c1 + rw - 1
        bb_pad = (r1 - 1, c1 - 1, r2 + 1, c2 + 1)
        if any(bbox_overlaps(bb_pad, (p[0]-1, p[1]-1, p[2]+1, p[3]+1)) for p in placed):
            continue
        placed.append((r1, c1, r2, c2))
    for r1, c1, r2, c2 in placed:
        draw_frame(g, r1, c1, r2, c2, 5)
        marker = rng.choice(list(random_palette(rng, 4, exclude={5})))
        sr = rng.randint(r1 + 1, r2 - 1)
        sc = rng.randint(c1 + 1, c2 - 1)
        g[sr][sc] = marker
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 13
    g = full_grid(h, w, 0)
    if name == "no_frames":
        # Markers but no 5-frames — rule's frame finder finds no
        # candidates; interior fill regions don't exist.
        g[3][3] = 4; g[5][8] = 6
        return g
    if name == "no_marker":
        # 5-frame but interior is empty — rule's "exactly one marker"
        # precondition fails (zero markers); flood color undefined.
        draw_frame(g, 1, 1, 6, 8, 5)
        return g
    if name == "multiple_marker_colors":
        # 5-frame with TWO distinct interior colors — rule's
        # "exactly one" precondition fails; flood color is ambiguous.
        draw_frame(g, 1, 1, 6, 8, 5)
        g[3][3] = 4; g[4][6] = 7
        return g
    return g


def _component_cells(grid, color):
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    comps = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != color or (sr, sc) in seen:
                continue
            q = [(sr, sc)]
            seen.add((sr, sc))
            comp = []
            while q:
                r, c = q.pop()
                comp.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        q.append((nr, nc))
            comps.append(comp)
    return comps


def _is_rect_frame(comp):
    rs = [r for r, _ in comp]
    cs = [c for _, c in comp]
    r1, r2 = min(rs), max(rs)
    c1, c2 = min(cs), max(cs)
    if r2 - r1 + 1 < 4 or c2 - c1 + 1 < 4:
        return None
    want = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
            if r in (r1, r2) or c in (c1, c2)}
    return (r1, c1, r2, c2) if set(comp) == want else None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for gray-frame seeded flood-fill rooms."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs: list[str] = []
    bad = sorted({v for row in grid for v in row if not isinstance(v, int) or v < 0 or v > 9})
    if bad:
        errs.append(f"cell values outside 0..9: {bad[:5]}")
    frames = []
    for comp in _component_cells(grid, 5):
        frame = _is_rect_frame(comp)
        if frame is None:
            errs.append("color-5 component is not a complete rectangular frame")
        else:
            frames.append(frame)
    if not frames:
        errs.append("expected at least one complete color-5 frame")
    for r1, c1, r2, c2 in frames:
        interior = [(r, c) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)]
        markers = [(r, c, grid[r][c]) for r, c in interior if grid[r][c] not in (0, 5)]
        marker_colors = {v for _, _, v in markers}
        if len(markers) != 1 or len(marker_colors) != 1:
            errs.append(f"frame {(r1, c1, r2, c2)} interior should contain exactly one non-0/non-5 marker")
    return errs
