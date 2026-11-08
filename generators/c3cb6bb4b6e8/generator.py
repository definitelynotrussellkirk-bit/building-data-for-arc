"""Generator for c3cb6bb4b6e8 — rotate a template by each frame's local key.

The input contains one small blue (1) template outside two or three hollow
7x7 gray (7) frames. Ordinary generated lessons keep the gray borders as
separate connected components. Every frame contains exactly one local key:
2 = identity, 3 = rotate clockwise, 4 = rotate 180 degrees, and
5 = rotate counter-clockwise.  The transformed template is centered in the
5x5 frame interior and recolored to the key color; the source template is
removed while frames and keys are preserved.

The selected oracle acts on gray connected components that are themselves
rectangular frames. Therefore canonical touching-border scenes remain accepted
by ``self_check`` but are not used as strict teaching draws: their merged gray
component is preserved without a pasted copy. The ordinary distribution is
anchored to a linked canonical profile while varying dimensions, placement,
template morphology, key positions, and key combinations. Every declared axis
is exactly recoverable from the returned grid.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c3cb6bb4b6e8"
TASK_ID = "c3cb6bb4b6e8"
VERSION = "2.0.0"
RULE_HASH = "514be61a9f3b"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "Extract and remove the unique blue (1) template. For every gray connected "
    "component that is itself a hollow rectangular frame, read its local key: 2 keeps the template, 3 rotates it 90 degrees "
    "clockwise, 4 rotates it 180 degrees, and 5 rotates it 90 degrees "
    "counter-clockwise. Center the transformed copy in that frame's 5x5 "
    "interior and recolor it to the key color. Preserve all frames and keys. "
    "Touching frame borders merge into a non-frame component, so the selected "
    "oracle preserves that group without adding copies."
)

INVARIANTS = [
    "background is 0 and the input palette is a subset of {0,1,2,3,4,5,7}",
    "exactly one 4-connected blue template of 3..5 cells lies outside every frame box",
    "exactly 2..3 geometric hollow 7x7 gray frames exist; canonical shared-border layouts remain authority-valid",
    "ordinary generated lessons keep every frame border in its own gray connected component",
    "each frame interior contains exactly one local key in {2,3,4,5}",
    "all gray cells belong to a detected frame border and all key cells belong to one frame",
    "the template fits centered in every 5x5 frame interior under every rotation",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[()] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile anchors plus 15..18 by difficulty",
        "valid": "15..18",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchors plus 15..20 by difficulty",
        "valid": "15..20",
    },
    "n_frames": {
        "type": "int",
        "default": "mostly 2 easy/medium and 3 hard, with both counts in every band",
        "valid": "2..3",
    },
    "template_cells": {
        "type": "int",
        "default": "3 easy, 4 medium, 5 hard with canonical-profile exceptions",
        "valid": "3..5",
    },
}

_FRAME_SIZE = 7
_KEY_COLORS = (2, 3, 4, 5)
_ALLOWED = {0, 1, 2, 3, 4, 5, 7}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    min_row = min(row for row, _col in points)
    min_col = min(col for _row, col in points)
    return tuple(sorted((row - min_row, col - min_col) for row, col in points))


def _rotate_once(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = _normalize(cells)
    max_row = max(row for row, _col in points)
    return _normalize((col, max_row - row) for row, col in points)


def _rotate(cells: Iterable[tuple[int, int]], turns: int) -> tuple[tuple[int, int], ...]:
    result = _normalize(cells)
    for _ in range(turns % 4):
        result = _rotate_once(result)
    return result


# All shapes fit inside a 3x3 box. The canonical subset is kept explicit so
# strict_canonical_like can measure the real linked morphology rather than only
# independent size marginals.
_SHAPES_BY_SIZE: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    3: (
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (1, 0)),
    ),
    4: (
        ((0, 1), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
    5: (
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    ),
}

# Exact canonical linked profiles: (height, width, frame top-lefts, normalized
# template). Key positions and key colors are lawful nuisance variables.
_CANONICAL_PROFILES: tuple[
    tuple[int, int, tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]], ...
] = (
    (14, 16, ((1, 9), (7, 8)), ((0, 0), (1, 0), (1, 1))),
    (15, 15, ((1, 8), (8, 1)), ((0, 0), (0, 1), (1, 1), (1, 2))),
    (16, 18, ((2, 10), (9, 9)), ((0, 1), (1, 0), (1, 1), (1, 2))),
    (15, 17, ((1, 10), (8, 9)), ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2))),
    (16, 16, ((2, 9), (9, 2)), ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0))),
    (16, 18, ((1, 10), (8, 1), (8, 9)), ((0, 0), (1, 0), (1, 1))),
)
_CANONICAL_PROFILE_KEYS = {
    (height, width, tuple(sorted(tops)), _normalize(shape))
    for height, width, tops, shape in _CANONICAL_PROFILES
}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in AXES:
        if name in overrides and overrides[name] is not None:
            value = overrides[name]
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name} must be an integer")


def _draw_scheduled_int(ctx, name: str, lo: int, hi: int, scheduled: int) -> int:
    """Record a deterministic default while honoring the full declared range."""
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, scheduled, scheduled)


def _default_plan(
    ctx, difficulty: str | None, sample_index: int, has_overrides: bool
) -> tuple[int, int, int, int, tuple[tuple[int, int], ...] | None, tuple[tuple[int, int], ...] | None]:
    """Return axes plus optional exact canonical frame/template profile."""
    band = "medium" if difficulty is None else difficulty
    schedule_slot = sample_index % 3 if not has_overrides else 2

    if schedule_slot in (0, 1):
        if schedule_slot == 0:
            # Canonical merged-border examples expose the selected oracle's
            # connected-component boundary. Keeping one in every three draws
            # also makes that branch identifiable in every three-demo window.
            merged_profiles = (2, 3, 5)
            profile_index = merged_profiles[(sample_index // 3) % len(merged_profiles)]
        else:
            # Profile 4 is a fully active, separated canonical profile.
            profile_index = 4
        height, width, frame_tops, shape = _CANONICAL_PROFILES[profile_index]
        return (
            _draw_scheduled_int(ctx, "grid_h", 15, 18, height),
            _draw_scheduled_int(ctx, "grid_w", 15, 20, width),
            _draw_scheduled_int(ctx, "n_frames", 2, 3, len(frame_tops)),
            _draw_scheduled_int(ctx, "template_cells", 3, 5, len(shape)),
            frame_tops,
            _normalize(shape),
        )

    if band == "easy":
        dim_options = ((15, 15), (15, 16), (16, 15), (16, 16))
        scheduled_frames = 3 if sample_index % 8 == 7 else 2
        scheduled_cells = 3
    elif band == "hard":
        dim_options = ((16, 18), (17, 18), (17, 19), (18, 20))
        scheduled_frames = 2 if sample_index % 8 == 7 else 3
        scheduled_cells = 5
    else:
        dim_options = ((15, 16), (15, 17), (16, 16), (16, 18), (17, 18))
        scheduled_frames = 3 if sample_index % 4 == 3 else 2
        scheduled_cells = 4

    scheduled_h, scheduled_w = dim_options[sample_index % len(dim_options)]
    return (
        _draw_scheduled_int(ctx, "grid_h", 15, 18, scheduled_h),
        _draw_scheduled_int(ctx, "grid_w", 15, 20, scheduled_w),
        _draw_scheduled_int(ctx, "n_frames", 2, 3, scheduled_frames),
        _draw_scheduled_int(ctx, "template_cells", 3, 5, scheduled_cells),
        None,
        None,
    )


def _frame_border(top: int, left: int) -> set[tuple[int, int]]:
    bottom = top + _FRAME_SIZE - 1
    right = left + _FRAME_SIZE - 1
    return {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if row in (top, bottom) or col in (left, right)
    }


def _frame_interior(top: int, left: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        (row, col)
        for row in range(top + 1, top + _FRAME_SIZE - 1)
        for col in range(left + 1, left + _FRAME_SIZE - 1)
    )


def _general_frame_tops(height: int, width: int, n_frames: int, sample_index: int) -> tuple[tuple[int, int], ...]:
    """Canonical-family placements that work for every declared axis tuple."""
    top_row = 0
    bottom_row = height - 7
    left_col = 0 if width == 15 else sample_index % min(2, width - 14)
    right_col = width - 7

    diagonal = ((top_row, right_col), (bottom_row, left_col))
    if n_frames == 2:
        return diagonal
    return diagonal + ((bottom_row, right_col),)


def _place_template(
    grid: list[list[int]],
    shape: tuple[tuple[int, int], ...],
    frame_tops: tuple[tuple[int, int], ...],
    rng,
) -> None:
    height, width = len(grid), len(grid[0])
    shape_h = max(row for row, _col in shape) + 1
    shape_w = max(col for _row, col in shape) + 1
    forbidden = {
        (row, col)
        for top, left in frame_tops
        for row in range(top, top + _FRAME_SIZE)
        for col in range(left, left + _FRAME_SIZE)
    }
    candidates = [
        (top, left)
        for top in range(height - shape_h + 1)
        for left in range(width - shape_w + 1)
        if all((top + dr, left + dc) not in forbidden for dr, dc in shape)
    ]
    rng.shuffle(candidates)
    # Prefer placements that do not touch a frame; this prevents location from
    # accidentally acting as a frame-membership cue while retaining edge cases.
    candidates.sort(
        key=lambda origin: sum(
            (origin[0] + dr + rr, origin[1] + dc + cc) in forbidden
            for dr, dc in shape
            for rr, cc in _CARDINAL
        )
    )
    if not candidates:
        raise ValueError("could not place the template outside all frame boxes")
    top, left = candidates[0]
    for dr, dc in shape:
        grid[top + dr][left + dc] = 1


def _components_of_color(grid: list[list[int]], color: int) -> list[tuple[tuple[int, int], ...]]:
    unseen = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    result: list[tuple[tuple[int, int], ...]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = [start]
        component: list[tuple[int, int]] = []
        for row, col in queue:
            component.append((row, col))
            for dr, dc in _CARDINAL:
                neighbour = (row + dr, col + dc)
                if neighbour in unseen:
                    unseen.remove(neighbour)
                    queue.append(neighbour)
        result.append(tuple(sorted(component)))
    return result


def _find_frames(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Find exact 7x7 frames even when canonical borders touch or overlap."""
    height, width = len(grid), len(grid[0])
    found: list[dict[str, Any]] = []
    for top in range(height - _FRAME_SIZE + 1):
        for left in range(width - _FRAME_SIZE + 1):
            border = _frame_border(top, left)
            if not all(grid[row][col] == 7 for row, col in border):
                continue
            interior = _frame_interior(top, left)
            keys = [
                (row, col, grid[row][col])
                for row, col in interior
                if grid[row][col] in _KEY_COLORS
            ]
            if len(keys) != 1:
                continue
            if any(grid[row][col] not in (0, * _KEY_COLORS) for row, col in interior):
                continue
            if any(
                grid[row][col] in _KEY_COLORS and (row, col, grid[row][col]) not in keys
                for row, col in interior
            ):
                continue
            found.append(
                {
                    "top": top,
                    "left": left,
                    "bbox": (top, left, top + 6, left + 6),
                    "border": border,
                    "interior": interior,
                    "key": keys[0],
                }
            )
    return sorted(found, key=lambda item: item["bbox"])


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a non-empty rectangle"]}
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return {"errors": ["grid rows must be lists or tuples"]}
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular with non-empty rows"]}
    work = [list(row) for row in grid]
    height = len(work)
    if not 14 <= height <= 18 or not 15 <= width <= 20:
        errors.append("grid dimensions must be within height 14..18 and width 15..20")

    bad = [
        (row, col, value)
        for row, values in enumerate(work)
        for col, value in enumerate(values)
        if isinstance(value, bool) or not isinstance(value, int) or value not in _ALLOWED
    ]
    if bad:
        errors.append("input palette must be a subset of {0,1,2,3,4,5,7}")
        return {"errors": errors, "grid_h": height, "grid_w": width, "bad_cells": bad[:8]}

    frames = _find_frames(work)
    if not 2 <= len(frames) <= 3:
        errors.append(f"expected exactly 2..3 hollow 7x7 frames, found {len(frames)}")

    all_border = set().union(*(frame["border"] for frame in frames)) if frames else set()
    gray_cells = {
        (row, col)
        for row, values in enumerate(work)
        for col, value in enumerate(values)
        if value == 7
    }
    if gray_cells != all_border:
        errors.append("every gray cell must belong to a detected 7x7 frame border")

    frame_keys = [frame["key"] for frame in frames]
    key_cells = [
        (row, col, value)
        for row, values in enumerate(work)
        for col, value in enumerate(values)
        if value in _KEY_COLORS
    ]
    if sorted(frame_keys) != sorted(key_cells):
        errors.append("every key cell must belong to exactly one detected frame interior")

    templates = _components_of_color(work, 1)
    if len(templates) != 1:
        errors.append(f"expected exactly one 4-connected blue template, found {len(templates)}")
        template: tuple[tuple[int, int], ...] = ()
    else:
        template = templates[0]
        if not 3 <= len(template) <= 5:
            errors.append(f"template must contain 3..5 cells, found {len(template)}")
        rows = [row for row, _col in template]
        cols = [col for _row, col in template]
        template_h = max(rows) - min(rows) + 1
        template_w = max(cols) - min(cols) + 1
        if template_h > 3 or template_w > 3:
            errors.append("template bounding box must fit within 3x3")
        for row, col in template:
            if any(
                top <= row <= top + 6 and left <= col <= left + 6
                for top, left in ((frame["top"], frame["left"]) for frame in frames)
            ):
                errors.append("template must lie outside every frame bounding box")
                break
        rotations = {_rotate(template, turns) for turns in range(4)}

    gray_components = [set(component) for component in _components_of_color(work, 7)]
    active_frames = [
        frame
        for frame in frames
        if any(component == frame["border"] for component in gray_components)
    ]
    frame_tops = tuple((frame["top"], frame["left"]) for frame in frames)
    template_shape = _normalize(template) if template else ()
    return {
        "errors": errors,
        "grid_h": height,
        "grid_w": width,
        "frames": frames,
        "active_frames": active_frames,
        "active_frame_tops": tuple((frame["top"], frame["left"]) for frame in active_frames),
        "gray_component_count": len(gray_components),
        "frame_tops": frame_tops,
        "n_frames": len(frames),
        "keys": frame_keys,
        "key_colors": tuple(key[2] for key in frame_keys),
        "active_key_colors": tuple(frame["key"][2] for frame in active_frames),
        "template": template,
        "template_shape": template_shape,
        "template_cells": len(template),
        "rotation_count": len(rotations) if template else 0,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Authority-valid input grammar; accepts all canonical train/test inputs."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_frames": analysis["n_frames"],
        "template_cells": analysis["template_cells"],
    }


