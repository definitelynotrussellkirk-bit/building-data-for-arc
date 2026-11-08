"""Generator for upward gravity inside cyan-walled chambers.

The selected rule treats color 8 as an immovable wall.  Every 4-connected
non-8 region is a chamber; within each chamber and each column, nonzero values
are compacted upward while preserving their top-to-bottom order.

This sampler deliberately cycles through single-chamber, vertical-only,
horizontal-only, and mixed chamber layouts.  The no-vertical-wall profiles are
ordinary curriculum members, not caller-only degenerates, because every public
canonical pair contains a vertical wall and therefore cannot by itself refute
"only apply gravity when a vertical wall exists".
"""
from __future__ import annotations

from collections import defaultdict, deque
from itertools import combinations
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ed98575459d2"
TASK_ID = GENERATOR_ID
RULE_HASH = "7798fc567577"
VERSION = "3.0.0"

SUMMARY = (
    "A solid color-8 outer frame, optionally crossed by 0-2 full-height "
    "vertical walls and 0-1 full-width horizontal wall, partitions a 0-bg "
    "grid into rectangular chambers.  Six to eight pebbles use every color "
    "2..7, with at least one pebble in each chamber.  In every chamber, each "
    "column's pebbles compact upward independently while retaining their "
    "top-to-bottom order; all color-8 walls stay fixed."
)

INVARIANTS = [
    "background is 0 and the complete outer rectangle is color 8",
    "all other color-8 cells belong to 0-2 complete vertical walls or 0-1 complete horizontal wall",
    "every rectangular chamber has at least two rows, two columns, and at least one pebble",
    "there are 6-8 pebbles and every color 2,3,4,5,6,7 appears",
    "at least one pebble moves under chamber-local upward compaction",
]

