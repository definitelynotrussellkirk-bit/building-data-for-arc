"""Generator for arc_puzzle_bank_21_set20_s:S20_E4.

A selector panel chooses the color used to fill exact template matches.

Combinatorial axes (8): grid_h, grid_w, palette_kind, match_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_template, no_selector, no_matches.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.panels import assemble_vertical_panels, paste

GENERATOR_ID = "f19060885666"
VERSION = "2.0.1"  # add executable self_check for template/selector/board invariants
TASK_ID = "f19060885666"
SUMMARY = ("3 panels split by full-9 columns: a TEMPLATE (plus of color 5), a "
           "SELECTOR (one fill color != 5/9), and a BOARD holding several plus-of-5 "
           "shapes. Rule: recolor every exact template match in the board to the "
           "selector color. (Was: hardcoded multicolor 3x3 block template.)")

INVARIANTS = [
    "divider color is 9",
    "panel 1 contains the template",
    "panel 2 contains one selector color",
    "panel 3 contains exact template matches",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_template", "no_selector", "no_matches")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "derived", "valid": "17..32"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "match_count":    {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "8", "valid": "8..8"},
    "position_bias":  {"type": "str", "default": "template_selector_board_3panels",
                       "valid": "template_selector_board_3panels"},
    "n_distinct_colors": {"type": "int", "default": "8", "valid": "8..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

TEMPLATE = [[0, 5, 0], [5, 5, 5], [0, 5, 0]]   # plus of color 5 (canonical template)


def _matches_template_at(grid, top, left):
    h, w = len(grid), len(grid[0])
    if top + 3 > h or left + 3 > w:
        return False
    for dr in range(3):
        for dc in range(3):
            if grid[top + dr][left + dc] != TEMPLATE[dr][dc]:
                return False
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    h, w = len(grid), len(grid[0])
    divs = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(divs) != 2:
        errors.append(f"expected exactly two full-height divider columns, found {len(divs)}")
        return errors
    d0, d1 = divs
    if d0 != 5 or d1 != 9:
        errors.append(f"expected divider columns at 5 and 9; got {divs}")
    template_panel = [row[:d0] for row in grid]
    selector_panel = [row[d0 + 1:d1] for row in grid]
    board = [row[d1 + 1:] for row in grid]
    if not _matches_template_at(template_panel, 1, 1):
        errors.append("template panel must contain canonical plus-of-5 at row=1,col=1")
    selectors = [(r, c, v) for r, row in enumerate(selector_panel) for c, v in enumerate(row) if v != 0]
    if len(selectors) != 1:
        errors.append(f"expected exactly one selector cell, found {len(selectors)}")
    elif selectors[0][2] in (5, 9):
        errors.append(f"selector color must differ from template/divider colors, got {selectors[0][2]}")
    matches = [(r, c) for r in range(max(0, len(board) - 2)) for c in range(max(0, len(board[0]) - 2))
               if _matches_template_at(board, r, c)]
    if not matches:
        errors.append("board must contain at least one exact plus-of-5 template match")
    board_vals = {v for row in board for v in row if v != 0}
    if board_vals - {5}:
        errors.append(f"board should contain only color-5 template cells before recolor, got {sorted(board_vals)}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("board_h", 8, 9)
        w = ctx.draw_int("board_w", 9, 11)
        count = ctx.draw_int("match_count", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("board_h", 11, 14)
        w = ctx.draw_int("board_w", 13, 18)
        count = ctx.draw_int("match_count", 4, 6)
    else:
        h = ctx.draw_int("board_h", 9, 12)
        w = ctx.draw_int("board_w", 11, 14)
        count = ctx.draw_int("match_count", 3, 5)
    rng = ctx.draw_rng("layout")
    template_panel = full_grid(h, 5, 0)
    paste(template_panel, TEMPLATE, 1, 1)
    selector = full_grid(h, 3, 0)
    selector[h // 2][1] = rng.choice([1, 2, 3, 4, 6, 7, 8])   # fill color != 5 (shape), != 9 (divider)
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
    return assemble_vertical_panels([template_panel, selector, board])


def _draw_from_degenerate(name, rng):
    h = 8
    if name == "no_template":
        # selector + board matches but no template → no shape to compare
        selector = full_grid(h, 3, 0)
        selector[h // 2][1] = 5
        board = full_grid(h, 9, 0)
        paste(board, TEMPLATE, 2, 2)
        return assemble_vertical_panels([selector, board])
    if name == "no_selector":
        # template + board matches but no selector color → no fill color defined
        template_panel = full_grid(h, 5, 0)
        paste(template_panel, TEMPLATE, 1, 1)
        selector = full_grid(h, 3, 0)
        board = full_grid(h, 9, 0)
        paste(board, TEMPLATE, 2, 2)
        return assemble_vertical_panels([template_panel, selector, board])
    if name == "no_matches":
        # template + selector but empty board → no targets to recolor
        template_panel = full_grid(h, 5, 0)
        paste(template_panel, TEMPLATE, 1, 1)
        selector = full_grid(h, 3, 0)
        selector[h // 2][1] = 5
        board = full_grid(h, 9, 0)
        return assemble_vertical_panels([template_panel, selector, board])
    return full_grid(h, 9, 0)
