"""Generator for dc0a7662670b — perimeter-sorted vertical shape stack.

Find every nonzero same-color 4-connected component. Compute its true exposed
4-neighbor edge perimeter, sort components by perimeter descending and then by
color ascending, crop each component to its bounding box, and stack the crops
top-to-bottom with one zero row between adjacent crops. Crops are left-aligned
and the output width is the widest crop.

The four-example cyclic schedule is semantic rather than merely random:
``canonical_four`` anchors the real task's size/palette profile,
``bbox_tie`` separates true perimeter from bounding-box perimeter,
``area_inversion`` refutes the cell-count shortcut that fits every canonical
pair, and ``color_tie`` exposes the otherwise-unseen ascending-color tie break.
Every four consecutive samples contain all four profiles.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dc0a7662670b"
TASK_ID = "dc0a7662670b"
VERSION = "2.0.0"
RULE_HASH = "eff15ddf94a7"

SUMMARY = (
    "Sort same-color 4-connected components by true exposed-edge perimeter "
    "descending, breaking equal-perimeter ties by ascending color; crop and "
    "left-align them in a vertical stack separated by one background row. "
    "A four-profile schedule explicitly refutes bbox, area, input-order, and "
    "descending-color tie shortcuts."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is 0",
    "there are three or four distinct-color 4-connected components",
    "components are sorted by true edge perimeter descending, then color ascending",
    "cropped shapes are left-aligned with exactly one zero row between them",
    "every four consecutive ordinary samples cover all semantic profiles",
]

SHAPE_PROFILES = (
    "canonical_four",
    "bbox_tie",
    "area_inversion",
    "color_tie",
)
SCHEDULE_PROFILES = SHAPE_PROFILES

AXES = {
    "grid_h": {
        "type": "int",
        "default": "profile-keyed canonical dimension",
        "valid": "10..14",
        "doc": "Exact returned input height; includes every canonical height.",
    },
    "grid_w": {
        "type": "int",
        "default": "profile-keyed canonical dimension",
        "valid": "11..16",
        "doc": "Exact returned input width; includes every canonical width.",
    },
    "shape_profile": {
        "type": "str",
        "default": "four-sample semantic schedule",
        "valid": "|".join(SHAPE_PROFILES),
        "doc": (
            "Linked component family: exact canonical support, bbox conflict, "
            "area/perimeter inversion, or equal-perimeter color tie."
        ),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Normalized polyominoes. Names state the true edge perimeter and purpose.
_SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    "p16_c": (
        (0, 0), (0, 1), (0, 2),
        (1, 0),
        (2, 0), (2, 1), (2, 2),
    ),
    "p14_l": (
        (0, 0), (1, 0), (2, 0),
        (3, 0), (3, 1), (3, 2),
    ),
    "p12_stair": ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    "p10_l": ((0, 0), (1, 0), (2, 0), (2, 1)),
    # p12 and p10 below both have five cells in a 3x2 bounding box.
    "p12_u": ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1)),
    "p10_five": ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    "p8_tri": ((0, 0), (1, 0), (1, 1)),
    # p10 rectangle has more cells than the p12 plus.
    "p12_plus": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    "p10_rect": ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    "p8_square": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "p12_zig": ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
}

# Items are listed in row-major INPUT position order, deliberately not answer
# order. The role suffixes are used only for deterministic color assignment.
_PROFILE_ITEMS: dict[str, tuple[tuple[str, str], ...]] = {
    "canonical_four": (
        ("p10_l", "p10"),
        ("p16_c", "p16"),
        ("p12_stair", "p12"),
        ("p14_l", "p14"),
    ),
    "bbox_tie": (
        ("p10_five", "p10_bbox_low"),
        ("p12_u", "p12_bbox_high"),
        ("p8_tri", "p8"),
    ),
    "area_inversion": (
        ("p10_rect", "p10"),
        ("p8_square", "p8"),
        ("p12_plus", "p12"),
    ),
    "color_tie": (
        ("p12_zig", "p12_high"),
        ("p14_l", "p14"),
        ("p12_plus", "p12_low"),
    ),
}

# (true perimeter, cell count, bbox perimeter), answer-sorted except ties where
# order is immaterial for profile recognition.
_PROFILE_SIGNATURES = {
    "canonical_four": ((16, 7, 12), (14, 6, 14), (12, 5, 12), (10, 4, 10)),
    "bbox_tie": ((12, 5, 10), (10, 5, 10), (8, 3, 8)),
    "area_inversion": ((12, 5, 12), (10, 6, 10), (8, 4, 8)),
    "color_tie": ((14, 6, 14), (12, 5, 12), (12, 5, 12)),
}

# All canonical examples plus every generated profile. This keeps self_check
# canonical-owning while still rejecting arbitrary random motif galleries.
_ALLOWED_PERIMETER_MULTISETS = {
    (10, 14, 16),
    (10, 12, 14),
    (10, 12, 16),
    (10, 12, 14, 16),
    (8, 10, 12),
    (12, 12, 14),
}

# These all match exact canonical (height, width, palette-size) profiles for the
# corresponding 3- or 4-component branch.
_DEFAULT_DIMENSIONS = {
    "canonical_four": ((11, 11),),
    "bbox_tie": ((10, 12), (11, 13)),
    "area_inversion": ((12, 14), (10, 13)),
    "color_tie": ((10, 13), (11, 13)),
}


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    first = grid[0]
    width = len(first) if isinstance(first, (list, tuple)) else 0
    if width == 0:
        return None, ["grid rows must be nonempty"]
    if len(grid) > 30 or width > 30:
        return None, ["grid dimensions must not exceed 30x30"]

    converted: list[list[int]] = []
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        converted_row: list[int] = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                converted_row.append(0)
            else:
                converted_row.append(value)
        converted.append(converted_row)
    return (None, errors) if errors else (converted, [])


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    row0 = min(row for row, _col in cells)
    col0 = min(col for _row, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _transform(
    cells: Iterable[tuple[int, int]], code: int
) -> tuple[tuple[int, int], ...]:
    transformed = _normalize(cells)
    if code >= 4:
        transformed = _normalize((row, -col) for row, col in transformed)
    for _ in range(code % 4):
        transformed = _normalize((col, -row) for row, col in transformed)
    return transformed


def _components_by_color(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    """Racket ``objects g 0`` semantics: same-color connected components."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row, next_col = row + drow, col + dcol
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and grid[next_row][next_col] == color
                        and (next_row, next_col) not in seen
                    ):
                        seen.add((next_row, next_col))
                        stack.append((next_row, next_col))
            components.append(cells)
    return components


