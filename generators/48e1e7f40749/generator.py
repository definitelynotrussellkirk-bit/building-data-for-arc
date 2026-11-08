"""Generator for arc_additional_puzzles_21_set17_bundle:H113 — palette-lift matrix with commands.

Rule: row 0 holds 3 palette colors. Rows 1-2 cols 0-1 are selectors (4 of them
referencing bank keys). Rows 3-4 cols 0-1 are transform commands. Row 6 has
bank keys; rows 7-9 hold 3x3 templates anchored at each key's column. For each
of 4 selector cells, look up the template, apply its transform, recolor with
the palette, and assemble into a 6x6 2x2 mosaic.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_palette (row 0 empty → rule's color-lift map is
empty); no_bank (row 6 / template area empty → rule's selectors
have no targets); selector_unmatched (selector references key not
present in bank → rule's lookup returns nothing).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "48e1e7f40749"
VERSION = "3.1.0"  # shape-locked-in (fixed 10x11): output is intrinsically 6x6 (2x2 of 3x3 blocks), but the INPUT width varies with the BANK size (row-6 keys + 3x3 blocks at cols 0,4,8,...). Now nbank 3..5 -> width 11/15/19; selectors reference keys 1..nbank. Height stays 10 (fixed meta-layout).
TASK_ID = "48e1e7f40749"

SUMMARY = (
    "Fixed 10×11 grid with: (a) "
    "ROW 0 cols 0-2 hold 3 "
    "DISTINCT PALETTE COLORS "
    "(rest 0); (b) ROWS 1-2 cols "
    "0-1 hold 4 SELECTOR cells "
    "(values 1..3 referencing "
    "bank keys); (c) ROWS 3-4 "
    "cols 0-1 hold 4 TRANSFORM "
    "COMMAND codes (0..5); (d) "
    "ROW 6 cols 0, 4, 8 hold "
    "3 BANK KEYS (values 1, 2, "
    "3); (e) ROWS 7-9 cols "
    "kcol..kcol+2 hold three "
    "3×3 TEMPLATES anchored at "
    "each bank key column with "
    "~50% sparsity. Rest is 0. "
    "Rule (PALETTE-LIFT MATRIX "
    "WITH TRANSFORMS): for EACH "
    "of 4 SELECTOR positions, "
    "look up the bank template "
    "by the selector's key, "
    "APPLY the transform "
    "indexed by the matching "
    "command, RECOLOR using the "
    "row-0 palette, and "
    "assemble all four results "
    "into a 6×6 2×2 MOSAIC. "
    "Output: 6×6 mosaic of "
    "4 transformed 3×3 "
    "palette-lifted templates. "
    "Net: matrix-of-templates "
    "addressed by selector × "
    "command → 2×2 mosaic with "
    "palette-colored cells."
)

INVARIANTS = [
    "background is 0",
    "row 0 has 3 distinct non-zero palette colors at cols 0, 1, 2 (rest 0)",
    "rows 1-2 cols 0-1 hold 4 selector keys (each in {1, 2, 3} matching a bank key)",
    "rows 3-4 cols 0-1 hold 4 transform commands (codes 0..5)",
    "row 6 has 3 distinct bank keys (1, 2, 3) at distinct columns spaced 4 apart",
    "rows 7-9 hold three 3x3 templates anchored at each bank key column",
    "rest of the grid is 0",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_palette", "no_bank", "selector_unmatched")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "fixed 10", "valid": "10"},
    "grid_w":            {"type": "int", "default": "4*nbank-1", "valid": "11|15|19"},
    "n_bank":            {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "palette_size":      {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "position_bias":     {"type": "str", "default": "fixed_meta_layout",
                          "valid": "fixed_meta_layout"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|no_palette|no_bank|selector_unmatched"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    # bank size drives input WIDTH (output is intrinsically 6x6).
    if difficulty == "easy":
        nbank = ctx.draw_int("n_bank", 3, 3)
    elif difficulty == "hard":
        nbank = ctx.draw_int("n_bank", 4, 5)
    else:
        nbank = ctx.draw_int("n_bank", 3, 4)
    h = 10
    w = 4 * nbank - 1
    g = full_grid(h, w, 0)

    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 3)
    for i, color in enumerate(palette):
        g[0][i] = color

    # selectors (rows 1-2) reference bank keys 1..nbank; commands (rows 3-4) 0..5
    for r in (1, 2):
        g[r][0] = rng.randint(1, nbank); g[r][1] = rng.randint(1, nbank)
    for r in (3, 4):
        g[r][0] = rng.randint(0, 5); g[r][1] = rng.randint(0, 5)
    command_cells = [(3, 0), (3, 1), (4, 0), (4, 1)]
    if len({g[r][c] for r, c in command_cells}) < 2:
        # Avoid rare all-same commands, which hide the transform-code branch.
        g[4][1] = (g[3][0] + 1) % 6

    bank_cols = [4 * i for i in range(nbank)]
    keys = list(range(1, nbank + 1))
    rng.shuffle(keys)
    for kcol, key in zip(bank_cols, keys):
        g[6][kcol] = key
        for r in range(7, 10):
            for c in range(kcol, kcol + 3):
                if rng.random() < 0.5:
                    g[r][c] = rng.randint(1, 3)
        if all(g[r][c] == 0 for r in range(7, 10) for c in range(kcol, kcol + 3)):
            g[rng.randint(7, 9)][rng.randint(kcol, kcol + 2)] = rng.randint(1, 3)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    if h != 10 or (w + 1) % 4 != 0:
        errs.append("expected 10 x (4*bank-1) meta-layout")
        return errs
    nbank = (w + 1) // 4
    palette = grid[0][:3]
    if len(set(palette)) != 3 or any(v == 0 for v in palette):
        errs.append("palette row should contain three distinct non-zero colors")
    keys = [grid[6][4 * i] for i in range(nbank)]
    if sorted(keys) != list(range(1, nbank + 1)):
        errs.append("bank keys should be a permutation of 1..nbank")
    commands = [grid[r][c] for r in (3, 4) for c in (0, 1)]
    if len(set(commands)) < 2:
        errs.append("expected at least two transform commands")
    for i in range(nbank):
        kcol = 4 * i
        if all(grid[r][c] == 0 for r in range(7, 10) for c in range(kcol, kcol + 3)):
            errs.append("bank templates should be nonempty")
            break
    return errs



def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "no_palette":
        # Row 0 empty — rule's color-lift map is empty.
        for r in (1, 2):
            g[r][0] = 1; g[r][1] = 2
        for r in (3, 4):
            g[r][0] = 0; g[r][1] = 1
        bank_cols = [0, 4, 8]
        for kcol, key in zip(bank_cols, [1, 2, 3]):
            g[6][kcol] = key
            g[7][kcol] = 1
            g[8][kcol + 1] = 2
        return g
    if name == "no_bank":
        # No bank rows — rule's selectors find no templates.
        g[0][0] = 4; g[0][1] = 5; g[0][2] = 6
        for r in (1, 2):
            g[r][0] = 1; g[r][1] = 2
        for r in (3, 4):
            g[r][0] = 0; g[r][1] = 1
        return g
    if name == "selector_unmatched":
        # Selectors reference keys not in bank.
        g[0][0] = 4; g[0][1] = 5; g[0][2] = 6
        for r in (1, 2):
            g[r][0] = 3; g[r][1] = 3   # all 3s
        for r in (3, 4):
            g[r][0] = 0; g[r][1] = 1
        # Bank only has key 1 (no 2 or 3)
        g[6][0] = 1
        g[7][0] = 1; g[8][1] = 2
        return g
    return g
