"""Generator for ARC task 0b999a8ea028.

The authoritative rule selects the largest non-blue connected component as a
prototype, finds color-1 components that are exact rectangular borders, and
rebuilds a blank output with a centered prototype copy inside every frame.
All source objects and frame pixels disappear.  A connected blue near-frame is
therefore not a destination, and a scene with no exact frames produces blank.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0b999a8ea028"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "d8a130fd2a56"

SUMMARY = (
    "Select the largest non-blue object, erase the input, and stamp its "
    "normalized shape centered inside each color-1 exact rectangular border. "
    "Smaller objects, malformed blue rings, and connected frame composites "
    "are erased; with no exact frame the output is blank."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.25
SCHEDULE_PROFILES = (
    "canonical",
    "size_contest",
    "nonframe_blue",
    "no_frames",
)
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-biased keyed draw",
        "valid": "11..18",
        "doc": "Returned grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-biased keyed draw",
        "valid": "11..20",
        "doc": "Returned grid width.",
    },
    "texture": {
        "type": "str",
        "default": "sample_index mod 4 schedule",
        "valid": "canonical|size_contest|nonframe_blue|no_frames",
        "doc": (
            "canonical uses only 5x5 frames; size_contest puts a smaller "
            "object before the true prototype and uses a 7x7 frame; "
            "nonframe_blue adds a broken blue ring beside a 6x6 frame; "
            "no_frames uses one connected blue frame-composite."
        ),
    },
}

INVARIANTS = [
    "one unique largest non-blue component always exists",
    "the largest component fits every exact frame interior",
    "every four consecutive natural draws cover all semantic profiles",
    "unknown overrides are rejected rather than ignored",
]

_COLORS = (2, 3, 4, 5, 6, 7, 8, 9)
_CANONICAL_SHAPES = (
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
)
_CONTEST_SHAPE = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))
_DECOY_SHAPE = ((0, 0), (0, 1))
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the semantic branch assigned to this sample index."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _rectangular_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} is not rectangular")
            continue
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("grid cells must be integer colors 0..9")
                return errors
    return errors


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Return nonzero monochrome 4-connected components in scan order."""
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
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for delta_row, delta_col in _NEIGHBORS:
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    point = (next_row, next_col)
                    if point in seen or grid[next_row][next_col] != color:
                        continue
                    seen.add(point)
                    stack.append(point)
            cells.sort()
            rows = [point[0] for point in cells]
            cols = [point[1] for point in cells]
            result.append(
                {
                    "color": color,
                    "cells": tuple(cells),
                    "size": len(cells),
                    "r1": min(rows),
                    "c1": min(cols),
                    "r2": max(rows),
                    "c2": max(cols),
                }
            )
    return result


def _border_cells(component: dict[str, Any]) -> set[tuple[int, int]]:
    r1, c1, r2, c2 = (
        component["r1"],
        component["c1"],
        component["r2"],
        component["c2"],
    )
    return {
        (row, col)
        for row in range(r1, r2 + 1)
        for col in range(c1, c2 + 1)
        if row in (r1, r2) or col in (c1, c2)
    }


def _is_exact_frame(component: dict[str, Any]) -> bool:
    return component["color"] == 1 and set(component["cells"]) == _border_cells(component)