def _perimeter(cells: Iterable[tuple[int, int]]) -> int:
    occupied = set(cells)
    return sum(
        (row + drow, col + dcol) not in occupied
        for row, col in occupied
        for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1))
    )


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [row for row, _col in cells]
    cols = [col for _row, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _crop(
    grid: list[list[int]], cells: Iterable[tuple[int, int]]
) -> list[list[int]]:
    cells = tuple(cells)
    occupied = set(cells)
    row0, col0, row1, col1 = _bbox(cells)
    return [
        [
            grid[row][col] if (row, col) in occupied else 0
            for col in range(col0, col1 + 1)
        ]
        for row in range(row0, row1 + 1)
    ]


def _pack(records: list[dict[str, Any]], *, gap: int = 1) -> list[list[int]]:
    crops = [record["crop"] for record in records]
    height = sum(len(crop) for crop in crops) + gap * max(0, len(crops) - 1)
    width = max(len(crop[0]) for crop in crops)
    output = full_grid(height, width, 0)
    top = 0
    for crop in crops:
        for row_index, row in enumerate(crop):
            for col_index, value in enumerate(row):
                if value != 0:
                    output[top + row_index][col_index] = value
        top += len(crop) + gap
    return output


def _analysis(grid: Any) -> dict[str, Any]:
    converted, errors = _coerce_grid(grid)
    result: dict[str, Any] = {"errors": list(errors)}
    if converted is None:
        return result

    height, width = len(converted), len(converted[0])
    if not 10 <= height <= 14:
        errors.append(f"grid height {height} outside 10..14")
    if not 11 <= width <= 16:
        errors.append(f"grid width {width} outside 11..16")

    records: list[dict[str, Any]] = []
    for cells in _components_by_color(converted):
        row0, col0, row1, col1 = _bbox(cells)
        color = converted[cells[0][0]][cells[0][1]]
        record = {
            "cells": tuple(sorted(cells)),
            "color": color,
            "size": len(cells),
            "perimeter": _perimeter(cells),
            "bbox": (row0, col0, row1, col1),
            "bbox_perimeter": 2 * ((row1 - row0 + 1) + (col1 - col0 + 1)),
            "bbox_area": (row1 - row0 + 1) * (col1 - col0 + 1),
            "crop": _crop(converted, cells),
        }
        records.append(record)

    if not 3 <= len(records) <= 4:
        errors.append(f"expected 3 or 4 components, found {len(records)}")
    colors = [record["color"] for record in records]
    if len(colors) != len(set(colors)):
        errors.append("component colors must be distinct")
    for index, record in enumerate(records):
        if not 3 <= record["size"] <= 7:
            errors.append(
                f"component {index} size {record['size']} outside required 3..7"
            )
        row0, col0, row1, col1 = record["bbox"]
        if row1 - row0 + 1 > 4 or col1 - col0 + 1 > 4:
            errors.append(f"component {index} bounding box exceeds 4x4")

    perimeter_multiset = tuple(sorted(record["perimeter"] for record in records))
    if records and perimeter_multiset not in _ALLOWED_PERIMETER_MULTISETS:
        errors.append(
            f"unsupported component perimeter multiset {perimeter_multiset}"
        )

    official = sorted(
        records,
        key=lambda record: (-record["perimeter"], record["color"]),
    )
    spatial = sorted(records, key=lambda record: (record["bbox"][0], record["bbox"][1]))
    bbox_sorted = sorted(
        records,
        key=lambda record: (-record["bbox_perimeter"], record["color"]),
    )
    area_sorted = sorted(
        records,
        key=lambda record: (-record["size"], record["color"]),
    )
    color_desc_ties = sorted(
        records,
        key=lambda record: (-record["perimeter"], -record["color"]),
    )

    signature = tuple(
        sorted(
            [
                (
                    record["perimeter"],
                    record["size"],
                    record["bbox_perimeter"],
                )
                for record in records
            ],
            reverse=True,
        )
    )
    shape_profile = next(
        (
            name
            for name, expected in _PROFILE_SIGNATURES.items()
            if signature == expected
        ),
        None,
    )

    result.update(
        {
            "grid": converted,
            "components": records,
            "perimeter_multiset": perimeter_multiset,
            "shape_profile": shape_profile,
            "perimeters_desc": tuple(record["perimeter"] for record in official),
            "spatial_perimeters": tuple(record["perimeter"] for record in spatial),
            "bbox_order_perimeters": tuple(
                record["perimeter"] for record in bbox_sorted
            ),
            "area_order_perimeters": tuple(
                record["perimeter"] for record in area_sorted
            ),
            "official": official,
            "spatial": spatial,
            "bbox_sorted": bbox_sorted,
            "area_sorted": area_sorted,
            "color_desc_ties": color_desc_ties,
            "output": _pack(official) if records else None,
            "errors": errors,
        }
    )
    return result


def self_check(
    grid: Any, *, difficulty: Any = None, meta: Any = None
) -> list[str]:
    del difficulty
    facts = _analysis(grid)
    errors = list(facts["errors"])
    if errors:
        return errors
    if meta and isinstance(meta, dict) and isinstance(meta.get("overrides"), dict):
        requested = meta["overrides"]
        try:
            observed = observe_overrides(grid)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            for key, expected in requested.items():
                if key in AXES and observed.get(key) != expected:
                    errors.append(
                        f"override {key}={expected!r} realized as "
                        f"{observed.get(key)!r}"
                    )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Complete grammar used for generated lessons and public examples."""
    return self_check(grid)


def observe_overrides(grid: Any) -> dict[str, Any]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    if facts["shape_profile"] is None:
        raise ValueError("grid does not match a declared generated shape profile")
    return {
        "grid_h": len(facts["grid"]),
        "grid_w": len(facts["grid"][0]),
        "shape_profile": facts["shape_profile"],
        "perimeters_desc": facts["perimeters_desc"],
        "spatial_perimeters": facts["spatial_perimeters"],
        "bbox_order_perimeters": facts["bbox_order_perimeters"],
        "area_order_perimeters": facts["area_order_perimeters"],
    }


def rule_mirror(grid: Any) -> list[list[int]]:
    """Pure Python mirror of the pinned canonical Racket authority."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return [row[:] for row in facts["output"]]


def _rival_from_key(
    grid: Any,
    key: Callable[[dict[str, Any]], Any],
    *,
    gap: int = 1,
) -> list[list[int]]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return _pack(sorted(facts["components"], key=key), gap=gap)


def _rival_sort_by_bbox_perimeter(grid: Any) -> list[list[int]]:
    return _rival_from_key(
        grid,
        lambda record: (-record["bbox_perimeter"], record["color"]),
    )


def _rival_sort_by_area(grid: Any) -> list[list[int]]:
    return _rival_from_key(
        grid,
        lambda record: (-record["size"], record["color"]),
    )


def _rival_sort_by_input_order(grid: Any) -> list[list[int]]:
    return _rival_from_key(
        grid,
        lambda record: (record["bbox"][0], record["bbox"][1]),
    )


def _rival_tie_break_color_descending(grid: Any) -> list[list[int]]:
    return _rival_from_key(
        grid,
        lambda record: (-record["perimeter"], -record["color"]),
    )


def _rival_no_separator_rows(grid: Any) -> list[list[int]]:
    return _rival_from_key(
        grid,
        lambda record: (-record["perimeter"], record["color"]),
        gap=0,
    )


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "sort_by_bbox_perimeter": _rival_sort_by_bbox_perimeter,
    "sort_by_area": _rival_sort_by_area,
    "sort_by_input_order": _rival_sort_by_input_order,
    "tie_break_color_descending": _rival_tie_break_color_descending,
    "omit_separator_rows": _rival_no_separator_rows,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "sort_by_area": _rival_sort_by_area,
    "tie_break_color_descending": _rival_tie_break_color_descending,
}


