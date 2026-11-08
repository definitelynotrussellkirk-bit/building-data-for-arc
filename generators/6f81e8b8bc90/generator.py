"""Generator for ARC task ``6f81e8b8bc90`` (Green Dot Count Square).

Canonical rule
--------------
Count cells of color 3.  If the count is ``n``, return an ``n x n`` solid
square of color 7.

The canonical examples contain only isolated green cells on black.  That
surface admits several wrong rules: count all nonzero cells, count green
components, count occupied rows/columns, or memorize a fixed output size.
This generator keeps a canonical-like anchor while scheduling colored
non-green distractors and an L-shaped green component so every materialized
lesson refutes those shortcuts.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6f81e8b8bc90"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "48e63841a0da"
EXPECTED_OUTPUT_CODOMAIN = 6  # side lengths 2..7, all exercised in each six-pair lesson

SUMMARY = (
    "Count every color-3 cell, regardless of position or connectivity. If the "
    "count is N, emit an N x N solid color-7 square. Canonical-like draws use "
    "isolated green cells on black; scheduled shortcut-rebuttal draws add one "
    "more-numerous non-green distractor color and connect some green cells in "
    "an L, proving the rule is not nonzero-count, component-count, row-count, "
    "column-count, modal-color, or fixed-size."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

INVARIANTS = [
    "the grid is 5..14 rows by 6..16 columns and color 0 is the unique mode",
    "there are exactly 2..7 cells of color 3",
    "color 7 never appears in the input",
    "the optional distractor uses exactly one non-{0,3,7} color and is more numerous than green",
    "sample_index mod 6 schedules counts 2..7; branches 0 and 1 are canonical-like",
    "branches 2..5 contain an L-shaped green component plus a dominant colored distractor",
]

# Keep the override surface restricted to values recoverable exactly from the
# returned grid.  Every boundary is valid in every difficulty band.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 5..14; canonical schedule pins 5",
        "valid": "5..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 6..16; canonical schedule pins 6 or 7",
        "valid": "6..16",
    },
    "dot_count": {
        "type": "int",
        "default": "sample_index cycle 2..9",
        "valid": "2..7",
    },
}

_CANONICAL_PROFILES = {(5, 6), (5, 7), (6, 7)}
_DISTRACTOR_COLORS = (1, 2, 4, 5, 6, 8, 9)
_NEIGHBORS_4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _validate_grid_shape(grid) -> tuple[int, int, list[str]]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return 0, 0, ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular and non-empty"]
    return len(grid), width, []


def _green_cells(grid) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 3
    ]


def _green_component_count(grid) -> int:
    cells = set(_green_cells(grid))
    components = 0
    while cells:
        components += 1
        start = cells.pop()
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in _NEIGHBORS_4:
                neighbor = (r + dr, c + dc)
                if neighbor in cells:
                    cells.remove(neighbor)
                    queue.append(neighbor)
    return components




def _has_green_l_corner(grid) -> bool:
    cells = set(_green_cells(grid))
    for r, c in cells:
        vertical = any((r + dr, c) in cells for dr in (-1, 1))
        horizontal = any((r, c + dc) in cells for dc in (-1, 1))
        if vertical and horizontal:
            return True
    return False


def _has_solid_green_2x2(grid) -> bool:
    height, width = len(grid), len(grid[0])
    return any(
        all(grid[r + dr][c + dc] == 3 for dr in (0, 1) for dc in (0, 1))
        for r in range(height - 1)
        for c in range(width - 1)
    )

def _isolated_eight_way(cells: list[tuple[int, int]]) -> bool:
    for index, (r, c) in enumerate(cells):
        for rr, cc in cells[index + 1 :]:
            if max(abs(r - rr), abs(c - cc)) <= 1:
                return False
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the lawful teaching grammar, including every canonical input."""
    del difficulty, meta
    height, width, errors = _validate_grid_shape(grid)
    if errors:
        return errors
    if not (5 <= height <= 14):
        errors.append(f"height {height} outside 5..14")
    if not (6 <= width <= 16):
        errors.append(f"width {width} outside 6..16")

    counts: dict[int, int] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append(f"cell ({r},{c}) is not an ARC color: {value!r}")
                continue
            counts[value] = counts.get(value, 0) + 1
    if errors:
        return errors

    green_count = counts.get(3, 0)
    if not (2 <= green_count <= 7):
        errors.append(f"expected 2..7 color-3 cells, found {green_count}")
    if counts.get(7, 0):
        errors.append("input color 7 is forbidden; it leaks the fixed output color")

    distractor_colors = sorted(color for color in counts if color not in (0, 3))
    if len(distractor_colors) > 1:
        errors.append(
            "at most one non-{0,3} distractor color is allowed; found "
            f"{distractor_colors}"
        )
    elif distractor_colors:
        distractor = distractor_colors[0]
        distractor_count = counts[distractor]
        if distractor_count <= green_count:
            errors.append(
                f"distractor color {distractor} must outnumber green "
                f"({distractor_count} <= {green_count}); otherwise the shortcut rebuttal is hidden"
            )

    component_count = _green_component_count(grid)
    if component_count < green_count:
        if green_count >= 3 and not _has_green_l_corner(grid):
            errors.append("three-or-more connected green cells must include an L-corner witness")
        if _has_solid_green_2x2(grid):
            errors.append("solid 2x2 green blocks are outside the teaching grammar")

    background_count = counts.get(0, 0)
    if not counts or background_count <= max(
        (count for color, count in counts.items() if color != 0),
        default=0,
    ):
        errors.append("color 0 must be the unique modal background")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Return [] only for the task's narrow canonical-like input manifold."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    height, width = len(grid), len(grid[0])
    if (height, width) not in _CANONICAL_PROFILES:
        reasons.append(
            f"dimensions {height}x{width} are outside canonical profiles "
            f"{sorted(_CANONICAL_PROFILES)}"
        )
    palette = {value for row in grid for value in row}
    if palette != {0, 3}:
        reasons.append(f"canonical-like palette must be exactly {{0,3}}, found {sorted(palette)}")
    cells = _green_cells(grid)
    if not (2 <= len(cells) <= 4):
        reasons.append(f"canonical-like green count must be 2..4, found {len(cells)}")
    if not _isolated_eight_way(cells):
        reasons.append("canonical-like green cells must be isolated in all eight directions")
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    """Expose all declared exact axes from the returned grid."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "dot_count": sum(value == 3 for row in grid for value in row),
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for tests only; Racket remains authoritative."""
    count = sum(value == 3 for row in grid for value in row)
    if count == 0:
        return [[0]]
    return [[7 for _ in range(count)] for _ in range(count)]


