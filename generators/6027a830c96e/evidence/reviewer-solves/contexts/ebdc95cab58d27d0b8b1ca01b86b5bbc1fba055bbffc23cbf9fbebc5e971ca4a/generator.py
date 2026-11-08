"""Input generator for ARC task 6027a830c96e, Select Panel by Border.

A zero-background scene contains two or three disjoint monochrome rectangular
frames.  One isolated external selector cell has the color of exactly one frame;
the selected Racket rule returns that frame's *full strict interior*, preserving
interior zeros and discarding every frame border, distractor frame, and selector.

The generator deliberately schedules examples that defeat four tempting
shortcuts: always choose the leftmost, rightmost, or largest frame, or tightly
crop the selected interior's nonzero content.  Outputs are still derived by the
canonical Racket authority; ``rule_mirror`` exists only for focused semantic
checks.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "6027a830c96e"
TASK_ID = GENERATOR_ID
RULE_HASH = "ca56dbdca539"
VERSION = "4.0.0"
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 5
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 10..12 by 14..17 zero-background grid contains two or three exact, "
    "disjoint rectangular frames with distinct border colors and nonempty "
    "interiors. Exactly one isolated nonzero cell lies outside all frame "
    "bounding boxes. Its color uniquely selects a frame; output is the full "
    "strict interior of that frame, including any blank rows or columns."
)

INVARIANTS = [
    "two or three exact 4-connected monochrome rectangular frame perimeters",
    "frame colors are distinct and every frame interior is nonempty",
    "exactly one external selector cell matches exactly one frame color",
    "the selector is disconnected from every frame component",
    "the selected frame is not position-, size-, or tight-content-identifiable",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "five-profile canonical schedule",
        "valid": "10..12",
    },
    "grid_w": {
        "type": "int",
        "default": "five-profile canonical schedule",
        "valid": "14..17",
    },
    "n_frames": {
        "type": "int",
        "default": "two or three by schedule",
        "valid": "2..3",
    },
    "selector": {
        "type": "int",
        "default": "uniform nonzero ARC color",
        "valid": "1..9",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_AXIS_RANGES = {
    "grid_h": (10, 12),
    "grid_w": (14, 17),
    "n_frames": (2, 3),
    "selector": (1, 9),
}

# name, height, width, total palette size (including zero), frame count,
# selected left-to-right frame index, selected frame (height, width).
_PROFILE_SPECS = (
    ("canonical_10x14_p6_middle", 10, 14, 6, 3, 1, (5, 4)),
    ("canonical_11x15_p6_left", 11, 15, 6, 2, 0, (5, 5)),
    ("canonical_10x17_p7_right", 10, 17, 7, 3, 2, (4, 5)),
    ("canonical_12x15_p5_right", 12, 15, 5, 2, 1, (5, 5)),
    ("canonical_12x17_p7_middle", 12, 17, 7, 3, 1, (6, 5)),
)
SCHEDULE_PROFILES = tuple(spec[0] for spec in _PROFILE_SPECS)


def _validate_call(
    seed: Any,
    sample_index: Any,
    difficulty: Any,
    overrides: dict[str, Any],
) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        lo, hi = _AXIS_RANGES[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside declared range {lo}..{hi}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the five-step semantic/canonical profile schedule."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _profile_spec(sample_index: int) -> tuple[str, int, int, int, int, int, tuple[int, int]]:
    return _PROFILE_SPECS[sample_index % LESSON_SCHEDULE_PERIOD]


def _draw_scheduled_int(
    ctx,
    overrides: dict[str, Any],
    name: str,
    scheduled: int,
) -> int:
    lo, hi = _AXIS_RANGES[name]
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, scheduled, scheduled)


def _selected_index(profile_index: int, scheduled_index: int, n_frames: int) -> int:
    if n_frames == 3:
        if scheduled_index == 0:
            return 0
        if scheduled_index >= 2:
            return 2
        return 1
    # Preserve left/right variation when a three-frame profile is overridden
    # down to two frames.
    if scheduled_index == 0:
        return 0
    if scheduled_index >= 2:
        return 1
    return profile_index % 2


def _horizontal_slots(width: int, count: int) -> list[tuple[int, int]]:
    """Partition the canvas into count slots separated by one blank column."""
    usable = width - (count - 1)
    base, remainder = divmod(usable, count)
    widths = [base + (1 if index < remainder else 0) for index in range(count)]
    slots: list[tuple[int, int]] = []
    left = 0
    for slot_width in widths:
        slots.append((left, slot_width))
        left += slot_width + 1
    if any(slot_width < 4 for _left, slot_width in slots):
        raise ValueError(f"grid width {width} cannot fit {count} four-column frames")
    return slots


def _frame_geometry(
    ctx,
    *,
    height: int,
    width: int,
    n_frames: int,
    selected_index: int,
    selected_shape: tuple[int, int],
) -> list[tuple[int, int, int, int]]:
    slots = _horizontal_slots(width, n_frames)
    largest_index = next(index for index in range(n_frames) if index != selected_index)
    result: list[tuple[int, int, int, int]] = []
    for index, (slot_left, slot_width) in enumerate(slots):
        max_height = min(7, height - 2)
        max_width = min(7, slot_width)
        if index == largest_index:
            frame_h, frame_w = max_height, max_width
        elif index == selected_index:
            frame_h = min(max(selected_shape[0], 4), max_height - 1)
            frame_w = min(max(selected_shape[1], 4), max_width)
            # If width cannot distinguish the selected frame, height does.
            if frame_h >= max_height and frame_w >= max_width:
                frame_h = max(4, max_height - 1)
        else:
            frame_h = min(max_height - 1, 5 + (index % 2))
            frame_w = min(max_width, 4 + ((index + 1) % 2))
        if frame_h < 4 or frame_w < 4:
            raise ValueError("frame geometry fell below a 4x4 rectangle")
        position_rng = ctx.draw_rng(f"frame_{index}_position")
        top = position_rng.randint(2, height - frame_h)
        left = slot_left + position_rng.randint(0, slot_width - frame_w)
        result.append((top, left, top + frame_h - 1, left + frame_w - 1))

    selected = result[selected_index]
    selected_area = (selected[2] - selected[0] + 1) * (selected[3] - selected[1] + 1)
    largest_area = max(
        (bottom - top + 1) * (right - left + 1)
        for top, left, bottom, right in result
    )
    if selected_area >= largest_area:
        raise AssertionError("scheduled selected frame must be strictly smaller than a distractor")
    return result


def _checkerboard_safe_cells(bbox: tuple[int, int, int, int]) -> list[tuple[int, int]]:
    """Interior cells excluding bottom/right margins; same parity is non-adjacent."""
    top, left, bottom, right = bbox
    candidates = [
        (row, col)
        for row in range(top + 1, bottom - 1)
        for col in range(left + 1, right - 1)
        if (row + col) % 2 == 0
    ]
    if not candidates:
        candidates = [(top + 1, left + 1)]
    return candidates


def _put_content(
    grid: list[list[int]],
    frames: list[dict[str, Any]],
    extras: list[int],
    *,
    difficulty: str,
    ctx,
) -> None:
    cells_by_frame = [_checkerboard_safe_cells(frame["bbox"]) for frame in frames]
    used: set[tuple[int, int]] = set()

    # Every frame is visibly nonempty.
    for index, cells in enumerate(cells_by_frame):
        row, col = cells[0]
        grid[row][col] = extras[index % len(extras)]
        used.add((row, col))

    # Every advertised palette color appears in pixels.
    all_cells = [cell for cells in cells_by_frame for cell in cells if cell not in used]
    for color in extras:
        if color in {grid[row][col] for row, col in used}:
            continue
        if not all_cells:
            raise AssertionError("insufficient interior capacity for the scheduled palette")
        row, col = all_cells.pop(0)
        grid[row][col] = color
        used.add((row, col))

    desired_per_frame = {"easy": 1, "medium": 3, "hard": 5}[difficulty]
    for index, cells in enumerate(cells_by_frame):
        free = [cell for cell in cells if cell not in used]
        rng = ctx.draw_rng(f"frame_{index}_content")
        rng.shuffle(free)
        already = sum(cell in used for cell in cells)
        for row, col in free[: max(0, min(desired_per_frame, len(cells)) - already)]:
            grid[row][col] = rng.choice(extras)
            used.add((row, col))


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    """Return one deterministic lawful input; Racket remains output authority."""
    _validate_call(seed, sample_index, difficulty, overrides)
    band = "medium" if difficulty is None else difficulty
    profile_index = sample_index % LESSON_SCHEDULE_PERIOD
    _name, default_h, default_w, palette_size, default_frames, default_selected, selected_shape = (
        _profile_spec(sample_index)
    )
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_scheduled_int(ctx, overrides, "grid_h", default_h)
    width = _draw_scheduled_int(ctx, overrides, "grid_w", default_w)
    n_frames = _draw_scheduled_int(ctx, overrides, "n_frames", default_frames)
    selector = ctx.draw_color_strict("selector", exclude={0})
    selected_index = _selected_index(profile_index, default_selected, n_frames)

    frame_colors: list[int | None] = [None] * n_frames
    frame_colors[selected_index] = selector
    remaining_colors = [color for color in range(1, 10) if color != selector]
    other_colors = ctx.draw_rng("frame_colors").sample(remaining_colors, n_frames - 1)
    other_iter = iter(other_colors)
    for index in range(n_frames):
        if frame_colors[index] is None:
            frame_colors[index] = next(other_iter)
    colors = [int(color) for color in frame_colors]

    extra_count = palette_size - 1 - n_frames
    if extra_count < 1:
        raise AssertionError("scheduled palette must leave at least one interior color")
    extra_pool = [color for color in range(1, 10) if color not in colors]
    extras = ctx.draw_rng("interior_palette").sample(extra_pool, extra_count)

    bboxes = _frame_geometry(
        ctx,
        height=height,
        width=width,
        n_frames=n_frames,
        selected_index=selected_index,
        selected_shape=selected_shape,
    )
    grid = full_grid(height, width, 0)
    frames: list[dict[str, Any]] = []
    for color, bbox in zip(colors, bboxes):
        top, left, bottom, right = bbox
        draw_frame(grid, top, left, bottom, right, color)
        frames.append({"color": color, "bbox": bbox})
    _put_content(grid, frames, extras, difficulty=band, ctx=ctx)

    selector_col = ctx.draw_rng("selector_position").randint(0, width - 1)
    grid[0][selector_col] = selector

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": overrides},
    )
    if errors:
        raise AssertionError("constructed invalid selector-frame input: " + "; ".join(errors))
    return grid


def _valid_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid cells must be integer ARC colors 0..9 (not bool)"]
    return []


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            todo = [(row, col)]
            cells: set[tuple[int, int]] = set()
            while todo:
                r, c = todo.pop()
                if not (0 <= r < height and 0 <= c < width):
                    continue
                if (r, c) in seen or grid[r][c] != color:
                    continue
                seen.add((r, c))
                cells.add((r, c))
                todo.extend(((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)))
            rows = [r for r, _c in cells]
            cols = [c for _r, c in cells]
            result.append({
                "color": color,
                "cells": cells,
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
            })
    return result


def _perimeter(bbox: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    top, left, bottom, right = bbox
    return {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if row in (top, bottom) or col in (left, right)
    }


def _visual_frames(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Recover rectangular panels, allowing extra same-color interior cells.

    The Racket authority treats only an *exact* border component as a frame.
    One canonical example nevertheless contains an impure non-selected panel.
    We therefore retain both facts: visual panel geometry for the task grammar,
    and ``exact`` component purity for determining whether the selector names a
    frame that the Racket rule can actually choose.
    """
    frames: list[dict[str, Any]] = []
    for component in _components(grid):
        top, left, bottom, right = component["bbox"]
        if bottom - top + 1 < 3 or right - left + 1 < 3:
            continue
        perimeter = _perimeter(component["bbox"])
        if all(grid[row][col] == component["color"] for row, col in perimeter):
            frame = dict(component)
            frame["exact"] = component["cells"] == perimeter
            frames.append(frame)
    return sorted(frames, key=lambda frame: (frame["bbox"][1], frame["bbox"][0]))


