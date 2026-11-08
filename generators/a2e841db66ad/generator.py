"""Input sampler for ARC task a2e841db66ad — header count selects height.

The canonical rule counts every blue (1) cell in the top row, selects the
unique body object whose tight bounding-box height equals that count, crops the
object, and recolors its cells cyan (8).  This module samples inputs only; the
Racket rule remains the label authority.
"""
from __future__ import annotations

from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a2e841db66ad"
TASK_ID = GENERATOR_ID
RULE_HASH = "b5be85c39dab"
VERSION = "3.0.0"
SUMMARY = (
    "Count all blue cells in the top row. Select the unique body component "
    "whose tight bounding-box height equals that count, crop it, and recolor "
    "its occupied cells cyan (8). Header placement varies so count, not run "
    "length or left packing, is required."
)
SOLID_OUTPUT_JUSTIFICATION = (
    "The selected canonical Racket rule crops the unique height-matched body "
    "component and recolors every occupied cell cyan; when that component is "
    "a solid rectangle, the lawful cropped output is therefore entirely color 8."
)

EXAMPLES_NEEDED = 4
HEADER_LAYOUTS = ("packed_left", "shifted_run", "scattered")
_HEIGHTS = tuple(range(9, 23))
_WIDTHS = tuple(range(15, 23))
_SELECTED_ROWS = tuple(range(2, 7))
_COMPONENT_COUNTS = tuple(range(3, 6))
_COMPONENT_HEIGHTS = tuple(range(1, 9))
_PALETTE = (2, 3, 4, 5, 6, 7, 9)
_CANONICAL_PROFILES = ((9, 15), (10, 16), (11, 17))
_HEADER_SCHEDULE = ("scattered", "packed_left", "scattered", "shifted_run")

INVARIANTS = [
    "the top row contains 2..6 blue cells and no other non-background color",
    "the body contains 3..5 separated, single-color, four-connected components",
    "body component colors and bounding-box heights are pairwise distinct",
    "exactly one component height equals the number of blue header cells",
    "the selected component is cropped and recolored to cyan (8)",
]

AXES = {
    "height": {
        "type": "int",
        "default": "9..22; scheduled canonical-profile anchors at residues 0 and 1",
        "valid": "9..22",
    },
    "width": {
        "type": "int",
        "default": "15..22; scheduled canonical-profile anchors at residues 0 and 1",
        "valid": "15..22",
    },
    "selected_rows": {
        "type": "int",
        "default": "weighted full-domain draw",
        "valid": "2..6",
    },
    "n_components": {
        "type": "int",
        "default": "3..5; canonical-profile anchors use 3",
        "valid": "3..5",
    },
    "header_layout": {
        "type": "str",
        "default": "periodic scattered/packed/scattered/shifted curriculum",
        "valid": "|".join(HEADER_LAYOUTS),
    },
}

# Every advertised endpoint product is constructed directly, including the
# tight 9x15 / k=6 / five-component / scattered case.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, or string)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool, float, or string)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty is not None:
        if type(difficulty) is not str:
            raise TypeError("difficulty must be None or one of easy/medium/hard")
        if difficulty not in ("easy", "medium", "hard"):
            raise ValueError("difficulty must be None or one of easy/medium/hard")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")

    domains: dict[str, Sequence[Any]] = {
        "height": _HEIGHTS,
        "width": _WIDTHS,
        "selected_rows": _SELECTED_ROWS,
        "n_components": _COMPONENT_COUNTS,
        "header_layout": HEADER_LAYOUTS,
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if name == "header_layout":
            if type(value) is not str:
                raise TypeError("header_layout override must be a string")
        elif type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool, float, or string)")
        if value not in domains[name]:
            raise ValueError(f"{name} override {value!r} outside {tuple(domains[name])!r}")


def _is_overridden(overrides: dict[str, Any], name: str) -> bool:
    return name in overrides and overrides[name] is not None


def _weighted_domain(domain: Sequence[Any], favored: Sequence[Any]) -> tuple[Any, ...]:
    """Keep every legal value reachable while applying a mild band preference."""
    return tuple(domain) + tuple(favored) * 6