AXES = {
    "grid_h": {"type": "int", "default": "five-profile schedule", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "five-profile schedule", "valid": "10..16"},
    "n_walls": {"type": "int", "default": "cycle 0,1,0,1,2", "valid": "0..2"},
    "n_hwalls": {"type": "int", "default": "cycle 0,0,1,1,0", "valid": "0..1"},
    "n_pebbles": {"type": "int", "default": "cycle 7,6,6,6,7", "valid": "6..8"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 5

_PROFILES = (
    {
        "name": "single_chamber",
        "grid_h": 8,
        "grid_w": 12,
        "n_walls": 0,
        "n_hwalls": 0,
        "n_pebbles": 7,
    },
    {
        "name": "vertical_split",
        "grid_h": 9,
        "grid_w": 11,
        "n_walls": 1,
        "n_hwalls": 0,
        "n_pebbles": 6,
    },
    {
        "name": "horizontal_split",
        "grid_h": 8,
        "grid_w": 13,
        "n_walls": 0,
        "n_hwalls": 1,
        "n_pebbles": 6,
    },
    {
        "name": "mixed_split",
        "grid_h": 10,
        "grid_w": 12,
        "n_walls": 1,
        "n_hwalls": 1,
        "n_pebbles": 6,
    },
    {
        "name": "three_vertical_chambers",
        "grid_h": 9,
        "grid_w": 12,
        "n_walls": 2,
        "n_hwalls": 0,
        "n_pebbles": 7,
    },
)
SCHEDULE_PROFILES = tuple(profile["name"] for profile in _PROFILES)
_ALLOWED_DIFFICULTIES = {None, "easy", "medium", "hard"}
_PEBBLE_COLORS = (2, 3, 4, 5, 6, 7)
_ALLOWED_COLORS = {0, 2, 3, 4, 5, 6, 7, 8}
_STACK_COLOR_ORDERS = {
    None: (7, 2, 3, 4, 5, 6),
    "easy": (4, 2, 3, 5, 6, 7),
    "medium": (6, 3, 2, 4, 5, 7),
    "hard": (7, 2, 3, 4, 5, 6),
}
_SINGLE_COLOR_ORDERS = {
    None: (2, 3, 4, 5, 6, 7),
    "easy": (2, 3, 4, 5, 6, 7),
    "medium": (3, 4, 5, 6, 7, 2),
    "hard": (7, 6, 5, 4, 3, 2),
}
_AXIS_BOUNDS = {
    "grid_h": (7, 14),
    "grid_w": (10, 16),
    "n_walls": (0, 2),
    "n_hwalls": (0, 1),
    "n_pebbles": (6, 8),
}


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the deterministic curriculum slot used by ordinary generation."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _profile(sample_index: int) -> dict[str, int | str]:
    return _PROFILES[int(sample_index) % len(_PROFILES)]


def _validate_request(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError(f"unknown difficulty {difficulty!r}; expected easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _line_sets(length: int, count: int) -> list[tuple[int, ...]]:
    """All internal full-line positions leaving >=2 cells in every band."""
    if count == 0:
        return [()]
    candidates = range(3, length - 3)
    legal = []
    for lines in combinations(candidates, count):
        edges = (0, *lines, length - 1)
        if all(right - left >= 3 for left, right in zip(edges, edges[1:])):
            legal.append(tuple(lines))
    return legal


def _choose_lines(rng, length: int, count: int, axis_name: str) -> tuple[int, ...]:
    legal = _line_sets(length, count)
    if not legal:
        raise ValueError(
            f"{axis_name}={count} cannot fit in length {length} while keeping two-cell chambers"
        )
    return rng.choice(legal)


def _bands(length: int, lines: Iterable[int]) -> list[tuple[int, int]]:
    edges = (0, *sorted(lines), length - 1)
    return [(left + 1, right - 1) for left, right in zip(edges, edges[1:])]


def _chambers(
    h: int, w: int, hrows: Iterable[int], vcols: Iterable[int]
) -> list[tuple[int, int, int, int]]:
    return [
        (r0, r1, c0, c1)
        for r0, r1 in _bands(h, hrows)
        for c0, c1 in _bands(w, vcols)
    ]


def _add_position(
    positions: list[tuple[int, int]], used: set[tuple[int, int]], point: tuple[int, int]
) -> bool:
    if point in used:
        return False
    positions.append(point)
    used.add(point)
    return True


def _pebble_positions(
    ctx,
    chambers: list[tuple[int, int, int, int]],
    count: int,
    difficulty: str | None,
):
    """Construct exact-count positions with chamber coverage and teaching stacks.

    Difficulty changes displacement rather than the exact structural axes:
    easy anchors sit just below a chamber top, medium anchors near mid-height,
    and hard anchors at the floor.  The keyed RNG label also includes the band.
    """
    rng = ctx.draw_rng(f"pebble_positions:{difficulty or 'default'}")

    def anchor_row(r0: int, r1: int) -> int:
        if difficulty == "easy":
            return min(r0 + 1, r1)
        if difficulty == "medium":
            return max(r0 + 1, (r0 + r1) // 2)
        return r1
    positions: list[tuple[int, int]] = []
    used: set[tuple[int, int]] = set()
    # Cells kept empty so at least one deliberately low pebble cannot become
    # accidentally top-packed when the remaining random positions are filled.
    protected_empty: set[tuple[int, int]] = set()
    stacked = count > len(chambers)

    if stacked:
        r0, r1, c0, c1 = chambers[0]
        stack_col = rng.randint(c0, c1)
        top_row = r0 + 1 if r1 - r0 >= 2 else r0
        _add_position(positions, used, (top_row, stack_col))
        _add_position(positions, used, (r1, stack_col))
        if top_row > r0:
            protected_empty.add((r0, stack_col))
        covered_from = 1
    else:
        covered_from = 0

    # One guaranteed moving pebble in every not-yet-covered chamber.  Keep the
    # top cell of its column empty even after filler placement.
    for r0, r1, c0, c1 in chambers[covered_from:]:
        columns = list(range(c0, c1 + 1))
        rng.shuffle(columns)
        target_row = anchor_row(r0, r1)
        point = next(((target_row, col) for col in columns if (target_row, col) not in used), None)
        if point is None:  # defensive; valid geometry always has one
            raise RuntimeError("constructive chamber placement unexpectedly exhausted")
        _add_position(positions, used, point)
        if point[0] > r0:
            protected_empty.add((r0, point[1]))

    # A one-chamber stack can be top-packed in a two-row chamber.  Reserve a
    # second column at the bottom and protect its top cell so the rule fires.
    if len(chambers) == 1 and stacked:
        r0, r1, c0, c1 = chambers[0]
        target_row = anchor_row(r0, r1)
        candidates = [
            (target_row, col)
            for col in range(c0, c1 + 1)
            if (target_row, col) not in used
        ]
        if candidates:
            point = rng.choice(candidates)
            _add_position(positions, used, point)
            if point[0] > r0:
                protected_empty.add((r0, point[1]))

    candidates = [
        (row, col)
        for r0, r1, c0, c1 in chambers
        for row in range(r0, r1 + 1)
        for col in range(c0, c1 + 1)
        if (row, col) not in used and (row, col) not in protected_empty
    ]
    rng.shuffle(candidates)
    needed = count - len(positions)
    if needed < 0 or needed > len(candidates):
        raise ValueError(f"cannot place {count} pebbles in the selected chamber geometry")
    positions.extend(candidates[:needed])
    return positions, stacked


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    profile = _profile(sample_index)
    effective = {
        name: overrides[name] if overrides.get(name) is not None else profile[name]
        for name in AXES
    }
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_int("grid_h", 7, 14)
    w = ctx.draw_int("grid_w", 10, 16)
    n_walls = ctx.draw_int("n_walls", 0, 2)
    n_hwalls = ctx.draw_int("n_hwalls", 0, 1)
    n_pebbles = ctx.draw_int("n_pebbles", 6, 8)

    vcols = _choose_lines(ctx.draw_rng("vertical_walls"), w, n_walls, "n_walls")
    hrows = _choose_lines(ctx.draw_rng("horizontal_walls"), h, n_hwalls, "n_hwalls")

    grid = full_grid(h, w, 0)
    for col in range(w):
        grid[0][col] = 8
        grid[h - 1][col] = 8
    for row in range(h):
        grid[row][0] = 8
        grid[row][w - 1] = 8
    for col in vcols:
        for row in range(h):
            grid[row][col] = 8
    for row in hrows:
        for col in range(w):
            grid[row][col] = 8

    chamber_boxes = _chambers(h, w, hrows, vcols)
    positions, stacked = _pebble_positions(ctx, chamber_boxes, n_pebbles, difficulty)
    if stacked:
        # Every band begins with a deliberately descending stack, but uses a
        # different color order so the difficulty knob cannot be byte-dead.
        colors = list(_STACK_COLOR_ORDERS[difficulty])
    else:
        colors = list(_SINGLE_COLOR_ORDERS[difficulty])
    extra_rng = ctx.draw_rng(f"extra_colors:{difficulty or 'default'}")
    colors.extend(extra_rng.choice(_PEBBLE_COLORS) for _ in range(n_pebbles - 6))
    for (row, col), color in zip(positions, colors, strict=True):
        grid[row][col] = color
    return grid


def _rectangular_grid(grid: Any) -> tuple[int, int] | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None
    return len(grid), width


def _regions_without_wall(grid) -> list[list[tuple[int, int]]]:
    dims = _rectangular_grid(grid)
    if dims is None:
        raise ValueError("expected a nonempty rectangular grid")
    h, w = dims
    seen: set[tuple[int, int]] = set()
    regions: list[list[tuple[int, int]]] = []
    for start_r in range(h):
        for start_c in range(w):
            start = (start_r, start_c)
            if start in seen or grid[start_r][start_c] == 8:
                continue
            queue = deque([start])
            seen.add(start)
            region = []
            while queue:
                row, col = queue.popleft()
                region.append((row, col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = (row + dr, col + dc)
                    if not (0 <= nxt[0] < h and 0 <= nxt[1] < w):
                        continue
                    if nxt in seen or grid[nxt[0]][nxt[1]] == 8:
                        continue
                    seen.add(nxt)
                    queue.append(nxt)
            regions.append(sorted(region))
    return regions


def _compact_regions(grid, *, direction: str = "up", sort_values: bool = False, keep_one=False):
    dims = _rectangular_grid(grid)
    if dims is None:
        raise ValueError("expected a nonempty rectangular grid")
    output = [list(row) for row in grid]
    for region in _regions_without_wall(grid):
        by_col: dict[int, list[int]] = defaultdict(list)
        for row, col in region:
            output[row][col] = 0
            by_col[col].append(row)
        for col, rows in by_col.items():
            rows.sort()
            values = [grid[row][col] for row in rows if grid[row][col] != 0]
            if sort_values:
                values = sorted(values)
            if keep_one:
                values = values[:1]
            destinations = rows[: len(values)] if direction == "up" else rows[len(rows) - len(values) :]
            for row, value in zip(destinations, values):
                output[row][col] = value
    return output


def rule_mirror(grid):
    """Python mirror of the selected Racket authority; does not mutate input."""
    return _compact_regions(grid, direction="up")


def _full_lines(grid):
    h, w = len(grid), len(grid[0])
    full_rows = [row for row in range(h) if all(grid[row][col] == 8 for col in range(w))]
    full_cols = [col for col in range(w) if all(grid[row][col] == 8 for row in range(h))]
    return full_rows, full_cols


def _analysis(grid) -> dict[str, Any]:
    dims = _rectangular_grid(grid)
    if dims is None:
        return {"errors": ["expected a nonempty rectangular grid"]}
    h, w = dims
    errors: list[str] = []
    bad_cells = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if type(value) is not int or value not in _ALLOWED_COLORS
    ]
    if bad_cells:
        errors.append("cells must be integer colors from 0,2,3,4,5,6,7,8")
    if not 7 <= h <= 14:
        errors.append(f"grid_h={h} outside [7,14]")
    if not 10 <= w <= 16:
        errors.append(f"grid_w={w} outside [10,16]")

    if any(grid[0][col] != 8 or grid[h - 1][col] != 8 for col in range(w)) or any(
        grid[row][0] != 8 or grid[row][w - 1] != 8 for row in range(h)
    ):
        errors.append("outer rectangle must be a complete color-8 frame")

    full_rows, full_cols = _full_lines(grid)
    full_row_set, full_col_set = set(full_rows), set(full_cols)
    if any(
        value == 8 and row not in full_row_set and col not in full_col_set
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
    ):
        errors.append("every color-8 cell must belong to a complete wall row or wall column")

    hrows = [row for row in full_rows if row not in (0, h - 1)]
    vcols = [col for col in full_cols if col not in (0, w - 1)]
    if len(vcols) > 2:
        errors.append(f"n_walls={len(vcols)} outside [0,2]")
    if len(hrows) > 1:
        errors.append(f"n_hwalls={len(hrows)} outside [0,1]")

    row_bands = _bands(h, hrows)
    col_bands = _bands(w, vcols)
    if any(r1 - r0 + 1 < 2 for r0, r1 in row_bands):
        errors.append("every chamber must have at least two interior rows")
    if any(c1 - c0 + 1 < 2 for c0, c1 in col_bands):
        errors.append("every chamber must have at least two interior columns")

    pebble_positions = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if type(value) is int and value in _PEBBLE_COLORS
    ]
    if not 6 <= len(pebble_positions) <= 8:
        errors.append(f"n_pebbles={len(pebble_positions)} outside [6,8]")
    observed_colors = {grid[row][col] for row, col in pebble_positions}
    missing = sorted(set(_PEBBLE_COLORS) - observed_colors)
    if missing:
        errors.append(f"every pebble color 2..7 must appear; missing {missing}")
    if not any(value == 0 for row in grid for value in row):
        errors.append("at least one background cell is required")

    chamber_boxes = _chambers(h, w, hrows, vcols)
    for index, (r0, r1, c0, c1) in enumerate(chamber_boxes):
        if not any(r0 <= row <= r1 and c0 <= col <= c1 for row, col in pebble_positions):
            errors.append(f"chamber {index} has no pebble")

    if not bad_cells:
        try:
            if rule_mirror(grid) == [list(row) for row in grid]:
                errors.append("at least one pebble must move under upward gravity")
        except ValueError as exc:  # defensive for malformed callers
            errors.append(str(exc))

    return {
        "errors": sorted(set(errors)),
        "height": h,
        "width": w,
        "hrows": hrows,
        "vcols": vcols,
        "chambers": chamber_boxes,
        "n_pebbles": len(pebble_positions),
    }


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe axes on invalid grid: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_walls": len(analysis["vcols"]),
        "n_hwalls": len(analysis["hrows"]),
        "n_pebbles": analysis["n_pebbles"],
    }


def self_check(grid, *, difficulty=None, meta=None):
    del meta
    if difficulty not in _ALLOWED_DIFFICULTIES:
        return [f"unknown difficulty {difficulty!r}"]
    return _analysis(grid)["errors"]


def strict_canonical_like(grid):
    """Lawful instances of the declared full-line chamber manifold."""
    return self_check(grid)


def _identity(grid):
    return [list(row) for row in grid]


def _rival_requires_vertical_wall(grid):
    """Canonical-fitting shortcut: do nothing unless a full vertical wall exists."""
    dims = _rectangular_grid(grid)
    if dims is None:
        return _identity(grid)
    _, full_cols = _full_lines(grid)
    internal = [col for col in full_cols if col not in (0, dims[1] - 1)]
    return rule_mirror(grid) if internal else _identity(grid)


def _rival_ignore_horizontal_walls(grid):
    """Pack through horizontal separators as if every column were one chamber."""
    dims = _rectangular_grid(grid)
    if dims is None:
        return _identity(grid)
    h, w = dims
    output = [list(row) for row in grid]
    for col in range(w):
        slots = [row for row in range(h) if grid[row][col] != 8]
        values = [grid[row][col] for row in slots if grid[row][col] != 0]
        for row in slots:
            output[row][col] = 0
        for row, value in zip(slots, values):
            output[row][col] = value
    return output


def _rival_keep_only_topmost(grid):
    return _compact_regions(grid, direction="up", keep_one=True)


def _rival_sort_stack_by_color(grid):
    return _compact_regions(grid, direction="up", sort_values=True)


def _rival_downward_gravity(grid):
    return _compact_regions(grid, direction="down")


def _witness_no_vertical_wall(grid) -> bool:
    try:
        return observe_overrides(grid)["n_walls"] == 0 and rule_mirror(grid) != grid
    except (TypeError, ValueError):
        return False


def _witness_horizontal_barrier(grid) -> bool:
    try:
        return observe_overrides(grid)["n_hwalls"] > 0 and _rival_ignore_horizontal_walls(grid) != rule_mirror(grid)
    except (TypeError, ValueError):
        return False


def _witness_rival_disagrees(rival: Callable[[Any], Any]):
    def witness(grid) -> bool:
        try:
            return rival(grid) != rule_mirror(grid)
        except (TypeError, ValueError):
            return False

    return witness


SEMANTIC_RIVALS = {
    "requires_vertical_wall": _rival_requires_vertical_wall,
    "ignore_horizontal_walls": _rival_ignore_horizontal_walls,
    "keep_only_topmost": _rival_keep_only_topmost,
    "sort_stack_by_color": _rival_sort_stack_by_color,
    "identity": _identity,
    "downward_gravity": _rival_downward_gravity,
}
SEMANTIC_WITNESSES = {
    "single_or_horizontal_chamber_without_vertical_wall": _witness_no_vertical_wall,
    "horizontal_barrier_changes_column_regions": _witness_horizontal_barrier,
    "all_stacked_pebbles_survive": _witness_rival_disagrees(_rival_keep_only_topmost),
    "stack_order_is_top_to_bottom_not_color_sorted": _witness_rival_disagrees(_rival_sort_stack_by_color),
    "motion_is_not_identity": _witness_rival_disagrees(_identity),
    "gravity_points_up_not_down": _witness_rival_disagrees(_rival_downward_gravity),
}
WITNESS_RIVALS = {
    "single_or_horizontal_chamber_without_vertical_wall": ["requires_vertical_wall"],
    "horizontal_barrier_changes_column_regions": ["ignore_horizontal_walls"],
    "all_stacked_pebbles_survive": ["keep_only_topmost"],
    "stack_order_is_top_to_bottom_not_color_sorted": ["sort_stack_by_color"],
    "motion_is_not_identity": ["identity"],
    "gravity_points_up_not_down": ["downward_gravity"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"requires_vertical_wall": _rival_requires_vertical_wall}


def lesson_identifiable(demos, query) -> list[str]:
    """Validate oracle pairs and require demonstrations to kill every named rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]

    reasons: list[str] = []
    usable = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        grammar = strict_canonical_like(pair["input"])
        reasons.extend(f"demo {index}: {reason}" for reason in grammar)
        try:
            expected = rule_mirror(pair["input"])
        except (TypeError, ValueError) as exc:
            reasons.append(f"demo {index}: rule mirror failed: {exc}")
            continue
        if expected != pair["output"]:
            reasons.append(f"demo {index} disagrees with chamber-local upward gravity")
        else:
            usable.append(pair)

    query_grammar = strict_canonical_like(query["input"])
    reasons.extend(f"query: {reason}" for reason in query_grammar)
    try:
        if rule_mirror(query["input"]) != query["output"]:
            reasons.append("query disagrees with chamber-local upward gravity")
    except (TypeError, ValueError) as exc:
        reasons.append(f"query rule mirror failed: {exc}")

    if reasons:
        return sorted(set(reasons))
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in usable):
            reasons.append(f"demonstrations do not falsify rival: {name}")
    return sorted(set(reasons))
