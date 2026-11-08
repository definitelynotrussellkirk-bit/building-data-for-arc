"""Task-linked generator for ARC task ``d8d37830884c``.

The selected Racket authority finds same-colour 4-connected nonzero objects.
Every object containing exactly six cells is recoloured red (2); every other
object is recoloured blue (1).  The scheduled curriculum interleaves exact
10x10 gray canonical-profile anchors with non-gray six-cell counterexamples,
so lessons cannot be solved by the canonical-fitting shortcut "only gray
six-cell objects become red".  Every four-item schedule window balances two
anchors and two counterexamples.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]
Cell = tuple[int, int]

GENERATOR_ID = "d8d37830884c"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "0b5bfbd1622f"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.40

SUMMARY = (
    "Find every same-colour 4-connected nonzero object. Recolour objects of "
    "exactly six cells red(2), and recolour all other object sizes blue(1). "
    "Four-slot lessons contain two 10x10 gray anchors and two non-gray "
    "six-cell witnesses that refute the strongest canonical colour shortcut."
)

INVARIANTS = [
    "background is color 0 and input object colors are 3..9",
    "there is at least one six-cell object and at least one non-six-cell object",
    "same-colour 4-connected components are the rule objects",
    "all six-cell objects share one recoverable input color",
    "all non-six-cell objects share one recoverable input color",
    "ordinary four-pair schedule windows contain two canonical anchors and two non-gray six-cell witnesses",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "10x10 canonical anchor / scheduled by band",
        "valid": "10..22",
    },
    "grid_w": {
        "type": "int",
        "default": "10x10 canonical anchor / scheduled by band",
        "valid": "10..22",
    },
    "n_size6": {
        "type": "int",
        "default": "scheduled 1..3",
        "valid": "1..3",
    },
    "n_other": {
        "type": "int",
        "default": "scheduled 1..5",
        "valid": "1..5",
    },
    "size6_color": {
        "type": "color",
        "default": "gray(5) anchor / scheduled non-gray 3..9",
        "valid": "3..9",
    },
    "other_color": {
        "type": "color",
        "default": "gray(5) anchor / scheduled 3..9",
        "valid": "3..9",
    },
}

# Every boundary and pairwise Cartesian combination above is constructible.
# Declaring an empty matrix opts into the strict rejection policy.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = (
    "canonical_gray_anchor_a",
    "canonical_gray_anchor_b",
    "non_gray_shape_witness",
    "non_gray_palette_witness",
)

_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_COLORS = tuple(range(3, 10))
_NON_GRAY_COLORS = (3, 4, 6, 7, 8, 9)
_OTHER_SIZES = (1, 2, 3, 4, 5, 7, 8)

# All templates fit in a 3x3 envelope.  Dense scenes deliberately fall back to
# 2x3 rectangles for the red class, while sparse scenes exercise these varied
# six-cell geometries.
_SIZE6_TEMPLATES: tuple[tuple[Cell, ...], ...] = (
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 1), (2, 2)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (1, 2)),
    ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2), (2, 1)),
)

_OTHER_TEMPLATES: dict[int, tuple[Cell, ...]] = {
    1: ((0, 0),),
    2: ((0, 0), (0, 1)),
    3: ((0, 0), (1, 0), (1, 1)),
    4: ((0, 0), (0, 1), (1, 0), (1, 1)),
    5: ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    7: ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1), (2, 2)),
    8: (
        (0, 0), (0, 1), (0, 2),
        (1, 0),         (1, 2),
        (2, 0), (2, 1), (2, 2),
    ),
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the auditable four-slot curriculum residue."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _scheduled_values(seed: int, sample_index: int, difficulty) -> dict[str, int]:
    """Full-domain defaults; difficulty changes dimensions, never legality."""
    del seed
    residue = int(sample_index) % 4
    cycle = int(sample_index) // 4
    if residue in (0, 1):
        return {
            "grid_h": 10,
            "grid_w": 10,
            "n_size6": 2,
            "n_other": 3 + (cycle + residue) % 3,
            "size6_color": 5,
            "other_color": 5,
        }

    dimension_bands = {
        None: (10, 22),
        "easy": (10, 14),
        "medium": (12, 18),
        "hard": (16, 22),
    }
    lo, hi = dimension_bands[difficulty]
    span = hi - lo + 1
    return {
        "grid_h": lo + (cycle * 4 + residue) % span,
        "grid_w": lo + (cycle * 7 + residue * 2) % span,
        "n_size6": 1 + (cycle + residue) % 3,
        "n_other": 1 + (cycle * 3 + residue) % 5,
        "size6_color": _NON_GRAY_COLORS[(cycle * 2 + residue) % 6],
        "other_color": _COLORS[(cycle * 2 + residue + 2) % 7],
    }


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    bounds = {
        "grid_h": (10, 22),
        "grid_w": (10, 22),
        "n_size6": (1, 3),
        "n_other": (1, 5),
        "size6_color": (3, 9),
        "other_color": (3, 9),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside {lo}..{hi}")


def _draw_axis(ctx, name: str, scheduled: int, lo: int, hi: int) -> int:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, scheduled, scheduled)


def _normalize(cells: Iterable[Cell]) -> tuple[Cell, ...]:
    cells = tuple(cells)
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _transform(cells: tuple[Cell, ...], code: int) -> tuple[Cell, ...]:
    transformed = list(cells)
    if code >= 4:
        transformed = [(row, -col) for row, col in transformed]
    for _ in range(code % 4):
        transformed = [(col, -row) for row, col in transformed]
    return _normalize(transformed)


def _paint(grid: Grid, top: int, left: int, cells: tuple[Cell, ...], color: int) -> None:
    for dr, dc in cells:
        row, col = top + dr, left + dc
        if grid[row][col] != 0:
            raise AssertionError(f"layout overlap at {(row, col)}")
        grid[row][col] = color


def _sparse_scene(
    h: int,
    w: int,
    n_size6: int,
    n_other: int,
    size6_color: int,
    other_color: int,
    *,
    seed: int,
    sample_index: int,
) -> Grid:
    slots = [
        (0, 0),
        (0, w - 3),
        (h // 2 - 1, w // 2 - 1),
        (h - 3, 0),
        (h - 3, w - 3),
    ]
    grid = full_grid(h, w, 0)
    cursor = 0
    for index in range(n_size6):
        template_index = (int(seed) + int(sample_index) * 3 + index * 2) % len(_SIZE6_TEMPLATES)
        code = (int(seed) * 3 + int(sample_index) + index) % 8
        cells = _transform(_SIZE6_TEMPLATES[template_index], code)
        _paint(grid, *slots[cursor], cells, size6_color)
        cursor += 1
    for index in range(n_other):
        size = _OTHER_SIZES[(int(sample_index) + int(seed) + index * 3) % len(_OTHER_SIZES)]
        code = (int(seed) + int(sample_index) * 5 + index) % 8
        cells = _transform(_OTHER_TEMPLATES[size], code)
        _paint(grid, *slots[cursor], cells, other_color)
        cursor += 1
    return grid


def _dense_scene(
    h: int,
    w: int,
    n_size6: int,
    n_other: int,
    size6_color: int,
    other_color: int,
    *,
    seed: int,
    sample_index: int,
) -> Grid:
    grid = full_grid(h, w, 0)
    rectangle = _SIZE6_TEMPLATES[0]
    size_slots = [
        (0, 0),
        (0, w // 2 - 1),
        (h // 2 - 1, 0),
    ]
    for index in range(n_size6):
        cells = _transform(rectangle, (int(seed) + int(sample_index) + index) % 2)
        _paint(grid, *size_slots[index], cells, size6_color)

    large_slots = [
        (h // 2 - 1, w // 2 - 1),
        (h - 3, w - 3),
    ]
    point_slots = [
        (0, w - 1),
        (max(3, h // 2 - 2), w - 1),
        (h - 2, 2),
    ]
    for index in range(n_other):
        if index < len(large_slots):
            size = _OTHER_SIZES[(int(sample_index) * 2 + int(seed) + index * 3) % len(_OTHER_SIZES)]
            code = (int(seed) + int(sample_index) * 5 + index) % 8
            cells = _transform(_OTHER_TEMPLATES[size], code)
            top, left = large_slots[index]
        else:
            cells = _OTHER_TEMPLATES[1]
            top, left = point_slots[index - len(large_slots)]
        _paint(grid, top, left, cells, other_color)
    return grid


def _build_scene(
    h: int,
    w: int,
    n_size6: int,
    n_other: int,
    size6_color: int,
    other_color: int,
    *,
    seed: int,
    sample_index: int,
) -> Grid:
    if n_size6 + n_other <= 5:
        return _sparse_scene(
            h,
            w,
            n_size6,
            n_other,
            size6_color,
            other_color,
            seed=seed,
            sample_index=sample_index,
        )
    return _dense_scene(
        h,
        w,
        n_size6,
        n_other,
        size6_color,
        other_color,
        seed=seed,
        sample_index=sample_index,
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a lawful scene with six exact, pixel-observable controls."""
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = _scheduled_values(seed, sample_index, difficulty)
    values = {
        "grid_h": _draw_axis(ctx, "grid_h", scheduled["grid_h"], 10, 22),
        "grid_w": _draw_axis(ctx, "grid_w", scheduled["grid_w"], 10, 22),
        "n_size6": _draw_axis(ctx, "n_size6", scheduled["n_size6"], 1, 3),
        "n_other": _draw_axis(ctx, "n_other", scheduled["n_other"], 1, 5),
        "size6_color": _draw_axis(ctx, "size6_color", scheduled["size6_color"], 3, 9),
        "other_color": _draw_axis(ctx, "other_color", scheduled["other_color"], 3, 9),
    }
    grid = _build_scene(
        values["grid_h"],
        values["grid_w"],
        values["n_size6"],
        values["n_other"],
        values["size6_color"],
        values["other_color"],
        seed=int(seed),
        sample_index=int(sample_index),
    )
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid size-classification scene: " + "; ".join(errors))
    realized = observe_overrides(grid)
    if realized != values:
        raise AssertionError(f"constructed axes drifted: expected {values}, observed {realized}")
    return grid


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["rows must be nonempty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _components(grid: Grid) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    result: list[dict[str, Any]] = []
    for start_row in range(h):
        for start_col in range(w):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            cells: list[Cell] = []
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [row for row, _ in cells]
            cols = [col for _, col in cells]
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "size": len(cells),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return result


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors, "components": []}
    normalized = [list(row) for row in grid]
    h, w = len(normalized), len(normalized[0])
    if not 10 <= h <= 22:
        errors.append(f"grid height must be 10..22, found {h}")
    if not 10 <= w <= 22:
        errors.append(f"grid width must be 10..22, found {w}")
    foreground = {value for row in normalized for value in row if value != 0}
    if not foreground:
        errors.append("input must contain nonzero objects")
    if any(color not in _COLORS for color in foreground):
        errors.append("input object colors must be in 3..9 (not output colors 1 or 2)")

    components = _components(normalized)
    six = [component for component in components if component["size"] == 6]
    other = [component for component in components if component["size"] != 6]
    if not 1 <= len(six) <= 3:
        errors.append(f"expected 1..3 six-cell objects, found {len(six)}")
    if not 1 <= len(other) <= 5:
        errors.append(f"expected 1..5 non-six-cell objects, found {len(other)}")
    six_colors = {component["color"] for component in six}
    other_colors = {component["color"] for component in other}
    if len(six_colors) != 1:
        errors.append("all six-cell objects must share one recoverable input color")
    if len(other_colors) != 1:
        errors.append("all non-six-cell objects must share one recoverable input color")

    # Different colors are separate Racket objects even when adjacent, but the
    # selected generator deliberately keeps a visible background separator.
    for row in range(h):
        for col in range(w):
            value = normalized[row][col]
            if value == 0:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = row + dr, col + dc
                if 0 <= nr < h and 0 <= nc < w:
                    neighbor = normalized[nr][nc]
                    if neighbor not in (0, value):
                        errors.append("different-color objects may not touch orthogonally")
                        break
            if errors and errors[-1] == "different-color objects may not touch orthogonally":
                break
        if errors and errors[-1] == "different-color objects may not touch orthogonally":
            break

    return {
        "errors": sorted(set(errors)),
        "grid": normalized,
        "grid_h": h,
        "grid_w": w,
        "components": components,
        "six": six,
        "other": other,
        "six_colors": six_colors,
        "other_colors": other_colors,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return structural diagnostics; malformed inputs never raise."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid generated scene: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_size6": len(analysis["six"]),
        "n_other": len(analysis["other"]),
        "size6_color": next(iter(analysis["six_colors"])),
        "other_color": next(iter(analysis["other_colors"])),
    }