def _draw_choice(ctx, overrides: dict[str, Any], name: str, domain: Sequence[Any], default: Any):
    options = tuple(domain) if _is_overridden(overrides, name) else (default,)
    return ctx.draw_choice(name, options)


def _draw_axes(ctx, sample_index: int, difficulty: str | None, overrides: dict[str, Any]):
    core = sample_index % 4 in (0, 1)
    profile_h, profile_w = _CANONICAL_PROFILES[sample_index % len(_CANONICAL_PROFILES)]

    if core:
        height_default: Any = profile_h
        width_default: Any = profile_w
        count_default: Any = 3
    else:
        if difficulty == "easy":
            h_favored, w_favored, n_favored = (9, 10, 11), (15, 16, 17), (3,)
        elif difficulty == "hard":
            h_favored, w_favored, n_favored = (19, 20, 21, 22), (20, 21, 22), (5,)
        else:
            h_favored, w_favored, n_favored = (13, 14, 15, 16), (17, 18, 19), (4,)
        height_default = ctx.draw_rng("height_default").choice(_weighted_domain(_HEIGHTS, h_favored))
        width_default = ctx.draw_rng("width_default").choice(_weighted_domain(_WIDTHS, w_favored))
        count_default = ctx.draw_rng("n_components_default").choice(
            _weighted_domain(_COMPONENT_COUNTS, n_favored)
        )

    if difficulty == "easy":
        k_favored = (2, 3)
    elif difficulty == "hard":
        k_favored = (5, 6)
    else:
        k_favored = (3, 4, 5)
    k_default = ctx.draw_rng("selected_rows_default").choice(
        _weighted_domain(_SELECTED_ROWS, k_favored)
    )
    layout_default = _HEADER_SCHEDULE[sample_index % len(_HEADER_SCHEDULE)]

    height = _draw_choice(ctx, overrides, "height", _HEIGHTS, height_default)
    width = _draw_choice(ctx, overrides, "width", _WIDTHS, width_default)
    selected_rows = _draw_choice(
        ctx, overrides, "selected_rows", _SELECTED_ROWS, k_default
    )
    n_components = _draw_choice(
        ctx, overrides, "n_components", _COMPONENT_COUNTS, count_default
    )
    header_layout = _draw_choice(
        ctx, overrides, "header_layout", HEADER_LAYOUTS, layout_default
    )
    return height, width, selected_rows, n_components, header_layout


def _header_columns(width: int, count: int, layout: str, rng) -> tuple[tuple[int, ...], int]:
    if layout == "packed_left":
        cols = tuple(range(count))
        return cols, count
    if layout == "shifted_run":
        start = rng.randint(1, width - count)
        cols = tuple(range(start, start + count))
        return cols, count

    # A non-contiguous count with a bounded span that is also realizable as a
    # distractor height in the body. Including both endpoints makes the span
    # exact and gives a decisive count-vs-span counterexample.
    span = rng.randint(count + 1, 8)
    start = rng.randint(0, width - span)
    interior = list(range(start + 1, start + span - 1))
    middle = rng.sample(interior, count - 2) if count > 2 else []
    cols = tuple(sorted((start, start + span - 1, *middle)))
    return cols, span


def _component_heights(count: int, selected: int, header_span: int, layout: str, rng) -> list[int]:
    distractors: list[int] = []
    if layout == "scattered":
        # This exact-height distractor makes the canonical-fitting blue-span
        # shortcut return a defined but wrong object.
        distractors.append(header_span)
    remaining = [h for h in _COMPONENT_HEIGHTS if h != selected and h not in distractors]
    rng.shuffle(remaining)
    distractors.extend(remaining[: count - 1 - len(distractors)])
    return [selected, *distractors]


