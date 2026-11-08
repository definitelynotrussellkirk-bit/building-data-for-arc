"""Generator for arc_additional_puzzles_21_set11_bundle:H73 — Count bbox overlaps.

Rule: per-cell, count how many object bboxes contain it.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_frames,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: single_frame, frames_disjoint, frames_identical.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "59a9a5c505fb"
VERSION = "2.1.0"
TASK_ID = "59a9a5c505fb"
SUMMARY = (
    "0-bg grid with N (2-4) connected non-bg components, each in its "
    "own distinct color, with OVERLAPPING bounding boxes (typically "
    "nested rectangle frames). Rule: extract every 4-conn component "
    "(objects g 0); for each output cell (r, c), set output[r][c] = "
    "the count of objects whose bbox (r1,c1,r2,c2) contains (r,c) "
    "(i.e., r1≤r≤r2 AND c1≤c≤c2). Output is a count map; the original "
    "colors are DROPPED — values are integers 0..N."
)

# Rivals: 'output is input' refuted by demos (output is a count map).
# 'output is binary nonzero-mask' refuted by demos where ≥2 bboxes
# overlap (count 2+ visible). 'count visible cells, not bbox' refuted
# by demos where cells INSIDE a frame but not ON the frame have the
# same count as ON-frame cells (it's bbox not object membership).
# 'use frame color, not count' refuted by demos where outputs are
# small integers ≠ frame colors. 'count over Manhattan distance'
# refuted by demos with non-square bboxes. 3 demos with ≥2
# differently-overlapping bboxes (different counts at different cells)
# pin the bbox-count rule.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "≥2 connected non-bg components (the count rule is invisible with 1)",
    "components' bboxes overlap (else max count is 1 everywhere)",
    "components use distinct colors so each is its own component",
    "at least one cell achieves count ≥2 (so the rule's effect is visible)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("single_frame", "frames_disjoint", "frames_identical")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..13", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "8..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_frames":       {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "nested_frames",
                       "valid": "nested_frames"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..5"},
    "density":        {"type": "str", "default": "framed", "valid": "framed"},
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
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 8, 10)
        n_frames = ctx.draw_int("n_frames", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16)
        w = ctx.draw_int("grid_w", 13, 16)
        n_frames = ctx.draw_int("n_frames", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 10, 13)
        n_frames = ctx.draw_int("n_frames", 2, 3)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    color_rng = ctx.draw_rng("colors")
    colors = [c for c in range(2, 10)]
    color_rng.shuffle(colors)
    # Construct a bbox with enough slack for the requested number of nested
    # frames.  The old random 1..3 shrink loop silently broke early (for
    # example, easy produced a single frame in 643/1000 sampled seeds), hiding
    # the bbox-overlap/count>=2 rule.  Unit-step nesting preserves variation in
    # the outer bbox while guaranteeing every requested frame is realizable.
    min_span = 3 + 2 * (n_frames - 1)
    if h < min_span or w < min_span:
        raise ValueError("grid too small for requested nested frames")
    box_h = rng.randint(min_span, h)
    box_w = rng.randint(min_span, w)
    r1 = rng.randint(0, h - box_h)
    c1 = rng.randint(0, w - box_w)
    r2 = r1 + box_h - 1
    c2 = c1 + box_w - 1
    frames = [(r1 + i, c1 + i, r2 - i, c2 - i, colors[i])
              for i in range(n_frames)]
    for fr1, fc1, fr2, fc2, col in frames:
        for c in range(fc1, fc2 + 1):
            g[fr1][c] = col
            g[fr2][c] = col
        for r in range(fr1, fr2 + 1):
            g[r][fc1] = col
            g[r][fc2] = col
    return g


def _draw_from_degenerate(name, rng):
    h, w = 11, 11
    g = full_grid(h, w, 0)
    if name == "single_frame":
        # one frame only → counts are all 0 or 1, no nesting depth visible
        for c in range(2, 9):
            g[2][c] = 4; g[8][c] = 4
        for r in range(2, 9):
            g[r][2] = 4; g[r][8] = 4
        return g
    if name == "frames_disjoint":
        # frames don't overlap → each cell is in at most 1 bbox, no count gradient
        for c in range(1, 4):
            g[1][c] = 4; g[3][c] = 4
        for r in range(1, 4):
            g[r][1] = 4; g[r][3] = 4
        for c in range(6, 10):
            g[6][c] = 6; g[9][c] = 6
        for r in range(6, 10):
            g[r][6] = 6; g[r][9] = 6
        return g
    if name == "frames_identical":
        # two frames at the exact same bbox → counts are identical (overlapping but same shape)
        for c in range(2, 9):
            g[2][c] = 4; g[8][c] = 4
        for r in range(2, 9):
            g[r][2] = 4; g[r][8] = 4
        # second frame at same bbox in different color (would draw over)
        for c in range(2, 9):
            g[2][c] = 6; g[8][c] = 6
        for r in range(2, 9):
            g[r][2] = 6; g[r][8] = 6
        return g
    return g


def _sc_color_components(grid, bg=0):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == bg or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append((color, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(v not in range(10) for row in grid for v in row):
        errors.append("grid values must be digits 0..9")
    comps = _sc_color_components(grid, 0)
    expected_min = 3 if difficulty == "hard" else 2
    if len(comps) < expected_min:
        errors.append(f"expected at least {expected_min} nested frame components, got {len(comps)}")
    colors = [color for color, _ in comps]
    if len(colors) != len(set(colors)):
        errors.append("frame colors must be distinct")
    boxes = []
    for _color, cells in comps:
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        boxes.append((min(rs), min(cs), max(rs), max(cs)))
    if len(boxes) >= 2:
        rlo = max(b[0] for b in boxes); clo = max(b[1] for b in boxes)
        rhi = min(b[2] for b in boxes); chi = min(b[3] for b in boxes)
        if rlo > rhi or clo > chi:
            errors.append("frame bounding boxes must overlap")
    return errors
