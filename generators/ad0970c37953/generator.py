"""Generator for ad0970c37953 — object areas become a bar gallery.

Each 4-connected non-zero object becomes a one-cell-wide vertical bar of the
same colour.  Bar height is object area.  Bars are sorted by descending area;
equal-area objects are ordered by top row, then left column.  The bars are
bottom-aligned and separated by one zero column.

The ordinary curriculum deliberately cycles through three complementary scene
profiles.  Three consecutive demonstrations therefore show (1) area order
beating spatial order, (2) the canonical row-before-column tie break, and
(3) separate same-colour objects remaining separate bars.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ad0970c37953"
TASK_ID = "ad0970c37953"
VERSION = "3.0.0"
RULE_HASH = "ea263d821c62"

SUMMARY = (
    "A 0-background grid contains 3-6 isolated, monochromatic, 4-connected "
    "objects with at least two different areas and at least one non-rectangular "
    "object. Replace each object by a one-column vertical bar of the same "
    "colour and height equal to its cell count. Sort bars by descending area; "
    "break equal-area ties by object top row and then left column. Pack bars "
    "left-to-right with one zero spacer column and bottom-align them. Separate "
    "objects may share a colour and still produce separate bars."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is 0 and all cells are integer colours 0..9",
    "there are 3-6 isolated monochromatic 4-connected objects",
    "at least two object areas differ",
    "at least one object is non-rectangular, so area is not bbox area",
    "ordinary lessons cycle through size-order, tie-break, and repeated-colour profiles",
]

# Every declared axis is exact and recoverable from the returned grid.
# Difficulty changes the draw distribution but never narrows these override bounds.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware keyed draw 8..16",
        "valid": "8..16",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware keyed draw 8..18",
        "valid": "8..18",
    },
    "n_blobs": {
        "type": "int",
        "default": "difficulty-aware keyed draw 3..6",
        "valid": "3..6",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_PROFILE_SIZE_ORDER = "size_order"
_PROFILE_TIE_BREAK = "tie_break"
_PROFILE_REPEATED_COLOUR = "repeated_colour"
SCHEDULE_PROFILES = (
    _PROFILE_SIZE_ORDER,
    _PROFILE_TIE_BREAK,
    _PROFILE_REPEATED_COLOUR,
)

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Connected templates with areas 1..6.  Areas 3-5 are deliberately
# non-rectangular so every normal scene can expose cell-count vs bbox-area.
_SHAPE_TEMPLATES: dict[int, tuple[tuple[int, int], ...]] = {
    1: ((0, 0),),
    2: ((0, 0), (0, 1)),
    3: ((0, 0), (1, 0), (1, 1)),
    4: ((0, 0), (0, 1), (0, 2), (1, 1)),
    5: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
    6: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
}


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Three consecutive sample indices cover every decisive lesson profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise KeyError(f"unknown override axis/axes: {', '.join(unknown)}")


def _split_axis(length: int, parts: int, rng) -> list[tuple[int, int]]:
    """Partition an axis into `parts` regions separated by one-cell gutters."""
    usable = length - (parts - 1)
    if usable < parts:
        raise ValueError(f"cannot split axis length {length} into {parts} regions")
    base, remainder = divmod(usable, parts)
    region_sizes = [base] * parts
    order = list(range(parts))
    rng.shuffle(order)
    for index in order[:remainder]:
        region_sizes[index] += 1
    regions: list[tuple[int, int]] = []
    start = 0
    for size in region_sizes:
        regions.append((start, start + size))  # half-open
        start += size + 1
    return regions


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(row for row, _ in cells)
    c0 = min(col for _, col in cells)
    return tuple(sorted((row - r0, col - c0) for row, col in cells))


def _shape_variants(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Return all distinct rotations/reflections of a normalized polyomino."""
    variants: set[tuple[tuple[int, int], ...]] = set()
    current = _normalize(cells)
    for _ in range(4):
        variants.add(_normalize(current))
        variants.add(_normalize((row, -col) for row, col in current))
        current = _normalize((col, -row) for row, col in current)
    return tuple(sorted(variants))


