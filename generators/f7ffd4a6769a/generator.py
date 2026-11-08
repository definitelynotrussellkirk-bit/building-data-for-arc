"""Generator for arc_additional_puzzles_21_set16_bundle:E108.

Rule: rank rows by non-zero count (desc, ties by row index asc); output
the top-ranked row as a 1-row grid. Fully deterministic — ANY grid is a
valid input; the only concept-clean requirement is that one row holds a
STRICT maximum non-zero count (so the "winner" is unambiguous). Other
rows may tie with each other freely (the rule never depends on them).

Combinatorial axes: grid size (h up to 14, w up to 20 — output width
tracks w, so this is the main output-shape driver), per-row fill counts,
and full 1-9 palette with a varying per-grid color subset.
Degenerates: empty_grid, all_rows_equal, full_row_winner.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f7ffd4a6769a"
VERSION = "2.1.0"  # output-quality: use contiguous row blocks, not scattered singletons, so object-count matches canonical row-extraction demos
TASK_ID = "f7ffd4a6769a"
SUMMARY = (
    "0-bg grid (size varies, up to ~14x20). Each row holds one contiguous "
    "non-bg block in a varied color; exactly ONE row has the STRICT maximum "
    "non-bg count (other rows may tie among themselves). Rule: rank rows by "
    "non-zero count and output the top row. Net: the densest row is extracted "
    "without teaching a noisy singleton-scatter prior."
)

INVARIANTS = [
    "background is 0",
    "exactly one row has the strict-maximum non-zero count (unambiguous winner)",
    "the winner's count is >= 1 (it has at least one colored cell)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("empty_grid", "all_rows_equal", "full_row_winner")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "5-7 easy / 7-10 med / 10-14 hard", "valid": "4..16"},
    "grid_w":         {"type": "int", "default": "7-10 easy / 10-14 med / 14-20 hard", "valid": "5..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "rng 3..9", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "rows", "valid": "rows"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..9", "valid": "1..9"},
    "count_spread":   {"type": "str", "default": "strict_max_winner", "valid": "strict_max_winner"},
    "density":        {"type": "str", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|empty_grid|all_rows_equal|full_row_winner"},
}


def self_check(grid, *, difficulty=None, meta=None):
    """Verify default teaching instances: one visibly densest row, no singleton-scatter texture."""
    errors = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["empty or malformed grid"]
    w = len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["non-rectangular grid"]
    h = len(grid)
    vals = [v for row in grid for v in row]
    bad = sorted({v for v in vals if not isinstance(v, int) or v < 0 or v > 9})
    if bad:
        errors.append(f"grid has non-color values: {bad}")
    if 0 not in set(vals):
        errors.append("expected visible 0 background")
    counts = [sum(1 for v in row if v != 0) for row in grid]
    max_count = max(counts)
    if max_count <= 0:
        errors.append("winner row has no non-zero cells")
    winners = [i for i, cnt in enumerate(counts) if cnt == max_count]
    if len(winners) != 1:
        errors.append(f"expected exactly one strict maximum row, got {winners}")
    if max_count == w:
        errors.append("default winner row is fully filled; keep that only for degenerate override")
    for r, row in enumerate(grid):
        nz = [c for c, v in enumerate(row) if v != 0]
        if not nz:
            continue
        if max(nz) - min(nz) + 1 != len(nz):
            errors.append(f"row {r} has scattered non-zero cells instead of one contiguous block")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        hr, wr = (5, 7), (7, 10)
    elif difficulty == "hard":
        hr, wr = (10, 14), (14, 20)
    else:
        hr, wr = (7, 10), (10, 14)
    rng = ctx.draw_rng("layout")
    h = rng.randint(*hr); w = rng.randint(*wr)
    g = full_grid(h, w, 0)

    # per-grid color subset for palette diversity (full 1-9 available)
    all_colors = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(all_colors)
    palette = all_colors[: rng.randint(3, 9)]

    # non-winner rows: contiguous colored blocks, not random singleton scatter.
    # The canonical task teaches "pick the densest row" through compact row motifs
    # (e.g. 0033300 or 0222200).  Scattered per-cell fills explode component count
    # and train the grid model on a different visual prior while still passing the
    # mathematical Racket rule.  Keep the strict-max count axis, but draw one block
    # per non-empty row.
    counts = [rng.randint(0, w - 2) for _ in range(h)]
    winner = rng.randrange(h)
    others_max = max(c for i, c in enumerate(counts) if i != winner) if h > 1 else 0
    # Avoid the default-path full-row shortcut; it is available as full_row_winner.
    counts[winner] = rng.randint(others_max + 1, max(others_max + 1, w - 1))
    for r, count in enumerate(counts):
        if count <= 0:
            continue
        color = rng.choice(palette)
        start = rng.randint(0, w - count)
        for c in range(start, start + count):
            g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 8
    g = full_grid(h, w, 0)
    if name == "empty_grid":
        # all rows have count 0 → "max" row is ambiguous (every row ties at zero)
        return g
    if name == "all_rows_equal":
        # every row has the same count → tie-break by row index, no strict winner
        for r in range(h):
            for c in range(3):
                g[r][c] = 4
        return g
    if name == "full_row_winner":
        # winner row is fully filled; other rows empty → trivial recovery, no spread
        for c in range(w):
            g[2][c] = 5
        return g
    return g
