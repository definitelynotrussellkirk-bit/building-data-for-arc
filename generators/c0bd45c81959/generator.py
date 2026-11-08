"""Generator for puzzle af24b4cc.

Rule: 2x3 cell-grid where each cell is 3rows x 2cols. Output is 4x5
with 0-border and mode color of each cell.

Combinatorial axes (8): n_distract_min, n_distract_max, palette_kind,
palette_size, mode_distribution, anchor_corner, asymmetry_force,
include_decoy.
Degenerates: tied_modes, single_color, full_grid.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c0bd45c81959"
VERSION = "1.3.2"
TASK_ID = "c0bd45c81959"
SUMMARY = "Fixed 9×10 grid with 6 cells (2×3 macro grid), each cell is 3 rows × 2 cols, separated by all-0 row 4 and all-0 cols 3 + 6 + border. Each cell has a majority color + possible distractor cells. Rule outputs a 4×5 grid: 0-border + each interior position = mode color of corresponding 3×2 cell."

# Rivals: 'output is input' refuted by any demo (output is 4×5).
# 'use any cell value' refuted by ≥2 demos where mode-color wins
# over outliers. 'output sized by input' refuted by any demo (always
# 4×5). 'use 0 for cell value' refuted by any demo where cell-mode
# is non-zero. 3 demos with varied modes cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "h>=8, w>=9 (rule reads last block at row 7, col 8; extra is bg-padding)",
    "blocks at fixed coords: rows 1-3 & 5-7, cols 1-2, 4-5, 7-8",
    "separator rows/cols and margins are all 0",
    "each 3x2 cell has unique majority non-zero color",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary", "rng")
DEGENERATE_TEXTURES = ("tied_modes", "single_color", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "n_distract_min": {"type": "int", "default": "1", "valid": "0..2"},
    "n_distract_max": {"type": "int", "default": "2", "valid": "1..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "6", "valid": "6"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "include_decoy":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "border_color":   {"type": "color", "default": "0", "valid": "0"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify the fixed six-block domain and a unique nonzero mode per block."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    if h < 8:
        errs.append(f"grid too short (h={h}); rule needs h≥8 to read all blocks")
    if w < 9:
        errs.append(f"grid too narrow (w={w}); rule needs w≥9 to read all blocks")
    if h < 8 or w < 9:
        return errs

    block_cells = {
        (r, c)
        for br in range(2)
        for bc in range(3)
        for r in range(1 + 4 * br, 4 + 4 * br)
        for c in range(1 + 3 * bc, 3 + 3 * bc)
    }
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if (r, c) not in block_cells and value != 0:
                errs.append(f"non-block cell ({r},{c}) must be zero")
                break
        if errs and errs[-1].startswith("non-block"):
            break

    for br in range(2):
        for bc in range(3):
            r1, c1 = 1 + 4 * br, 1 + 3 * bc
            counts = Counter(
                grid[r][c]
                for r in range(r1, r1 + 3)
                for c in range(c1, c1 + 2)
                if grid[r][c] != 0
            )
            if not counts:
                errs.append(f"block ({br},{bc}) has no nonzero mode")
                continue
            maximum = max(counts.values())
            winners = [color for color, count in counts.items() if count == maximum]
            if len(winners) != 1:
                errs.append(
                    f"block ({br},{bc}) needs one unique nonzero mode; tied {sorted(winners)}"
                )
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    palette_kind = (overrides.get("texture") or
                    overrides.get("palette_kind")
                    or ctx.draw_choice("palette_kind",
                                       list(PALETTE_KINDS)))
    palette = _build_palette(palette_kind, 6, rng)
    n_min = int(overrides.get("n_distract_min", 1))
    n_max = int(overrides.get("n_distract_max", 2))
    n_min = max(0, min(2, n_min))
    n_max = max(n_min, min(3, n_max))
    # The rule reads 6 blocks at FIXED coords (rows 1-3 & 5-7, cols 1-2,4-5,7-8)
    # and ignores everything else; the output is always 4x5. v1.2.0 hardcoded
    # 9x10 -> in_shapes=1 (shape-locked-in). The grid only needs to reach the last
    # read cell (row 7, col 8), so pad it bigger with bg=0 (matches canonical's
    # all-0 margins) to vary input size without touching the block reads.
    h = ctx.draw_int("grid_h", 8, 13)
    w = ctx.draw_int("grid_w", 9, 14)
    g = full_grid(h, w, 0)
    cell_idx = 0
    for br in range(2):
        for bc in range(3):
            r1 = 1 + br * 4
            c1 = 1 + bc * 3
            mode_color = palette[cell_idx]
            distract = [v for v in palette if v != mode_color]
            cell_idx += 1
            n_d = rng.randint(n_min, n_max)
            for r in range(r1, r1 + 3):
                for c in range(c1, c1 + 2):
                    g[r][c] = mode_color
            cells = [(r, c) for r in range(r1, r1 + 3)
                     for c in range(c1, c1 + 2)]
            rng.shuffle(cells)
            # Three replaced cells may still be lawful, but using one repeated
            # distractor three times creates a 3-3 tie with the intended mode.
            # Distinct distractor colors preserve the advertised override while
            # guaranteeing that the original mode remains unique.
            distractor_colors = rng.sample(distract, n_d)
            for (r, c), color in zip(cells[:n_d], distractor_colors):
                g[r][c] = color
    return g


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def _draw_from_degenerate(name, rng):
    h = 9; w = 10
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 6)
    if name == "tied_modes":
        # Each cell has tied mode → ambiguous
        for br in range(2):
            for bc in range(3):
                r1 = 1 + br * 4
                c1 = 1 + bc * 3
                g[r1][c1] = palette[0]; g[r1][c1 + 1] = palette[1]
                g[r1 + 1][c1] = palette[1]; g[r1 + 1][c1 + 1] = palette[0]
                g[r1 + 2][c1] = palette[0]; g[r1 + 2][c1 + 1] = palette[1]
        return g
    if name == "single_color":
        c = palette[0]
        for r in range(1, 8):
            if r in (4,):
                continue
            for cc in range(1, 9):
                if cc in (3, 6):
                    continue
                g[r][cc] = c
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = palette[0]
        return g
    return g
