"""Generator for ARC task 875ce5d835db: read column markers as a row.

The selected Racket rule scans columns left-to-right, takes the unique nonzero
marker from each active column, skips empty columns, and emits the colors as a
one-row grid.  The curriculum deliberately varies marker count because all five
canonical inputs contain exactly four markers, leaving a fixed-width-four rival
unfalsified by canonical data alone.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "875ce5d835db"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "d02a970277c5"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "On a 0-background grid, three to six colored cells occupy distinct "
    "columns, with exactly one marker in every active column and at least two "
    "empty columns. Scan columns from left to right, append each marker color, "
    "skip empty columns, and emit the resulting sequence as a one-row grid. "
    "A four-slot schedule varies marker count and repeated-color structure so "
    "every three-demo lesson refutes fixed-width, row-order, sorted-color, "
    "deduplication, and include-empty-column shortcuts. Every fourth draw is "
    "anchored to a canonical (height, width, palette-size) profile."
)

INVARIANTS = [
    "background is color 0 and every nonzero cell is an ARC color 1..9",
    "three to six active columns each contain exactly one marker",
    "at least two columns are empty and at least one empty column lies between markers",
    "the intended output is the active-column colors in left-to-right order",
    "ordinary draws make column order differ from row order and from sorted-color order",
    "the canonical Racket program, not the Python audit mirror, is output authority",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-anchor / difficulty-aware schedule",
        "valid": "5..10",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-anchor / difficulty-aware schedule",
        "valid": "8..14",
    },
    "marker_count": {
        "type": "int",
        "default": "four-slot schedule 4|3|5|6",
        "valid": "3..6",
    },
    "color_mode": {
        "type": "str",
        "default": "four-slot schedule distinct|repeat|distinct|repeat",
        "valid": "distinct|repeat",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_CANONICAL_DIM_PROFILES: tuple[tuple[int, int], ...] = (
    (5, 8),
    (6, 9),
    (6, 11),
    (7, 10),
    (8, 12),
)
_BAND_OFFSETS = {None: 1, "easy": 0, "medium": 1, "hard": 2}
_NONANCHOR_DIMS = {
    "easy": ((5, 8), (6, 9), (6, 10), (7, 11)),
    "medium": ((6, 9), (7, 10), (8, 11), (8, 12), (9, 13)),
    "hard": ((8, 11), (8, 12), (9, 13), (10, 14)),
}
_MARKER_SCHEDULE = (4, 3, 5, 6)
_COLOR_MODE_SCHEDULE = ("distinct", "repeat", "distinct", "repeat")
SCHEDULE_PROFILES = (
    "canonical_four_distinct",
    "three_with_repeat",
    "five_distinct",
    "six_with_repeat",
)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Name the four-slot lesson schedule; every 3-wide window sees variation."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> str:
    band = "medium" if difficulty is None else difficulty
    if band not in _NONANCHOR_DIMS:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown!r}")
    for name in ("grid_h", "grid_w", "marker_count"):
        if name in overrides and overrides[name] is not None:
            value = overrides[name]
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name} must be an integer")
    if "color_mode" in overrides and overrides["color_mode"] is not None:
        if not isinstance(overrides["color_mode"], str):
            raise ValueError("color_mode must be a string")
    return band


def _recorded_default_int(ctx, label: str, lo: int, hi: int, default: int) -> int:
    """Consume a full-domain override or record one exact scheduled default."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        value = int(ctx.overrides[label])
        if not lo <= value <= hi:
            raise ValueError(f"{label} override {value} outside [{lo}, {hi}]")
        return int(ctx._record(label, value, from_override=True))
    return int(ctx._record(label, int(default), from_override=False))


