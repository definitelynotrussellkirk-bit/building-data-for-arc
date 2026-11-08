"""Generator for arc_puzzle_bank_third_21_bundle:easy_17_extend_exact_horizontal_triples.

Combinatorial axes (8): grid_h, grid_w, palette_kind, triples,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_triples, all_too_long, no_room_to_extend.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7ad144546d43"
VERSION = "1.1.1"
TASK_ID = "7ad144546d43"

SUMMARY = "Isolated orange triples are extended one cell to the left and right."

INVARIANTS = [
    "background is 0",
    "target runs are horizontal orange bars of exact length 3",
    "target runs have one blank cell on both sides",
    "longer orange runs are optional distractors and should not extend",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_triples", "all_too_long", "no_room_to_extend")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "4..16"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "6..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "triples":        {"type": "int", "default": "rng 2..4", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "isolated_horizontal_triples",
                       "valid": "isolated_horizontal_triples"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _row_free(g, r, c0, c1):
    w = len(g[0])
    lo = max(0, c0 - 1)
    hi = min(w - 1, c1 + 1)
    return all(g[r][c] == 0 for c in range(lo, hi + 1))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg 0, ≥1 exact run of exactly 3 color-7 cells in a row with bg on both sides."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    found_triple = False
    for r in range(h):
        row = grid[r]
        c = 0
        while c < w:
            if row[c] == 7:
                start = c
                while c < w and row[c] == 7:
                    c += 1
                run_len = c - start
                if run_len == 3:
                    # Check bg on both sides
                    left_ok = start == 0 or row[start - 1] == 0
                    right_ok = c == w or row[c] == 0
                    if left_ok and right_ok:
                        found_triple = True
                        break
            else:
                c += 1
        if found_triple:
            break
    if not found_triple:
        errs.append("no exact-3 color-7 run with bg on both sides found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 7)
        w = ctx.draw_int("grid_w", 10, 11)
        target = min(ctx.draw_int("triples", 2, 2), h)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 12, 13)
        target = min(ctx.draw_int("triples", 3, 4), h)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 10, 13)
        target = min(ctx.draw_int("triples", 2, 4), h)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)

    for r in rng.sample(range(h), target):
        for _ in range(40):
            c0 = rng.randint(1, w - 5)
            if _row_free(g, r, c0, c0 + 2):
                for c in range(c0, c0 + 3):
                    g[r][c] = 7
                break

    for r in rng.sample(range(h), min(2, h)):
        for _ in range(20):
            c0 = rng.randint(0, w - 4)
            if _row_free(g, r, c0, c0 + 3):
                for c in range(c0, c0 + 4):
                    g[r][c] = 7
                break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 12
    g = full_grid(h, w, 0)
    if name == "no_triples":
        # blank → no targets to extend
        return g
    if name == "all_too_long":
        # only 4-runs (distractors), no 3-runs → rule has no targets
        for c in range(2, 6): g[2][c] = 7
        for c in range(5, 9): g[5][c] = 7
        return g
    if name == "no_room_to_extend":
        # 3-run touches grid edge → can't extend without OOB
        for c in range(0, 3): g[2][c] = 7
        for c in range(w - 3, w): g[5][c] = 7
        return g
    return g