def _witness_difference(rival_name: str, grid: Any) -> bool:
    if strict_canonical_like(grid):
        return False
    return SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "true_perimeter_not_bbox": lambda grid: _witness_difference(
        "sort_by_bbox_perimeter", grid
    ),
    "true_perimeter_not_area": lambda grid: _witness_difference(
        "sort_by_area", grid
    ),
    "not_input_position_order": lambda grid: _witness_difference(
        "sort_by_input_order", grid
    ),
    "ascending_color_tie_break": lambda grid: _witness_difference(
        "tie_break_color_descending", grid
    ),
    "one_blank_row_between_crops": lambda grid: _witness_difference(
        "omit_separator_rows", grid
    ),
}
WITNESS_RIVALS = {
    "true_perimeter_not_bbox": ("sort_by_bbox_perimeter",),
    "true_perimeter_not_area": ("sort_by_area",),
    "not_input_position_order": ("sort_by_input_order",),
    "ascending_color_tie_break": ("tie_break_color_descending",),
    "one_blank_row_between_crops": ("omit_separator_rows",),
}


def _pair_errors(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} is missing input/output"]
    grammar = strict_canonical_like(pair["input"])
    if grammar:
        return [f"{label} input is outside the grammar: {grammar[0]}"]
    try:
        expected = rule_mirror(pair["input"])
    except ValueError as exc:
        return [f"{label} mirror failed: {exc}"]
    if expected != pair["output"]:
        return [f"{label} output does not follow the perimeter-stack rule"]
    return []


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require every four-demo lesson to eliminate all declared competitors."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    errors: list[str] = []
    for index, pair in enumerate(demos):
        errors.extend(_pair_errors(pair, f"demo {index}"))
    errors.extend(_pair_errors(query, "query"))
    if errors:
        return errors

    profiles: set[str] = set()
    for pair in demos:
        try:
            profiles.add(observe_overrides(pair["input"])["shape_profile"])
        except ValueError:
            pass
    missing = set(SHAPE_PROFILES) - profiles
    if missing:
        errors.append(f"demonstrations miss scheduled profiles: {sorted(missing)}")

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(pair["input"]) == pair["output"] for pair in demos
            )
        except Exception as exc:
            errors.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if survives:
            query_agrees = competitor(query["input"]) == query["output"]
            suffix = "and matches the query" if query_agrees else "but differs on the query"
            errors.append(f"competitor {name} survives all demonstrations {suffix}")
    return errors


