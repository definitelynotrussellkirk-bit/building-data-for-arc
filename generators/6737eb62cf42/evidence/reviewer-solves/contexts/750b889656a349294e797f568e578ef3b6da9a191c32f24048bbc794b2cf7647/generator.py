"""Generator for 6737eb62cf42 — crop the tight non-zero bounding box.

The selected Racket program remains the label authority.  Version 3 replaces a
large set of dead or singleton controls with four exact, pixel-observable axes.
The ordinary 20-slot schedule alternates canonical-profile examples with
singleton-extreme counterexamples, so lessons teach that *every* non-zero cell
contributes to the crop, not merely repeated colors or the two largest groups.
"""
from __future__ import annotations

from collections import Counter, deque
from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6737eb62cf42"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "debb1a8a129a"
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 20
MIN_STRICT_FRAC = 0.45

SUMMARY = (
    "Place two to four non-zero colors inside a padded canonical-scale canvas. "
    "The answer is the smallest rectangular subgrid containing every non-zero "
    "cell, preserving colors and internal zeros. Ordinary lessons alternate "
    "paired-object scenes with a singleton color that alone defines the lower-"
    "right crop boundary."
)

INVARIANTS = [
    "background is color 0 and occurs outside the active rectangle",
    "the non-zero bounding box is at least 3x3 and strictly padded on all sides",
    "two to four distinct non-zero colors occur",
    "the crop preserves every cell, including internal background zeros",
]

PROFILE_DIMENSIONS = {
    "canonical_8x9_crop4x6": (8, 9, 4, 6),
    "canonical_9x10_crop6x6": (9, 10, 6, 6),
    "canonical_10x10_crop4x6": (10, 10, 4, 6),
    "canonical_8x11_crop5x8": (8, 11, 5, 8),
    "canonical_9x10_crop5x7": (9, 10, 5, 7),
}
SCHEDULE_PROFILES = tuple(PROFILE_DIMENSIONS)
PLACEMENTS = ("upper_left", "upper_right", "lower_left", "lower_right")
TEXTURES = ("paired_objects", "singleton_extreme")

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five canonical input/output shape profiles in a 20-slot schedule",
        "valid": "canonical_8x9_crop4x6|canonical_9x10_crop6x6|canonical_10x10_crop4x6|canonical_8x11_crop5x8|canonical_9x10_crop5x7",
    },
    "placement": {
        "type": "str",
        "default": "cyclic upper_left|upper_right|lower_left|lower_right",
        "valid": "upper_left|upper_right|lower_left|lower_right",
    },
    "palette_size": {
        "type": "int",
        "default": "2 on paired slots; 3 on singleton slots",
        "valid": "2..4",
    },
    "texture": {
        "type": "str",
        "default": "alternating paired_objects|singleton_extreme",
        "valid": "paired_objects|singleton_extreme",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple = ()

_PRIMARY_TEMPLATES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (0, 1), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1)),
)
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_DIFFICULTY_TEMPLATE_SHIFT = {None: 3, "easy": 0, "medium": 1, "hard": 2}
_PROFILE_BY_SIGNATURE = {
    dimensions: name for name, dimensions in PROFILE_DIMENSIONS.items()
}


