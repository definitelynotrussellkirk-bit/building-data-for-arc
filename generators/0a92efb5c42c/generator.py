"""Generator for arc_additional_puzzle_bank_volume4:H28 — label
intersection grid.

Rule: col-0 cells (rows >=1) with color in {1,2,3} are ROW labels;
row-0 cells (cols >=1) likewise are COLUMN labels. The output is
REBUILT: only the labels survive (body content, (0,0), and any
non-{1,2,3} header cell are erased), then every (r,c) where the row
label color EQUALS the column label color is painted that color.

Combinatorial axes: grid_h/w, n labels per axis, texture
(plain|invalid_mark|body_noise|corner_mark|multi_match).
Degenerates: no_row_markers, no_col_markers, no_match.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0a92efb5c42c"
VERSION = "2.0.0"
TASK_ID = "0a92efb5c42c"
SUMMARY = (
    "Row/column labels in colors 1-3; equal-color intersections "
    "paint. invalid_mark boards put colors 4-9 in the headers - those "
    "are NOT labels and get erased; body_noise boards scatter content "
    "that the rebuild wipes; corner_mark boards color (0,0), which is "
    "never a label; multi_match boards light a full intersection "
    "lattice. (Was: the SAME hardcoded 6-label layout every board - "
    "unique_in=8, RED.)"
)

# Rivals: 'any header color is a label' refuted by invalid_mark.
# 'body content survives' refuted by body_noise. '(0,0) is a label'
# refuted by corner_mark. 'one match per color' refuted by repeated
# same-color labels (full sub-lattice). 3-4 demos.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "main-path boards: >=1 row label matching >=1 column label color",
    "labels only in {1,2,3}; invalid_mark headers use 4-9 (erased)",
    "rebuild semantics: body always wiped before intersections paint",
]

DEGENERATE_TEXTURES = ("no_row_markers", "no_col_markers", "no_match")
HELPFUL_TEXTURES = ("plain", "invalid_mark", "body_noise", "corner_mark",
                    "multi_match")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 6..12", "valid": "5..16"},
    "grid_w":  {"type": "int", "default": "rng 6..12", "valid": "5..16"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|invalid_mark|body_noise|corner_mark|"
                         "multi_match|no_row_markers|no_col_markers|"
                         "no_match",
                "doc": "invalid_mark: non-{1,2,3} header cells erased; "
                       "body_noise: body wiped by the rebuild; "
                       "corner_mark: (0,0) is never a label."},
}


def _mirror(g):
    h, w = len(g), len(g[0])
    row_marks = [r for r in range(1, h) if g[r][0] in (1, 2, 3)]
    col_marks = [c for c in range(1, w) if g[0][c] in (1, 2, 3)]
    out = [[0] * w for _ in range(h)]
    for r in row_marks:
        out[r][0] = g[r][0]
    for c in col_marks:
        out[0][c] = g[0][c]
    for r in row_marks:
        for c in col_marks:
            if g[r][0] == g[0][c]:
                out[r][c] = g[r][0]
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain",
                                              "invalid_mark", "body_noise",
                                              "corner_mark", "multi_match"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 6, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 10, 12)
    else:
        h = ctx.draw_int("grid_h", 6, 12)
        w = ctx.draw_int("grid_w", 6, 12)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)

    if texture == "multi_match":
        row_colors = [1, 2, 3]
        col_colors = [1, 2, 3]
    else:
        row_colors = [rng.choice([1, 2, 3])
                      for _ in range(rng.randint(1, min(4, h - 2)))]
        col_colors = [rng.choice([1, 2, 3])
                      for _ in range(rng.randint(1, min(4, w - 2)))]
        if not set(row_colors) & set(col_colors):
            col_colors[0] = row_colors[0]  # guarantee >=1 match
    rows = rng.sample(range(1, h), min(len(row_colors), h - 1))
    cols = rng.sample(range(1, w), min(len(col_colors), w - 1))
    for r, color in zip(rows, row_colors):
        g[r][0] = color
    for c, color in zip(cols, col_colors):
        g[0][c] = color

    if texture == "invalid_mark":
        bad = rng.choice([4, 5, 6, 7, 8, 9])
        spots = []
        free_rows = [r for r in range(1, h) if g[r][0] == 0]
        free_cols = [c for c in range(1, w) if g[0][c] == 0]
        if free_rows:
            spots.append(("r", rng.choice(free_rows)))
        if free_cols:
            spots.append(("c", rng.choice(free_cols)))
        for kind, i in spots:
            if kind == "r":
                g[i][0] = bad
            else:
                g[0][i] = bad
    elif texture == "body_noise":
        for _ in range(rng.randint(3, 7)):
            r = rng.randint(1, h - 1)
            c = rng.randint(1, w - 1)
            g[r][c] = rng.randint(1, 9)
    elif texture == "corner_mark":
        g[0][0] = rng.choice([1, 2, 3])
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    row_labels = [(r, grid[r][0]) for r in range(1, h) if grid[r][0] in (1, 2, 3)]
    col_labels = [(c, grid[0][c]) for c in range(1, w) if grid[0][c] in (1, 2, 3)]
    if not row_labels:
        errors.append("expected at least one row label in colors 1..3")
    if not col_labels:
        errors.append("expected at least one column label in colors 1..3")
    if row_labels and col_labels and not ({v for _, v in row_labels} & {v for _, v in col_labels}):
        errors.append("main-path boards should include at least one matching row/column label color")
    if any(v < 0 or v > 9 for row in grid for v in row):
        errors.append("grid values must be digits 0..9")
    return errors


def _draw_from_degenerate(name, ctx):
    """no_row_markers / no_col_markers — one axis empty, no
    intersections (output = surviving labels only). no_match — both
    axes labeled with disjoint colors, intersections empty. rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 6, 10)
    w = ctx.draw_int("grid_w", 6, 10)
    g = full_grid(h, w, 0)
    if name != "no_row_markers":
        color_r = 1 if name == "no_match" else rng.choice([1, 2, 3])
        for r in rng.sample(range(1, h), rng.randint(1, 3)):
            g[r][0] = color_r if name == "no_match" \
                else rng.choice([1, 2, 3])
    if name != "no_col_markers":
        for c in rng.sample(range(1, w), rng.randint(1, 3)):
            g[0][c] = rng.choice([2, 3]) if name == "no_match" \
                else rng.choice([1, 2, 3])
    if name == "no_match":
        # force disjoint: rows all 1, cols drawn from {2,3} above
        for r in range(1, h):
            if g[r][0] != 0:
                g[r][0] = 1
    return g