def _apply_variant(
    grid: list[list[int]],
    *,
    rotation_mode: str = "local",
    placement: str = "center",
    keep_template: bool = False,
    fixed_color: int | None = None,
    frame_mode: str = "active",
) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 7 or value in _KEY_COLORS or (keep_template and value == 1):
                output[row][col] = value

    selected_frames = (
        analysis["frames"] if frame_mode == "geometric" else analysis["active_frames"]
    )
    first_key = selected_frames[0]["key"][2] if selected_frames else 2
    for frame in selected_frames:
        key = frame["key"][2]
        if rotation_mode == "none":
            turns = 0
        elif rotation_mode == "global_first":
            turns = first_key - 2
        elif rotation_mode == "shifted":
            turns = (key - 1) % 4
        else:
            turns = key - 2
        shape = _rotate(analysis["template_shape"], turns)
        shape_h = max(row for row, _col in shape) + 1
        shape_w = max(col for _row, col in shape) + 1
        if placement == "top_left":
            top = frame["top"] + 1
            left = frame["left"] + 1
        else:
            top = frame["top"] + 1 + (5 - shape_h) // 2
            left = frame["left"] + 1 + (5 - shape_w) // 2
        paint = key if fixed_color is None else fixed_color
        for dr, dc in shape:
            output[top + dr][left + dc] = paint
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror used only for tests; Racket is authoritative."""
    return _apply_variant(grid)


def strict_canonical_like(grid) -> list[str]:
    """Require the exact linked canonical dimensions/layout/morphology profile."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    profile = (
        analysis["grid_h"],
        analysis["grid_w"],
        tuple(sorted(analysis["frame_tops"])),
        analysis["template_shape"],
    )
    reasons: list[str] = []
    if profile not in _CANONICAL_PROFILE_KEYS:
        reasons.append("dimension, frame-layout, and template morphology are not a linked canonical profile")
    if len(set(analysis["key_colors"])) != analysis["n_frames"]:
        reasons.append("canonical inputs use a distinct local key in every geometric frame")
    return reasons


