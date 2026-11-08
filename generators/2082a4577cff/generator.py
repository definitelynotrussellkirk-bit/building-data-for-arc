"""Generator for puzzle 15696249.

Rule: 3x3 grid. Find rows/cols that are uniform. Output 9x9 tiles only
at uniform-row blocks or uniform-col blocks.

Combinatorial axes (8): n_uniform_rows, n_uniform_cols, palette_kind,
palette_size, uniform_position, anchor_corner, asymmetry_force,
include_diagonal.
Degenerates: all_uniform, no_uniform, monochrome.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2082a4577cff"
VERSION = "2.0.0"  # shape-locked in/out (fixed n=3 -> 3x3 in / 9x9 out). Rule generalizes to any square n x n -> n^2 x n^2; now vary n (3-5, capped so n^2<=25<=30 canvas). Replaced n=3-specific named positions with general random uniform row/col indices.
TASK_ID = "2082a4577cff"
SUMMARY = "n x n grid (n=3..5); rule tiles an n^2 x n^2 output, placing the grid only at the block-row of the first uniform row and the block-col of the first uniform column."

INVARIANTS = [
    "grid is square n x n (n=3..5)",
    ">=1 uniform row OR >=1 uniform col (else the rule blanks the output)",
    "non-uniform rows/cols have >=2 distinct values",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
UNIFORM_POSITIONS = ("top_row", "middle_row", "bottom_row",
                     "left_col", "middle_col", "right_col", "rng")
DEGENERATE_TEXTURES = ("all_uniform", "no_uniform", "monochrome")
HELPFUL_TEXTURES = UNIFORM_POSITIONS

AXES = {
    "grid_n":           {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "n_uniform_rows":   {"type": "int", "default": "rng 0..1", "valid": "0..3"},
    "n_uniform_cols":   {"type": "int", "default": "rng 0..1", "valid": "0..3"},
    "palette_kind":     {"type": "str", "default": "rng helpful",
                         "valid": "|".join(PALETTE_KINDS)},
    "palette_size":     {"type": "int", "default": "3", "valid": "2..6"},
    "uniform_position": {"type": "str", "default": "rng helpful",
                         "valid": "|".join(UNIFORM_POSITIONS)},
    "anchor_corner":    {"type": "bool", "default": "false",
                         "valid": "true|false"},
    "texture":          {"type": "str", "default": "alias for uniform_position",
                         "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], ctx.draw_rng("degen"))
    # the rule works for any SQUARE n x n input -> n^2 x n^2 output. Was hardcoded
    # n=3 (in=1 out=1). Vary n (cap 5 so n^2 <= 25 <= the 30 canvas) -> output dims vary.
    if difficulty == "easy":
        n = ctx.draw_int("grid_n", 3, 3)
    elif difficulty == "hard":
        n = ctx.draw_int("grid_n", 4, 5)
    else:
        n = ctx.draw_int("grid_n", 3, 5)
    rng = ctx.draw_rng("layout")
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    palette_size = int(overrides.get("palette_size", min(6, n + 1)))
    palette_size = max(2, min(6, palette_size))
    palette = _build_palette(palette_kind, palette_size, rng)
    n_urows = int(overrides.get("n_uniform_rows",
                                ctx.draw_int("n_uniform_rows", 0, 1)))
    n_ucols = int(overrides.get("n_uniform_cols",
                                ctx.draw_int("n_uniform_cols", 0, 1)))
    if n_urows + n_ucols == 0:
        # the rule blanks the output unless >=1 uniform row OR column exists -> force one
        if rng.random() < 0.5:
            n_urows = 1
        else:
            n_ucols = 1
    # Draw/reject rather than accepting accidental default degenerates.  The
    # random fill plus one forced uniform row/col can occasionally make every
    # row or every column uniform (a texture already reserved for the explicit
    # all_uniform/monochrome degenerate overrides).  Keep the normal path
    # pedagogically useful: at least one, but not all, row/col bands fire.
    last = None
    for _attempt in range(80):
        g = [[rng.choice(palette) for _ in range(n)] for _ in range(n)]
        for ur in rng.sample(range(n), min(n_urows, n)):
            c = rng.choice(palette)
            for k in range(n):
                g[ur][k] = c
        for uc in rng.sample(range(n), min(n_ucols, n)):
            c = rng.choice(palette)
            for k in range(n):
                g[k][uc] = c
        last = g
        if _default_ok(g):
            return g
    # Extremely unlikely; still deterministic and still rule-compatible.
    return last


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 6, 7, 8, 9]
    rng.shuffle(pool)
    while len(pool) < n:
        for c in [1, 2, 3, 4, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
    return pool[:n]


def _draw_from_degenerate(name, rng):
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 3)
    if name == "all_uniform":
        c = palette[0]
        return [[c] * 3 for _ in range(3)]
    if name == "no_uniform":
        # 3x3 with no uniform row/col
        return [[palette[0], palette[1], palette[2]],
                [palette[1], palette[2], palette[0]],
                [palette[2], palette[0], palette[1]]]
    if name == "monochrome":
        return [[palette[0]] * 3 for _ in range(3)]
    return [[palette[0]] * 3 for _ in range(3)]


def _uniform_rows_cols(g):
    n = len(g)
    urows = [r for r in range(n) if len(set(g[r])) == 1]
    ucols = [c for c in range(n) if len({g[r][c] for r in range(n)}) == 1]
    return urows, ucols


def _default_ok(g):
    if not g or any(len(row) != len(g) for row in g):
        return False
    n = len(g)
    if n < 3 or n > 5:
        return False
    urows, ucols = _uniform_rows_cols(g)
    if not urows and not ucols:
        return False
    # All row-bands or all col-bands firing hides the selection rule; those
    # belong to explicit degenerate textures, not ordinary training rows.
    if len(urows) == n or len(ucols) == n:
        return False
    return True


def self_check(grid, *, difficulty=None, meta=None):
    problems = []
    if not isinstance(grid, list) or not grid or not all(isinstance(r, list) for r in grid):
        return ["grid is not a nonempty 2D list"]
    n = len(grid)
    if any(len(row) != n for row in grid):
        problems.append("input must be square n x n")
        return problems
    if difficulty == "easy" and n != 3:
        problems.append("easy examples should stay 3x3")
    elif difficulty == "hard" and n not in (4, 5):
        problems.append("hard examples should be 4x4 or 5x5")
    elif difficulty is None and n not in (3, 4, 5):
        problems.append("default examples should be 3x3..5x5")
    urows, ucols = _uniform_rows_cols(grid)
    if not urows and not ucols:
        problems.append("at least one uniform row or column is required")
    if len(urows) == n or len(ucols) == n:
        problems.append("default path leaked all-uniform/monochrome degenerate")
    return problems
