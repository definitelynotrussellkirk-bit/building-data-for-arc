"""Generator for frame-local row/column intersections with a fill key.

Each input contains two or three independent hollow color-7 frames.  Within
one frame, color 2 marks active rows on the left inner axis, color 3 marks
active columns on the top inner axis, and one other local color is the fill
key.  The transformation paints every local row/column intersection with that
frame's key color while preserving the input.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "694d3ee0b12a"
VERSION = "3.0.0"
TASK_ID = "694d3ee0b12a"
RULE_HASH = "c13ecc4348dc"
SUMMARY = (
    "A zero-background grid contains two or three separate 7x7 hollow orange "
    "frames. Each frame is an independent workspace: red cells on its left "
    "inner axis select rows, green cells on its top inner axis select columns, "
    "and a local non-marker color inside the frame is that frame's fill key. "
    "Paint every selected-row x selected-column intersection with the local "
    "key color, preserving all existing cells."
)

INVARIANTS = [
    "exactly two or three separate 7x7 hollow color-7 frames",
    "each frame has one to three row markers on its left inner axis",
    "each frame has one to three column markers on its top inner axis",
    "each frame has one unambiguous local fill-key color",
    "all nonzero cells belong to exactly one frame workspace",
]

# Canonical-scale layouts.  A profile supplies (height, width, frame top-lefts).
_LAYOUTS: dict[str, tuple[int, int, tuple[tuple[int, int], ...]]] = {
    "pair_down_right": (16, 18, ((1, 1), (8, 10))),
    "pair_down_left": (15, 17, ((1, 9), (7, 1))),
    "pair_square": (16, 16, ((1, 1), (8, 8))),
    "pair_cross": (17, 18, ((1, 10), (9, 1))),
    "triple_l": (17, 19, ((1, 1), (9, 1), (9, 11))),
    "triple_corner": (18, 19, ((1, 11), (10, 1), (10, 11))),
}
SCHEDULE_PROFILES = tuple(_LAYOUTS)
_PROFILE_SCHEDULES = {
    "easy": (
        "pair_down_right",
        "pair_down_left",
        "pair_square",
        "triple_l",
    ),
    "medium": SCHEDULE_PROFILES,
    "hard": (
        "triple_l",
        "pair_cross",
        "triple_corner",
        "pair_down_right",
        "pair_down_left",
        "pair_square",
    ),
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic canonical-scale schedule",
        "valid": "pair_down_right|pair_down_left|pair_square|pair_cross|triple_l|triple_corner",
    },
}

_FILL_COLORS = (4, 5, 6, 8, 9)
_FRAME_SIZE = 7
EXAMPLES_NEEDED = 2


def _band(difficulty) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in _PROFILE_SCHEDULES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    return difficulty


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    del seed
    schedule = _PROFILE_SCHEDULES[_band(difficulty)]
    return schedule[int(sample_index) % len(schedule)]


def _seven_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 7 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            component: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                component.append((rr, cc))
                for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                    point = rr + dr, cc + dc
                    if (
                        0 <= point[0] < height
                        and 0 <= point[1] < width
                        and point not in seen
                        and grid[point[0]][point[1]] == 7
                    ):
                        seen.add(point)
                        stack.append(point)
            components.append(component)
    return components


def _frame_record(grid: list[list[int]], component: list[tuple[int, int]]) -> dict[str, Any]:
    rows = [row for row, _ in component]
    cols = [col for _, col in component]
    r0, r1 = min(rows), max(rows)
    c0, c1 = min(cols), max(cols)
    border = {
        (row, col)
        for row in range(r0, r1 + 1)
        for col in range(c0, c1 + 1)
        if row in (r0, r1) or col in (c0, c1)
    }
    row_marks = [
        row for row in range(r0 + 1, r1) if grid[row][c0 + 1] == 2
    ]
    col_marks = [
        col for col in range(c0 + 1, c1) if grid[r0 + 1][col] == 3
    ]
    key_cells = [
        (row, col, grid[row][col])
        for row in range(r0 + 1, r1)
        for col in range(c0 + 1, c1)
        if grid[row][col] not in (0, 2, 3, 7)
    ]
    return {
        "bbox": (r0, c0, r1, c1),
        "cells": set(component),
        "border": border,
        "row_marks": row_marks,
        "col_marks": col_marks,
        "key_cells": key_cells,
        "key_colors": {value for _, _, value in key_cells},
    }


def _analysis(grid) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid must be a nonempty list of rows"], "frames": []}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"], "frames": []}
    if any(not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid values must be integer ARC colors 0..9")

    components = _seven_components(grid)
    frames = [_frame_record(grid, component) for component in components]
    frames.sort(key=lambda record: record["bbox"][:2])
    if len(frames) not in (2, 3):
        errors.append(f"expected two or three independent color-7 frames, found {len(frames)}")

    covered: set[tuple[int, int]] = set()
    for index, frame in enumerate(frames):
        r0, c0, r1, c1 = frame["bbox"]
        if (r1 - r0 + 1, c1 - c0 + 1) != (_FRAME_SIZE, _FRAME_SIZE):
            errors.append(f"frame {index} must be exactly 7x7")
        if frame["cells"] != frame["border"]:
            errors.append(f"frame {index} must be a complete hollow rectangular border")
        rectangle = {
            (row, col)
            for row in range(r0, r1 + 1)
            for col in range(c0, c1 + 1)
        }
        if covered & rectangle:
            errors.append(f"frame {index} overlaps another frame workspace")
        covered.update(rectangle)

        if not 1 <= len(frame["row_marks"]) <= 3:
            errors.append(f"frame {index} must have one to three row markers")
        if not 1 <= len(frame["col_marks"]) <= 3:
            errors.append(f"frame {index} must have one to three column markers")
        if len(frame["key_colors"]) != 1:
            errors.append(f"frame {index} must have one unambiguous fill-key color")
        if not frame["key_cells"]:
            errors.append(f"frame {index} must have at least one fill-key cell")

        for row in range(r0 + 1, r1):
            for col in range(c0 + 1, c1):
                value = grid[row][col]
                if value == 2 and col != c0 + 1:
                    errors.append(f"frame {index} has a row marker off its left inner axis")
                if value == 3 and row != r0 + 1:
                    errors.append(f"frame {index} has a column marker off its top inner axis")

    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0 and (row, col) not in covered:
                errors.append("nonzero cell lies outside every frame workspace")
                break
        if errors and errors[-1] == "nonzero cell lies outside every frame workspace":
            break

    return {"errors": errors, "frames": frames}


def self_check(grid, *, seed=None, sample_index=None, difficulty=None, **kwargs) -> list[str]:
    del seed, sample_index, difficulty, kwargs
    return list(_analysis(grid)["errors"])


def observe_overrides(grid) -> dict[str, object]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    signature = (
        len(grid),
        len(grid[0]),
        tuple(frame["bbox"][:2] for frame in analysis["frames"]),
    )
    for profile, (height, width, positions) in _LAYOUTS.items():
        if signature == (height, width, positions):
            return {"scene_profile": profile}
    return {"errors": ["unrecognized scene profile"]}


def strict_canonical_like(grid) -> list[str]:
    """Return reasons when a grid leaves this task's canonical input grammar."""
    return self_check(grid)