def _place_template(
    *,
    area: int,
    row_region: tuple[int, int],
    col_region: tuple[int, int],
    rng,
) -> set[tuple[int, int]]:
    row0, row1 = row_region
    col0, col1 = col_region
    region_h, region_w = row1 - row0, col1 - col0
    fitting = []
    for shape in _shape_variants(_SHAPE_TEMPLATES[area]):
        shape_h = max(row for row, _ in shape) + 1
        shape_w = max(col for _, col in shape) + 1
        if shape_h <= region_h and shape_w <= region_w:
            fitting.append((shape, shape_h, shape_w))
    if not fitting:
        raise ValueError(
            f"area-{area} template cannot fit region {region_h}x{region_w}"
        )
    shape, shape_h, shape_w = rng.choice(fitting)
    drow = rng.randint(0, region_h - shape_h)
    dcol = rng.randint(0, region_w - shape_w)
    return {
        (row0 + drow + row, col0 + dcol + col)
        for row, col in shape
    }


def _layout_shape(n_blobs: int) -> tuple[int, int]:
    if n_blobs <= 4:
        return 2, 2
    return 2, 3


def _profile_sizes(profile: str, n_blobs: int, rng) -> list[int]:
    if profile == _PROFILE_TIE_BREAK:
        rows, cols = _layout_shape(n_blobs)
        del rows
        upper_right = cols - 1
        lower_left = cols
        sizes = [value for value in (6, 5, 3, 2, 1, 5)[:n_blobs]]
        tie_size = 4
        sizes[upper_right] = tie_size
        sizes[lower_left] = tie_size
        # Shuffle only non-witness slots so the tied pair remains in the
        # row/column-order conflict positions while the remaining mapping varies.
        other_indices = [
            index for index in range(n_blobs)
            if index not in (upper_right, lower_left)
        ]
        other_values = [sizes[index] for index in other_indices]
        rng.shuffle(other_values)
        for index, value in zip(other_indices, other_values):
            sizes[index] = value
        return sizes

    sizes = list(range(1, n_blobs + 1))
    rng.shuffle(sizes)
    # Spatial row-major order must not already equal descending-area order.
    if sizes[0] == max(sizes):
        sizes[0], sizes[-1] = sizes[-1], sizes[0]
    return sizes


def _profile_colours(profile: str, n_blobs: int, sizes: list[int], rng) -> list[int]:
    if profile != _PROFILE_REPEATED_COLOUR:
        return rng.sample(range(1, 10), n_blobs)

    colours = rng.sample(range(1, 10), n_blobs - 1)
    repeated = colours[0]
    result = colours + [repeated]
    rng.shuffle(result)
    duplicate_indices = [index for index, colour in enumerate(result) if colour == repeated]
    # Keep the repeated objects at different areas so color aggregation cannot
    # accidentally imitate either separate bar.
    if sizes[duplicate_indices[0]] == sizes[duplicate_indices[1]]:
        swap_index = next(
            index for index in range(n_blobs)
            if index not in duplicate_indices and sizes[index] != sizes[duplicate_indices[0]]
        )
        result[duplicate_indices[1]], result[swap_index] = (
            result[swap_index],
            result[duplicate_indices[1]],
        )
    return result


