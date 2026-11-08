"""Generator for dc9884cdb6ae.

Rule: count 0-cells per row and per col. For cells in max-zero-row or
max-zero-col, replace 0 with 3.

Combinatorial axes (8): grid_h/w, target_row_zeros, target_col_zeros,
n_extra_zeros, n_twos, position_bias, anchor_corner, asymmetry_force.
Degenerates: no_zeros, all_zeros, tied_max.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.place import random_free_cell

GENERATOR_ID = "dc9884cdb6ae"
VERSION = "2.4.0"
TASK_ID = "dc9884cdb6ae"
SUMMARY = (
    "8-bg grid with a connected zero field and one connected 2-region. The "
    "0s are distributed unevenly: at least one ROW has the maximum "
    "0-count (≥ all other rows), and at least one COL also has the "
    "maximum 0-count. Rule: count 0s per row → max-rz. Count 0s per "
    "col → max-cz. For each 0-cell at (r, c), if row r has count "
    "max-rz OR col c has count max-cz, replace it with color 3. "
    "Otherwise leave it as 0. Other cells (8, 2) are preserved. The generator "
    "keeps 8/2 as low-component regions like the canonical examples instead "
    "of scattering 2s as independent speckles."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 8",
    "≥1 row has the global max 0-count (its 0-cells will become 3)",
    "≥1 col has the global max 0-count (its 0-cells will become 3)",
    "≥1 other row/col has a smaller 0-count (so they're preserved — selectivity)",
    "one connected 2-region distractor/border component",
]

POSITION_BIASES = ("scattered", "row_focus", "col_focus", "corner",
                   "centered")
DEGENERATE_TEXTURES = ("no_zeros", "all_zeros", "tied_max")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":           {"type": "int", "default": "rng 5..9", "valid": "4..12"},
    "grid_w":           {"type": "int", "default": "rng 9..13", "valid": "7..16"},
    "target_row_zeros": {"type": "int", "default": "rng w-4..w-2",
                         "valid": "3..w-1"},
    "n_extra_zeros":    {"type": "int", "default": "rng 2..5",
                         "valid": "0..10"},
    "n_twos":           {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "position_bias":    {"type": "str", "default": "rng helpful",
                         "valid": "|".join(POSITION_BIASES)},
    "anchor_corner":    {"type": "bool", "default": "false",
                         "valid": "true|false"},
    "texture":          {"type": "str", "default": "alias for position_bias",
                         "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 8, 10
    elif difficulty == "hard":
        h_lo, h_hi = 11, 14
    else:
        h_lo, h_hi = 10, 12
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi + 2)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)

    # Canonical instances are not a salt-and-pepper cloud: 8 and 2 are each
    # usually one component, while the 0-field carries the row/column count
    # signal. Build that structure directly.
    g = full_grid(h, w, 8)
    r1 = rng.randint(1, max(1, h // 4))
    r2 = rng.randint(max(r1 + 3, h - 3), h - 2)
    c1 = rng.randint(1, max(1, w // 4))
    c2 = rng.randint(max(c1 + 4, w - 4), w - 2)
    target_row = _pick_target_row(overrides.get("position_bias", "scattered"), r2 - r1 + 1, rng) + r1
    target_col = _pick_target_col(overrides.get("position_bias", "scattered"), c2 - c1 + 1, rng) + c1

    width = c2 - c1 + 1
    for r in range(r1, r2 + 1):
        cols = list(range(c1, c2 + 1))
        if r != target_row:
            # Remove a few non-target columns so only target_row has the row max.
            removable = [c for c in cols if c != target_col]
            rng.shuffle(removable)
            for c in removable[:rng.randint(1, max(1, width // 3))]:
                cols.remove(c)
        for c in cols:
            g[r][c] = 0

    # Thin every non-target column in at least one row so target_col has the
    # column max. Keep enough zeros away from the target row/col to demonstrate
    # preservation.
    for c in range(c1, c2 + 1):
        if c == target_col:
            continue
        candidates = [r for r in range(r1, r2 + 1) if r != target_row and g[r][c] == 0]
        if candidates:
            g[rng.choice(candidates)][c] = 8
    if _changed_and_preserved_zero_counts(g)[1] == 0:
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if r != target_row and c != target_col and g[r][c] == 8:
                    g[r][c] = 0
                    break
            if _changed_and_preserved_zero_counts(g)[1] > 0:
                break

    _paint_connected_two_region(g, rng)
    return g


def _paint_connected_two_region(g, rng):
    h, w = len(g), len(g[0])
    side = rng.choice(["top", "bottom", "left", "right"])
    if side in ("top", "bottom"):
        r = 0 if side == "top" else h - 1
        length = rng.randint(max(2, w // 4), max(2, w // 2))
        c0 = rng.randint(0, w - length)
        for c in range(c0, c0 + length):
            g[r][c] = 2
        if (0 < r < h - 1) and rng.random() < 0.5:
            g[r - 1 if r == h - 1 else r + 1][c0] = 2
    else:
        c = 0 if side == "left" else w - 1
        length = rng.randint(max(2, h // 4), max(2, h // 2))
        r0 = rng.randint(0, h - length)
        for r in range(r0, r0 + length):
            g[r][c] = 2
        if (0 < c < w - 1) and rng.random() < 0.5:
            g[r0][c - 1 if c == w - 1 else c + 1] = 2


def _zero_counts(grid):
    h, w = len(grid), len(grid[0])
    row_counts = [row.count(0) for row in grid]
    col_counts = [sum(grid[r][c] == 0 for r in range(h)) for c in range(w)]
    return row_counts, col_counts


def _changed_and_preserved_zero_counts(grid):
    h, w = len(grid), len(grid[0])
    row_counts, col_counts = _zero_counts(grid)
    max_row = max(row_counts) if row_counts else 0
    max_col = max(col_counts) if col_counts else 0
    changed = preserved = 0
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                continue
            if row_counts[r] == max_row or col_counts[c] == max_col:
                changed += 1
            else:
                preserved += 1
    return changed, preserved


def _ensure_preserved_zero(grid, rng):
    if _changed_and_preserved_zero_counts(grid)[1] > 0:
        return
    h, w = len(grid), len(grid[0])
    row_counts, col_counts = _zero_counts(grid)
    max_row = max(row_counts); max_col = max(col_counts)
    candidates = [(r, c) for r in range(h) for c in range(w)
                  if grid[r][c] == 8 and row_counts[r] + 1 < max_row
                  and col_counts[c] + 1 < max_col]
    rng.shuffle(candidates)
    if candidates:
        r, c = candidates[0]
        grid[r][c] = 0


def _pick_target_row(bias, h, rng):
    if bias == "row_focus":
        return rng.randint(1, h - 2)
    if bias == "centered":
        return h // 2
    if bias == "corner":
        return 1
    return rng.randint(1, h - 2)


def _pick_target_col(bias, w, rng):
    if bias == "col_focus":
        return rng.randint(1, w - 2)
    if bias == "centered":
        return w // 2
    if bias == "corner":
        return 1
    return rng.randint(1, w - 2)


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 8)
    if name == "no_zeros":
        # Sprinkled 2s, no 0s — rule has no work
        for _ in range(3):
            cell = random_free_cell(g, rng, bg=8, max_tries=20)
            if cell:
                g[cell[0]][cell[1]] = 2
        return g
    if name == "all_zeros":
        for r in range(h):
            for c in range(w):
                g[r][c] = 0
        return g
    if name == "tied_max":
        # Two rows with same 0-count
        for r in [1, 3]:
            if r < h:
                for c in range(w - 2):
                    g[r][c] = 0
        return g
    return g



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    errors = []
    allowed = {0, 2, 3, 8}
    bad = sorted({v for row in grid for v in row if v not in allowed})
    if bad:
        errors.append(f"unexpected colors: {bad}")
    changed, preserved = _changed_and_preserved_zero_counts(grid)
    if changed < 1:
        errors.append("need at least one 0 that lies on a max-zero row/column")
    if preserved < 1:
        errors.append("need at least one preserved 0 away from max-zero rows/columns")
    twos = sum(v == 2 for row in grid for v in row)
    if twos < 2:
        errors.append("need a connected distractor color-2 region of size at least 2")
    return sorted(set(errors))
