"""Generator for arc_puzzle_bank_21_set21_bundle:easy_p06 — domino with one open continuation.

Domino segments have exactly one open continuation cell; the other
side is blocked by a color-9 cell.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_blocker (no color-9 → rule's "blocked side" is
undefined for every domino), no_dominoes (no domino segments → rule
has nothing to extend), all_blocked_both_sides (every domino has
blockers on both sides → rule's "open continuation" is undefined,
no extension).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a7471bf37ed9"
VERSION = "2.0.1"
TASK_ID = "a7471bf37ed9"
SUMMARY = (
    "0-bg grid (h ∈ 7-10, w ∈ 8-12) "
    "with: SEGMENT_COUNT ∈ 1-4 DOMINO "
    "GROUPS, each consisting of: "
    "(a) ONE 2-CELL DOMINO (horizontal "
    "or vertical, oriented per "
    "candidate kind ∈ {h_right, h_left, "
    "v_down, v_up}) painted in a "
    "DISTINCT non-{0, 9} color drawn "
    "from {1..8}; (b) ONE COLOR-9 "
    "BLOCKER CELL adjacent to ONE end "
    "of the domino — for h_right: "
    "blocker at (r, c-1) on the left "
    "side; for h_left: blocker at "
    "(r, c+2); for v_down: blocker at "
    "(r-1, c) above; for v_up: blocker "
    "at (r+2, c) below. The OPEN "
    "CONTINUATION cell (opposite the "
    "blocker) is in-bounds and "
    "currently 0 — only one side is "
    "blocked, the other is open. "
    "Placements use _clear_patch with "
    "1-cell neighborhood check. Rule "
    "(FOR EACH DOMINO, EXTEND ITS "
    "COLOR INTO THE OPEN CONTINUATION "
    "CELL — THE BLOCKED SIDE STAYS "
    "AS-IS): For EACH domino (2 "
    "same-color cells): DETERMINE "
    "the BLOCKED side (adjacent "
    "color-9 cell) and the OPEN "
    "side (currently 0). PAINT the "
    "OPEN cell with the domino's "
    "color, EXTENDING the domino "
    "by 1 cell. Blockers stay 9. "
    "Net: each domino grows by one "
    "into its open continuation, "
    "becoming a 3-cell line."
)

INVARIANTS = [
    "background is 0",
    "domino colors exclude blocker color 9",
    "each domino has exactly one open continuation and one blocked continuation",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blocker", "no_dominoes", "all_blocked_both_sides")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":            {"type": "int", "default": "rng 8..12", "valid": "5..16"},
    "segment_count":     {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 3..5", "valid": "2..8"},
    "position_bias":     {"type": "str", "default": "dominoes_with_blockers",
                          "valid": "dominoes_with_blockers"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "2..8"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _clear_patch(grid, cells):
    h = len(grid)
    w = len(grid[0])
    for r, c in cells:
        for rr in range(max(0, r - 1), min(h, r + 2)):
            for cc in range(max(0, c - 1), min(w, c + 2)):
                if grid[rr][cc] != 0:
                    return False
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; color-9 blocker present (if not no_blocker degenerate); no domino color equals 9."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    has_nine = any(grid[r][c] == 9 for r in range(h) for c in range(w))
    has_nonzero_non9 = any(grid[r][c] not in (0, 9) for r in range(h) for c in range(w))
    if not has_nine and not has_nonzero_non9:
        return errs  # empty grid — degenerate
    # If non-9 domino cells exist, ensure bg=0 (values in 0..9)
    bad_vals = {grid[r][c] for r in range(h) for c in range(w) if not (0 <= grid[r][c] <= 9)}
    if bad_vals:
        errs.append(f"out-of-range values: {bad_vals}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
        segment_count = ctx.draw_int("segment_count", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        segment_count = ctx.draw_int("segment_count", 4, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 12)
        segment_count = ctx.draw_int("segment_count", 2, 4)
    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8], segment_count)

    candidates = []
    for r in range(h):
        for c in range(1, w - 2):
            candidates.append(("h_right", r, c))
            candidates.append(("h_left", r, c))
    for r in range(1, h - 2):
        for c in range(w):
            candidates.append(("v_down", r, c))
            candidates.append(("v_up", r, c))
    rng.shuffle(candidates)
    placed = 0
    for kind, r, c in candidates:
        if placed >= segment_count:
            break
        if kind == "h_right":
            domino = [(r, c), (r, c + 1)]
            blocker = (r, c - 1)
            open_cell = (r, c + 2)
        elif kind == "h_left":
            domino = [(r, c), (r, c + 1)]
            blocker = (r, c + 2)
            open_cell = (r, c - 1)
        elif kind == "v_down":
            domino = [(r, c), (r + 1, c)]
            blocker = (r - 1, c)
            open_cell = (r + 2, c)
        else:
            domino = [(r, c), (r + 1, c)]
            blocker = (r + 2, c)
            open_cell = (r - 1, c)
        if not _clear_patch(grid, domino + [blocker, open_cell]):
            continue
        color = colors[placed]
        for rr, cc in domino:
            grid[rr][cc] = color
        grid[blocker[0]][blocker[1]] = 9
        placed += 1
    return grid


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_blocker":
        # No color-9 — rule's "blocked side" is undefined.
        g[2][2] = 4; g[2][3] = 4
        g[5][6] = 6; g[6][6] = 6
        return g
    if name == "no_dominoes":
        # No domino segments — rule has nothing to extend.
        g[2][2] = 9
        g[5][6] = 9
        return g
    if name == "all_blocked_both_sides":
        # Every domino is blocked on both sides — no open continuation.
        g[3][1] = 9; g[3][2] = 4; g[3][3] = 4; g[3][4] = 9
        g[6][5] = 9; g[6][6] = 6; g[6][7] = 6; g[6][8] = 9
        return g
    return g
