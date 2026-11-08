"""Generator for puzzle 9968a131.

Rule: bg=7. Rows whose visible run starts with the larger color shift
right one cell; smaller-value rows stay fixed.

Combinatorial axes (8): row_count, grid_w, palette_kind, run_min,
run_max, start_min, start_max, anchor_corner.
Degenerates: empty_rows, all_same_color, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e83be06f6b58"
VERSION = "2.1.1"  # add executable self_check; clean (both branches 30/30) but: never used color 0 as fg (canonical does, bg=7), runs fixed 3-5 (canonical is 2), rigid even/odd. Add 0 to palette, run length 2-6, randomize which rows shift (guarantee both branches), easy >=2 rows
TASK_ID = "e83be06f6b58"
SUMMARY = (
    "Color-7 (orange) BACKGROUND grid "
    "(row_count~4-7, w~8-12). Each row contains "
    "a visible RUN of 3-5 cells using two "
    "ALTERNATING non-7 colors {a, b} from a "
    "palette, where a < b. Rows alternate which "
    "color STARTS the run: even rows start with "
    "a (smaller); odd rows start with b (larger). "
    "Run start column and length vary per row. "
    "Rule: examine each row's visible run. If "
    "the run STARTS with the MAX of the two "
    "colors (the larger one), SHIFT the entire "
    "row's run ONE CELL RIGHT (i.e., the leftmost "
    "cell becomes 7-bg, the rightmost shifts "
    "into the cell right of the previous end). "
    "If it starts with the min color, leave the "
    "row unchanged. Net: max-starting rows "
    "slide right by 1; min-starting rows stay."
)

INVARIANTS = [
    "background is 7",
    "rows have visible runs of 2 alternating colors",
    "runs starting with min color preserved; max-starting shift right",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("empty_rows", "all_same_color", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "row_count":      {"type": "int", "default": "rng 4..7", "valid": "1..12"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "run_min":        {"type": "int", "default": "3", "valid": "2..5"},
    "run_max":        {"type": "int", "default": "5", "valid": "3..7"},
    "start_min":      {"type": "int", "default": "0", "valid": "0..3"},
    "start_max":      {"type": "int", "default": "2", "valid": "0..4"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        rc_lo, rc_hi = 2, 4
    elif difficulty == "hard":
        rc_lo, rc_hi = 7, 12
    else:
        rc_lo, rc_hi = 4, 7
    row_count = int(overrides.get("row_count",
                                  ctx.draw_int("row_count", rc_lo, rc_hi)))
    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind")
                    or ctx.draw_choice("palette_kind",
                                       list(PALETTE_KINDS)))
    palette = _build_palette(palette_kind, rng)
    a, b = sorted(palette[:2])
    w = int(overrides.get("grid_w",
                          ctx.draw_int("grid_w", 8, 14)))
    run_min = int(overrides.get("run_min", 2))
    run_max = int(overrides.get("run_max", 6))
    start_min = int(overrides.get("start_min", 0))
    start_max = int(overrides.get("start_max", 3))
    g = full_grid(row_count, w, 7)
    # per-row start color: a (min) -> row stays, b (max) -> row shifts right.
    # randomize which rows shift, but guarantee BOTH branches appear.
    starts = [rng.choice([a, b]) for _ in range(row_count)]
    if len(set(starts)) == 1:
        starts[0] = a; starts[-1] = b
    for r in range(row_count):
        start = rng.randint(start_min, min(start_max, max(start_min, w - run_min - 1)))
        length = rng.randint(run_min, max(run_min, min(run_max, w - start - 1)))
        s0 = starts[r]
        s1 = b if s0 == a else a
        vals = [s0 if i % 2 == 0 else s1 for i in range(length)]
        for i, v in enumerate(vals):
            if start + i < w:
                g[r][start + i] = v
    return g


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [0, 1, 5, 8]          # 0 is a valid foreground here (bg is 7; canonical uses it)
    elif kind == "primary":
        pool = [0, 1, 2, 3, 4]
    else:
        pool = [0, 1, 2, 3, 4, 5, 6, 8, 9]
    pool = [c for c in pool if c != 7]
    rng.shuffle(pool)
    return pool


def _draw_from_degenerate(name, rng):
    h = 5; w = 10
    g = full_grid(h, w, 7)
    if name == "empty_rows":
        return g
    if name == "all_same_color":
        c = rng.choice([1, 2, 3, 4, 5, 6, 8, 9])
        for r in range(h):
            for cc in range(2, 7):
                g[r][cc] = c
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = rng.choice([1, 2, 3])
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Default demos must show both row branches with clean alternating runs."""
    msgs = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    if h == 0 or w == 0:
        return ["empty grid"]
    if any(len(row) != w for row in grid):
        msgs.append("ragged grid")
        return msgs
    if any(v == 7 for row in grid for v in row) is False:
        msgs.append("missing color-7 background")
    min_start = 0
    max_start = 0
    for r, row in enumerate(grid):
        nz = [c for c, v in enumerate(row) if v != 7]
        if not nz:
            msgs.append(f"row {r} has no visible run")
            continue
        if nz != list(range(nz[0], nz[-1] + 1)):
            msgs.append(f"row {r} has a non-contiguous visible run")
            continue
        vals = row[nz[0]:nz[-1] + 1]
        colors = sorted(set(vals))
        if len(colors) != 2:
            msgs.append(f"row {r} run does not use exactly two foreground colors")
            continue
        a, b = colors
        expected = [vals[0] if i % 2 == 0 else (b if vals[0] == a else a) for i in range(len(vals))]
        if vals != expected:
            msgs.append(f"row {r} run is not cleanly alternating")
        if nz[-1] >= w - 1:
            msgs.append(f"row {r} run has no right-side space for the shift branch")
        if vals[0] == a:
            min_start += 1
        elif vals[0] == b:
            max_start += 1
    if min_start < 1:
        msgs.append("no min-start row branch")
    if max_start < 1:
        msgs.append("no max-start row branch")
    return msgs
