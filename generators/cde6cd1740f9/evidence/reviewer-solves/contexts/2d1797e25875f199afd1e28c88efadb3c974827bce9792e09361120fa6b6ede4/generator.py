"""Semantic generator for ARC task cde6cd1740f9.

Each nonzero input column contains exactly ``k²`` cells for ``k`` in ``{2, 3}``.
Reading that column from bottom to top gives the order of its distinct colors;
the count of each color fills one or more *complete, consecutive* pyramid
layers of widths ``2k-1, 2k-3, ..., 1``.  The output discards input row
positions and paints those layers at the bottom of the grid, centered on the
source column.

Canvas dimensions and pyramid structure are scheduled independently.  Every
eight consecutive ordinary samples cover all four canvases and all four
public structural profiles (small/large pyramid, one/two columns, and
one/two/three colors).  The input rows remain genuinely scattered, so neither
gravity, identity, nor a canvas-template lookup is a viable shortcut.
"""
from __future__ import annotations

from collections import Counter
from math import isqrt
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cde6cd1740f9"
TASK_ID = GENERATOR_ID
VERSION = "4.1.0"
RULE_HASH = "027335bb451f"
EXAMPLES_NEEDED = 8
LESSON_SCHEDULE_PERIOD = 16
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Every active input column contains 4 or 9 scattered colored cells. "
    "Its total determines a 2- or 3-layer odd-width pyramid; its bottom-to-top "
    "distinct-color order and exact color counts determine complete consecutive "
    "layers. The output moves those layers to the grid bottom, centered on the "
    "same column. Canvas and structure vary independently; every eight "
    "consecutive samples cover all four canvases and all four structures."
)

INVARIANTS = [
    "background is color 0 and dimensions match one of the four canonical profiles",
    "there are one or two active columns with pairwise-disjoint output footprints",
    "each active column contains exactly 4 or 9 nonzero cells",
    "bottom-to-top color runs never return to a previously seen color",
    "each color count equals a sum of complete consecutive odd-width layers",
    "ordinary inputs keep the future bottom pyramid rows empty and scatter source rows",
]

PROFILES = ("16x11", "16x13", "21x9", "30x10")
STRUCTURES = (
    "k2_solid",
    "k3_solid",
    "k3_three_color",
    "mixed_k3_k2",
)
LESSON_SCHEDULE = (
    ("16x11", "k2_solid"),
    ("16x13", "k3_solid"),
    ("21x9", "k3_three_color"),
    ("30x10", "mixed_k3_k2"),
    ("21x9", "k2_solid"),
    ("16x11", "k3_solid"),
    ("16x13", "mixed_k3_k2"),
    ("30x10", "k2_solid"),
    ("16x11", "k3_three_color"),
    ("21x9", "k3_solid"),
    ("16x13", "k3_three_color"),
    ("21x9", "mixed_k3_k2"),
    ("30x10", "k3_solid"),
    ("16x13", "k2_solid"),
    ("16x11", "mixed_k3_k2"),
    ("30x10", "k3_three_color"),
)
assert len(LESSON_SCHEDULE) == LESSON_SCHEDULE_PERIOD
assert set(LESSON_SCHEDULE) == {
    (profile, structure) for profile in PROFILES for structure in STRUCTURES
}
PROFILE_DIMS = {
    "16x11": (16, 11),
    "16x13": (16, 13),
    "21x9": (21, 9),
    "30x10": (30, 10),
}
CANONICAL_STRUCTURE_BY_PROFILE = {
    "16x11": "k2_solid",
    "16x13": "k3_solid",
    "21x9": "k3_three_color",
    "30x10": "mixed_k3_k2",
}
PRIMARY_COLORS = tuple(range(1, 10))