def _interior(grid: list[list[int]], frame: dict[str, Any]) -> list[list[int]]:
    top, left, bottom, right = frame["bbox"]
    return [list(row[left + 1:right]) for row in grid[top + 1:bottom]]


def _bbox_cells(frame: dict[str, Any]) -> set[tuple[int, int]]:
    top, left, bottom, right = frame["bbox"]
    return {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
    }


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _valid_grid(grid)
    result: dict[str, Any] = {"errors": errors}
    if errors:
        return result
    height, width = len(grid), len(grid[0])
    if not _AXIS_RANGES["grid_h"][0] <= height <= _AXIS_RANGES["grid_h"][1]:
        errors.append(f"grid height must be 10..12, got {height}")
    if not _AXIS_RANGES["grid_w"][0] <= width <= _AXIS_RANGES["grid_w"][1]:
        errors.append(f"grid width must be 14..17, got {width}")

    frames = _visual_frames(grid)
    if not 2 <= len(frames) <= 3:
        errors.append(f"expected 2-3 rectangular frame panels, found {len(frames)}")
        return result
    colors = [int(frame["color"]) for frame in frames]
    if len(set(colors)) != len(colors):
        errors.append("frame colors must be distinct")

    visual_cells: set[tuple[int, int]] = set()
    for index, frame in enumerate(frames):
        top, left, bottom, right = frame["bbox"]
        if bottom - top + 1 < 4 or right - left + 1 < 4:
            errors.append(f"frame {index} must be at least 4x4")
        bbox_cells = _bbox_cells(frame)
        if visual_cells & bbox_cells:
            errors.append("frame bounding boxes must be disjoint")
        visual_cells.update(bbox_cells)
        interior = _interior(grid, frame)
        if not any(value != 0 for row in interior for value in row):
            errors.append(f"frame {index} interior must be nonempty")

    # At the conceptual task level there is exactly one nonzero cell outside
    # every visible panel.  This remains true for the canonical example whose
    # non-selected panel is impure as a connected component.
    external = [
        (row, col, value)
        for row, line in enumerate(grid)
        for col, value in enumerate(line)
        if value != 0 and (row, col) not in visual_cells
    ]
    if len(external) != 1:
        errors.append(f"expected exactly one external selector cell, found {len(external)}")
        return result
    selector_cell = external[0]
    selector = int(selector_cell[2])
    matching = [index for index, frame in enumerate(frames) if frame["color"] == selector]
    if len(matching) != 1:
        errors.append(
            f"selector color {selector} must match exactly one frame, found {len(matching)}"
        )
        return result
    selected_index = matching[0]
    selected = frames[selected_index]
    if not selected["exact"]:
        errors.append(
            "selected frame is not an exact monochrome perimeter component; "
            "same-color interior cells merged into its border"
        )
        return result

    # Mirror the authority's selector lookup.  It computes frame bboxes from
    # exact components only, then takes the first row-major nonzero cell outside
    # those bboxes.  Impure distractor panels are therefore harmless only when
    # the true external selector appears first, as in the canonical example.
    exact_bbox_cells: set[tuple[int, int]] = set()
    for frame in frames:
        if frame["exact"]:
            exact_bbox_cells.update(_bbox_cells(frame))
    racket_external = [
        (row, col, value)
        for row, line in enumerate(grid)
        for col, value in enumerate(line)
        if value != 0 and (row, col) not in exact_bbox_cells
    ]
    if not racket_external or racket_external[0] != selector_cell:
        errors.append(
            "the external selector is not the first nonzero cell outside exact frame bboxes"
        )
        return result

    output = _interior(grid, selected)
    palette_size = len({value for row in grid for value in row})
    if not 5 <= palette_size <= 7:
        errors.append(f"palette size must be 5..7, got {palette_size}")

    areas = [
        (frame["bbox"][2] - frame["bbox"][0] + 1)
        * (frame["bbox"][3] - frame["bbox"][1] + 1)
        for frame in frames
    ]
    result.update({
        "grid_h": height,
        "grid_w": width,
        "n_frames": len(frames),
        "selector": selector,
        "selector_cell": selector_cell[:2],
        "frames": frames,
        "selected_index": selected_index,
        "selected": selected,
        "selected_area": areas[selected_index],
        "largest_area": max(areas),
        "output": output,
        "palette_size": palette_size,
    })
    return result


