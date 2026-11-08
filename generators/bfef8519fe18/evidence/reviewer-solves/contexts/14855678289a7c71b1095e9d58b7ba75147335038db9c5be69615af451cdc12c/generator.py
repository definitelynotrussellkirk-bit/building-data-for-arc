"""Generator for ARC task bfef8519fe18 — fill every seeded room.

Color 1 is a wall.  The wall graph partitions the bordered grid into two,
three, or four 4-connected rooms.  Every room contains exactly one nonzero,
non-wall seed, and the selected rule floods each room's zero cells with its
seed color.

The schedule intentionally alternates rectangular and dogleg partitions.  The
latter are counterexamples to shortcuts that memorize the canonical T-shaped
three-room layout or assume every room is an axis-aligned rectangle.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from functools import lru_cache
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bfef8519fe18"
TASK_ID = "bfef8519fe18"
VERSION = "2.1.0"
# Whitespace-normalized sha256[:12] of the selected canonical Racket rule.
RULE_HASH = "77ee2c0d890d"

SUMMARY = (
    "A complete color-1 border plus connected internal color-1 walls split a "
    "7..14 by 8..16 grid into two to four rooms. Each room has one distinct "
    "seed color from 2..9 and at least one zero. Fill every room's zeros with "
    "its seed color while leaving all color-1 walls unchanged."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "color 1 forms the complete outer border and the internal room walls",
    "the non-wall cells form exactly two, three, or four connected rooms",
    "every room contains exactly one seed cell and at least one zero cell",
    "seed colors are distinct members of 2..9",
]

LAYOUTS = (
    "vertical_2",
    "horizontal_2",
    "t_top_3",
    "t_bottom_3",
    "t_left_3",
    "t_right_3",
    "cross_4",
    "dogleg_vertical_2",
    "dogleg_horizontal_2",
    "dogleg_vertical_cross_4",
    "dogleg_horizontal_cross_4",
)
IRREGULAR_LAYOUTS = frozenset(
    {
        "dogleg_vertical_2",
        "dogleg_horizontal_2",
        "dogleg_vertical_cross_4",
        "dogleg_horizontal_cross_4",
    }
)
EXPECTED_ROOMS = {
    "vertical_2": 2,
    "horizontal_2": 2,
    "t_top_3": 3,
    "t_bottom_3": 3,
    "t_left_3": 3,
    "t_right_3": 3,
    "cross_4": 4,
    "dogleg_vertical_2": 2,
    "dogleg_horizontal_2": 2,
    "dogleg_vertical_cross_4": 4,
    "dogleg_horizontal_cross_4": 4,
}
SEED_COLORS = tuple(range(2, 10))
_ALLOWED_COLORS = {0, 1, *SEED_COLORS}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "eight-slot curriculum with canonical 7x8 and 8x9 anchors",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "eight-slot curriculum with canonical 7x8 and 8x9 anchors",
        "valid": "8..16",
    },
    "layout": {
        "type": "enum",
        "default": "alternating regular and dogleg curriculum",
        "valid": "|".join(LAYOUTS),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# The regular/irregular alternation makes every cyclic four-pair lesson contain
# exactly two non-rectangular counterexamples.  Holding out any one pair still
# leaves an irregular demonstration that refutes both declared shortcuts.
_SCHEDULE = (
    ("canonical_7x8_t_top", 7, 8, ("t_top_3",), (3, 3)),
    ("dogleg_two_room", None, None, ("dogleg_vertical_2", "dogleg_horizontal_2"), None),
    ("rotated_three_room", None, None, ("t_bottom_3", "t_left_3", "t_right_3"), None),
    (
        "dogleg_four_room",
        None,
        None,
        ("dogleg_vertical_cross_4", "dogleg_horizontal_cross_4"),
        None,
    ),
    ("canonical_8x9_t_top", 8, 9, ("t_top_3",), (4, 4)),
    ("dogleg_two_room_alt", None, None, ("dogleg_horizontal_2", "dogleg_vertical_2"), None),
    ("regular_four_room", None, None, ("cross_4",), None),
    (
        "dogleg_four_room_alt",
        None,
        None,
        ("dogleg_horizontal_cross_4", "dogleg_vertical_cross_4"),
        None,
    ),
)
LESSON_SCHEDULE_PERIOD = len(_SCHEDULE)
SCHEDULE_PROFILES = tuple(row[0] for row in _SCHEDULE)
CANONICAL_PROFILES = frozenset({(7, 8, 5), (8, 9, 5)})


def _schedule_index(sample_index: int, difficulty: Any) -> int:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    if isinstance(sample_index, bool) or not isinstance(sample_index, int):
        raise TypeError("sample_index must be an integer (not bool)")
    return sample_index % LESSON_SCHEDULE_PERIOD


def schedule_profile(seed: Any, sample_index: int, difficulty: Any = None) -> str:
    """Expose the exact eight-slot lesson curriculum."""
    del seed
    return SCHEDULE_PROFILES[_schedule_index(sample_index, difficulty)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    for name, lo, hi in (("grid_h", 7, 14), ("grid_w", 8, 16)):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"override {name} must be an integer (not bool)")
        if not lo <= value <= hi:
            raise ValueError(f"override {name} must be in {lo}..{hi}, got {value}")

    if "layout" in overrides and overrides["layout"] is not None:
        value = overrides["layout"]
        if not isinstance(value, str) or value not in LAYOUTS:
            raise ValueError(f"override layout must be one of {LAYOUTS}, got {value!r}")


def _scheduled_int(ctx: Any, name: str, lo: int, hi: int, fixed: int | None) -> int:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    if fixed is not None:
        return ctx.draw_int_strict(name, fixed, fixed)
    # draw_int_diff does not reject bool/float overrides, but all overrides have
    # already been type-checked above.
    return ctx.draw_int_diff(name, lo, hi)


def _scheduled_choice(
    ctx: Any, name: str, options: tuple[str, ...], scheduled: tuple[str, ...]
) -> str:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, scheduled)


def _components(cells: Iterable[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for point in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    queue.append(point)
        result.append(component)
    return sorted(result, key=lambda room: min(room))


def _interior(height: int, width: int) -> set[tuple[int, int]]:
    return {
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
    }


def _regular_split_rows(height: int) -> range:
    # Leaves at least two open rows on either side of the wall.
    return range(3, height - 3)


def _regular_split_cols(width: int) -> range:
    # Leaves at least two open columns on either side of the wall.
    return range(3, width - 3)


def _full_vertical(height: int, col: int) -> set[tuple[int, int]]:
    return {(row, col) for row in range(1, height - 1)}


def _full_horizontal(width: int, row: int) -> set[tuple[int, int]]:
    return {(row, col) for col in range(1, width - 1)}


def _dogleg_vertical_wall(
    height: int, top_col: int, bottom_col: int, pivot_row: int
) -> set[tuple[int, int]]:
    """One top-to-bottom orthogonal divider with a single horizontal bend."""
    wall = {(row, top_col) for row in range(1, pivot_row + 1)}
    wall.update(
        (pivot_row, col)
        for col in range(min(top_col, bottom_col), max(top_col, bottom_col) + 1)
    )
    wall.update((row, bottom_col) for row in range(pivot_row, height - 1))
    return wall


def _dogleg_vertical_raw(
    height: int, width: int
) -> list[set[tuple[int, int]]]:
    walls: list[set[tuple[int, int]]] = []
    # A dogleg may bend nearer an edge than a straight divider because its
    # other segment restores room area.  Candidate filtering below still
    # requires four cells per room.  Using the straight-divider range here
    # would leave only one possible row after transposition at the minimum
    # 7-cell height, making horizontal doglegs unrealizable.
    split_cols = tuple(range(2, width - 2))
    for top_col in split_cols:
        for bottom_col in split_cols:
            if top_col == bottom_col:
                continue
            for pivot_row in range(2, height - 2):
                walls.append(
                    _dogleg_vertical_wall(
                        height, top_col, bottom_col, pivot_row
                    )
                )
    return walls


def _transpose_wall(wall: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    return {(col, row) for row, col in wall}


def _valid_wall_candidate(
    height: int,
    width: int,
    wall: set[tuple[int, int]],
    room_count: int,
) -> bool:
    interior = _interior(height, width)
    if not wall or not wall < interior:
        return False
    rooms = _components(interior - wall)
    return len(rooms) == room_count and all(len(room) >= 4 for room in rooms)


def _dedupe_candidates(
    height: int,
    width: int,
    candidates: Iterable[set[tuple[int, int]]],
    room_count: int,
) -> tuple[frozenset[tuple[int, int]], ...]:
    unique = {
        frozenset(wall)
        for wall in candidates
        if _valid_wall_candidate(height, width, wall, room_count)
    }
    return tuple(sorted(unique, key=lambda wall: tuple(sorted(wall))))


@lru_cache(maxsize=None)
def _wall_candidates(
    height: int, width: int, layout: str
) -> tuple[frozenset[tuple[int, int]], ...]:
    """Enumerate every valid wall realization for one public layout."""
    if layout not in EXPECTED_ROOMS:
        raise ValueError(f"unsupported layout: {layout!r}")
    candidates: list[set[tuple[int, int]]] = []

    if layout == "vertical_2":
        candidates = [
            _full_vertical(height, col) for col in _regular_split_cols(width)
        ]
    elif layout == "horizontal_2":
        candidates = [
            _full_horizontal(width, row) for row in _regular_split_rows(height)
        ]
    elif layout in {"t_top_3", "t_bottom_3", "cross_4"}:
        for row in _regular_split_rows(height):
            for col in _regular_split_cols(width):
                horizontal = _full_horizontal(width, row)
                if layout == "t_top_3":
                    candidates.append(
                        horizontal | {(rr, col) for rr in range(1, row)}
                    )
                elif layout == "t_bottom_3":
                    candidates.append(
                        horizontal | {(rr, col) for rr in range(row + 1, height - 1)}
                    )
                else:
                    candidates.append(horizontal | _full_vertical(height, col))
    elif layout in {"t_left_3", "t_right_3"}:
        for row in _regular_split_rows(height):
            for col in _regular_split_cols(width):
                vertical = _full_vertical(height, col)
                if layout == "t_left_3":
                    candidates.append(
                        vertical | {(row, cc) for cc in range(1, col)}
                    )
                else:
                    candidates.append(
                        vertical | {(row, cc) for cc in range(col + 1, width - 1)}
                    )
    elif layout == "dogleg_vertical_2":
        candidates = _dogleg_vertical_raw(height, width)
    elif layout == "dogleg_horizontal_2":
        candidates = [
            _transpose_wall(wall)
            for wall in _dogleg_vertical_raw(width, height)
        ]
    elif layout == "dogleg_vertical_cross_4":
        for dogleg in _dogleg_vertical_raw(height, width):
            # The dogleg connector is its only internal row containing more
            # than one wall cell. Avoid using that same row as the crossbar.
            counts: dict[int, int] = {}
            for row, _ in dogleg:
                counts[row] = counts.get(row, 0) + 1
            connector = max(counts, key=lambda row: (counts[row], -row))
            for row in _regular_split_rows(height):
                if row != connector:
                    candidates.append(dogleg | _full_horizontal(width, row))
    elif layout == "dogleg_horizontal_cross_4":
        transposed = _wall_candidates(width, height, "dogleg_vertical_cross_4")
        candidates = [_transpose_wall(wall) for wall in transposed]

    result = _dedupe_candidates(
        height, width, candidates, EXPECTED_ROOMS[layout]
    )
    if not result:
        raise ValueError(
            f"no valid wall candidates for {layout!r} at {height}x{width}"
        )
    return result


def _choose_wall(
    height: int, width: int, layout: str, rng: Any
) -> frozenset[tuple[int, int]]:
    """Choose one valid realization without enumerating the full corpus.

    Exhaustive dogleg-cross enumeration is useful for diagnostics, but putting
    it on the generation or validation path made a 20-draw lint cohort take
    minutes.  Parameter tuples are shuffled deterministically and checked until
    the first valid wall is found; all supported shapes have many witnesses.
    """
    if layout not in EXPECTED_ROOMS:
        raise ValueError(f"unsupported layout: {layout!r}")

    walls: list[set[tuple[int, int]]] = []
    if layout == "vertical_2":
        walls = [_full_vertical(height, col) for col in _regular_split_cols(width)]
    elif layout == "horizontal_2":
        walls = [_full_horizontal(width, row) for row in _regular_split_rows(height)]
    elif layout in {"t_top_3", "t_bottom_3", "cross_4"}:
        params = [
            (row, col)
            for row in _regular_split_rows(height)
            for col in _regular_split_cols(width)
        ]
        rng.shuffle(params)
        for row, col in params:
            horizontal = _full_horizontal(width, row)
            if layout == "t_top_3":
                wall = horizontal | {(rr, col) for rr in range(1, row)}
            elif layout == "t_bottom_3":
                wall = horizontal | {
                    (rr, col) for rr in range(row + 1, height - 1)
                }
            else:
                wall = horizontal | _full_vertical(height, col)
            if _valid_wall_candidate(
                height, width, wall, EXPECTED_ROOMS[layout]
            ):
                return frozenset(wall)
    elif layout in {"t_left_3", "t_right_3"}:
        params = [
            (row, col)
            for row in _regular_split_rows(height)
            for col in _regular_split_cols(width)
        ]
        rng.shuffle(params)
        for row, col in params:
            vertical = _full_vertical(height, col)
            if layout == "t_left_3":
                wall = vertical | {(row, cc) for cc in range(1, col)}
            else:
                wall = vertical | {
                    (row, cc) for cc in range(col + 1, width - 1)
                }
            if _valid_wall_candidate(
                height, width, wall, EXPECTED_ROOMS[layout]
            ):
                return frozenset(wall)
    elif layout in {"dogleg_horizontal_2", "dogleg_horizontal_cross_4"}:
        transposed_layout = (
            "dogleg_vertical_2"
            if layout == "dogleg_horizontal_2"
            else "dogleg_vertical_cross_4"
        )
        transposed = _choose_wall(width, height, transposed_layout, rng)
        wall = _transpose_wall(transposed)
        if _valid_wall_candidate(
            height, width, wall, EXPECTED_ROOMS[layout]
        ):
            return frozenset(wall)
        raise AssertionError("transposed dogleg candidate lost validity")
    else:
        split_cols = tuple(range(2, width - 2))
        params = [
            (top_col, bottom_col, pivot_row, split_row)
            for top_col in split_cols
            for bottom_col in split_cols
            if top_col != bottom_col
            for pivot_row in range(2, height - 2)
            for split_row in (
                tuple(_regular_split_rows(height))
                if layout == "dogleg_vertical_cross_4"
                else (None,)
            )
            if split_row is None or split_row != pivot_row
        ]
        rng.shuffle(params)
        for top_col, bottom_col, pivot_row, split_row in params:
            wall = _dogleg_vertical_wall(
                height, top_col, bottom_col, pivot_row
            )
            if split_row is not None:
                wall |= _full_horizontal(width, split_row)
            if _valid_wall_candidate(
                height, width, wall, EXPECTED_ROOMS[layout]
            ):
                return frozenset(wall)

    rng.shuffle(walls)
    for wall in walls:
        if _valid_wall_candidate(height, width, wall, EXPECTED_ROOMS[layout]):
            return frozenset(wall)
    raise ValueError(f"no valid wall candidate for {layout!r} at {height}x{width}")


def _canonical_wall(
    height: int, width: int, split: tuple[int, int]
) -> frozenset[tuple[int, int]]:
    row, col = split
    wall = frozenset(
        _full_horizontal(width, row)
        | {(rr, col) for rr in range(1, row)}
    )
    if not _valid_wall_candidate(height, width, set(wall), 3):
        raise AssertionError("canonical wall anchor is outside valid support")
    return wall


def _seed_candidates(room: set[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    """Prefer non-articulation seed sites so zero cells stay connected."""
    valid: list[tuple[int, int]] = []
    for point in sorted(room):
        remaining = room - {point}
        if remaining and len(_components(remaining)) == 1:
            valid.append(point)
    return tuple(valid)


def _make_grid(
    height: int,
    width: int,
    wall: frozenset[tuple[int, int]],
    seed_rng: Any,
) -> list[list[int]]:
    grid = full_grid(height, width, 0)
    for row in range(height):
        grid[row][0] = 1
        grid[row][width - 1] = 1
    for col in range(width):
        grid[0][col] = 1
        grid[height - 1][col] = 1
    for row, col in wall:
        grid[row][col] = 1

    rooms = _components(_interior(height, width) - set(wall))
    colors = seed_rng.sample(list(SEED_COLORS), len(rooms))
    for room, color in zip(rooms, colors):
        candidates = _seed_candidates(room)
        if not candidates:
            raise AssertionError("wall candidate has no non-articulation seed site")
        row, col = seed_rng.choice(candidates)
        grid[row][col] = color
    return grid


def generate(seed: Any, sample_index: int, *, difficulty: Any = None, **overrides: Any):
    """Generate one deterministic, exactly controllable puzzle input."""
    _validate_call(difficulty, overrides)
    index = _schedule_index(sample_index, difficulty)
    profile, fixed_h, fixed_w, scheduled_layouts, canonical_split = _SCHEDULE[index]
    del profile

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _scheduled_int(ctx, "grid_h", 7, 14, fixed_h)
    width = _scheduled_int(ctx, "grid_w", 8, 16, fixed_w)
    layout = _scheduled_choice(ctx, "layout", LAYOUTS, scheduled_layouts)

    exact_canonical_slot = (
        canonical_split is not None
        and not any(
            name in overrides and overrides[name] is not None
            for name in ("grid_h", "grid_w", "layout")
        )
    )
    if exact_canonical_slot:
        wall = _canonical_wall(height, width, canonical_split)
    else:
        wall = _choose_wall(
            height, width, layout, ctx.draw_rng("wall_geometry")
        )

    grid = _make_grid(height, width, wall, ctx.draw_rng("seed_cells_and_colors"))
    errors = self_check(grid)
    if errors:
        raise AssertionError("generator produced an invalid grid: " + "; ".join(errors))
    return grid


def _basic_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["every row must be a non-empty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    errors: list[str] = []
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if isinstance(value, bool) or not isinstance(value, int):
                errors.append(f"cell ({row},{col}) is not an integer ARC color")
            elif value not in _ALLOWED_COLORS:
                errors.append(f"cell ({row},{col}) has unsupported color {value}")
    return errors


def _matches_vertical_dogleg(
    height: int,
    width: int,
    walls: frozenset[tuple[int, int]],
    *,
    with_crossbar: bool,
) -> bool:
    top_cols = [col for col in range(1, width - 1) if (1, col) in walls]
    bottom_cols = [
        col for col in range(1, width - 1) if (height - 2, col) in walls
    ]
    if len(top_cols) != 1 or len(bottom_cols) != 1:
        return False
    top_col, bottom_col = top_cols[0], bottom_cols[0]
    if top_col == bottom_col:
        return False

    crossbars: tuple[int | None, ...]
    if with_crossbar:
        rows = tuple(
            row
            for row in _regular_split_rows(height)
            if all((row, col) in walls for col in range(1, width - 1))
        )
        if len(rows) != 1:
            return False
        crossbars = rows
    else:
        crossbars = (None,)

    for pivot_row in range(2, height - 2):
        for split_row in crossbars:
            if split_row is not None and split_row == pivot_row:
                continue
            candidate = _dogleg_vertical_wall(
                height, top_col, bottom_col, pivot_row
            )
            if split_row is not None:
                candidate |= _full_horizontal(width, split_row)
            if walls == frozenset(candidate):
                return True
    return False


def _layout_matches(
    height: int, width: int, internal_walls: frozenset[tuple[int, int]]
) -> list[str]:
    """Recognize wall geometry directly in O(grid area), not by corpus scan."""
    matches: list[str] = []
    for col in _regular_split_cols(width):
        if internal_walls == frozenset(_full_vertical(height, col)):
            matches.append("vertical_2")
    for row in _regular_split_rows(height):
        if internal_walls == frozenset(_full_horizontal(width, row)):
            matches.append("horizontal_2")
        for col in _regular_split_cols(width):
            horizontal = _full_horizontal(width, row)
            vertical = _full_vertical(height, col)
            if internal_walls == frozenset(
                horizontal | {(rr, col) for rr in range(1, row)}
            ):
                matches.append("t_top_3")
            if internal_walls == frozenset(
                horizontal
                | {(rr, col) for rr in range(row + 1, height - 1)}
            ):
                matches.append("t_bottom_3")
            if internal_walls == frozenset(
                vertical | {(row, cc) for cc in range(1, col)}
            ):
                matches.append("t_left_3")
            if internal_walls == frozenset(
                vertical
                | {(row, cc) for cc in range(col + 1, width - 1)}
            ):
                matches.append("t_right_3")
            if internal_walls == frozenset(horizontal | vertical):
                matches.append("cross_4")

    if _matches_vertical_dogleg(
        height, width, internal_walls, with_crossbar=False
    ):
        matches.append("dogleg_vertical_2")
    transposed = frozenset(_transpose_wall(internal_walls))
    if _matches_vertical_dogleg(
        width, height, transposed, with_crossbar=False
    ):
        matches.append("dogleg_horizontal_2")
    if _matches_vertical_dogleg(
        height, width, internal_walls, with_crossbar=True
    ):
        matches.append("dogleg_vertical_cross_4")
    if _matches_vertical_dogleg(
        width, height, transposed, with_crossbar=True
    ):
        matches.append("dogleg_horizontal_cross_4")
    return matches


def _analyze(grid: Any) -> tuple[dict[str, Any], list[str]]:
    errors = _basic_grid_errors(grid)
    if errors:
        return {}, errors

    height = len(grid)
    width = len(grid[0])
    if not 7 <= height <= 14:
        errors.append(f"grid height must be 7..14, got {height}")
    if not 8 <= width <= 16:
        errors.append(f"grid width must be 8..16, got {width}")

    border = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    }
    missing_border = sorted(
        point for point in border if grid[point[0]][point[1]] != 1
    )
    if missing_border:
        errors.append(
            f"outer border must be entirely color 1; first mismatch is {missing_border[0]}"
        )

    internal_walls = frozenset(
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if grid[row][col] == 1
    )
    matches: list[str] = []
    if 7 <= height <= 14 and 8 <= width <= 16:
        matches = _layout_matches(height, width, internal_walls)
    if len(matches) != 1:
        errors.append(
            "internal color-1 walls must match exactly one supported layout; "
            f"matched {matches!r}"
        )
    layout = matches[0] if len(matches) == 1 else None

    non_walls = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 1
    }
    rooms = _components(non_walls)
    expected = EXPECTED_ROOMS.get(layout) if layout is not None else None
    if expected is not None and len(rooms) != expected:
        errors.append(f"layout {layout} must make {expected} rooms, got {len(rooms)}")
    if len(rooms) not in (2, 3, 4):
        errors.append(f"expected two, three, or four rooms, got {len(rooms)}")

    seed_records: list[tuple[int, int, int]] = []
    room_colors: list[int] = []
    for index, room in enumerate(rooms):
        seeds = [
            (row, col, grid[row][col])
            for row, col in sorted(room)
            if grid[row][col] not in (0, 1)
        ]
        zeros = {(row, col) for row, col in room if grid[row][col] == 0}
        if len(seeds) != 1:
            errors.append(f"room {index} must contain exactly one seed, got {len(seeds)}")
        else:
            seed_records.extend(seeds)
            room_colors.append(seeds[0][2])
        if not zeros:
            errors.append(f"room {index} must contain at least one zero cell")
        elif len(_components(zeros)) != 1:
            errors.append(f"room {index}'s zero cells must remain 4-connected")
    if len(room_colors) != len(set(room_colors)):
        errors.append("seed colors must be distinct across rooms")

    facts = {
        "height": height,
        "width": width,
        "grid_h": height,
        "grid_w": width,
        "layout": layout,
        "internal_walls": internal_walls,
        "rooms": rooms,
        "room_count": len(rooms),
        "seeds": seed_records,
        "seed_colors": tuple(room_colors),
        "palette_size": len({value for row in grid for value in row}),
        "irregular": layout in IRREGULAR_LAYOUTS,
    }
    return facts, errors


def scene_facts(grid: Any) -> dict[str, Any]:
    """Return independently reconstructed semantic facts for a valid input."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid room scene: " + "; ".join(errors))
    return facts