def _recorded_default_choice(
    ctx, label: str, options: tuple[str, ...], default: str
) -> str:
    """Consume a finite enum override or record one exact scheduled default."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        value = str(ctx.overrides[label])
        if value not in options:
            raise ValueError(f"{label} override {value!r} not in {options!r}")
        return str(ctx._record(label, value, from_override=True))
    return str(ctx._record(label, default, from_override=False))


def _scheduled_defaults(
    seed: int, sample_index: int, band: str
) -> tuple[int, int, int, str]:
    slot = int(sample_index) % len(_MARKER_SCHEDULE)
    marker_count = _MARKER_SCHEDULE[slot]
    color_mode = _COLOR_MODE_SCHEDULE[slot]
    if slot == 0:
        offset = _BAND_OFFSETS[band]
        profile_index = (int(seed) + int(sample_index) // 4 + offset) % len(
            _CANONICAL_DIM_PROFILES
        )
        h, w = _CANONICAL_DIM_PROFILES[profile_index]
    else:
        options = _NONANCHOR_DIMS[band]
        index = (int(seed) + int(sample_index) + _BAND_OFFSETS[band]) % len(options)
        h, w = options[index]
    return h, w, marker_count, color_mode


def _draw_columns(w: int, marker_count: int, rng) -> list[int]:
    """Choose active columns with a visible internal skipped-column witness."""
    for _ in range(256):
        columns = sorted(rng.sample(range(w), marker_count))
        if columns[-1] - columns[0] + 1 > marker_count:
            return columns
    raise RuntimeError("could not place marker columns with an internal gap")


def _draw_colors(marker_count: int, color_mode: str, rng) -> list[int]:
    if color_mode == "distinct":
        colors = rng.sample(range(1, 10), marker_count)
    else:
        unique = rng.sample(range(1, 10), marker_count - 1)
        colors = unique + [unique[rng.randrange(len(unique))]]
        rng.shuffle(colors)
    # Refute the sorted-colors shortcut on every ordinary draw.
    if colors == sorted(colors):
        colors = list(reversed(colors))
    return colors


def _draw_rows(h: int, columns: list[int], colors: list[int], rng) -> list[int]:
    """Place rows so top-to-bottom reading disagrees with column reading."""
    count = len(columns)
    for _ in range(256):
        rows = [rng.randrange(h) for _ in range(count)]
        if len(set(rows)) < 2:
            continue
        row_order = sorted(range(count), key=lambda i: (rows[i], columns[i]))
        if row_order == list(range(count)):
            continue
        if [colors[i] for i in row_order] == colors:
            continue
        return rows
    raise RuntimeError("could not construct a row-order discriminator")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    default_h, default_w, default_count, default_mode = _scheduled_defaults(
        int(seed), int(sample_index), band
    )
    h = _recorded_default_int(ctx, "grid_h", 5, 10, default_h)
    w = _recorded_default_int(ctx, "grid_w", 8, 14, default_w)
    marker_count = _recorded_default_int(ctx, "marker_count", 3, 6, default_count)
    color_mode = _recorded_default_choice(
        ctx, "color_mode", ("distinct", "repeat"), default_mode
    )

    layout_rng = ctx.draw_rng(
        f"layout|h={h}|w={w}|count={marker_count}|mode={color_mode}"
    )
    columns = _draw_columns(w, marker_count, layout_rng)
    colors = _draw_colors(marker_count, color_mode, layout_rng)
    rows = _draw_rows(h, columns, colors, layout_rng)

    grid = full_grid(h, w, 0)
    for row, col, color in zip(rows, columns, colors):
        grid[row][col] = color

    errors = strict_canonical_like(grid)
    if errors:
        raise AssertionError("generated invalid teaching scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    for label, requested in ctx.recorded_draws().items():
        if label in AXES and observed.get(label) != requested:
            raise AssertionError(
                f"axis {label!r}: requested/drawn {requested!r}, "
                f"observed {observed.get(label)!r}"
            )
    return grid


def _coerce_grid(grid) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["grid rows must be nonempty"]
    width = len(grid[0])
    converted: list[list[int]] = []
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        out_row: list[int] = []
        for value in row:
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                out_row.append(0)
            else:
                out_row.append(value)
        converted.append(out_row)
    return (None, errors) if errors else (converted, [])


def _analyze(grid) -> dict[str, Any]:
    normalized, errors = _coerce_grid(grid)
    if errors or normalized is None:
        return {"errors": errors}
    h, w = len(normalized), len(normalized[0])
    if not 5 <= h <= 10:
        errors.append(f"grid height {h} outside 5..10")
    if not 8 <= w <= 14:
        errors.append(f"grid width {w} outside 8..14")

    columns: list[int] = []
    rows: list[int] = []
    colors: list[int] = []
    for col in range(w):
        hits = [(row, normalized[row][col]) for row in range(h) if normalized[row][col] != 0]
        if len(hits) > 1:
            errors.append(f"column {col} contains {len(hits)} markers; expected at most one")
        elif hits:
            row, color = hits[0]
            columns.append(col)
            rows.append(row)
            colors.append(color)

    marker_count = len(columns)
    if not 3 <= marker_count <= 6:
        errors.append(f"expected 3..6 active columns, got {marker_count}")
    if w - marker_count < 2:
        errors.append("at least two empty columns are required")
    if marker_count and columns[-1] - columns[0] + 1 == marker_count:
        errors.append("active columns are contiguous; an internal skipped column is required")
    if marker_count and len(set(rows)) < 2:
        errors.append("markers must occupy at least two different rows")

    color_mode = (
        "distinct" if colors and len(set(colors)) == len(colors) else "repeat"
    )
    return {
        "errors": errors,
        "grid": normalized,
        "grid_h": h,
        "grid_w": w,
        "marker_count": marker_count,
        "columns": columns,
        "rows": rows,
        "colors": colors,
        "color_mode": color_mode,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task input grammar and exact override realization."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = observe_overrides(grid)
            for axis in AXES:
                if axis in requested and requested[axis] is not None:
                    if requested[axis] != observed[axis]:
                        errors.append(
                            f"override {axis}={requested[axis]!r} realized as "
                            f"{observed[axis]!r}"
                        )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require the structural grammar plus decisive shortcut discriminators."""
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    colors = analysis["colors"]
    if colors == sorted(colors):
        errors.append("column-order colors equal sorted-color order")
    row_order = sorted(
        range(analysis["marker_count"]),
        key=lambda i: (analysis["rows"][i], analysis["columns"][i]),
    )
    row_colors = [colors[index] for index in row_order]
    if row_colors == colors:
        errors.append("top-to-bottom marker order equals left-to-right column order")
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact declared axis from a valid returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe invalid scene: " + "; ".join(analysis["errors"]))
    return {name: analysis[name] for name in AXES}