def _place_isolated(height: int, width: int, count: int, rng) -> list[tuple[int, int]]:
    """Choose count cells from a two-step lattice (8-neighbor isolated)."""
    candidate_sets = []
    for row_offset in (0, 1):
        for col_offset in (0, 1):
            candidates = [
                (r, c)
                for r in range(row_offset, height, 2)
                for c in range(col_offset, width, 2)
            ]
            if len(candidates) >= count:
                candidate_sets.append(candidates)
    if not candidate_sets:
        raise ValueError(
            f"cannot place {count} isolated green cells in {height}x{width}"
        )
    candidates = list(rng.choice(candidate_sets))
    rng.shuffle(candidates)
    return candidates[:count]


def _border_l_shape(height: int, width: int, branch: int, rng) -> list[tuple[int, int]]:
    """An L triomino touching a border and containing an interior cell."""
    orientation = branch % 4
    if orientation == 0:  # top
        c = rng.randint(1, width - 2)
        return [(0, c), (0, c + 1), (1, c)]
    if orientation == 1:  # bottom
        c = rng.randint(1, width - 3)
        return [(height - 1, c), (height - 1, c + 1), (height - 2, c + 1)]
    if orientation == 2:  # left
        r = rng.randint(1, height - 2)
        return [(r, 0), (r + 1, 0), (r, 1)]
    r = rng.randint(1, height - 3)  # right
    return [(r, width - 1), (r + 1, width - 1), (r + 1, width - 2)]


def _place_shortcut_rebuttal(
    height: int, width: int, count: int, branch: int, rng
) -> list[tuple[int, int]]:
    cells = _border_l_shape(height, width, branch, rng)[: min(3, count)]
    used = set(cells)
    remaining = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if (r, c) not in used
    ]
    rng.shuffle(remaining)
    needed = count - len(cells)
    for candidate in remaining:
        if needed == 0:
            break
        trial = set(cells) | {candidate}
        r, c = candidate
        completes_block = any(
            all((rr, cc) in trial for rr in (r0, r0 + 1) for cc in (c0, c0 + 1))
            for r0 in (r - 1, r)
            for c0 in (c - 1, c)
            if 0 <= r0 < height - 1 and 0 <= c0 < width - 1
        )
        if completes_block:
            continue
        cells.append(candidate)
        needed -= 1
    if needed:
        raise ValueError(f"cannot place {count} green cells without a solid 2x2")
    return cells


