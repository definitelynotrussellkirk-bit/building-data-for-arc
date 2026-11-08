"""Input sampler for ARC task 2c1567aea733: align colors to blue's top.

Every non-background color is translated vertically as one color-wide object so
its top row matches the top row of color 1.  The sampler retains canonical
three-copy scenes, including the detached-tail test morphology, while adding
lawful mixed-shape witnesses and a three-example anchor-rank schedule that
rules out rectangle-only, median-object, and canonical-size shortcuts.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "2c1567aea733"
TASK_ID = GENERATOR_ID
RULE_HASH = "837d7987242d"
VERSION = "2.1.0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 0-background grid contains colors 1, 2, and 4 in horizontally disjoint "
    "regions. Color 1 is the anchor. Translate every cell of each nonzero color "
    "vertically, preserving its exact shape and columns, until that color's top "
    "row equals color 1's original top row."
)

INVARIANTS = [
    "the palette is exactly background 0 plus colors 1, 2, and 4",
    "each color occupies a horizontally disjoint column extent",
    "four consecutive sample indices use blue ranks top/middle/bottom/top so every three-demo rotation refutes rank shortcuts",
    "the output preserves every per-color shape and cell count",
    "all three color tops coincide with blue's original top after the rule",
]

SCENE_PROFILES = (
    "copied_rectangles",
    "copied_irregular",
    "mixed_shapes",
)
AXES = {
    "grid_h": {
        "type": "int",
        "default": "weighted 5..12, anchored at canonical heights 5 and 10",
        "valid": "5..12",
    },
    "grid_w": {
        "type": "int",
        "default": "weighted 10..15, anchored at canonical width 10",
        "valid": "10..15",
    },
    "scene_profile": {
        "type": "str",
        "default": "uniform copied_rectangles|copied_irregular|mixed_shapes",
        "valid": "|".join(SCENE_PROFILES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
LAWFUL_DEGENERATE_TEXTURES = ()

_COLORS = (1, 2, 4)
_RECTANGLE_SHAPES = {
    "vertical_bar": frozenset({(0, 0), (1, 0)}),
    "block": frozenset({(0, 0), (0, 1), (1, 0), (1, 1)}),
    "wide": frozenset({(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)}),
}
# Exact normalized morphology used by the canonical test query: a 2x2 body and
# a diagonally detached lower-left cell.  The selected rule moves both
# components together because it groups by color, not connectivity.
_DETACHED_TAIL = frozenset({(0, 1), (0, 2), (1, 1), (1, 2), (2, 0)})
_L_SHAPE = frozenset({(0, 0), (1, 0), (1, 1)})


def _validate_call(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, or string)")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool, float, or string)")
    profile = overrides.get("scene_profile")
    if profile is not None and type(profile) is not str:
        raise TypeError("scene_profile must be a string")


def _weighted_dimension(ctx, label, lo, hi, anchors) -> int:
    # Include every advertised value in every band so all exact overrides remain
    # constructive. Repeated anchors supply canonical profile support without
    # copying any canonical layout.
    options = list(range(lo, hi + 1)) + list(anchors)
    return ctx.draw_choice(label, options)


def _shape_extent(shape) -> tuple[int, int]:
    return (
        max(row for row, _ in shape) + 1,
        max(col for _, col in shape) + 1,
    )


def _reflect(shape):
    _, width = _shape_extent(shape)
    return frozenset((row, width - 1 - col) for row, col in shape)


def _profile_shapes(ctx, profile, difficulty):
    if profile == "copied_rectangles":
        names = {
            "easy": ("vertical_bar", "block", "block", "wide"),
            "medium": ("vertical_bar", "block", "wide"),
            "hard": ("block", "wide", "wide", "vertical_bar"),
            None: ("vertical_bar", "block", "wide"),
        }[difficulty]
        shape = _RECTANGLE_SHAPES[ctx.draw_choice("rectangle_shape", names)]
        return {color: shape for color in _COLORS}

    if profile == "copied_irregular":
        shape = _DETACHED_TAIL
        if ctx.draw_choice("irregular_reflection", (False, True)):
            shape = _reflect(shape)
        return {color: shape for color in _COLORS}

    if profile == "mixed_shapes":
        shapes = [
            _RECTANGLE_SHAPES["vertical_bar"],
            _L_SHAPE,
            _DETACHED_TAIL,
        ]
        if ctx.draw_choice("mixed_reflection", (False, True)):
            shapes = [_reflect(shape) for shape in shapes]
        ctx.draw_rng("shape_assignment").shuffle(shapes)
        return dict(zip(_COLORS, shapes))

    raise ValueError(f"unknown scene_profile: {profile!r}")


def _top_rows(ctx, height, shapes, sample_index):
    max_shape_h = max(_shape_extent(shape)[0] for shape in shapes.values())
    # height>=5 and max_shape_h<=3, so there are at least three legal distinct
    # top rows.  Cycling the blue rank is deliberate lesson scheduling: all
    # four-pair lessons (three demonstrations plus one query) show that color,
    # not vertical rank or grid size, selects the target.  Duplicating top rank
    # means every held-out-query rotation leaves a top-ranked counterexample to
    # the canonical size-conditioned shortcut in the demonstrations.
    legal_tops = range(0, height - max_shape_h + 1)
    selected_tops = sorted(ctx.draw_rng("vertical_positions").sample(legal_tops, 3))
    blue_rank = (0, 1, 2, 0)[sample_index % 4]
    tops = {1: selected_tops[blue_rank]}
    nonblue = [2, 4]
    ctx.draw_rng("vertical_order").shuffle(nonblue)
    remaining_tops = [
        top for rank, top in enumerate(selected_tops) if rank != blue_rank
    ]
    tops.update(zip(nonblue, remaining_tops))
    return tops


def _left_columns(ctx, width, shapes):
    order = list(_COLORS)
    ctx.draw_rng("horizontal_order").shuffle(order)
    shape_widths = [_shape_extent(shapes[color])[1] for color in order]
    slack = width - sum(shape_widths)
    if slack < 0:
        raise ValueError("grid width cannot hold the selected shapes")
    gaps = [0, 0, 0, 0]
    gap_rng = ctx.draw_rng("horizontal_gaps")
    for _ in range(slack):
        gaps[gap_rng.randrange(len(gaps))] += 1
    lefts = {}
    cursor = gaps[0]
    for index, (color, shape_width) in enumerate(zip(order, shape_widths)):
        lefts[color] = cursor
        cursor += shape_width + gaps[index + 1]
    return lefts


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

    height_anchors = {
        "easy": (5,) * 24 + (10,) * 12,
        "medium": (5,) * 18 + (10,) * 18,
        "hard": (10,) * 24 + (5,) * 12,
        None: (5,) * 18 + (10,) * 18,
    }[difficulty]
    height = _weighted_dimension(ctx, "grid_h", 5, 12, height_anchors)
    width = _weighted_dimension(ctx, "grid_w", 10, 15, (10,) * 42)
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)

    shapes = _profile_shapes(ctx, profile, difficulty)
    tops = _top_rows(ctx, height, shapes, sample_index)
    lefts = _left_columns(ctx, width, shapes)
    grid = full_grid(height, width, 0)
    for color in _COLORS:
        for row_offset, col_offset in shapes[color]:
            row = tops[color] + row_offset
            col = lefts[color] + col_offset
            if grid[row][col] != 0:
                raise RuntimeError("constructive placement collided")
            grid[row][col] = color
    return grid


def _basic_grid_errors(grid) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return ["grid cells must be literal integers in 0..9"]
    return []


def _cells_by_color(grid):
    cells = {}
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value:
                cells.setdefault(value, set()).add((row_index, col_index))
    return cells


def _normalized(cells):
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return frozenset((row - top, col - left) for row, col in cells)


def _is_rectangle(cells) -> bool:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    area = (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)
    return len(cells) == area


def _align_to_top(grid, target_top):
    errors = _basic_grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    height, width = len(grid), len(grid[0])
    by_color = _cells_by_color(grid)
    output = full_grid(height, width, 0)
    for color, cells in by_color.items():
        color_top = min(row for row, _ in cells)
        shift = target_top - color_top
        for row, col in cells:
            new_row = row + shift
            if 0 <= new_row < height:
                output[new_row][col] = color
    return output


def rule_mirror(grid):
    errors = _basic_grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    by_color = _cells_by_color(grid)
    if 1 not in by_color:
        raise ValueError("missing blue(1) anchor")
    blue_top = min(row for row, _ in by_color[1])
    return _align_to_top(grid, blue_top)


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    errors = _basic_grid_errors(grid)
    if errors:
        return errors
    by_color = _cells_by_color(grid)
    if set(by_color) != set(_COLORS):
        errors.append("nonzero palette must be exactly {1, 2, 4}")
        return errors

    extents = {}
    tops = {}
    for color, cells in by_color.items():
        columns = [col for _, col in cells]
        extents[color] = (min(columns), max(columns))
        tops[color] = min(row for row, _ in cells)
    for left_index, left_color in enumerate(_COLORS):
        for right_color in _COLORS[left_index + 1 :]:
            left = extents[left_color]
            right = extents[right_color]
            if not (left[1] < right[0] or right[1] < left[0]):
                errors.append("color column extents must be pairwise disjoint")
                return errors
    if all(top == tops[1] for color, top in tops.items() if color != 1):
        errors.append("all colors are already aligned, so the rule is identity")
        return errors

    try:
        output = rule_mirror(grid)
    except ValueError as exc:
        errors.append(str(exc))
        return errors
    input_count = sum(value != 0 for row in grid for value in row)
    output_count = sum(value != 0 for row in output for value in row)
    if output_count != input_count:
        errors.append("alignment clips cells or creates a collision")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    by_color = _cells_by_color(grid)
    shapes = [_normalized(by_color[color]) for color in _COLORS]
    if len(set(shapes)) == 1:
        profile = (
            "copied_rectangles"
            if all(_is_rectangle(by_color[color]) for color in _COLORS)
            else "copied_irregular"
        )
    else:
        profile = "mixed_shapes"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "scene_profile": profile,
    }


def _identity_rival(grid):
    return deepcopy(grid)


def _highest_rival(grid):
    by_color = _cells_by_color(grid)
    return _align_to_top(grid, min(min(row for row, _ in cells) for cells in by_color.values()))


def _lowest_rival(grid):
    by_color = _cells_by_color(grid)
    return _align_to_top(grid, max(min(row for row, _ in cells) for cells in by_color.values()))


def _median_rival(grid):
    by_color = _cells_by_color(grid)
    tops = sorted(min(row for row, _ in cells) for cells in by_color.values())
    return _align_to_top(grid, tops[len(tops) // 2])


def _canonical_size_rank_rival(grid):
    """Cue-free rule fitting all three canonical demonstrations.

    The sole 10-row demonstration aligns to the lowest-starting object, while
    both 5-row demonstrations align to the median-starting object.  The actual
    rule instead follows blue regardless of size or rank.
    """
    by_color = _cells_by_color(grid)
    tops = sorted(min(row for row, _ in cells) for cells in by_color.values())
    target_top = tops[-1] if len(grid) >= 10 else tops[len(tops) // 2]
    return _align_to_top(grid, target_top)


def _visible_motion(grid) -> bool:
    return rule_mirror(grid) != grid


def _blue_between_extremes(grid) -> bool:
    by_color = _cells_by_color(grid)
    tops = {color: min(row for row, _ in cells) for color, cells in by_color.items()}
    return min(tops.values()) < tops[1] < max(tops.values())


def _blue_not_median(grid) -> bool:
    by_color = _cells_by_color(grid)
    tops = {color: min(row for row, _ in cells) for color, cells in by_color.items()}
    ordered = sorted(tops.values())
    return tops[1] != ordered[len(ordered) // 2]


def _blue_topmost(grid) -> bool:
    by_color = _cells_by_color(grid)
    tops = {color: min(row for row, _ in cells) for color, cells in by_color.items()}
    return tops[1] == min(tops.values())


SEMANTIC_WITNESSES: dict[str, Callable] = {
    "visible_motion": _visible_motion,
    "blue_between_extremes": _blue_between_extremes,
    "blue_not_median": _blue_not_median,
    "blue_topmost": _blue_topmost,
}
SEMANTIC_RIVALS: dict[str, Callable] = {
    "identity": _identity_rival,
    "align_to_highest": _highest_rival,
    "align_to_lowest": _lowest_rival,
    "align_to_median": _median_rival,
    "canonical_size_rank": _canonical_size_rank_rival,
}
WITNESS_RIVALS = {
    "visible_motion": ["identity"],
    "blue_between_extremes": ["align_to_highest", "align_to_lowest"],
    "blue_not_median": ["align_to_median"],
    "blue_topmost": ["canonical_size_rank"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    errors = []
    if len(demos or []) < EXAMPLES_NEEDED:
        errors.append(f"need at least {EXAMPLES_NEEDED} demonstrations")
        return errors
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demo {index} is not a labeled pair")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except ValueError as exc:
            errors.append(f"demo {index} invalid: {exc}")
            continue
        if expected != pair["output"]:
            errors.append(f"demo {index} output disagrees with the selected rule")
    if not isinstance(query, dict) or "input" not in query:
        errors.append("query is missing an input")
        return errors
    try:
        query_answer = rule_mirror(query["input"])
    except ValueError as exc:
        errors.append(f"query invalid: {exc}")
        return errors
    if query.get("output") is not None and query["output"] != query_answer:
        errors.append("query output disagrees with the selected rule")
    if errors:
        return errors

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query_answer:
                errors.append(
                    f"{name} survives every demonstration and changes the query answer"
                )
    return errors
