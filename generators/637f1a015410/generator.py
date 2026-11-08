"""Generator for arc_puzzle_bank_21_set4:S4_E7 — diagonal red dominoes recolor cyan.

Rule: red diagonal domino components are recolored cyan; axis-aligned
dominoes stay red.

Combinatorial axes (8): grid_h, grid_w, palette_kind, diagonal_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_diagonals, all_diagonals, no_dominoes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.place import place_no_overlap

GENERATOR_ID = "637f1a015410"
VERSION = "1.2.0"  # add executable domino-shape invariants
TASK_ID = "637f1a015410"

SUMMARY = "Red diagonal domino components are recolored cyan; axis-aligned dominoes stay red."

INVARIANTS = [
    "background is 0",
    "all input objects are red dominoes",
    "some dominoes are diagonal under 8-connectivity",
    "horizontal and vertical dominoes remain red",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_diagonals", "all_diagonals", "no_dominoes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "diagonal_count": {"type": "int", "default": "rng 1..3", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "diag_with_axis_distractors",
                       "valid": "diag_with_axis_distractors"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_DIAGONALS = [
    [(0, 0), (1, 1)],
    [(0, 1), (1, 0)],
]

_AXIS = [
    [(0, 0), (0, 1)],
    [(0, 0), (1, 0)],
]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        diagonal_count = ctx.draw_int("diagonal_count", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
        diagonal_count = ctx.draw_int("diagonal_count", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 8, 11)
        diagonal_count = ctx.draw_int("diagonal_count", 1, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    shapes = [rng.choice(_DIAGONALS) for _ in range(diagonal_count)]
    shapes.extend(rng.choice(_AXIS) for _ in range(rng.randint(1, 2)))
    rng.shuffle(shapes)
    for cells in shapes:
        if place_no_overlap(rng, g, cells, 2, padding=1, max_tries=400) is None:
            raise ValueError("could not place red domino")
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_diagonals":
        # only axis-aligned dominoes → rule has nothing to recolor
        g[1][1] = 2; g[1][2] = 2   # horizontal
        g[5][5] = 2; g[6][5] = 2   # vertical
        return g
    if name == "all_diagonals":
        # only diagonals → all recolored, no axis-aligned distractor for contrast
        g[1][1] = 2; g[2][2] = 2
        g[5][6] = 2; g[6][7] = 2
        return g
    if name == "no_dominoes":
        # blank → no objects at all
        return g
    return g

def _red_components8(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    dirs8 = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc]
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 2 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in dirs8:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 2
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(v not in range(10) for row in grid for v in row):
        errors.append("grid values must be digits 0..9")
    if not ({v for row in grid for v in row} <= {0, 2}):
        errors.append("normal sample may contain only background 0 and red 2")
    diag = axis = 0
    for cells in _red_components8(grid):
        if len(cells) != 2:
            errors.append("every red object must be a 2-cell domino under 8-connectivity")
            break
        (r0, c0), (r1, c1) = cells
        dr, dc = abs(r0 - r1), abs(c0 - c1)
        if dr == 1 and dc == 1:
            diag += 1
        elif dr + dc == 1:
            axis += 1
        else:
            errors.append("red domino cells must be adjacent orthogonally or diagonally")
            break
    if diag < (2 if difficulty == "hard" else 1):
        errors.append("normal sample must contain the expected diagonal domino target(s)")
    if axis < 1:
        errors.append("normal sample must include an axis-aligned red distractor")
    return errors
