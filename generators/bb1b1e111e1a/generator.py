"""Generator for arc_puzzle_bank_sixteenth21:H110 — 3-panel mask-select combine.

Rule: the grid is 3 equal-width panels separated by single COLOR-5 columns
(width = 3*pw + 2). panel0 = MASK, panel1 = A, panel2 = B. The output is a
pw-wide grid where each cell takes A's value if the MASK cell is non-zero,
else B's value. (`s17-split-panel-row g 3` then per-cell select.)

Combinatorial axes: grid_h, panel_w, mask_density, palette per panel.
Degenerates: mask_all_zero (output == B), mask_all_on (output == A),
identical_panels (A == B → output == A == B regardless of mask).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bb1b1e111e1a"
VERSION = "2.1.0"  # 1.1.0->2.0.0: WRONG-TASK rewrite. Old gen made scattered
# motifs with no panel structure (rule is a 3-panel color-5-separated mask
# select). Now builds 3 equal-width panels + single 5-columns; panel0 mask
# picks A vs B per cell. Mask density, panel contents, palette all varied.
TASK_ID = "bb1b1e111e1a"

SUMMARY = (
    "Grid = 3 equal-width panels separated by single color-5 columns. "
    "panel0 is a binary MASK (some color on bg 0), panel1 (A) and panel2 (B) "
    "hold colored content. Rule: output[r][c] = A[r][c] where mask non-zero, "
    "else B[r][c]."
)

INVARIANTS = [
    "width == 3*panel_w + 2",
    "the two separator columns (at panel_w and 2*panel_w+1) are entirely color 5",
    "panel0 (mask) contains both zero and non-zero cells (so both A and B show)",
    "panels A and B are not identical (so the mask choice is observable)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("mask_all_zero", "mask_all_on", "identical_panels")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":       {"type": "int", "default": "rng 4..7", "valid": "3..10"},
    "panel_w":      {"type": "int", "default": "rng 4..7", "valid": "3..9"},
    "mask_density": {"type": "float", "default": "rng 0.3..0.7", "valid": "0.1..0.9"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "|".join(PALETTE_KINDS)},
    "texture":      {"type": "str", "default": "alias for palette_kind",
                     "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _assemble(h, pw, mask_painted, a_painted, b_painted,
              mask_color, a_color, b_color):
    """Build the full 3-panel grid with single color-5 separator columns."""
    w = 3 * pw + 2
    g = full_grid(h, w, 0)
    # panel0 = mask at col 0..pw-1
    for (r, c) in mask_painted:
        g[r][c] = mask_color
    # separator col at pw
    sep1 = pw
    sep2 = 2 * pw + 1
    for r in range(h):
        g[r][sep1] = 5
        g[r][sep2] = 5
    # panel1 = A at col pw+1 .. 2*pw
    a_left = pw + 1
    for (r, c) in a_painted:
        g[r][a_left + c] = a_color
    # panel2 = B at col 2*pw+2 .. 3*pw+1
    b_left = 2 * pw + 2
    for (r, c) in b_painted:
        g[r][b_left + c] = b_color
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"],
                                     ctx.draw_rng("degenerate"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 5)
        pw = ctx.draw_int("panel_w", 4, 5)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 9)
        pw = ctx.draw_int("panel_w", 6, 9)
    else:
        h = ctx.draw_int("grid_h", 4, 7)
        pw = ctx.draw_int("panel_w", 4, 7)
    rng = ctx.draw_rng("layout")

    # distinct colors for mask / A / B
    mask_color, a_color, b_color = rng.sample([2, 3, 4, 6, 7, 8, 9], 3)

    for _ in range(40):
        density = rng.uniform(0.3, 0.7)
        mask_painted = _fill_panel_mask(rng, h, pw, density)  # both on+off cells
        a_painted = _panel_cells(rng, h, pw, rng.uniform(0.3, 0.8))
        b_painted = _panel_cells(rng, h, pw, rng.uniform(0.3, 0.8))
        # Ensure the training input contains visible evidence for both branches:
        # at least one mask-on cell draws from A and at least one mask-off cell
        # draws from B.  A != B alone allowed a branch to be hidden when the
        # chosen panel had no painted cell under the relevant mask state.
        shows_a = bool(mask_painted & a_painted)
        shows_b = bool(b_painted - mask_painted)
        if a_painted == b_painted or not (shows_a and shows_b):
            continue
        return _assemble(h, pw, mask_painted, a_painted, b_painted,
                         mask_color, a_color, b_color)
    # fallback: guaranteed-valid layout
    mask_painted = {(0, 0), (0, 1), (1, 1)}
    a_painted = {(r, c) for r in range(h) for c in range(pw)}
    b_painted = set()
    return _assemble(h, pw, mask_painted, a_painted, b_painted,
                     mask_color, a_color, b_color)


def _fill_panel_mask(rng, h, pw, density):
    """Mask cells: both on and off must appear so both A and B contribute."""
    while True:
        painted = {(r, c) for r in range(h) for c in range(pw)
                   if rng.random() < density}
        # need at least one on AND one off
        if 0 < len(painted) < h * pw:
            return painted


def _panel_cells(rng, h, pw, density):
    return {(r, c) for r in range(h) for c in range(pw)
            if rng.random() < density}


def _draw_from_degenerate(name, rng):
    h, pw = 5, 5
    mask_color, a_color, b_color = 8, 2, 6
    if name == "mask_all_zero":
        # mask entirely 0 -> output == B everywhere
        mask = set()
        a = {(r, c) for r in range(h) for c in range(pw) if rng.random() < 0.5}
        b = {(r, c) for r in range(h) for c in range(pw) if rng.random() < 0.5}
        return _assemble(h, pw, mask, a, b, mask_color, a_color, b_color)
    if name == "mask_all_on":
        # mask entirely on -> output == A everywhere
        mask = {(r, c) for r in range(h) for c in range(pw)}
        a = {(r, c) for r in range(h) for c in range(pw) if rng.random() < 0.5}
        b = {(r, c) for r in range(h) for c in range(pw) if rng.random() < 0.5}
        return _assemble(h, pw, mask, a, b, mask_color, a_color, b_color)
    if name == "identical_panels":
        # A == B -> output independent of mask
        same = {(r, c) for r in range(h) for c in range(pw) if rng.random() < 0.5}
        mask = {(r, c) for r in range(h) for c in range(pw) if rng.random() < 0.5}
        return _assemble(h, pw, mask, same, same, mask_color, a_color, b_color)
    return _assemble(h, pw, {(0, 0)}, {(1, 1)}, set(),
                     mask_color, a_color, b_color)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    issues: list[str] = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    if h == 0 or w < 11 or (w - 2) % 3 != 0:
        return ["width must be 3*panel_w+2"]
    pw = (w - 2) // 3
    sep1, sep2 = pw, 2 * pw + 1
    if any(row[sep1] != 5 or row[sep2] != 5 for row in grid):
        issues.append("separator columns are not all color 5")
    mask = [row[:pw] for row in grid]
    a = [row[pw + 1:2 * pw + 1] for row in grid]
    b = [row[2 * pw + 2:] for row in grid]
    mask_on = {(r, c) for r in range(h) for c in range(pw) if mask[r][c] != 0}
    if not (0 < len(mask_on) < h * pw):
        issues.append("mask must contain both on and off cells")
    shows_a = any((r, c) in mask_on and a[r][c] != 0 for r in range(h) for c in range(pw))
    shows_b = any((r, c) not in mask_on and b[r][c] != 0 for r in range(h) for c in range(pw))
    if not shows_a:
        issues.append("no visible A-selected cell")
    if not shows_b:
        issues.append("no visible B-selected cell")
    if a == b:
        issues.append("A and B panels identical")
    return issues