def observe_overrides(grid: Any) -> dict[str, Any]:
    """Recover every declared exact control from returned pixels."""
    facts = scene_facts(grid)
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "layout": facts["layout"],
    }


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Reject malformed, ambiguous, or shortcut-only room scenes."""
    del difficulty, meta
    return _analyze(grid)[1]


def strict_canonical_like(grid: Any) -> list[str]:
    """Generated support is the canonical rule manifold, including rotations."""
    return self_check(grid)


def rule_mirror(grid: Any) -> list[list[int]]:
    """Pure Python mirror of the selected Racket connected-component rule."""
    errors = _basic_grid_errors(grid)
    if errors:
        raise ValueError("cannot solve malformed grid: " + "; ".join(errors))
    height = len(grid)
    width = len(grid[0])
    output = deepcopy(grid)
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 1
    }
    for room in _components(unseen):
        colors = {
            grid[row][col]
            for row, col in room
            if grid[row][col] != 0
        }
        if len(colors) == 1:
            color = next(iter(colors))
            for row, col in room:
                if grid[row][col] == 0:
                    output[row][col] = color
    return output


def _identity(grid: Any) -> list[list[int]]:
    return deepcopy(grid)


def _is_canonical_t_top(facts: dict[str, Any]) -> bool:
    return (
        facts["layout"] == "t_top_3"
        and (facts["height"], facts["width"], facts["palette_size"])
        in CANONICAL_PROFILES
    )


def _canonical_t_top_only(grid: Any) -> list[list[int]]:
    """Wrong rule: solve only the two public T-top profile families."""
    try:
        facts = scene_facts(grid)
    except (TypeError, ValueError):
        return _identity(grid)
    return rule_mirror(grid) if _is_canonical_t_top(facts) else _identity(grid)


def _room_is_rectangle(room: set[tuple[int, int]]) -> bool:
    r0 = min(row for row, _ in room)
    r1 = max(row for row, _ in room)
    c0 = min(col for _, col in room)
    c1 = max(col for _, col in room)
    return room == {
        (row, col)
        for row in range(r0, r1 + 1)
        for col in range(c0, c1 + 1)
    }


def _rectangular_rooms_only(grid: Any) -> list[list[int]]:
    """Wrong rule: flood only when every room is an axis-aligned rectangle."""
    try:
        facts = scene_facts(grid)
    except (TypeError, ValueError):
        return _identity(grid)
    if all(_room_is_rectangle(room) for room in facts["rooms"]):
        return rule_mirror(grid)
    return _identity(grid)


def _fillable_rooms(grid: Any) -> bool:
    try:
        facts = scene_facts(grid)
    except (TypeError, ValueError):
        return False
    return bool(facts["rooms"]) and rule_mirror(grid) != grid


def _noncanonical_layout(grid: Any) -> bool:
    try:
        facts = scene_facts(grid)
    except (TypeError, ValueError):
        return False
    return not _is_canonical_t_top(facts)


def _irregular_rooms(grid: Any) -> bool:
    try:
        return bool(scene_facts(grid)["irregular"])
    except (TypeError, ValueError):
        return False


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "identity": _identity,
    "canonical_t_top_only": _canonical_t_top_only,
    "rectangular_rooms_only": _rectangular_rooms_only,
}
CANONICAL_SHORTCUTS: dict[str, Callable[[Any], list[list[int]]]] = {
    "canonical_t_top_only": _canonical_t_top_only,
    "rectangular_rooms_only": _rectangular_rooms_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "fillable_rooms": _fillable_rooms,
    "noncanonical_layout": _noncanonical_layout,
    "irregular_rooms": _irregular_rooms,
}
WITNESS_RIVALS = {
    "fillable_rooms": ("identity",),
    "noncanonical_layout": ("canonical_t_top_only",),
    "irregular_rooms": ("rectangular_rooms_only",),
}
BRANCH_WITNESSES = ("fillable_rooms", "noncanonical_layout", "irregular_rooms")


def lesson_identifiable(
    demos: list[dict[str, Any]], query: dict[str, Any]
) -> list[str]:
    """Report competitors that fit every demonstration but change the query."""
    reasons: list[str] = []
    for name, solve in LESSON_COMPETITORS.items():
        fits_demos = all(solve(pair["input"]) == pair["output"] for pair in demos)
        if fits_demos and solve(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} fits every demonstration but changes the query"
            )
    return reasons
