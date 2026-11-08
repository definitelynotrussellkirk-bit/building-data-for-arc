"""Generate chamber-filling lessons that require parsing cyan walls.

The first three cells of row 0 are a left-to-right priority legend.  Full cyan
walls below the legend divide the canvas into two, three, or four rectangular
chambers.  Each chamber contains one or two legend-colour seeds; the unchanged
Racket authority fills every chamber with its highest-priority present seed.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import product
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e03758508612"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "d93ad16a99ae"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Read the three-colour priority legend at row 0, parse the cyan-wall "
    "chambers below it, and fill each chamber with its highest-priority "
    "present seed colour.  Lessons vary horizontal, vertical, and 2x2 wall "
    "layouts, including unequal partitions that defeat midpoint shortcuts."
)

INVARIANTS = [
    "row 0 columns 0..2 are three distinct non-background, non-cyan legend colours",
    "a closed cyan frame below row 0 contains 2..4 rectangular 4-connected chambers",
    "each chamber contains one or two seeds whose colours occur in the legend",
    "all other chamber cells are background 0",
    "the authoritative output preserves the legend and walls and fills each chamber by legend priority",
]

LAYOUTS = ("horizontal", "vertical", "grid")
SEED_PATTERNS = ("single", "mixed", "double")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "eight-slot canonical-linked schedule",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "eight-slot canonical-linked schedule",
        "valid": "9..17",
    },
    "layout": {
        "type": "enum",
        "default": "eight-slot horizontal/vertical/grid schedule",
        "valid": LAYOUTS,
    },
    "seed_pattern": {
        "type": "enum",
        "default": "eight-slot single/mixed/double schedule",
        "valid": SEED_PATTERNS,
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = tuple(range(8))

_PALETTE = (1, 2, 3, 4, 5, 6, 7, 9)
_CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> int:
    """Expose the deterministic eight-slot curriculum schedule."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _validate_call(
    seed: Any,
    sample_index: Any,
    difficulty: Any,
    overrides: dict[str, Any],
) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be a literal Python integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in ("grid_h", "grid_w"):
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise TypeError(f"{label} must be an integer")
    for label in ("layout", "seed_pattern"):
        value = overrides.get(label)
        if value is not None and type(value) is not str:
            raise TypeError(f"{label} must be a string")


