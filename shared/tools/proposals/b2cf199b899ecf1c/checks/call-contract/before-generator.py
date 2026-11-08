"""Generator for ARC task 2692a3e47a66.

Four solid square blocks occupy the four corners of a color-7 canvas.  Every
color represented by at least two disconnected corner blocks moves inward:
each block is translated by its own bounding-box height and width toward the
center.  A color represented by only one block stays in place.

The four-sample schedule retains the canonical all-same / repeated-plus-unique
cases and adds two decisive teaching cases: two independently repeated colors,
and repeated blocks with unequal sizes.  Those cases refute the strongest
canonical-fitting shortcuts without changing the Racket authority.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "2692a3e47a66"
TASK_ID = GENERATOR_ID
VERSION = "3.0.1"
RULE_HASH = "f5a9e05539e5"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 7-30 by 7-30 color-7 grid has one solid square block in each corner. "
    "Corner-block colors may occur once, twice, three times, or four times, "
    "and block sides range from 1 to 4. For every color occupying at least "
    "two disconnected corner blocks, erase those blocks and translate each "
    "one inward by its own height and width. Singleton-color blocks remain "
    "at their original corners."
)

INVARIANTS = [
    "background 7 is the unique modal color",
    "exactly four solid square foreground components occupy the four corners",
    "corner-block side lengths are 1..4 and opposite blocks remain disconnected",
    "at least one foreground color occurs in two or more corner components",
    "each repeated-color block moves inward by that block's own side length",
    "singleton-color corner blocks stay fixed",
]

SCENE_PROFILES = (
    "all_same_uniform",
    "triple_single_mixed",
    "pair_singletons_uniform",
    "two_pairs_mixed",
)
SCHEDULE_PROFILES = SCENE_PROFILES

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 16 anchor on all-same profile; otherwise difficulty-keyed 7..30",
        "valid": "7..30",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 16 anchor on all-same profile; otherwise difficulty-keyed 7..30",
        "valid": "7..30",
    },
    "scene_profile": {
        "type": "enum",
        "default": "four-sample cyclic teaching schedule",
        "valid": SCENE_PROFILES,
    },
}
_ALLOWED_OVERRIDES = frozenset(AXES)

_CORNERS = ("tl", "tr", "bl", "br")
_PALETTE = (1, 2, 3, 4, 5, 6, 8, 9)
_DELTAS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Expose the four-case cyclic curriculum used by the semantic gate."""
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _copy_grid(grid: Iterable[Iterable[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard") and not isinstance(
        difficulty, (int, float)
    ):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    for name in ("grid_h", "grid_w"):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} must be an integer in 7..30")
        if not 7 <= value <= 30:
            raise ValueError(f"{name} must be in 7..30, got {value}")
    if "scene_profile" in overrides and overrides["scene_profile"] is not None:
        profile = overrides["scene_profile"]
        if profile not in SCENE_PROFILES:
            raise ValueError(
                f"scene_profile must be one of {SCENE_PROFILES}, got {profile!r}"
            )


def _grid_shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty list/tuple"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 7 <= len(grid) <= 30 or not 7 <= width <= 30:
        return [f"grid dimensions must be within 7..30, got {len(grid)}x{width}"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be literal ARC color integers 0..9"]
    return []


def _mode_color(grid: list[list[int]]) -> int:
    counts = Counter(value for row in grid for value in row)
    # The canonical prelude's numeric tie behavior is immaterial on the lawful
    # manifold because background 7 is unique-modal.  Lowest-color tie-break is
    # deterministic for diagnostic rival calls outside that manifold.
    return min(counts, key=lambda color: (-counts[color], color))


def _components_for_color(
    grid: list[list[int]], color: int
) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for dr, dc in _DELTAS4:
                neighbor = (row + dr, col + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        result.append(component)
    return result


def _foreground_components(
    grid: list[list[int]], background: int = 7
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    colors = sorted({value for row in grid for value in row if value != background})
    for color in colors:
        for cells in _components_for_color(grid, color):
            rows = [row for row, _col in cells]
            cols = [col for _row, col in cells]
            r0, r1 = min(rows), max(rows)
            c0, c1 = min(cols), max(cols)
            result.append(
                {
                    "color": color,
                    "cells": cells,
                    "bbox": (r0, c0, r1, c1),
                    "height": r1 - r0 + 1,
                    "width": c1 - c0 + 1,
                }
            )
    return result


def _component_corner(
    component: dict[str, Any], height: int, width: int
) -> str | None:
    r0, c0, r1, c1 = component["bbox"]
    matches = []
    if r0 == 0 and c0 == 0:
        matches.append("tl")
    if r0 == 0 and c1 == width - 1:
        matches.append("tr")
    if r1 == height - 1 and c0 == 0:
        matches.append("bl")
    if r1 == height - 1 and c1 == width - 1:
        matches.append("br")
    return matches[0] if len(matches) == 1 else None


def _profile_from_facts(
    multiplicities: list[int], components: list[dict[str, Any]]
) -> str | None:
    sides = [component["height"] for component in components]
    uniform = len(set(sides)) == 1
    by_color: dict[int, list[int]] = {}
    for component in components:
        by_color.setdefault(component["color"], []).append(component["height"])

    if multiplicities == [4] and uniform:
        return "all_same_uniform"
    if multiplicities == [1, 3] and any(
        len(values) == 3 and len(set(values)) > 1 for values in by_color.values()
    ):
        return "triple_single_mixed"
    if multiplicities == [1, 1, 2] and uniform:
        return "pair_singletons_uniform"
    if multiplicities == [2, 2] and not uniform and all(
        len(set(values)) == 1 for values in by_color.values()
    ):
        return "two_pairs_mixed"
    return None


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _grid_shape_errors(grid)
    result: dict[str, Any] = {
        "errors": errors,
        "height": 0,
        "width": 0,
        "components": [],
        "by_corner": {},
        "multiplicities": [],
        "scene_profile": None,
    }
    if errors:
        return result

    height, width = len(grid), len(grid[0])
    result["height"], result["width"] = height, width
    counts = Counter(value for row in grid for value in row)
    other_max = max((count for color, count in counts.items() if color != 7), default=0)
    if counts.get(7, 0) <= other_max:
        errors.append(
            "background must be 7 and uniquely modal; "
            f"count(7)={counts.get(7, 0)}, largest foreground={other_max}"
        )

    components = _foreground_components(grid, 7)
    result["components"] = components
    if len(components) != 4:
        errors.append(
            "expected exactly four solid square corner blocks; "
            f"found {len(components)} foreground components"
        )

    by_corner: dict[str, dict[str, Any]] = {}
    for index, component in enumerate(components):
        side_h, side_w = component["height"], component["width"]
        expected_area = side_h * side_w
        if side_h != side_w or len(component["cells"]) != expected_area:
            errors.append(
                f"foreground component {index} must be a solid square, got "
                f"bbox {side_h}x{side_w} with {len(component['cells'])} cells"
            )
        if not 1 <= side_h <= 4 or not 1 <= side_w <= 4:
            errors.append(
                f"foreground component {index} side must be 1..4, got "
                f"{side_h}x{side_w}"
            )
        corner = _component_corner(component, height, width)
        component["corner"] = corner
        if corner is None:
            errors.append(f"foreground component {index} must occupy exactly one grid corner")
        elif corner in by_corner:
            errors.append(f"multiple foreground components occupy corner {corner}")
        else:
            by_corner[corner] = component
    result["by_corner"] = by_corner
    missing = sorted(set(_CORNERS) - set(by_corner))
    if missing:
        errors.append(f"missing corner blocks at {missing}")

    color_counts = Counter(component["color"] for component in components)
    multiplicities = sorted(color_counts.values())
    result["multiplicities"] = multiplicities
    result["color_counts"] = color_counts
    if not any(count >= 2 for count in color_counts.values()):
        errors.append("at least one repeated corner-block color is required")

    if not errors:
        result["scene_profile"] = _profile_from_facts(multiplicities, components)
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete lawful four-corner teaching manifold."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """The generated manifold is the direct, authority-compatible task grammar."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe overrides on invalid grid: " + "; ".join(analysis["errors"]))
    profile = analysis["scene_profile"]
    if profile not in SCENE_PROFILES:
        raise ValueError("valid grid does not encode one public scene_profile")
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "scene_profile": profile,
    }


def _largest_uniform_side(height: int, width: int) -> int:
    limit = min(4, (height - 1) // 2, (width - 1) // 2)
    while limit > 1 and 8 * limit * limit >= height * width:
        limit -= 1
    return max(1, limit)


def _largest_mixed_side(height: int, width: int) -> int:
    limit = min(4, (height - 1) // 2, (width - 1) // 2)
    # Mixed profiles use sides [1, L, 1, L].  Keep background 7 larger
    # than all foreground cells combined, which is stronger than mode requires.
    while limit > 2 and 2 * (2 + 2 * limit * limit) >= height * width:
        limit -= 1
    return max(2, limit)


def _rotate(values: list[Any], amount: int) -> list[Any]:
    amount %= len(values)
    return values[amount:] + values[:amount]


def _profile_layout(
    profile: str,
    height: int,
    width: int,
    sample_index: int,
    palette_rng,
    layout_rng,
) -> tuple[list[int], list[int]]:
    rotation = layout_rng.randrange(4)
    if profile in ("all_same_uniform", "pair_singletons_uniform"):
        max_side = _largest_uniform_side(height, width)
        side = 1 + (abs(int(sample_index)) + layout_rng.randrange(max_side)) % max_side
        sizes = [side] * 4
    else:
        large = _largest_mixed_side(height, width)
        # Exercise multiple legal scales while preserving the profile signature.
        if large > 2:
            large = 2 + (abs(int(sample_index)) + layout_rng.randrange(large - 1)) % (large - 1)
        sizes = [1, large, 1, large]

    if profile == "all_same_uniform":
        color = palette_rng.choice(_PALETTE)
        colors = [color] * 4
    elif profile == "pair_singletons_uniform":
        repeated, singleton_a, singleton_b = palette_rng.sample(_PALETTE, 3)
        pair_layouts = (
            [repeated, repeated, singleton_a, singleton_b],
            [repeated, singleton_a, repeated, singleton_b],
            [repeated, singleton_a, singleton_b, repeated],
        )
        colors = list(pair_layouts[layout_rng.randrange(len(pair_layouts))])
    elif profile == "triple_single_mixed":
        repeated, singleton = palette_rng.sample(_PALETTE, 2)
        colors = [repeated, repeated, repeated, singleton]
        # Rotate colors and sizes together: the repeated color always spans
        # both side 1 and side L, making per-object displacement observable.
    elif profile == "two_pairs_mixed":
        first, second = palette_rng.sample(_PALETTE, 2)
        # Keep different repeated colors separated along the mixed-size axis;
        # their moved outputs cannot overwrite one another even on 7x7 grids.
        if layout_rng.randrange(2) == 0:
            colors = [first, first, second, second]
            sizes = [1, 1, sizes[1], sizes[1]]
        else:
            colors = [first, second, first, second]
            sizes = [1, sizes[1], 1, sizes[1]]
    else:  # guarded by _validate_call / ctx.draw_choice
        raise ValueError(f"unknown scene_profile: {profile!r}")

    return _rotate(colors, rotation), _rotate(sizes, rotation)


def _paint_corner_square(
    grid: list[list[int]], corner: str, side: int, color: int
) -> None:
    height, width = len(grid), len(grid[0])
    if corner == "tl":
        rows, cols = range(side), range(side)
    elif corner == "tr":
        rows, cols = range(side), range(width - side, width)
    elif corner == "bl":
        rows, cols = range(height - side, height), range(side)
    elif corner == "br":
        rows, cols = range(height - side, height), range(width - side, width)
    else:
        raise ValueError(f"unknown corner {corner!r}")
    for row in rows:
        for col in cols:
            grid[row][col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, source-valid four-corner input grid."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    profile_options = SCENE_PROFILES if "scene_profile" in overrides else (scheduled,)
    profile = ctx.draw_choice("scene_profile", profile_options)

    # One quarter of the cyclic curriculum is an exact canonical profile:
    # all four same-colored blocks on a 16x16 canvas.  The remaining profiles
    # retain the full difficulty-aware 7..30 shape range.  Exact overrides
    # always win and are validated against the public axis bounds.
    if profile == "all_same_uniform" and overrides.get("grid_h") is None:
        height = ctx.draw_int("grid_h", 16, 16)
    else:
        height = ctx.draw_int_diff("grid_h", 7, 30)
    if profile == "all_same_uniform" and overrides.get("grid_w") is None:
        width = ctx.draw_int("grid_w", 16, 16)
    else:
        width = ctx.draw_int_diff("grid_w", 7, 30)

    colors, sizes = _profile_layout(
        profile,
        height,
        width,
        int(sample_index),
        ctx.draw_rng("palette"),
        ctx.draw_rng("layout"),
    )
    grid = [[7] * width for _ in range(height)]
    for corner, color, side in zip(_CORNERS, colors, sizes):
        _paint_corner_square(grid, corner, side, color)

    analysis = _analysis(grid)
    if analysis["errors"] or analysis["scene_profile"] != profile:
        raise RuntimeError(
            f"constructed {profile!r} but observed {analysis['scene_profile']!r}: "
            + "; ".join(analysis["errors"])
        )
    return grid


def _translate_selected_colors(
    grid: list[list[int]],
    selected_colors: set[int],
    *,
    global_side: int | None = None,
) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    background = _mode_color(grid)
    output = _copy_grid(grid)
    original_components = {
        color: _components_for_color(grid, color)
        for color in range(10)
        if color != background
    }
    for color in range(10):
        if color == background or color not in selected_colors:
            continue
        components = original_components.get(color, [])
        if not components:
            continue
        for row in range(height):
            for col in range(width):
                if grid[row][col] == color:
                    output[row][col] = background
        for cells in components:
            rows = [row for row, _col in cells]
            cols = [col for _row, col in cells]
            r0, c0 = min(rows), min(cols)
            side_h = max(rows) - r0 + 1
            side_w = max(cols) - c0 + 1
            shift_h = global_side if global_side is not None else side_h
            shift_w = global_side if global_side is not None else side_w
            dr = shift_h if 2 * r0 < height else -shift_h
            dc = shift_w if 2 * c0 < width else -shift_w
            for row, col in cells:
                nr, nc = row + dr, col + dc
                if 0 <= nr < height and 0 <= nc < width:
                    output[nr][nc] = color
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Pure-Python mirror of the pinned Racket authority."""
    copied = _copy_grid(grid)
    background = _mode_color(copied)
    selected = {
        color
        for color in range(10)
        if color != background and len(_components_for_color(copied, color)) >= 2
    }
    return _translate_selected_colors(copied, selected)


def _rival_move_only_modal_object_color(grid) -> list[list[int]]:
    """Canonical-fit rival: move only the color with most corner objects."""
    copied = _copy_grid(grid)
    background = _mode_color(copied)
    counts = {
        color: len(_components_for_color(copied, color))
        for color in range(10)
        if color != background and any(color in row for row in copied)
    }
    if not counts:
        return copied
    target = min(counts, key=lambda color: (-counts[color], color))
    if counts[target] < 2:
        return copied
    return _translate_selected_colors(copied, {target})


def _rival_move_repeated_blocks_by_one_global_size(grid) -> list[list[int]]:
    """Canonical-fit rival: use the top-left block's side for every move."""
    copied = _copy_grid(grid)
    background = _mode_color(copied)
    components = _foreground_components(copied, background)
    top_left = next(
        (
            component
            for component in components
            if component["bbox"][0] == 0 and component["bbox"][1] == 0
        ),
        None,
    )
    if top_left is None:
        return copied
    selected = {
        color
        for color in range(10)
        if color != background and len(_components_for_color(copied, color)) >= 2
    }
    return _translate_selected_colors(
        copied, selected, global_side=top_left["height"]
    )


def _has_two_repeated_colors(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["multiplicities"] == [2, 2]


def _repeated_blocks_have_unequal_sizes(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    by_color: dict[int, set[int]] = {}
    for component in analysis["components"]:
        by_color.setdefault(component["color"], set()).add(component["height"])
    return any(
        analysis["color_counts"][color] >= 2 and len(sides) > 1
        for color, sides in by_color.items()
    )


SEMANTIC_RIVALS = {
    "move_only_modal_object_color": _rival_move_only_modal_object_color,
    "move_repeated_blocks_by_one_global_size": (
        _rival_move_repeated_blocks_by_one_global_size
    ),
}

SEMANTIC_WITNESSES = {
    "two_repeated_colors": _has_two_repeated_colors,
    "repeated_blocks_have_unequal_sizes": _repeated_blocks_have_unequal_sizes,
}

WITNESS_RIVALS = {
    "two_repeated_colors": ["move_only_modal_object_color"],
    "repeated_blocks_have_unequal_sizes": [
        "move_repeated_blocks_by_one_global_size"
    ],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _same_grid(left, right) -> bool:
    return tuple(map(tuple, left)) == tuple(map(tuple, right))


def lesson_identifiable(demos, query) -> list[str]:
    """Require the visible demonstrations to refute every declared rival."""
    del query
    errors: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        if all(
            _same_grid(competitor(pair["input"]), pair["output"])
            for pair in demos
        ):
            errors.append(f"competitor {name} survives every demonstration")
    return errors
