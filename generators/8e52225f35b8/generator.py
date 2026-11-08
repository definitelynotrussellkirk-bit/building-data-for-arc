"""Generator for S18_H4 — close panel motifs, then take a majority mask.

The input is split into three or four equal panels by full-height color-9
separator columns.  Each panel contains four color-2 corner marks.  The
canonical rule closes each motif row-wise and then column-wise, aligns the
completed panels, and paints cyan where at least two completed panels cover a
cell.

Ordinary draws deliberately include both cells covered by every panel and cells
covered by exactly two panels.  The latter prevents the plausible but wrong
"intersection of all panels" shortcut that survived the old two-panel easy
band.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8e52225f35b8"
TASK_ID = GENERATOR_ID
VERSION = "3.2.0"
RULE_HASH = "c6c70b256a40"

SUMMARY = (
    "0-background grid split into 3-4 equal panels by full-height color-9 "
    "divider columns. Each panel contains four color-2 rectangle corners. "
    "Complete every panel by row-then-column closure and output one panel-sized "
    "grid, painting 8 wherever at least two completed rectangles overlap."
)

INVARIANTS = [
    "three or four equal-width panels are separated by one full-height color-9 column",
    "each panel contains exactly four color-2 marks at one rectangle's corners",
    "completed rectangles have a nonempty common overlap and a nonempty exactly-two overlap",
]

DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
AXES = {
    "panel_h": {"type": "int", "default": "difficulty-aware", "valid": "5..14"},
    "panel_w": {"type": "int", "default": "rng 5..6", "valid": "5..6"},
    "n_panels": {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "texture": {
        "type": "str",
        "default": "default",
        "valid": "default|no_motifs|single_motif|all_same_color",
        "probe": "diagnostic",
    },
}


def _profiles(ph: int, pw: int, rng, count: int) -> list[tuple[int, int, int, int]]:
    """Return corner-anchored rectangles sharing a core but retaining 2-way-only cells."""
    core_top = rng.randint(1, max(1, ph // 3))
    core_bottom = rng.randint(max(core_top + 1, (2 * ph) // 3), ph - 2)
    core_left = rng.randint(1, max(1, pw // 3))
    core_right = rng.randint(max(core_left + 1, (2 * pw) // 3), pw - 2)
    candidates = [
        (0, 0, core_bottom, core_right),
        (core_top, 0, ph - 1, core_right),
        (0, core_left, core_bottom, pw - 1),
        (core_top, core_left, ph - 1, pw - 1),
    ]
    rng.shuffle(candidates)
    return candidates[:count]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    texture = overrides.get("texture", "default")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx.draw_rng("degenerate"))
    if texture != "default":
        raise ValueError(f"unknown texture {texture!r}")

    if difficulty == "easy":
        ph = ctx.draw_int("panel_h", 5, 7)
    elif difficulty == "hard":
        ph = ctx.draw_int("panel_h", 10, 14)
    else:
        ph = ctx.draw_int("panel_h", 7, 11)
    pw = ctx.draw_int("panel_w", 5, 6)
    panel_count = ctx.draw_int("n_panels", 3, 4)
    width = panel_count * pw + panel_count - 1
    if width > 30:
        raise ValueError("panel geometry exceeds the 30-column ARC limit")

    rng = ctx.draw_rng("layout")
    rectangles = _profiles(ph, pw, rng, panel_count)
    grid = full_grid(ph, width, 0)
    for panel_index in range(1, panel_count):
        divider = panel_index * (pw + 1) - 1
        for row in range(ph):
            grid[row][divider] = 9
    for panel_index, (r1, c1, r2, c2) in enumerate(rectangles):
        offset = panel_index * (pw + 1)
        for row, col in ((r1, c1), (r1, c2), (r2, c1), (r2, c2)):
            grid[row][offset + col] = 2
    return grid


def _panel_bounds(grid: list[list[int]]) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    separators = [col for col in range(w) if all(grid[row][col] == 9 for row in range(h))]
    separator_set = set(separators)
    panels: list[tuple[int, int]] = []
    groups: list[tuple[int, int]] = []
    col = 0
    while col < w:
        if col in separator_set:
            start = col
            while col < w and col in separator_set:
                col += 1
            groups.append((start, col))
        else:
            start = col
            while col < w and col not in separator_set:
                col += 1
            panels.append((start, col))
    return panels, groups


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the teachable three/four-panel canonical grammar."""
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        return ["grid exceeds the 30x30 ARC limit"]
    if any(type(row) is not list or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        return ["grid must contain exact integer ARC colors 0..9"]

    errors: list[str] = []
    panels, separator_groups = _panel_bounds(grid)
    if len(panels) not in (3, 4):
        errors.append(f"expected three or four panels, found {len(panels)}")
    if len(separator_groups) != max(0, len(panels) - 1):
        errors.append("expected one separator group between each adjacent panel")
    if any(end - start != 1 for start, end in separator_groups):
        errors.append("ordinary generator separators must be exactly one column wide")
    widths = [end - start for start, end in panels]
    if widths and len(set(widths)) != 1:
        errors.append("all panels must have equal width")

    closures: list[set[tuple[int, int]]] = []
    for panel_index, (left, right) in enumerate(panels):
        marks = [
            (row, col - left, grid[row][col])
            for row in range(h)
            for col in range(left, right)
            if grid[row][col] != 0
        ]
        if len(marks) != 4:
            errors.append(f"panel {panel_index} must contain exactly four corner marks")
            continue
        if {color for _, _, color in marks} != {2}:
            errors.append(f"panel {panel_index} marks must all use color 2")
            continue
        rows = [row for row, _, _ in marks]
        cols = [col for _, col, _ in marks]
        r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
        expected = {(r1, c1), (r1, c2), (r2, c1), (r2, c2)}
        actual = {(row, col) for row, col, _ in marks}
        if r1 == r2 or c1 == c2 or actual != expected:
            errors.append(f"panel {panel_index} marks must be four distinct rectangle corners")
            continue
        closures.append({(row, col) for row in range(r1, r2 + 1) for col in range(c1, c2 + 1)})

    counts: dict[tuple[int, int], int] = {}
    for closure in closures:
        for cell in closure:
            counts[cell] = counts.get(cell, 0) + 1
    if closures and not any(value >= 3 for value in counts.values()):
        errors.append("completed panels need a shared three-way overlap")
    if closures and not any(value == 2 for value in counts.values()):
        errors.append("completed panels need cells covered by exactly two panels")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    grid = full_grid(h, w, 0)
    if name == "no_motifs":
        return grid
    if name == "single_motif":
        for row, col in ((2, 2), (2, 3), (3, 2), (3, 3)):
            grid[row][col] = 2
        return grid
    if name == "all_same_color":
        for row, col in ((1, 1), (1, 3), (3, 1), (3, 3), (6, 7), (6, 9), (8, 7), (8, 9)):
            grid[row][col] = 2
        return grid
    raise ValueError(name)
