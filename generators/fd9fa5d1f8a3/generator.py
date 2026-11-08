"""Generator for arc_puzzle_bank_nineteenth_21_bundle:easy_129_expand_singletons_to_radius1_pluses.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_singletons,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_singletons, multi_cell_blob, on_edge.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fd9fa5d1f8a3"
VERSION = "2.2.0"  # retry placement until default samples realize the requested singleton count
TASK_ID = "fd9fa5d1f8a3"

SUMMARY = (
    "0-bg grid with 2-12 ISOLATED SINGLETON cells in varied "
    "non-zero colors, placed ANYWHERE (interior OR on the "
    "edges/corners) with a 2-cell buffer between any pair so "
    "radius-1 plus expansions never overlap. Rule: produce a "
    "FRESH same-size empty grid; for each non-zero source "
    "cell at (r, c), paint a plus — the cell itself + its 4 "
    "cardinal neighbors — in the same color, keeping only "
    "in-bounds cells (edge/corner pluses are clipped). Net: "
    "each singleton expands into a radius-1 plus of its color."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "each source cell is a singleton",
    "source cells may sit anywhere incl. edges/corners (the rule clips out-of-bounds arms)",
    "source cells are separated (2-cell buffer) so plus expansions do not overlap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_singletons", "multi_cell_blob", "on_edge")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "6-9 easy / 9-13 med / 12-18 hard", "valid": "5..22"},
    "grid_w":         {"type": "int", "default": "6-9 easy / 9-13 med / 12-18 hard", "valid": "5..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_singletons":   {"type": "int", "default": "2-3 easy / 3-6 med / 5-12 hard", "valid": "1..12"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "isolated_interior_singletons",
                       "valid": "isolated_interior_singletons"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _guard(r: int, c: int, h: int, w: int) -> set[tuple[int, int]]:
    return {
        (rr, cc)
        for rr in range(max(0, r - 2), min(h, r + 3))
        for cc in range(max(0, c - 2), min(w, c + 3))
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 6, 9)
        target = ctx.draw_int("singletons", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 18)
        w = ctx.draw_int("grid_w", 12, 18)
        target = ctx.draw_int("singletons", 5, 12)
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 9, 13)
        target = ctx.draw_int("singletons", 3, 6)
    rng = ctx.draw_rng("layout")

    # Earlier versions accepted under-filled random placements (occasionally one
    # singleton in easy/default samples), hiding the multi-plus rule. Retry the
    # whole layout and fail closed only if the requested separated packing is
    # genuinely not achieved.
    best = None
    best_count = -1
    for _attempt in range(30):
        g = full_grid(h, w, 0)
        reserved: set[tuple[int, int]] = set()
        placed = 0
        for _ in range(400):
            if placed >= target:
                break
            r = rng.randint(0, h - 1)
            c = rng.randint(0, w - 1)
            guard = _guard(r, c, h, w)
            if guard & reserved:
                continue
            g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
            reserved.update(guard)
            placed += 1
        if placed > best_count:
            best, best_count = g, placed
        if placed >= target:
            return g

    # Deterministic greedy completion for high target/dense hard cases.  It still
    # uses the keyed RNG to shuffle candidate order, but does not fail-open to a
    # one-cell sample.
    g = full_grid(h, w, 0)
    reserved: set[tuple[int, int]] = set()
    cells = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(cells)
    placed = 0
    for r, c in cells:
        if placed >= target:
            break
        guard = _guard(r, c, h, w)
        if guard & reserved:
            continue
        g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        reserved.update(guard)
        placed += 1
    if placed >= 2:
        return g
    if best is not None and best_count >= 2:
        return best
    raise ValueError(f"could not place at least two separated singletons on {h}x{w}; best={best_count}")


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_singletons":
        # blank → no singletons to expand
        return g
    if name == "multi_cell_blob":
        # multi-cell blob → not singleton, "singleton" precondition fails
        for r, c in [(2, 2), (2, 3), (3, 2)]: g[r][c] = 4
        return g
    if name == "on_edge":
        # singleton at corner → plus expansion goes out of bounds
        g[0][0] = 4
        g[7][7] = 6
        return g
    return g



def self_check(grid, *, difficulty=None, meta=None):
    """Default samples contain separated nonzero singleton source cells."""
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if len(cells) < 2:
        errs.append(f"expected at least two singleton sources, got {len(cells)}")
    if len(cells) > 12:
        errs.append(f"too many singleton sources: {len(cells)}")
    for r, c in cells:
        if not (1 <= grid[r][c] <= 9):
            errs.append(f"bad nonzero color {grid[r][c]} at {(r, c)}")
    for i, (r1, c1) in enumerate(cells):
        for r2, c2 in cells[i + 1:]:
            if max(abs(r1 - r2), abs(c1 - c2)) < 3:
                errs.append(f"source cells too close: {(r1, c1)} and {(r2, c2)}")
                return errs
    return errs
