"""Generator for arc_additional_puzzles_21_set19_bundle:E127 — Slide non-9 blob east to 9-dock.

Rule: dock = right column of 9s. Slide the non-{0,9} blob east until
it abuts the dock; output keeps 9s + slid blob.

Combinatorial axes (8): grid_h, grid_w, palette_kind, blob_choice,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_dock, no_blob, blob_already_at_dock.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bcb40bed1599"
# 2.1.0: blob was a 3-shape bank with cell-clipping that could disconnect it.
# Now a random connected polyomino (no clipping), placed at a varied row with
# guaranteed >=1 east move. Output is driven by blob shape + row, so maximise
# both (plus grid height).
VERSION = "2.1.1"  # add self_check
TASK_ID = "bcb40bed1599"
SUMMARY = (
    "0-bg grid (h~4-6, w~8-10) with: (a) the RIGHTMOST column "
    "filled entirely with color-9 (maroon) cells — the DOCK; "
    "(b) one connected BLOB of 3-4 cells in some non-{0,9} "
    "color, placed on the LEFT side with empty space to its "
    "right. Rule: extract dock cells and blob cells. While "
    "the blob can be shifted east by 1 (all next-column cells "
    "in bounds AND either 0 or in the blob itself), shift it "
    "east. Stop when shifting would hit the dock or wall. "
    "Output: empty grid + dock(9) + blob in original color at "
    "final position (abutting the dock)."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "right column is fully 9 (dock)",
    "exactly 1 non-{0,9} blob with empty space to its right",
    "blob has room to slide ≥1 cell east (so motion is observable)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dock", "no_blob", "blob_already_at_dock")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..6", "valid": "3..10"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "blob_choice":    {"type": "int", "default": "rng 0..2", "valid": "0..2"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "left_blob_with_9_dock",
                       "valid": "left_blob_with_9_dock"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: right column is fully color-9 (dock); has non-{0,9} blob."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    right_col = [grid[r][w - 1] for r in range(h)]
    has_nine = any(v == 9 for v in right_col)
    if not has_nine:
        return errs  # degenerate no_dock
    if not all(v == 9 for v in right_col):
        errs.append("right column is not fully color-9")
    blob = any(grid[r][c] not in (0, 9) for r in range(h) for c in range(w))
    if not blob:
        errs.append("no non-{0,9} blob cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 5)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 10, 13)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 8, 11)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    for r in range(h):
        g[r][w - 1] = 9
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
    # Random connected polyomino blob whose bbox fits left of the dock with
    # >=1 cell of clearance to the right (so it can slide east).
    shape = _poly(rng, rng.randint(3, min(6, h)), max_dim=min(4, h))
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    if sh > h:
        shape = [(0, 0), (1, 0), (2, 0)]; sh, sw = 3, 1
    top = rng.randint(0, h - sh)
    # leave at least 1 empty column between the blob's right edge and the dock
    max_left = (w - 1) - sw - 1
    left = rng.randint(0, max(0, max_left))
    for dr, dc in shape:
        g[top + dr][left + dc] = color
    return g


def _poly(rng, size, max_dim=4):
    cells = {(0, 0)}; frontier = [(0, 0)]
    while len(cells) < size and frontier:
        r, c = rng.choice(frontier)
        opts = [(r + dr, c + dc) for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))]
        rng.shuffle(opts)
        grown = False
        for nr, nc in opts:
            if (nr, nc) in cells:
                continue
            rs = [x for x, _ in cells] + [nr]; cs = [y for _, y in cells] + [nc]
            if max(rs) - min(rs) + 1 > max_dim or max(cs) - min(cs) + 1 > max_dim:
                continue
            cells.add((nr, nc)); frontier.append((nr, nc)); grown = True
            break
        if not grown:
            frontier.remove((r, c))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _draw_from_degenerate(name, rng):
    h, w = 5, 9
    g = full_grid(h, w, 0)
    if name == "no_dock":
        # blob but no right-9 dock → slide target undefined
        for (dr, dc) in [(0, 0), (1, 0), (2, 0)]: g[1 + dr][1 + dc] = 4
        return g
    if name == "no_blob":
        # dock but no blob → nothing to slide
        for r in range(h): g[r][w - 1] = 9
        return g
    if name == "blob_already_at_dock":
        # blob already abuts the dock → no slide motion (input == output)
        for r in range(h): g[r][w - 1] = 9
        for (dr, dc) in [(0, 0), (1, 0), (2, 0)]: g[1 + dr][w - 2 + dc] = 4
        return g
    return g
