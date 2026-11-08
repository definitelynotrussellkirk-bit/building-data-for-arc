"""Generator for puzzle 6e82a1ae.

Rule: for each non-bg 4-connected object: size 4 → 1, 3 → 2, 2 → 3,
else → 5.

Combinatorial axes: grid_h/w, n_size4, n_size3, n_size2, n_other,
input_color (any non-{0,1,2,3}).
Degenerates: only_size4, only_size3, only_size2, mixed_with_other.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.shape import normalize, rect_cells
from puzzle_generators.helpers.place import place_no_overlap

GENERATOR_ID = "154382a9e3e8"
# 2.1.0: reverse-diversity / branch-coverage -- default path placed only sizes
# 2,3,4, never exercising the rule's else->5 (gray) branch (size 1 or >=5). Now
# sometimes add size-1 and size-5+ components, and use non-rectangular polyomino
# shapes for all sizes (rule keys only on cell count).
VERSION = "2.2.0"  # use padding=1 so size-coded components cannot merge; strengthen self_check
TASK_ID = "154382a9e3e8"
SUMMARY = (
    "0-bg grid (h, w ~11-18) with 4-conn rectangular "
    "components in sizes 2, 3, and 4 (1-3 components of "
    "each size), all in a SINGLE input color drawn from "
    "{4..9} (so input color != target output colors). "
    "Components are non-overlapping with ≥1-cell margin. "
    "Rule: extract every 4-conn non-bg object. Recolor "
    "each based on its CELL COUNT: size 4 → color 1 "
    "(blue), size 3 → color 2 (red), size 2 → color 3 "
    "(green), any other size → color 5 (gray). Input "
    "color is discarded; output uses the size-keyed "
    "palette."
)

INVARIANTS = [
    "background is 0",
    "≥1 component of size 4 (becomes 1)",
    "≥1 component of size 3 (becomes 2)",
    "≥1 component of size 2 (becomes 3)",
    "components 4-connected, non-overlapping with margin ≥ 1",
]

DEGENERATE_TEXTURES = ("only_size4", "only_size3", "only_size2", "with_size_5plus")
HELPFUL_TEXTURES = ("balanced_each_size",)

AXES = {
    "grid_h":      {"type": "int", "default": "rng 11..18", "valid": "10..22"},
    "grid_w":      {"type": "int", "default": "rng 11..18", "valid": "10..22"},
    "n_size4":     {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "n_size3":     {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "n_size2":     {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "input_color": {"type": "color", "default": "rng (≠0,1,2,3)", "valid": "4..9"},
    "texture":     {"type": "str", "default": "rng helpful",
                    "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify normal examples cover size->color branches 2, 3, and 4."""
    if not isinstance(grid, list) or not grid or any(not isinstance(row, list) for row in grid):
        return ["grid must be a non-empty rectangular list"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid rows are ragged"]
    if h == 1 and w == 1 and grid[0][0] == 0:
        return ["fallback empty grid emitted"]
    colors = {v for row in grid for v in row if v != 0}
    if len(colors) != 1:
        return [f"components should share one input color, got {sorted(colors)}"]
    if colors & {1, 2, 3}:
        return [f"input uses reserved output colors 1/2/3: {sorted(colors)}"]
    seen = set(); sizes = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 and (r, c) not in seen:
                stack = [(r, c)]; seen.add((r, c)); cells = []
                while stack:
                    cr, cc = stack.pop(); cells.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0 and (nr, nc) not in seen:
                            seen.add((nr, nc)); stack.append((nr, nc))
                sizes.append(len(cells))
    errs = []
    for need in (2, 3, 4):
        if need not in sizes:
            errs.append(f"missing component of size {need}")
    return errs

def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, n_lo, n_hi = 11, 13, 1, 1
    elif difficulty == "hard":
        h_lo, h_hi, n_lo, n_hi = 16, 18, 2, 3
    else:
        h_lo, h_hi, n_lo, n_hi = 11, 18, 1, 3
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_4 = int(overrides.get("n_size4", ctx.draw_int("n_size4", n_lo, n_hi)))
    n_3 = int(overrides.get("n_size3", ctx.draw_int("n_size3", n_lo, n_hi)))
    n_2 = int(overrides.get("n_size2", ctx.draw_int("n_size2", n_lo, n_hi)))
    color = int(overrides.get("input_color",
                              ctx.draw_color("input_color", exclude={0, 1, 2, 3})))
    # Occasionally also place "other"-size components (size 1 or >=5) to exercise
    # the rule's else->5 branch.
    n_other = rng.randint(0, 2)
    g = full_grid(h, w, 0)
    placed = {4: 0, 3: 0, 2: 0}
    for size, n_target in [(4, n_4), (3, n_3), (2, n_2)]:
        for _ in range(n_target * 4):
            if placed[size] >= n_target:
                break
            shape = _shape_for_size(size, rng)
            if place_no_overlap(rng, g, shape, color, bg=0, margin=1, padding=1, max_tries=160):
                placed[size] += 1
    for _ in range(n_other):
        osize = rng.choice([1, 5, 6, 7])
        shape = _poly(rng, osize)
        place_no_overlap(rng, g, shape, color, bg=0, margin=1, padding=1, max_tries=160)
    if any(v < 1 for v in placed.values()):
        return [[0]]
    return g


def _poly(rng, n):
    """Random connected polyomino of n cells, normalized."""
    cells = {(0, 0)}
    while len(cells) < n:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        cells.add((r + dr, c + dc))
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _shape_for_size(size, rng):
    if size == 4:
        return normalize(rect_cells(*rng.choice([(2, 2), (1, 4), (4, 1)])))
    if size == 3:
        return normalize(rect_cells(*rng.choice([(1, 3), (3, 1)])))
    if size == 2:
        return normalize(rect_cells(*rng.choice([(1, 2), (2, 1)])))
    if size == 5:
        return normalize([(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)])
    return normalize(rect_cells(2, 2))


def _draw_from_degenerate(name, h, w, rng):
    color = rng.choice([4, 5, 6, 7, 8, 9])
    g = full_grid(h, w, 0)
    if name == "only_size4":
        for _ in range(4):
            place_no_overlap(rng, g, _shape_for_size(4, rng), color,
                             bg=0, margin=1, padding=1, max_tries=160)
        return g
    if name == "only_size3":
        for _ in range(4):
            place_no_overlap(rng, g, _shape_for_size(3, rng), color,
                             bg=0, margin=1, padding=1, max_tries=160)
        return g
    if name == "only_size2":
        for _ in range(4):
            place_no_overlap(rng, g, _shape_for_size(2, rng), color,
                             bg=0, margin=1, padding=1, max_tries=160)
        return g
    if name == "with_size_5plus":
        for _ in range(2):
            place_no_overlap(rng, g, _shape_for_size(5, rng), color,
                             bg=0, margin=1, padding=1, max_tries=160)
        return g
    return g