def _truth(grid) -> list[list[int]]:
    """Pure Python audit mirror; the canonical Racket rule remains authoritative."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid marker scene: " + "; ".join(analysis["errors"]))
    return [list(analysis["colors"])]


def _rival_row_order(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    order = sorted(
        range(analysis["marker_count"]),
        key=lambda i: (analysis["rows"][i], analysis["columns"][i]),
    )
    return [[analysis["colors"][index] for index in order]]


def _rival_include_empty_columns(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    by_column = dict(zip(analysis["columns"], analysis["colors"]))
    return [[by_column.get(col, 0) for col in range(analysis["grid_w"])]]


def _rival_sorted_colors(grid) -> list[list[int]]:
    return [sorted(_analyze(grid)["colors"])]


def _rival_fixed_width_four(grid) -> list[list[int]]:
    colors = list(_analyze(grid)["colors"])
    return [(colors + [0, 0, 0, 0])[:4]]


def _rival_deduplicate(grid) -> list[list[int]]:
    colors = _analyze(grid)["colors"]
    return [list(dict.fromkeys(colors))]


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "read_markers_top_to_bottom": _rival_row_order,
    "include_empty_columns_as_zero": _rival_include_empty_columns,
    "sort_marker_colors": _rival_sorted_colors,
    "always_emit_four_slots": _rival_fixed_width_four,
    "deduplicate_repeated_colors": _rival_deduplicate,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _witness_empty_columns(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["marker_count"] < analysis["grid_w"]


def _witness_row_order(grid) -> bool:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return False
    order = sorted(
        range(analysis["marker_count"]),
        key=lambda i: (analysis["rows"][i], analysis["columns"][i]),
    )
    return [analysis["colors"][index] for index in order] != analysis["colors"]


def _witness_unsorted(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["colors"] != sorted(analysis["colors"])


def _witness_non_four(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["marker_count"] != 4


def _witness_repeat(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["color_mode"] == "repeat"


SEMANTIC_WITNESSES = {
    "empty_columns_are_skipped": _witness_empty_columns,
    "column_order_differs_from_row_order": _witness_row_order,
    "column_order_differs_from_sorted_colors": _witness_unsorted,
    "marker_count_is_not_always_four": _witness_non_four,
    "repeated_colors_are_preserved": _witness_repeat,
}
WITNESS_RIVALS = {
    "empty_columns_are_skipped": ["include_empty_columns_as_zero"],
    "column_order_differs_from_row_order": ["read_markers_top_to_bottom"],
    "column_order_differs_from_sorted_colors": ["sort_marker_colors"],
    "marker_count_is_not_always_four": ["always_emit_four_slots"],
    "repeated_colors_are_preserved": ["deduplicate_repeated_colors"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Every three-demo window must eliminate every named plausible rival."""
    del query
    reasons: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named shortcut survives all demonstrations: {name}")
    return reasons


def negative_recombination_fixture() -> list[list[int]]:
    """Malformed fixture: a second marker of a new color is added to one column."""
    grid = generate(94117, 1, difficulty="medium")
    out = deepcopy(grid)
    analysis = _analyze(grid)
    column = analysis["columns"][0]
    occupied_row = analysis["rows"][0]
    replacement_color = next(
        color for color in range(1, 10) if color not in set(analysis["colors"])
    )
    row = next(r for r in range(analysis["grid_h"]) if r != occupied_row)
    out[row][column] = replacement_color
    return out
