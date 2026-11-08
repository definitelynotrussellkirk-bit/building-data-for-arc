"""Generator for arc_puzzle_bank_21_set20_s:S20_E2.

Rule (canonical Racket): split input at a full color-9 divider column. Crop the
nonzero/non-9 pattern from the left panel; zero cells inside that crop are
wildcards. Scan the right board for same-orientation matches of the template,
and render a board-sized output with color 8 at the template's occupied cells
for every match.

Combinatorial axes: grid height, board width, template shape, match count,
match placement, distractors.
Degenerates: no_matches, no_template, single_match.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.panels import assemble_vertical_panels

GENERATOR_ID = "d50ba3ef0962"
VERSION = "3.0.0"  # semantic fix: generate the canonical left-template / right-board wildcard-match task, not a dense multicolor 3x3 exact-match gallery.
TASK_ID = "d50ba3ef0962"
SUMMARY = (
    "0-bg grid split by one full color-9 divider column. The left panel holds a "
    "cropped color-3 template with internal 0 wildcard cells; the right board "
    "contains 2-4 separated same-orientation occurrences of that template. "
    "Rule: crop the left template, scan the board with zeros as wildcards, and "
    "render the union of matched occupied template cells as color 8 on a "
    "board-sized output."
)

INVARIANTS = [
    "one full-height color-9 divider column separates template panel and board",
    "left panel contains one nonempty color-3 template; zeros are wildcards",
    "right board contains at least two same-orientation matches of the template",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_matches", "no_template", "single_match")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..10", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "derived from panels", "valid": "9..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "match_count":    {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "3", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "template_board_matches",
                       "valid": "template_board_matches"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_matches|no_template|single_match"},
}

# Occupied cells of template crops, normalized to (0, 0). Zero cells inside the
# bbox are intentionally meaningful: the canonical matcher treats them as
# wildcards, then paints only these occupied cells into the output.
_TEMPLATE_CELLS = [
    [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)],          # canonical T / post
    [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],          # L / foot
    [(0, 1), (1, 1), (2, 1), (2, 0), (2, 2)],          # fork
    [(0, 0), (0, 1), (1, 1), (2, 1)],                  # hook
    [(0, 0), (1, 0), (1, 1), (1, 2)],                  # low bar
]


def _shape_size(cells: list[tuple[int, int]]) -> tuple[int, int]:
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _paint(grid: list[list[int]], top: int, left: int, cells: list[tuple[int, int]], color: int) -> None:
    for dr, dc in cells:
        grid[top + dr][left + dc] = color


def _crop_nonzero(panel: list[list[int]]) -> list[tuple[int, int]]:
    cells = [(r, c) for r, row in enumerate(panel) for c, v in enumerate(row) if v not in (0, 9)]
    if not cells:
        return []
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return sorted((r - r0, c - c0) for r, c in cells)


def _match_count(board: list[list[int]], cells: list[tuple[int, int]], color: int = 3) -> int:
    if not cells or not board or not board[0]:
        return 0
    h, w = len(board), len(board[0])
    th, tw = _shape_size(cells)
    total = 0
    for r0 in range(0, h - th + 1):
        for c0 in range(0, w - tw + 1):
            if all(board[r0 + dr][c0 + dc] == color for dr, dc in cells):
                total += 1
    return total


def _split_at_divider(grid: list[list[int]]) -> tuple[list[list[int]], list[list[int]]] | None:
    if not grid or not grid[0]:
        return None
    h, w = len(grid), len(grid[0])
    divs = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(divs) != 1:
        return None
    d = divs[0]
    if d == 0 or d == w - 1:
        return None
    return [row[:d] for row in grid], [row[d + 1:] for row in grid]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Check the executable structure the canonical wildcard matcher depends on."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errors: list[str] = []
    panels = _split_at_divider(grid)
    if panels is None:
        return ["expected exactly one interior full-height color-9 divider column"]
    template_panel, board = panels
    if any(v not in (0, 3, 6, 9) for row in grid for v in row):
        errors.append("normal input should contain only 0/3/6/9")
    template = _crop_nonzero(template_panel)
    if len(template) < 3:
        errors.append(f"template must have at least 3 occupied cells, got {len(template)}")
    if template:
        matches = _match_count(board, template, 3)
        min_matches = 3 if difficulty == "hard" else 2
        if matches < min_matches:
            errors.append(f"expected at least {min_matches} board matches, got {matches}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        board_w = ctx.draw_int("board_w", 7, 8)
        target = ctx.draw_int("match_count", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 11)
        board_w = ctx.draw_int("board_w", 9, 12)
        target = ctx.draw_int("match_count", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 6, 10)
        board_w = ctx.draw_int("board_w", 7, 10)
        target = ctx.draw_int("match_count", 2, 4)
    rng = ctx.draw_rng("layout")

    for _outer in range(80):
        shape = list(rng.choice(_TEMPLATE_CELLS))
        th, tw = _shape_size(shape)
        if th > h or tw > board_w:
            continue
        template_panel = full_grid(h, max(3, tw), 0)
        _paint(template_panel, 0, 0, shape, 3)
        board = full_grid(h, board_w, 0)

        # Keep template bboxes disjoint. The canonical examples sometimes put
        # matches fairly close, so a full 1-cell halo over-constrains small
        # boards and can make valid seeds impossible.
        spots = [(r, c) for r in range(0, h - th + 1) for c in range(0, board_w - tw + 1)]
        rng.shuffle(spots)
        reserved: set[tuple[int, int]] = set()
        placed = 0
        min_required = 3 if difficulty == "hard" else 2
        for r0, c0 in spots:
            bbox = {(r, c) for r in range(r0, r0 + th) for c in range(c0, c0 + tw)}
            if bbox & reserved:
                continue
            _paint(board, r0, c0, shape, 3)
            reserved |= bbox
            placed += 1
            if placed >= target:
                break
        if placed < min_required:
            continue

        # Optional color-6 distractors as in the canonical examples.  They are
        # singletons placed away from template-occupied cells so they cannot
        # satisfy a nonzero template position, but they may sit under wildcard
        # cells in unrelated windows.
        if rng.random() < 0.45:
            occupied = {(r, c) for r in range(h) for c in range(board_w) if board[r][c] != 0}
            for _ in range(rng.randint(1, 2)):
                for _try in range(40):
                    r = rng.randrange(h); c = rng.randrange(board_w)
                    if (r, c) not in occupied:
                        board[r][c] = 6
                        occupied.add((r, c))
                        break
        return assemble_vertical_panels([template_panel, board])

    raise ValueError("could not place enough separated template matches")


def _draw_from_degenerate(name, rng):
    h = 7
    shape = _TEMPLATE_CELLS[0]
    if name == "no_matches":
        template_panel = full_grid(h, 3, 0)
        _paint(template_panel, 0, 0, shape, 3)
        return assemble_vertical_panels([template_panel, full_grid(h, 7, 0)])
    if name == "no_template":
        template_panel = full_grid(h, 3, 0)
        board = full_grid(h, 7, 0)
        _paint(board, 2, 2, shape, 3)
        return assemble_vertical_panels([template_panel, board])
    if name == "single_match":
        template_panel = full_grid(h, 3, 0)
        _paint(template_panel, 0, 0, shape, 3)
        board = full_grid(h, 7, 0)
        _paint(board, 2, 2, shape, 3)
        return assemble_vertical_panels([template_panel, board])
    return full_grid(h, 11, 0)