def strict_canonical_like(grid) -> list[str]:
    """Canonical manifold: lawful 10x10 scenes using only gray(5)."""
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if analysis["grid_h"] != 10 or analysis["grid_w"] != 10:
        errors.append("canonical profile is exactly 10x10")
    palette = {value for row in analysis["grid"] for value in row}
    if palette != {0, 5}:
        errors.append(f"canonical profile palette must be {{0, 5}}, found {sorted(palette)}")
    return errors


def rule_mirror(grid: Any) -> Grid:
    """Faithful Python mirror; the selected Racket source remains authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene: " + "; ".join(analysis["errors"]))
    output = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    for component in analysis["components"]:
        color = 2 if component["size"] == 6 else 1
        for row, col in component["cells"]:
            output[row][col] = color
    return output


def _gray_only_size_six(grid: Any) -> Grid:
    """Wrong but canonical-fitting rule: non-gray six-cell objects stay blue."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene: " + "; ".join(analysis["errors"]))
    output = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    for component in analysis["components"]:
        color = (
            2
            if component["size"] == 6 and component["color"] == 5
            else 1
        )
        for row, col in component["cells"]:
            output[row][col] = color
    return output


def _non_gray_size6(grid: Any) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and any(
        component["color"] != 5 for component in analysis["six"]
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "non_gray_size6": _non_gray_size6,
}
SEMANTIC_RIVALS: dict[str, Callable[[Any], Grid]] = {
    "gray_only_size_six": _gray_only_size_six,
}
WITNESS_RIVALS = {"non_gray_size6": ["gray_only_size_six"]}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a declared rival survives demos and changes query."""
    errors: list[str] = []
    if not isinstance(demos, list) or len(demos) < 1:
        return ["lesson requires at least one demonstration"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            errors.append(f"demo {index} must contain input and output grids")
            continue
        try:
            expected = rule_mirror(demo["input"])
        except (TypeError, ValueError) as exc:
            errors.append(f"invalid demo {index}: {exc}")
            continue
        if expected != demo["output"]:
            errors.append(f"demo {index} output disagrees with the pinned rule")
    if errors:
        return errors

    try:
        expected_query = rule_mirror(query["input"])
    except (TypeError, ValueError) as exc:
        return [f"invalid query: {exc}"]

    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(
                rival(demo["input"]) == demo["output"] for demo in demos
            )
            changes_query = rival(query["input"]) != expected_query
        except (TypeError, ValueError) as exc:
            errors.append(f"competitor {name!r} failed: {exc}")
            continue
        if survives and changes_query:
            errors.append(
                f"competitor {name!r} fits every demo but changes the query answer"
            )
    return errors
