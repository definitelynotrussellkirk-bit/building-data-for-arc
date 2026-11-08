"""Generator for overlaying two keyed components after rotating the second.

The first row contains two selector colors in left-to-right order.  Below a
blank separator row, one component of each selected color appears together
with one or two larger distractor components.  Crop the selected components,
rotate the second crop 90 degrees clockwise, top-left align the crops, and
merge them; overlap cells are always color 8.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "93d3caa82997"
TASK_ID = "93d3caa82997"
VERSION = "3.0.0"
RULE_HASH = "f3ff69e38bd8"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Read the two nonzero selector colors from row 0 in left-to-right order. "
    "Below the blank separator row, locate the single component of the first "
    "selector color and the single component of the second selector color; "
    "ignore the one or two larger distractor components. Crop both selected "
    "components to their bounding boxes, rotate the second crop 90 degrees "
    "clockwise, align the crops at their top-left corners on a canvas large "
    "enough for both, and overlay them. First-only cells keep the first color, "
    "second-only cells keep the second color, and overlaps become color 8."
)

INVARIANTS = [
    "row 0 contains exactly two distinct nonzero selector colors",
    "row 1 is a blank separator",
    "the body contains exactly one component of each selector color",
    "the body contains one or two nonselected distractor components",
    "the selected shape pair makes clockwise rotation and selector order decisive",
    "the top-left-aligned overlay has both exclusive cells and at least one overlap",
]

# Every declared axis is exact, keyed through GenCtx, and recoverable from the
# returned grid by observe_overrides().  Palette and placement texture vary but
# are deliberately not advertised as exact semantic axes.
AXES = {
    "grid_h": {"type": "int", "default": "keyed uniform", "valid": "10..12"},
    "grid_w": {"type": "int", "default": "keyed uniform", "valid": "12..15"},
    "shape_pair": {"type": "int", "default": "keyed uniform", "valid": "0..7"},
    "selector_layout": {"type": "int", "default": "keyed uniform", "valid": "0..2"},
    "distractor_count": {"type": "int", "default": "keyed uniform", "valid": "1..2"},
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


# The first five pairs reproduce every selected-shape relation seen in the
# canonical train/test set.  The remaining three broaden rotation/overlap
# structure while preserving a unique answer and nonempty exclusive regions.
_S0 = _shape("100", "111")
_S1 = _shape("111", "010", "010")
_S2 = _shape("10", "11", "01")
_S3 = _shape("110", "010", "011")
_S4 = _shape("010", "111", "010")
_S5 = _shape("11", "10", "10")
_S6 = _shape("111", "100")
_S7 = _shape("10", "10", "11")
_S9 = _shape("110", "011")

_SHAPE_PAIRS: tuple[tuple[Shape, Shape], ...] = (
    (_S0, _S1),
    (_S1, _S0),
    (_S2, _S3),
    (_S4, _S2),
    (_S1, _S2),
    (_S3, _S3),
    (_S5, _S6),
    (_S7, _S1),
)
_PAIR_INDEX = {pair: index for index, pair in enumerate(_SHAPE_PAIRS)}

# Both distractors have six cells, so a size-ranked shortcut must select at
# least one distractor instead of the intended keyed pair on every generated
# draw.  Canonical inputs with four/five-cell distractors remain accepted.
_DISTRACTOR_SHAPES: tuple[Shape, ...] = (
    _shape("111", "111"),
    _shape("11", "11", "11"),
)


@dataclass(frozen=True)
class _Object:
    color: int
    cells: frozenset[Cell]

    @property
    def top(self) -> int:
        return min(r for r, _ in self.cells)

    @property
    def left(self) -> int:
        return min(c for _, c in self.cells)

    @property
    def bottom(self) -> int:
        return max(r for r, _ in self.cells)

    @property
    def right(self) -> int:
        return max(c for _, c in self.cells)

    @property
    def area(self) -> int:
        return len(self.cells)

    @property
    def crop(self) -> Shape:
        return frozenset((r - self.top, c - self.left) for r, c in self.cells)


def _shape_hw(shape: Shape) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _rotate_cw(shape: Shape) -> Shape:
    h, _ = _shape_hw(shape)
    return frozenset((c, h - 1 - r) for r, c in shape)


def _paint(grid: Grid, top: int, left: int, shape: Shape, color: int) -> None:
    for dr, dc in shape:
        grid[top + dr][left + dc] = color


def _components(grid: Grid) -> list[_Object]:
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[_Object] = []
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
            components.append(_Object(color, frozenset(cells)))
    return components


def _selector_columns(grid: Grid) -> tuple[int, int]:
    cols = tuple(c for c, value in enumerate(grid[0]) if value != 0)
    if len(cols) != 2:
        raise ValueError(f"expected exactly two selector cells, got {cols}")
    return cols


def _selector_layout_from_columns(w: int, columns: tuple[int, int]) -> int:
    layouts = (
        (1, 3),
        (0, w - 1),
        (w // 2 - 2, w // 2 + 2),
    )
    try:
        return layouts.index(columns)
    except ValueError as exc:
        raise ValueError(f"unrecognized selector layout {columns} for width {w}") from exc


def _scene(grid: Grid) -> tuple[int, int, _Object, _Object, list[_Object]]:
    selector_cols = _selector_columns(grid)
    a = grid[0][selector_cols[0]]
    b = grid[0][selector_cols[1]]
    body_objects = _components(grid[1:])
    a_objects = [obj for obj in body_objects if obj.color == a]
    b_objects = [obj for obj in body_objects if obj.color == b]
    if len(a_objects) != 1 or len(b_objects) != 1:
        raise ValueError(
            f"expected one object for each selector, got a={len(a_objects)} b={len(b_objects)}"
        )
    distractors = [obj for obj in body_objects if obj.color not in {a, b}]
    return a, b, a_objects[0], b_objects[0], distractors


def _overlay_shapes(
    first: Shape,
    second: Shape,
    first_color: int,
    second_color: int,
    *,
    rotate_second: bool = True,
    overlap_color: int = 8,
) -> Grid:
    second_shape = _rotate_cw(second) if rotate_second else second
    h = max(_shape_hw(first)[0], _shape_hw(second_shape)[0])
    w = max(_shape_hw(first)[1], _shape_hw(second_shape)[1])
    out = full_grid(h, w, 0)
    for r, c in first:
        out[r][c] = first_color
    for r, c in second_shape:
        out[r][c] = overlap_color if out[r][c] != 0 else second_color
    return out


def _solve_grid(grid: Grid) -> Grid:
    a, b, first, second, _ = _scene(grid)
    return _overlay_shapes(first.crop, second.crop, a, b)


def _no_rotation_rival(grid: Grid) -> Grid:
    a, b, first, second, _ = _scene(grid)
    return _overlay_shapes(
        first.crop, second.crop, a, b, rotate_second=False
    )


def _reversed_selectors_rival(grid: Grid) -> Grid:
    a, b, first, second, _ = _scene(grid)
    return _overlay_shapes(second.crop, first.crop, b, a)


def _wrong_overlap_marker_rival(grid: Grid) -> Grid:
    a, b, first, second, _ = _scene(grid)
    return _overlay_shapes(first.crop, second.crop, a, b, overlap_color=9)


def _overlay_objects(first: _Object, second: _Object) -> Grid:
    return _overlay_shapes(first.crop, second.crop, first.color, second.color)


def _first_two_body_objects_rival(grid: Grid) -> Grid:
    body_components = sorted(
        _components(grid[1:]), key=lambda obj: (obj.top, obj.left, obj.color)
    )
    return _overlay_objects(body_components[0], body_components[1])


def _largest_two_objects_rival(grid: Grid) -> Grid:
    body_components = sorted(
        _components(grid[1:]),
        key=lambda obj: (-obj.area, obj.top, obj.left, obj.color),
    )
    return _overlay_objects(body_components[0], body_components[1])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic, shortcut-rebutting canonical lesson input."""
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)}")

    band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int("grid_h", 10, 12)
    w = ctx.draw_int("grid_w", 12, 15)
    pair_index = ctx.draw_int("shape_pair", 0, len(_SHAPE_PAIRS) - 1)
    selector_layout = ctx.draw_int("selector_layout", 0, 2)
    distractor_count = ctx.draw_int("distractor_count", 1, 2)

    palette = ctx.draw_distinct_colors(
        f"palette_{band}", n=2 + distractor_count, exclude={0}
    )
    a, b, *distractor_colors = palette
    # For canonical pair 4, making the first selector color 8 aliases the
    # overlap marker and can hide whether the second object was rotated.  Keep
    # color 8 in-distribution by moving it to the second selector instead.
    if pair_index == 4 and a == 8:
        a, b = b, a
    first_shape, second_shape = _SHAPE_PAIRS[pair_index]

    selector_columns = (
        (1, 3),
        (0, w - 1),
        (w // 2 - 2, w // 2 + 2),
    )[selector_layout]

    rng = ctx.draw_rng(f"placement_{band}")
    top = rng.randint(2, h - 7)
    bottom = rng.randint(top + 4, h - 3)
    left = rng.randint(0, max(0, w // 2 - 4))
    right = rng.randint(max(w // 2 + 1, left + 4), w - 3)
    anchors = sorted(((top, left), (top, right), (bottom, left), (bottom, right)))
    anchors = sorted(rng.sample(anchors, 2 + distractor_count))

    # A distractor is always the first row-major body object.  The selected
    # objects alternate spatial order, so neither "first two body objects" nor
    # a fixed A-before-B assumption can fit the lesson distribution.
    selected_order = rng.randrange(2)
    if distractor_count == 1:
        roles = (
            (("d0", _DISTRACTOR_SHAPES[0]), ("a", first_shape), ("b", second_shape))
            if selected_order == 0
            else (("d0", _DISTRACTOR_SHAPES[0]), ("b", second_shape), ("a", first_shape))
        )
    else:
        roles = (
            (
                ("d0", _DISTRACTOR_SHAPES[0]),
                ("a", first_shape),
                ("d1", _DISTRACTOR_SHAPES[1]),
                ("b", second_shape),
            )
            if selected_order == 0
            else (
                ("d0", _DISTRACTOR_SHAPES[0]),
                ("b", second_shape),
                ("d1", _DISTRACTOR_SHAPES[1]),
                ("a", first_shape),
            )
        )

    grid = full_grid(h, w, 0)
    grid[0][selector_columns[0]] = a
    grid[0][selector_columns[1]] = b
    colors = {"a": a, "b": b}
    for index, color in enumerate(distractor_colors):
        colors[f"d{index}"] = color
    for (role, shape), (anchor_r, anchor_c) in zip(roles, anchors):
        _paint(grid, anchor_r, anchor_c, shape, colors[role])

    # These are construction invariants, not a Python replacement oracle.  The
    # Racket rule remains the sole emitted-output authority in the runner.
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"internal generator invariant failed: {errors}")
    true_output = _solve_grid(grid)
    rivals = (
        _no_rotation_rival,
        _reversed_selectors_rival,
        _wrong_overlap_marker_rival,
        _first_two_body_objects_rival,
        _largest_two_objects_rival,
    )
    if any(rival(grid) == true_output for rival in rivals):
        raise RuntimeError("constructed lesson failed to refute a required rival")
    return grid


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis from the returned input grid."""
    a, b, first, second, distractors = _scene(grid)
    del a, b
    signature = (first.crop, second.crop)
    if signature not in _PAIR_INDEX:
        raise ValueError("selected shapes do not match a declared shape_pair")
    columns = _selector_columns(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "shape_pair": _PAIR_INDEX[signature],
        "selector_layout": _selector_layout_from_columns(len(grid[0]), columns),
        "distractor_count": len(distractors),
    }


def _objects_touch(first: _Object, second: _Object) -> bool:
    second_cells = second.cells
    return any(
        (r + dr, c + dc) in second_cells
        for r, c in first.cells
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or shortcut-hiding lesson inputs."""
    del difficulty, meta
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid rows must be rectangular"]
    if not (10 <= h <= 12 and 12 <= w <= 15):
        errors.append(f"expected canonical-scale dimensions 10..12x12..15, got {h}x{w}")
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
    if errors:
        return errors

    selector_columns = tuple(c for c, value in enumerate(grid[0]) if value != 0)
    if len(selector_columns) != 2:
        return [f"row 0 must contain exactly two selectors, got {selector_columns}"]
    selector_colors = tuple(grid[0][c] for c in selector_columns)
    if selector_colors[0] == selector_colors[1]:
        errors.append("selector colors must be distinct")
    try:
        _selector_layout_from_columns(w, selector_columns)
    except ValueError as exc:
        errors.append(str(exc))
    if any(value != 0 for value in grid[1]):
        errors.append("row 1 must be a blank separator")

    body_objects = _components(grid[1:])
    for color in selector_colors:
        count = sum(obj.color == color for obj in body_objects)
        if count != 1:
            errors.append(f"selector color {color} must have exactly one body component, got {count}")
    distractors = [obj for obj in body_objects if obj.color not in set(selector_colors)]
    if not 1 <= len(distractors) <= 2:
        errors.append(f"expected one or two distractor components, got {len(distractors)}")
    if len({obj.color for obj in distractors}) != len(distractors):
        errors.append("each distractor component must use a distinct nonselector color")
    for obj in distractors:
        dh, dw = _shape_hw(obj.crop)
        if not (4 <= obj.area <= 6 and dh <= 3 and dw <= 3):
            errors.append(
                f"distractor color {obj.color} must be a 4..6-cell component inside 3x3; "
                f"got area={obj.area} bbox={dh}x{dw}"
            )
    if errors:
        return errors

    try:
        _, _, first, second, _ = _scene(grid)
    except ValueError as exc:
        return [str(exc)]
    if _objects_touch(first, second):
        errors.append("the two selected components must be spatially separated")
    pair = (first.crop, second.crop)
    if pair not in _PAIR_INDEX:
        errors.append("selected components are not one of the eight lawful shape pairs")
        return errors

    rotated_second = _rotate_cw(second.crop)
    overlap = first.crop & rotated_second
    if not overlap:
        errors.append("rotated selected components must overlap at least once")
    if not (first.crop - rotated_second):
        errors.append("overlay must retain at least one first-only cell")
    if not (rotated_second - first.crop):
        errors.append("overlay must retain at least one second-only cell")
    if errors:
        return errors

    true_output = _solve_grid(grid)
    if _no_rotation_rival(grid) == true_output:
        errors.append("clockwise rotation is not observable in the answer")
    if _reversed_selectors_rival(grid) == true_output:
        errors.append("selector order is not observable in the answer")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The strict teaching grammar includes all five canonical inputs."""
    return self_check(grid)


MIN_STRICT_FRAC = 0.95


def _overlap_count(grid: Grid) -> int:
    _, _, first, second, _ = _scene(grid)
    return len(first.crop & _rotate_cw(second.crop))


def _selected_body_order(grid: Grid) -> str:
    _, _, first, second, _ = _scene(grid)
    return "a_before_b" if (first.top, first.left) < (second.top, second.left) else "b_before_a"


def _differs(rival: Callable[[Grid], Grid]) -> Callable[[Grid], bool]:
    return lambda grid: rival(grid) != _solve_grid(grid)


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "overlay_without_rotating_second": _no_rotation_rival,
    "reverse_selector_order": _reversed_selectors_rival,
    "use_color_9_for_overlap": _wrong_overlap_marker_rival,
    "use_first_two_body_objects": _first_two_body_objects_rival,
    "use_two_largest_body_objects": _largest_two_objects_rival,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS

SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "clockwise_rotation_decisive": _differs(_no_rotation_rival),
    "selector_order_decisive": _differs(_reversed_selectors_rival),
    "cyan_overlap_marker_decisive": _differs(_wrong_overlap_marker_rival),
    "distractor_refutes_body_order": _differs(_first_two_body_objects_rival),
    "distractor_refutes_size_ranking": _differs(_largest_two_objects_rival),
    "one_distractor": lambda grid: (
        observe_overrides(grid)["distractor_count"] == 1
        and _largest_two_objects_rival(grid) != _solve_grid(grid)
    ),
    "two_distractors": lambda grid: (
        observe_overrides(grid)["distractor_count"] == 2
        and _largest_two_objects_rival(grid) != _solve_grid(grid)
    ),
    "one_overlap_cell": lambda grid: (
        _overlap_count(grid) == 1 and _wrong_overlap_marker_rival(grid) != _solve_grid(grid)
    ),
    "two_overlap_cells": lambda grid: (
        _overlap_count(grid) == 2 and _wrong_overlap_marker_rival(grid) != _solve_grid(grid)
    ),
    "three_overlap_cells": lambda grid: (
        _overlap_count(grid) == 3 and _wrong_overlap_marker_rival(grid) != _solve_grid(grid)
    ),
    "canonical_selector_layout": lambda grid: (
        observe_overrides(grid)["selector_layout"] == 0
        and _reversed_selectors_rival(grid) != _solve_grid(grid)
    ),
    "edge_selector_layout": lambda grid: (
        observe_overrides(grid)["selector_layout"] == 1
        and _reversed_selectors_rival(grid) != _solve_grid(grid)
    ),
    "centered_selector_layout": lambda grid: (
        observe_overrides(grid)["selector_layout"] == 2
        and _reversed_selectors_rival(grid) != _solve_grid(grid)
    ),
    "a_before_b_in_body": lambda grid: (
        _selected_body_order(grid) == "a_before_b"
        and _first_two_body_objects_rival(grid) != _solve_grid(grid)
    ),
    "b_before_a_in_body": lambda grid: (
        _selected_body_order(grid) == "b_before_a"
        and _first_two_body_objects_rival(grid) != _solve_grid(grid)
    ),
    **{
        f"shape_pair_{index}": (
            lambda grid, expected=index: (
                observe_overrides(grid)["shape_pair"] == expected
                and _no_rotation_rival(grid) != _solve_grid(grid)
            )
        )
        for index in range(len(_SHAPE_PAIRS))
    },
}

WITNESS_RIVALS = {
    "clockwise_rotation_decisive": ["overlay_without_rotating_second"],
    "selector_order_decisive": ["reverse_selector_order"],
    "cyan_overlap_marker_decisive": ["use_color_9_for_overlap"],
    "distractor_refutes_body_order": ["use_first_two_body_objects"],
    "distractor_refutes_size_ranking": ["use_two_largest_body_objects"],
    "one_distractor": ["use_two_largest_body_objects"],
    "two_distractors": ["use_two_largest_body_objects"],
    "one_overlap_cell": ["use_color_9_for_overlap"],
    "two_overlap_cells": ["use_color_9_for_overlap"],
    "three_overlap_cells": ["use_color_9_for_overlap"],
    "canonical_selector_layout": ["reverse_selector_order"],
    "edge_selector_layout": ["reverse_selector_order"],
    "centered_selector_layout": ["reverse_selector_order"],
    "a_before_b_in_body": ["use_first_two_body_objects"],
    "b_before_a_in_body": ["use_first_two_body_objects"],
    **{
        f"shape_pair_{index}": ["overlay_without_rotating_second"]
        for index in range(len(_SHAPE_PAIRS))
    },
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any lesson whose demonstrations leave a named rival viable."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    reasons: list[str] = []
    all_pairs = [*demos, query]
    for index, pair in enumerate(all_pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        try:
            expected = _solve_grid(pair["input"])
        except Exception as exc:
            reasons.append(f"pair {index} is outside the teaching grammar: {exc}")
            continue
        if pair["output"] != expected:
            reasons.append(f"pair {index} output disagrees with keyed-rotation overlay rule")

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
                    f"demonstrations leave competitor answer-equivalent on the query: {name}"
                )
    return reasons