AXES = {
    "profile": {
        "type": "str",
        "default": "balanced 16-step canvas-by-structure schedule",
        "valid": "|".join(PROFILES),
    },
    "structure": {
        "type": "str",
        "default": "balanced 16-step canvas-by-structure schedule",
        "valid": "|".join(STRUCTURES),
    },
    "active_columns": {
        "type": "int",
        "default": "2 for mixed_k3_k2, otherwise 1",
        "valid": "1..2",
    },
    "primary_color": {
        "type": "color",
        "default": "scheduled 1..9",
        "valid": "1..9",
    },
    "layout_shift": {
        "type": "int",
        "default": "scheduled 0..2 legal column-position variants",
        "valid": "0..2",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _draw_scheduled(ctx, name: str, domain: Iterable[Any], scheduled: Any, overrides: dict[str, Any]):
    options = tuple(domain)
    if name in overrides and overrides[name] is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (scheduled,))


def _scheduled_profile_structure(sample_index: int, band: str) -> tuple[str, str]:
    """Return one cell of the balanced, rotation-robust lesson schedule."""
    offset = {"easy": 0, "medium": 1, "hard": 2}[band]
    return LESSON_SCHEDULE[(sample_index + offset) % LESSON_SCHEDULE_PERIOD]


def _next_color(color: int, step: int) -> int:
    return ((color - 1 + step) % 9) + 1


def _layout_columns(profile: str, active_columns: int, layout_shift: int) -> tuple[int, ...]:
    layouts = {
        ("16x11", 1): ((4,), (5,), (6,)),
        ("16x11", 2): ((2, 6), (3, 7), (4, 8)),
        ("16x13", 1): ((5,), (6,), (7,)),
        ("16x13", 2): ((2, 8), (3, 9), (4, 10)),
        ("21x9", 1): ((3,), (4,), (5,)),
        ("21x9", 2): ((2, 6), (2, 7), (3, 7)),
        ("30x10", 1): ((2,), (4,), (7,)),
        ("30x10", 2): ((2, 7), (2, 8), (3, 8)),
    }
    try:
        return layouts[(profile, active_columns)][layout_shift]
    except (KeyError, IndexError) as exc:
        raise ValueError(
            f"no layout for profile={profile!r}, active_columns={active_columns}, "
            f"layout_shift={layout_shift}"
        ) from exc


def _column_specs(
    structure: str,
    profile: str,
    active_columns: int,
    primary_color: int,
    layout_shift: int,
):
    """Return ``(center_col, bottom-up layer colors)`` specifications."""
    secondary = _next_color(primary_color, 3)
    tertiary = _next_color(primary_color, 6)
    columns = _layout_columns(profile, active_columns, layout_shift)

    first_column = {
        "k2_solid": (primary_color, primary_color),
        "k3_solid": (primary_color, primary_color, primary_color),
        "k3_three_color": (primary_color, secondary, tertiary),
        "mixed_k3_k2": (primary_color, secondary, secondary),
    }.get(structure)
    if first_column is None:
        raise ValueError(f"unknown structure: {structure!r}")

    colors = (first_column,)
    if active_columns == 2:
        colors += ((tertiary, tertiary),)
    return tuple(zip(columns, colors))


def _layer_widths(k: int) -> tuple[int, ...]:
    return tuple(2 * k - 1 - 2 * index for index in range(k))


def _input_colors_top_to_bottom(layer_colors: tuple[int, ...]) -> list[int]:
    counts: Counter[int] = Counter()
    order: list[int] = []
    for color, width in zip(layer_colors, _layer_widths(len(layer_colors))):
        counts[color] += width
        if color not in order:
            order.append(color)
    result: list[int] = []
    for color in reversed(order):
        result.extend([color] * counts[color])
    return result


def _scattered_rows(ctx, label: str, height: int, k: int, total: int) -> list[int]:
    """Draw source rows above the future pyramid, with visible gaps."""
    candidates = tuple(range(0, height - k))
    if len(candidates) < total + 2:
        raise ValueError("profile has insufficient rows for a scattered source column")
    rng = ctx.draw_rng(label)
    for _ in range(128):
        rows = sorted(rng.sample(candidates, total))
        if rows[-1] - rows[0] >= total + 1:
            return rows
    # Stable deterministic fallback, unreachable for current profiles.
    stride = max(1, (len(candidates) - 1) // (total - 1))
    rows = list(range(0, stride * total, stride))[:total]
    if rows[-1] >= height - k:
        rows = list(candidates[:total])
    return rows


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return a deterministic strict lesson input from the balanced schedule."""
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    scheduled_profile, scheduled_structure = _scheduled_profile_structure(
        sample_index, band
    )
    profile = _draw_scheduled(ctx, "profile", PROFILES, scheduled_profile, overrides)
    structure = _draw_scheduled(
        ctx, "structure", STRUCTURES, scheduled_structure, overrides
    )
    scheduled_columns = 2 if structure == "mixed_k3_k2" else 1
    active_columns = _draw_scheduled(
        ctx, "active_columns", (1, 2), scheduled_columns, overrides
    )
    scheduled_color = PRIMARY_COLORS[(seed + sample_index + len(band)) % len(PRIMARY_COLORS)]
    primary_color = _draw_scheduled(
        ctx, "primary_color", PRIMARY_COLORS, scheduled_color, overrides
    )
    scheduled_layout = (seed // 9 + sample_index // 2 + {"easy": 0, "medium": 1, "hard": 2}[band]) % 3
    layout_shift = _draw_scheduled(
        ctx, "layout_shift", (0, 1, 2), scheduled_layout, overrides
    )

    height, width = PROFILE_DIMS[profile]
    grid = full_grid(height, width, 0)
    for index, (col, layer_colors) in enumerate(
        _column_specs(
            structure,
            profile,
            active_columns,
            primary_color,
            layout_shift,
        )
    ):
        k = len(layer_colors)
        colors = _input_colors_top_to_bottom(layer_colors)
        rows = _scattered_rows(ctx, f"rows_{index}", height, k, len(colors))
        for row, color in zip(rows, colors):
            grid[row][col] = color
    return grid


def _grid_validation(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be non-empty"]
    height, width = len(grid), len(grid[0])
    errors: list[str] = []
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return height, width, ["grid must be rectangular"]
    if (height, width) not in set(PROFILE_DIMS.values()):
        errors.append(
            f"grid dimensions must be one of {tuple(PROFILE_DIMS.values())}, got {(height, width)}"
        )
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be integer ARC colors 0..9")
    return height, width, errors


def _distinct_in_order(values: Iterable[int]) -> tuple[int, ...]:
    result: list[int] = []
    seen: set[int] = set()
    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)
    return tuple(result)


def _compressed_runs(values: Iterable[int]) -> tuple[int, ...]:
    result: list[int] = []
    for value in values:
        if not result or result[-1] != value:
            result.append(value)
    return tuple(result)


def _derive_layer_colors(bottom_values: tuple[int, ...], k: int):
    order = _distinct_in_order(bottom_values)
    counts = Counter(bottom_values)
    if not order:
        raise ValueError("empty active column")
    widths = _layer_widths(k)
    result: list[int] = []
    color_index = 0
    remaining = counts[order[0]]
    for width in widths:
        if remaining <= 0:
            color_index += 1
            if color_index >= len(order):
                raise ValueError("color counts end before all pyramid layers are assigned")
            remaining = counts[order[color_index]]
        result.append(order[color_index])
        remaining -= width
    return tuple(result), order, counts


def _infer_structure(columns: Iterable[dict[str, Any]]) -> str | None:
    columns = tuple(columns)
    if not columns:
        return None
    first = columns[0]
    signature = (first["k"], len(set(first["layer_colors"])))
    return {
        (2, 1): "k2_solid",
        (3, 1): "k3_solid",
        (3, 3): "k3_three_color",
        (3, 2): "mixed_k3_k2",
    }.get(signature)


def _analyze(grid: Any) -> tuple[dict[str, Any], list[str]]:
    height, width, errors = _grid_validation(grid)
    profile = next(
        (name for name, dims in PROFILE_DIMS.items() if dims == (height, width)),
        None,
    )
    info: dict[str, Any] = {
        "height": height,
        "width": width,
        "profile": profile,
    }
    if errors:
        return info, errors

    active = [
        col
        for col in range(width)
        if any(grid[row][col] != 0 for row in range(height))
    ]
    if not 1 <= len(active) <= 2:
        errors.append(f"expected one or two active columns, got {len(active)}")
        return info, errors

    columns: list[dict[str, Any]] = []
    spans: list[tuple[int, int]] = []
    for col in active:
        cells = tuple((row, grid[row][col]) for row in range(height) if grid[row][col])
        total = len(cells)
        k = isqrt(total)
        if k not in (2, 3) or k * k != total:
            errors.append(
                f"column {col} must contain exactly 4 or 9 cells, got {total}"
            )
            continue

        bottom_values = tuple(value for _row, value in reversed(cells))
        runs = _compressed_runs(bottom_values)
        if len(runs) != len(set(runs)):
            errors.append(
                f"column {col} returns to a previously seen color bottom-to-top"
            )

        try:
            layer_colors, color_order, counts = _derive_layer_colors(bottom_values, k)
        except ValueError as exc:
            errors.append(f"column {col}: {exc}")
            continue

        expected_counts: Counter[int] = Counter()
        for color, layer_width in zip(layer_colors, _layer_widths(k)):
            expected_counts[color] += layer_width
        if counts != expected_counts:
            errors.append(
                f"column {col} color counts {dict(counts)} do not partition complete "
                f"consecutive layers {dict(expected_counts)}"
            )

        radius = k - 1
        span = (col - radius, col + radius)
        if span[0] < 0 or span[1] >= width:
            errors.append(f"column {col} pyramid footprint {span} leaves the grid")
        spans.append(span)
        columns.append(
            {
                "col": col,
                "cells": cells,
                "rows": tuple(row for row, _value in cells),
                "total": total,
                "k": k,
                "bottom_values": bottom_values,
                "color_order": color_order,
                "counts": dict(counts),
                "layer_colors": layer_colors,
                "span": span,
            }
        )

    if len(spans) == len(active):
        for left, right in zip(spans, spans[1:]):
            if left[1] >= right[0]:
                errors.append(f"output pyramid footprints overlap: {left} and {right}")

    if columns:
        primary_color = columns[0]["bottom_values"][0]
    else:
        primary_color = None
    structure = _infer_structure(columns)
    if columns and structure is None:
        first = columns[0]
        errors.append(
            "first active column does not match a declared structure: "
            f"k={first['k']}, distinct layer colors="
            f"{len(set(first['layer_colors']))}"
        )
    active_tuple = tuple(active)
    layout_shift = next(
        (
            shift
            for shift in range(3)
            if _layout_columns(profile, len(active), shift) == active_tuple
        ),
        None,
    )
    if layout_shift is None:
        errors.append(
            f"active columns {active_tuple} are not a declared layout for {profile}"
        )
    info.update(
        {
            "active_columns": len(active),
            "active_column_indices": tuple(active),
            "structure": structure,
            "primary_color": primary_color,
            "layout_shift": layout_shift,
            "columns": tuple(columns),
            "palette_size": len({value for row in grid for value in row}),
        }
    )
    return info, errors


def observe_overrides(grid: Any) -> dict[str, Any]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {name: info[name] for name in AXES}


def _requested_axes(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    requested = {name: meta[name] for name in AXES if name in meta}
    nested = meta.get("overrides")
    if isinstance(nested, dict):
        requested.update({name: nested[name] for name in AXES if name in nested})
    return requested


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed grids and grids whose counts cannot encode full layers."""
    del difficulty
    info, errors = _analyze(grid)
    if errors:
        return errors
    for name, requested in _requested_axes(meta).items():
        if requested is not None and info[name] != requested:
            errors.append(f"{name} requested {requested!r}, observed {info[name]!r}")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Enforce the ordinary scattered-input curriculum in addition to grammar."""
    info, errors = _analyze(grid)
    if errors:
        return errors
    for column in info["columns"]:
        k = column["k"]
        rows = column["rows"]
        if any(row >= info["height"] - k for row in rows):
            errors.append(
                f"column {column['col']} occupies rows reserved for its output pyramid"
            )
        if rows[-1] - rows[0] < len(rows) + 1:
            errors.append(f"column {column['col']} source rows are insufficiently scattered")
    return errors


def rule_mirror(grid: Any) -> list[list[int]]:
    """Pure Python parity mirror; the selected Racket rule remains authority."""
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = full_grid(info["height"], info["width"], 0)
    for column in info["columns"]:
        col = column["col"]
        for layer_index, (layer_width, color) in enumerate(
            zip(_layer_widths(column["k"]), column["layer_colors"])
        ):
            row = info["height"] - 1 - layer_index
            start = col - layer_width // 2
            for offset in range(layer_width):
                out_col = start + offset
                if 0 <= out_col < info["width"]:
                    output[row][out_col] = color
    return output


def canonical_profile_signature(grid: Any):
    info, errors = _analyze(grid)
    if errors:
        return None
    return (info["height"], info["width"], info["palette_size"])


def semantic_signature(grid: Any) -> dict[str, Any]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        **observe_overrides(grid),
        "column_sizes": tuple(column["k"] for column in info["columns"]),
        "layer_color_counts": tuple(
            len(set(column["layer_colors"])) for column in info["columns"]
        ),
        "palette_size": info["palette_size"],
        "strict_canonical_like": not strict_canonical_like(grid),
    }


def schedule_profile(seed: int, sample_index: int, difficulty=None):
    del seed
    return _scheduled_profile_structure(sample_index, _band(difficulty))


SCHEDULE_PROFILES = tuple(
    _scheduled_profile_structure(sample_index, "easy")
    for sample_index in range(LESSON_SCHEDULE_PERIOD)
)


def _witness(predicate: Callable[[dict[str, Any]], bool]):
    def wrapped(grid: Any) -> bool:
        info, errors = _analyze(grid)
        return not errors and bool(predicate(info))

    return wrapped


def _has_column(info: dict[str, Any], predicate: Callable[[dict[str, Any]], bool]) -> bool:
    return any(predicate(column) for column in info["columns"])


SEMANTIC_WITNESSES = {
    "small_k2_column": _witness(
        lambda info: _has_column(info, lambda column: column["k"] == 2)
    ),
    "large_k3_column": _witness(
        lambda info: _has_column(info, lambda column: column["k"] == 3)
    ),
    "single_color_column": _witness(
        lambda info: _has_column(
            info, lambda column: len(set(column["layer_colors"])) == 1
        )
    ),
    "two_color_grouped_layers": _witness(
        lambda info: _has_column(
            info,
            lambda column: column["k"] == 3
            and len(set(column["layer_colors"])) == 2,
        )
    ),
    "three_color_layers": _witness(
        lambda info: _has_column(
            info,
            lambda column: column["k"] == 3
            and len(set(column["layer_colors"])) == 3,
        )
    ),
    "multiple_columns": _witness(lambda info: info["active_columns"] == 2),
    "mixed_column_sizes": _witness(
        lambda info: len({column["k"] for column in info["columns"]}) > 1
    ),
    "cross_canvas_structure": _witness(
        lambda info: info["structure"]
        != CANONICAL_STRUCTURE_BY_PROFILE[info["profile"]]
    ),
    "scattered_source_rows": _witness(lambda info: not strict_canonical_like_grid_info(info)),
}


def strict_canonical_like_grid_info(info: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for column in info["columns"]:
        rows = column["rows"]
        if any(row >= info["height"] - column["k"] for row in rows):
            errors.append("source occupies output rows")
        if rows[-1] - rows[0] < len(rows) + 1:
            errors.append("source rows insufficiently scattered")
    return errors


def _rival_identity(grid: Any) -> list[list[int]]:
    return [list(row) for row in grid]


def _rival_vertical_gravity(grid: Any) -> list[list[int]]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = full_grid(info["height"], info["width"], 0)
    for column in info["columns"]:
        for offset, value in enumerate(column["bottom_values"]):
            out[info["height"] - 1 - offset][column["col"]] = value
    return out


def _rival_monochrome_pyramids(grid: Any) -> list[list[int]]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = full_grid(info["height"], info["width"], 0)
    for column in info["columns"]:
        color = column["bottom_values"][0]
        for layer_index, width in enumerate(_layer_widths(column["k"])):
            row = info["height"] - 1 - layer_index
            start = column["col"] - width // 2
            for offset in range(width):
                out[row][start + offset] = color
    return out


def _rival_reverse_color_order(grid: Any) -> list[list[int]]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = full_grid(info["height"], info["width"], 0)
    for column in info["columns"]:
        colors = tuple(reversed(column["layer_colors"]))
        for layer_index, (width, color) in enumerate(zip(_layer_widths(column["k"]), colors)):
            row = info["height"] - 1 - layer_index
            start = column["col"] - width // 2
            for offset in range(width):
                out[row][start + offset] = color
    return out


def _rival_fixed_k3(grid: Any) -> list[list[int]]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = full_grid(info["height"], info["width"], 0)
    for column in info["columns"]:
        color = column["bottom_values"][0]
        for layer_index, width in enumerate(_layer_widths(3)):
            row = info["height"] - 1 - layer_index
            start = column["col"] - width // 2
            for offset in range(width):
                out_col = start + offset
                if 0 <= out_col < info["width"]:
                    out[row][out_col] = color
    return out


def _rival_centered_pyramid(grid: Any) -> list[list[int]]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = full_grid(info["height"], info["width"], 0)
    center = info["width"] // 2
    for column in info["columns"]:
        for layer_index, (width, color) in enumerate(
            zip(_layer_widths(column["k"]), column["layer_colors"])
        ):
            row = info["height"] - 1 - layer_index
            start = center - width // 2
            for offset in range(width):
                out[row][start + offset] = color
    return out


def _rival_canvas_template(grid: Any) -> list[list[int]]:
    """Wrongly infer pyramid size/color grouping from canvas dimensions."""
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    template_sizes = {
        "16x11": (2, 2),
        "16x13": (3, 3),
        "21x9": (3, 2),
        "30x10": (3, 2),
    }[info["profile"]]
    out = full_grid(info["height"], info["width"], 0)
    for index, column in enumerate(info["columns"]):
        k = template_sizes[min(index, len(template_sizes) - 1)]
        colors = column["color_order"]
        if len(colors) == 1:
            layer_colors = (colors[0],) * k
        elif k == 2:
            layer_colors = colors[:2]
        elif len(colors) == 2:
            layer_colors = (colors[0], colors[1], colors[1])
        else:
            layer_colors = colors[:3]
        for layer_index, (width, color) in enumerate(
            zip(_layer_widths(k), layer_colors)
        ):
            row = info["height"] - 1 - layer_index
            start = column["col"] - width // 2
            for offset in range(width):
                out_col = start + offset
                if 0 <= out_col < info["width"]:
                    out[row][out_col] = color
    return out


SEMANTIC_RIVALS = {
    "identity_input": _rival_identity,
    "vertical_gravity": _rival_vertical_gravity,
    "monochrome_pyramids": _rival_monochrome_pyramids,
    "reverse_color_order": _rival_reverse_color_order,
    "fixed_k3": _rival_fixed_k3,
    "move_to_grid_center": _rival_centered_pyramid,
    "canvas_template": _rival_canvas_template,
}

WITNESS_RIVALS = {
    name: list(SEMANTIC_RIVALS) for name in SEMANTIC_WITNESSES
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "assume_identity": _rival_identity,
    "assume_gravity_only": _rival_vertical_gravity,
    "assume_single_color": _rival_monochrome_pyramids,
    "assume_every_column_has_nine_cells": _rival_fixed_k3,
    "canvas_template": _rival_canvas_template,
}


def _pair_errors(pair: Any, label: str):
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return None, [f"{label} must contain input and output grids"]
    info, errors = _analyze(pair["input"])
    if errors:
        return None, [f"{label} input: {reason}" for reason in errors]
    try:
        expected = rule_mirror(pair["input"])
    except ValueError as exc:
        return None, [f"{label} mirror failed: {exc}"]
    if pair["output"] != expected:
        return None, [f"{label} output does not match the column-pyramid rule"]
    return info, []


def lesson_identifiable(demos, query) -> list[str]:
    """Require a cross-canvas lesson that eliminates all named rivals."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)):
        return ["demonstrations must be a list"]
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations, got {len(demos)}")

    analyses: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        info, pair_reasons = _pair_errors(pair, f"demo {index}")
        reasons.extend(pair_reasons)
        if info is not None:
            analyses.append(info)
    _query_info, query_reasons = _pair_errors(query, "query")
    reasons.extend(query_reasons)
    if reasons:
        return reasons

    profiles = {info["profile"] for info in analyses}
    if profiles != set(PROFILES):
        reasons.append(f"demonstrations do not cover all profiles: {sorted(profiles)}")
    structures = {info["structure"] for info in analyses}
    if structures != set(STRUCTURES):
        reasons.append(
            f"demonstrations do not cover all structures: {sorted(structures)}"
        )
    sizes = {column["k"] for info in analyses for column in info["columns"]}
    if sizes != {2, 3}:
        reasons.append(f"demonstrations do not cover k=2 and k=3: {sorted(sizes)}")
    color_branches = {
        len(set(column["layer_colors"]))
        for info in analyses
        for column in info["columns"]
    }
    if color_branches != {1, 2, 3}:
        reasons.append(
            f"demonstrations do not cover one/two/three-color layers: {sorted(color_branches)}"
        )
    if {info["active_columns"] for info in analyses} != {1, 2}:
        reasons.append("demonstrations do not cover one- and two-column scenes")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named competitor {name!r} survives every demonstration")
    return reasons
