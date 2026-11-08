"""Semantic generator for ARC task ``486375757aca`` (Seeded Frames).

The executable authority operates on each 4-connected blue(1) object, not on
an abstract list of rectangles.  It takes that object's bounding box, selects
the last non-{0,1} seed in row-major order from the original input, and fills
the whole bounding-box interior with the selected color.  Separate frames act
independently; touching frames merge into one object, so their combined box and
seed order are observable parts of the rule.
"""
from __future__ import annotations

from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid


GENERATOR_ID = "486375757aca"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "32695808b436"

SUMMARY = (
    "On a 0-background grid, blue(1) rectangular frames contain colored seed "
    "cells. For each 4-connected blue object, take its bounding box, choose "
    "the last non-{0,1} seed in row-major order from that box's interior, and "
    "fill the entire bounding-box interior with that color. Disconnected "
    "frames act independently; touching frames merge, so internal blue frame "
    "segments and earlier seeds can be overwritten."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is 0 and frame pixels are blue(1)",
    "the scene contains two or three complete seeded rectangular frames",
    "every blue connected component has a non-empty bounding-box interior and at least one seed",
    "every non-{0,1} cell lies inside a complete frame",
    "touching profiles contain multiple distinct seeds in one blue component",
]

# The six profiles deliberately alternate disconnected and touching scenes.
# Therefore every cyclic window of three generated demonstrations contains a
# touching case that refutes the tempting 'fill every frame independently'
# shortcut.  Shapes are unique, making the sole public axis exactly observable.
SCENE_PROFILES = (
    "disjoint_pair_8x11",
    "touching_pair_8x12",
    "narrow_pair_9x12",
    "isolated_touching_11x14",
    "edge_pair_10x13",
    "touching_chain_10x14",
)
SCHEDULE_PROFILES = SCENE_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic alternating touching/disjoint curriculum",
        "valid": "disjoint_pair_8x11|touching_pair_8x12|narrow_pair_9x12|isolated_touching_11x14|edge_pair_10x13|touching_chain_10x14",
    }
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Inclusive frame bounds: (top, left, bottom, right).
_PROFILE_SPECS = {
    "disjoint_pair_8x11": (
        8,
        11,
        ((0, 0, 4, 3), (2, 6, 7, 10)),
    ),
    "touching_pair_8x12": (
        8,
        12,
        ((1, 1, 5, 5), (2, 6, 6, 10)),
    ),
    "narrow_pair_9x12": (
        9,
        12,
        ((1, 1, 6, 5), (4, 8, 7, 10)),
    ),
    "isolated_touching_11x14": (
        11,
        14,
        ((1, 1, 5, 6), (2, 9, 7, 12), (7, 4, 10, 8)),
    ),
    "edge_pair_10x13": (
        10,
        13,
        ((0, 1, 4, 5), (4, 8, 9, 12)),
    ),
    "touching_chain_10x14": (
        10,
        14,
        ((0, 0, 4, 4), (2, 5, 7, 9), (5, 10, 9, 13)),
    ),
}
_PROFILE_BY_SHAPE = {
    (height, width): name
    for name, (height, width, _frames) in _PROFILE_SPECS.items()
}
_STRICT_SHAPES = set(_PROFILE_BY_SHAPE)
_BAND_OFFSETS = {"easy": 0, "medium": 2, "hard": 4}


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty in _BAND_OFFSETS:
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the pinned alternating curriculum profile for one pair."""
    del seed
    band = _band(difficulty)
    return SCENE_PROFILES[(int(sample_index) + _BAND_OFFSETS[band]) % len(SCENE_PROFILES)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic, source-bound seeded-frame input."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    band = _band(difficulty)
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in _PROFILE_SPECS:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    scheduled = requested or schedule_profile(seed, sample_index, difficulty=band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", [scheduled])
    height, width, frames = _PROFILE_SPECS[profile]
    grid = full_grid(height, width, 0)
    for top, left, bottom, right in frames:
        draw_frame(grid, top, left, bottom, right, 1)

    rng = ctx.draw_rng("seed_cells")
    colors = rng.sample(list(range(2, 10)), len(frames))
    for color, (top, left, bottom, right) in zip(colors, frames):
        interior = [
            (row, col)
            for row in range(top + 1, bottom)
            for col in range(left + 1, right)
        ]
        if not interior:
            raise ValueError(f"profile {profile!r} contains a frame without an interior")
        row, col = rng.choice(interior)
        grid[row][col] = color
    return grid


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 3 <= len(grid) <= 30 or not 3 <= width <= 30:
        return [f"grid dimensions must be in 3..30, found {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _components(grid: Sequence[Sequence[int]], color: int = 1) -> list[list[tuple[int, int]]]:
    """Return 4-connected components in row-major discovery order."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((1, 0), (0, 1), (-1, 0), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def _bbox(cells: Sequence[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _seed_cells(
    grid: Sequence[Sequence[int]], bbox: tuple[int, int, int, int]
) -> list[tuple[int, int, int]]:
    top, left, bottom, right = bbox
    return [
        (row, col, grid[row][col])
        for row in range(top + 1, bottom)
        for col in range(left + 1, right)
        if grid[row][col] not in (0, 1)
    ]