def observe_overrides(grid: Any) -> dict[str, int]:
    """Recover every declared exact axis from returned pixels."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid selector-frame input: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": int(analysis["grid_h"]),
        "grid_w": int(analysis["grid_w"]),
        "n_frames": int(analysis["n_frames"]),
        "selector": int(analysis["selector"]),
    }


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Validate the exact component grammar used by the Racket frame predicate."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update(nested)
        for name in AXES:
            if name in meta:
                requested[name] = meta[name]
    if not errors and requested:
        observed = observe_overrides(grid)
        for name, value in requested.items():
            if name in AXES and value is not None and observed.get(name) != value:
                errors.append(
                    f"override {name} requested {value!r}, observed {observed.get(name)!r}"
                )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """The generated grammar contains every canonical input and no invalid frame."""
    return self_check(grid)


def rule_mirror(grid: Any) -> list[list[int]]:
    """Independent Python mirror for semantic tests; Racket remains authoritative."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid selector-frame input: " + "; ".join(analysis["errors"]))
    return [list(row) for row in analysis["output"]]


def _crop_nonzero(grid: list[list[int]]) -> list[list[int]]:
    cells = [
        (row, col)
        for row, line in enumerate(grid)
        for col, value in enumerate(line)
        if value != 0
    ]
    if not cells:
        return []
    top = min(row for row, _col in cells)
    left = min(col for _row, col in cells)
    bottom = max(row for row, _col in cells)
    right = max(col for _row, col in cells)
    return [list(row[left:right + 1]) for row in grid[top:bottom + 1]]


