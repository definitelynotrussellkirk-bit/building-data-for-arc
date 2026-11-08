"""Constructive generator for ARC task 4238cc89338a.

The input contains exactly one blue (1) object and one red (2) object.  Let the
blue object's bounding-box row counts be ``B`` and the red object's bounding-
box column counts be ``R``.  The output has ``len(B)`` rows and ``len(R)``
columns, with color 8 at (r, c) exactly when ``c < B[r]`` and ``r < R[c]``.

The ordinary two-slot semantic schedule alternates between row-convex blue
objects and a deliberate counterexample to the strongest simple rival that
fits all canonical demonstrations: using each blue row's occupied *span*
instead of its number of cells.  The ten-slot outer schedule also guarantees
support for both canonical canvas profiles in every difficulty band.
"""
from __future__ import annotations

from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4238cc89338a"
TASK_ID = GENERATOR_ID
RULE_HASH = "e8d6ce4b7903"
VERSION = "3.0.0"

SUMMARY = (
    "Exactly one blue object supplies per-row cell counts and exactly one red "
    "object supplies per-column cell counts. The output is their color-8 "
    "threshold intersection. A cyclic curriculum includes blue rows with "
    "internal gaps, refuting the canonical-fitting row-span shortcut."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.10
# The declared input grammar realizes exactly 39 different output matrices.
# The ordinary seed/index schedule covers all 39 in the standard 24x6 probe.
EXPECTED_OUTPUT_CODOMAIN = 39
_SCHEDULE_PERIOD = 10
PROFILE_MODES = ("compact", "counterexample")
SCHEDULE_PROFILES = tuple(
    f"slot-{slot}:{'counterexample' if slot % 2 == 0 else 'compact'}"
    for slot in range(_SCHEDULE_PERIOD)
)

INVARIANTS = [
    "the input is a rectangular 10..22 by 14..22 grid over colors 0,1,2",
    "there is exactly one 4-connected blue object and one 4-connected red object",
    "each object has 5..9 cells and the two objects have a one-cell moat",
    "output rows are blue bounding-box row counts; output columns are red bounding-box column counts",
    "every three consecutive ordinary samples include a row-span counterexample",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "10-slot difficulty-aware schedule; slot 0 is canonical 10x18 and slot 1 is canonical 11x20",
        "valid": "10..22",
        "doc": "exact returned input height",
    },
    "grid_w": {
        "type": "int",
        "default": "10-slot difficulty-aware schedule; slot 0 is canonical 10x18 and slot 1 is canonical 11x20",
        "valid": "14..22",
        "doc": "exact returned input width",
    },
    "blue_size": {
        "type": "int",
        "default": "39-state output-coverage schedule over 5..9",
        "valid": "5..9",
        "doc": "exact number of blue cells",
    },
    "red_size": {
        "type": "int",
        "default": "39-state output-coverage schedule over 5..9",
        "valid": "5..9",
        "doc": "exact number of red cells",
    },
    "profile_mode": {
        "type": "str",
        "default": "counterexample on even sample indices, compact on odd indices",
        "valid": "compact|counterexample",
        "doc": "whether the blue object contains a semantically effective internal row gap",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Row-convex, connected shapes.  Every red base has width >= 3, which makes the
# counterexample's top-row gap observable in the derived output.
_COMPACT_BASES: dict[int, tuple[tuple[int, int], ...]] = {
    5: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
    6: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    7: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2)),
    8: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3)),
    9: tuple((r, c) for r in range(3) for c in range(3)),
}

# All members preserve the missing top-middle cell.  Therefore top row count 2
# and span 3 disagree at output column 2, while any lawful red base makes its
# third column nonempty.
_COUNTEREXAMPLE_BASES: dict[int, tuple[tuple[int, int], ...]] = {
    5: ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
    6: ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0)),
    7: ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),
    8: ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)),
    9: ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2), (3, 1)),
}


