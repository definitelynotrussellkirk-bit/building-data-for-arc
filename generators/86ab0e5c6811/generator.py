"""Generate lessons for copying a red object by the green-to-yellow vector.

The unique green (3) and yellow (4) markers define a translation.  The
canonical Racket rule keeps the input and paints cyan (8) at translated red
(2) cells whose destinations are in bounds and currently one of {0, 3, 4}.
This generator keeps marker destinations clear, but deliberately varies vector
quadrant, partial clipping, and a non-cyan blocking decoration.
"""
from __future__ import annotations

from collections import deque
from itertools import combinations
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "86ab0e5c6811"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "0b37a0a27f79"

SUMMARY = (
    "Translate the connected red object by the exact vector from the unique "
    "green marker to the unique yellow marker; paint eligible destinations "
    "cyan, clipping out-of-bounds cells and preserving occupied blockers."
)

INVARIANTS = [
    "exactly one green(3) marker and one yellow(4) marker define a non-zero vector",
    "the red(2) source is one 4-connected component with 3-6 cells",
    "at least one translated red cell lands on a blank in-bounds destination",
    "translated destinations never overlap the source or either marker",
    "exactly one decoration color from 5-9 is present, with a distractor outside the destination footprint",
    "ordinary lessons schedule every vector quadrant and both clipping/blocker branches",
]

DECORATION_COLORS = (5, 6, 7, 8, 9)
ROW_SIGNS = ("down", "up")
COL_SIGNS = ("right", "left")
CLIPPING_MODES = ("none", "partial")

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 8..12", "valid": "8..12"},
    "grid_w": {"type": "int", "default": "difficulty-aware 10..14", "valid": "10..14"},
    "blob_size": {"type": "int", "default": "difficulty-aware 3..6", "valid": "3..6"},
    "delta_row_sign": {"type": "str", "default": "scheduled", "valid": "down|up"},
    "delta_col_sign": {"type": "str", "default": "scheduled", "valid": "right|left"},
    "delta_row_abs": {"type": "int", "default": "difficulty-aware 2..4", "valid": "2..4"},
    "delta_col_abs": {"type": "int", "default": "difficulty-aware 2..5", "valid": "2..5"},
    "clipping": {"type": "str", "default": "scheduled", "valid": "none|partial"},
    "blocked_destination": {"type": "bool", "default": "scheduled", "valid": "false|true"},
    "decoration_color": {"type": "color", "default": "scheduled 5..9", "valid": "5..9"},
}

# Painting an already-cyan blocker is observationally identical to ignoring the
# blocker, so that exact pair would hide the branch rather than teach it.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"blocked_destination": True, "decoration_color": 8},
]

EXAMPLES_NEEDED = 4
SCHEDULE_PROFILES = (0, 1, 2, 3)
MIN_STRICT_FRAC = 1.0

_ALLOWED_DESTINATION_COLORS = {0, 3, 4}
_ALLOWED_INPUT_COLORS = set(range(10))
_SPECIAL_COLORS = {0, 2, 3, 4}


def schedule_profile(seed, sample_index, difficulty=None):
    """Four consecutive samples cover all vector quadrants and both branches."""
    del seed, difficulty
    return int(sample_index) % 4


def _scheduled_choice(ctx, label: str, options: tuple[Any, ...], scheduled: Any):
    """Record a deterministic curriculum schedule while preserving overrides."""
    draw_options = options if label in ctx.overrides else (scheduled,)
    return ctx.draw_choice(label, draw_options)


def _neighbors4(cell: tuple[int, int]) -> Iterable[tuple[int, int]]:
    row, column = cell
    yield row - 1, column
    yield row + 1, column
    yield row, column - 1
    yield row, column + 1


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    min_row = min(row for row, _ in cells)
    min_column = min(column for _, column in cells)
    return tuple(sorted((row - min_row, column - min_column) for row, column in cells))


def _compact_shapes(size: int) -> list[tuple[tuple[int, int], ...]]:
    """Enumerate every normalized connected size-``size`` subset of 3x3."""
    shapes = set()
    cells = tuple((row, column) for row in range(3) for column in range(3))
    for subset in combinations(cells, size):
        subset_set = set(subset)
        if _is_connected(subset_set):
            shapes.add(_normalize(subset))
    return sorted(shapes)


