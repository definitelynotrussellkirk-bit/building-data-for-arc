"""Reviewed generator for arbitrary-colour seeded rectangular frames.

Each input contains one to three separate monochrome rectangular outlines.  A
frame has exactly one differently coloured interior seed and at least three
background cells left to transform.  The canonical rule is colour-blind: for
every frame, fill its whole interior with that frame's seed colour while leaving
all borders and exterior background unchanged.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "cb3541dd8827"
TASK_ID = GENERATOR_ID
RULE_HASH = "6f461f08806c"
VERSION = "2.0.0"
SUMMARY = (
    "One to three separate arbitrary-colour rectangular frames each contain "
    "one differently coloured seed; fill each entire interior with its own "
    "seed colour."
)

INVARIANTS = [
    "background is color 0",
    "every non-background rectangular outline is at least 4x4",
    "frames are separated by at least one background row or column",
    "each frame interior has exactly one seed cell of a color different from its border",
    "each frame retains at least three background interior cells, so every output changes",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchors plus banded broad shapes",
        "valid": "7..20",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchors plus banded broad shapes",
        "valid": "9..22",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Four consecutive demonstrations traverse every scheduled branch.  Three of
# those branches contain multiple frames with different seeds, so every normal
# four-demo lesson refutes one-global-colour and one-frame-only shortcuts.
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (
    "canonical_single",
    "canonical_double",
    "broad_double",
    "broad_multi",
)
MIN_STRICT_FRAC = 1.0

_AXIS_LIMITS = {
    "grid_h": (7, 20),
    "grid_w": (9, 22),
}
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be an integer, not {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = _AXIS_LIMITS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _broad_shape(ctx, profile: str, difficulty: Any) -> tuple[int, int]:
    if profile == "broad_multi":
        ranges = {
            "easy": (range(9, 14), range(9, 17)),
            "medium": (range(10, 18), range(11, 21)),
            "hard": (range(12, 21), range(13, 23)),
            None: (range(9, 21), range(9, 23)),
        }
    else:
        ranges = {
            "easy": (range(8, 13), range(10, 16)),
            "medium": (range(9, 17), range(11, 20)),
            "hard": (range(10, 21), range(12, 23)),
            None: (range(7, 21), range(9, 23)),
        }
    heights, widths = ranges[difficulty]
    rng = ctx.draw_rng(f"{profile}_shape")
    return rng.choice(tuple(heights)), rng.choice(tuple(widths))


def _default_shape(ctx, profile: str, difficulty: Any) -> tuple[int, int]:
    if profile == "canonical_single":
        return 7, 9
    if profile == "canonical_double":
        return 11, 9
    return _broad_shape(ctx, profile, difficulty)


def _draw_exact_or_default(ctx, overrides: dict[str, Any], name: str, default: int) -> int:
    lo, hi = _AXIS_LIMITS[name]
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    # The default is scheduled before the public axis draw. A singleton keyed
    # choice records exact provenance; exact overrides still use the complete
    # declared range above, matching the retained passing-generator pattern.
    return ctx.draw_choice(name, (default,))


def _two_slots(height: int, width: int, rng) -> list[tuple[int, int, int, int]]:
    orientations: list[str] = []
    if width >= 9:
        orientations.append("columns")
    if height >= 9:
        orientations.append("rows")
    if not orientations:
        raise ValueError(f"canvas {height}x{width} cannot fit two separated 4x4 frames")
    orientation = rng.choice(orientations)
    if orientation == "columns":
        left_w = (width - 1) // 2
        right_w = width - 1 - left_w
        return [(0, 0, height, left_w), (0, left_w + 1, height, right_w)]
    top_h = (height - 1) // 2
    bottom_h = height - 1 - top_h
    return [(0, 0, top_h, width), (top_h + 1, 0, bottom_h, width)]


def _three_slots(height: int, width: int, rng) -> list[tuple[int, int, int, int]]:
    if height < 9 or width < 9:
        return _two_slots(height, width, rng)
    top_h = (height - 1) // 2
    bottom_h = height - 1 - top_h
    left_w = (width - 1) // 2
    right_w = width - 1 - left_w
    slots = [
        (0, 0, top_h, left_w),
        (0, left_w + 1, top_h, right_w),
        (top_h + 1, 0, bottom_h, left_w),
        (top_h + 1, left_w + 1, bottom_h, right_w),
    ]
    rng.shuffle(slots)
    return slots[:3]


def _slots(height: int, width: int, n_frames: int, rng) -> list[tuple[int, int, int, int]]:
    if n_frames == 1:
        return [(0, 0, height, width)]
    if n_frames == 2:
        return _two_slots(height, width, rng)
    return _three_slots(height, width, rng)


def _place_frame(
    grid: list[list[int]],
    slot: tuple[int, int, int, int],
    *,
    frame_color: int,
    seed_color: int,
    rng,
    leave_exterior: bool,
) -> None:
    slot_r, slot_c, slot_h, slot_w = slot
    max_h = slot_h - 1 if leave_exterior and slot_h > 4 else slot_h
    max_w = slot_w - 1 if leave_exterior and slot_w > 4 else slot_w
    if max_h < 4 or max_w < 4:
        raise ValueError(f"slot {slot} cannot fit a 4x4 frame")
    frame_h = rng.randint(4, max_h)
    frame_w = rng.randint(4, max_w)
    top = slot_r + rng.randint(0, slot_h - frame_h)
    left = slot_c + rng.randint(0, slot_w - frame_w)
    bottom = top + frame_h - 1
    right = left + frame_w - 1
    draw_frame(grid, top, left, bottom, right, frame_color)
    interior = [
        (row, col)
        for row in range(top + 1, bottom)
        for col in range(left + 1, right)
    ]
    if len(interior) < 4:
        raise RuntimeError("frame interior is too small for a nontrivial seeded fill")
    row, col = rng.choice(interior)
    grid[row][col] = seed_color


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
    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_w = _default_shape(ctx, profile, difficulty)
    height = _draw_exact_or_default(ctx, overrides, "grid_h", default_h)
    width = _draw_exact_or_default(ctx, overrides, "grid_w", default_w)

    requested_frames = {
        "canonical_single": 1,
        "canonical_double": 2,
        "broad_double": 2,
        "broad_multi": 3,
    }[profile]
    n_frames = 3 if requested_frames == 3 and height >= 9 and width >= 9 else min(requested_frames, 2)

    slot_rng = ctx.draw_rng("frame_slots")
    slots = _slots(height, width, n_frames, slot_rng)
    color_rng = ctx.draw_rng("frame_colors")
    colors = color_rng.sample(tuple(range(1, 10)), 2 * n_frames)
    frame_colors = colors[:n_frames]
    seed_colors = colors[n_frames:]

    grid = full_grid(height, width, 0)
    geometry_rng = ctx.draw_rng("frame_geometry")
    for slot, frame_color, seed_color in zip(slots, frame_colors, seed_colors):
        _place_frame(
            grid,
            slot,
            frame_color=frame_color,
            seed_color=seed_color,
            rng=geometry_rng,
            leave_exterior=n_frames == 1,
        )
    return grid


def _grid_rows(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None, ["ragged grid"]
    rows = [list(row) for row in grid]
    if any(type(value) is not int or not 0 <= value <= 9 for row in rows for value in row):
        return None, ["input cells must be integer ARC colors 0..9"]
    return rows, []


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for start_r in range(height):
        for start_c in range(width):
            color = grid[start_r][start_c]
            if color == 0 or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells: set[tuple[int, int]] = set()
            while stack:
                row, col = stack.pop()
                cells.add((row, col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append({"color": color, "cells": cells})
    return result


def _frame_components(grid: list[list[int]]) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    for component in _components(grid):
        cells = component["cells"]
        r1 = min(row for row, _ in cells)
        r2 = max(row for row, _ in cells)
        c1 = min(col for _, col in cells)
        c2 = max(col for _, col in cells)
        if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
            continue
        border = (
            {(r1, col) for col in range(c1, c2 + 1)}
            | {(r2, col) for col in range(c1, c2 + 1)}
            | {(row, c1) for row in range(r1, r2 + 1)}
            | {(row, c2) for row in range(r1, r2 + 1)}
        )
        if cells == border:
            frames.append(
                {
                    "r1": r1,
                    "c1": c1,
                    "r2": r2,
                    "c2": c2,
                    "frame_color": component["color"],
                    "border": border,
                }
            )
    return sorted(frames, key=lambda frame: (frame["r1"], frame["c1"], frame["frame_color"]))


def _separated(first: dict[str, Any], second: dict[str, Any]) -> bool:
    return (
        first["r2"] + 1 < second["r1"]
        or second["r2"] + 1 < first["r1"]
        or first["c2"] + 1 < second["c1"]
        or second["c2"] + 1 < first["c1"]
    )


def _analyze(grid: Any) -> tuple[list[str], list[dict[str, Any]], dict[str, Any] | None]:
    rows, errors = _grid_rows(grid)
    if rows is None:
        return errors, [], None
    height, width = len(rows), len(rows[0])
    if not 7 <= height <= 20:
        errors.append(f"grid height {height} outside 7..20")
    if not 9 <= width <= 22:
        errors.append(f"grid width {width} outside 9..22")

    frames = _frame_components(rows)
    if not 1 <= len(frames) <= 3:
        errors.append(f"expected one to three rectangular frames, found {len(frames)}")
    for frame in frames:
        if frame["r2"] - frame["r1"] + 1 < 4 or frame["c2"] - frame["c1"] + 1 < 4:
            errors.append(
                f"frame at {(frame['r1'], frame['c1'])} must be at least 4x4"
            )
    for index, first in enumerate(frames):
        for second in frames[index + 1 :]:
            if not _separated(first, second):
                errors.append(
                    f"frames at {(first['r1'], first['c1'])} and "
                    f"{(second['r1'], second['c1'])} touch or overlap"
                )

    enriched: list[dict[str, Any]] = []
    for frame in frames:
        interior = [
            (row, col)
            for row in range(frame["r1"] + 1, frame["r2"])
            for col in range(frame["c1"] + 1, frame["c2"])
        ]
        if any(rows[row][col] == frame["frame_color"] for row, col in interior):
            errors.append(
                f"frame at {(frame['r1'], frame['c1'])} contains border-colored interior cells"
            )
        seeds = [
            (row, col)
            for row, col in interior
            if rows[row][col] not in (0, frame["frame_color"])
        ]
        seed_colors = {rows[row][col] for row, col in seeds}
        zeros = sum(rows[row][col] == 0 for row, col in interior)
        if len(seeds) != 1 or len(seed_colors) != 1:
            errors.append(
                f"frame at {(frame['r1'], frame['c1'])} must contain exactly one seed cell"
            )
        if zeros < 3:
            errors.append(
                f"frame at {(frame['r1'], frame['c1'])} has fewer than three fill targets"
            )
        enriched.append(
            dict(
                frame,
                seed_cells=seeds,
                seed_color=next(iter(seed_colors)) if len(seed_colors) == 1 else None,
            )
        )

    border_cells = set().union(*(frame["border"] for frame in frames)) if frames else set()
    for row, line in enumerate(rows):
        for col, value in enumerate(line):
            if value == 0 or (row, col) in border_cells:
                continue
            owners = [
                frame
                for frame in enriched
                if frame["r1"] < row < frame["r2"] and frame["c1"] < col < frame["c2"]
            ]
            if len(owners) != 1:
                errors.append(f"non-frame color at {(row, col)} is not inside exactly one frame")
            elif owners[0]["seed_color"] != value:
                errors.append(f"interior color at {(row, col)} does not match its frame seed")

    facts = {
        "grid_h": height,
        "grid_w": width,
        "n_frames": len(frames),
        "palette_size": len({value for row in rows for value in row}),
    }
    return errors, enriched, facts


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty
    errors, _, facts = _analyze(grid)
    if errors or facts is None:
        return errors
    if isinstance(meta, dict) and isinstance(meta.get("overrides"), dict):
        for name, expected in meta["overrides"].items():
            if name in AXES and expected is not None and facts.get(name) != expected:
                errors.append(f"override {name}={expected!r} realized as {facts.get(name)!r}")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    errors, _, facts = _analyze(grid)
    if errors or facts is None:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors[:4]))
    return {name: int(facts[name]) for name in AXES}


def _semantic_frames(grid: Any) -> tuple[list[list[int]], list[dict[str, Any]]]:
    rows, errors = _grid_rows(grid)
    if rows is None:
        raise ValueError("invalid grid: " + "; ".join(errors))
    frames = _frame_components(rows)
    enriched: list[dict[str, Any]] = []
    for frame in frames:
        colors = sorted(
            {
                rows[row][col]
                for row in range(frame["r1"] + 1, frame["r2"])
                for col in range(frame["c1"] + 1, frame["c2"])
                if rows[row][col] not in (0, frame["frame_color"])
            }
        )
        enriched.append(dict(frame, seed_colors=colors))
    return rows, enriched


def _apply_variant(
    grid: Any,
    chooser: Callable[[list[dict[str, Any]], int], int | None],
) -> list[list[int]]:
    rows, frames = _semantic_frames(grid)
    out = deepcopy(rows)
    for index, frame in enumerate(frames):
        fill_color = chooser(frames, index)
        if fill_color is None:
            continue
        for row in range(frame["r1"] + 1, frame["r2"]):
            for col in range(frame["c1"] + 1, frame["c2"]):
                out[row][col] = fill_color
    return out


def rule_mirror(grid):
    """Python mirror for tests; the selected Racket rule remains authoritative."""
    return _apply_variant(
        grid,
        lambda frames, index: (
            frames[index]["seed_colors"][0]
            if len(frames[index]["seed_colors"]) == 1
            else None
        ),
    )


def _color_two_frames_only(grid):
    return _apply_variant(
        grid,
        lambda frames, index: (
            frames[index]["seed_colors"][0]
            if frames[index]["frame_color"] == 2
            and len(frames[index]["seed_colors"]) == 1
            else None
        ),
    )


def _single_global_seed(grid):
    _, frames = _semantic_frames(grid)
    global_seed = next(
        (frame["seed_colors"][0] for frame in frames if len(frame["seed_colors"]) == 1),
        None,
    )
    return _apply_variant(grid, lambda _frames, _index: global_seed)


def _first_frame_only(grid):
    return _apply_variant(
        grid,
        lambda frames, index: (
            frames[index]["seed_colors"][0]
            if index == 0 and len(frames[index]["seed_colors"]) == 1
            else None
        ),
    )


def _fill_with_frame_color(grid):
    return _apply_variant(grid, lambda frames, index: frames[index]["frame_color"])


def _valid_frames(grid: Any) -> list[dict[str, Any]]:
    errors, frames, _ = _analyze(grid)
    return [] if errors else frames


def _has_non_two_frame(grid) -> bool:
    return any(frame["frame_color"] != 2 for frame in _valid_frames(grid))


def _has_multiple_seed_colors(grid) -> bool:
    return len({frame["seed_color"] for frame in _valid_frames(grid)}) >= 2


def _has_multiple_frames(grid) -> bool:
    return len(_valid_frames(grid)) >= 2


def _seed_differs_from_frame(grid) -> bool:
    frames = _valid_frames(grid)
    return bool(frames) and all(frame["seed_color"] != frame["frame_color"] for frame in frames)


SEMANTIC_WITNESSES = {
    "non_two_frame": _has_non_two_frame,
    "multiple_seed_colors": _has_multiple_seed_colors,
    "multiple_frames": _has_multiple_frames,
    "seed_differs_from_frame": _seed_differs_from_frame,
}
SEMANTIC_RIVALS = {
    "color_two_frames_only": _color_two_frames_only,
    "single_global_seed": _single_global_seed,
    "first_frame_only": _first_frame_only,
    "fill_with_frame_color": _fill_with_frame_color,
}
WITNESS_RIVALS = {
    "non_two_frame": ["color_two_frames_only"],
    "multiple_seed_colors": ["single_global_seed"],
    "multiple_frames": ["first_frame_only"],
    "seed_differs_from_frame": ["fill_with_frame_color"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    reasons: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                competitor(pair["input"]) == pair["output"]
                for pair in demos
            )
            changes_query = competitor(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"{name} competitor failed to score: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
