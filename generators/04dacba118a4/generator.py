"""Generator for the normalized priority-overlay task ``04dacba118a4``.

The top-left cell is a key.  Remove that key, sort the two remaining
single-color 4-connected objects by the canonical bounding-box comparator,
crop each object to its own bounding box, align the crops at their top-left
corners, and overlay them.  Key 1 gives overlap priority to the first object;
key 2 gives priority to the second object.

Ordinary lessons use a four-sample schedule.  Every four consecutive samples
contain both key values and both assignments of one color pair to object order,
so neither a constant object priority nor a fixed color priority can explain a
materialized lesson.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "04dacba118a4"
TASK_ID = "04dacba118a4"
VERSION = "4.0.0"
RULE_HASH = "00fd17fc125d"
EXAMPLES_NEEDED = 4

SUMMARY = (
    "Read key 1 or 2 from (0,0), then erase that cell. Find exactly two "
    "single-color 4-connected objects and sort them by bounding box in the "
    "canonical order: top row, bottom row, left column, right column. Crop "
    "each object tightly and align the two crops at their top-left corners. "
    "Overlay them on the smallest common canvas: key 1 makes the first sorted "
    "object win overlap cells, while key 2 makes the second object win."
)

INVARIANTS = [
    "the input is a rectangular ARC grid and (0,0) is key 1 or 2",
    "after erasing the key there are exactly two nonempty single-color 4-connected objects",
    "the two normalized crops are different and overlap in at least one cell",
    "flipping the key changes the normalized overlay answer",
    "ordinary generated crops each retain an exclusive cell, so both object colors remain visible",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware keyed draw",
        "valid": "8..13",
        "doc": "Input-grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware keyed draw",
        "valid": "10..15",
        "doc": "Input-grid width.",
    },
    "key": {
        "type": "int",
        "default": "four-sample lesson schedule",
        "valid": "1..2",
        "doc": "1 gives overlap priority to the first bbox-sorted object; 2 to the second.",
    },
    "shape_pair": {
        "type": "int",
        "default": "eight-profile lesson schedule",
        "valid": "0..7",
        "doc": "Ordered pair of normalized connected motif shapes.",
    },
    "layout": {
        "type": "str",
        "default": "four-sample lesson schedule",
        "valid": "first_left|first_right",
        "doc": "Whether the bbox-first object is left or right of the bbox-second object.",
    },
}

Cell = tuple[int, int]
Shape = frozenset[Cell]
Grid = list[list[int]]


def _shape(*rows: str) -> Shape:
    return frozenset(
        (r, c)
        for r, row in enumerate(rows)
        for c, value in enumerate(row)
        if value == "1"
    )


# All generated pairs are connected, overlap after normalization, differ from
# one another, and retain at least one exclusive cell on each side.  The
# canonical checker intentionally accepts a broader lawful shape family so it
# also owns all four source examples.
_SHAPE_PAIRS: tuple[tuple[Shape, Shape], ...] = (
    (_shape("10", "11"), _shape("111")),
    (_shape("111", "010"), _shape("010", "111")),
    (_shape("110", "011"), _shape("011", "110")),
    (_shape("010", "111", "010"), _shape("110", "100", "110")),
    (_shape("100", "111"), _shape("111", "001")),
    (_shape("110", "010", "011"), _shape("011", "010", "110")),
    (_shape("111", "100", "100"), _shape("001", "001", "111")),
    (_shape("010", "110", "011"), _shape("110", "011", "010")),
)
_PAIR_INDEX = {pair: index for index, pair in enumerate(_SHAPE_PAIRS)}
_LAYOUTS = ("first_left", "first_right")
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}

SCHEDULE_PROFILES = (
    "key1_base_first_left",
    "key2_base_first_left",
    "key1_swapped_first_right",
    "key2_swapped_first_right",
)


@dataclass(frozen=True)
class _Object:
    color: int
    cells: frozenset[Cell]

    @property
    def top(self) -> int:
        return min(r for r, _ in self.cells)

    @property
    def bottom(self) -> int:
        return max(r for r, _ in self.cells)

    @property
    def left(self) -> int:
        return min(c for _, c in self.cells)

    @property
    def right(self) -> int:
        return max(c for _, c in self.cells)

    @property
    def crop(self) -> Shape:
        return frozenset((r - self.top, c - self.left) for r, c in self.cells)


def _shape_hw(shape: Shape) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _components(grid: Grid) -> list[_Object]:
    """Match Racket ``objects``: same-color, 4-connected components."""
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    found: list[_Object] = []
    for start_r in range(h):
        for start_c in range(w):
            color = grid[start_r][start_c]
            if color == 0 or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells: set[Cell] = set()
            while stack:
                r, c = stack.pop()
                cells.add((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            found.append(_Object(color=color, cells=frozenset(cells)))
    return found


def _bbox_sort_key(obj: _Object) -> tuple[int, int, int, int]:
    # Canonical Racket bbox< compares r1, then r2, then c1, then c2.
    return (obj.top, obj.bottom, obj.left, obj.right)


def _scene(grid: Grid) -> tuple[int, _Object, _Object]:
    key = grid[0][0]
    work = [row[:] for row in grid]
    work[0][0] = 0
    components = sorted(_components(work), key=_bbox_sort_key)
    if len(components) != 2:
        raise ValueError(
            f"expected exactly two objects after erasing key, got {len(components)}"
        )
    return key, components[0], components[1]


def _overlay(
    first: _Object,
    second: _Object,
    *,
    first_wins: bool,
) -> Grid:
    first_shape = first.crop
    second_shape = second.crop
    h = max(_shape_hw(first_shape)[0], _shape_hw(second_shape)[0])
    w = max(_shape_hw(first_shape)[1], _shape_hw(second_shape)[1])
    out = full_grid(h, w, 0)
    for r, c in first_shape:
        out[r][c] = first.color
    for r, c in second_shape:
        if out[r][c] == 0 or not first_wins:
            out[r][c] = second.color
    return out


def expected_output(grid: Grid) -> Grid:
    """Python mirror for tests/rivals; the Racket program remains authority."""
    key, first, second = _scene(grid)
    return _overlay(first, second, first_wins=(key == 1))


def _first_always_wins(grid: Grid) -> Grid:
    _, first, second = _scene(grid)
    return _overlay(first, second, first_wins=True)


def _second_always_wins(grid: Grid) -> Grid:
    _, first, second = _scene(grid)
    return _overlay(first, second, first_wins=False)


def _lower_color_wins(grid: Grid) -> Grid:
    _, first, second = _scene(grid)
    return _overlay(first, second, first_wins=(first.color < second.color))


def _higher_color_wins(grid: Grid) -> Grid:
    _, first, second = _scene(grid)
    return _overlay(first, second, first_wins=(first.color > second.color))


def _keep_original_spacing(grid: Grid) -> Grid:
    """Rival: crop the joint scene without independently normalizing objects."""
    _, first, second = _scene(grid)
    top = min(first.top, second.top)
    bottom = max(first.bottom, second.bottom)
    left = min(first.left, second.left)
    right = max(first.right, second.right)
    out = full_grid(bottom - top + 1, right - left + 1, 0)
    for obj in (first, second):
        for r, c in obj.cells:
            out[r - top][c - left] = obj.color
    return out


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % 4]


def _scheduled_int(ctx, label: str, lo: int, hi: int, value: int) -> int:
    """Record a scheduled default while preserving the full override domain."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, value, value)


