"""Constructive generator for 961add4a2688, “Column Packing Inside Frame”.

The selected Racket authority finds the unique rectangular color-8 border,
repaints only that border on a zero canvas, and independently packs each
interior column upward while preserving its original top-to-bottom color order.
This generator keeps the authority unchanged and makes the input distribution,
overrides, validation, and teaching contract explicit and observable.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "961add4a2688"
TASK_ID = GENERATOR_ID
RULE_HASH = "9c6db5aba1ba"
VERSION = "2.0.0"
SUMMARY = (
    "A complete color-8 rectangle encloses 6 or 7 colored markers. Each "
    "interior column is packed upward independently, preserving vertical order."
)

INVARIANTS = [
    "one complete color-8 rectangular border of height at least 6 and width at least 6",
    "all nonzero non-8 markers lie strictly inside the frame; outside cells are zero",
    "the selected distribution contains 6 or 7 markers using exactly 4 or 6 marker colors",
    "at least one marker moves upward; stacked and mixed profiles expose order preservation",
]

_PROFILE_TABLE: dict[str, tuple[int, int, int]] = {
    "canonical_8x9_p6": (8, 9, 6),
    "canonical_9x10_p8": (9, 10, 8),
    "canonical_9x11_p8": (9, 11, 8),
    "canonical_10x10_p6": (10, 10, 6),
}
_PROFILE_NAMES = tuple(_PROFILE_TABLE)
_COLUMN_PATTERNS = ("separate", "stacked", "mixed")
_FRAME_POSITIONS = ("top_left", "center", "bottom_right")
_MARKER_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four-slot cyclic canonical-profile schedule",
        "valid": "canonical_8x9_p6|canonical_9x10_p8|canonical_9x11_p8|canonical_10x10_p6",
    },
    "n_markers": {
        "type": "int",
        "default": "schedule cycles 6,6,7,7",
        "valid": "6..7",
    },
    "column_pattern": {
        "type": "str",
        "default": "schedule cycles mixed,separate,stacked,mixed",
        "valid": "separate|stacked|mixed",
    },
    "frame_position": {
        "type": "str",
        "default": "schedule cycles top_left,center,bottom_right,center",
        "valid": "top_left|center|bottom_right",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 4
SCHEDULE_PROFILES = (0, 1, 2, 3)

# Every five-pair lesson (four demonstrations plus one query) contains two
# order-bearing examples even after any one pair is held out as the query.
_SCHEDULE = (
    dict(
        scene_profile="canonical_8x9_p6",
        n_markers=6,
        column_pattern="mixed",
        frame_position="top_left",
    ),
    dict(
        scene_profile="canonical_9x10_p8",
        n_markers=6,
        column_pattern="separate",
        frame_position="center",
    ),
    dict(
        scene_profile="canonical_9x11_p8",
        n_markers=7,
        column_pattern="stacked",
        frame_position="bottom_right",
    ),
    dict(
        scene_profile="canonical_10x10_p6",
        n_markers=7,
        column_pattern="mixed",
        frame_position="center",
    ),
)


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> int:
    """Return the deterministic public curriculum residue."""
    del seed, difficulty
    if type(sample_index) is not int:
        raise ValueError("sample_index must be an integer")
    return sample_index % len(_SCHEDULE)


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    value = overrides.get("n_markers")
    if value is not None and type(value) is not int:
        raise ValueError(f"n_markers must be an integer, not {type(value).__name__}")
    for name, allowed in (
        ("scene_profile", _PROFILE_NAMES),
        ("column_pattern", _COLUMN_PATTERNS),
        ("frame_position", _FRAME_POSITIONS),
    ):
        value = overrides.get(name)
        if value is not None and type(value) is not str:
            raise ValueError(f"{name} must be a string, not {type(value).__name__}")
        if value is not None and value not in allowed:
            raise ValueError(f"{name}={value!r} is not one of {allowed}")


def _frame_size(n_markers: int, pattern: str) -> tuple[int, int]:
    # Four interior rows are enough for two ordered stacks with visible gaps.
    frame_h = 6
    # Separate means exactly one occupied column per marker. Mixed uses two
    # two-cell stacks plus singles, requiring at most five interior columns.
    frame_w = n_markers + 2 if pattern == "separate" else 7
    return frame_h, frame_w


def _frame_origin(
    h: int, w: int, frame_h: int, frame_w: int, position: str
) -> tuple[int, int]:
    if frame_h > h or frame_w > w:
        raise ValueError(
            f"{frame_h}x{frame_w} frame cannot fit in {h}x{w} scene"
        )
    if position == "top_left":
        return 0, 0
    if position == "center":
        return (h - frame_h) // 2, (w - frame_w) // 2
    if position == "bottom_right":
        return h - frame_h, w - frame_w
    raise ValueError(f"unknown frame position: {position!r}")


def _draw_frame(grid: list[list[int]], box: tuple[int, int, int, int]) -> None:
    r0, c0, r1, c1 = box
    for c in range(c0, c1 + 1):
        grid[r0][c] = 8
        grid[r1][c] = 8
    for r in range(r0, r1 + 1):
        grid[r][c0] = 8
        grid[r][c1] = 8


def _placement_positions(
    box: tuple[int, int, int, int],
    n_markers: int,
    pattern: str,
    rng,
) -> list[tuple[int, int]]:
    r0, c0, r1, c1 = box
    rows = list(range(r0 + 1, r1))
    cols = list(range(c0 + 1, c1))
    if len(rows) != 4:
        raise RuntimeError("selected construction expects exactly four interior rows")

    if pattern == "separate":
        chosen_cols = rng.sample(cols, n_markers)
        # Every marker starts below the top interior row, so the transform is
        # visible while every occupied column still contains exactly one cell.
        return [(rng.choice(rows[1:]), c) for c in chosen_cols]

    if pattern == "mixed":
        # Two gapped two-cell stacks (one descending and one ascending after
        # color assignment), followed by singleton columns.
        occupied = rng.sample(cols, n_markers - 2)
        first, second, *singles = occupied
        positions = [
            (rows[0], first),
            (rows[-1], first),
            (rows[0], second),
            (rows[-1], second),
        ]
        positions.extend((rng.choice(rows[1:]), c) for c in singles)
        return positions

    if pattern == "stacked":
        first, second = rng.sample(cols, 2)
        counts = (3, 3) if n_markers == 6 else (4, 3)
        positions: list[tuple[int, int]] = []
        for index, (c, count) in enumerate(zip((first, second), counts)):
            if count == 4:
                selected_rows = rows
            elif index == 0:
                selected_rows = (rows[0], rows[2], rows[3])
            else:
                selected_rows = (rows[0], rows[1], rows[3])
            positions.extend((r, c) for r in selected_rows)
        return positions

    raise ValueError(f"unknown column pattern: {pattern!r}")


def _assign_colors(
    positions: Sequence[tuple[int, int]], palette: Sequence[int], rng
) -> list[int]:
    """Use every palette color and create opposite-order stacks when possible."""
    by_col: dict[int, list[int]] = {}
    for index, (_, c) in enumerate(positions):
        by_col.setdefault(c, []).append(index)
    multi = [indices for _, indices in sorted(by_col.items()) if len(indices) >= 2]

    colors: list[int | None] = [None] * len(positions)
    ordered = sorted(palette)
    if len(multi) >= 1:
        colors[multi[0][0]] = ordered[-1]
        colors[multi[0][1]] = ordered[0]
    if len(multi) >= 2:
        colors[multi[1][0]] = ordered[1]
        colors[multi[1][1]] = ordered[-2]

    already = {value for value in colors if value is not None}
    remaining_colors = [value for value in palette if value not in already]
    rng.shuffle(remaining_colors)
    empty_indices = [index for index, value in enumerate(colors) if value is None]
    for index, value in zip(empty_indices, remaining_colors):
        colors[index] = value
    for index in empty_indices[len(remaining_colors):]:
        colors[index] = rng.choice(tuple(palette))

    result = [int(value) for value in colors]
    if set(result) != set(palette):
        raise RuntimeError("constructive palette assignment lost a requested color")
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    scheduled = dict(_SCHEDULE[schedule_profile(seed, sample_index, difficulty)])
    effective = {
        **scheduled,
        **{name: value for name, value in overrides.items() if value is not None},
    }
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    profile = ctx.draw_choice("scene_profile", _PROFILE_NAMES)
    n_markers = ctx.draw_int_strict("n_markers", 6, 7)
    pattern = ctx.draw_choice("column_pattern", _COLUMN_PATTERNS)
    position = ctx.draw_choice("frame_position", _FRAME_POSITIONS)

    h, w, palette_size = _PROFILE_TABLE[profile]
    frame_h, frame_w = _frame_size(n_markers, pattern)
    r0, c0 = _frame_origin(h, w, frame_h, frame_w, position)
    box = (r0, c0, r0 + frame_h - 1, c0 + frame_w - 1)

    grid = full_grid(h, w, 0)
    _draw_frame(grid, box)
    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    placement_rng = ctx.draw_rng(f"placement:{band}")
    positions = _placement_positions(box, n_markers, pattern, placement_rng)

    marker_color_count = palette_size - 2  # background 0 and frame 8
    palette_rng = ctx.draw_rng(f"palette:{band}")
    palette = palette_rng.sample(list(_MARKER_COLORS), marker_color_count)
    colors = _assign_colors(positions, palette, ctx.draw_rng(f"color_order:{band}"))
    for (r, c), color in zip(positions, colors):
        if grid[r][c] != 0:
            raise RuntimeError("constructive marker placement collided with frame")
        grid[r][c] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructed invalid grid: {errors}")
    return grid


def _shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30x30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _find_frame(grid: Sequence[Sequence[int]]) -> tuple[int, int, int, int]:
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8}
    if not cells:
        raise ValueError("expected one color-8 rectangular border")
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    if r1 - r0 + 1 < 6 or c1 - c0 + 1 < 6:
        raise ValueError("color-8 frame must be at least 6x6")
    border = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    if cells != border:
        raise ValueError("color-8 cells must be exactly one complete rectangular border")
    return r0, c0, r1, c1


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _shape_errors(grid)
    if errors:
        return {"errors": errors}
    try:
        box = _find_frame(grid)
    except ValueError as exc:
        return {"errors": [str(exc)]}
    r0, c0, r1, c1 = box
    errors = []
    markers: list[tuple[int, int, int]] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            inside = r0 < r < r1 and c0 < c < c1
            on_frame = (r0 <= r <= r1 and c0 <= c <= c1 and
                        (r in (r0, r1) or c in (c0, c1)))
            if on_frame:
                if value != 8:
                    errors.append(f"frame cell {(r, c)} must be color 8")
            elif inside:
                if value == 8:
                    errors.append(f"interior cell {(r, c)} cannot be color 8")
                elif value != 0:
                    markers.append((r, c, value))
            elif value != 0:
                errors.append(f"outside-frame cell {(r, c)} must be background 0")
    if not 2 <= len(markers) <= 12:
        errors.append(f"expected 2..12 interior markers, found {len(markers)}")
    if len({value for _, _, value in markers}) < 2:
        errors.append("interior markers must use at least two colors")
    return {"errors": errors, "box": box, "markers": markers}


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror of the pinned Racket rule for testing/rivals."""
    errors = _shape_errors(grid)
    if errors:
        raise ValueError(errors[0])
    r0, c0, r1, c1 = _find_frame(grid)
    out = full_grid(len(grid), len(grid[0]), 0)
    _draw_frame(out, (r0, c0, r1, c1))
    for c in range(c0 + 1, c1):
        values = [grid[r][c] for r in range(r0 + 1, r1) if grid[r][c] != 0]
        for offset, value in enumerate(values):
            out[r0 + 1 + offset][c] = value
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if rule_mirror(grid) == [list(row) for row in grid]:
        errors.append("at least one marker must move upward")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the selected lawful domain, including all canonical inputs."""
    return self_check(grid)


def _column_values(grid: Sequence[Sequence[int]]) -> dict[int, list[int]]:
    r0, c0, r1, c1 = _find_frame(grid)
    return {
        c: [grid[r][c] for r in range(r0 + 1, r1) if grid[r][c] != 0]
        for c in range(c0 + 1, c1)
        if any(grid[r][c] != 0 for r in range(r0 + 1, r1))
    }


def observe_overrides(grid) -> dict[str, object]:
    """Recover every advertised exact control from returned pixels."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError(analysis["errors"][0])
    h, w = len(grid), len(grid[0])
    palette_size = len({value for row in grid for value in row})
    signature = (h, w, palette_size)
    matches = [name for name, value in _PROFILE_TABLE.items() if value == signature]
    if len(matches) != 1:
        raise ValueError(f"grid signature {signature} does not identify one scene_profile")
    profile = matches[0]

    columns = _column_values(grid)
    counts = [len(values) for values in columns.values()]
    if counts and all(count == 1 for count in counts):
        pattern = "separate"
    elif counts and all(count >= 2 for count in counts):
        pattern = "stacked"
    elif any(count >= 2 for count in counts) and any(count == 1 for count in counts):
        pattern = "mixed"
    else:
        raise ValueError(f"occupied-column counts {counts} do not identify a pattern")

    r0, c0, r1, c1 = analysis["box"]
    frame_h, frame_w = r1 - r0 + 1, c1 - c0 + 1
    anchors = {
        name: _frame_origin(h, w, frame_h, frame_w, name)
        for name in _FRAME_POSITIONS
    }
    positions = [name for name, origin in anchors.items() if origin == (r0, c0)]
    if len(positions) != 1:
        raise ValueError(f"frame origin {(r0, c0)} does not identify one frame_position")

    return {
        "scene_profile": profile,
        "n_markers": len(analysis["markers"]),
        "column_pattern": pattern,
        "frame_position": positions[0],
    }