def _component_widths(n: int, canvas_width: int, rng) -> list[int]:
    # Reserve one blank column between neighboring bounding boxes. Start from
    # one-column bars, then spend a bounded random budget on wider shapes.
    widths = [1] * n
    budget = canvas_width - (n - 1) - n
    spend = rng.randint(0, min(budget, 3 * n))
    while spend:
        choices = [i for i, width in enumerate(widths) if width < 4]
        if not choices:
            break
        i = rng.choice(choices)
        widths[i] += 1
        spend -= 1
    return widths


def _shape(height: int, width: int, rng) -> list[tuple[int, int]]:
    """Create a connected shape with exactly the requested bounding box."""
    cells = {(r, 0) for r in range(height)}
    arm_row = rng.randrange(height)
    cells.update((arm_row, c) for c in range(width))

    available = height * width - len(cells)
    extra = rng.randint(0, available) if available else 0
    for _ in range(extra):
        frontier = []
        for r, c in cells:
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < height and 0 <= cc < width and (rr, cc) not in cells:
                    frontier.append((rr, cc))
        if not frontier:
            break
        cells.add(rng.choice(frontier))
    return sorted(cells)


def _column_positions(width: int, component_widths: Sequence[int], rng) -> list[int]:
    n = len(component_widths)
    gaps = [0] + [1] * (n - 1) + [0]
    slack = width - sum(component_widths) - (n - 1)
    for _ in range(slack):
        gaps[rng.randrange(n + 1)] += 1
    starts: list[int] = []
    cursor = gaps[0]
    for i, component_width in enumerate(component_widths):
        starts.append(cursor)
        cursor += component_width + gaps[i + 1]
    return starts


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height, width, selected_rows, n_components, header_layout = _draw_axes(
        ctx, sample_index, difficulty, overrides
    )

    grid = full_grid(height, width, 0)
    header_cols, header_span = _header_columns(
        width, selected_rows, header_layout, ctx.draw_rng("header_cells")
    )
    for col in header_cols:
        grid[0][col] = 1

    heights = _component_heights(
        n_components,
        selected_rows,
        header_span,
        header_layout,
        ctx.draw_rng("component_heights"),
    )
    colors = list(ctx.draw_rng("component_colors").sample(_PALETTE, n_components))
    specs = list(zip(heights, colors))
    ctx.draw_rng("component_order").shuffle(specs)

    widths = _component_widths(n_components, width, ctx.draw_rng("component_widths"))
    starts = _column_positions(width, widths, ctx.draw_rng("component_columns"))
    row_rng = ctx.draw_rng("component_rows")
    for index, ((component_height, color), component_width, col0) in enumerate(
        zip(specs, widths, starts)
    ):
        row0 = row_rng.randint(1, height - component_height)
        shape = _shape(component_height, component_width, ctx.draw_rng(f"shape_{index}"))
        for dr, dc in shape:
            if grid[row0 + dr][col0 + dc] != 0:
                raise RuntimeError("constructive component placement collided")
            grid[row0 + dr][col0 + dc] = color

    errors = self_check(grid)
    if errors:
        raise RuntimeError("generator constructed an invalid grid: " + "; ".join(errors))
    return grid