def _frame_fill_color(frame: dict[str, Any]) -> int | None:
    if not frame["key_cells"]:
        return None
    counts: dict[int, int] = {}
    first_seen: list[int] = []
    for _, _, value in frame["key_cells"]:
        if value not in counts:
            counts[value] = 0
            first_seen.append(value)
        counts[value] += 1
    return max(first_seen, key=lambda value: counts[value])


def rule_mirror(grid):
    """Pure-Python mirror of the selected frame-local intersection rule."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    output = [row[:] for row in grid]
    for frame in analysis["frames"]:
        fill_color = _frame_fill_color(frame)
        if fill_color is None:
            return None
        for row in frame["row_marks"]:
            for col in frame["col_marks"]:
                output[row][col] = fill_color
    return output


def _rival_fixed_bottom_right_key(grid):
    """Canonical shortcut: every key happens to be at local cell (5, 5)."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    output = [row[:] for row in grid]
    for frame in analysis["frames"]:
        _, _, r1, c1 = frame["bbox"]
        fill_color = grid[r1 - 1][c1 - 1]
        for row in frame["row_marks"]:
            for col in frame["col_marks"]:
                output[row][col] = fill_color
    return output


def _rival_global_first_key(grid):
    """Wrongly reuse the first frame's key color in every frame."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    fill_color = _frame_fill_color(analysis["frames"][0])
    if fill_color is None:
        return None
    output = [row[:] for row in grid]
    for frame in analysis["frames"]:
        for row in frame["row_marks"]:
            for col in frame["col_marks"]:
                output[row][col] = fill_color
    return output


def _rival_first_frame_only(grid):
    """Transform only the first workspace and leave later frames untouched."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    output = [row[:] for row in grid]
    frame = analysis["frames"][0]
    fill_color = _frame_fill_color(frame)
    if fill_color is None:
        return None
    for row in frame["row_marks"]:
        for col in frame["col_marks"]:
            output[row][col] = fill_color
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "fixed_bottom_right_key": _rival_fixed_bottom_right_key,
    "global_first_key": _rival_global_first_key,
    "first_frame_only": _rival_first_frame_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "fixed_bottom_right_key": _rival_fixed_bottom_right_key,
}


