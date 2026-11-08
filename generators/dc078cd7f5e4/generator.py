"""Generator for 18419cfa.

Rule: red cells inside a cyan frame are mirrored horizontally,
vertically and both.

Combinatorial axes (8): grid_h/w, frame_size, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias, n_red.
Degenerates: no_frame, no_red, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = "dc078cd7f5e4"
VERSION = "2.2.0"  # spacious 2D canvas + scattered frames (canonical h/area coverage); 30-box safe
TASK_ID = "dc078cd7f5e4"
SUMMARY = (
    "0-bg grid with one to three CYAN(8) rectangular frames (hollow outlines) "
    "of size 5-9 per side. Inside each frame interior, 1-3 RED(2) cells "
    "are placed (not on border), preferably in the top-left quadrant "
    "so the rule's mirror operations are visible. Rule: for each "
    "color-2 cell at (r, c) inside the frame, compute mirror "
    "positions: horizontal mirror (r, 2*cc - c), vertical mirror "
    "(2*cr - r, c), both (2*cr - r, 2*cc - c) where (cr, cc) is "
    "frame center. Paint each mirror position with 2 (if currently 0 "
    "and within frame). Output preserves frame + original reds + adds "
    "mirrored reds."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "1-3 cyan(8) rectangular frame outlines (5×5 to 9×9)",
    "1-3 red(2) cells inside each frame interior (not on border)",
    "red cells placed asymmetrically (so mirroring is visible)",
    "frame has ≥1-cell margin from grid borders",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_frame", "no_red", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "frame_size":     {"type": "int", "default": "rng 5..7", "valid": "5..11"},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "rng", "valid": "rng"},
    "n_frames":       {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "n_red":          {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_frame|no_red|full_grid"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    # The rule reflects color-2 cells across EACH color-8 frame's center; the old
    # gen drew ONE frame -> dup 49%. Place MULTIPLE frames at separated positions
    # with random interior 2s (asymmetric so the reflection adds cells).
    if difficulty == "easy":
        size_lo, size_hi = 5, 5; n_frames = ctx.draw_int("n_frames", 1, 1)
    elif difficulty == "hard":
        size_lo, size_hi = 7, 9; n_frames = ctx.draw_int("n_frames", 2, 3)
    else:
        size_lo, size_hi = 5, 7; n_frames = ctx.draw_int("n_frames", 1, 2)
    # Canonical demos put frames on a SPACIOUS 2D canvas (h median 18, wide
    # blank margins), not a tight one-row strip (defect-lint coverage: old
    # h topped out at 13, area ~81 vs canonical ~352). Draw a canvas with
    # canonical-scale margins and scatter the frames with >=2 separation.
    sizes = [rng.randint(size_lo, size_hi) for _ in range(n_frames)]
    need = max(sizes) + 2
    h = min(30, rng.randint(max(14, need + 4), max(20, need + 10)))
    w = min(30, rng.randint(max(14, need + 4), max(20, need + 10)))
    g = full_grid(h, w, 0)
    placed = []          # (r0, c0, size)
    for size in sizes:
        for _try in range(60):
            r0 = rng.randint(1, h - size - 1)
            c0 = rng.randint(1, w - size - 1)
            if all(r0 + size + 1 < pr or pr + ps + 1 < r0 or
                   c0 + size + 1 < pc or pc + ps + 1 < c0
                   for pr, pc, ps in placed):
                placed.append((r0, c0, size))
                break
    if not placed:
        raise ValueError("could not place any frame on the canvas")
    for r0, c0, size in placed:
        draw_rect_outline(g, r0, c0, size, size, 8)
        interior = [(r, c) for r in range(r0 + 1, r0 + size - 1)
                    for c in range(c0 + 1, c0 + size - 1)]
        # Place 2s strictly in the top-left quadrant relative to the frame's
        # reflection axes.  The old <= test allowed the exact center cell in odd
        # frames; a single center red mirrors only to itself, producing an
        # identity demo.  Strict quadrant placement guarantees at least one new
        # mirrored cell for every frame.
        r1 = r0 + size - 1
        c1 = c0 + size - 1
        quad = [(r, c) for (r, c) in interior
                if (2 * r < r0 + r1 and 2 * c < c0 + c1)]
        if quad:
            k = rng.randint(1, min(3, len(quad)))
            for r, c in rng.sample(quad, k):
                g[r][c] = 2
    if not any(2 in row for row in g):
        raise ValueError("could not place asymmetric red cells inside any frame")
    return g


def _frame_boxes(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    boxes = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != 8 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            comp = []
            while stack:
                r, c = stack.pop()
                comp.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 8 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rs = [r for r, _ in comp]
            cs = [c for _, c in comp]
            r0, r1 = min(rs), max(rs)
            c0, c1 = min(cs), max(cs)
            if r1 - r0 != c1 - c0:
                continue
            size = r1 - r0 + 1
            border = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                      if r in (r0, r1) or c in (c0, c1)}
            if set(comp) == border:
                boxes.append((r0, c0, r1, c1))
    return boxes


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    boxes = _frame_boxes(grid)
    if not boxes:
        errors.append("expected at least one cyan frame outline")
        return errors
    if len(boxes) > 3:
        errors.append(f"expected at most 3 cyan frames, found {len(boxes)}")
    any_visible = False
    for r0, c0, r1, c1 in boxes:
        size = r1 - r0 + 1
        if not (5 <= size <= 9):
            errors.append(f"frame size {size} outside 5..9")
        reds = [(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)
                if grid[r][c] == 2]
        if not reds:
            errors.append("frame has no interior red cell")
            continue
        for r, c in reds:
            mirrors = {(r, c), (r0 + r1 - r, c), (r, c0 + c1 - c), (r0 + r1 - r, c0 + c1 - c)}
            if len(mirrors) > 1 and any(grid[mr][mc] == 0 for mr, mc in mirrors):
                any_visible = True
    stray_red = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
                 if v == 2 and not any(r0 < r < r1 and c0 < c < c1 for r0, c0, r1, c1 in boxes)]
    if stray_red:
        errors.append("red cells must be inside cyan frame interiors")
    if not any_visible:
        errors.append("no red cell has a missing mirror counterpart; reflection branch hidden")
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 9, 0)
    if name == "no_frame":
        g[3][3] = 2
        return g
    if name == "no_red":
        draw_rect_outline(g, 1, 1, 6, 6, 8)
        return g
    if name == "full_grid":
        for r in range(9):
            for c in range(9):
                g[r][c] = 8
        return g
    return g
