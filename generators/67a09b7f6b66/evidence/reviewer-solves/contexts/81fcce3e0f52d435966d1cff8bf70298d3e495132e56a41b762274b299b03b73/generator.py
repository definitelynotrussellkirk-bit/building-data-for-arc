"""Generator for 15b:hard_101 — fill chambers by dot-count legend.

Input grammar
-------------
The three cells at row 0, columns 1..3 are an ordered color legend.
Color-8 walls below that row form three equal vertical chambers.  Each
chamber contains a distinct count from {1, 2, 3} of color-1 dots.

Rule
----
Count the dots in each chamber.  If a chamber contains n dots, fill its
entire interior with legend color n (using one-based legend positions).
The wall color 8 is also a lawful legend color; its role is positional.

The canonical examples always place counts 1,2,3 from left to right and put
at most one dot in each row.  Thus both "color by chamber position" and
"count occupied rows" fit them.  Default generation cycles through all six
count orders and regularly puts the two-dot chamber on one row so every
three-example lesson refutes both shortcuts while retaining regular 9x13
canonical-profile anchors.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "67a09b7f6b66"
TASK_ID = GENERATOR_ID
RULE_HASH = "100ba25d6ec9"
VERSION = "2.1.0"
SUMMARY = (
    "An ordered three-color legend maps dot counts 1/2/3 to fill colors for "
    "three equal color-8-walled chambers; chamber order is independently varied."
)

INVARIANTS = [
    "row 0 has exactly three distinct legend colors at columns 1, 2, 3",
    "legend colors are 2..9; color 8 may serve both as wall and legend color",
    "row 1, the last row, and four chamber-boundary columns are color 8",
    "three equal chamber interiors contain only 0 and color-1 dots",
    "each chamber retains one connected zero region touching every dot",
    "left-to-right dot counts are a permutation of 1, 2, 3",
]

COUNT_ORDERS = ("123", "132", "213", "231", "312", "321")
PALETTE_KINDS = ("wall_excluded", "wall_shared")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "ch_h": {
        "type": "int",
        "default": "scheduled 5..9 with frequent canonical value 6",
        "valid": "5..9",
    },
    "ch_w": {
        "type": "int",
        "default": "scheduled 3..5 with frequent canonical value 3",
        "valid": "3..5",
    },
    "palette_kind": {
        "type": "str",
        "default": "five-slot schedule covering both contextual roles of color 8",
        "valid": "wall_excluded|wall_shared",
    },
    "count_order": {
        "type": "str",
        "default": "six-slot permutation schedule",
        "valid": "123|132|213|231|312|321",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

_INT_DOMAINS = {
    "ch_h": tuple(range(5, 10)),
    "ch_w": tuple(range(3, 6)),
}
_STR_DOMAINS = {
    "palette_kind": PALETTE_KINDS,
    "count_order": COUNT_ORDERS,
}
_NON_WALL_LEGEND = (2, 3, 4, 5, 6, 7, 9)
# Period five deliberately de-correlates palette role from the six count orders.
_PALETTE_SCHEDULE = (
    "wall_excluded",
    "wall_shared",
    "wall_excluded",
    "wall_shared",
    "wall_shared",
)
# Each band retains the complete domain.  Half of the twelve slots are
# canonical 6x3 chamber profiles; the other half cover every advertised height
# and width.  This clears the pinned 25% canonical-envelope floor without
# narrowing exact overrides or sacrificing noncanonical count-order witnesses.
_DIMENSION_SCHEDULES = {
    None: (
        (6, 3), (6, 3), (7, 5), (8, 4),
        (6, 3), (6, 3), (5, 3), (7, 4),
        (6, 3), (6, 3), (9, 3), (5, 5),
    ),
    "easy": (
        (6, 3), (6, 3), (6, 4), (5, 5),
        (6, 3), (6, 3), (5, 4), (8, 3),
        (6, 3), (6, 3), (7, 5), (9, 3),
    ),
    "medium": (
        (6, 3), (6, 3), (5, 5), (8, 3),
        (6, 3), (6, 3), (7, 3), (5, 4),
        (6, 3), (6, 3), (9, 4), (6, 5),
    ),
    "hard": (
        (6, 3), (6, 3), (8, 5), (9, 4),
        (6, 3), (6, 3), (9, 3), (8, 4),
        (6, 3), (6, 3), (7, 4), (5, 5),
    ),
}


def _validate_request(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, domain in _INT_DOMAINS.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if value not in domain:
            raise ValueError(f"{name}={value} outside {domain[0]}..{domain[-1]}")
    for name, domain in _STR_DOMAINS.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not str:
            raise TypeError(f"{name} must be a string, not {type(value).__name__}")
        if value not in domain:
            raise ValueError(f"{name}={value!r} not in {domain}")


def _scheduled_axis(ctx, name: str, domain: tuple[Any, ...], scheduled: Any) -> Any:
    """Honor exact overrides while recording deterministic curriculum defaults."""
    value = ctx.draw_choice(name, domain)
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return value
    # GenCtx has no public setter for a scheduled value.  _record is the same
    # provenance path used by typed draws and is isolated here for later migration.
    return ctx._record(name, scheduled, from_override=False)


def _default_axes(sample_index: int, difficulty: str | None) -> tuple[int, int, str, str]:
    dimensions = _DIMENSION_SCHEDULES[difficulty]
    ch_h, ch_w = dimensions[int(sample_index) % len(dimensions)]
    palette_kind = _PALETTE_SCHEDULE[int(sample_index) % len(_PALETTE_SCHEDULE)]
    count_order = COUNT_ORDERS[int(sample_index) % len(COUNT_ORDERS)]
    return ch_h, ch_w, palette_kind, count_order


def _legend(ctx, palette_kind: str) -> list[int]:
    rng = ctx.draw_rng("legend")
    if palette_kind == "wall_shared":
        colors = rng.sample(_NON_WALL_LEGEND, 2) + [8]
        rng.shuffle(colors)
        return colors
    return rng.sample(_NON_WALL_LEGEND, 3)


def _wall_columns(ch_w: int, width: int) -> tuple[int, int, int, int]:
    return (0, ch_w + 1, 2 * ch_w + 2, width - 1)


def _authority_safe_dot_cells(
    rng,
    rows: tuple[int, ...],
    cols: tuple[int, ...],
    count: int,
    *,
    force_same_row_pair: bool,
) -> set[tuple[int, int]]:
    """Choose dots without splitting the Racket authority's zero region."""
    positions = tuple((row, col) for row in rows for col in cols)
    if force_same_row_pair:
        if count != 2:
            raise ValueError("same-row witness is defined only for the two-dot chamber")
        row = rng.choice(rows)
        dots = {(row, col) for col in rng.sample(cols, 2)}
        return dots

    for _attempt in range(100):
        dots = set(rng.sample(positions, count))
        zero_cells = set(positions) - dots
        if _zero_components(zero_cells) != 1:
            continue
        if all(
            any(
                point in zero_cells
                for point in (
                    (row - 1, col),
                    (row + 1, col),
                    (row, col - 1),
                    (row, col + 1),
                )
            )
            for row, col in dots
        ):
            return dots
    raise RuntimeError("failed to sample an authority-safe chamber dot layout")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_h, default_w, default_palette, default_order = _default_axes(
        int(sample_index), difficulty
    )
    ch_h = int(_scheduled_axis(ctx, "ch_h", _INT_DOMAINS["ch_h"], default_h))
    ch_w = int(_scheduled_axis(ctx, "ch_w", _INT_DOMAINS["ch_w"], default_w))
    palette_kind = str(
        _scheduled_axis(ctx, "palette_kind", PALETTE_KINDS, default_palette)
    )
    count_order = str(
        _scheduled_axis(ctx, "count_order", COUNT_ORDERS, default_order)
    )

    height = ch_h + 3
    width = 3 * ch_w + 4
    grid = full_grid(height, width, 0)
    legend = _legend(ctx, palette_kind)
    for index, color in enumerate(legend, start=1):
        grid[0][index] = color

    walls = _wall_columns(ch_w, width)
    for col in range(width):
        grid[1][col] = 8
        grid[-1][col] = 8
    for row in range(1, height):
        for col in walls:
            grid[row][col] = 8

    for chamber, count_char in enumerate(count_order):
        # Keep each chamber's zero background connected.  The selected Racket
        # authority operates on connected zero regions, not on wall rectangles
        # directly; arbitrary dots can isolate a corner and produce a spurious
        # second fill.  Even-indexed examples deliberately place the two dots
        # on one row, refuting the canonical-fitting occupied-row shortcut.
        rng = ctx.draw_rng(f"dots_{chamber}")
        count = int(count_char)
        dots = _authority_safe_dot_cells(
            rng,
            tuple(range(2, height - 1)),
            tuple(range(walls[chamber] + 1, walls[chamber + 1])),
            count,
            force_same_row_pair=(count == 2 and int(sample_index) % 2 == 0),
        )
        for row, col in dots:
            grid[row][col] = 1
    return grid