def schedule_profile(
    seed: int, sample_index: int, difficulty: Any = None
) -> str:
    del seed, difficulty
    return SHAPE_PROFILES[sample_index % len(SHAPE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    for name, lo, hi in (("grid_h", 10, 14), ("grid_w", 11, 16)):
        if name not in overrides:
            continue
        value = overrides[name]
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"{name} must be an integer")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside {lo}..{hi}")
    if "shape_profile" in overrides:
        value = overrides["shape_profile"]
        if not isinstance(value, str) or value not in SHAPE_PROFILES:
            raise ValueError(
                f"shape_profile must be one of {list(SHAPE_PROFILES)}"
            )


def _scheduled_choice(ctx, sample_index: int) -> str:
    if "shape_profile" in ctx.overrides:
        return ctx.draw_choice("shape_profile", SHAPE_PROFILES)
    scheduled = schedule_profile(ctx.seed, sample_index, ctx.difficulty)
    return ctx.draw_choice("shape_profile", (scheduled,))


def _random_composition(total: int, parts: int, rng) -> list[int]:
    values = [0] * parts
    for _ in range(total):
        values[rng.randrange(parts)] += 1
    return values


def _profile_colors(profile: str, raw_colors: list[int], rng) -> dict[str, int]:
    colors = sorted(raw_colors)
    if profile == "bbox_tie":
        # Bbox/area ties break toward p10 under ascending color, opposite truth.
        return {"p10_bbox_low": colors[0], "p8": colors[1], "p12_bbox_high": colors[2]}
    if profile == "color_tie":
        return {"p12_low": colors[0], "p14": colors[1], "p12_high": colors[2]}

    rng.shuffle(colors)
    roles = [role for _shape, role in _PROFILE_ITEMS[profile]]
    return dict(zip(roles, colors))


def _place_profile(
    height: int,
    width: int,
    profile: str,
    colors: dict[str, int],
    rng,
) -> list[list[int]]:
    items = []
    for shape_name, role in _PROFILE_ITEMS[profile]:
        cells = _transform(_SHAPES[shape_name], rng.randrange(8))
        shape_h = max(row for row, _col in cells) + 1
        shape_w = max(col for _row, col in cells) + 1
        items.append(
            {
                "cells": cells,
                "height": shape_h,
                "width": shape_w,
                "color": colors[role],
            }
        )

    top_indices = (0, 1)
    bottom_indices = tuple(range(2, len(items)))
    left_indices = tuple(index for index in (0, 2) if index < len(items))
    right_indices = tuple(index for index in (1, 3) if index < len(items))
    top_height = max(items[index]["height"] for index in top_indices)
    bottom_height = max(items[index]["height"] for index in bottom_indices)
    left_width = max(items[index]["width"] for index in left_indices)
    right_width = max(items[index]["width"] for index in right_indices)

    mandatory_h = top_height + 1 + bottom_height
    mandatory_w = left_width + 1 + right_width
    if mandatory_h > height or mandatory_w > width:
        raise ValueError(
            f"grid {height}x{width} cannot fit profile {profile} "
            f"requiring {mandatory_h}x{mandatory_w}"
        )

    top_margin, extra_v_gap, _bottom_margin = _random_composition(
        height - mandatory_h, 3, rng
    )
    left_margin, extra_h_gap, _right_margin = _random_composition(
        width - mandatory_w, 3, rng
    )
    right_col = left_margin + left_width + 1 + extra_h_gap
    bottom_row = top_margin + top_height + 1 + extra_v_gap
    slots = (
        (top_margin, left_margin),
        (top_margin, right_col),
        (bottom_row, left_margin),
        (bottom_row, right_col),
    )

    grid = full_grid(height, width, 0)
    for item, (top, left) in zip(items, slots):
        for row, col in item["cells"]:
            grid[top + row][left + col] = item["color"]
    return grid


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    _validate_overrides(overrides)
    band = "medium" if difficulty is None else difficulty
    if band not in ("easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = _scheduled_choice(ctx, sample_index)
    dimension_rng = ctx.draw_rng(f"default-dimensions:{profile}")
    default_height, default_width = dimension_rng.choice(_DEFAULT_DIMENSIONS[profile])
    height = (
        ctx.draw_int("grid_h", 10, 14)
        if "grid_h" in overrides
        else ctx.draw_int("grid_h", default_height, default_height)
    )
    width = (
        ctx.draw_int("grid_w", 11, 16)
        if "grid_w" in overrides
        else ctx.draw_int("grid_w", default_width, default_width)
    )

    n_components = len(_PROFILE_ITEMS[profile])
    raw_colors = list(
        ctx.draw_distinct_colors("component_colors", n=n_components, exclude=(0,))
    )
    rng = ctx.draw_rng(f"layout:{profile}:{band}")
    colors = _profile_colors(profile, raw_colors, rng)
    grid = _place_profile(height, width, profile, colors, rng)

    errors = self_check(grid)
    if errors:
        raise AssertionError("internal generator invariant failed: " + "; ".join(errors))
    observed = observe_overrides(grid)
    if observed["shape_profile"] != profile:
        raise AssertionError(
            f"shape profile drift: requested {profile}, observed "
            f"{observed['shape_profile']}"
        )
    return grid


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Stable near-misses used by the strict defect lint."""
    base = generate(991, 0, difficulty="medium", shape_profile="canonical_four")
    facts = _analysis(base)

    duplicate_color = [row[:] for row in base]
    first, second = facts["components"][:2]
    for row, col in second["cells"]:
        duplicate_color[row][col] = first["color"]

    extra_component = [row[:] for row in base]
    for row in range(len(extra_component)):
        for col in range(len(extra_component[0])):
            if extra_component[row][col] != 0:
                continue
            if all(
                not (0 <= row + dr < len(extra_component)
                     and 0 <= col + dc < len(extra_component[0]))
                or extra_component[row + dr][col + dc] == 0
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
            ):
                extra_component[row][col] = 9
                return [
                    ("duplicate_component_color", duplicate_color),
                    ("isolated_extra_component", extra_component),
                ]
    raise AssertionError("failed to construct isolated mutation fixture")