def _draw_exact_int(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_choice(label, (scheduled,))


def _draw_exact_choice(ctx, label: str, options: tuple[str, ...], scheduled: str) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _scheduled_defaults(profile: int, difficulty: Any) -> dict[str, int | str]:
    # Slots 0..3 anchor every imported canonical (height, width, colour-count)
    # profile in every difficulty band.  Slots 4..7 broaden geometry and seed
    # evidence without changing the canonical rule.
    canonical = {
        0: (9, 11, "grid", "mixed"),
        1: (8, 10, "horizontal", "double"),
        2: (10, 12, "vertical", "double"),
        3: (9, 9, "horizontal", "double"),
    }
    if profile in canonical:
        height, width, layout, pattern = canonical[profile]
        return {
            "grid_h": height,
            "grid_w": width,
            "layout": layout,
            "seed_pattern": pattern,
        }

    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    broad = {
        "easy": {
            4: (8, 9, "horizontal", "single"),
            5: (9, 10, "vertical", "mixed"),
            6: (10, 11, "grid", "double"),
            7: (9, 12, "grid", "mixed"),
        },
        "medium": {
            4: (10, 13, "horizontal", "single"),
            5: (11, 14, "vertical", "mixed"),
            6: (12, 15, "grid", "double"),
            7: (11, 16, "grid", "mixed"),
        },
        "hard": {
            4: (12, 15, "horizontal", "single"),
            5: (13, 16, "vertical", "mixed"),
            6: (14, 17, "grid", "double"),
            7: (14, 16, "grid", "mixed"),
        },
    }
    height, width, layout, pattern = broad[band][profile]
    return {
        "grid_h": height,
        "grid_w": width,
        "layout": layout,
        "seed_pattern": pattern,
    }


def _compositions(total: int, parts: int, minimum: int = 2) -> list[tuple[int, ...]]:
    if parts == 1:
        return [(total,)] if total >= minimum else []
    choices: list[tuple[int, ...]] = []
    for first in range(minimum, total - minimum * (parts - 1) + 1):
        for rest in _compositions(total - first, parts - 1, minimum):
            choices.append((first, *rest))
    return choices


def _partition(
    total: int,
    parts: int,
    rng,
    *,
    preferred: tuple[int, ...] | None = None,
    prefer_offset: bool = False,
) -> tuple[int, ...]:
    choices = _compositions(total, parts)
    if not choices:
        raise ValueError(f"cannot split {total} cells into {parts} rooms of size at least 2")
    if preferred in choices:
        return preferred
    if prefer_offset and len(choices) > 1:
        unequal = [choice for choice in choices if len(set(choice)) > 1]
        if unequal:
            choices = unequal
    return rng.choice(choices)


def _room_geometry(
    ctx,
    profile: int,
    height: int,
    width: int,
    layout: str,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if layout == "horizontal":
        row_parts, col_parts = 2, 1
    elif layout == "vertical":
        row_parts = 1
        # The canonical vertical slot has three rooms.  Other vertical cases
        # vary between two and three when the width can support both.
        if profile == 2 and width >= 10:
            col_parts = 3
        elif width >= 10:
            col_parts = ctx.draw_rng("vertical_room_count").choice((2, 3))
        else:
            col_parts = 2
    elif layout == "grid":
        row_parts, col_parts = 2, 2
    else:  # guarded by _validate_call / draw_choice
        raise ValueError(f"unsupported layout: {layout}")

    row_total = height - 1 - (row_parts + 1)
    col_total = width - (col_parts + 1)
    preferred_rows = {
        0: (2, 3),
        1: (2, 2),
        3: (2, 3),
    }.get(profile)
    preferred_cols = {
        0: (4, 4),
        2: (3, 3, 2),
    }.get(profile)
    row_sizes = _partition(
        row_total,
        row_parts,
        ctx.draw_rng("row_partition"),
        preferred=preferred_rows,
        prefer_offset=profile >= 4 and row_parts > 1,
    )
    col_sizes = _partition(
        col_total,
        col_parts,
        ctx.draw_rng("column_partition"),
        preferred=preferred_cols,
        prefer_offset=profile >= 4 and col_parts > 1,
    )
    return row_sizes, col_sizes


def _ranges(start: int, sizes: Iterable[int]) -> tuple[tuple[int, int], ...]:
    spans = []
    cursor = start
    for size in sizes:
        spans.append((cursor, cursor + size - 1))
        cursor += size + 1
    return tuple(spans)


def _wall_lines(start: int, sizes: Iterable[int]) -> tuple[int, ...]:
    lines = [start - 1]
    cursor = start
    for size in sizes:
        cursor += size
        lines.append(cursor)
        cursor += 1
    return tuple(lines)


def _build_partitioned_grid(
    height: int,
    width: int,
    row_sizes: tuple[int, ...],
    col_sizes: tuple[int, ...],
) -> tuple[list[list[int]], list[list[tuple[int, int]]]]:
    grid = full_grid(height, width, 0)
    row_ranges = _ranges(2, row_sizes)
    col_ranges = _ranges(1, col_sizes)
    wall_rows = _wall_lines(2, row_sizes)
    wall_columns = _wall_lines(1, col_sizes)
    for row in wall_rows:
        for column in range(width):
            grid[row][column] = 8
    for column in wall_columns:
        for row in range(1, height):
            grid[row][column] = 8
    rooms = [
        [(row, column) for row in range(r1, r2 + 1) for column in range(c1, c2 + 1)]
        for (r1, r2), (c1, c2) in product(row_ranges, col_ranges)
    ]
    return grid, rooms


def _seed_counts(pattern: str, room_count: int, profile: int) -> tuple[int, ...]:
    if pattern == "single":
        return (1,) * room_count
    if pattern == "double":
        return (2,) * room_count
    # Both counts occur in every mixed scene (all supported layouts have >=2 rooms).
    return tuple(2 if (index + profile) % 2 == 0 else 1 for index in range(room_count))


def _seed_colors(legend: tuple[int, int, int], count: int, index: int, profile: int) -> tuple[int, ...]:
    if count == 1:
        return (legend[(index + profile) % 3],)
    pairs = ((0, 1), (1, 2), (0, 2))
    a, b = pairs[(index + profile) % len(pairs)]
    return legend[a], legend[b]


def _seed_slots(
    cells: list[tuple[int, int]],
    count: int,
    *,
    layout: str,
    room_index: int,
    height: int,
    width: int,
    rng,
) -> list[tuple[int, int]]:
    # Non-grid layouts deliberately place a chamber's seeds on one side of the
    # canvas midpoint.  The true wall-connected fill crosses that midpoint, while
    # the old quadrant shortcut leaves or miscolours the seedless side.
    preferred = cells
    if layout == "horizontal":
        left = room_index % 2 == 0
        preferred = [cell for cell in cells if (cell[1] < width // 2) == left]
    elif layout == "vertical":
        top = room_index % 2 == 0
        preferred = [cell for cell in cells if (cell[0] < height // 2) == top]
    if len(preferred) < count:
        preferred = cells
    return rng.sample(preferred, count)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    defaults = _scheduled_defaults(profile, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_exact_int(ctx, "grid_h", 8, 14, int(defaults["grid_h"]))
    width = _draw_exact_int(ctx, "grid_w", 9, 17, int(defaults["grid_w"]))
    layout = _draw_exact_choice(ctx, "layout", LAYOUTS, str(defaults["layout"]))
    pattern = _draw_exact_choice(
        ctx,
        "seed_pattern",
        SEED_PATTERNS,
        str(defaults["seed_pattern"]),
    )

    row_sizes, col_sizes = _room_geometry(ctx, profile, height, width, layout)
    grid, rooms = _build_partitioned_grid(height, width, row_sizes, col_sizes)
    legend = tuple(ctx.draw_rng("legend").sample(_PALETTE, 3))
    for column, color in enumerate(legend):
        grid[0][column] = color

    counts = _seed_counts(pattern, len(rooms), profile)
    for index, (cells, count) in enumerate(zip(rooms, counts)):
        slots = _seed_slots(
            cells,
            count,
            layout=layout,
            room_index=index,
            height=height,
            width=width,
            rng=ctx.draw_rng(f"room_{index}_slots"),
        )
        colors = _seed_colors(legend, count, index, profile)
        for (row, column), color in zip(slots, colors):
            grid[row][column] = color
    return grid


def _legend_chambers(grid) -> list[list[tuple[int, int]]]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    chambers: list[list[tuple[int, int]]] = []
    for row in range(1, height):
        for column in range(width):
            if grid[row][column] == 8 or (row, column) in seen:
                continue
            stack = [(row, column)]
            seen.add((row, column))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in _CARDINALS:
                    neighbour = (r + dr, c + dc)
                    nr, nc = neighbour
                    if (
                        1 <= nr < height
                        and 0 <= nc < width
                        and neighbour not in seen
                        and grid[nr][nc] != 8
                    ):
                        seen.add(neighbour)
                        stack.append(neighbour)
            chambers.append(sorted(cells))
    return chambers


def _bounds(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (
        min(row for row, _ in cells),
        min(column for _, column in cells),
        max(row for row, _ in cells),
        max(column for _, column in cells),
    )


def _layout_kind(grid) -> str:
    rooms = _legend_chambers(grid)
    bounds = [_bounds(room) for room in rooms]
    row_spans = {(r1, r2) for r1, _, r2, _ in bounds}
    col_spans = {(c1, c2) for _, c1, _, c2 in bounds}
    combinations = {((r1, r2), (c1, c2)) for r1, c1, r2, c2 in bounds}
    if len(rooms) == 2 and len(row_spans) == 2 and len(col_spans) == 1:
        return "horizontal"
    if len(rooms) in (2, 3) and len(row_spans) == 1 and len(col_spans) == len(rooms):
        return "vertical"
    if (
        len(rooms) == 4
        and len(row_spans) == 2
        and len(col_spans) == 2
        and combinations == set(product(row_spans, col_spans))
    ):
        return "grid"
    return "other"


def _seed_pattern(grid) -> str:
    legend = set(grid[0][:3])
    counts = [sum(grid[row][column] in legend for row, column in room) for room in _legend_chambers(grid)]
    if counts and all(count == 1 for count in counts):
        return "single"
    if counts and all(count == 2 for count in counts):
        return "double"
    if counts and set(counts) == {1, 2}:
        return "mixed"
    return "other"


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every advertised control from returned pixels."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "layout": _layout_kind(grid),
        "seed_pattern": _seed_pattern(grid),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colours 0..9"]
    height = len(grid)
    if height < 8 or width < 9:
        return ["grid is too small for the declared chamber family"]

    errors: list[str] = []
    legend = tuple(grid[0][:3])
    if len(set(legend)) != 3 or any(value in (0, 8) for value in legend):
        errors.append(f"legend must be three distinct nonzero/non-8 colours, got {legend}")
    if any(value != 0 for value in grid[0][3:]):
        errors.append("legend row cells after column 2 must be background 0")
    allowed = {0, 8, *legend}
    unexpected = sorted({value for row in grid[1:] for value in row if value not in allowed})
    if unexpected:
        errors.append(f"cells below legend use colours outside background/wall/legend: {unexpected}")
    if any(value != 8 for value in grid[1]) or any(value != 8 for value in grid[-1]):
        errors.append("top and bottom chamber-frame rows must be cyan")
    if any(row[0] != 8 or row[-1] != 8 for row in grid[1:]):
        errors.append("left and right chamber-frame columns must be cyan")

    rooms = _legend_chambers(grid)
    if not 2 <= len(rooms) <= 4:
        errors.append(f"expected 2..4 chambers below legend, got {len(rooms)}")
    for index, room in enumerate(rooms):
        r1, c1, r2, c2 = _bounds(room)
        expected_area = (r2 - r1 + 1) * (c2 - c1 + 1)
        if len(room) != expected_area:
            errors.append(f"chamber {index} is not a solid rectangle")
        if r2 - r1 + 1 < 2 or c2 - c1 + 1 < 2:
            errors.append(f"chamber {index} must be at least 2x2")
        seeds = [(row, column) for row, column in room if grid[row][column] in legend]
        if not 1 <= len(seeds) <= 2:
            errors.append(f"chamber {index} expected 1..2 legend-colour seeds, got {len(seeds)}")
    layout = _layout_kind(grid) if rooms else "other"
    if layout not in LAYOUTS:
        errors.append(f"wall arrangement is not horizontal, vertical, or 2x2 grid: {layout}")
    return errors


def strict_canonical_like(grid):
    """Lawful inputs in the selected rectangular-wall task domain."""
    return self_check(grid)


def rule_mirror(grid, *, reverse: bool = False):
    """Supplementary Python mirror; canonical labels still come from Racket."""
    legend = [value for value in grid[0] if value not in (0, 8)]
    order = list(reversed(legend)) if reverse else legend
    output = deepcopy(grid)
    for room in _legend_chambers(grid):
        present = {grid[row][column] for row, column in room} & set(legend)
        winner = next((color for color in order if color in present), None)
        if winner is None:
            continue
        for row, column in room:
            output[row][column] = winner
    return output


def _midpoint_rival(grid):
    """Rival: ignore cyan connectivity and fill fixed midpoint quadrants."""
    height = len(grid)
    width = len(grid[0])
    legend = [value for value in grid[0] if value not in (0, 8)]
    output = deepcopy(grid)
    groups: dict[tuple[bool, bool], list[tuple[int, int]]] = {}
    for row in range(1, height):
        for column in range(width):
            if grid[row][column] != 8:
                groups.setdefault((row >= height // 2, column >= width // 2), []).append((row, column))
    for cells in groups.values():
        present = {grid[row][column] for row, column in cells} & set(legend)
        winner = next((color for color in legend if color in present), None)
        if winner is None:
            continue
        for row, column in cells:
            output[row][column] = winner
    return output


def _lowest_priority_rival(grid):
    """Rival: parse the rooms correctly but reverse the legend priority."""
    return rule_mirror(grid, reverse=True)


def _wall_parsing_witness(grid) -> bool:
    return _midpoint_rival(grid) != rule_mirror(grid)


def _priority_witness(grid) -> bool:
    return _lowest_priority_rival(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "wall_parsing": _wall_parsing_witness,
    "priority_order": _priority_witness,
}
SEMANTIC_RIVALS = {
    "midpoint_partition": _midpoint_rival,
    "lowest_priority": _lowest_priority_rival,
}
WITNESS_RIVALS = {
    "wall_parsing": ["midpoint_partition"],
    "priority_order": ["lowest_priority"],
}
CANONICAL_SHORTCUTS: dict[str, Any] = {}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query=None):
    """Report declared rivals not contradicted by the supplied demonstrations."""
    del query
    errors = []
    for name, rival in LESSON_COMPETITORS.items():
        if not any(rival(pair["input"]) != pair["output"] for pair in demos):
            errors.append(f"demonstrations do not distinguish rival {name}")
    return errors
