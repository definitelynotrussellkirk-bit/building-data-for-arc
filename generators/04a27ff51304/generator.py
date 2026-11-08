"""Generator for arc_puzzle_bank_21_set8_s:S8_M2 — long-run crossings.

Rule: cells where a row-run of length ≥3 crosses a col-run of length ≥3
get painted 8. Other cells become 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_lines,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_lines, only_horizontal, no_crossings.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "04a27ff51304"
VERSION = "2.1.0"  # add executable same-color-crossing self_check
TASK_ID = "04a27ff51304"
SUMMARY = (
    "SAME-COLOR crosses: a horizontal and a vertical line of one color "
    "crossing (the crossing cell joins a row-run >=3 AND a col-run >=3 "
    "of that color, so the rule paints it 8). Decoy content — "
    "different-color crossings (the runs break at the crossing) and "
    "non-crossing lines — yields no 8. (The OLD generator gave every "
    "line a distinct color and skipped occupied cells, so the rule "
    "NEVER fired: every output was an all-zero grid.)"
)

# Rivals: 'any crossing counts' refuted by different-color crossings
# that stay unpainted. 'output is blank' refuted by same-color crosses
# producing 8s. 'paint the whole cross' refuted (only the crossing
# cell). 3 demos incl. >=1 decoy crossing.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    ">=1 SAME-COLOR h+v crossing (output non-empty — the rule needs "
    "the crossing cell inside runs >=3 both ways)",
    "decoy content (when present) yields no extra 8s",
]

DEGENERATE_TEXTURES = ("no_lines", "no_crossings")
HELPFUL_TEXTURES = ("plain", "decoy_cross", "decoy_lines")

AXES = {
    "grid_h":    {"type": "int", "default": "rng 7..10 (hard 9..13)",
                  "valid": "6..14", "doc": "Grid height."},
    "grid_w":    {"type": "int", "default": "rng 8..11 (hard 10..14)",
                  "valid": "7..14", "doc": "Grid width."},
    "n_crosses": {"type": "int", "default": "rng 1..2", "valid": "1..2",
                  "doc": "Same-color crossings (each painted 8)."},
    "texture":   {"type": "str", "default": "rng helpful",
                  "valid": "plain|decoy_cross|decoy_lines|no_lines|no_crossings",
                  "doc": "decoy_cross: a different-color crossing (no 8); "
                         "decoy_lines: extra non-crossing lines."},
}


def _draw_cross(g, rng, color, taken_rows, taken_cols):
    """Same-color h+v lines crossing; returns True if placed."""
    h, w = len(g), len(g[0])
    for _ in range(60):
        r = rng.randint(1, h - 2)
        c = rng.randint(1, w - 2)
        if r in taken_rows or c in taken_cols:
            continue
        # horizontal span around (r, c), >=3 long, containing c
        c1 = rng.randint(max(0, c - 3), c - 1)
        c2 = rng.randint(c + 1, min(w - 1, c + 3))
        r1 = rng.randint(max(0, r - 3), r - 1)
        r2 = rng.randint(r + 1, min(h - 1, r + 3))
        if c2 - c1 < 2 or r2 - r1 < 2:
            continue
        cells = [(r, cc) for cc in range(c1, c2 + 1)] + \
                [(rr, c) for rr in range(r1, r2 + 1)]
        if any(g[rr][cc] != 0 and (rr, cc) != (r, c) for rr, cc in cells):
            continue
        for rr, cc in cells:
            g[rr][cc] = color
        taken_rows.update(range(r1, r2 + 1))
        taken_cols.update(range(c1, c2 + 1))
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "decoy_cross", "decoy_lines"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 10, 14)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 11)
    n_crosses = int(overrides.get("n_crosses", ctx.draw_int("n_crosses", 1, 2)))
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 4)
    taken_rows, taken_cols = set(), set()

    placed = 0
    for i in range(n_crosses):
        if _draw_cross(g, rng, palette[i], taken_rows, taken_cols):
            placed += 1
    if placed == 0:
        # guaranteed minimal cross
        r, c = h // 2, w // 2
        for cc in range(c - 1, c + 2):
            g[r][cc] = palette[0]
        for rr in range(r - 1, r + 2):
            g[rr][c] = palette[0]
        taken_rows.update(range(r - 1, r + 2))
        taken_cols.update(range(c - 1, c + 2))

    if texture == "decoy_cross":
        # different-color crossing: the v-line breaks the h-run at the
        # crossing (and vice versa) — no cell is in both runs, no 8
        for _ in range(60):
            r = rng.randint(1, h - 2)
            c = rng.randint(1, w - 2)
            if r in taken_rows or c in taken_cols:
                continue
            ok = all(g[r][cc] == 0 for cc in range(max(0, c - 2), min(w, c + 3))) \
                and all(g[rr][c] == 0 for rr in range(max(0, r - 2), min(h, r + 3)))
            if not ok:
                continue
            for cc in range(max(0, c - 2), min(w, c + 3)):
                g[r][cc] = palette[2]
            for rr in range(max(0, r - 2), min(h, r + 3)):
                if g[rr][c] == 0:
                    g[rr][c] = palette[3]
            break
    elif texture == "decoy_lines":
        for _ in range(60):
            r = rng.randint(0, h - 1)
            if r in taken_rows:
                continue
            c1 = rng.randint(0, w - 4)
            if any(g[r][cc] != 0 for cc in range(c1, c1 + 3)):
                continue
            for cc in range(c1, c1 + 3):
                g[r][cc] = palette[3]
            break
    return g


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied so each board differs.

    no_lines     — blank: output all-zero.
    no_crossings — parallel lines only: no cell is in two runs.
    """
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 7, 9)
    w = ctx.draw_int("grid_w", 8, 10)
    g = full_grid(h, w, 0)
    if name == "no_lines":
        return g
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 9])
    for r in rng.sample(range(h), 2):
        c1 = rng.randint(0, w - 4)
        for cc in range(c1, c1 + 3):
            g[r][cc] = color
    return g


def _run_len(grid, r, c, dr, dc):
    color = grid[r][c]
    if color == 0:
        return 0
    h, w = len(grid), len(grid[0])
    n = 1
    rr, cc = r + dr, c + dc
    while 0 <= rr < h and 0 <= cc < w and grid[rr][cc] == color:
        n += 1; rr += dr; cc += dc
    rr, cc = r - dr, c - dc
    while 0 <= rr < h and 0 <= cc < w and grid[rr][cc] == color:
        n += 1; rr -= dr; cc -= dc
    return n


def _cross_targets(grid):
    return [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
            if v != 0 and _run_len(grid, r, c, 0, 1) >= 3 and _run_len(grid, r, c, 1, 0) >= 3]


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    targets = _cross_targets(grid)
    if not targets:
        errs.append("expected at least one same-color long-run crossing target")
    if difficulty == "easy" and len(targets) > 2:
        errs.append(f"easy mode should stay small; found {len(targets)} crossing targets")
    bad = [v for row in grid for v in row if v == 8]
    if bad:
        errs.append("input should not already contain output color 8")
    return errs
