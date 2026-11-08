"""Generator for arc_puzzle_bank_21_set19_bundle:hard_p05 — pack transformed base.

Rule: row 0 holds 1-4 transform codes; rows 2..h-1 hold a base motif.
For each code, transform a crop of the base; pack the transformed pieces
left-to-right with one blank column between them.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_codes,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_codes, no_motif, motif_in_codes_row.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a4dabc2e7822"
VERSION = "2.0.1"
TASK_ID = "a4dabc2e7822"

SUMMARY = (
    "0-bg grid (h~8-10, w~11-14) "
    "with: (a) ROW 0 containing "
    "1-4 TRANSFORM CODES (values "
    "1-4) at random distinct "
    "columns; (b) ROW 1 entirely "
    "0 (separator); (c) ROWS 2.."
    "h-1 contain a SMALL BASE "
    "MOTIF (3-5 cells, 4-conn) "
    "in a DISTINCT color (8 or 9). "
    "Rule (PACK TRANSFORMED CROPS "
    "BY ROW-0 CODES): identify "
    "the BASE MOTIF in rows 2+. "
    "CROP its bbox. For EACH "
    "TRANSFORM CODE in row 0 "
    "(left to right): APPLY the "
    "transform (1=identity, "
    "2=rot CW 90°, 3=rot 180°, "
    "4=rot CCW 90°) to the "
    "cropped base. PACK the "
    "transformed pieces LEFT-TO-"
    "RIGHT with ONE BLANK COLUMN "
    "between them. Net: motif "
    "appears multiple times, "
    "transformed per row-0 codes."
)

INVARIANTS = [
    "background is 0",
    "row 0 has 1-4 non-zero transform codes (1..7) at distinct columns",
    "row 1 is all 0 (separator)",
    "rows 2..h-1 hold a connected base motif (3-5 cells)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_codes", "no_motif", "motif_in_codes_row")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 11..14", "valid": "10..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_codes":        {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..5"},
    "position_bias":  {"type": "str", "default": "row0_codes_motif_below",
                       "valid": "row0_codes_motif_below"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: row 0 has at least one non-zero transform code (1..7);
    row 1 is all 0 (separator); rows 2+ have at least one non-bg base motif cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if h < 3:
        return []
    errs = []
    codes = [grid[0][c] for c in range(w) if grid[0][c] != 0]
    if not codes:
        errs.append("row 0 has no non-zero transform codes")
    if any(grid[1][c] != 0 for c in range(w)):
        errs.append("row 1 is not all-zero (expected separator row)")
    motif_cells = sum(1 for r in range(2, h) for c in range(w) if grid[r][c] != 0)
    if motif_cells == 0:
        errs.append("no base motif cells in rows 2+")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 11, 12)
        n_codes = ctx.draw_int("n_codes", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 13, 16)
        n_codes = ctx.draw_int("n_codes", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 11, 14)
        n_codes = ctx.draw_int("n_codes", 2, 4)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    cols = rng.sample(range(w), n_codes)
    cols.sort()
    for c in cols:
        g[0][c] = rng.randint(1, 4)

    motif_color = rng.choice([8, 9])
    cells = [(0, 0)]
    seen = {(0, 0)}
    target = rng.randint(3, 5)
    while len(cells) < target:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    sh = max(rs) - min(rs) + 1
    sw = max(cs) - min(cs) + 1
    sr0, sc0 = -min(rs), -min(cs)
    r0 = rng.randint(2, h - sh)
    c0 = rng.randint(0, w - sw)
    for r, c in cells:
        g[r0 + sr0 + r][c0 + sc0 + c] = motif_color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 12
    g = full_grid(h, w, 0)
    if name == "no_codes":
        # Row 0 empty — rule has no transforms to apply.
        g[3][3] = 8; g[3][4] = 8; g[4][3] = 8
        return g
    if name == "no_motif":
        # Codes present but no motif below — rule has nothing to transform.
        g[0][2] = 1; g[0][6] = 2
        return g
    if name == "motif_in_codes_row":
        # Motif cell in row 0 — code/motif boundaries collide.
        g[0][2] = 1; g[0][3] = 8
        g[2][3] = 8; g[3][3] = 8
        return g
    return g