def _with_geometry(component: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(component)
    enriched["height"] = component["r2"] - component["r1"] + 1
    enriched["width"] = component["c2"] - component["c1"] + 1
    return enriched


def analyze_scene(grid: list[list[int]]) -> dict[str, Any]:
    """Expose structural facts used by checks, witnesses, and tests."""
    errors = _rectangular_grid_errors(grid)
    if errors:
        return {
            "errors": errors,
            "components": [],
            "frames": [],
            "blue_impostors": [],
            "nonblue": [],
            "prototype": None,
        }
    components = [_with_geometry(component) for component in _components(grid)]
    frames = [component for component in components if _is_exact_frame(component)]
    blue_impostors = [
        component
        for component in components
        if component["color"] == 1 and not _is_exact_frame(component)
    ]
    nonblue = [component for component in components if component["color"] != 1]
    prototype = max(nonblue, key=lambda component: component["size"]) if nonblue else None
    return {
        "errors": [],
        "components": components,
        "frames": frames,
        "blue_impostors": blue_impostors,
        "nonblue": nonblue,
        "prototype": prototype,
    }


def _normalized_shape(component: dict[str, Any]) -> tuple[tuple[int, int], ...]:
    return tuple(
        sorted(
            (row - component["r1"], col - component["c1"])
            for row, col in component["cells"]
        )
    )


def _quotient_toward_zero(numerator: int, denominator: int) -> int:
    quotient = abs(numerator) // denominator
    return quotient if numerator >= 0 else -quotient


def _stamp_output(
    grid: list[list[int]],
    prototype: dict[str, Any],
    frames: list[dict[str, Any]],
    *,
    top_left: bool = False,
) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    shape = _normalized_shape(prototype)
    shape_height = prototype["height"]
    shape_width = prototype["width"]
    for frame in frames:
        interior_height = frame["height"] - 2
        interior_width = frame["width"] - 2
        row_offset = 0 if top_left else _quotient_toward_zero(
            interior_height - shape_height, 2
        )
        col_offset = 0 if top_left else _quotient_toward_zero(
            interior_width - shape_width, 2
        )
        start_row = frame["r1"] + 1 + row_offset
        start_col = frame["c1"] + 1 + col_offset
        for shape_row, shape_col in shape:
            out_row = start_row + shape_row
            out_col = start_col + shape_col
            if 0 <= out_row < height and 0 <= out_col < width:
                output[out_row][out_col] = prototype["color"]
    return output


def _solve_with(
    grid: list[list[int]],
    *,
    selector: Callable[[list[dict[str, Any]]], dict[str, Any]],
    frame_selector: Callable[[dict[str, Any]], bool] | None = None,
    top_left: bool = False,
    blue_bboxes: bool = False,
) -> list[list[int]]:
    facts = analyze_scene(grid)
    if facts["errors"]:
        raise ValueError("malformed grid: " + "; ".join(facts["errors"]))
    if not facts["nonblue"]:
        raise ValueError("authoritative rule has no non-blue prototype")
    prototype = selector(facts["nonblue"])
    if blue_bboxes:
        frames = [
            {
                **component,
                "height": component["height"],
                "width": component["width"],
            }
            for component in facts["components"]
            if component["color"] == 1
            and component["height"] >= 3
            and component["width"] >= 3
        ]
    else:
        frames = list(facts["frames"])
    if frame_selector is not None:
        frames = [frame for frame in frames if frame_selector(frame)]
    return _stamp_output(grid, prototype, frames, top_left=top_left)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure-Python mirror of the selected canonical Racket rule."""
    return _solve_with(
        grid,
        selector=lambda components: max(components, key=lambda component: component["size"]),
    )


# Backward-compatible private name retained for local consumers of v2.
_mirror = rule_mirror


def _rival_first_nonblue(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with(grid, selector=lambda components: components[0])


def _rival_fixed_5x5_frames(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with(
        grid,
        selector=lambda components: max(components, key=lambda component: component["size"]),
        frame_selector=lambda frame: frame["height"] == frame["width"] == 5,
    )


def _rival_interior_top_left(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with(
        grid,
        selector=lambda components: max(components, key=lambda component: component["size"]),
        top_left=True,
    )


def _rival_any_blue_bbox(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with(
        grid,
        selector=lambda components: max(components, key=lambda component: component["size"]),
        blue_bboxes=True,
    )


SEMANTIC_RIVALS = {
    "first_nonblue": _rival_first_nonblue,
    "fixed_5x5_frames": _rival_fixed_5x5_frames,
    "interior_top_left": _rival_interior_top_left,
    "any_blue_bbox": _rival_any_blue_bbox,
}
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in ("first_nonblue", "fixed_5x5_frames", "interior_top_left")
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _infer_texture(facts: dict[str, Any]) -> str:
    frames = facts["frames"]
    impostors = facts["blue_impostors"]
    nonblue = facts["nonblue"]
    frame_sizes = {(frame["height"], frame["width"]) for frame in frames}
    if (
        len(nonblue) == 1
        and len(frames) in (2, 3)
        and frame_sizes == {(5, 5)}
        and not impostors
    ):
        return "canonical"
    if (
        len(nonblue) == 2
        and len(frames) == 1
        and frame_sizes == {(7, 7)}
        and not impostors
    ):
        return "size_contest"
    if (
        len(nonblue) == 1
        and len(frames) == 1
        and frame_sizes == {(6, 6)}
        and len(impostors) == 1
    ):
        return "nonframe_blue"
    if len(nonblue) == 1 and not frames and len(impostors) == 1:
        return "no_frames"
    return "unknown"


def semantic_signature(grid: list[list[int]]) -> dict[str, Any]:
    facts = analyze_scene(grid)
    prototype = facts["prototype"]
    return {
        "texture": _infer_texture(facts),
        "frame_count": len(facts["frames"]),
        "blue_impostor_count": len(facts["blue_impostors"]),
        "nonblue_count": len(facts["nonblue"]),
        "prototype_size": prototype["size"] if prototype else 0,
        "prototype_bbox": (
            (prototype["height"], prototype["width"]) if prototype else None
        ),
    }


def observe_overrides(grid: list[list[int]]) -> dict[str, Any]:
    if _rectangular_grid_errors(grid):
        return {}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "texture": semantic_signature(grid)["texture"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject scenes outside the four explicit teaching profiles."""
    del difficulty
    errors = _rectangular_grid_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not (11 <= height <= 18 and 11 <= width <= 20):
        errors.append(f"grid dimensions {height}x{width} are outside 11..18 x 11..20")

    facts = analyze_scene(grid)
    nonblue = facts["nonblue"]
    prototype = facts["prototype"]
    if not nonblue:
        errors.append("no non-blue prototype")
        return errors
    if len(nonblue) not in (1, 2):
        errors.append(f"expected one prototype and at most one decoy, got {len(nonblue)}")
    if len(nonblue) == 2:
        sizes = sorted(component["size"] for component in nonblue)
        if sizes[0] >= sizes[1]:
            errors.append("prototype must be uniquely larger than the decoy")
    if prototype is None:
        errors.append("prototype selection failed")
        return errors

    for frame in facts["frames"]:
        if prototype["height"] > frame["height"] - 2:
            errors.append("prototype is taller than a frame interior")
        if prototype["width"] > frame["width"] - 2:
            errors.append("prototype is wider than a frame interior")

    texture = _infer_texture(facts)
    if texture == "unknown":
        errors.append("scene does not match any declared texture profile")
    elif texture == "canonical":
        if prototype["size"] not in (3, 4):
            errors.append("canonical prototype must contain 3 or 4 cells")
    elif texture == "size_contest":
        if prototype["size"] != 5:
            errors.append("size_contest prototype must contain 5 cells")
        if nonblue and nonblue[0] is prototype:
            errors.append("size_contest decoy must precede the larger prototype")
        if min(component["size"] for component in nonblue) != 2:
            errors.append("size_contest decoy must contain 2 cells")
    elif texture == "nonframe_blue":
        impostor = facts["blue_impostors"][0]
        if (impostor["height"], impostor["width"]) != (5, 5):
            errors.append("nonframe_blue impostor must have a 5x5 bounding box")
        if len(_border_cells(impostor) - set(impostor["cells"])) != 1:
            errors.append("nonframe_blue impostor must be a one-cell-broken ring")
    elif texture == "no_frames":
        impostor = facts["blue_impostors"][0]
        if impostor["height"] < 5 or impostor["width"] < 5 or impostor["size"] < 16:
            errors.append("no_frames blue component is too small to teach frame rejection")

    if meta:
        requested = meta.get("overrides", meta) if isinstance(meta, dict) else {}
        if isinstance(requested, dict):
            observed = observe_overrides(grid)
            for axis in AXES:
                if axis in requested and requested[axis] != observed.get(axis):
                    errors.append(
                        f"override {axis}={requested[axis]!r} realized as {observed.get(axis)!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the narrow public manifold, including its negative example."""
    errors = self_check(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    facts = analyze_scene(grid)
    texture = _infer_texture(facts)
    prototype = facts["prototype"]
    reasons: list[str] = []
    if (height, width) not in {(11, 11), (12, 12), (13, 13)}:
        reasons.append("grid dimensions are not one of the public 11/12/13 square profiles")
    palette = {value for row in grid for value in row}
    if len(palette) != 3 or not {0, 1}.issubset(palette):
        reasons.append("public profile uses exactly background, blue, and one prototype color")
    if len(facts["nonblue"]) != 1:
        reasons.append("public profile has exactly one non-blue object")
    if prototype and (
        prototype["size"] not in (3, 4)
        or (prototype["height"], prototype["width"]) not in {(2, 2), (2, 3)}
    ):
        reasons.append("prototype is outside the public 3/4-cell 2-row shapes")
    if texture not in {"canonical", "no_frames"}:
        reasons.append("public profile is either exact 5x5 frames or the connected-frame negative")
    return reasons


def _witness_decoy_precedes_largest(grid) -> bool:
    facts = analyze_scene(grid)
    return (
        len(facts["nonblue"]) == 2
        and facts["prototype"] is not None
        and facts["nonblue"][0] is not facts["prototype"]
        and facts["nonblue"][0]["size"] < facts["prototype"]["size"]
    )


def _witness_generalized_frame(grid) -> bool:
    facts = analyze_scene(grid)
    return any((frame["height"], frame["width"]) != (5, 5) for frame in facts["frames"])


def _witness_positive_center_offset(grid) -> bool:
    facts = analyze_scene(grid)
    prototype = facts["prototype"]
    if prototype is None:
        return False
    return any(
        (frame["height"] - 2 - prototype["height"]) // 2 > 0
        or (frame["width"] - 2 - prototype["width"]) // 2 > 0
        for frame in facts["frames"]
    )


def _witness_nonframe_blue(grid) -> bool:
    return bool(analyze_scene(grid)["blue_impostors"])


SEMANTIC_WITNESSES = {
    "decoy_precedes_largest": _witness_decoy_precedes_largest,
    "generalized_frame": _witness_generalized_frame,
    "positive_center_offset": _witness_positive_center_offset,
    "nonframe_blue_component": _witness_nonframe_blue,
}
WITNESS_RIVALS = {
    "decoy_precedes_largest": ["first_nonblue"],
    "generalized_frame": ["fixed_5x5_frames"],
    "positive_center_offset": ["interior_top_left"],
    "nonframe_blue_component": ["any_blue_bbox"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require a four-profile lesson that refutes every declared shortcut."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need {EXAMPLES_NEEDED} demos, got {len(demos)}")
    profiles: set[str] = set()
    for index, pair in enumerate(demos):
        try:
            actual = rule_mirror(pair["input"])
        except Exception as exc:  # pragma: no cover - contract guard
            reasons.append(f"demo {index} mirror failed: {type(exc).__name__}: {exc}")
            continue
        if actual != pair.get("output"):
            reasons.append(f"demo {index} output disagrees with the selected rule")
        profiles.add(semantic_signature(pair["input"])["texture"])
    missing = sorted(set(SCHEDULE_PROFILES) - profiles)
    if missing:
        reasons.append(f"lesson misses semantic profile(s): {missing}")
    for name, competitor in LESSON_COMPETITORS.items():
        survived = True
        for pair in demos:
            try:
                if competitor(pair["input"]) != pair["output"]:
                    survived = False
                    break
            except Exception:
                survived = False
                break
        if survived:
            reasons.append(f"competitor {name!r} fits every demo")
    try:
        if rule_mirror(query["input"]) != query.get("output"):
            reasons.append("query output disagrees with the selected rule")
    except Exception as exc:  # pragma: no cover - contract guard
        reasons.append(f"query mirror failed: {type(exc).__name__}: {exc}")
    return reasons


def _paint_shape(grid, shape, row0: int, col0: int, color: int) -> None:
    for row, col in shape:
        grid[row0 + row][col0 + col] = color


def _paint_frame(grid, row0: int, col0: int, size: int) -> None:
    for col in range(col0, col0 + size):
        grid[row0][col] = 1
        grid[row0 + size - 1][col] = 1
    for row in range(row0, row0 + size):
        grid[row][col0] = 1
        grid[row][col0 + size - 1] = 1


def _paint_broken_ring(grid, row0: int, col0: int) -> None:
    _paint_frame(grid, row0, col0, 5)
    grid[row0][col0 + 2] = 0


def _draw_dimension(ctx, label: str, lo: int, hi: int, preferred: int, overridden: bool) -> int:
    if overridden:
        return ctx.draw_int(label, lo, hi)
    # Keep exact canonical scale visible without suppressing the declared
    # endpoints.  Every legal override remains an option and is validated by
    # GenCtx; the repeated preferred value only biases natural draws.
    options = (preferred,) * 128 + tuple(range(lo, hi + 1))
    return int(ctx.draw_choice(label, options))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty=difficulty)
    if "texture" in overrides:
        texture = ctx.draw_choice("texture", SCHEDULE_PROFILES)
    else:
        texture = ctx.draw_choice("texture", (scheduled,))

    preferred = 11 + ((int(seed) + int(sample_index)) % 3)
    grid_h = _draw_dimension(
        ctx, "grid_h", 11, 18, preferred, "grid_h" in overrides
    )
    grid_w = _draw_dimension(
        ctx, "grid_w", 11, 20, preferred, "grid_w" in overrides
    )
    prototype_color = ctx.draw_color("prototype_color", exclude=(0, 1))
    grid = full_grid(grid_h, grid_w, 0)

    if texture == "canonical":
        shape = ctx.draw_choice("prototype_shape", _CANONICAL_SHAPES)
        _paint_shape(grid, shape, 0, 0, prototype_color)
        _paint_frame(grid, 0, grid_w - 5, 5)
        _paint_frame(grid, grid_h - 5, 0, 5)
        if grid_h >= 13 and grid_w >= 13:
            _paint_frame(grid, grid_h - 5, grid_w - 5, 5)
    elif texture == "size_contest":
        decoy_color = ctx.draw_choice(
            "decoy_color", tuple(color for color in _COLORS if color != prototype_color)
        )
        _paint_shape(grid, _DECOY_SHAPE, 0, 0, decoy_color)
        _paint_shape(grid, _CONTEST_SHAPE, 0, max(4, grid_w - 6), prototype_color)
        _paint_frame(grid, grid_h - 7, grid_w - 7, 7)
    elif texture == "nonframe_blue":
        shape = ctx.draw_choice("prototype_shape", _CANONICAL_SHAPES)
        _paint_shape(grid, shape, 0, 0, prototype_color)
        _paint_frame(grid, 0, grid_w - 6, 6)
        _paint_broken_ring(grid, grid_h - 5, 0)
    elif texture == "no_frames":
        shape = ctx.draw_choice("prototype_shape", _CANONICAL_SHAPES)
        _paint_shape(grid, shape, 0, 0, prototype_color)
        row0, col0 = grid_h - 5, grid_w - 10
        _paint_frame(grid, row0, col0, 5)
        _paint_frame(grid, row0, col0 + 5, 5)
    else:  # GenCtx already validates overrides; this guards future edits.
        raise ValueError(f"unsupported texture {texture!r}")

    findings = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": dict(overrides)},
    )
    if findings:
        raise ValueError("constructed invalid scene: " + "; ".join(findings))
    return grid


def mutation_fixtures():
    """Near-miss that must not be admitted as an exact-frame lesson."""
    grid = generate(44, 0, grid_h=11, grid_w=11, texture="canonical")
    frame = analyze_scene(grid)["frames"][0]
    broken = [row[:] for row in grid]
    broken[frame["r1"]][frame["c1"] + 1] = 0
    return [("one_cell_broken_exact_frame", broken)]