def _rival_frame_by_index(grid: Any, index_fn: Callable[[dict[str, Any]], int]) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid selector-frame input: " + "; ".join(analysis["errors"]))
    frame = analysis["frames"][index_fn(analysis)]
    return _interior(grid, frame)


def _rival_always_leftmost(grid: Any) -> list[list[int]]:
    return _rival_frame_by_index(grid, lambda _analysis: 0)


def _rival_always_rightmost(grid: Any) -> list[list[int]]:
    return _rival_frame_by_index(grid, lambda analysis: len(analysis["frames"]) - 1)


def _rival_always_largest(grid: Any) -> list[list[int]]:
    def choose(analysis: dict[str, Any]) -> int:
        areas = [
            (frame["bbox"][2] - frame["bbox"][0] + 1)
            * (frame["bbox"][3] - frame["bbox"][1] + 1)
            for frame in analysis["frames"]
        ]
        return max(range(len(areas)), key=lambda index: (areas[index], -index))

    return _rival_frame_by_index(grid, choose)


def _rival_tight_crop_selected(grid: Any) -> list[list[int]]:
    return _crop_nonzero(rule_mirror(grid))


def _analysis_ok(grid: Any) -> dict[str, Any] | None:
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis


def _w_selected_not_leftmost(grid: Any) -> bool:
    analysis = _analysis_ok(grid)
    return bool(analysis and analysis["selected_index"] > 0)