def _complete_frames(grid: Sequence[Sequence[int]]) -> list[dict[str, Any]]:
    """Enumerate complete blue rectangles with at least one colored seed inside."""
    height, width = len(grid), len(grid[0])
    row_prefix = [[0] * (width + 1) for _ in range(height)]
    col_prefix = [[0] * (height + 1) for _ in range(width)]
    for row in range(height):
        for col in range(width):
            is_blue = int(grid[row][col] == 1)
            row_prefix[row][col + 1] = row_prefix[row][col] + is_blue
            col_prefix[col][row + 1] = col_prefix[col][row] + is_blue

    frames: list[dict[str, Any]] = []
    for top in range(height - 2):
        for bottom in range(top + 2, height):
            frame_height = bottom - top + 1
            for left in range(width - 2):
                for right in range(left + 2, width):
                    frame_width = right - left + 1
                    if row_prefix[top][right + 1] - row_prefix[top][left] != frame_width:
                        continue
                    if row_prefix[bottom][right + 1] - row_prefix[bottom][left] != frame_width:
                        continue
                    if col_prefix[left][bottom + 1] - col_prefix[left][top] != frame_height:
                        continue
                    if col_prefix[right][bottom + 1] - col_prefix[right][top] != frame_height:
                        continue
                    bbox = (top, left, bottom, right)
                    seeds = _seed_cells(grid, bbox)
                    if seeds:
                        frames.append({"bbox": bbox, "seeds": seeds})
    return frames


def _frame_border(bbox: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    top, left, bottom, right = bbox
    return {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if row in (top, bottom) or col in (left, right)
    }


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    components = _components(grid, 1)
    if not components:
        errors.append("expected at least one blue(1) connected component")
    component_rows = []
    for index, cells in enumerate(components):
        bbox = _bbox(cells)
        top, left, bottom, right = bbox
        if bottom - top < 2 or right - left < 2:
            errors.append(f"blue component {index} has no bounding-box interior")
        seeds = _seed_cells(grid, bbox)
        if not seeds:
            errors.append(f"blue component {index} has no non-{{0,1}} seed in its interior")
        component_rows.append({"cells": cells, "bbox": bbox, "seeds": seeds})

    frames = _complete_frames(grid)
    if len(frames) < 2:
        errors.append(f"expected at least two complete seeded blue frames, found {len(frames)}")
    blue_cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 1
    }
    covered_blue: set[tuple[int, int]] = set()
    for frame in frames:
        covered_blue.update(_frame_border(frame["bbox"]))
    stray_blue = sorted(blue_cells - covered_blue)
    if stray_blue:
        errors.append(f"blue cells outside every complete frame: {stray_blue[:3]}")

    colored = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 1)
    ]
    for row, col, color in colored:
        if not any(
            top < row < bottom and left < col < right
            for top, left, bottom, right in (frame["bbox"] for frame in frames)
        ):
            errors.append(f"seed color {color} at {(row, col)} is outside every complete frame")
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "components": component_rows,
        "frames": frames,
        "colored": colored,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical inputs and reject malformed or rule-hiding scenes."""
    if difficulty is not None:
        _band(difficulty)
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    try:
        if rule_mirror(grid) == [list(row) for row in grid]:
            errors.append("scene is an identity/no-op under the canonical rule")
    except ValueError as exc:
        errors.append(str(exc))
    return errors


def observe_overrides(grid) -> dict[str, str | None]:
    errors = _rectangular_errors(grid)
    if errors:
        return {}
    return {"scene_profile": _PROFILE_BY_SHAPE.get((len(grid), len(grid[0])))}


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python transcription; synchronized Racket remains authority."""
    errors = _rectangular_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    output = [list(row) for row in grid]
    for cells in _components(grid, 1):
        bbox = _bbox(cells)
        seeds = _seed_cells(grid, bbox)
        if not seeds:
            raise ValueError("blue component has no non-{0,1} seed in its interior")
        color = seeds[-1][2]
        top, left, bottom, right = bbox
        for row in range(top + 1, bottom):
            for col in range(left + 1, right):
                output[row][col] = color
    return output