def _zero_components(cells: set[tuple[int, int]]) -> int:
    remaining = set(cells)
    components = 0
    while remaining:
        components += 1
        stack = [remaining.pop()]
        while stack:
            row, col = stack.pop()
            for point in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if point in remaining:
                    remaining.remove(point)
                    stack.append(point)
    return components


def _parse_grid(grid: Any) -> tuple[dict[str, Any] | None, list[str]]:
    """Return observable axes plus short structural diagnostics; never raise."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a non-empty row sequence"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return None, ["every row must be a sequence"]
    width = len(grid[0])
    if width == 0:
        return None, ["grid rows must be non-empty"]
    if any(len(row) != width for row in grid):
        return None, ["grid must be rectangular"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return None, ["cells must be integer ARC colors 0..9"]

    height = len(grid)
    ch_h = height - 3
    errors: list[str] = []
    if ch_h not in _INT_DOMAINS["ch_h"]:
        errors.append(f"height {height} does not encode ch_h 5..9")
    if (width - 4) % 3:
        errors.append(f"width {width} does not encode three equal chambers")
        return None, errors
    ch_w = (width - 4) // 3
    if ch_w not in _INT_DOMAINS["ch_w"]:
        errors.append(f"width {width} does not encode ch_w 3..5")
    if errors:
        return None, errors

    legend = tuple(grid[0][1:4])
    if len(set(legend)) != 3 or any(color not in range(2, 10) for color in legend):
        errors.append(f"legend must be three distinct colors 2..9, got {list(legend)}")
    if any(
        value != 0
        for col, value in enumerate(grid[0])
        if col not in (1, 2, 3)
    ):
        errors.append("row 0 has a nonzero cell outside legend columns 1..3")

    walls = _wall_columns(ch_w, width)
    if any(value != 8 for value in grid[1]):
        errors.append("row 1 is not a complete color-8 wall")
    if any(value != 8 for value in grid[-1]):
        errors.append("last row is not a complete color-8 wall")
    if any(
        grid[row][col] != 8
        for row in range(1, height)
        for col in walls
    ):
        errors.append("one or more vertical chamber-wall cells are not color 8")

    counts: list[int] = []
    for chamber in range(3):
        positions = [
            (row, col)
            for row in range(2, height - 1)
            for col in range(walls[chamber] + 1, walls[chamber + 1])
        ]
        values = [grid[row][col] for row, col in positions]
        if any(value not in (0, 1) for value in values):
            errors.append(
                f"chamber {chamber + 1} contains a color other than background 0 or dot 1"
            )
        zero_cells = {point for point, value in zip(positions, values) if value == 0}
        dot_cells = {point for point, value in zip(positions, values) if value == 1}
        counts.append(len(dot_cells))
        components = _zero_components(zero_cells) if zero_cells else 0
        if components != 1:
            errors.append(
                f"chamber {chamber + 1} must retain one connected zero region, got {components}"
            )
        for row, col in dot_cells:
            if not any(
                point in zero_cells
                for point in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
            ):
                errors.append(
                    f"chamber {chamber + 1} has a dot not adjacent to its zero region"
                )
                break
    if sorted(counts) != [1, 2, 3]:
        errors.append(f"dot counts must be a permutation of 1,2,3, got {counts}")

    if errors:
        return None, errors
    return {
        "ch_h": ch_h,
        "ch_w": ch_w,
        "palette_kind": "wall_shared" if 8 in legend else "wall_excluded",
        "count_order": "".join(str(count) for count in counts),
    }, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete ordinary input grammar; metadata never waives it."""
    del difficulty, meta
    _state, errors = _parse_grid(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept the canonical 9x13 profile while allowing either canonical palette role."""
    state, errors = _parse_grid(grid)
    if errors:
        return errors
    assert state is not None
    if (state["ch_h"], state["ch_w"]) != (6, 3):
        return [
            "strict canonical profile requires ch_h=6 and ch_w=3 "
            f"(got {state['ch_h']} and {state['ch_w']})"
        ]
    return []


def observe_overrides(grid) -> dict[str, Any]:
    state, errors = _parse_grid(grid)
    if errors or state is None:
        raise ValueError("invalid chamber input: " + "; ".join(errors))
    return state


def _fill_by_indices(grid, indices: tuple[int, int, int]) -> list[list[int]]:
    state = observe_overrides(grid)
    out = deepcopy(grid)
    legend = grid[0][1:4]
    ch_w = int(state["ch_w"])
    walls = _wall_columns(ch_w, len(grid[0]))
    for chamber, legend_index in enumerate(indices):
        for row in range(2, len(grid) - 1):
            for col in range(walls[chamber] + 1, walls[chamber + 1]):
                out[row][col] = legend[legend_index]
    return out


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python mirror of the selected Racket rule for tests and rivals."""
    state = observe_overrides(grid)
    indices = tuple(int(count) - 1 for count in state["count_order"])
    return _fill_by_indices(grid, indices)


def _position_only(grid) -> list[list[int]]:
    """Plausible shortcut: color chambers by left-to-right position."""
    return _fill_by_indices(grid, (0, 1, 2))


def _occupied_rows(grid) -> list[list[int]]:
    """Plausible shortcut: use the number of rows containing dots."""
    state = observe_overrides(grid)
    ch_w = int(state["ch_w"])
    walls = _wall_columns(ch_w, len(grid[0]))
    indices = []
    for chamber in range(3):
        occupied = {
            row
            for row in range(2, len(grid) - 1)
            for col in range(walls[chamber] + 1, walls[chamber + 1])
            if grid[row][col] == 1
        }
        if len(occupied) not in (1, 2, 3):
            raise ValueError(
                f"occupied-row shortcut is undefined for {len(occupied)} rows"
            )
        indices.append(len(occupied) - 1)
    return _fill_by_indices(grid, tuple(indices))


def _noncanonical_count_order(grid) -> bool:
    try:
        return observe_overrides(grid)["count_order"] != "123"
    except (TypeError, ValueError):
        return False


def _wall_shared_palette(grid) -> bool:
    try:
        return observe_overrides(grid)["palette_kind"] == "wall_shared"
    except (TypeError, ValueError):
        return False


def _same_row_dot_pair(grid) -> bool:
    try:
        state = observe_overrides(grid)
    except (TypeError, ValueError):
        return False
    ch_w = int(state["ch_w"])
    walls = _wall_columns(ch_w, len(grid[0]))
    for chamber in range(3):
        dots = [
            (row, col)
            for row in range(2, len(grid) - 1)
            for col in range(walls[chamber] + 1, walls[chamber + 1])
            if grid[row][col] == 1
        ]
        if len({row for row, _col in dots}) < len(dots):
            return True
    return False


SEMANTIC_WITNESSES = {
    "noncanonical_count_order": _noncanonical_count_order,
    "same_row_dot_pair": _same_row_dot_pair,
    "wall_shared_palette": _wall_shared_palette,
}
BRANCH_WITNESSES = ("wall_shared_palette",)
SEMANTIC_RIVALS = {
    "position_only": _position_only,
    "occupied_rows": _occupied_rows,
}
WITNESS_RIVALS = {
    "noncanonical_count_order": ("position_only",),
    "same_row_dot_pair": ("occupied_rows",),
}
CANONICAL_SHORTCUTS = {
    "position_only": _position_only,
    "occupied_rows": _occupied_rows,
}
LESSON_COMPETITORS = {
    "position_only": _position_only,
    "occupied_rows": _occupied_rows,
}


def _labeled_pair_errors(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input invalid: {'; '.join(errors)}"]
    try:
        expected = rule_mirror(pair["input"])
    except (TypeError, ValueError) as exc:
        return [f"{label} rule mirror failed: {exc}"]
    if pair["output"] != expected:
        return [f"{label} output does not match the dot-count rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Require lawful labels and demonstrations that refute the canonical shortcut."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)):
        return ["demos must be a sequence of labeled pairs"]
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(
            f"need at least {EXAMPLES_NEEDED} demonstrations, got {len(demos)}"
        )
    for index, demo in enumerate(demos):
        reasons.extend(_labeled_pair_errors(demo, f"demo {index}"))
    reasons.extend(_labeled_pair_errors(query, "query"))
    if reasons:
        return reasons

    if not any(_wall_shared_palette(demo["input"]) for demo in demos):
        reasons.append(
            "demonstrations never show color 8 serving as a legend color"
        )
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            reasons.append(f"{name} fits every demonstration; include its declared witness")
    return reasons
