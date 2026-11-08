"""Canonical-like sampler for row-wise right gravity between color-8 walls.

The Racket authority scans each row independently.  Every color-8 cell is a
fixed wall; each maximal run of non-wall cells is a segment.  Nonzero values in
a segment keep their left-to-right order and are packed against that segment's
right edge.  This module produces inputs only; :func:`rule_mirror` is an
independent Python oracle used by tests and semantic rivals.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d185ceed5cc1"
TASK_ID = GENERATOR_ID
RULE_HASH = "a1ebff603893"
VERSION = "3.0.0"
SUMMARY = (
    "Rows contain independently placed color-8 walls and ordered colored "
    "pebbles.  Within every maximal non-wall segment, the canonical rule "
    "packs pebbles rightward while preserving their left-to-right order."
)

INVARIANTS = [
    "input profiles stay within the canonical 4..6 by 10..13 envelope",
    "every input uses all colors 0..9; color 8 is the wall and 0 is empty",
    "each row has the requested wall and pebble counts",
    "at least two rows have different wall signatures",
    "every input refutes ignore-walls, sort-before-packing, and bounded-only rivals",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted 4..6",
        "valid": "4..6",
        "doc": "Full input-grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted 10..13",
        "valid": "10..13",
        "doc": "Full input-grid width.",
    },
    "walls_per_row": {
        "type": "int",
        "default": "difficulty-weighted 2..4",
        "valid": "2..4",
        "doc": "Exact number of color-8 walls in every row.",
    },
    "pebbles_per_row": {
        "type": "int",
        "default": "difficulty-weighted 2..4",
        "valid": "2..4",
        "doc": "Exact number of colored pebbles in every row.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_PEBBLE_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_DIFFICULTY_OPTIONS = {
    "easy": {
        "grid_h": (4, 4, 4, 5, 5, 6),
        "grid_w": (10, 10, 11, 11, 12, 13),
        "walls_per_row": (2, 2, 2, 3, 3, 4),
        "pebbles_per_row": (2, 2, 2, 3, 3, 4),
    },
    "medium": {
        "grid_h": (4, 5, 5, 5, 6),
        "grid_w": (10, 11, 11, 12, 12, 13),
        "walls_per_row": (2, 2, 3, 3, 4),
        "pebbles_per_row": (2, 3, 3, 3, 4),
    },
    "hard": {
        "grid_h": (4, 5, 6, 6, 6),
        "grid_w": (10, 11, 12, 13, 13, 13),
        "walls_per_row": (2, 3, 3, 4, 4),
        "pebbles_per_row": (2, 3, 3, 4, 4),
    },
}
_FULL_OPTIONS = {
    "grid_h": (4, 5, 6),
    "grid_w": (10, 11, 12, 13),
    "walls_per_row": (2, 3, 4),
    "pebbles_per_row": (2, 3, 4),
}


def _segments(width: int, walls: tuple[int, ...] | set[int]) -> list[tuple[int, ...]]:
    """Return maximal non-wall column runs, including open edge segments."""
    result: list[tuple[int, ...]] = []
    start = 0
    for wall in sorted(walls):
        if start < wall:
            result.append(tuple(range(start, wall)))
        start = wall + 1
    if start < width:
        result.append(tuple(range(start, width)))
    return result


@lru_cache(maxsize=None)
def _pattern_families(width: int, wall_count: int):
    """Finite constructive wall layouts for the three teaching obligations."""
    general = []
    locality = []
    edge = []
    for walls in combinations(range(width), wall_count):
        segments = _segments(width, walls)
        if max((len(segment) for segment in segments), default=0) < 3:
            continue
        general.append(walls)
        if sum(len(segment) >= 2 for segment in segments) >= 2:
            locality.append(walls)
        if (
            0 not in walls
            and width - 1 not in walls
            and (len(segments[0]) >= 3 or len(segments[-1]) >= 3)
        ):
            edge.append(walls)
    if not general or not locality or not edge:
        raise ValueError(
            f"no constructive wall patterns for width={width}, walls={wall_count}"
        )
    return tuple(general), tuple(locality), tuple(edge)


def _pick_distinct(options, used, rng):
    available = [option for option in options if option not in used]
    return rng.choice(available or list(options))


def _wall_rows(ctx, height: int, width: int, wall_count: int):
    general, locality, edge = _pattern_families(width, wall_count)
    rows: list[tuple[int, ...]] = []
    rows.append(_pick_distinct(general, rows, ctx.draw_rng("walls_order_row")))
    rows.append(_pick_distinct(locality, rows, ctx.draw_rng("walls_locality_row")))
    rows.append(_pick_distinct(edge, rows, ctx.draw_rng("walls_edge_row")))
    for row_index in range(3, height):
        rows.append(
            _pick_distinct(
                general,
                rows[-2:],
                ctx.draw_rng(f"walls_row_{row_index}"),
            )
        )
    return rows


def _complete_positions(
    width: int,
    walls: tuple[int, ...],
    primary: list[int],
    count: int,
    rng,
) -> list[int]:
    positions = list(primary)
    candidates = [
        column
        for column in range(width)
        if column not in walls and column not in positions
    ]
    rng.shuffle(candidates)
    positions.extend(candidates[: count - len(positions)])
    if len(positions) != count:
        raise RuntimeError("constructive placement could not realize pebble count")
    return positions


def _pebble_positions(ctx, wall_rows, width: int, pebble_count: int):
    all_positions: list[list[int]] = []
    for row_index, walls in enumerate(wall_rows):
        segments = _segments(width, walls)
        rng = ctx.draw_rng(f"pebbles_row_{row_index}")
        if row_index == 0:
            # Two adjacent values, with an empty cell to their right, make
            # left-to-right order observable against a sort-then-pack rival.
            longest = max(segments, key=lambda segment: (len(segment), -segment[0]))
            primary = [longest[0], longest[1]]
        elif row_index == 1:
            # Pebbles in separated segments make crossing an 8-wall visibly wrong.
            eligible = [segment for segment in segments if len(segment) >= 2]
            primary = [eligible[0][0], eligible[-1][0]]
        elif row_index == 2:
            # A moving pebble in an open edge segment refutes a rule that only
            # processes intervals bounded by an 8 on both sides.
            edge_segments = [
                segment
                for segment in (segments[0], segments[-1])
                if len(segment) >= 3
                and (segment[0] == 0 or segment[-1] == width - 1)
            ]
            primary = [rng.choice(edge_segments)[0]]
        else:
            longest = max(segments, key=lambda segment: (len(segment), -segment[0]))
            primary = [longest[0]]
        all_positions.append(
            _complete_positions(width, walls, primary, pebble_count, rng)
        )
    return all_positions


def _color_stream(ctx, total: int) -> list[int]:
    rng = ctx.draw_rng("pebble_colors")
    first_cycle = list(_PEBBLE_COLORS)
    rng.shuffle(first_cycle)
    # The first two cells are the row-0 adjacent teaching pair.  Force a
    # descending pair so sorting changes the authoritative result.
    if first_cycle[0] < first_cycle[1]:
        first_cycle[0], first_cycle[1] = first_cycle[1], first_cycle[0]
    stream = list(first_cycle)
    cycle_index = 1
    while len(stream) < total:
        cycle = list(_PEBBLE_COLORS)
        ctx.draw_rng(f"pebble_colors_cycle_{cycle_index}").shuffle(cycle)
        stream.extend(cycle)
        cycle_index += 1
    return stream[:total]


def _draw_axis(ctx, name: str):
    options = _DIFFICULTY_OPTIONS.get(ctx.difficulty, _FULL_OPTIONS)[name]
    return ctx.draw_choice(name, options)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer (not {type(seed).__name__})")
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be an integer (not {type(sample_index).__name__})"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )

    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not {type(value).__name__})")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_axis(ctx, "grid_h")
    width = _draw_axis(ctx, "grid_w")
    wall_count = _draw_axis(ctx, "walls_per_row")
    pebble_count = _draw_axis(ctx, "pebbles_per_row")

    wall_rows = _wall_rows(ctx, height, width, wall_count)
    positions = _pebble_positions(ctx, wall_rows, width, pebble_count)
    colors = _color_stream(ctx, height * pebble_count)

    grid = full_grid(height, width, 0)
    color_index = 0
    for row_index, walls in enumerate(wall_rows):
        for column in walls:
            grid[row_index][column] = 8
        for column in positions[row_index]:
            grid[row_index][column] = colors[color_index]
            color_index += 1
    return grid


def observe_overrides(grid):
    """Recover every exact axis from pixels, independent of draw bookkeeping."""
    height = len(grid)
    width = len(grid[0])
    wall_counts = {sum(value == 8 for value in row) for row in grid}
    pebble_counts = {
        sum(value not in (0, 8) for value in row)
        for row in grid
    }
    return {
        "grid_h": height,
        "grid_w": width,
        "walls_per_row": next(iter(wall_counts)) if len(wall_counts) == 1 else -1,
        "pebbles_per_row": (
            next(iter(pebble_counts)) if len(pebble_counts) == 1 else -1
        ),
    }


def rule_mirror(grid):
    """Independent Python mirror of the pinned Racket row-segment rule."""
    output: list[list[int]] = []
    for source in grid:
        row = [0] * len(source)
        column = 0
        while column < len(source):
            if source[column] == 8:
                row[column] = 8
                column += 1
                continue
            end = column
            while end < len(source) and source[end] != 8:
                end += 1
            values = [value for value in source[column:end] if value != 0]
            start = end - len(values)
            for offset, value in enumerate(values):
                row[start + offset] = value
            column = end
        output.append(row)
    return output


def _segment_pebble_counts(row):
    counts = []
    column = 0
    while column < len(row):
        if row[column] == 8:
            column += 1
            continue
        end = column
        while end < len(row) and row[end] != 8:
            end += 1
        counts.append(sum(value != 0 for value in row[column:end]))
        column = end
    return counts


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    height = len(grid)
    errors: list[str] = []
    if not 4 <= height <= 6:
        errors.append(f"height {height} outside canonical envelope 4..6")
    if not 10 <= width <= 13:
        errors.append(f"width {width} outside canonical envelope 10..13")

    palette = {value for row in grid for value in row}
    if palette != set(range(10)):
        errors.append(f"expected full canonical palette 0..9, got {sorted(palette)}")

    wall_signatures = []
    for row_index, row in enumerate(grid):
        walls = tuple(column for column, value in enumerate(row) if value == 8)
        wall_signatures.append(walls)
        if not 2 <= len(walls) <= 5:
            errors.append(f"row {row_index} has {len(walls)} walls; expected 2..5")
        pebbles = sum(value not in (0, 8) for value in row)
        if pebbles < 1:
            errors.append(f"row {row_index} has no pebble")
    if len(set(wall_signatures)) < 2:
        errors.append("all rows share one wall signature; row-local walls are untested")

    if not any(
        count >= 2
        for row in grid
        for count in _segment_pebble_counts(row)
    ):
        errors.append("no segment contains two ordered pebbles")
    if not errors and rule_mirror(grid) == [list(row) for row in grid]:
        errors.append("right gravity is a no-op")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _ignore_walls(grid):
    """Wrong rival: pack each whole row across walls into rightmost free cells."""
    output = []
    for source in grid:
        row = [8 if value == 8 else 0 for value in source]
        values = [value for value in source if value not in (0, 8)]
        destinations = [index for index, value in enumerate(source) if value != 8]
        for index, value in zip(destinations[-len(values):], values):
            row[index] = value
        output.append(row)
    return output


def _sort_then_pack(grid):
    """Wrong rival: sort colors inside each segment before right-packing."""
    output = []
    for source in grid:
        row = [0] * len(source)
        column = 0
        while column < len(source):
            if source[column] == 8:
                row[column] = 8
                column += 1
                continue
            end = column
            while end < len(source) and source[end] != 8:
                end += 1
            values = sorted(value for value in source[column:end] if value != 0)
            for offset, value in enumerate(values):
                row[end - len(values) + offset] = value
            column = end
        output.append(row)
    return output


def _bounded_segments_only(grid):
    """Wrong rival: leave open leading/trailing segments unchanged."""
    output = []
    for source in grid:
        row = list(source)
        walls = [index for index, value in enumerate(source) if value == 8]
        for left, right in zip(walls, walls[1:]):
            values = [value for value in source[left + 1:right] if value != 0]
            row[left + 1:right] = [0] * (right - left - 1)
            row[right - len(values):right] = values
        output.append(row)
    return output


SEMANTIC_RIVALS = {
    "ignore_walls": _ignore_walls,
    "sort_then_pack": _sort_then_pack,
    "bounded_segments_only": _bounded_segments_only,
}
SEMANTIC_WITNESSES = {
    "segment_locality": lambda grid: _ignore_walls(grid) != rule_mirror(grid),
    "order_preservation": lambda grid: _sort_then_pack(grid) != rule_mirror(grid),
    "edge_segments": lambda grid: _bounded_segments_only(grid) != rule_mirror(grid),
}
WITNESS_RIVALS = {
    "segment_locality": ["ignore_walls"],
    "order_preservation": ["sort_then_pack"],
    "edge_segments": ["bounded_segments_only"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