def _is_connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        cell = queue.popleft()
        for neighbor in _neighbors4(cell):
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen == cells


def _marker_delta(grid: list[list[int]]) -> tuple[int, int]:
    threes = [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == 3
    ]
    fours = [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == 4
    ]
    if len(threes) != 1 or len(fours) != 1:
        raise ValueError("grid must contain exactly one 3-marker and one 4-marker")
    return fours[0][0] - threes[0][0], fours[0][1] - threes[0][1]


def _translated_positions(
    grid: list[list[int]], dr: int, dc: int
) -> list[tuple[int, int, bool]]:
    h, w = len(grid), len(grid[0])
    translated = []
    for row, values in enumerate(grid):
        for column, value in enumerate(values):
            if value != 2:
                continue
            nr, nc = row + dr, column + dc
            translated.append((nr, nc, 0 <= nr < h and 0 <= nc < w))
    return translated


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, no-op, and rule-hiding lesson inputs."""
    del difficulty, meta
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["empty or non-grid input"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["ragged grid"]
    if not (1 <= h <= 30 and 1 <= w <= 30):
        errors.append(f"grid dimensions {h}x{w} outside ARC bounds")
    if any(value not in _ALLOWED_INPUT_COLORS for row in grid for value in row):
        errors.append("grid contains a non-integer or color outside 0..9")
        return errors

    threes = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    fours = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4]
    if len(threes) != 1:
        errors.append(f"expected exactly 1 green(3) marker; found {len(threes)}")
    if len(fours) != 1:
        errors.append(f"expected exactly 1 yellow(4) marker; found {len(fours)}")
    if errors:
        return errors

    dr = fours[0][0] - threes[0][0]
    dc = fours[0][1] - threes[0][1]
    if dr == 0 and dc == 0:
        errors.append("marker vector must be non-zero")

    red = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2}
    if not (3 <= len(red) <= 8):
        errors.append(f"red source must have 3-8 cells; found {len(red)}")
    elif not _is_connected(red):
        errors.append("red source must be one 4-connected component")

    decoration_colors = sorted(
        {value for row in grid for value in row if value not in _SPECIAL_COLORS}
    )
    if len(decoration_colors) != 1:
        errors.append(
            "expected exactly one decoration color outside {0,2,3,4}; "
            f"found {decoration_colors}"
        )
        return errors
    decoration_color = decoration_colors[0]
    decoration = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == decoration_color
    }
    if not (1 <= len(decoration) <= 4):
        errors.append(f"decoration must have 1-4 cells; found {len(decoration)}")

    translated = _translated_positions(grid, dr, dc)
    in_bounds = {(r, c) for r, c, inside in translated if inside}
    out_of_bounds = [(r, c) for r, c, inside in translated if not inside]
    del out_of_bounds  # presence is observed by the clipping axis, not required here.

    source_overlap = sorted(in_bounds & red)
    if source_overlap:
        errors.append(f"translated source overlaps red cells at {source_overlap[:3]}")
    marker_overlap = sorted(in_bounds & {threes[0], fours[0]})
    if marker_overlap:
        errors.append(f"translated destination overlaps a marker at {marker_overlap[:3]}")

    blocked = {
        (r, c)
        for r, c in in_bounds
        if grid[r][c] not in _ALLOWED_DESTINATION_COLORS
    }
    if len(blocked) > 1:
        errors.append(f"at most one translated destination may be blocked; found {len(blocked)}")
    unexpected_blockers = sorted(blocked - decoration)
    if unexpected_blockers:
        errors.append(f"translated blockers must use the decoration color: {unexpected_blockers[:3]}")

    eligible = {
        (r, c)
        for r, c in in_bounds
        if grid[r][c] in _ALLOWED_DESTINATION_COLORS
    }
    if not eligible:
        errors.append("no translated red cell reaches an eligible in-bounds destination")

    distractors = decoration - in_bounds
    if not distractors:
        errors.append("decoration must include a distractor outside the translated footprint")
    if blocked and decoration_color == 8:
        errors.append("cyan(8) cannot serve as a blocker because overwrite-vs-skip is unobservable")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The task-linked canonical manifold is exactly the structural grammar."""
    return self_check(grid)