def _pack_rival(
    grid: Sequence[Sequence[int]],
    *,
    sort_reverse: bool | None = None,
    downward: bool = False,
    first_only: bool = False,
) -> list[list[int]]:
    r0, c0, r1, c1 = _find_frame(grid)
    out = full_grid(len(grid), len(grid[0]), 0)
    _draw_frame(out, (r0, c0, r1, c1))
    for c in range(c0 + 1, c1):
        values = [grid[r][c] for r in range(r0 + 1, r1) if grid[r][c] != 0]
        if first_only:
            values = values[:1]
        if sort_reverse is not None:
            values = sorted(values, reverse=sort_reverse)
        start = r1 - len(values) if downward else r0 + 1
        for offset, value in enumerate(values):
            out[start + offset][c] = value
    return out


def _rival_sort_ascending(grid):
    return _pack_rival(grid, sort_reverse=False)


def _rival_sort_descending(grid):
    return _pack_rival(grid, sort_reverse=True)


def _rival_pack_down(grid):
    return _pack_rival(grid, downward=True)


def _rival_keep_first(grid):
    return _pack_rival(grid, first_only=True)


def _rival_identity(grid):
    return deepcopy(grid)


def _has_descending_stack(grid) -> bool:
    return any(
        any(a > b for a, b in zip(values, values[1:]))
        for values in _column_values(grid).values()
    )