def strict_canonical_like(grid) -> list[str]:
    """Require the canonical seeded-frame grammar and visible rule action."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analysis(grid)
    if (analysis["height"], analysis["width"]) not in _STRICT_SHAPES:
        errors.append("shape is outside the canonical/generated seeded-frame envelope")
    if len(analysis["components"]) not in (1, 2):
        errors.append("expected one or two blue connected components")
    if len(analysis["colored"]) not in (2, 3):
        errors.append("expected two or three colored seed cells")
    return errors


def _rival_first_seed_per_component(grid):
    output = [list(row) for row in grid]
    for cells in _components(grid, 1):
        bbox = _bbox(cells)
        seeds = _seed_cells(grid, bbox)
        if not seeds:
            return [list(row) for row in grid]
        color = seeds[0][2]
        top, left, bottom, right = bbox
        for row in range(top + 1, bottom):
            for col in range(left + 1, right):
                output[row][col] = color
    return output


def _rival_preserve_internal_blue(grid):
    output = [list(row) for row in grid]
    for cells in _components(grid, 1):
        bbox = _bbox(cells)
        seeds = _seed_cells(grid, bbox)
        if not seeds:
            return [list(row) for row in grid]
        color = seeds[-1][2]
        top, left, bottom, right = bbox
        for row in range(top + 1, bottom):
            for col in range(left + 1, right):
                if grid[row][col] != 1:
                    output[row][col] = color
    return output


def _rival_fill_each_frame_independently(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    output = [list(row) for row in grid]
    for frame in sorted(analysis["frames"], key=lambda item: item["bbox"]):
        top, left, bottom, right = frame["bbox"]
        color = frame["seeds"][-1][2]
        for row in range(top + 1, bottom):
            for col in range(left + 1, right):
                output[row][col] = color
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "first_seed_per_component": _rival_first_seed_per_component,
    "fill_each_frame_independently": _rival_fill_each_frame_independently,
    "preserve_internal_blue": _rival_preserve_internal_blue,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _multi_seed_component(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and any(
        len(component["seeds"]) >= 2 for component in analysis["components"]
    )


def _internal_blue_overwritten(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    output = rule_mirror(grid)
    return any(
        grid[row][col] == 1 and output[row][col] != 1
        for row in range(len(grid))
        for col in range(len(grid[0]))
    )


def _independent_frame_disagrees(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and _rival_fill_each_frame_independently(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "multi_seed_component": _multi_seed_component,
    "internal_blue_overwritten": _internal_blue_overwritten,
    "independent_frame_shortcut_breaker": _independent_frame_disagrees,
}
WITNESS_RIVALS = {
    "multi_seed_component": ["first_seed_per_component"],
    "internal_blue_overwritten": ["preserve_internal_blue"],
    "independent_frame_shortcut_breaker": ["fill_each_frame_independently"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require the demonstrations to falsify every declared rival rule."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:
            reasons.append(f"demo {index} mirror failed: {type(exc).__name__}: {exc}")
            continue
        if expected != pair["output"]:
            reasons.append(f"demo {index} disagrees with the component-bbox rule")
    try:
        if rule_mirror(query["input"]) != query["output"]:
            reasons.append("query disagrees with the component-bbox rule")
    except Exception as exc:
        reasons.append(f"query mirror failed: {type(exc).__name__}: {exc}")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"demonstrations do not falsify rival: {name}")
    return reasons