def _position_candidates(
    h: int,
    w: int,
    shape: tuple[tuple[int, int], ...],
    dr: int,
    dc: int,
    clipping: str,
    min_in_bounds: int,
) -> list[tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]]:
    shape_h = max(row for row, _ in shape) + 1
    shape_w = max(column for _, column in shape) + 1
    candidates = []
    for top in range(h - shape_h + 1):
        for left in range(w - shape_w + 1):
            source = tuple((top + row, left + column) for row, column in shape)
            source_set = set(source)
            destinations = tuple((row + dr, column + dc) for row, column in source)
            in_bounds = tuple(
                (row, column)
                for row, column in destinations
                if 0 <= row < h and 0 <= column < w
            )
            if set(in_bounds) & source_set:
                continue
            if clipping == "none" and len(in_bounds) != len(source):
                continue
            if clipping == "partial" and not (min_in_bounds <= len(in_bounds) < len(source)):
                continue
            candidates.append((source, in_bounds))
    return candidates


def _marker_candidates(
    h: int,
    w: int,
    dr: int,
    dc: int,
    forbidden: set[tuple[int, int]],
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    candidates = []
    for row in range(h):
        for column in range(w):
            yellow = (row + dr, column + dc)
            if not (0 <= yellow[0] < h and 0 <= yellow[1] < w):
                continue
            green = (row, column)
            if green in forbidden or yellow in forbidden:
                continue
            candidates.append((green, yellow))
    return candidates


def _choose_scene_layout(h, w, shape, dr, dc, clipping, min_in_bounds, rng):
    layouts = _position_candidates(h, w, shape, dr, dc, clipping, min_in_bounds)
    rng.shuffle(layouts)
    for source, in_bounds in layouts:
        forbidden = set(source) | set(in_bounds)
        markers = _marker_candidates(h, w, dr, dc, forbidden)
        if markers:
            return source, in_bounds, rng.choice(markers)
    raise ValueError(
        "no layout satisfies grid_h, grid_w, blob_size, marker vector, and clipping"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    requested_blocked = overrides.get("blocked_destination")
    requested_decoration = overrides.get("decoration_color")
    if requested_blocked is True and int(requested_decoration or -1) == 8:
        raise ValueError(
            "blocked_destination=True is incompatible with decoration_color=8"
        )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int("grid_h", 8, 12)
    w = ctx.draw_int("grid_w", 10, 14)
    blob_size = ctx.draw_int_diff("blob_size", 3, 6)

    profile = schedule_profile(seed, sample_index, difficulty)
    scheduled_row_sign = "down" if profile in (0, 1) else "up"
    scheduled_col_sign = "right" if profile in (0, 2) else "left"
    scheduled_clipping = "none" if profile in (0, 1) else "partial"
    scheduled_blocked = profile in (1, 3)

    row_sign = _scheduled_choice(ctx, "delta_row_sign", ROW_SIGNS, scheduled_row_sign)
    col_sign = _scheduled_choice(ctx, "delta_col_sign", COL_SIGNS, scheduled_col_sign)
    row_abs = ctx.draw_int_diff("delta_row_abs", 2, 4)
    col_abs = ctx.draw_int_diff("delta_col_abs", 2, 5)
    clipping = _scheduled_choice(ctx, "clipping", CLIPPING_MODES, scheduled_clipping)

    scheduled_decoration = DECORATION_COLORS[int(sample_index) % len(DECORATION_COLORS)]
    decoration_options = DECORATION_COLORS
    if requested_blocked is True or (requested_blocked is None and scheduled_blocked):
        decoration_options = tuple(color for color in DECORATION_COLORS if color != 8)
        if requested_decoration == 8:
            # A single exact decoration override must remain satisfiable; make
            # the unrequested blocker branch false rather than hiding it.
            scheduled_blocked = False
            decoration_options = DECORATION_COLORS
    decoration_color = _scheduled_choice(
        ctx, "decoration_color", decoration_options, scheduled_decoration
        if scheduled_decoration in decoration_options else decoration_options[0]
    )
    if requested_blocked is None and decoration_color == 8:
        scheduled_blocked = False
    blocked = _scheduled_choice(
        ctx, "blocked_destination", (False, True), scheduled_blocked
    )
    if blocked and decoration_color == 8:
        raise ValueError(
            "blocked_destination=True is incompatible with decoration_color=8"
        )

    dr = row_abs if row_sign == "down" else -row_abs
    dc = col_abs if col_sign == "right" else -col_abs
    shape_rng = ctx.draw_rng("shape")
    shapes = _compact_shapes(blob_size)
    shape_rng.shuffle(shapes)
    layout_rng = ctx.draw_rng("layout")
    layout = None
    for shape in shapes:
        try:
            layout = _choose_scene_layout(
                h, w, shape, dr, dc, clipping, 2 if blocked else 1, layout_rng
            )
            break
        except ValueError:
            continue
    if layout is None:
        raise ValueError(
            "no compact shape/layout satisfies the requested axes"
        )
    source, in_bounds, (green, yellow) = layout

    grid = full_grid(h, w, 0)
    for row, column in source:
        grid[row][column] = 2
    grid[green[0]][green[1]] = 3
    grid[yellow[0]][yellow[1]] = 4

    destination_set = set(in_bounds)
    if blocked:
        block_cell = layout_rng.choice(sorted(destination_set))
        grid[block_cell[0]][block_cell[1]] = decoration_color

    forbidden = set(source) | destination_set | {green, yellow}
    distractor_candidates = [
        (row, column)
        for row in range(h)
        for column in range(w)
        if (row, column) not in forbidden
    ]
    if not distractor_candidates:
        raise ValueError("no cell available for a decoration distractor")
    layout_rng.shuffle(distractor_candidates)
    distractor_count = 1 + int(layout_rng.random() < 0.35)
    for row, column in distractor_candidates[:distractor_count]:
        grid[row][column] = decoration_color

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    return grid


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact axis from the returned input grid."""
    h, w = len(grid), len(grid[0])
    dr, dc = _marker_delta(grid)
    translated = _translated_positions(grid, dr, dc)
    in_bounds = [(row, column) for row, column, inside in translated if inside]
    decoration_colors = sorted(
        {value for row in grid for value in row if value not in _SPECIAL_COLORS}
    )
    decoration_color = decoration_colors[0] if len(decoration_colors) == 1 else None
    blocked = any(grid[row][column] not in _ALLOWED_DESTINATION_COLORS for row, column in in_bounds)
    return {
        "grid_h": h,
        "grid_w": w,
        "blob_size": sum(value == 2 for row in grid for value in row),
        "delta_row_sign": "down" if dr > 0 else "up",
        "delta_col_sign": "right" if dc > 0 else "left",
        "delta_row_abs": abs(dr),
        "delta_col_abs": abs(dc),
        "clipping": "partial" if len(in_bounds) < sum(value == 2 for row in grid for value in row) else "none",
        "blocked_destination": blocked,
        "decoration_color": decoration_color,
    }


def _apply_with_delta(
    grid: list[list[int]],
    dr: int,
    dc: int,
    *,
    ignore_blockers: bool = False,
    all_or_nothing: bool = False,
) -> list[list[int]]:
    output = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    red = [
        (row, column)
        for row in range(h)
        for column in range(w)
        if grid[row][column] == 2
    ]
    destinations = [(row + dr, column + dc) for row, column in red]
    if all_or_nothing and any(
        not (0 <= row < h and 0 <= column < w) for row, column in destinations
    ):
        return output
    for row, column in destinations:
        if not (0 <= row < h and 0 <= column < w):
            continue
        if ignore_blockers or grid[row][column] in _ALLOWED_DESTINATION_COLORS:
            output[row][column] = 8
    return output


def _canonical_python(grid):
    dr, dc = _marker_delta(grid)
    return _apply_with_delta(grid, dr, dc)


def _rival_fixed_down_right_3_3(grid):
    return _apply_with_delta(grid, 3, 3)


def _rival_reverse_marker_vector(grid):
    dr, dc = _marker_delta(grid)
    return _apply_with_delta(grid, -dr, -dc)


def _rival_ignore_blockers(grid):
    dr, dc = _marker_delta(grid)
    return _apply_with_delta(grid, dr, dc, ignore_blockers=True)


def _rival_all_or_nothing(grid):
    dr, dc = _marker_delta(grid)
    return _apply_with_delta(grid, dr, dc, all_or_nothing=True)


SEMANTIC_RIVALS = {
    "fixed_down_right_3_3": _rival_fixed_down_right_3_3,
    "reverse_marker_vector": _rival_reverse_marker_vector,
    "ignore_blockers": _rival_ignore_blockers,
    "all_or_nothing_clipping": _rival_all_or_nothing,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _valid(grid) -> bool:
    return self_check(grid) == []


def _delta(grid) -> tuple[int, int]:
    return _marker_delta(grid)


def _has_partial_clipping(grid) -> bool:
    dr, dc = _delta(grid)
    translated = _translated_positions(grid, dr, dc)
    return any(not inside for _, _, inside in translated)


def _has_blocked_destination(grid) -> bool:
    dr, dc = _delta(grid)
    return any(
        inside and grid[row][column] not in _ALLOWED_DESTINATION_COLORS
        for row, column, inside in _translated_positions(grid, dr, dc)
    )


SEMANTIC_WITNESSES = {
    "vector_down_right": lambda grid: _valid(grid) and _delta(grid)[0] > 0 and _delta(grid)[1] > 0,
    "vector_down_left": lambda grid: _valid(grid) and _delta(grid)[0] > 0 and _delta(grid)[1] < 0,
    "vector_up_right": lambda grid: _valid(grid) and _delta(grid)[0] < 0 and _delta(grid)[1] > 0,
    "vector_up_left": lambda grid: _valid(grid) and _delta(grid)[0] < 0 and _delta(grid)[1] < 0,
    "fully_in_bounds": lambda grid: _valid(grid) and not _has_partial_clipping(grid),
    "partially_clipped": lambda grid: _valid(grid) and _has_partial_clipping(grid),
    "blocked_destination": lambda grid: _valid(grid) and _has_blocked_destination(grid),
    "unblocked_destination": lambda grid: _valid(grid) and not _has_blocked_destination(grid),
    "non_fixed_3_3_vector": lambda grid: _valid(grid) and _delta(grid) != (3, 3),
}

WITNESS_RIVALS = {
    "vector_down_right": ["reverse_marker_vector"],
    "vector_down_left": ["reverse_marker_vector", "fixed_down_right_3_3"],
    "vector_up_right": ["reverse_marker_vector", "fixed_down_right_3_3"],
    "vector_up_left": ["reverse_marker_vector", "fixed_down_right_3_3"],
    "fully_in_bounds": ["reverse_marker_vector"],
    "partially_clipped": ["reverse_marker_vector", "all_or_nothing_clipping"],
    "blocked_destination": ["reverse_marker_vector", "ignore_blockers"],
    "unblocked_destination": ["reverse_marker_vector"],
    "non_fixed_3_3_vector": ["fixed_down_right_3_3", "reverse_marker_vector"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Falsify marker-free fixed offsets and the named structural rivals."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"pair {index} input invalid: {'; '.join(errors)}")
        if pair["output"] != _canonical_python(pair["input"]):
            reasons.append(f"pair {index} output disagrees with marker-vector rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            if competitor(query["input"]) != query["output"]:
                reasons.append(f"named competitor {name} fits every demo but changes the query")

    fixed_survivors = []
    for dr in range(-6, 7):
        for dc in range(-6, 7):
            if dr == 0 and dc == 0:
                continue
            if all(_apply_with_delta(pair["input"], dr, dc) == pair["output"] for pair in demos):
                if _apply_with_delta(query["input"], dr, dc) != query["output"]:
                    fixed_survivors.append((dr, dc))
    if fixed_survivors:
        reasons.append(
            "marker-free fixed offsets fit every demo but change the query: "
            + repr(fixed_survivors[:5])
        )
    return reasons