def _draw_or_pin_int(ctx, label: str, lo: int, hi: int, pinned: int | None) -> int:
    """Honor any explicit override; otherwise record an internally chosen value."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    if pinned is None:
        return ctx.draw_int_diff(label, lo, hi)
    if not lo <= pinned <= hi:
        raise ValueError(f"internal {label}={pinned} outside [{lo}, {hi}]")
    return ctx.draw_choice(label, (pinned,))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)

    # Anchor the teaching distribution to the four canonical (h, w, palette)
    # profiles in every difficulty band, while retaining a broad-scale tail.
    # Correlation matters here: independent h/w draws made exact canonical
    # profiles needlessly rare even when both marginals looked reasonable.
    scale_rng = ctx.draw_rng("scale")
    has_h_override = "grid_h" in overrides and overrides["grid_h"] is not None
    has_w_override = "grid_w" in overrides and overrides["grid_w"] is not None
    canonical_anchor = not has_h_override and not has_w_override and scale_rng.random() < 0.65
    target_palette_size: int | None = None
    if canonical_anchor:
        height_pin, width_pin, target_palette_size = scale_rng.choice(
            ((8, 8, 4), (9, 9, 5), (10, 10, 5), (9, 10, 4))
        )
    elif not has_h_override and not has_w_override:
        ranges = {
            "easy": ((8, 11), (8, 12)),
            "hard": ((10, 16), (10, 18)),
        }
        (h_lo, h_hi), (w_lo, w_hi) = ranges.get(
            difficulty, ((9, 14), (9, 15))
        )
        height_pin = scale_rng.randint(h_lo, h_hi)
        width_pin = scale_rng.randint(w_lo, w_hi)
    else:
        height_pin = width_pin = None

    height = _draw_or_pin_int(ctx, "grid_h", 8, 16, height_pin)
    width = _draw_or_pin_int(ctx, "grid_w", 8, 18, width_pin)

    if "n_blobs" in overrides and overrides["n_blobs"] is not None:
        n_pin = None
    elif target_palette_size is not None:
        # Repeated-colour profiles have one fewer distinct foreground colour.
        n_pin = (
            target_palette_size
            if profile == _PROFILE_REPEATED_COLOUR
            else target_palette_size - 1
        )
    else:
        choices = {
            "easy": (3, 3, 3, 4, 4, 5, 6),
            "hard": (3, 4, 4, 4, 5, 5, 6, 6),
        }.get(difficulty, (3, 3, 4, 4, 4, 5, 6))
        n_pin = scale_rng.choice(choices)
    n_blobs = _draw_or_pin_int(ctx, "n_blobs", 3, 6, n_pin)
    rng = ctx.draw_rng("layout")

    n_rows, n_cols = _layout_shape(n_blobs)
    row_regions = _split_axis(height, n_rows, rng)
    col_regions = _split_axis(width, n_cols, rng)
    slots = [
        (row_region, col_region)
        for row_region in row_regions
        for col_region in col_regions
    ][:n_blobs]

    sizes = _profile_sizes(profile, n_blobs, rng)
    colours = _profile_colours(profile, n_blobs, sizes, rng)
    grid = full_grid(height, width, 0)
    for area, colour, (row_region, col_region) in zip(sizes, colours, slots):
        cells = _place_template(
            area=area,
            row_region=row_region,
            col_region=col_region,
            rng=rng,
        )
        for row, col in cells:
            grid[row][col] = colour

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError(f"internal generation error: {errors}")
    return grid


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a non-empty list"]}
    if not all(isinstance(row, list) and row for row in grid):
        return {"errors": ["every row must be a non-empty list"]}
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}

    height = len(grid)
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("all cells must be integer colours 0..9")
                break
        if errors:
            break

    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            colour = grid[row][col]
            if colour == 0 or (row, col) in seen:
                continue
            cells = {(row, col)}
            seen.add((row, col))
            queue = deque([(row, col)])
            while queue:
                current_row, current_col = queue.popleft()
                for drow, dcol in _DIR4:
                    nxt = current_row + drow, current_col + dcol
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == colour
                    ):
                        seen.add(nxt)
                        cells.add(nxt)
                        queue.append(nxt)
            bbox = (
                min(r for r, _ in cells),
                min(c for _, c in cells),
                max(r for r, _ in cells),
                max(c for _, c in cells),
            )
            components.append(
                {
                    "colour": colour,
                    "cells": frozenset(cells),
                    "area": len(cells),
                    "bbox": bbox,
                    "bbox_area": (bbox[2] - bbox[0] + 1) * (bbox[3] - bbox[1] + 1),
                }
            )

    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value == 0:
                continue
            for drow, dcol in ((1, 0), (0, 1)):
                nr, nc = row + drow, col + dcol
                if (
                    nr < height
                    and nc < width
                    and grid[nr][nc] not in (0, value)
                ):
                    errors.append("different-colour objects must not touch orthogonally")
                    break

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "components": components,
        "areas": [component["area"] for component in components],
        "colours": [component["colour"] for component in components],
        "palette": {value for row in grid for value in row},
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    analysis = _analysis(grid)
    errors = list(analysis.get("errors", []))
    if errors and "components" not in analysis:
        return errors

    components = analysis["components"]
    if 0 not in analysis["palette"]:
        errors.append("background colour 0 must be present")
    if not 3 <= len(components) <= 6:
        errors.append(f"expected 3-6 objects, got {len(components)}")
    if any(not 1 <= component["area"] <= 9 for component in components):
        errors.append("object areas must be in 1..9")
    if len(set(analysis["areas"])) < 2:
        errors.append("need at least two distinct object areas")
    if components and not any(
        component["area"] < component["bbox_area"] for component in components
    ):
        errors.append("need at least one non-rectangular object")
    return errors


def strict_canonical_like(grid) -> list[str]:
    reasons = self_check(grid)
    analysis = _analysis(grid)
    if "height" not in analysis:
        return reasons
    if not 8 <= analysis["height"] <= 16:
        reasons.append("height is outside the 8..16 teaching envelope")
    if not 8 <= analysis["width"] <= 18:
        reasons.append("width is outside the 8..18 teaching envelope")
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analysis(grid)
    if analysis.get("errors"):
        raise ValueError("cannot observe overrides from malformed grid")
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_blobs": len(analysis["components"]),
    }


def _canonical_components(grid) -> list[dict[str, Any]]:
    analysis = _analysis(grid)
    if analysis.get("errors"):
        raise ValueError(f"malformed bar-gallery input: {analysis['errors']}")
    return sorted(
        analysis["components"],
        key=lambda component: (
            -component["area"],
            component["bbox"][0],
            component["bbox"][1],
        ),
    )


def _render_bars(items: list[tuple[int, int]], *, top_aligned=False, gaps=True):
    if not items:
        return [[0]]
    height = max(area for _, area in items)
    width = len(items) if not gaps else 2 * len(items) - 1
    output = full_grid(height, width, 0)
    for index, (colour, area) in enumerate(items):
        col = index if not gaps else 2 * index
        rows = range(area) if top_aligned else range(height - area, height)
        for row in rows:
            output[row][col] = colour
    return output


def rule_bar_gallery(grid):
    """Python audit mirror; the canonical Racket program remains authoritative."""
    components = _canonical_components(grid)
    return _render_bars(
        [(component["colour"], component["area"]) for component in components]
    )


def _rival_spatial_order(grid):
    analysis = _analysis(grid)
    if analysis.get("errors"):
        return None
    components = sorted(
        analysis["components"],
        key=lambda component: (component["bbox"][0], component["bbox"][1]),
    )
    return _render_bars([(c["colour"], c["area"]) for c in components])


def _rival_ascending_area(grid):
    analysis = _analysis(grid)
    if analysis.get("errors"):
        return None
    components = sorted(
        analysis["components"],
        key=lambda component: (
            component["area"],
            component["bbox"][0],
            component["bbox"][1],
        ),
    )
    return _render_bars([(c["colour"], c["area"]) for c in components])


def _rival_ties_left_to_right(grid):
    analysis = _analysis(grid)
    if analysis.get("errors"):
        return None
    components = sorted(
        analysis["components"],
        key=lambda component: (
            -component["area"],
            component["bbox"][1],
            component["bbox"][0],
        ),
    )
    return _render_bars([(c["colour"], c["area"]) for c in components])


def _rival_aggregate_by_colour(grid):
    analysis = _analysis(grid)
    if analysis.get("errors"):
        return None
    totals = Counter()
    first_bbox: dict[int, tuple[int, int, int, int]] = {}
    for component in analysis["components"]:
        colour = component["colour"]
        totals[colour] += component["area"]
        first_bbox[colour] = min(first_bbox.get(colour, component["bbox"]), component["bbox"])
    items = sorted(
        ((colour, area, first_bbox[colour]) for colour, area in totals.items()),
        key=lambda item: (-item[1], item[2][0], item[2][1]),
    )
    return _render_bars([(colour, area) for colour, area, _ in items])


def _rival_bbox_area(grid):
    analysis = _analysis(grid)
    if analysis.get("errors"):
        return None
    components = sorted(
        analysis["components"],
        key=lambda component: (
            -component["bbox_area"],
            component["bbox"][0],
            component["bbox"][1],
        ),
    )
    return _render_bars([(c["colour"], c["bbox_area"]) for c in components])


def _rival_top_aligned(grid):
    components = _canonical_components(grid)
    return _render_bars(
        [(component["colour"], component["area"]) for component in components],
        top_aligned=True,
    )


def _rival_no_gaps(grid):
    components = _canonical_components(grid)
    return _render_bars(
        [(component["colour"], component["area"]) for component in components],
        gaps=False,
    )


def _witness_multiple_area_levels(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis.get("errors") and len(set(analysis["areas"])) >= 2


def _witness_size_order_differs_from_spatial(grid) -> bool:
    return _rival_spatial_order(grid) != rule_bar_gallery(grid)


def _witness_row_before_column_tie(grid) -> bool:
    analysis = _analysis(grid)
    if analysis.get("errors"):
        return False
    components = analysis["components"]
    for left_index, left in enumerate(components):
        for right in components[left_index + 1:]:
            if left["area"] != right["area"]:
                continue
            row_order = (left["bbox"][0], left["bbox"][1]) < (
                right["bbox"][0], right["bbox"][1]
            )
            col_order = (left["bbox"][1], left["bbox"][0]) < (
                right["bbox"][1], right["bbox"][0]
            )
            if row_order != col_order:
                return _rival_ties_left_to_right(grid) != rule_bar_gallery(grid)
    return False


def _witness_same_colour_separate_objects(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis.get("errors") and len(set(analysis["colours"])) < len(
        analysis["colours"]
    )


def _witness_nonrectangular_object(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis.get("errors") and any(
        component["area"] < component["bbox_area"]
        for component in analysis["components"]
    )


def _witness_multiple_objects(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis.get("errors") and len(analysis["components"]) >= 3


SEMANTIC_WITNESSES = {
    "multiple_area_levels": _witness_multiple_area_levels,
    "area_order_differs_from_spatial_order": _witness_size_order_differs_from_spatial,
    "row_before_column_equal_area_tie": _witness_row_before_column_tie,
    "same_colour_separate_objects": _witness_same_colour_separate_objects,
    "nonrectangular_object_rebuts_bbox_area": _witness_nonrectangular_object,
    "multiple_objects_require_zero_gaps": _witness_multiple_objects,
}

SEMANTIC_RIVALS = {
    "sort objects only by spatial position": _rival_spatial_order,
    "sort object areas ascending": _rival_ascending_area,
    "break equal-area ties left-to-right": _rival_ties_left_to_right,
    "aggregate disconnected objects by colour": _rival_aggregate_by_colour,
    "use bounding-box area instead of cell count": _rival_bbox_area,
    "top-align bars": _rival_top_aligned,
    "remove spacer columns": _rival_no_gaps,
}

WITNESS_RIVALS = {
    "multiple_area_levels": ["sort object areas ascending", "top-align bars"],
    "area_order_differs_from_spatial_order": ["sort objects only by spatial position"],
    "row_before_column_equal_area_tie": ["break equal-area ties left-to-right"],
    "same_colour_separate_objects": ["aggregate disconnected objects by colour"],
    "nonrectangular_object_rebuts_bbox_area": ["use bounding-box area instead of cell count"],
    "multiple_objects_require_zero_gaps": ["remove spacer columns"],
}

# Canonical examples use a distinct colour for every object, so this shortcut
# fits all four canonical pairs.  Generated repeated-colour scenes are the
# necessary counterexample that makes the object-level rule identifiable.
CANONICAL_SHORTCUTS = {
    "aggregate disconnected objects by colour": _rival_aggregate_by_colour,
    "sort objects only by spatial position": _rival_spatial_order,
    "break equal-area ties left-to-right": _rival_ties_left_to_right,
    "use bounding-box area instead of cell count": _rival_bbox_area,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any lesson on which a named plausible rival survives the demos."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    for index, pair in enumerate(demos):
        expected = rule_bar_gallery(pair["input"])
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output does not match the bar-gallery rule")
    query_answer = rule_bar_gallery(query["input"])
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output does not match the bar-gallery rule")
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons
