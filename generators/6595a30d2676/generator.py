"""Generator for arc_puzzle_bank_21_set4_d:hard_d02 — rotate each framed shape.

REAL rule (verified from canonical Racket): the grid holds rectangular
FRAMES (>=3x3 outlines) whose color is in {1,2,3,4}. Each frame encloses an
inner shape (a different non-bg color). The output rotates each frame's inner
shape by (frame_color - 1) quarter-turns (1=0 turns, 2=CW, 3=180, 4=CCW),
re-centers it in the interior, and keeps the frame. Output size == input size.

The previous 2.0.0 body drew SCATTERED MOTIFS (no frames at all), so the rule
found zero frames and emitted a BLANK grid for every input (only ~9 distinct
outputs = the distinct grid sizes). This 3.0.0 rewrite builds genuine frames
with inner shapes: frame color in {1,2,3,4} (the rotation key, varied), inner
color in {5,6,7,8,9}, frame size/count/inner-shape all random.

Degenerates: no_frames, single_frame, frame_no_interior.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6595a30d2676"
VERSION = "3.0.1"  # WRONG-TASK rewrite: drew scattered motifs (no frames) -> rule emitted blank grids (9 outputs). Now build real frames (color 1..4) + inner shapes (color 5..9); output rotates each inner shape by frame_color-1 quarter-turns.
TASK_ID = "6595a30d2676"

SUMMARY = (
    "0-bg grid with several rectangular FRAMES (square outlines, side in "
    "{5,7,9}) whose color is in {1,2,3,4} (the per-frame ROTATION KEY: "
    "1=identity, 2=CW, 3=180, 4=CCW). Each frame encloses a random inner "
    "polyomino in a color from {5,6,7,8,9}. Frames are >=2 cells apart so each "
    "is its own component. Rule: for every {1,2,3,4}-colored frame, crop the "
    "interior shape, ROTATE it by (frame_color - 1) quarter-turns, re-centre it "
    "in the interior, and keep the frame. Output size == input size."
)

INVARIANTS = [
    "background is 0",
    "each frame is a complete rectangular outline (>=3x3) in a color in {1,2,3,4}",
    "each frame encloses a non-empty inner shape in a color in {5,6,7,8,9}",
    "frames are separated by >=1 bg cell (distinct components)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "single_frame", "frame_no_interior")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 14..22", "valid": "9..28"},
    "grid_w":         {"type": "int", "default": "rng 14..24", "valid": "9..28"},
    "n_frames":       {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "frame_side":     {"type": "int", "default": "rng {5,7,9}", "valid": "5..9"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "position_bias":  {"type": "str", "default": "scattered_frames",
                       "valid": "scattered_frames"},
    "n_distinct_colors": {"type": "int", "default": "rng", "valid": "2..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 cell with color in {1,2,3,4} (frame); ≥1 with color in {5..9} (inner)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    has_frame = any(grid[r][c] in (1, 2, 3, 4)
                    for r in range(h) for c in range(w))
    has_inner = any(grid[r][c] in (5, 6, 7, 8, 9)
                    for r in range(h) for c in range(w))
    if not has_frame:
        errs.append("no frame cells (colors 1..4) found")
    if not has_inner:
        errs.append("no inner shape cells (colors 5..9) found")
    return errs


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _rand_poly(rng, maxh, maxw, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    for _ in range(200):
        if len(cells) >= k:
            break
        br, bc = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = br + dr, bc + dc
        if (nr, nc) not in seen and 0 <= nr < maxh and 0 <= nc < maxw:
            cells.append((nr, nc)); seen.add((nr, nc))
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    r0, c0 = min(rs), min(cs)
    return [(r - r0, c - c0) for r, c in cells]


def _draw_frame_with_shape(g, r0, c0, side, frame_color, inner_color, rng):
    # square outline in frame_color
    for c in range(c0, c0 + side):
        g[r0][c] = frame_color
        g[r0 + side - 1][c] = frame_color
    for r in range(r0, r0 + side):
        g[r][c0] = frame_color
        g[r][c0 + side - 1] = frame_color
    # inner random polyomino in inner_color (strictly inside, never full)
    intsz = side - 2
    k = rng.randint(2, max(2, intsz * intsz - 1))
    poly = _rand_poly(rng, intsz, intsz, k)
    for dr, dc in poly:
        g[r0 + 1 + dr][c0 + 1 + dc] = inner_color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 12, 16)
        n = ctx.draw_int("n_frames", 2, 2); sides = [5]
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 20, 28); w = ctx.draw_int("grid_w", 22, 28)
        n = ctx.draw_int("n_frames", 4, 5); sides = [5, 7, 9]
    else:
        h = ctx.draw_int("grid_h", 16, 24); w = ctx.draw_int("grid_w", 16, 24)
        n = ctx.draw_int("n_frames", 2, 4); sides = [5, 7]
    g = full_grid(h, w, 0)
    placed = 0
    for _ in range(n * 60):
        if placed >= n:
            break
        side = rng.choice(sides)
        if side + 1 > h or side + 1 > w:
            side = 5
        r0 = rng.randint(0, h - side); c0 = rng.randint(0, w - side)
        if not _free(g, r0, c0, r0 + side - 1, c0 + side - 1):
            continue
        frame_color = rng.choice([1, 2, 3, 4])     # the rotation key (varied)
        inner_color = rng.choice([5, 6, 7, 8, 9])  # never confused with a frame
        _draw_frame_with_shape(g, r0, c0, side, frame_color, inner_color, rng)
        placed += 1
    if placed == 0:  # guarantee a non-empty, rule-firing scene
        _draw_frame_with_shape(g, 0, 0, 5, 2, 6, rng)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    if name == "no_frames":
        # scattered cells, no complete frame -> rule emits a blank grid
        for r, c in [(2, 2), (2, 3), (6, 7), (9, 1)]:
            g[r][c] = 5
        return g
    if name == "single_frame":
        _draw_frame_with_shape(g, 1, 1, 5, 3, 7, rng)
        return g
    if name == "frame_no_interior":
        # complete frame but empty interior -> crop-nonzero is trivial
        for c in range(1, 6):
            g[1][c] = 2; g[5][c] = 2
        for r in range(1, 6):
            g[r][1] = 2; g[r][5] = 2
        return g
    return g
