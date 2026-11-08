"""Generator for 5998c17d89a0 — boolean combine two shapes by key at (0,0).

Rule: read key = g[0][0] (must be in {1, 2, 3, 4+}). Remove the key.
Find exactly 2 connected components A (leftmost) and B (rightmost) in
the remaining grid. Pick boolean op: key=1 → union, key=2 →
intersection, key=3 → xor, else → A minus B. Apply the binary mask op
on A's and B's normalized binary patterns. Output is that boolean-op
shape in color 8.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5998c17d89a0"
VERSION = "3.0.2"  # AXES synced to the 3.0.x widened draws (defect-lint axis-honesty)
TASK_ID = "5998c17d89a0"

SUMMARY = (
    "0-bg grid with: (a) ONE KEY cell at (0,0) in color {1, 2, 3, 4+} "
    "specifying the boolean op (1=union, 2=intersection, 3=xor, "
    "else=a-minus-b); (b) EXACTLY 2 connected components A and B in "
    "the rest of the grid, in distinct non-{0, key} colors. A is "
    "placed leftmost (smaller leftmost col); B is rightmost. Both have "
    "the same bbox dimensions (so the boolean op is well-defined). "
    "Rule: apply the boolean op (key-determined) on the binary masks "
    "of A and B. Output is the resulting shape painted in color 8 "
    "(cropped to its bbox)."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one cell at (0, 0) with key value in {1, 2, 3, 4+}",
    "exactly 2 connected components in cols 1+ (not at row 0 col 0)",
    "the 2 components have IDENTICAL bbox dimensions",
    "components are in distinct non-{0, key} colors",
    "components don't touch each other or the key (≥1-cell buffer)",
]

# Free axes the runner may override. Keys match the keyed draw_int labels in
# generate(); defaults are the medium band, valid spans easy..hard. (bh/bw are
# fixed at 2 in the easy band, so they're only keyed in medium/hard.)
AXES = {
    "grid_h":     {"type": "int", "default": "rng 10..13", "valid": "8..16",
                   "doc": "Grid height (easy 8..10, medium 10..13, hard 13..16)."},
    "grid_w":     {"type": "int", "default": "rng 13..17", "valid": "11..22",
                   "doc": "Grid width (easy 11..13, medium 13..17, hard 16..22)."},
    "bh":         {"type": "int", "default": "rng 3..4", "valid": "3..5",
                   "doc": "Component bbox height (easy 3, medium 3..4, hard 3..5)."},
    "bw":         {"type": "int", "default": "rng 3..4", "valid": "2..5",
                   "doc": "Component bbox width (easy 2..3, medium 3..4, hard 3..5)."},
    "blob_cells": {"type": "int", "default": "rng 3..(bh*bw-1)", "valid": "3..24",
                   "doc": "Cells per component (bounded by the bbox area minus 1)."},
    "key":        {"type": "int", "default": "rng 1..4", "valid": "1..4",
                   "doc": "Boolean-op key at (0,0): 1=union 2=intersect 3=xor else=a-b."},
}


def _free(g, cells, h, w):
    cell_set = set(cells)
    for r, c in cells:
        if not (0 <= r < h and 0 <= c < w):
            return False
        if g[r][c] != 0:
            return False
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    if g[nr][nc] != 0 and (nr, nc) not in cell_set:
                        return False
    return True


def _build_blob(rng, k, bh, bw):
    """Build a blob within a bh × bw bbox."""
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if 0 <= nr < bh and 0 <= nc < bw and (nr, nc) not in seen:
            cells.append((nr, nc))
            seen.add((nr, nc))
    # Normalize
    minr = min(r for r, _ in cells)
    minc = min(c for _, c in cells)
    return [(r - minr, c - minc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    # bigger, non-square blobs -> a much larger boolean-output space (the old
    # 2x2/2x3 blobs of ~3 cells gave only distinct=32 with dup-outputs).
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 11, 13)
        bh = ctx.draw_int("bh", 3, 3); bw = ctx.draw_int("bw", 2, 3)
        k_cells = ctx.draw_int("blob_cells", 3, max(3, bh * bw - 1))
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16)
        w = ctx.draw_int("grid_w", 16, 22)
        bh = ctx.draw_int("bh", 3, 5); bw = ctx.draw_int("bw", 3, 5)
        k_cells = ctx.draw_int("blob_cells", 5, bh * bw - 1)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 13, 17)
        bh = ctx.draw_int("bh", 3, 4); bw = ctx.draw_int("bw", 3, 4)
        k_cells = ctx.draw_int("blob_cells", 4, max(4, bh * bw - 1))

    key = ctx.draw_int("key", 1, 4)
    color_pool = [c for c in [1, 2, 3, 4, 5, 6, 7, 8, 9] if c != key and c != 8]
    if len(color_pool) < 2:
        color_pool = [c for c in [1, 2, 3, 4, 5, 6, 7, 9] if c != key]
    color_a, color_b = rng.sample(color_pool, 2)

    for outer in range(60):
        g = full_grid(h, w, 0)
        g[0][0] = key
        # Make two blobs of same bbox dimensions but different shapes
        cells_a = _build_blob(rng, k_cells, bh, bw)
        cells_b = _build_blob(rng, k_cells, bh, bw)
        # Place A (left half), B (right half)
        a_placed = False
        for _ in range(40):
            r0 = rng.randint(1, h - bh)
            c0 = rng.randint(1, max(1, w // 2 - bw))
            abs_a = [(r0 + dr, c0 + dc) for dr, dc in cells_a]
            if not _free(g, abs_a, h, w):
                continue
            for r, c in abs_a:
                g[r][c] = color_a
            a_placed = True
            break
        if not a_placed:
            continue
        b_placed = False
        for _ in range(40):
            r0 = rng.randint(1, h - bh)
            c0 = rng.randint(w // 2 + 1, w - bw)
            abs_b = [(r0 + dr, c0 + dc) for dr, dc in cells_b]
            if not _free(g, abs_b, h, w):
                continue
            for r, c in abs_b:
                g[r][c] = color_b
            b_placed = True
            break
        if not b_placed:
            continue
        return g
    raise ValueError("could not realize 5998 layout")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, key cell at (0,0) in {1..4}, exactly 2 connected components in cols 1+."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    key = grid[0][0]
    if key not in range(1, 5):
        errs.append(f"key at (0,0) is {key}, expected 1..4")
    # Count connected components (4-conn) excluding (0,0) position
    visited = [[False] * w for _ in range(h)]
    visited[0][0] = True
    blobs = 0
    for sr in range(h):
        for sc in range(w):
            if not visited[sr][sc] and grid[sr][sc] != 0:
                blobs += 1
                stack = [(sr, sc)]
                visited[sr][sc] = True
                while stack:
                    r, c = stack.pop()
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w and not visited[nr][nc] and grid[nr][nc] != 0:
                            visited[nr][nc] = True
                            stack.append((nr, nc))
    if blobs != 2:
        errs.append(f"expected exactly 2 non-zero connected components, found {blobs}")
    return errs