def _validate_scalar(name: str, value: Any, options: Sequence[Any]) -> None:
    if type(value) is not type(options[0]):
        expected = "integer" if type(options[0]) is int else "string"
        raise TypeError(f"{name} override must be a {expected}")
    if value not in options:
        raise ValueError(f"{name} override {value!r} not in {tuple(options)!r}")


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict) -> None:
    if type(seed) is not int or type(sample_index) is not int:
        raise TypeError("seed and sample_index must be integers (not bool)")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(
            f"difficulty must be one of {_VALID_DIFFICULTIES!r}; got {difficulty!r}"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise KeyError(f"unknown override axis: {unknown[0]}")
    if "scene_profile" in overrides:
        _validate_scalar("scene_profile", overrides["scene_profile"], SCHEDULE_PROFILES)
    if "placement" in overrides:
        _validate_scalar("placement", overrides["placement"], PLACEMENTS)
    if "palette_size" in overrides:
        value = overrides["palette_size"]
        if type(value) is not int:
            raise TypeError("palette_size override must be an integer (not bool)")
        if not 2 <= value <= 4:
            raise ValueError("palette_size override must be in [2, 4]")
    if "texture" in overrides:
        _validate_scalar("texture", overrides["texture"], TEXTURES)


def schedule_axes(seed: int, sample_index: int, difficulty=None) -> dict[str, Any]:
    """Return the exact finite default schedule without generating pixels."""
    _validate_call(seed, sample_index, difficulty, {})
    texture = TEXTURES[sample_index % 2]
    return {
        "scene_profile": SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)],
        "placement": PLACEMENTS[sample_index % len(PLACEMENTS)],
        "palette_size": 2 if texture == "paired_objects" else 3,
        "texture": texture,
    }


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the declared profile for one default schedule slot."""
    return schedule_axes(seed, sample_index, difficulty)["scene_profile"]


def _origin(
    grid_h: int,
    grid_w: int,
    crop_h: int,
    crop_w: int,
    placement: str,
) -> tuple[int, int]:
    top = 1 if placement.startswith("upper") else grid_h - crop_h - 1
    left = 1 if placement.endswith("left") else grid_w - crop_w - 1
    return top, left


def _paint_pattern(
    ctx,
    crop_h: int,
    crop_w: int,
    colors: tuple[int, ...],
    texture: str,
    difficulty: str | None,
) -> list[list[int]]:
    local = full_grid(crop_h, crop_w, 0)
    used: set[tuple[int, int]] = set()

    base_index = ctx.draw_rng("primary_template").choice(
        tuple(range(len(_PRIMARY_TEMPLATES)))
    )
    primary = _PRIMARY_TEMPLATES[
        (base_index + _DIFFICULTY_TEMPLATE_SHIFT[difficulty])
        % len(_PRIMARY_TEMPLATES)
    ]
    for row, col in primary:
        local[row][col] = colors[0]
        used.add((row, col))

    if texture == "paired_objects":
        secondary = (
            (crop_h - 1, crop_w - 1),
            (crop_h - 1, crop_w - 2),
            (crop_h - 2, crop_w - 1),
        )
        for row, col in secondary:
            local[row][col] = colors[1]
            used.add((row, col))
        remaining_colors = colors[2:]
    else:
        singleton = (crop_h - 1, crop_w - 1)
        local[singleton[0]][singleton[1]] = colors[-1]
        used.add(singleton)
        remaining_colors = colors[1:-1]

    candidates = [
        (row, col)
        for row in range(1, crop_h - 1)
        for col in range(2, crop_w - 1)
        if (row, col) not in used
    ]
    ctx.draw_rng("interior_pairs").shuffle(candidates)
    needed = 2 * len(remaining_colors)
    if len(candidates) < needed:
        raise RuntimeError("profile cannot fit requested palette without overlap")
    for index, color in enumerate(remaining_colors):
        for row, col in candidates[2 * index : 2 * index + 2]:
            local[row][col] = color
            used.add((row, col))
    return local


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one exact, source-bound crop input."""
    _validate_call(seed, sample_index, difficulty, overrides)
    effective = schedule_axes(seed, sample_index, difficulty)
    effective.update(overrides)

    # Supplying scheduled defaults through the normal override path makes the
    # provenance and explicit-call contracts identical.
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    profile = ctx.draw_choice("scene_profile", SCHEDULE_PROFILES)
    placement = ctx.draw_choice("placement", PLACEMENTS)
    palette_size = ctx.draw_int_strict("palette_size", 2, 4)
    texture = ctx.draw_choice("texture", TEXTURES)

    grid_h, grid_w, crop_h, crop_w = PROFILE_DIMENSIONS[profile]
    colors = ctx.draw_distinct_colors("colors", n=palette_size, exclude={0})
    local = _paint_pattern(ctx, crop_h, crop_w, colors, texture, difficulty)
    top, left = _origin(grid_h, grid_w, crop_h, crop_w, placement)
    grid = full_grid(grid_h, grid_w, 0)
    for row in range(crop_h):
        for col in range(crop_w):
            grid[top + row][left + col] = local[row][col]

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": effective},
    )
    if errors:
        raise RuntimeError(f"constructed invalid grid: {errors}")
    return grid


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if any(not isinstance(row, list) or not row for row in grid):
        return ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                return [
                    f"cell ({row_index},{col_index}) must be an integer color 0..9"
                ]
    return []


def _facts(grid: list[list[int]]) -> dict[str, Any]:
    nonzero = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    rows = [row for row, _, _ in nonzero]
    cols = [col for _, col, _ in nonzero]
    counts = Counter(value for _, _, value in nonzero)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "cells": nonzero,
        "counts": counts,
        "r0": min(rows),
        "r1": max(rows),
        "c0": min(cols),
        "c1": max(cols),
        "crop_h": max(rows) - min(rows) + 1,
        "crop_w": max(cols) - min(cols) + 1,
    }


