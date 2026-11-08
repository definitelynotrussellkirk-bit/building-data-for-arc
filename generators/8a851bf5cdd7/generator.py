"""Generator for arc_puzzle_bank_twentyfirst21:H142.

Rule: infer the additions and deletions in panel A -> panel B, then apply that
edit stencil to panel C. Additions use C's color and deletions become 0.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8a851bf5cdd7"
VERSION = "3.1.0"
TASK_ID = "8a851bf5cdd7"
RULE_HASH = "d2ea4a091d55"
SUMMARY = (
    "0-background grid with three equal panels separated by two full-height "
    "color-8 columns. Panel B is panel A after at least one addition and one "
    "deletion. Apply that edit stencil to differently colored panel C: additions "
    "take C's color and deletions become 0. Every generated lesson makes both "
    "operations visibly affect C."
)

INVARIANTS = [
    "three equal rectangular panels are separated by exactly two full color-8 columns",
    "panels A and B use one shared nonzero color and differ by additions and deletions",
    "panel C uses one different nonzero color",
    "at least one addition and one deletion visibly change panel C",
]

# The previous palette/texture declarations were not consumed and included an
# unlabelable no-separator branch. Keep only the one real, finite control axis.
AXES = {
    "variant": {"type": "int", "default": "rng 0..2", "valid": "0..2"},
}

COLORS = (1, 2, 3, 4, 5, 6, 7, 9)


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError("unsupported/unknown override(s): " + ", ".join(sorted(unknown)))


def _panel_width(width: int) -> int | None:
    if width < 5 or (width - 2) % 3:
        return None
    width = (width - 2) // 3
    return width if width >= 1 else None


def _extract_panels(grid, panel_width):
    height = len(grid)
    return [
        [[grid[r][panel * (panel_width + 1) + c] for c in range(panel_width)]
         for r in range(height)]
        for panel in range(3)
    ]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete three-panel teaching contract without raising."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["empty grid"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        return ["grid cells must be exact integer colors 0..9"]

    height = len(grid)
    panel_width = _panel_width(width)
    if panel_width is None:
        return ["width must encode three equal panels plus two separators"]
    expected_separators = [panel_width, 2 * panel_width + 1]
    full_8_columns = [
        c for c in range(width) if all(grid[r][c] == 8 for r in range(height))
    ]
    if full_8_columns != expected_separators:
        return [
            "expected full-color-8 separator columns at "
            f"{expected_separators}; found {full_8_columns}"
        ]
    if any(grid[r][c] == 8 for r in range(height) for c in range(width)
           if c not in expected_separators):
        return ["color 8 is reserved for separator columns"]

    before, after, query = _extract_panels(grid, panel_width)
    palettes = [{cell for row in panel for cell in row if cell != 0}
                for panel in (before, after, query)]
    if len(palettes[0]) != 1 or len(palettes[1]) != 1 or palettes[0] != palettes[1]:
        return ["panels A and B must use one shared nonzero color"]
    if len(palettes[2]) != 1 or palettes[2] == palettes[0]:
        return ["panel C must use one different nonzero color"]

    additions = []
    deletions = []
    for r in range(height):
        for c in range(panel_width):
            a_on = before[r][c] != 0
            b_on = after[r][c] != 0
            if not a_on and b_on:
                additions.append((r, c))
            elif a_on and not b_on:
                deletions.append((r, c))
    if not additions or not deletions:
        return ["A -> B must contain at least one addition and one deletion"]
    if not any(query[r][c] == 0 for r, c in additions):
        return ["the addition branch is not visible on C"]
    if not any(query[r][c] != 0 for r, c in deletions):
        return ["the deletion branch is not visible on C"]
    return []


def _rand_mask(rng, height, width, count):
    cells = [(r, c) for r in range(height) for c in range(width)]
    selected = set(rng.sample(cells, count))
    return [[1 if (r, c) in selected else 0 for c in range(width)]
            for r in range(height)]


def _recolor(mask, color):
    return [[color if value else 0 for value in row] for row in mask]


def _paste_panel(out, panel_index, panel, panel_width):
    left = panel_index * (panel_width + 1)
    for r, row in enumerate(panel):
        for c, value in enumerate(row):
            out[r][left + c] = value


def _variant_counts(area: int, variant: int) -> tuple[int, int, int]:
    """Return distinct A density, edit count, and C density profiles."""
    a_counts = (
        max(2, area // 4),
        max(2, area // 2),
        min(area - 2, max(2, (3 * area) // 4)),
    )
    a_count = min(area - 2, a_counts[variant])
    max_edits = max(1, min(a_count - 1, area - a_count))
    edit_count = min(max_edits, (1, max(1, area // 8), max(1, area // 4))[variant])
    c_count = min(area - 1, (max(1, area // 4), max(1, area // 2), max(1, (3 * area) // 4))[variant])
    return a_count, edit_count, c_count


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    variant = ctx.draw_int_strict("variant", 0, 2)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        panel_h = ctx.draw_int("panel_h", 3, 3)
        panel_w = ctx.draw_int("panel_w", 3, 3)
    elif difficulty == "hard":
        panel_h = ctx.draw_int("panel_h", 4, 6)
        panel_w = ctx.draw_int("panel_w", 4, 6)
    else:
        panel_h = ctx.draw_int("panel_h", 3, 5)
        panel_w = ctx.draw_int("panel_w", 3, 5)

    base_color, query_color = rng.sample(COLORS, 2)
    area = panel_h * panel_w
    a_count, edit_count, c_count = _variant_counts(area, variant)
    before_mask = _rand_mask(rng, panel_h, panel_w, a_count)
    occupied = sorted((r, c) for r in range(panel_h) for c in range(panel_w)
                      if before_mask[r][c])
    empty = sorted((r, c) for r in range(panel_h) for c in range(panel_w)
                   if not before_mask[r][c])
    removals = rng.sample(occupied, edit_count)
    additions = rng.sample(empty, edit_count)

    after_mask = [row[:] for row in before_mask]
    for r, c in removals:
        after_mask[r][c] = 0
    for r, c in additions:
        after_mask[r][c] = 1

    # Make both causal branches observable: a deletion site is occupied in C,
    # while an addition site is empty in C. Fill the remaining requested density
    # without touching those two protected witnesses.
    forced_on = removals[0]
    forced_off = additions[0]
    available = [(r, c) for r in range(panel_h) for c in range(panel_w)
                 if (r, c) not in {forced_on, forced_off}]
    remaining = max(0, min(len(available), c_count - 1))
    query_on = {forced_on, *rng.sample(available, remaining)}
    query_mask = [[1 if (r, c) in query_on else 0 for c in range(panel_w)]
                  for r in range(panel_h)]

    output = full_grid(panel_h, 3 * panel_w + 2, 0)
    for separator in (panel_w, 2 * panel_w + 1):
        for r in range(panel_h):
            output[r][separator] = 8
    _paste_panel(output, 0, _recolor(before_mask, base_color), panel_w)
    _paste_panel(output, 1, _recolor(after_mask, base_color), panel_w)
    _paste_panel(output, 2, _recolor(query_mask, query_color), panel_w)
    errors = self_check(output, difficulty=difficulty)
    if errors:
        raise ValueError("constructed invalid stencil lesson: " + "; ".join(errors))
    return output