def _normalize_band(difficulty: Any) -> str:
    if difficulty in (None, "default", "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> str:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative integer (not bool)")
    band = _normalize_band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    for label in ("grid_h", "grid_w", "blue_size", "red_size"):
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise TypeError(f"{label} must be an integer (not bool)")
    value = overrides.get("profile_mode")
    if value is not None and not isinstance(value, str):
        raise TypeError("profile_mode must be a string")
    return band


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Name the exact branch of the declared ten-slot ordinary schedule."""
    del seed
    _normalize_band(difficulty)
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative integer (not bool)")
    return SCHEDULE_PROFILES[sample_index % _SCHEDULE_PERIOD]


def _scheduled_dimensions(ctx, sample_index: int, band: str) -> tuple[int, int]:
    slot = sample_index % _SCHEDULE_PERIOD
    if slot == 0:
        h_options, w_options = (10,), (18,)
    elif slot == 1:
        h_options, w_options = (11,), (20,)
    elif slot == 2:
        h_options, w_options = (10,), (18,)
    else:
        h_range, w_range = {
            "easy": ((10, 14), (14, 18)),
            "medium": ((12, 18), (16, 20)),
            "hard": ((16, 22), (18, 22)),
        }[band]
        h_options = tuple(range(h_range[0], h_range[1] + 1))
        w_options = tuple(range(w_range[0], w_range[1] + 1))
    return (
        _draw_exact_int(ctx, "grid_h", 10, 22, h_options),
        _draw_exact_int(ctx, "grid_w", 14, 22, w_options),
    )


def _draw_exact_int(ctx, label: str, lo: int, hi: int, defaults: tuple[int, ...]) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_choice(label, defaults)


def _draw_exact_choice(ctx, label: str, options: tuple[str, ...], default: str) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _size_options(band: str) -> tuple[int, ...]:
    return {
        "easy": (5, 6),
        "medium": (5, 6, 7, 8),
        "hard": (7, 8, 9),
    }[band]


def _normalized(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _shape_variant(
    base: tuple[tuple[int, int], ...], *, horizontal: bool, vertical: bool
) -> tuple[tuple[int, int], ...]:
    height = max(r for r, _ in base) + 1
    width = max(c for _, c in base) + 1
    return _normalized(
        (
            height - 1 - r if vertical else r,
            width - 1 - c if horizontal else c,
        )
        for r, c in base
    )


def _shape_row_counts(shape: tuple[tuple[int, int], ...]) -> tuple[int, ...]:
    height = max(r for r, _ in shape) + 1
    return tuple(sum(r == row for r, _ in shape) for row in range(height))


def _shape_column_counts(shape: tuple[tuple[int, int], ...]) -> tuple[int, ...]:
    width = max(c for _, c in shape) + 1
    return tuple(sum(c == column for _, c in shape) for column in range(width))


def _derived_signature(blue, red) -> tuple[tuple[int, ...], ...]:
    blue_rows = _shape_row_counts(blue)
    red_columns = _shape_column_counts(red)
    return tuple(
        tuple(
            8 if column < blue_rows[row] and row < red_columns[column] else 0
            for column in range(len(red_columns))
        )
        for row in range(len(blue_rows))
    )


def _recipe_catalog(mode: str) -> tuple[tuple[int, bool, int, bool], ...]:
    """One representative recipe per distinct output in a semantic mode.

    A recipe stores (blue_size, blue_vertical, red_size, red_horizontal).
    Blue horizontal and red vertical reflection are output-preserving nuisance
    factors and remain independently randomized during materialization.
    """
    blue_bases = _COUNTEREXAMPLE_BASES if mode == "counterexample" else _COMPACT_BASES
    signatures: dict[tuple[tuple[int, ...], ...], tuple[int, bool, int, bool]] = {}
    for blue_size, blue_base in blue_bases.items():
        blue_verticals = (False,) if mode == "counterexample" else (False, True)
        for blue_vertical in blue_verticals:
            blue = _shape_variant(
                blue_base, horizontal=False, vertical=blue_vertical
            )
            for red_size, red_base in _COMPACT_BASES.items():
                for red_horizontal in (False, True):
                    red = _shape_variant(
                        red_base, horizontal=red_horizontal, vertical=False
                    )
                    signature = _derived_signature(blue, red)
                    signatures.setdefault(
                        signature,
                        (blue_size, blue_vertical, red_size, red_horizontal),
                    )
    return tuple(signatures[key] for key in sorted(signatures))


_DEFAULT_RECIPES = {
    "compact": _recipe_catalog("compact"),
    "counterexample": _recipe_catalog("counterexample"),
}
assert len(_DEFAULT_RECIPES["compact"]) == 25
assert len(_DEFAULT_RECIPES["counterexample"]) == 19
assert len({
    _derived_signature(
        _shape_variant(
            (_COUNTEREXAMPLE_BASES if mode == "counterexample" else _COMPACT_BASES)[recipe[0]],
            horizontal=False,
            vertical=recipe[1],
        ),
        _shape_variant(
            _COMPACT_BASES[recipe[2]],
            horizontal=recipe[3],
            vertical=False,
        ),
    )
    for mode, catalog in _DEFAULT_RECIPES.items()
    for recipe in catalog
}) == EXPECTED_OUTPUT_CODOMAIN


def _shapes_from_recipe(ctx, mode: str, recipe: tuple[int, bool, int, bool]):
    blue_size, blue_vertical, red_size, red_horizontal = recipe
    blue_bases = _COUNTEREXAMPLE_BASES if mode == "counterexample" else _COMPACT_BASES
    blue = _shape_variant(
        blue_bases[blue_size],
        horizontal=bool(ctx.draw_choice("blue_horizontal_reflection", (0, 1))),
        vertical=blue_vertical,
    )
    red = _shape_variant(
        _COMPACT_BASES[red_size],
        horizontal=red_horizontal,
        vertical=bool(ctx.draw_choice("red_vertical_reflection", (0, 1))),
    )
    return blue_size, red_size, blue, red


def _choose_shapes(ctx, blue_size: int, red_size: int, mode: str):
    if mode == "counterexample":
        # Horizontal reflection preserves the witness in row 0.  Vertical
        # reflection could move the gap below the red profile's active height
        # and turn a syntactic gap into a semantically inert one.
        blue = _shape_variant(
            _COUNTEREXAMPLE_BASES[blue_size],
            horizontal=bool(ctx.draw_choice("blue_horizontal_reflection", (0, 1))),
            vertical=False,
        )
    else:
        blue = _shape_variant(
            _COMPACT_BASES[blue_size],
            horizontal=bool(ctx.draw_choice("blue_horizontal_reflection", (0, 1))),
            vertical=bool(ctx.draw_choice("blue_vertical_reflection", (0, 1))),
        )
    red = _shape_variant(
        _COMPACT_BASES[red_size],
        horizontal=bool(ctx.draw_choice("red_horizontal_reflection", (0, 1))),
        vertical=bool(ctx.draw_choice("red_vertical_reflection", (0, 1))),
    )
    return blue, red


def _shape_bounds(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _constructive_positions(ctx, h: int, w: int, blue, red):
    """Place both bounding boxes side by side with a guaranteed empty column.

    The smallest advertised canvas has twelve interior columns, while the two
    widest supported boxes need at most eight.  Therefore this construction is
    total for every valid override and uses constant memory.
    """
    blue_h, blue_w = _shape_bounds(blue)
    red_h, red_w = _shape_bounds(red)
    rng = ctx.draw_rng("object_placements")
    blue_first = bool(rng.randint(0, 1))
    left_w, right_w = (blue_w, red_w) if blue_first else (red_w, blue_w)
    interior_width = w - 2
    spare = interior_width - left_w - right_w
    if spare < 1:
        raise ValueError("canvas cannot fit two separated object boxes")
    gap = rng.randint(1, spare)
    remaining = spare - gap
    left_col = 1 + rng.randint(0, remaining)
    right_col = left_col + left_w + gap
    blue_top = rng.randint(1, h - blue_h - 1)
    red_top = rng.randint(1, h - red_h - 1)
    if blue_first:
        return (blue_top, left_col), (red_top, right_col)
    return (blue_top, right_col), (red_top, left_col)

def _paint(grid: list[list[int]], shape, position, color: int) -> None:
    top, left = position
    for r, c in shape:
        grid[top + r][left + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    h, w = _scheduled_dimensions(ctx, sample_index, band)
    scheduled_mode = "counterexample" if sample_index % 2 == 0 else "compact"
    profile_mode = _draw_exact_choice(ctx, "profile_mode", PROFILE_MODES, scheduled_mode)
    semantic_override = any(
        label in overrides and overrides[label] is not None
        for label in ("blue_size", "red_size", "profile_mode")
    )
    if semantic_override:
        sizes = _size_options(band)
        blue_size = _draw_exact_int(ctx, "blue_size", 5, 9, sizes)
        red_size = _draw_exact_int(ctx, "red_size", 5, 9, sizes)
        blue, red = _choose_shapes(ctx, blue_size, red_size, profile_mode)
    else:
        catalog = _DEFAULT_RECIPES[profile_mode]
        recipe = catalog[(seed + sample_index) % len(catalog)]
        scheduled_blue_size, scheduled_red_size, blue, red = _shapes_from_recipe(
            ctx, profile_mode, recipe
        )
        blue_size = _draw_exact_int(
            ctx, "blue_size", 5, 9, (scheduled_blue_size,)
        )
        red_size = _draw_exact_int(
            ctx, "red_size", 5, 9, (scheduled_red_size,)
        )
    blue_pos, red_pos = _constructive_positions(ctx, h, w, blue, red)
    grid = full_grid(h, w, 0)
    _paint(grid, blue, blue_pos, 1)
    _paint(grid, red, red_pos, 2)

    errors = self_check(grid)
    if errors:
        raise RuntimeError("internal construction error: " + "; ".join(errors))
    expected = {
        "grid_h": h,
        "grid_w": w,
        "blue_size": blue_size,
        "red_size": red_size,
        "profile_mode": profile_mode,
    }
    actual = observe_overrides(grid)
    if actual != expected:
        raise RuntimeError(f"internal construction mismatch: expected {expected}, observed {actual}")
    if profile_mode == "counterexample" and _blue_row_span(grid) == _intended_output(grid):
        raise RuntimeError("counterexample construction failed to refute blue-row span")
    return [row[:] for row in grid]


def _components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        component = {start}
        stack = [start]
        remaining.remove(start)
        while stack:
            r, c = stack.pop()
            for dr, dc in _CARDINAL:
                point = (r + dr, c + dc)
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    stack.append(point)
        result.append(component)
    return sorted(result, key=min)


def _single_object(grid: list[list[int]], color: int) -> set[tuple[int, int]]:
    components = _components(grid, color)
    if len(components) != 1:
        raise ValueError(f"expected exactly one color-{color} object, found {len(components)}")
    return components[0]


def _profiles(
    cells: Iterable[tuple[int, int]], *, row_span: bool = False
) -> tuple[list[int], list[int]]:
    cells = set(cells)
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    rows: list[int] = []
    for r in range(r0, r1 + 1):
        cols = [c for rr, c in cells if rr == r]
        rows.append(max(cols) - min(cols) + 1 if row_span else len(cols))
    columns = [
        sum((r, c) in cells for r in range(r0, r1 + 1))
        for c in range(c0, c1 + 1)
    ]
    return rows, columns


def _prediction(grid: list[list[int]], *, blue_row_span: bool = False) -> list[list[int]]:
    blue = _single_object(grid, 1)
    red = _single_object(grid, 2)
    blue_rows, _ = _profiles(blue, row_span=blue_row_span)
    _, red_columns = _profiles(red)
    return [
        [
            8 if c < blue_rows[r] and r < red_columns[c] else 0
            for c in range(len(red_columns))
        ]
        for r in range(len(blue_rows))
    ]


def _intended_output(grid: list[list[int]]) -> list[list[int]]:
    return _prediction(grid, blue_row_span=False)


def _blue_row_span(grid: list[list[int]]) -> list[list[int]]:
    """Rival: use occupied blue row spans instead of blue cell counts."""
    return _prediction(grid, blue_row_span=True)


def _has_blue_row_gap(grid: list[list[int]]) -> bool:
    blue = _single_object(grid, 1)
    r0 = min(r for r, _ in blue)
    r1 = max(r for r, _ in blue)
    for r in range(r0, r1 + 1):
        cols = sorted(c for rr, c in blue if rr == r)
        if cols and cols[-1] - cols[0] + 1 > len(cols):
            return True
    return False


def observe_overrides(grid) -> dict[str, int | str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    blue = _single_object(grid, 1)
    red = _single_object(grid, 2)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "blue_size": len(blue),
        "red_size": len(red),
        "profile_mode": "counterexample" if _has_blue_row_gap(grid) else "compact",
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or value not in (0, 1, 2) for row in grid for value in row):
        return ["cells must be integer colors from 0,1,2"]

    errors: list[str] = []
    height = len(grid)
    if not 10 <= height <= 22:
        errors.append(f"grid height {height} outside 10..22")
    if not 14 <= width <= 22:
        errors.append(f"grid width {width} outside 14..22")

    components_by_color: dict[int, set[tuple[int, int]]] = {}
    for color, label in ((1, "blue"), (2, "red")):
        components = _components(grid, color)
        if len(components) != 1:
            errors.append(f"expected exactly one {label} object, found {len(components)}")
            continue
        components_by_color[color] = components[0]
        size = len(components[0])
        if not 5 <= size <= 9:
            errors.append(f"{label} object size {size} outside 5..9")

    if len(components_by_color) == 2:
        if any(
            max(abs(br - rr), abs(bc - rc)) <= 1
            for br, bc in components_by_color[1]
            for rr, rc in components_by_color[2]
        ):
            errors.append("blue and red objects must have a one-cell moat")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Strict generated/canonical support used by the semantic gate."""
    errors = list(self_check(grid))
    if errors:
        return errors
    dimensions = (len(grid), len(grid[0]))
    if dimensions not in ((10, 18), (11, 20)):
        errors.append("strict examples use canonical canvas profiles 10x18 or 11x20")
    return errors


def _blue_row_gap_witness(grid) -> bool:
    try:
        return not self_check(grid) and _has_blue_row_gap(grid) and _blue_row_span(grid) != _intended_output(grid)
    except (TypeError, ValueError, IndexError):
        return False


SEMANTIC_WITNESSES = {"blue_row_gap": _blue_row_gap_witness}
SEMANTIC_RIVALS = {"blue_row_span": _blue_row_span}
WITNESS_RIVALS = {"blue_row_gap": ["blue_row_span"]}
LESSON_COMPETITORS = {"blue_row_span": _blue_row_span}


def lesson_identifiable(demos, query) -> list[str]:
    """Return a warning while the row-span rival still fits every demo."""
    del query
    for pair in demos:
        try:
            prediction = _blue_row_span(pair["input"])
            if prediction != pair["output"]:
                return []
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            return [f"invalid demonstration for blue_row_span check: {type(exc).__name__}: {exc}"]
    return ["blue_row_span fits every demonstration; include a blue-row-gap counterexample"]