def _lawful(grid) -> dict[str, Any] | None:
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis


def _witness(grid, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    analysis = _lawful(grid)
    return False if analysis is None else bool(predicate(analysis))


SEMANTIC_WITNESSES = {
    "key_identity_2": lambda grid: _witness(grid, lambda a: 2 in a["active_key_colors"]),
    "key_clockwise_3": lambda grid: _witness(grid, lambda a: 3 in a["active_key_colors"]),
    "key_half_turn_4": lambda grid: _witness(grid, lambda a: 4 in a["active_key_colors"]),
    "key_counterclockwise_5": lambda grid: _witness(grid, lambda a: 5 in a["active_key_colors"]),
    "four_distinct_template_rotations": lambda grid: _witness(
        grid, lambda a: a["rotation_count"] == 4
    ),
    "multiple_distinct_local_keys": lambda grid: _witness(
        grid, lambda a: len(set(a["active_key_colors"])) >= 2
    ),
    "centered_not_top_left": lambda grid: _witness(
        grid, lambda a: bool(a["active_frames"])
    ),
    "source_template_removed": lambda grid: _witness(grid, lambda a: bool(a["template"])),
    "recolor_by_local_key": lambda grid: _witness(
        grid, lambda a: any(color != 2 for color in a["active_key_colors"])
    ),
    "merged_frame_group_preserved_without_copy": lambda grid: _witness(
        grid, lambda a: len(a["active_frames"]) < a["n_frames"]
    ),
}


def _rival_no_rotation(grid):
    return _apply_variant(grid, rotation_mode="none")


def _rival_global_first_key(grid):
    return _apply_variant(grid, rotation_mode="global_first")


def _rival_shifted_key_map(grid):
    return _apply_variant(grid, rotation_mode="shifted")


def _rival_top_left(grid):
    return _apply_variant(grid, placement="top_left")


def _rival_keep_template(grid):
    return _apply_variant(grid, keep_template=True)


def _rival_fixed_red(grid):
    return _apply_variant(grid, fixed_color=2)


def _rival_transform_every_geometric_frame(grid):
    return _apply_variant(grid, frame_mode="geometric")


SEMANTIC_RIVALS = {
    "ignore_rotation_keys": _rival_no_rotation,
    "one_global_key_for_all_frames": _rival_global_first_key,
    "shifted_key_rotation_map": _rival_shifted_key_map,
    "top_left_instead_of_center": _rival_top_left,
    "keep_source_template": _rival_keep_template,
    "paint_every_copy_red": _rival_fixed_red,
    "transform_touching_geometric_frames": _rival_transform_every_geometric_frame,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
WITNESS_RIVALS = {
    "multiple_distinct_local_keys": ["one_global_key_for_all_frames"],
    "centered_not_top_left": ["top_left_instead_of_center"],
    "source_template_removed": ["keep_source_template"],
    "recolor_by_local_key": ["paint_every_copy_red"],
    "key_identity_2": ["shifted_key_rotation_map"],
    "key_clockwise_3": ["ignore_rotation_keys", "shifted_key_rotation_map"],
    "key_half_turn_4": ["ignore_rotation_keys", "shifted_key_rotation_map"],
    "key_counterclockwise_5": ["ignore_rotation_keys", "shifted_key_rotation_map"],
    "merged_frame_group_preserved_without_copy": [
        "transform_touching_geometric_frames"
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named plausible rival survives all demos."""
    reasons: list[str] = []
    query_input = query.get("input") if isinstance(query, dict) else None
    query_analysis = _lawful(query_input)
    if query_analysis is None:
        return ["query input is not a lawful local-key frame scene"]
    query_truth = rule_mirror(query_input)

    for index, demo in enumerate(demos):
        demo_input = demo.get("input") if isinstance(demo, dict) else None
        if _lawful(demo_input) is None:
            reasons.append(f"demo {index} input is not a lawful local-key frame scene")
            continue
        if demo.get("output") != rule_mirror(demo_input):
            reasons.append(f"demo {index} output disagrees with the local-key rule mirror")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query_input) != query_truth:
                reasons.append(
                    f"competing rule {name!r} matches every demo but changes the query answer"
                )
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, observable, structurally lawful input grid."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height, width, n_frames, template_cells, canonical_tops, canonical_shape = _default_plan(
        ctx, difficulty, sample_index, bool(overrides)
    )
    frame_tops = (
        canonical_tops
        if canonical_tops is not None
        else _general_frame_tops(height, width, n_frames, sample_index)
    )
    if len(frame_tops) != n_frames:
        raise ValueError("frame layout does not realize the requested n_frames")

    grid = full_grid(height, width, 0)
    for top, left in frame_tops:
        if not (0 <= top <= height - 7 and 0 <= left <= width - 7):
            raise ValueError("requested dimensions cannot contain the selected frame layout")
        for row, col in _frame_border(top, left):
            grid[row][col] = 7

    # The schedule rotates through the four key meanings. Every frame in a
    # scene receives a distinct key, so local-vs-global control is observable.
    start = sample_index % len(_KEY_COLORS)
    key_colors = [_KEY_COLORS[(start + index) % 4] for index in range(n_frames)]
    key_rng = ctx.draw_rng("key_positions")
    for (top, left), key_color in zip(frame_tops, key_colors):
        legal = [(row, col) for row, col in _frame_interior(top, left) if grid[row][col] == 0]
        if not legal:
            raise ValueError("frame overlap leaves no legal key position")
        key_rng.shuffle(legal)
        row, col = legal[0]
        grid[row][col] = key_color

    if canonical_shape is not None:
        shape = canonical_shape
    else:
        options = _SHAPES_BY_SIZE[template_cells]
        shape = _normalize(options[sample_index % len(options)])
        # S/Z tetromino has only two rotations and is retained only as a
        # canonical archival morphology; ordinary draws use four-way shapes.
        if len({_rotate(shape, turns) for turns in range(4)}) != 4:
            shape = _normalize(options[0])
    _place_template(grid, shape, frame_tops, ctx.draw_rng("template_position"))

    errors = self_check(grid)
    if errors:
        raise ValueError("constructed invalid local-key scene: " + "; ".join(errors))
    return grid