def _w_selected_not_rightmost(grid: Any) -> bool:
    analysis = _analysis_ok(grid)
    return bool(
        analysis
        and analysis["selected_index"] < len(analysis["frames"]) - 1
    )


def _w_selected_not_largest(grid: Any) -> bool:
    analysis = _analysis_ok(grid)
    return bool(analysis and analysis["selected_area"] < analysis["largest_area"])


def _w_full_interior_extent(grid: Any) -> bool:
    analysis = _analysis_ok(grid)
    return bool(analysis and _crop_nonzero(analysis["output"]) != analysis["output"])


SEMANTIC_RIVALS = {
    "always_leftmost": _rival_always_leftmost,
    "always_rightmost": _rival_always_rightmost,
    "always_largest": _rival_always_largest,
    "tight_crop_selected": _rival_tight_crop_selected,
}

SEMANTIC_WITNESSES = {
    "selected_not_leftmost": _w_selected_not_leftmost,
    "selected_not_rightmost": _w_selected_not_rightmost,
    "selected_not_largest": _w_selected_not_largest,
    "full_interior_extent": _w_full_interior_extent,
}

WITNESS_RIVALS = {
    "selected_not_leftmost": ["always_leftmost"],
    "selected_not_rightmost": ["always_rightmost"],
    "selected_not_largest": ["always_largest"],
    "full_interior_extent": ["tight_crop_selected"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require demonstrations to refute all declared shortcut selectors/crops."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    errors: list[str] = []
    refuted = {name: False for name in LESSON_COMPETITORS}
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demo {index} is missing input/output")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except ValueError as exc:
            errors.append(f"demo {index} input is malformed: {exc}")
            continue
        if pair["output"] != expected:
            errors.append(f"demo {index} output disagrees with the selector-frame rule")
            continue
        for name, rival in LESSON_COMPETITORS.items():
            if rival(pair["input"]) != expected:
                refuted[name] = True
    for name, is_refuted in refuted.items():
        if not is_refuted:
            errors.append(f"demonstrations do not refute rival {name!r}")

    if not isinstance(query, dict) or "input" not in query:
        errors.append("query is missing its input")
    else:
        try:
            expected_query = rule_mirror(query["input"])
            if "output" in query and query["output"] != expected_query:
                errors.append("query output disagrees with the selector-frame rule")
        except ValueError as exc:
            errors.append(f"query input is malformed: {exc}")
    return errors
