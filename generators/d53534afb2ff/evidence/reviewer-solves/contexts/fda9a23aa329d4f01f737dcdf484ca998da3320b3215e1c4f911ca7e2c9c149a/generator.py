"""Semantic input generator for ARC task d53534afb2ff.

The selected Racket rule finds exact hollow rectangular outlines and recolors
EVERY same-color 4-connected object strictly inside an outline to that
outline's color.  Outside objects are unchanged.

The four-profile schedule deliberately teaches the distinctions that the old
sampler omitted: unchanged outside controls, connected multi-cell targets,
multiple targets in one frame, and target colors other than canonical color 3.
"""
from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d53534afb2ff"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "372b08419c67"

SUMMARY = (
    "One or two exact hollow rectangular frames recolor every connected object "
    "strictly inside them; same-color objects outside remain unchanged."
)

INVARIANTS = [
    "background is color 0 and every frame is an exact hollow rectangle",
    "each frame strictly encloses one or more non-frame objects in other colors",
    "all cells of each enclosed connected object inherit its enclosing frame color",
    "objects outside every frame remain unchanged",
]

SCENE_PROFILES = (
    "two_singletons",
    "outside_same_color",
    "multi_cell",
    "multiple_inside",
)
SCHEDULE_PROFILES = SCENE_PROFILES
EXAMPLES_NEEDED = 4

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "cyclic four-example teaching schedule",
        "valid": "|".join(SCENE_PROFILES),
    }
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_NEIGHBORS = ((1, 0), (-1, 0), (0, 1), (0, -1))
_SINGLE = ((0, 0),)
_LARGE_SHAPES = (
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
)
_HARD_LARGE_SHAPES = _LARGE_SHAPES + (
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (0, 3)),
    ((0, 0), (1, 0), (2, 0), (3, 0)),
)
_SMALL_SECOND_SHAPES = (
    _SINGLE,
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0)),
)


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    """Return the teaching slot; every consecutive four examples cover all slots."""
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % EXAMPLES_NEEDED]


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["ARC grids may have at most 30 rows and columns"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be literal integer ARC colors 0 through 9"]
    return []


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _components(grid: list[list[int]] | tuple[tuple[int, ...], ...]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for drow, dcol in _NEIGHBORS:
                    neighbor = current[0] + drow, current[1] + dcol
                    nr, nc = neighbor
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and neighbor not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            ordered = tuple(sorted(cells))
            result.append(
                {
                    "index": len(result),
                    "color": color,
                    "cells": ordered,
                    "bbox": _bbox(ordered),
                    "size": len(ordered),
                }
            )
    return result


def _is_exact_frame(obj: dict[str, Any]) -> bool:
    row0, col0, row1, col1 = obj["bbox"]
    if row1 - row0 < 2 or col1 - col0 < 2:
        return False
    expected = {
        (row, col)
        for row in range(row0, row1 + 1)
        for col in range(col0, col1 + 1)
        if row in (row0, row1) or col in (col0, col1)
    }
    return set(obj["cells"]) == expected


def _strictly_contains(frame: dict[str, Any], obj: dict[str, Any]) -> bool:
    frow0, fcol0, frow1, fcol1 = frame["bbox"]
    orow0, ocol0, orow1, ocol1 = obj["bbox"]
    return (
        frow0 < orow0
        and fcol0 < ocol0
        and orow1 < frow1
        and ocol1 < fcol1
    )


def _scan_scene(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {
            "errors": errors,
            "objects": [],
            "frames": [],
            "inside_objects": [],
            "outside_objects": [],
            "by_frame": {},
        }
    scene_components = _components(grid)
    frames = [dict(obj) for obj in scene_components if _is_exact_frame(obj)]
    others = [dict(obj) for obj in scene_components if not _is_exact_frame(obj)]
    inside: list[dict[str, Any]] = []
    outside: list[dict[str, Any]] = []
    by_frame: dict[int, list[dict[str, Any]]] = {
        index: [] for index in range(len(frames))
    }
    for obj in others:
        hits = tuple(
            index for index, frame in enumerate(frames) if _strictly_contains(frame, obj)
        )
        enriched = dict(obj)
        enriched["frame_indexes"] = hits
        if hits:
            enriched["frame_index"] = hits[0]
            inside.append(enriched)
            for index in hits:
                by_frame[index].append(enriched)
        else:
            outside.append(enriched)
    return {
        "errors": [],
        "objects": scene_components,
        "frames": frames,
        "inside_objects": inside,
        "outside_objects": outside,
        "by_frame": by_frame,
    }


def _classify_profile(scan: dict[str, Any]) -> str | None:
    frames = scan["frames"]
    inside = scan["inside_objects"]
    outside = scan["outside_objects"]
    by_frame = scan["by_frame"]
    if any(len(obj["frame_indexes"]) != 1 for obj in inside):
        return None

    if len(frames) == 1 and len(inside) >= 2 and len(by_frame[0]) >= 2:
        return "multiple_inside"

    if len(frames) != 2 or any(len(by_frame[index]) != 1 for index in range(2)):
        return None

    inside_sizes = [obj["size"] for obj in inside]
    inside_colors = {obj["color"] for obj in inside}
    same_color_outside = any(obj["color"] in inside_colors for obj in outside)
    if not outside and inside_sizes == [1, 1]:
        return "two_singletons"
    if outside and all(size == 1 for size in inside_sizes) and same_color_outside:
        return "outside_same_color"
    if outside and any(size > 1 for size in inside_sizes) and same_color_outside:
        return "multi_cell"
    return None


def analyze_scene(grid: Any) -> dict[str, Any]:
    """Return a pixel-derived structural analysis used by checks and tests."""
    scan = _scan_scene(grid)
    if scan["errors"]:
        scan["scene_profile"] = None
        return scan

    errors: list[str] = []
    frames = scan["frames"]
    inside = scan["inside_objects"]
    if not 1 <= len(frames) <= 2:
        errors.append(f"expected one or two exact hollow frames, found {len(frames)}")
    if len({frame["color"] for frame in frames}) != len(frames):
        errors.append("frame colors must be distinct")
    for obj in inside:
        if len(obj["frame_indexes"]) != 1:
            errors.append(
                f"object {obj['index']} must be strictly inside exactly one frame"
            )
            continue
        frame = frames[obj["frame_index"]]
        if obj["color"] == frame["color"]:
            errors.append(
                f"inside object {obj['index']} already has its frame color"
            )
    for index in range(len(frames)):
        if not scan["by_frame"].get(index):
            errors.append(f"frame {index} contains no target object")

    profile = _classify_profile(scan)
    if profile is None:
        errors.append("scene does not match any declared teaching profile")
    scan["scene_profile"] = profile
    scan["errors"] = errors
    return scan


def _paint_object(output: list[list[int]], obj: dict[str, Any], color: int) -> None:
    for row, col in obj["cells"]:
        output[row][col] = color


def _transform(
    grid: Any,
    eligible: Callable[[dict[str, Any], dict[str, Any]], bool],
) -> list[list[int]]:
    scan = _scan_scene(grid)
    if scan["errors"]:
        raise ValueError("; ".join(scan["errors"]))
    output = [list(row) for row in grid]
    for obj in scan["inside_objects"]:
        frame = scan["frames"][obj["frame_index"]]
        if eligible(obj, frame):
            _paint_object(output, obj, frame["color"])
    return output


def rule_mirror(grid: Any) -> list[list[int]]:
    """Input-pure Python mirror on the selected rule's ordinary domain."""
    return _transform(grid, lambda obj, frame: True)


def self_check(grid: Any, *, difficulty: str | None = None, meta: Any = None) -> list[str]:
    del difficulty, meta
    analysis = analyze_scene(grid)
    errors = list(analysis["errors"])
    if not errors and rule_mirror(grid) == [list(row) for row in grid]:
        errors.append("rule would be identity; at least one target must change")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    return self_check(grid)


def observe_overrides(grid: Any) -> dict[str, str]:
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe scene_profile: " + "; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def _color_three_only(grid: Any) -> list[list[int]]:
    return _transform(grid, lambda obj, frame: obj["color"] == 3)


def _at_most_two_cells(grid: Any) -> list[list[int]]:
    return _transform(grid, lambda obj, frame: obj["size"] <= 2)


def _first_object_only(grid: Any) -> list[list[int]]:
    scan = _scan_scene(grid)
    if scan["errors"]:
        raise ValueError("; ".join(scan["errors"]))
    output = [list(row) for row in grid]
    seen_frames: set[int] = set()
    for obj in scan["inside_objects"]:
        frame_index = obj["frame_index"]
        if frame_index in seen_frames:
            continue
        seen_frames.add(frame_index)
        _paint_object(output, obj, scan["frames"][frame_index]["color"])
    return output


def _global_same_color(grid: Any) -> list[list[int]]:
    """Wrong rival: once a color occurs inside, recolor that color everywhere."""
    scan = _scan_scene(grid)
    if scan["errors"]:
        raise ValueError("; ".join(scan["errors"]))
    mapping: dict[int, int] = {}
    for obj in scan["inside_objects"]:
        mapping.setdefault(obj["color"], scan["frames"][obj["frame_index"]]["color"])
    output = [list(row) for row in grid]
    frame_indexes = {obj["index"] for obj in scan["frames"]}
    for obj in scan["objects"]:
        if obj["index"] not in frame_indexes and obj["color"] in mapping:
            _paint_object(output, obj, mapping[obj["color"]])
    return output


def _has_non_three_inside(grid: Any) -> bool:
    scan = _scan_scene(grid)
    return not scan["errors"] and any(obj["color"] != 3 for obj in scan["inside_objects"])


def _has_large_inside_object(grid: Any) -> bool:
    scan = _scan_scene(grid)
    return not scan["errors"] and any(obj["size"] > 2 for obj in scan["inside_objects"])


def _has_multiple_objects_one_frame(grid: Any) -> bool:
    scan = _scan_scene(grid)
    return not scan["errors"] and any(len(group) >= 2 for group in scan["by_frame"].values())


def _has_outside_same_color(grid: Any) -> bool:
    scan = _scan_scene(grid)
    if scan["errors"]:
        return False
    inside_colors = {obj["color"] for obj in scan["inside_objects"]}
    return any(obj["color"] in inside_colors for obj in scan["outside_objects"])


SEMANTIC_WITNESSES = {
    "non_three_inside": _has_non_three_inside,
    "large_inside_object": _has_large_inside_object,
    "multiple_objects_one_frame": _has_multiple_objects_one_frame,
    "outside_same_color": _has_outside_same_color,
}
SEMANTIC_RIVALS = {
    "color_three_only": _color_three_only,
    "at_most_two_cells": _at_most_two_cells,
    "first_object_only": _first_object_only,
    "global_same_color": _global_same_color,
}
WITNESS_RIVALS = {
    "non_three_inside": ["color_three_only"],
    "large_inside_object": ["at_most_two_cells"],
    "multiple_objects_one_frame": ["first_object_only"],
    "outside_same_color": ["global_same_color"],
}
CANONICAL_SHORTCUTS = {
    "color_three_only": _color_three_only,
    "at_most_two_cells": _at_most_two_cells,
    "first_object_only": _first_object_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos: list[dict[str, Any]], query: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        fits = all(rival(demo["input"]) == demo["output"] for demo in demos)
        if fits and rival(query["input"]) != query["output"]:
            reasons.append(f"{name} fits every demonstration but changes the query answer")
    return reasons


def _draw_frame(
    grid: list[list[int]], rect: tuple[int, int, int, int], color: int
) -> None:
    row0, col0, row1, col1 = rect
    for col in range(col0, col1 + 1):
        grid[row0][col] = color
        grid[row1][col] = color
    for row in range(row0, row1 + 1):
        grid[row][col0] = color
        grid[row][col1] = color


def _separated(
    first: tuple[int, int, int, int], second: tuple[int, int, int, int]
) -> bool:
    return (
        first[2] + 1 < second[0]
        or second[2] + 1 < first[0]
        or first[3] + 1 < second[1]
        or second[3] + 1 < first[1]
    )


def _rect_positions(
    height: int, width: int, sizes: tuple[tuple[int, int], ...]
) -> tuple[tuple[int, int, int, int], ...]:
    positions = []
    for frame_height, frame_width in sizes:
        for row0 in range(height - frame_height + 1):
            for col0 in range(width - frame_width + 1):
                positions.append(
                    (row0, col0, row0 + frame_height - 1, col0 + frame_width - 1)
                )
    return tuple(positions)


@lru_cache(maxsize=32)
def _pair_layouts(
    height: int,
    width: int,
    first_sizes: tuple[tuple[int, int], ...],
    second_sizes: tuple[tuple[int, int], ...],
) -> tuple[tuple[tuple[int, int, int, int], tuple[int, int, int, int]], ...]:
    first = _rect_positions(height, width, first_sizes)
    second = _rect_positions(height, width, second_sizes)
    return tuple((a, b) for a in first for b in second if _separated(a, b))


def _shape_placements(
    grid: list[list[int]],
    bounds: tuple[int, int, int, int],
    shapes: tuple[tuple[tuple[int, int], ...], ...],
) -> list[tuple[tuple[int, int], ...]]:
    row0, col0, row1, col1 = bounds
    result: list[tuple[tuple[int, int], ...]] = []
    for shape in shapes:
        max_row = max(row for row, _ in shape)
        max_col = max(col for _, col in shape)
        for base_row in range(row0, row1 - max_row + 1):
            for base_col in range(col0, col1 - max_col + 1):
                cells = tuple(
                    (base_row + row, base_col + col) for row, col in shape
                )
                if all(grid[row][col] == 0 for row, col in cells):
                    result.append(cells)
    return result


def _place_shape(
    grid: list[list[int]],
    bounds: tuple[int, int, int, int],
    color: int,
    shapes: tuple[tuple[tuple[int, int], ...], ...],
    rng: Any,
) -> tuple[tuple[int, int], ...]:
    candidates = _shape_placements(grid, bounds, shapes)
    if not candidates:
        raise RuntimeError(f"no shape placement available inside {bounds}")
    cells = rng.choice(candidates)
    for row, col in cells:
        grid[row][col] = color
    return cells


def _inside_bounds(rect: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    return rect[0] + 1, rect[1] + 1, rect[2] - 1, rect[3] - 1


def _place_outside(
    grid: list[list[int]],
    frames: tuple[tuple[int, int, int, int], ...],
    color: int,
    shapes: tuple[tuple[tuple[int, int], ...], ...],
    rng: Any,
) -> tuple[tuple[int, int], ...]:
    height, width = len(grid), len(grid[0])
    candidates = _shape_placements(grid, (0, 0, height - 1, width - 1), shapes)
    existing_same = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    lawful = []
    for cells in candidates:
        obj = {"bbox": _bbox(cells)}
        if any(
            _strictly_contains({"bbox": frame}, obj)
            for frame in frames
        ):
            continue
        if any(
            (row + drow, col + dcol) in existing_same
            for row, col in cells
            for drow, dcol in _NEIGHBORS
        ):
            continue
        lawful.append(cells)
    if not lawful:
        raise RuntimeError("no outside-object placement available")
    cells = rng.choice(lawful)
    for row, col in cells:
        grid[row][col] = color
    return cells


def _large_shapes(difficulty: str | None) -> tuple[tuple[tuple[int, int], ...], ...]:
    return _HARD_LARGE_SHAPES if difficulty == "hard" else _LARGE_SHAPES


def _draw_role_colors(
    ctx: Any,
    *,
    target_count: int = 1,
    targets_exclude_three: bool = False,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Draw distinct frame/target colors without encoding a profile palette.

    The first tuple contains one or two frame colors as requested by callers;
    callers derive that count from the number of remaining sampled colors.
    Target colors can exclude canonical color 3 when a profile must always
    witness the color-three-only shortcut.
    """
    if target_count not in (1, 2):
        raise ValueError("target_count must be one or two")
    rng = ctx.draw_rng("palette")
    target_pool = [color for color in range(1, 10) if not (targets_exclude_three and color == 3)]
    targets = tuple(rng.sample(target_pool, target_count))
    available_frames = [color for color in range(1, 10) if color not in targets]
    frame_count = 3 - target_count
    frames = tuple(rng.sample(available_frames, frame_count))
    return frames, targets


def _build_two_singletons(ctx: Any) -> list[list[int]]:
    height, width = 8, 12
    grid = full_grid(height, width, 0)
    layouts = _pair_layouts(
        height,
        width,
        ((3, 5), (4, 4), (4, 5), (5, 4)),
        ((3, 4), (4, 4), (4, 5), (5, 4)),
    )
    first, second = ctx.draw_rng("layout").choice(layouts)
    frame_colors, target_colors = _draw_role_colors(ctx)
    target_color = target_colors[0]
    _draw_frame(grid, first, frame_colors[0])
    _draw_frame(grid, second, frame_colors[1])
    motif_rng = ctx.draw_rng("motifs")
    _place_shape(grid, _inside_bounds(first), target_color, (_SINGLE,), motif_rng)
    _place_shape(grid, _inside_bounds(second), target_color, (_SINGLE,), motif_rng)
    return grid


def _build_outside_same_color(ctx: Any) -> list[list[int]]:
    height, width = 9, 12
    grid = full_grid(height, width, 0)
    layouts = _pair_layouts(
        height,
        width,
        ((4, 4), (4, 5), (5, 4)),
        ((4, 4), (4, 5), (5, 4)),
    )
    first, second = ctx.draw_rng("layout").choice(layouts)
    frame_colors, target_colors = _draw_role_colors(ctx)
    target_color = target_colors[0]
    _draw_frame(grid, first, frame_colors[0])
    _draw_frame(grid, second, frame_colors[1])
    motif_rng = ctx.draw_rng("motifs")
    _place_shape(grid, _inside_bounds(first), target_color, (_SINGLE,), motif_rng)
    _place_shape(grid, _inside_bounds(second), target_color, (_SINGLE,), motif_rng)
    _place_outside(
        grid, (first, second), target_color, (_SINGLE,), ctx.draw_rng("outside")
    )
    return grid


def _build_multi_cell(ctx: Any) -> list[list[int]]:
    height, width = 9, 13
    grid = full_grid(height, width, 0)
    layouts = _pair_layouts(
        height,
        width,
        ((5, 5), (5, 6), (6, 5), (6, 6)),
        ((4, 4), (4, 5), (5, 4), (5, 5)),
    )
    first, second = ctx.draw_rng("layout").choice(layouts)
    frame_colors, target_colors = _draw_role_colors(ctx)
    target_color = target_colors[0]
    _draw_frame(grid, first, frame_colors[0])
    _draw_frame(grid, second, frame_colors[1])
    motif_rng = ctx.draw_rng("motifs")
    _place_shape(
        grid,
        _inside_bounds(first),
        target_color,
        _large_shapes(ctx.difficulty),
        motif_rng,
    )
    _place_shape(grid, _inside_bounds(second), target_color, (_SINGLE,), motif_rng)
    _place_outside(
        grid, (first, second), target_color, (_SINGLE,), ctx.draw_rng("outside")
    )
    return grid


def _single_frame_layout(ctx: Any) -> tuple[int, int, int, int]:
    height, width = 10, 14
    candidates = _rect_positions(height, width, ((7, 8), (7, 9), (8, 7), (8, 8)))
    return ctx.draw_rng("layout").choice(candidates)


def _build_multiple_inside(ctx: Any) -> list[list[int]]:
    height, width = 10, 14
    grid = full_grid(height, width, 0)
    frame = _single_frame_layout(ctx)
    frame_colors, target_colors = _draw_role_colors(
        ctx, target_count=2, targets_exclude_three=True
    )
    _draw_frame(grid, frame, frame_colors[0])
    row0, col0, row1, col1 = _inside_bounds(frame)
    row_mid = (row0 + row1) // 2
    col_mid = (col0 + col1) // 2
    first_region = (row0, col0, max(row0 + 2, row_mid), max(col0 + 2, col_mid))
    second_region = (min(row1 - 1, row_mid + 1), min(col1 - 1, col_mid + 1), row1, col1)
    motif_rng = ctx.draw_rng("motifs")
    _place_shape(
        grid, first_region, target_colors[0], _large_shapes(ctx.difficulty), motif_rng
    )
    _place_shape(grid, second_region, target_colors[1], _SMALL_SECOND_SHAPES, motif_rng)
    _place_outside(
        grid,
        (frame,),
        target_colors[0],
        (_SINGLE, ((0, 0), (0, 1))),
        ctx.draw_rng("outside"),
    )
    return grid


_BUILDERS = {
    "two_singletons": _build_two_singletons,
    "outside_same_color": _build_outside_same_color,
    "multi_cell": _build_multi_cell,
    "multiple_inside": _build_multiple_inside,
}


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    profile = overrides.get("scene_profile")
    if profile is not None:
        if not isinstance(profile, str):
            raise TypeError("scene_profile must be a string")
        if profile not in SCENE_PROFILES:
            raise ValueError(
                f"scene_profile {profile!r} is not one of {list(SCENE_PROFILES)}"
            )


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: str | None = None,
    **overrides: Any,
) -> list[list[int]]:
    _validate_call(difficulty, overrides)
    scheduled = dict(overrides)
    if scheduled.get("scene_profile") is None:
        scheduled["scene_profile"] = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=scheduled,
    )
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    grid = _BUILDERS[profile](ctx)
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise RuntimeError(
            f"constructed {profile!r} but pixels observe as {observed!r}"
        )
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructed invalid scene: " + "; ".join(errors))
    return grid
