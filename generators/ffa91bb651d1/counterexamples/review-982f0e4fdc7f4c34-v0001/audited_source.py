"""Generator for arc_puzzle_bank_fifth_21_bundle:easy_32_fill_between_row_endpoints.

Rule: rows with two same-color endpoints have the cells between them filled.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_spans,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_endpoints, mismatched_endpoints, single_endpoint.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ffa91bb651d1"
VERSION = "2.0.0"
TASK_ID = "ffa91bb651d1"
SUMMARY = "Rows with two matching endpoint cells are filled across."

INVARIANTS = [
    "background is 0",
    "target rows have exactly two nonzero cells",
    "the two target cells share a color",
    "0-3 decoy rows (single cell / 3 same-color / 2 mismatched) that the rule leaves untouched",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_endpoints", "mismatched_endpoints", "single_endpoint")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "6..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_spans":        {"type": "int", "default": "2 easy / 3-6 med / 5-9 hard", "valid": "1..15"},
    "palette_size":   {"type": "int", "default": "9", "valid": "2..9"},
    "position_bias":  {"type": "str", "default": "row_endpoints_with_decoys",
                       "valid": "row_endpoints_with_decoys"},
    "n_distinct_colors": {"type": "int", "default": "up to 9", "valid": "2..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
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
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 7, 11)
        n_spans = ctx.draw_int("n_spans", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16)
        w = ctx.draw_int("grid_w", 12, 16)
        n_spans = ctx.draw_int("n_spans", 5, 9)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 9, 15)
        n_spans = ctx.draw_int("n_spans", 3, 6)
    colors = ctx.draw_distinct_colors("colors", n=9, exclude={0})
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    all_rows = list(range(h)); rng.shuffle(all_rows)
    n_spans = min(n_spans, max(1, h - 1))     # keep >=1 row free for decoys
    fill_rows = all_rows[:n_spans]
    rest_rows = all_rows[n_spans:]

    # FILL rows: exactly two same-color endpoints (>=1 gap) -> the rule fills between.
    for i, r in enumerate(fill_rows):
        color = colors[i % len(colors)]
        c1 = rng.randint(0, w - 3)
        c2 = rng.randint(c1 + 2, w - 1)
        g[r][c1] = color
        g[r][c2] = color

    # DECOY rows: the rule fires ONLY on rows with EXACTLY two same-color cells,
    # so these three non-conforming shapes are left untouched and force that
    # precondition to be learned. Rule-safe distractors on distinct rows.
    n_decoy = rng.randint(0, min(3, len(rest_rows)))
    for r in rest_rows[:n_decoy]:
        kind = rng.choice(["single", "triple", "mismatch"])
        if kind == "single" or w < 3:
            g[r][rng.randint(0, w - 1)] = rng.choice(colors)
        elif kind == "triple":
            col = rng.choice(colors)
            for c in rng.sample(range(w), 3):
                g[r][c] = col          # 3 cells -> count != 2 -> rule ignores
        else:                          # two cells, different colors -> same-color test fails
            ca, cb = rng.sample(range(w), 2)
            g[r][ca] = colors[0]
            g[r][cb] = colors[1] if colors[1] != colors[0] else colors[2]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_endpoints":
        # blank → no spans to fill, rule has no effect
        return g
    if name == "mismatched_endpoints":
        # all rows have two endpoints but in different colors → rule's predicate fails everywhere
        g[1][1] = 4; g[1][w - 2] = 6
        g[3][2] = 3; g[3][w - 1] = 8
        g[5][0] = 7; g[5][5] = 4
        return g
    if name == "single_endpoint":
        # rows have only one endpoint each → no pair, rule has no effect
        g[1][3] = 4
        g[3][5] = 6
        g[5][7] = 3
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid is empty or ragged"]
    target_rows = 0
    for r, row in enumerate(grid):
        nz = [(c, v) for c, v in enumerate(row) if v != 0]
        if len(nz) == 2 and nz[0][1] == nz[1][1]:
            target_rows += 1
            if nz[1][0] - nz[0][0] < 2:
                errs.append(f"target row {r} endpoints have no gap")
    if target_rows < 1:
        errs.append("no row has two matching endpoints")
    return errs