def _base_analysis(grid: Any) -> tuple[list[str], dict[str, Any] | None]:
    errors = _grid_errors(grid)
    if errors:
        return errors, None
    if not any(value == 0 for row in grid for value in row):
        return ["background color 0 must occur"], None
    if not any(value != 0 for row in grid for value in row):
        return ["at least one non-zero cell is required"], None

    facts = _facts(grid)
    counts: Counter = facts["counts"]
    if not 2 <= len(counts) <= 4:
        errors.append(
            f"expected 2..4 non-zero colors, found {len(counts)}"
        )
    if len(facts["cells"]) < 4:
        errors.append("expected at least four non-zero cells")
    if facts["crop_h"] < 3 or facts["crop_w"] < 3:
        errors.append(
            f"active bounding box must be at least 3x3, found "
            f"{facts['crop_h']}x{facts['crop_w']}"
        )
    if not (
        facts["r0"] > 0
        and facts["c0"] > 0
        and facts["r1"] < facts["grid_h"] - 1
        and facts["c1"] < facts["grid_w"] - 1
    ):
        errors.append("non-zero bounding box must be strictly padded on all sides")
    crop_area = facts["crop_h"] * facts["crop_w"]
    if len(facts["cells"]) >= crop_area:
        errors.append("active crop must preserve at least one internal background cell")
    return errors, facts


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full lawful generator domain, not merely cell count."""
    del difficulty
    errors, _ = _base_analysis(grid)
    if errors:
        return errors
    requested = (meta or {}).get("overrides")
    if requested:
        try:
            observed = observe_overrides(grid)
        except Exception as exc:
            return [f"override observation failed: {type(exc).__name__}: {exc}"]
        for name, value in requested.items():
            if name in AXES and observed.get(name) != value:
                errors.append(
                    f"override {name}={value!r} realized as {observed.get(name)!r}"
                )
    return errors


def strict_canonical_like(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the five canonical shape/palette profiles without replay."""
    del difficulty, meta
    errors, facts = _base_analysis(grid)
    if errors:
        return errors
    assert facts is not None
    signature = (
        facts["grid_h"],
        facts["grid_w"],
        facts["crop_h"],
        facts["crop_w"],
    )
    if signature not in _PROFILE_BY_SIGNATURE:
        errors.append(f"non-canonical input/crop shape profile: {signature}")
    if len(facts["counts"]) != 2:
        errors.append("canonical profile requires exactly two non-zero colors")
    if any(count < 2 for count in facts["counts"].values()):
        errors.append("canonical profile requires every non-zero color to repeat")
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact public axis from returned pixels alone."""
    errors, facts = _base_analysis(grid)
    if errors:
        raise ValueError(errors[0])
    assert facts is not None
    signature = (
        facts["grid_h"],
        facts["grid_w"],
        facts["crop_h"],
        facts["crop_w"],
    )
    profile = _PROFILE_BY_SIGNATURE.get(signature)
    if profile is None:
        raise ValueError(f"input/crop shape is not a declared scene profile: {signature}")

    if facts["r0"] == 1:
        vertical = "upper"
    elif facts["r1"] == facts["grid_h"] - 2:
        vertical = "lower"
    else:
        raise ValueError("active rectangle does not occupy a declared vertical placement")
    if facts["c0"] == 1:
        horizontal = "left"
    elif facts["c1"] == facts["grid_w"] - 2:
        horizontal = "right"
    else:
        raise ValueError("active rectangle does not occupy a declared horizontal placement")
    placement = f"{vertical}_{horizontal}"

    singleton_colors = [
        color for color, count in facts["counts"].items() if count == 1
    ]
    if not singleton_colors:
        if any(count < 2 for count in facts["counts"].values()):
            raise ValueError("paired texture contains a non-repeated color")
        texture = "paired_objects"
    elif len(singleton_colors) == 1:
        singleton = singleton_colors[0]
        singleton_cells = [
            (row, col)
            for row, col, value in facts["cells"]
            if value == singleton
        ]
        if singleton_cells != [(facts["r1"], facts["c1"])]:
            raise ValueError("singleton texture must place its singleton at lower-right")
        texture = "singleton_extreme"
    else:
        raise ValueError("declared textures permit at most one singleton color")

    return {
        "scene_profile": profile,
        "placement": placement,
        "palette_size": len(facts["counts"]),
        "texture": texture,
    }


def _crop_from_cells(
    grid: list[list[int]], cells: Sequence[tuple[int, int]]
) -> list[list[int]]:
    if not cells:
        return [[0]]
    r0 = min(row for row, _ in cells)
    r1 = max(row for row, _ in cells)
    c0 = min(col for _, col in cells)
    c1 = max(col for _, col in cells)
    return [list(row[c0 : c1 + 1]) for row in grid[r0 : r1 + 1]]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for checks; Racket remains authoritative."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    return _crop_from_cells(grid, cells)


def _crop_repeated_colors(grid: list[list[int]]) -> list[list[int]]:
    counts = Counter(value for row in grid for value in row if value != 0)
    keep = {color for color, count in counts.items() if count >= 2}
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value in keep
    ]
    return _crop_from_cells(grid, cells)


def _crop_two_most_frequent_colors(grid: list[list[int]]) -> list[list[int]]:
    counts = Counter(value for row in grid for value in row if value != 0)
    first_seen: dict[int, tuple[int, int]] = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0 and value not in first_seen:
                first_seen[value] = (row, col)
    ranked = sorted(counts, key=lambda color: (-counts[color], first_seen[color], color))
    keep = set(ranked[:2])
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value in keep
    ]
    return _crop_from_cells(grid, cells)


def _monochrome_components(
    grid: list[list[int]],
) -> list[tuple[int, set[tuple[int, int]]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[tuple[int, set[tuple[int, int]]]] = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            queue = deque([(start_row, start_col)])
            seen.add((start_row, start_col))
            cells: set[tuple[int, int]] = set()
            while queue:
                row, col = queue.popleft()
                cells.add((row, col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = (row + dr, col + dc)
                    nr, nc = neighbor
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and neighbor not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            components.append((color, cells))
    return components


def _crop_largest_monochrome_component(grid: list[list[int]]) -> list[list[int]]:
    components = _monochrome_components(grid)
    if not components:
        return [[0]]
    _, cells = min(
        components,
        key=lambda item: (
            -len(item[1]),
            min(row for row, _ in item[1]),
            min(col for _, col in item[1]),
            item[0],
        ),
    )
    return _crop_from_cells(grid, tuple(cells))


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "repeated_colors_only": _crop_repeated_colors,
    "two_most_frequent_colors": _crop_two_most_frequent_colors,
    "largest_monochrome_component": _crop_largest_monochrome_component,
}
CANONICAL_SHORTCUTS = {
    "repeated_colors_only": _crop_repeated_colors,
    "two_most_frequent_colors": _crop_two_most_frequent_colors,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _rival_disagrees(grid, rival_name: str) -> bool:
    try:
        return SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)
    except Exception:
        return False


def _observed_texture(grid) -> str | None:
    try:
        return observe_overrides(grid)["texture"]
    except Exception:
        return None


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "all_objects_define_crop": lambda grid: _rival_disagrees(
        grid, "largest_monochrome_component"
    ),
    "singleton_color_matters": lambda grid: (
        _observed_texture(grid) == "singleton_extreme"
        and _rival_disagrees(grid, "repeated_colors_only")
    ),
    "third_color_matters": lambda grid: (
        len({value for row in grid for value in row if value != 0}) >= 3
        and _rival_disagrees(grid, "two_most_frequent_colors")
    ),
}
WITNESS_RIVALS = {
    "all_objects_define_crop": ["largest_monochrome_component"],
    "singleton_color_matters": ["repeated_colors_only"],
    "third_color_matters": ["two_most_frequent_colors"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Check declared rivals on one materialized lesson; finite evidence only."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    findings: list[str] = []
    labelled = [*demos, query]
    for index, pair in enumerate(labelled):
        if not isinstance(pair, dict) or "input" not in pair:
            findings.append(f"pair {index} is missing an input")
            continue
        expected = rule_mirror(pair["input"])
        present = pair.get("output")
        if present is not None and present != expected:
            findings.append(f"pair {index} output does not match the selected rule")
    if findings:
        return findings

    query_output = query.get("output") or rule_mirror(query["input"])
    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(
                rival(pair["input"]) == pair["output"] for pair in demos
            )
            changes_query = rival(query["input"]) != query_output
        except Exception as exc:
            findings.append(f"rival {name} raised {type(exc).__name__}: {exc}")
            continue
        if survives and changes_query:
            findings.append(
                f"declared rival fits demonstrations but changes query: {name}"
            )
    return findings