def _has_ascending_stack(grid) -> bool:
    return any(
        any(a < b for a, b in zip(values, values[1:]))
        for values in _column_values(grid).values()
    )


def _has_multi_marker_column(grid) -> bool:
    return any(len(values) >= 2 for values in _column_values(grid).values())


def _moves_up(grid) -> bool:
    return rule_mirror(grid) != [list(row) for row in grid]


def _up_differs_from_down(grid) -> bool:
    return rule_mirror(grid) != _rival_pack_down(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "descending_stack": _has_descending_stack,
    "ascending_stack": _has_ascending_stack,
    "multiple_in_column": _has_multi_marker_column,
    "upward_motion": _moves_up,
    "top_vs_bottom": _up_differs_from_down,
}
SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "sort_each_column_ascending": _rival_sort_ascending,
    "sort_each_column_descending": _rival_sort_descending,
    "pack_each_column_down": _rival_pack_down,
    "keep_only_first_marker": _rival_keep_first,
    "leave_markers_in_place": _rival_identity,
}
WITNESS_RIVALS = {
    "descending_stack": ("sort_each_column_ascending",),
    "ascending_stack": ("sort_each_column_descending",),
    "multiple_in_column": ("keep_only_first_marker",),
    "upward_motion": ("leave_markers_in_place",),
    "top_vs_bottom": ("pack_each_column_down",),
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable] = {}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose demonstrations leave a declared rival viable."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]

    reasons: list[str] = []
    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} must contain input and output")
            continue
        grammar = strict_canonical_like(pair["input"])
        if grammar:
            reasons.append(f"pair {index} is outside the lawful domain: {grammar[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"pair {index} output disagrees with the pinned rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if survives and rival(query["input"]) != query["output"]:
            reasons.append(f"demonstrations do not falsify rival: {name}")
    return reasons