def _default_axis_overrides(sample_index: int) -> dict[str, int]:
    branch = sample_index % 6
    defaults = {"dot_count": 2 + branch}
    # Two consecutive canonical-like branches anchor exact canonical profiles.
    if branch == 0:
        defaults.update(grid_h=5, grid_w=6)
    elif branch == 1:
        defaults.update(grid_h=5, grid_w=7)
    return defaults


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)}")

    effective_overrides = _default_axis_overrides(sample_index)
    effective_overrides.update(overrides)  # explicit caller values always win
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    height = ctx.draw_int_diff("grid_h", 5, 14)
    width = ctx.draw_int_diff("grid_w", 6, 16)
    dot_count = ctx.draw_int("dot_count", 2, 7)
    rng = ctx.draw_rng("layout")
    branch = sample_index % 6

    grid = full_grid(height, width, 0)
    if branch in (0, 1):
        green_cells = _place_isolated(height, width, dot_count, rng)
    else:
        green_cells = _place_shortcut_rebuttal(
            height, width, dot_count, branch, rng
        )
    for r, c in green_cells:
        grid[r][c] = 3

    if branch >= 2:
        distractor_color = rng.choice(_DISTRACTOR_COLORS)
        distractor_count = dot_count + 1
        available = [
            (r, c)
            for r in range(height)
            for c in range(width)
            if grid[r][c] == 0
        ]
        rng.shuffle(available)
        if len(available) < distractor_count:
            raise ValueError(
                f"cannot place {distractor_count} distractors in {height}x{width}"
            )
        for r, c in available[:distractor_count]:
            grid[r][c] = distractor_color

    errors = self_check(grid)
    if errors:
        raise ValueError("generated grid failed self_check: " + "; ".join(errors))
    return grid


# ---------------------------------------------------------------------------
# Task-linked semantic witnesses and lesson identifiability
# ---------------------------------------------------------------------------


def _witness_canonical_anchor(grid) -> bool:
    return strict_canonical_like(grid) == []


def _witness_adjacent_green_cells(grid) -> bool:
    green_count = len(_green_cells(grid))
    return green_count > 0 and _green_component_count(grid) < green_count


def _witness_same_green_row(grid) -> bool:
    return any(sum(value == 3 for value in row) >= 2 for row in grid)


def _witness_same_green_column(grid) -> bool:
    return any(
        sum(grid[r][c] == 3 for r in range(len(grid))) >= 2
        for c in range(len(grid[0]))
    )


def _witness_distractor_dominates_green(grid) -> bool:
    counts: dict[int, int] = {}
    for row in grid:
        for value in row:
            counts[value] = counts.get(value, 0) + 1
    green = counts.get(3, 0)
    return any(
        color not in (0, 3, 7) and count > green
        for color, count in counts.items()
    )


def _witness_border_and_interior_green(grid) -> bool:
    height, width = len(grid), len(grid[0])
    cells = _green_cells(grid)
    border = any(r in (0, height - 1) or c in (0, width - 1) for r, c in cells)
    interior = any(0 < r < height - 1 and 0 < c < width - 1 for r, c in cells)
    return border and interior


SEMANTIC_WITNESSES = {
    "canonical_isolated_anchor": _witness_canonical_anchor,
    "adjacent_green_component_rebuttal": _witness_adjacent_green_cells,
    "multiple_green_cells_same_row": _witness_same_green_row,
    "multiple_green_cells_same_column": _witness_same_green_column,
    "dominant_non_green_distractor": _witness_distractor_dominates_green,
    "green_positions_span_border_and_interior": _witness_border_and_interior_green,
}


def _square(side: int) -> list[list[int]]:
    if side <= 0:
        return [[0]]
    return [[7 for _ in range(side)] for _ in range(side)]


def _competitor_count_all_nonzero(grid):
    return _square(sum(value != 0 for row in grid for value in row))


def _competitor_count_green_components(grid):
    return _square(_green_component_count(grid))


def _competitor_count_green_rows(grid):
    return _square(sum(any(value == 3 for value in row) for row in grid))


def _competitor_count_green_columns(grid):
    return _square(
        sum(
            any(grid[r][c] == 3 for r in range(len(grid)))
            for c in range(len(grid[0]))
        )
    )


_LESSON_COMPETITORS = {
    "count every nonzero cell": _competitor_count_all_nonzero,
    "count 4-connected green components": _competitor_count_green_components,
    "count rows containing green": _competitor_count_green_rows,
    "count columns containing green": _competitor_count_green_columns,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named shortcut fits all demos but changes query."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        expected = rule_mirror(demo["input"])
        if expected != demo["output"]:
            reasons.append(
                f"demo {index} output does not match the count-color-3 rule"
            )
    query_answer = rule_mirror(query["input"])
    if query.get("output") is not None and query["output"] != query_answer:
        reasons.append("query output does not match the count-color-3 rule")

    for name, competitor in _LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo["output"] for demo in demos
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule '{name}' fits every demo but answers the query differently"
            )

    demo_sides = {
        len(demo["output"])
        for demo in demos
        if demo.get("output") and isinstance(demo["output"], list)
    }
    if len(demo_sides) == 1:
        fixed_side = next(iter(demo_sides))
        if _square(fixed_side) != query_answer:
            reasons.append(
                f"fixed {fixed_side}x{fixed_side} output-size shortcut fits every demo"
            )
    return reasons
