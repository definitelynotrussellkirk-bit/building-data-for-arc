"""Generator for 1b60fb0c.

Rule: blue cells are completed by 180-degree symmetry with missing
partners marked red.

Combinatorial axes (8): grid_h/w, missing_pair, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_pairs.
Degenerates: no_blue, all_paired, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b82be04c88b1"
# 2.1.0: replace fixed 5-pair cross with a RANDOM connected blue blob made
# (mostly) 180-symmetric about a random center, then a few cells deleted so
# the rule recovers the center and paints the missing partners red.
VERSION = "2.1.1"
TASK_ID = "b82be04c88b1"
SUMMARY = (
    "0-bg grid (h, w~9-16) holding a RANDOM CONNECTED BLUE(1) BLOB that is "
    "(nearly) 180-degree symmetric about an interior cell center (cr, cc): "
    "the blob is grown on one side then mirrored through the center, and a "
    "FEW cells are then DELETED so their symmetric partners are unmatched. "
    "Rule (COMPLETE 180-deg SYMMETRY, MARK NEW CELLS RED): SEARCH all "
    "candidate centers for the one that best maps the blue set onto itself "
    "while sending at least one blue cell onto a BG-0 cell; for each blue "
    "cell whose partner about that center is BG-0, PAINT the partner RED(2). "
    "Existing blue cells stay. Net: the missing symmetric partners fill in "
    "red. Blob shape, size, center and number of deletions all vary."
)

INVARIANTS = [
    "all source cells are blue",
    "most blue cells already have 180-degree partners around one center",
    "at least one blue cell has an empty symmetric partner",
    "the symmetry center sits clear of grid borders",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_blue", "all_paired", "full_grid")

# (legacy fixed offset pairs, used only by the all_paired degenerate sample)
PAIRS = [
    ((-1, -1), (1, 1)),
    ((-1, 1), (1, -1)),
    ((0, -2), (0, 2)),
    ((-2, 0), (2, 0)),
    ((-2, -1), (2, 1)),
]

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..13", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "8..16"},
    "blob_n":         {"type": "int", "default": "rng 5..10", "valid": "4..14"},
    "n_missing":      {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "rng", "valid": "rng"},
    "texture":        {"type": "str", "default": "degenerate selector",
                       "valid": "|".join(DEGENERATE_TEXTURES)},
}


def _grow_blob(rng, cr, cc, n, rmin, rmax, cmin, cmax):
    """Random connected blob seeded at (cr,cc) kept inside the box."""
    cells = {(cr, cc)}
    frontier = [(cr, cc)]
    tries = 0
    while len(cells) < n and frontier and tries < 400:
        tries += 1
        r, c = rng.choice(frontier)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if rmin <= nr <= rmax and cmin <= nc <= cmax and (nr, nc) not in cells:
            cells.add((nr, nc))
            frontier.append((nr, nc))
    return cells


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: all nonzero values are 1 (only blue cells allowed in input)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    bad = [(r, c, grid[r][c]) for r in range(h) for c in range(w)
           if grid[r][c] not in (0, 1)]
    if bad:
        return [f"non-blue nonzero cells found: {bad[:3]} (all input cells must be 0 or 1)"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        h = rng.randint(9, 11); w = rng.randint(9, 11)
        blob_n = rng.randint(4, 7); n_missing = rng.randint(1, 2)
    elif difficulty == "hard":
        h = rng.randint(12, 16); w = rng.randint(12, 16)
        blob_n = rng.randint(8, 14); n_missing = rng.randint(1, 4)
    else:
        h = rng.randint(9, 13); w = rng.randint(9, 13)
        blob_n = rng.randint(5, 10); n_missing = rng.randint(1, 3)

    # Build a random blob on ONE side of a chosen center, then mirror every
    # cell through the center -> a 180-symmetric blue shape. The center has
    # half-integer support, so use a cell-anchored center (cr,cc) and partner
    # = (2*cr - r, 2*cc - c). Keep everything well inside the grid.
    cr = rng.randint(3, h - 4)
    cc = rng.randint(3, w - 4)
    # box must keep both a cell and its partner in-bounds:
    rmin = max(1, 2 * cr - (h - 2)); rmax = min(h - 2, 2 * cr - 1)
    cmin = max(1, 2 * cc - (w - 2)); cmax = min(w - 2, 2 * cc - 1)
    if rmin > cr: rmin = cr
    if rmax < cr: rmax = cr
    if cmin > cc: cmin = cc
    if cmax < cc: cmax = cc

    blob = _grow_blob(rng, cr, cc, blob_n, rmin, rmax, cmin, cmax)
    # symmetrize: add every partner so the full shape is 180-symmetric
    full = set(blob)
    for (r, c) in blob:
        pr, pc = 2 * cr - r, 2 * cc - c
        if 0 <= pr < h and 0 <= pc < w:
            full.add((pr, pc))

    # delete a few cells (not the center) so their partners become "missing"
    # -> the rule recovers the center and paints those partners red.
    deletable = [p for p in full if p != (cr, cc)]
    rng.shuffle(deletable)
    removed = set(deletable[:max(1, min(n_missing, len(deletable) - 2))])
    blue = full - removed
    # ensure at least one removed cell's partner is still blue (so red appears)
    if not any((2 * cr - r, 2 * cc - c) in blue for (r, c) in removed):
        # keep one partner present
        if removed:
            r, c = next(iter(removed))
            blue.add((2 * cr - r, 2 * cc - c))

    g = full_grid(h, w, 0)
    for (r, c) in blue:
        g[r][c] = 1
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 10, 0)
    if name == "no_blue":
        return g
    if name == "all_paired":
        for i, pair in enumerate(PAIRS):
            for dr, dc in pair:
                g[5 + dr][5 + dc] = 1
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(10):
                g[r][c] = 1
        return g
    return g
