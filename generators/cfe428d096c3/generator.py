"""Reviewed generator for ARC task cfe428d096c3.

The canonical rule inspects each color-1 connected component independently.
A solid rectangle becomes color 8 when square, color 2 when wider than tall,
and color 3 when taller than wide.  Non-rectangular color-1 components and all
non-1 cells are preserved.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cfe428d096c3"
TASK_ID = "cfe428d096c3"
VERSION = "3.0.0"
RULE_HASH = "aba2f01fcba9"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.15

SUMMARY = (
    "A 12-14 square color-0 canvas contains three to five separated solid "
    "color-1 rectangles, always including at least one square, one wider "
    "rectangle, and one taller rectangle.  Most draws also contain one "
    "separated non-rectangular color-1 component, which is a decisive "
    "negative witness: it must remain color 1.  One four-cell non-rectangular "
    "color-6 distractor is always preserved.  Every fourth sample is a linked "
    "canonical anchor with exactly four solid blue rectangles and no blue "
    "non-rectangle.  The canonical Racket rule is the sole output authority: "
    "solid blue squares become 8, wider rectangles 2, taller rectangles 3, "
    "and every other cell is unchanged."
)

INVARIANTS = [
    "grid is a 12-14 square with input palette exactly {0, 1, 6}",
    "three to five separated solid color-1 rectangles are present",
    "at least one square, one wider, and one taller solid blue rectangle are present",
    "ordinary non-anchor draws contain one allowed non-rectangular blue component",
    "one separated four-cell non-rectangular color-6 distractor is present",
    "all nonzero components have at least one zero-cell of Chebyshev separation",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_size": {
        "type": "int",
        "default": "sample-index schedule over 12..14",
        "valid": "12..14",
    },
    "n_extra_rects": {
        "type": "int",
        "default": "sample-index schedule over 0..2; canonical anchors use 1",
        "valid": "0..2",
    },
}

_BAND_OFFSETS = {None: 0, "easy": 0, "medium": 1, "hard": 2}

# Three consecutive demonstrations expose multiple dimensions for every aspect;
# the fourth sample repeats profile 0, so an exact-dimension lookup rival is
# answer-equivalent on the query rather than silently disagreeing there.
_RECT_PROFILES: tuple[tuple[tuple[int, int], tuple[int, int], tuple[int, int]], ...] = (
    ((1, 3), (3, 1), (2, 2)),
    ((2, 4), (4, 2), (3, 3)),
    ((3, 5), (5, 3), (2, 2)),
)

_BASE_NONRECT_SHAPES: dict[str, frozenset[tuple[int, int]]] = {
    "l4": frozenset({(0, 0), (1, 0), (2, 0), (2, 1)}),
    "t5": frozenset({(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)}),
    "zigzag4": frozenset({(0, 0), (0, 1), (1, 1), (1, 2)}),
}
_DECORATION_SHAPE = _BASE_NONRECT_SHAPES["l4"]


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in _BAND_OFFSETS:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown!r}")
    for name in AXES:
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")


def _draw_exact_or_override(
    ctx, overrides: dict[str, Any], name: str, default: int, lo: int, hi: int
) -> int:
    """Record an exact default while exposing the full lawful override range."""
    if overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _normalize(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = tuple(cells)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return frozenset((r - min_r, c - min_c) for r, c in cells)


def _rotate(shape: frozenset[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    height = max(r for r, _ in shape) + 1
    return _normalize((c, height - 1 - r) for r, c in shape)


def _reflect(shape: frozenset[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    width = max(c for _, c in shape) + 1
    return _normalize((r, width - 1 - c) for r, c in shape)


def _variants(shape: frozenset[tuple[int, int]]) -> tuple[frozenset[tuple[int, int]], ...]:
    found: set[frozenset[tuple[int, int]]] = set()
    current = shape
    for _ in range(4):
        found.add(_normalize(current))
        found.add(_reflect(current))
        current = _rotate(current)
    return tuple(sorted(found, key=lambda s: sorted(s)))


_NONRECT_VARIANTS = {
    name: _variants(shape) for name, shape in _BASE_NONRECT_SHAPES.items()
}
_NONRECT_FAMILY_BY_SHAPE = {
    shape: name for name, variants in _NONRECT_VARIANTS.items() for shape in variants
}
_DECORATION_VARIANTS = _variants(_DECORATION_SHAPE)


def _rect_cells(height: int, width: int) -> frozenset[tuple[int, int]]:
    return frozenset((r, c) for r in range(height) for c in range(width))


def _shape_dims(shape: frozenset[tuple[int, int]]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _candidate_positions(
    shape: frozenset[tuple[int, int]], height: int, width: int
) -> list[tuple[int, int]]:
    shape_h, shape_w = _shape_dims(shape)
    return [
        (r0, c0)
        for r0 in range(height - shape_h + 1)
        for c0 in range(width - shape_w + 1)
    ]


def _translated(
    shape: frozenset[tuple[int, int]], r0: int, c0: int
) -> frozenset[tuple[int, int]]:
    return frozenset((r0 + r, c0 + c) for r, c in shape)


def _has_padding(cells: frozenset[tuple[int, int]], occupied: set[tuple[int, int]]) -> bool:
    return all(
        (r + dr, c + dc) not in occupied
        for r, c in cells
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
    )


def _place_parts(
    height: int,
    width: int,
    parts: list[dict[str, Any]],
    rng,
) -> list[tuple[dict[str, Any], frozenset[tuple[int, int]]]]:
    """Place every component with one-cell inter-component padding.

    Largest-first randomized greedy placement is restarted from a fresh keyed
    permutation.  The small 12-14 canvases and at most seven compact parts give
    ample room, while the hard failure prevents silent branch loss.
    """
    for attempt in range(96):
        attempt_rng = rng
        order = list(parts)
        attempt_rng.shuffle(order)
        order.sort(key=lambda part: len(part["shape"]), reverse=True)
        occupied: set[tuple[int, int]] = set()
        placed: list[tuple[dict[str, Any], frozenset[tuple[int, int]]]] = []
        failed = False
        for part in order:
            positions = _candidate_positions(part["shape"], height, width)
            attempt_rng.shuffle(positions)
            for r0, c0 in positions:
                cells = _translated(part["shape"], r0, c0)
                if _has_padding(cells, occupied):
                    occupied.update(cells)
                    placed.append((part, cells))
                    break
            else:
                failed = True
                break
        if not failed:
            return placed
    raise RuntimeError(
        f"failed to place {len(parts)} padded components in {height}x{width}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    offset = _BAND_OFFSETS[difficulty]
    scheduled_size = 12 + ((sample_index + offset) % 3)
    grid_size = _draw_exact_or_override(
        ctx, overrides, "grid_size", scheduled_size, 12, 14
    )

    has_axis_override = any(
        name in overrides and overrides[name] is not None for name in AXES
    )
    canonical_anchor = not has_axis_override and sample_index % 4 == 0
    scheduled_extras = 1 if canonical_anchor else (sample_index + offset) % 3
    n_extra_rects = _draw_exact_or_override(
        ctx, overrides, "n_extra_rects", scheduled_extras, 0, 2
    )

    profile_index = sample_index % len(_RECT_PROFILES)
    wide, tall, square = _RECT_PROFILES[profile_index]
    rect_dims = [wide, tall, square]
    # Extra rectangles deliberately repeat dimensions already demonstrated in
    # the same grid.  They vary object count without creating a fixed-size
    # query branch unsupported by the demonstrations.
    for _extra_index in range(n_extra_rects):
        rect_dims.append(square)

    layout_rng = ctx.draw_rng(
        f"layout|size={grid_size}|profile={profile_index}|extras={n_extra_rects}|"
        f"anchor={int(canonical_anchor)}"
    )
    parts: list[dict[str, Any]] = [
        {"kind": "solid_rect", "color": 1, "shape": _rect_cells(rh, rw)}
        for rh, rw in rect_dims
    ]

    if not canonical_anchor:
        family_names = tuple(_BASE_NONRECT_SHAPES)
        family = family_names[(int(seed) + sample_index + offset) % len(family_names)]
        variants = _NONRECT_VARIANTS[family]
        parts.append(
            {
                "kind": f"nonrect_{family}",
                "color": 1,
                "shape": variants[layout_rng.randrange(len(variants))],
            }
        )

    parts.append(
        {
            "kind": "decoration",
            "color": 6,
            "shape": _DECORATION_VARIANTS[
                layout_rng.randrange(len(_DECORATION_VARIANTS))
            ],
        }
    )

    placed = _place_parts(grid_size, grid_size, parts, layout_rng)
    grid = full_grid(grid_size, grid_size, 0)
    for part, cells in placed:
        for row, col in cells:
            grid[row][col] = part["color"]

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={
            "grid_size": grid_size,
            "n_extra_rects": n_extra_rects,
            "canonical_anchor": canonical_anchor,
        },
    )
    if errors:
        raise AssertionError("generated invalid aspect lesson: " + "; ".join(errors))
    return grid


def _coerce_grid(grid) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)):
        raise ValueError("grid must be a list or tuple")
    result: list[list[int]] = []
    for row in grid:
        if isinstance(row, str):
            result.append([int(value) for value in row])
        elif isinstance(row, (list, tuple)):
            result.append(list(row))
        else:
            raise ValueError("grid rows must be lists, tuples, or digit strings")
    return result


def _components(grid: list[list[int]], color: int) -> list[frozenset[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    unseen = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] == color
    }
    result: list[frozenset[tuple[int, int]]] = []
    while unseen:
        start = next(iter(unseen))
        queue = deque([start])
        unseen.remove(start)
        cells: set[tuple[int, int]] = set()
        while queue:
            r, c = queue.popleft()
            cells.add((r, c))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (r + dr, c + dc)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        result.append(frozenset(cells))
    return result


def _component_record(cells: frozenset[tuple[int, int]]) -> dict[str, Any]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    height = max(rows) - min(rows) + 1
    width = max(cols) - min(cols) + 1
    normalized = _normalize(cells)
    solid = len(cells) == height * width
    aspect = "square" if height == width else "wide" if width > height else "tall"
    return {
        "cells": cells,
        "normalized": normalized,
        "height": height,
        "width": width,
        "size": len(cells),
        "solid": solid,
        "aspect": aspect,
        "family": None if solid else _NONRECT_FAMILY_BY_SHAPE.get(normalized),
    }


def _min_chebyshev_gap(left: set[tuple[int, int]], right: set[tuple[int, int]]) -> int:
    return min(
        max(abs(r1 - r2), abs(c1 - c2))
        for r1, c1 in left
        for r2, c2 in right
    )


def _analyze(grid) -> dict[str, Any]:
    errors: list[str] = []
    try:
        values = _coerce_grid(grid)
    except (TypeError, ValueError) as exc:
        return {"errors": [str(exc)]}
    if not values or not values[0]:
        return {"errors": ["grid must be non-empty"]}
    width = len(values[0])
    if any(len(row) != width for row in values):
        return {"errors": ["grid must be rectangular"]}
    height = len(values)
    if height != width or not 12 <= height <= 14:
        errors.append("grid must be square with size in 12..14")
    if any(type(value) is not int or not 0 <= value <= 9 for row in values for value in row):
        errors.append("every cell must be an integer ARC color in 0..9")
        return {"errors": errors, "grid": values}

    palette = {value for row in values for value in row}
    if palette != {0, 1, 6}:
        errors.append(f"input palette must be exactly {{0, 1, 6}}, got {sorted(palette)}")

    blue = [_component_record(cells) for cells in _components(values, 1)]
    decorations = [_component_record(cells) for cells in _components(values, 6)]
    solids = [component for component in blue if component["solid"]]
    nonrects = [component for component in blue if not component["solid"]]

    if not 3 <= len(solids) <= 5:
        errors.append(f"expected 3..5 solid blue rectangles, got {len(solids)}")
    aspects = {component["aspect"] for component in solids}
    for aspect in ("square", "wide", "tall"):
        if aspect not in aspects:
            errors.append(f"missing required {aspect} solid blue rectangle")
    for component in solids:
        if component["height"] > 5 or component["width"] > 5:
            errors.append("solid blue rectangle dimensions must not exceed 5")

    canonical_form = len(solids) == 4 and len(nonrects) == 0
    generated_form = len(nonrects) == 1 and nonrects[0]["family"] is not None
    if not (canonical_form or generated_form):
        errors.append(
            "expected either the four-rectangle canonical form or exactly one "
            "allowed non-rectangular blue component"
        )
    if len(nonrects) == 1 and nonrects[0]["family"] is None:
        errors.append("blue non-rectangle is not an allowed L/T/zigzag witness")

    if len(decorations) != 1:
        errors.append(f"expected exactly one color-6 component, got {len(decorations)}")
    else:
        decoration = decorations[0]
        if decoration["solid"] or decoration["size"] != 4:
            errors.append("color-6 distractor must be a non-solid four-cell component")
        if decoration["normalized"] not in _DECORATION_VARIANTS:
            errors.append("color-6 distractor must be an L tetromino")

    all_components = [component["cells"] for component in blue + decorations]
    for left_index in range(len(all_components)):
        for right_index in range(left_index + 1, len(all_components)):
            if _min_chebyshev_gap(
                set(all_components[left_index]), set(all_components[right_index])
            ) < 2:
                errors.append("nonzero components must have one-cell padding")
                break
        if errors and errors[-1] == "nonzero components must have one-cell padding":
            break

    return {
        "errors": errors,
        "grid": values,
        "height": height,
        "width": width,
        "palette": palette,
        "blue": blue,
        "solid_rectangles": solids,
        "blue_nonrectangles": nonrects,
        "decorations": decorations,
        "n_extra_rects": len(solids) - 3,
        "canonical_form": canonical_form,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors or not isinstance(meta, dict):
        return errors
    expected = {
        "grid_size": analysis["height"],
        "n_extra_rects": analysis["n_extra_rects"],
    }
    requested = meta.get("overrides") if isinstance(meta.get("overrides"), dict) else meta
    for name, actual in expected.items():
        value = requested.get(name)
        if value is not None and value != actual:
            errors.append(f"meta {name} requested {value!r}, observed {actual!r}")
    anchor = requested.get("canonical_anchor")
    if anchor is True and not analysis["canonical_form"]:
        errors.append("meta requested a canonical anchor but a blue non-rectangle is present")
    if anchor is False and analysis["canonical_form"]:
        errors.append("meta requested a teaching draw but the blue non-rectangle is absent")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("cannot observe overrides: " + "; ".join(analysis["errors"]))
    return {
        "grid_size": analysis["height"],
        "n_extra_rects": analysis["n_extra_rects"],
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors
    if not analysis["canonical_form"]:
        return ["canonical inputs have four solid blue rectangles and no blue non-rectangle"]
    return []


def _has_aspect(grid, aspect: str) -> bool:
    analysis = _analyze(grid)
    return not analysis.get("errors") and any(
        component["aspect"] == aspect for component in analysis["solid_rectangles"]
    )


def _has_blue_nonrectangle(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis.get("errors") and len(analysis["blue_nonrectangles"]) == 1


def _has_canonical_anchor(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis.get("errors") and analysis["canonical_form"]


def _has_extra_rectangle(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis.get("errors") and analysis["n_extra_rects"] > 0


def _has_larger_dimension_profile(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis.get("errors") and any(
        component["height"] >= 4 or component["width"] >= 4
        for component in analysis["solid_rectangles"]
    )


def _has_color6_distractor(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis.get("errors") and len(analysis["decorations"]) == 1


SEMANTIC_WITNESSES = {
    "square_blue_rectangle": lambda grid: _has_aspect(grid, "square"),
    "wider_blue_rectangle": lambda grid: _has_aspect(grid, "wide"),
    "taller_blue_rectangle": lambda grid: _has_aspect(grid, "tall"),
    "preserved_nonrectangular_blue_cue": _has_blue_nonrectangle,
    "canonical_four_rectangle_anchor": _has_canonical_anchor,
    "extra_rectangle_count_branch": _has_extra_rectangle,
    "larger_rectangle_dimension_profile": _has_larger_dimension_profile,
    "preserved_color6_distractor": _has_color6_distractor,
}


def rule_mirror(grid) -> list[list[int]]:
    """Diagnostic Python mirror; the canonical Racket rule remains authority."""
    values = _coerce_grid(grid)
    output = [row[:] for row in values]
    for cells in _components(values, 1):
        component = _component_record(cells)
        if not component["solid"]:
            continue
        color = 8 if component["aspect"] == "square" else 2 if component["aspect"] == "wide" else 3
        for row, col in cells:
            output[row][col] = color
    return output


def _competitor_all_blue_bbox(grid) -> list[list[int]]:
    values = _coerce_grid(grid)
    output = [row[:] for row in values]
    for cells in _components(values, 1):
        component = _component_record(cells)
        color = 8 if component["aspect"] == "square" else 2 if component["aspect"] == "wide" else 3
        for row, col in cells:
            output[row][col] = color
    return output


def _competitor_all_blue_to_8(grid) -> list[list[int]]:
    return [[8 if value == 1 else value for value in row] for row in _coerce_grid(grid)]


def _competitor_swap_wide_tall(grid) -> list[list[int]]:
    values = _coerce_grid(grid)
    output = [row[:] for row in values]
    for cells in _components(values, 1):
        component = _component_record(cells)
        if not component["solid"]:
            continue
        color = 8 if component["aspect"] == "square" else 3 if component["aspect"] == "wide" else 2
        for row, col in cells:
            output[row][col] = color
    return output


def _competitor_square_only(grid) -> list[list[int]]:
    values = _coerce_grid(grid)
    output = [row[:] for row in values]
    for cells in _components(values, 1):
        component = _component_record(cells)
        if component["solid"] and component["aspect"] == "square":
            for row, col in cells:
                output[row][col] = 8
    return output


def _competitor_recolor_color6_too(grid) -> list[list[int]]:
    output = rule_mirror(grid)
    values = _coerce_grid(grid)
    for cells in _components(values, 6):
        component = _component_record(cells)
        color = 8 if component["aspect"] == "square" else 2 if component["aspect"] == "wide" else 3
        for row, col in cells:
            output[row][col] = color
    return output


_LESSON_COMPETITORS = {
    "recolor every blue bounding box, even when it is not solid": _competitor_all_blue_bbox,
    "recolor every blue component cyan": _competitor_all_blue_to_8,
    "swap the wider and taller output colors": _competitor_swap_wide_tall,
    "recolor only square blue rectangles": _competitor_square_only,
    "apply the aspect mapping to the color-6 marker too": _competitor_recolor_color6_too,
}


def _dimension_lookup_output(
    grid, learned: dict[tuple[int, int], int]
) -> list[list[int]]:
    values = _coerce_grid(grid)
    output = [row[:] for row in values]
    for cells in _components(values, 1):
        component = _component_record(cells)
        if not component["solid"]:
            continue
        color = learned.get((component["height"], component["width"]))
        if color is not None:
            for row, col in cells:
                output[row][col] = color
    return output


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible rival changes the query answer."""
    reasons: list[str] = []
    for index, pair in enumerate([*demos, query]):
        label = f"demo {index}" if index < len(demos) else "query"
        if self_check(pair["input"]):
            reasons.append(f"{label} input is outside the teaching grammar")
            continue
        expected = rule_mirror(pair["input"])
        if expected != pair["output"]:
            reasons.append(f"{label} output does not match the aspect rule")
    if reasons:
        return reasons

    for name, competitor in _LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competing rule '{name}' fits every demo but answers the query differently"
            )

    learned: dict[tuple[int, int], int] = {}
    for demo in demos:
        for component in _analyze(demo["input"])["solid_rectangles"]:
            key = (component["height"], component["width"])
            learned[key] = 8 if component["aspect"] == "square" else 2 if component["aspect"] == "wide" else 3
    if all(_dimension_lookup_output(demo["input"], learned) == demo["output"] for demo in demos):
        rival_query = _dimension_lookup_output(query["input"], learned)
        if rival_query != query["output"]:
            reasons.append(
                "exact-dimension lookup fits every demo but leaves an unseen query size unchanged"
            )
    return reasons