def _scheduled_choice(ctx, label: str, options: tuple[str, ...], value: str) -> str:
    """Record a scheduled default while preserving the full override domain."""
    available = options if label in ctx.overrides and ctx.overrides[label] is not None else (value,)
    return str(ctx.draw_choice(label, available))


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {unknown}")


def _paint(grid: Grid, top: int, left: int, shape: Shape, color: int) -> None:
    for dr, dc in shape:
        grid[top + dr][left + dc] = color


def _place_shapes(
    h: int,
    w: int,
    first_shape: Shape,
    second_shape: Shape,
    layout: str,
    rng,
) -> tuple[int, int, int, int]:
    first_h, first_w = _shape_hw(first_shape)
    second_h, second_w = _shape_hw(second_shape)

    # Distinct top rows make the canonical bbox order unambiguous.  The
    # objects occupy opposite horizontal regions, so their row spans may
    # overlap without joining or visually conflating the two components.
    first_top = rng.randint(1, max(1, min(2, h - first_h - 1)))
    second_top = rng.randint(first_top + 1, h - second_h)

    if layout == "first_left":
        first_left = rng.randint(0, max(0, w // 3 - first_w))
        second_left_min = max(w // 2 + 1, first_left + first_w + 2)
        second_left = rng.randint(second_left_min, w - second_w)
    else:
        second_left = rng.randint(0, max(0, w // 3 - second_w))
        first_left_min = max(w // 2 + 1, second_left + second_w + 2)
        first_left = rng.randint(first_left_min, w - first_w)
    return first_top, first_left, second_top, second_left


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic, structurally checked teaching input."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    h = ctx.draw_int_diff("grid_h", 8, 13)
    w = ctx.draw_int_diff("grid_w", 10, 15)
    phase = int(sample_index) % 4
    key = _scheduled_int(ctx, "key", 1, 2, 1 if phase in (0, 2) else 2)
    pair_index = _scheduled_int(
        ctx, "shape_pair", 0, len(_SHAPE_PAIRS) - 1, int(sample_index) % len(_SHAPE_PAIRS)
    )
    layout = _scheduled_choice(
        ctx,
        "layout",
        _LAYOUTS,
        "first_left" if phase in (0, 1) else "first_right",
    )

    # The block pair is shared across four schedule phases.  The second half of
    # the block swaps object/color roles, defeating fixed-color priority.
    palette_rng = stable_rng(
        int(seed), f"{TASK_ID}|palette-block|{int(sample_index) // 4}", VERSION
    )
    base_colors = tuple(palette_rng.sample(range(1, 10), 2))
    first_color, second_color = (
        base_colors if phase in (0, 1) else tuple(reversed(base_colors))
    )

    first_shape, second_shape = _SHAPE_PAIRS[pair_index]
    placement_rng = ctx.draw_rng("placement")
    first_top, first_left, second_top, second_left = _place_shapes(
        h, w, first_shape, second_shape, layout, placement_rng
    )

    grid = full_grid(h, w, 0)
    grid[0][0] = key
    _paint(grid, first_top, first_left, first_shape, first_color)
    _paint(grid, second_top, second_left, second_shape, second_color)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"internal generator invariant failed: {errors}")
    _, first, second = _scene(grid)
    if not (first.crop - second.crop) or not (second.crop - first.crop):
        raise RuntimeError("generated shapes must each retain an exclusive normalized cell")
    if _keep_original_spacing(grid) == expected_output(grid):
        raise RuntimeError("generated scene failed to make independent normalization observable")
    return grid


def _valid_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a nonempty list of nonempty rows"]
    w = len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    errors: list[str] = []
    if len(grid) > 30 or w > 30:
        errors.append(f"grid exceeds ARC limit: {len(grid)}x{w}")
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
    return errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed scenes and scenes where the key/normalization is hidden."""
    del difficulty, meta
    errors = _valid_grid_errors(grid)
    if errors:
        return errors
    key = grid[0][0]
    if key not in (1, 2):
        errors.append(f"(0,0) = {key}; expected key 1 or 2")
    if any(value != 0 for value in grid[0][1:]):
        errors.append("row 0 may contain only the top-left key")
    if errors:
        return errors

    try:
        _, first, second = _scene(grid)
    except ValueError as exc:
        return [str(exc)]
    if first.color == second.color:
        errors.append("the two objects must use distinct colors")
    if first.crop == second.crop:
        errors.append("normalized object crops must differ so key priority is observable")
    if not (first.crop & second.crop):
        errors.append("normalized object crops must overlap in at least one cell")
    if errors:
        return errors

    key1 = _overlay(first, second, first_wins=True)
    key2 = _overlay(first, second, first_wins=False)
    if key1 == key2:
        errors.append("flipping the key does not change the normalized overlay answer")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The task grammar is color-generic and includes every canonical input."""
    return self_check(grid)


MIN_STRICT_FRAC = 1.0


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared exact axis from a generated input grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    key, first, second = _scene(grid)
    pair = (first.crop, second.crop)
    if pair not in _PAIR_INDEX:
        raise ValueError("normalized crops do not match a declared shape_pair")
    if first.left == second.left:
        raise ValueError("generated layout is not observable: object left edges are equal")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "key": key,
        "shape_pair": _PAIR_INDEX[pair],
        "layout": "first_left" if first.left < second.left else "first_right",
    }


def _differs(rival: Callable[[Grid], Grid]) -> Callable[[Grid], bool]:
    return lambda grid: rival(grid) != expected_output(grid)


def _overlap_count(grid: Grid) -> int:
    _, first, second = _scene(grid)
    return len(first.crop & second.crop)


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "first_object_always_wins": _first_always_wins,
    "second_object_always_wins": _second_always_wins,
    "lower_color_always_wins": _lower_color_wins,
    "higher_color_always_wins": _higher_color_wins,
    "keep_original_object_spacing": _keep_original_spacing,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS

SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "key_1_first_priority": lambda grid: (
        grid[0][0] == 1 and _second_always_wins(grid) != expected_output(grid)
    ),
    "key_2_second_priority": lambda grid: (
        grid[0][0] == 2 and _first_always_wins(grid) != expected_output(grid)
    ),
    "lower_color_priority_refuted": _differs(_lower_color_wins),
    "higher_color_priority_refuted": _differs(_higher_color_wins),
    "independent_normalization_decisive": _differs(_keep_original_spacing),
    "first_object_left_layout": lambda grid: (
        observe_overrides(grid)["layout"] == "first_left"
        and _keep_original_spacing(grid) != expected_output(grid)
    ),
    "first_object_right_layout": lambda grid: (
        observe_overrides(grid)["layout"] == "first_right"
        and _keep_original_spacing(grid) != expected_output(grid)
    ),
    "single_overlap_cell": lambda grid: (
        _overlap_count(grid) == 1
        and _keep_original_spacing(grid) != expected_output(grid)
    ),
    "multiple_overlap_cells": lambda grid: (
        _overlap_count(grid) >= 2
        and _keep_original_spacing(grid) != expected_output(grid)
    ),
    **{
        f"shape_pair_{index}": (
            lambda grid, expected=index: (
                observe_overrides(grid)["shape_pair"] == expected
                and _keep_original_spacing(grid) != expected_output(grid)
            )
        )
        for index in range(len(_SHAPE_PAIRS))
    },
}

WITNESS_RIVALS = {
    "key_1_first_priority": ["second_object_always_wins"],
    "key_2_second_priority": ["first_object_always_wins"],
    "lower_color_priority_refuted": ["lower_color_always_wins"],
    "higher_color_priority_refuted": ["higher_color_always_wins"],
    "independent_normalization_decisive": ["keep_original_object_spacing"],
    "first_object_left_layout": ["keep_original_object_spacing"],
    "first_object_right_layout": ["keep_original_object_spacing"],
    "single_overlap_cell": ["keep_original_object_spacing"],
    "multiple_overlap_cells": ["keep_original_object_spacing"],
    **{
        f"shape_pair_{index}": ["keep_original_object_spacing"]
        for index in range(len(_SHAPE_PAIRS))
    },
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose demos leave a named rival viable on the query."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    reasons: list[str] = []
    all_pairs = [*demos, query]
    for index, pair in enumerate(all_pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        try:
            expected = expected_output(pair["input"])
        except Exception as exc:
            reasons.append(f"pair {index} is outside the teaching grammar: {exc}")
            continue
        if pair["output"] != expected:
            reasons.append(f"pair {index} output disagrees with normalized priority overlay")

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(demo["input"]) == demo["output"] for demo in demos
            )
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised: {exc}")
            continue
        if survives:
            if competitor(query["input"]) != query["output"]:
                reasons.append(f"demonstrations do not refute competitor: {name}")
            else:
                reasons.append(
                    f"demonstrations leave competitor answer-equivalent on query: {name}"
                )
    return reasons
