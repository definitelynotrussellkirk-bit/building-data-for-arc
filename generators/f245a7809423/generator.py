"""Generator for arc_puzzle_bank_21_set6_s:S6_M4 — seeded checker fill.

Rule: a single rect-frame contains one seed cell of a different color.
Fill the frame interior with a checker pattern matching the seed's
parity (cells with (r+c) parity == seed parity become seed-color).

Combinatorial axes (8): grid_h, grid_w, palette_kind, frame_h,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_frame, no_seed, multiple_seeds.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f245a7809423"
VERSION = "1.2.0"  # bigger frames + grids for larger checker interiors (canonical frames are near-full-grid)
TASK_ID = "f245a7809423"
SUMMARY = ("One rect-frame (4x5 up to ~9x13) with a single seed inside (a different "
           "color). Rule checker-fills the interior 0-cells at the seed's (r+c) "
           "parity in the seed color. Frame/grid size and seed position vary.")

INVARIANTS = [
    "background is 0",
    "exactly one rect-frame, color != seed color",
    "frame interior has exactly one seed cell",
    "frame interior has ≥3 cells of opposite parity (so checker fill is non-trivial)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frame", "no_seed", "multiple_seeds")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..15"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "frame_h":        {"type": "int", "default": "rng 4..5", "valid": "4..5"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "frame_with_seed",
                       "valid": "frame_with_seed"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
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
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 9, 11)
        fhr, fwr = (4, 5), (5, 7)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 15)
        w = ctx.draw_int("grid_w", 13, 18)
        fhr, fwr = (6, 9), (9, 13)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 11, 14)
        fhr, fwr = (5, 7), (7, 10)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2)
    fc, sc = palette
    fh = min(rng.randint(*fhr), h)
    fw = min(rng.randint(*fwr), w)
    r1 = rng.randint(0, h - fh)
    c1 = rng.randint(0, w - fw)
    r2 = r1 + fh - 1
    c2 = c1 + fw - 1
    for c in range(c1, c2 + 1):
        g[r1][c] = fc; g[r2][c] = fc
    for r in range(r1, r2 + 1):
        g[r][c1] = fc; g[r][c2] = fc
    inner = [(r, c) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)]
    sr, sk = rng.choice(inner)
    g[sr][sk] = sc
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Executable invariants for the seeded checker-fill task.

    Default examples should teach one rectangle frame plus one interior seed.
    The canonical rule finds the largest rect-frame, takes the single non-frame
    colored cell inside it as the seed, and checker-fills zero cells of the same
    parity.  Catch regressions that remove/duplicate the seed, break the frame,
    or make the fill branch trivial.
    """
    errs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]

    by_color = {}
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v != 0:
                by_color.setdefault(v, []).append((r, c))
    if len(by_color) != 2:
        return [f"expected exactly frame+seed colors, got {sorted(by_color)}"]

    seed_color, seed_cells = min(by_color.items(), key=lambda kv: len(kv[1]))
    frame_color, frame_cells = max(by_color.items(), key=lambda kv: len(kv[1]))
    if len(seed_cells) != 1:
        errs.append(f"expected exactly one seed cell, got {len(seed_cells)}")
    if frame_color == seed_color:
        errs.append("frame and seed colors must differ")

    rs = [r for r, _ in frame_cells]
    cs = [c for _, c in frame_cells]
    r1, r2 = min(rs), max(rs)
    c1, c2 = min(cs), max(cs)
    if r2 - r1 + 1 < 4 or c2 - c1 + 1 < 5:
        errs.append(f"frame too small: {(r2-r1+1)}x{(c2-c1+1)}")
    expected = (
        {(r1, c) for c in range(c1, c2 + 1)}
        | {(r2, c) for c in range(c1, c2 + 1)}
        | {(r, c1) for r in range(r1, r2 + 1)}
        | {(r, c2) for r in range(r1, r2 + 1)}
    )
    frame_set = set(frame_cells)
    if frame_set != expected:
        errs.append("frame color cells are not exactly one rectangular outline")

    if len(seed_cells) == 1:
        sr, sc = seed_cells[0]
        if not (r1 < sr < r2 and c1 < sc < c2):
            errs.append(f"seed {seed_cells[0]} is not strictly inside the frame")
        same_parity_zeros = 0
        opposite_parity_zeros = 0
        for r in range(r1 + 1, r2):
            for c in range(c1 + 1, c2):
                if (r, c) == (sr, sc):
                    continue
                if grid[r][c] != 0:
                    errs.append(f"unexpected nonzero interior cell {(r, c)}")
                elif (r + c) % 2 == (sr + sc) % 2:
                    same_parity_zeros += 1
                else:
                    opposite_parity_zeros += 1
        # The smallest canonical/easy frame can have a 2x3 interior, so after
        # removing the seed there may be only two additional same-parity cells.
        # That is still a real checker fill; require at least two fill targets
        # and at least two contrast cells instead of overfitting to larger frames.
        if same_parity_zeros < 2:
            errs.append(f"checker fill too small/trivial: {same_parity_zeros} same-parity zeros")
        if opposite_parity_zeros < 2:
            errs.append(f"checker contrast too small: {opposite_parity_zeros} opposite-parity zeros")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_frame":
        # seed without frame → no boundary to fill within
        g[3][4] = 6
        return g
    if name == "no_seed":
        # frame without seed → no parity color to checker with
        for c in range(1, 8):
            g[1][c] = 4; g[5][c] = 4
        for r in range(1, 6):
            g[r][1] = 4; g[r][7] = 4
        return g
    if name == "multiple_seeds":
        # frame with 2 seeds → "exactly one seed" precondition fails
        for c in range(1, 8):
            g[1][c] = 4; g[5][c] = 4
        for r in range(1, 6):
            g[r][1] = 4; g[r][7] = 4
        g[2][3] = 6
        g[3][5] = 7  # second seed (different color too)
        return g
    return g
