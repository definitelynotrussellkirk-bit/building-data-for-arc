"""Generator for arc_additional_puzzles_21_set15_bundle:H101.

Rule: row 0 holds a sequence of transform COMMANDS (codes 1-6 =
identity / rot-cw / rot-180 / transpose / flip-lr / flip-ud). The MOTIF
is the cropped non-zero content below row 0. Output = the motif
transformed by each command in turn, packed left-to-right with 1-column
gaps (height = the tallest piece).

Combinatorial axes: grid size, the command sequence (length + codes),
the motif shape, and the motif color.
Degenerates: no_motif, no_commands, full_grid_motif.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1e597464e3c7"
VERSION = "2.0.1"


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: row 0 has command codes in {1..6}; motif exists below row 0."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if h < 2:
        return [f"grid too short: {h} rows (need >=2)"]
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
        return errs
    row0_nz = [grid[0][c] for c in range(w) if grid[0][c] != 0]
    if not row0_nz:
        errs.append("row 0 has no command codes")
    elif any(v not in {1, 2, 3, 4, 5, 6} for v in row0_nz):
        bad = [v for v in row0_nz if v not in {1, 2, 3, 4, 5, 6}]
        errs.append(f"row 0 has invalid command codes: {bad}")
    body_nz = [(r, c) for r in range(1, h) for c in range(w) if grid[r][c] != 0]
    if not body_nz:
        errs.append("no motif cells below row 0")
    return errs
TASK_ID = "1e597464e3c7"
SUMMARY = (
    "0-bg grid (size varies). Row 0 holds 2-5 transform COMMANDS (codes "
    "1-6: id / rot-cw / rot-180 / transpose / flip-lr / flip-ud) in the "
    "leftmost cells. Below row 0 sits a single MOTIF (a connected "
    "polyomino in one color). Rule: crop the motif, apply each command to "
    "it, and pack the transformed copies left-to-right with 1-column gaps "
    "(output height = the tallest piece). The grid size, the command "
    "sequence, the motif shape and color all vary freely (was a fixed 7x9 "
    "motif + sample_index-keyed commands, ~9 distinct)."
)

INVARIANTS = [
    "row 0 holds a left-packed sequence of 2-5 transform codes (1-6)",
    "below row 0 is exactly one connected motif in a single color",
    "the motif is the cropped non-zero content below row 0",
]

PALETTE_KINDS = ("default", "wide_motif_color", "rainbow_command", "minimal")
DEGENERATE_TEXTURES = ("no_motif", "no_commands", "full_grid_motif")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "6..10"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|wide_motif_color|rainbow_command|minimal"},
    "command_count":  {"type": "int", "default": "varies", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|wide_motif_color|rainbow_command|minimal|"
                                "no_motif|no_commands|full_grid_motif"},
}


def _conn_poly(rng, size, maxd):
    for _ in range(80):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        mr = min(r for r, c in cells); mc = min(c for r, c in cells)
        n = [(r - mr, c - mc) for r, c in cells]
        if max(r for r, c in n) < maxd and max(c for r, c in n) < maxd:
            return n
    return [(0, 0), (0, 1), (1, 0)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)

    if difficulty == "easy":
        hr, wr, ncr, szr, md = (6, 8), (9, 12), (2, 2), (3, 4), 3
    elif difficulty == "hard":
        hr, wr, ncr, szr, md = (7, 10), (12, 16), (3, 5), (4, 6), 4
    else:
        hr, wr, ncr, szr, md = (6, 9), (10, 14), (2, 4), (3, 5), 4

    for _attempt in range(40):
        n_cmd = rng.randint(*ncr)
        motif = _conn_poly(rng, rng.randint(*szr), md)
        mh = max(r for r, c in motif) + 1; mw = max(c for r, c in motif) + 1
        h = rng.randint(*hr); w = rng.randint(*wr)
        if n_cmd > w or mw > w or mh + 1 > h:
            continue
        g = full_grid(h, w, 0)
        # commands in row 0, leftmost cells
        for i in range(n_cmd):
            g[0][i] = rng.randint(1, 6)
        # motif somewhere in rows 1.., in one color
        color = rng.randint(1, 9)
        top = rng.randint(1, h - mh); left = rng.randint(0, w - mw)
        for r, c in motif:
            g[top + r][left + c] = color
        return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 9, 0)
    if name == "no_motif":
        for i in range(3):
            g[0][i] = i + 1
        return g
    if name == "no_commands":
        for dr, dc in [(0, 0), (1, 0), (1, 1), (2, 1)]:
            g[2 + dr][2 + dc] = 7
        return g
    if name == "full_grid_motif":
        for r in range(1, 7):
            for c in range(9):
                g[r][c] = 7
        g[0][0] = 1
        return g
    return g