def _refutes(rival_name: str):
    def witness(grid) -> bool:
        answer = rule_mirror(grid)
        rival = SEMANTIC_RIVALS[rival_name](grid)
        return answer is not None and rival is not None and answer != rival

    return witness


SEMANTIC_WITNESSES = {
    "key_position_is_not_fixed": _refutes("fixed_bottom_right_key"),
    "keys_are_frame_local": _refutes("global_first_key"),
    "every_frame_is_transformed": _refutes("first_frame_only"),
}
WITNESS_RIVALS = {
    "key_position_is_not_fixed": ["fixed_bottom_right_key"],
    "keys_are_frame_local": ["global_first_key"],
    "every_frame_is_transformed": ["first_frame_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Check that the demonstrations eliminate every declared rival rule."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} is outside the lawful input grammar: {errors[0]}")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output disagrees with the frame-local rule")

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query is outside the lawful input grammar: {query_errors[0]}")
        return reasons
    query_answer = rule_mirror(query["input"])
    if query.get("output") is not None and query["output"] != query_answer:
        reasons.append("query output disagrees with the frame-local rule")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            isinstance(demo, dict)
            and "input" in demo
            and competitor(demo["input"]) == demo.get("output")
            for demo in demos
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons


def _stamp_frame(
    grid: list[list[int]],
    top: int,
    left: int,
    *,
    row_marks: list[int],
    col_marks: list[int],
    key_position: tuple[int, int],
    fill_color: int,
) -> None:
    bottom = top + _FRAME_SIZE - 1
    right = left + _FRAME_SIZE - 1
    for col in range(left, right + 1):
        grid[top][col] = 7
        grid[bottom][col] = 7
    for row in range(top, bottom + 1):
        grid[row][left] = 7
        grid[row][right] = 7
    for local_row in row_marks:
        grid[top + local_row][left + 1] = 2
    for local_col in col_marks:
        grid[top + 1][left + local_col] = 3
    key_row, key_col = key_position
    grid[top + key_row][left + key_col] = fill_color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    default_profile = schedule_profile(seed, sample_index, band)
    profile_options = SCHEDULE_PROFILES if overrides.get("scene_profile") is not None else (default_profile,)
    profile = ctx.draw_choice("scene_profile", profile_options)
    height, width, positions = _LAYOUTS[profile]
    grid = full_grid(height, width, 0)
    rng = ctx.draw_rng("frame_content")
    fill_colors = rng.sample(list(_FILL_COLORS), len(positions))

    for index, ((top, left), fill_color) in enumerate(zip(positions, fill_colors)):
        row_count = rng.randint(1, 3)
        col_count = rng.randint(1, 3)
        row_marks = sorted(rng.sample(range(1, 6), row_count))
        col_marks = sorted(rng.sample(range(1, 6), col_count))
        # The two marker axes share local cell (1, 1); one cell cannot carry
        # both marker colors, so keep at most one axis selected there.
        if 1 in row_marks and 1 in col_marks:
            alternatives = [value for value in range(2, 6) if value not in col_marks]
            if alternatives:
                col_marks[col_marks.index(1)] = rng.choice(alternatives)
                col_marks.sort()
            else:
                row_marks[row_marks.index(1)] = rng.choice(
                    [value for value in range(2, 6) if value not in row_marks]
                )
                row_marks.sort()
        key_candidates = [
            (row, col)
            for row in range(2, 6)
            for col in range(2, 6)
        ]
        # The first frame always moves the key away from the canonical fixed
        # bottom-right location; other frames retain a mix of positions.
        if index == 0:
            key_candidates.remove((5, 5))
        # Keep at least one intersection genuinely changed in every frame so
        # an "only transform the first frame" shortcut is always observable.
        intersections = {(row, col) for row in row_marks for col in col_marks}
        if len(intersections) == 1:
            key_candidates = [point for point in key_candidates if point not in intersections]
        key_position = rng.choice(key_candidates)
        _stamp_frame(
            grid,
            top,
            left,
            row_marks=row_marks,
            col_marks=col_marks,
            key_position=key_position,
            fill_color=fill_color,
        )

    errors = self_check(grid)
    if errors:
        raise ValueError(f"internal generator contract violation: {errors}")
    return [row[:] for row in grid]


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Deterministic near-miss inputs used by the mutation-sensitivity gate."""
    base = generate(2026, 0, difficulty="medium", scene_profile="pair_down_right")
    analysis = _analysis(base)
    frames = analysis["frames"]

    blank = full_grid(len(base), len(base[0]), 0)

    one_frame = [row[:] for row in base]
    r0, c0, r1, c1 = frames[1]["bbox"]
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            one_frame[row][col] = 0

    broken_border = [row[:] for row in base]
    r0, c0, _, _ = frames[0]["bbox"]
    broken_border[r0][c0 + 3] = 0

    off_axis_marker = [row[:] for row in base]
    r0, c0, _, _ = frames[0]["bbox"]
    off_axis_marker[r0 + 3][c0 + 3] = 2

    ambiguous_key = [row[:] for row in base]
    r0, c0, _, _ = frames[0]["bbox"]
    existing = _frame_fill_color(frames[0])
    replacement = next(color for color in _FILL_COLORS if color != existing)
    point = next(
        (row, col)
        for row in range(r0 + 2, r0 + 6)
        for col in range(c0 + 2, c0 + 6)
        if ambiguous_key[row][col] == 0
    )
    ambiguous_key[point[0]][point[1]] = replacement

    stray_nonzero = [row[:] for row in base]
    stray_nonzero[0][0] = 9

    no_row_markers = [row[:] for row in base]
    for frame in frames:
        _, c0, _, _ = frame["bbox"]
        for row in frame["row_marks"]:
            no_row_markers[row][c0 + 1] = 0

    no_col_markers = [row[:] for row in base]
    for frame in frames:
        r0, _, _, _ = frame["bbox"]
        for col in frame["col_marks"]:
            no_col_markers[r0 + 1][col] = 0

    ragged = [row[:] for row in base]
    ragged[-1] = ragged[-1][:-1]

    return [
        ("blank_no_frames", blank),
        ("only_one_frame", one_frame),
        ("broken_frame_border", broken_border),
        ("row_marker_off_axis", off_axis_marker),
        ("ambiguous_fill_key", ambiguous_key),
        ("stray_nonzero_outside_frames", stray_nonzero),
        ("missing_row_markers", no_row_markers),
        ("missing_column_markers", no_col_markers),
        ("ragged_grid", ragged),
    ]