def _components(grid: Sequence[Sequence[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(1, height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        1 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            components.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "r1": min(rows),
                    "r2": max(rows),
                    "c1": min(cols),
                    "c2": max(cols),
                }
            )
    return components


def _bbox_height(component: dict[str, Any]) -> int:
    return component["r2"] - component["r1"] + 1


def _header_layout(grid: Sequence[Sequence[int]]) -> str:
    cols = [col for col, value in enumerate(grid[0]) if value == 1]
    if not cols:
        raise ValueError("header contains no blue cells")
    contiguous = cols == list(range(cols[0], cols[-1] + 1))
    if contiguous and cols[0] == 0:
        return "packed_left"
    if contiguous:
        return "shifted_run"
    return "scattered"


def observe_overrides(grid):
    """Recover every advertised axis exactly from returned pixels."""
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "selected_rows": sum(value == 1 for value in grid[0]),
        "n_components": len(_components(grid)),
        "header_layout": _header_layout(grid),
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    height = len(grid)
    errors: list[str] = []
    if height not in _HEIGHTS:
        errors.append(f"height {height} outside 9..22")
    if width not in _WIDTHS:
        errors.append(f"width {width} outside 15..22")

    header = grid[0]
    if any(value not in (0, 1) for value in header):
        errors.append("top row must contain only background and blue header cells")
    selected = sum(value == 1 for value in header)
    if selected not in _SELECTED_ROWS:
        errors.append(f"blue header count {selected} outside 2..6")
    try:
        layout = _header_layout(grid)
        if layout not in HEADER_LAYOUTS:
            errors.append("unrecognized header layout")
    except ValueError as exc:
        errors.append(str(exc))

    if any(value in (1, 8) for row in grid[1:] for value in row):
        errors.append("body may not contain header blue or output cyan")
    components = _components(grid)
    if len(components) not in _COMPONENT_COUNTS:
        errors.append(f"body component count {len(components)} outside 3..5")
    colors = [component["color"] for component in components]
    if len(set(colors)) != len(colors):
        errors.append("body component colors must be pairwise distinct")
    heights = [_bbox_height(component) for component in components]
    if any(component_height not in _COMPONENT_HEIGHTS for component_height in heights):
        errors.append(f"component heights must lie in 1..8; got {heights}")
    if len(set(heights)) != len(heights):
        errors.append(f"component heights must be pairwise distinct; got {heights}")
    if heights.count(selected) != 1:
        errors.append(
            f"expected exactly one component of header-selected height {selected}; got {heights}"
        )
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _crop_recolor(component: dict[str, Any]) -> list[list[int]]:
    out_height = _bbox_height(component)
    out_width = component["c2"] - component["c1"] + 1
    output = full_grid(out_height, out_width, 0)
    for row, col in component["cells"]:
        output[row - component["r1"]][col - component["c1"]] = 8
    return output


def _select_by_height(grid, wanted_height: int) -> list[list[int]]:
    components = sorted(_components(grid), key=lambda component: (component["r1"], component["c1"]))
    matches = [component for component in components if _bbox_height(component) == wanted_height]
    if not matches:
        raise ValueError(f"no body component has bounding-box height {wanted_height}")
    return _crop_recolor(matches[0])


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid rule input: " + "; ".join(errors))
    selected = sum(value == 1 for value in grid[0])
    return _select_by_height(grid, selected)


def _blue_span_selects_height(grid):
    """Plausible canonical shortcut: use blue run span instead of blue count."""
    blue_cols = [col for col, value in enumerate(grid[0]) if value == 1]
    if not blue_cols:
        raise ValueError("header contains no blue cells")
    span = blue_cols[-1] - blue_cols[0] + 1
    return _select_by_height(grid, span)


def _is_scattered_counterexample(grid) -> bool:
    try:
        return (
            not self_check(grid)
            and _header_layout(grid) == "scattered"
            and _blue_span_selects_height(grid) != rule_mirror(grid)
        )
    except (TypeError, ValueError):
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "scattered_header": _is_scattered_counterexample,
}
SEMANTIC_RIVALS = {"blue_span_selects_height": _blue_span_selects_height}
WITNESS_RIVALS = {"scattered_header": ["blue_span_selects_height"]}
CANONICAL_SHORTCUTS = {"blue_span_selects_height": _blue_span_selects_height}
LESSON_COMPETITORS = {"blue_span_selects_height": _blue_span_selects_height}


def _pair_errors(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input is invalid: {'; '.join(errors)}"]
    try:
        expected = rule_mirror(pair["input"])
    except ValueError as exc:
        return [f"{label} rule evaluation failed: {exc}"]
    if pair["output"] != expected:
        return [f"{label} output does not match the header-count rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson only when a named rival survives demos and changes query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    reasons: list[str] = []
    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        pair_errors = _pair_errors(demo, f"demo {index}")
        reasons.extend(pair_errors)
        if not pair_errors:
            valid_demos.append(demo)
    reasons.extend(_pair_errors(query, "query"))
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo["output"] for demo in valid_demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} fits every demonstration but changes the query answer"
            )
    return reasons
