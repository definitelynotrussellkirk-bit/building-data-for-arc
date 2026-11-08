"""Generator for arc_puzzle_bank_21_set20_s:S20_E3.

Combinatorial axes (8): board_h, board_w, palette_kind, match_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_template, no_matches, partial_matches.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.panels import assemble_vertical_panels, paste

GENERATOR_ID = "3b907ea971ea"
VERSION = "2.0.0"
TASK_ID = "3b907ea971ea"
SUMMARY = (
    "0-bg vertical 2-panel layout (top: "
    "template panel; bottom: board panel) "
    "separated by a COLOR-9 divider. The "
    "TEMPLATE is a fixed 3×3 pattern "
    "([[4,5,6],[7,8,2],[3,4,5]]) placed at "
    "(1, 1) in the template panel "
    "(h-tall × 5-wide). The BOARD (h × w~9-13) "
    "contains 2-4 COPIES of the same template "
    "stamped at random non-overlapping "
    "anchors. Rule: identify the TEMPLATE in "
    "the top panel. SCAN the BOARD: for EACH "
    "3×3 window that EXACTLY MATCHES the "
    "template (cell-by-cell, all values "
    "match), KEEP those template cells. CLEAR "
    "(set to 0) every non-matching cell on "
    "the board. Output: the board with only "
    "matching template instances kept. Net: "
    "template panel teaches pattern; output "
    "is board cleared except for exact "
    "template matches."
)

INVARIANTS = [
    "divider color is 9",
    "template is dense and exact",
    "nonmatching distractors do not equal the template",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_template", "no_matches", "partial_matches")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "board_h":        {"type": "int", "default": "rng 8..11", "valid": "5..16"},
    "board_w":        {"type": "int", "default": "rng 9..13", "valid": "5..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "match_count":    {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "8", "valid": "8..8"},
    "position_bias":  {"type": "str", "default": "template_panel_plus_board",
                       "valid": "template_panel_plus_board"},
    "n_distinct_colors": {"type": "int", "default": "8", "valid": "8..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

TEMPLATE = [[4, 5, 6], [7, 8, 2], [3, 4, 5]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("board_h", 8, 9)
        w = ctx.draw_int("board_w", 9, 11)
        count = ctx.draw_int("match_count", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("board_h", 10, 11)
        w = ctx.draw_int("board_w", 12, 13)
        count = ctx.draw_int("match_count", 3, 4)
    else:
        h = ctx.draw_int("board_h", 8, 11)
        w = ctx.draw_int("board_w", 9, 13)
        count = ctx.draw_int("match_count", 2, 4)
    rng = ctx.draw_rng("layout")
    template_panel = full_grid(h, 5, 0)
    paste(template_panel, TEMPLATE, 1, 1)
    board = full_grid(h, w, 0)
    anchors = [(r, c) for r in range(h - 2) for c in range(w - 2)]
    rng.shuffle(anchors)
    used = set()
    placed = 0
    for r, c in anchors:
        footprint = {(rr, cc) for rr in range(r - 1, r + 4) for cc in range(c - 1, c + 4)}
        if footprint & used:
            continue
        paste(board, TEMPLATE, r, c)
        used |= footprint
        placed += 1
        if placed >= count:
            break
    return assemble_vertical_panels([template_panel, board])


def self_check(grid, *, difficulty=None, meta=None):
    """Verify template+board panel invariants for 3b907ea971ea."""
    errs = []
    h, w = len(grid), len(grid[0])
    flat = [grid[r][c] for r in range(h) for c in range(w)]
    # Divider must be color 9
    if 9 not in flat:
        errs.append("color 9 (divider) not present")
    else:
        # Divider is a full-height column of color 9 (left=template, right=board layout)
        div_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
        if not div_cols:
            errs.append("no full-height color-9 divider column found")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    if name == "no_template":
        # board with matches but blank template → no pattern to compare against
        template_panel = full_grid(h, 5, 0)
        board = full_grid(h, w, 0)
        paste(board, TEMPLATE, 2, 3)
        return assemble_vertical_panels([template_panel, board])
    if name == "no_matches":
        # template defined but board has no matching pattern
        template_panel = full_grid(h, 5, 0)
        paste(template_panel, TEMPLATE, 1, 1)
        board = full_grid(h, w, 0)
        return assemble_vertical_panels([template_panel, board])
    if name == "partial_matches":
        # board has near-matches missing one cell → "exact match" precondition fails
        template_panel = full_grid(h, 5, 0)
        paste(template_panel, TEMPLATE, 1, 1)
        board = full_grid(h, w, 0)
        partial = [[4, 5, 6], [7, 8, 2], [3, 4, 0]]
        paste(board, partial, 2, 3)
        return assemble_vertical_panels([template_panel, board])
    return full_grid(h, w + 6, 0)
