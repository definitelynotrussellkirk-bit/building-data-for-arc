"""Generator for v0_original:easy_04.

Rule: cells in the left half (col < w/2) are mirrored to the right half
(col w-1-c).

Combinatorial axes (8): grid_h/w, palette_kind, num_marks,
palette_size, position_bias, n_distinct_colors, half_offset, texture.
Degenerates: already_symmetric, on_center_column, no_marks.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "69ebef53a2ac"
VERSION = "2.1.0"  # canonical-like connected one-color source component; clears object-count drift
TASK_ID = "69ebef53a2ac"
SUMMARY = (
    "0-bg grid (h~5-8, w~7-10) with 3-6 non-zero cells "
    "placed exclusively in the LEFT HALF (cols 0..w//2-1) "
    "in varied colors. RIGHT HALF (cols w//2..w-1) is all 0. "
    "Rule: for each cell (r, c) in output: if c < w//2 → "
    "keep input[r][c]. Else → mirror = input[r][w-1-c] "
    "(left-half value at the mirrored column). Net effect: "
    "the right half becomes a horizontal mirror image of the "
    "left half; result is a horizontally-symmetric grid."
)

# Rivals: 'rotate 180° instead of mirror' refuted by ≥2 demos where
# rotation would put cells on different rows. 'mirror only color X'
# refuted by ≥1 demo with multiple colors all mirrored. 'output left
# half only' refuted by any demo (right half is non-empty).
# 'mirror with new color' refuted by any demo (mirror cells match
# original colors).
# 4 demos with varied left-half patterns cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "one 4-connected, one-color non-zero component in the left half (cols 0..w/2-1)",
    "right half is all 0",
]

PALETTE_KINDS = ("default", "sparse", "dense", "rainbow")
DEGENERATE_TEXTURES = ("already_symmetric", "on_center_column", "no_marks")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..6", "valid": "3..10"},
    "grid_w":         {"type": "int", "default": "rng 6..8", "valid": "4..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|sparse|dense|rainbow"},
    "num_marks":      {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "9", "valid": "9"},
    "position_bias":  {"type": "str", "default": "left_half",
                       "valid": "left_half"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..4",
                          "valid": "1..9"},
    "half_offset":    {"type": "int", "default": "0", "valid": "0"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|sparse|dense|rainbow|already_symmetric|on_center_column|no_marks"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 3, 5)
        w = ctx.draw_int("grid_w", 6, 8)
        n_lo, n_hi = 3, 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 10, 12)
        n_lo, n_hi = 6, 12
    else:
        h = ctx.draw_int("grid_h", 5, 8)
        w = ctx.draw_int("grid_w", 7, 10)
        n_lo, n_hi = 4, 6
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    half = w // 2
    n = min(rng.randint(n_lo, n_hi), h * half)
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])

    # Canonical demos contain a single connected one-color source object, not
    # several independent marks.  Grow a random 4-connected polyomino entirely
    # inside the source half so the mirror rule is always demonstrated by one
    # coherent shape.
    blob = {(rng.randint(0, h - 1), rng.randint(0, half - 1))}
    for _ in range(400):
        if len(blob) >= n:
            break
        r, c = rng.choice(tuple(blob))
        nbrs = [(r + dr, c + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if 0 <= r + dr < h and 0 <= c + dc < half]
        rng.shuffle(nbrs)
        for cell in nbrs:
            if cell not in blob:
                blob.add(cell)
                break
    for r, c in blob:
        g[r][c] = color
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    half = w // 2
    marks = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    if not marks:
        errs.append("default path produced no non-zero marks")
    for r, c, _v in marks:
        if not (0 <= r < h and 0 <= c < half):
            errs.append("non-zero mark appears outside the source left half")
            break
    if any(grid[r][c] != 0 for r in range(h) for c in range(half, w)):
        errs.append("right half / center column is not blank before mirroring")
    colors = {v for _, _, v in marks}
    if len(colors) > 1:
        errs.append(f"source component should be one color, found {sorted(colors)}")
    cells = {(r, c) for r, c, _ in marks}
    if cells:
        stack = [next(iter(cells))]
        seen = {stack[0]}
        while stack:
            r, c = stack.pop()
            for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if (nr, nc) in cells and (nr, nc) not in seen:
                    seen.add((nr, nc)); stack.append((nr, nc))
        if seen != cells:
            errs.append("source marks should form one 4-connected component")
    if difficulty == "easy" and not (3 <= len(marks) <= 4):
        errs.append(f"easy should have 3-4 marks, found {len(marks)}")
    elif difficulty == "hard" and not (6 <= len(marks) <= 12):
        errs.append(f"hard should have 6-12 marks, found {len(marks)}")
    elif difficulty not in ("easy", "hard") and not (4 <= len(marks) <= 6):
        errs.append(f"medium/default should have 4-6 marks, found {len(marks)}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 5, 7
    g = full_grid(h, w, 0)
    if name == "already_symmetric":
        # both halves filled with mirror image — rule output equals input
        for r, c, v in [(1, 1, 4), (1, 5, 4), (3, 2, 7), (3, 4, 7)]:
            g[r][c] = v
        return g
    if name == "on_center_column":
        # cells on center column (odd width) mirror to themselves
        cc = w // 2
        g[1][cc] = 5
        g[3][cc] = 6
        return g
    if name == "no_marks":
        return g
    return g
