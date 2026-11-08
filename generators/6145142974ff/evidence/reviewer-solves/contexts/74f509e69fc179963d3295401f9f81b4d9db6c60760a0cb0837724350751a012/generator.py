"""Generator for Shape Match with Majority-Key Recolor (6145142974ff).

The color-1 component is an exact translation-only shape template.  Color-3
components matching that normalized shape are selected; nonmatching green
components are counterexamples, not decoration.  The selected components are
painted on an otherwise blank output using the most frequent non-{1,3} marker
color, with ties broken by the larger color exactly as the Racket authority does.
"""
from __future__ import annotations

from collections import Counter
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6145142974ff"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "d5061c3b9df5"

SUMMARY = (
    "A color-1 polyomino is the translation-only template. One or two color-3 "
    "components match it exactly, while one or two green distractors include a "
    "same-area wrong shape. Isolated key cells in 2-3 other colors have one "
    "strictly repeated majority. The output is blank except that exactly the "
    "matching green components are recolored to that majority key color."
)

INVARIANTS = [
    "background is color 0 and the grid is 10..16 by 12..18",
    "exactly one recognized multi-cell color-1 template is present",
    "ordinary draws contain 1-2 matching and 1-2 nonmatching color-3 components",
    "at least one nonmatching green component has the same cell count as the template",
    "2-3 non-{0,1,3} marker colors occur as isolated singleton components",
    "one marker color occurs 2-3 times and every other marker color occurs once",
    "the authoritative output clears the source scene and paints only exact green matches",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical core plus banded 10..16", "valid": "10..16"},
    "grid_w": {"type": "int", "default": "canonical core plus banded 12..18", "valid": "12..18"},
    "template_shape": {
        "type": "str",
        "default": "band-weighted",
        "valid": "l3|corner3|t4|s4_vertical|s4_horizontal|square4|long_l5|zigzag5",
    },
    "n_matches": {"type": "int", "default": "cyclic 1|2|1", "valid": "1..2"},
    "n_distractors": {"type": "int", "default": "cyclic 1|1|2", "valid": "1..2"},
    "majority_color": {"type": "int", "default": "curriculum palette", "valid": "2|4|5|6|7|8|9"},
    "majority_count": {"type": "int", "default": "2..3", "valid": "2..3"},
    "n_marker_colors": {"type": "int", "default": "2..3", "valid": "2..3"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = ("single_match_low_key", "double_match_low_key", "two_distractors_high_key")

_SHAPES = {
    "l3": ((0, 0), (1, 0), (1, 1)),
    "corner3": ((0, 0), (0, 1), (1, 0)),
    "t4": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "s4_vertical": ((0, 0), (1, 0), (1, 1), (2, 1)),
    "s4_horizontal": ((0, 0), (0, 1), (1, 1), (1, 2)),
    "square4": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "long_l5": ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    "zigzag5": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 2)),
}
_SHAPE_NAMES = tuple(_SHAPES)
_SHAPE_NAME_BY_CELLS = {cells: name for name, cells in _SHAPES.items()}
_SAME_SIZE_DISTRACTOR = {
    "l3": ((0, 0), (0, 1), (0, 2)),
    "corner3": ((0, 0), (1, 0), (2, 0)),
    "t4": _SHAPES["square4"],
    "s4_vertical": _SHAPES["t4"],
    "s4_horizontal": _SHAPES["square4"],
    "square4": _SHAPES["t4"],
    "long_l5": _SHAPES["zigzag5"],
    "zigzag5": _SHAPES["long_l5"],
}
_DIFFERENT_SIZE_DISTRACTOR = ((0, 0), (0, 1))
_MARKER_COLORS = (2, 4, 5, 6, 7, 8, 9)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """A 3-period schedule; every consecutive three demos covers all rivals."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    int_axes = {
        "grid_h": (10, 16),
        "grid_w": (12, 18),
        "n_matches": (1, 2),
        "n_distractors": (1, 2),
        "majority_count": (2, 3),
        "n_marker_colors": (2, 3),
    }
    for name, (lo, hi) in int_axes.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")
    value = overrides.get("majority_color")
    if value is not None:
        if type(value) is not int:
            raise ValueError("majority_color must be an integer")
        if value not in _MARKER_COLORS:
            raise ValueError(f"majority_color must be one of {_MARKER_COLORS}")
    value = overrides.get("template_shape")
    if value is not None:
        if type(value) is not str:
            raise ValueError("template_shape must be a string")
        if value not in _SHAPES:
            raise ValueError(f"template_shape must be one of {_SHAPE_NAMES}")


def _draw_int(ctx, label: str, lo: int, hi: int, default: int) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_choice(label, (default,))


def _draw_choice(ctx, label: str, choices: tuple, defaults: tuple):
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, choices)
    return ctx.draw_choice(label, defaults)


def _default_dimensions(ctx) -> tuple[int, int]:
    # A deterministic canonical-density component guarantees each 20-draw band
    # contains an 11x13 profile without replaying a canonical grid.
    if ctx.sample_index % 5 == 0:
        return 11, 13
    if ctx.difficulty == "easy":
        return (
            ctx.draw_rng("default_grid_h").choice((10, 10, 11, 12)),
            ctx.draw_rng("default_grid_w").choice((12, 13, 13, 14)),
        )
    if ctx.difficulty == "hard":
        return (
            ctx.draw_rng("default_grid_h").choice((12, 13, 14, 15, 16)),
            ctx.draw_rng("default_grid_w").choice((14, 15, 16, 17, 18)),
        )
    return (
        ctx.draw_rng("default_grid_h").randint(10, 14),
        ctx.draw_rng("default_grid_w").randint(12, 16),
    )


def _default_shape_choices(difficulty) -> tuple[str, ...]:
    if difficulty == "easy":
        return ("l3", "corner3", "t4", "s4_horizontal", "square4")
    if difficulty == "hard":
        return ("long_l5", "zigzag5", "t4", "s4_vertical", "square4")
    return _SHAPE_NAMES


def _slot_anchors(height: int, width: int) -> list[tuple[int, int]]:
    rows = (0, height - 6)
    cols = (0, (width - 3) // 2, width - 3)
    return [(r, c) for r in rows for c in cols]


def _paint(grid: list[list[int]], shape: Iterable[tuple[int, int]], anchor: tuple[int, int], color: int) -> None:
    r0, c0 = anchor
    for dr, dc in shape:
        if grid[r0 + dr][c0 + dc] != 0:
            raise RuntimeError("constructive object slots overlapped")
        grid[r0 + dr][c0 + dc] = color


def _default_majority(ctx, profile: str) -> int:
    if ctx.sample_index % 5 == 0:
        return 5
    if profile == "two_distractors_high_key":
        return 9
    return ctx.draw_rng("default_majority_color").choice((2, 4, 5, 6, 7, 8))


def _other_marker_colors(ctx, majority: int, count: int) -> list[int]:
    available = [color for color in _MARKER_COLORS if color != majority]
    chosen: list[int] = []
    # For low-key profiles, a singleton 9 explicitly refutes "choose max color".
    if majority != 9 and count:
        chosen.append(9)
    remaining = [color for color in available if color not in chosen]
    ctx.draw_rng("other_marker_colors").shuffle(remaining)
    chosen.extend(remaining[: count - len(chosen)])
    return chosen


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_w = _default_dimensions(ctx)
    height = _draw_int(ctx, "grid_h", 10, 16, default_h)
    width = _draw_int(ctx, "grid_w", 12, 18, default_w)
    shape_name = _draw_choice(
        ctx,
        "template_shape",
        _SHAPE_NAMES,
        _default_shape_choices(difficulty),
    )
    match_default = 2 if profile == "double_match_low_key" else 1
    distractor_default = 2 if profile == "two_distractors_high_key" else 1
    n_matches = _draw_int(ctx, "n_matches", 1, 2, match_default)
    n_distractors = _draw_int(ctx, "n_distractors", 1, 2, distractor_default)
    majority = _draw_choice(
        ctx,
        "majority_color",
        _MARKER_COLORS,
        (_default_majority(ctx, profile),),
    )
    majority_default = 3 if profile == "double_match_low_key" else 2
    marker_colors_default = 3 if profile == "double_match_low_key" else 2
    majority_count = _draw_int(ctx, "majority_count", 2, 3, majority_default)
    n_marker_colors = _draw_int(ctx, "n_marker_colors", 2, 3, marker_colors_default)

    grid = full_grid(height, width, 0)
    slots = _slot_anchors(height, width)
    ctx.draw_rng("object_slots").shuffle(slots)
    needed = 1 + n_matches + n_distractors
    if needed > len(slots):
        raise RuntimeError("declared object counts exceed constructive slot capacity")

    shape = _SHAPES[shape_name]
    _paint(grid, shape, slots[0], 1)
    cursor = 1
    for _ in range(n_matches):
        _paint(grid, shape, slots[cursor], 3)
        cursor += 1
    _paint(grid, _SAME_SIZE_DISTRACTOR[shape_name], slots[cursor], 3)
    cursor += 1
    if n_distractors == 2:
        _paint(grid, _DIFFERENT_SIZE_DISTRACTOR, slots[cursor], 3)

    other_colors = _other_marker_colors(ctx, majority, n_marker_colors - 1)
    marker_plan = [majority] * majority_count + other_colors
    marker_columns = list(range(0, width, 2))
    if len(marker_plan) > len(marker_columns):
        raise RuntimeError("declared marker counts exceed constructive marker capacity")
    ctx.draw_rng("marker_positions").shuffle(marker_columns)
    ctx.draw_rng("marker_order").shuffle(marker_plan)
    for color, column in zip(marker_plan, marker_columns):
        grid[height - 1][column] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructive generator produced an invalid grid: " + "; ".join(errors))
    return grid


def _grid_shape_errors(grid) -> list[str]:
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
                return ["cells must be integer colors 0..9 (bool is not a color)"]
    return []


def _components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == color}
    result: list[list[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        component: list[tuple[int, int]] = []
        while stack:
            r, c = stack.pop()
            component.append((r, c))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    stack.append(point)
        result.append(sorted(component))
    return sorted(result, key=lambda cells: cells[0])


def _normalized(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _marker_counts(grid: list[list[int]]) -> Counter[int]:
    return Counter(value for row in grid for value in row if value not in (0, 1, 3))


def _analysis(grid) -> dict:
    errors = _grid_shape_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    if not (10 <= height <= 16):
        errors.append("grid height must be in 10..16")
    if not (12 <= width <= 18):
        errors.append("grid width must be in 12..18")

    templates = _components(grid, 1)
    template_shape = None
    if len(templates) != 1:
        errors.append(f"expected exactly one color-1 component, found {len(templates)}")
    else:
        template_cells = _normalized(templates[0])
        template_shape = _SHAPE_NAME_BY_CELLS.get(template_cells)
        if template_shape is None:
            errors.append(f"unrecognized color-1 template shape: {template_cells}")

    greens = _components(grid, 3)
    matches: list[list[tuple[int, int]]] = []
    distractors: list[list[tuple[int, int]]] = []
    if template_shape is not None:
        target = _SHAPES[template_shape]
        for component in greens:
            (matches if _normalized(component) == target else distractors).append(component)
    if not 1 <= len(matches) <= 2:
        errors.append(f"expected 1-2 matching color-3 components, found {len(matches)}")
    if not 0 <= len(distractors) <= 2:
        errors.append(f"expected 0-2 nonmatching color-3 components, found {len(distractors)}")

    counts = _marker_counts(grid)
    if not 2 <= len(counts) <= 3:
        errors.append(f"expected 2-3 marker colors, found {len(counts)}")
    for color in counts:
        if color not in _MARKER_COLORS:
            errors.append(f"illegal marker color {color}")
        if any(len(component) != 1 for component in _components(grid, color)):
            errors.append(f"color-{color} markers must be isolated singleton components")
    majority = None
    if counts:
        majority = max(counts, key=lambda color: (counts[color], color))
        if counts[majority] not in (2, 3):
            errors.append("majority marker count must be 2 or 3")
        if any(count != 1 for color, count in counts.items() if color != majority):
            errors.append("every non-majority marker color must occur exactly once")
        if sum(count == counts[majority] for count in counts.values()) != 1:
            errors.append("marker majority must be strict")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "template_shape": template_shape,
        "matches": matches,
        "distractors": distractors,
        "marker_counts": counts,
        "majority_color": majority,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Accept the canonical domain and the widened candidate-rich curriculum."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe an invalid grid: " + "; ".join(analysis["errors"]))
    counts = analysis["marker_counts"]
    majority = analysis["majority_color"]
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "template_shape": analysis["template_shape"],
        "n_matches": len(analysis["matches"]),
        "n_distractors": len(analysis["distractors"]),
        "majority_color": majority,
        "majority_count": counts[majority],
        "n_marker_colors": len(counts),
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Supplemental Python mirror of the selected Racket authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene: " + "; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    for component in analysis["matches"]:
        for r, c in component:
            output[r][c] = analysis["majority_color"]
    return output


def _rival_recolor_all_green(grid: list[list[int]]) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene")
    output = full_grid(analysis["height"], analysis["width"], 0)
    for component in analysis["matches"] + analysis["distractors"]:
        for r, c in component:
            output[r][c] = analysis["majority_color"]
    return output


def _rival_same_cell_count(grid: list[list[int]]) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene")
    target_size = len(_SHAPES[analysis["template_shape"]])
    output = full_grid(analysis["height"], analysis["width"], 0)
    for component in analysis["matches"] + analysis["distractors"]:
        if len(component) == target_size:
            for r, c in component:
                output[r][c] = analysis["majority_color"]
    return output


def _rival_largest_marker_color(grid: list[list[int]]) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene")
    selected = max(analysis["marker_counts"])
    output = full_grid(analysis["height"], analysis["width"], 0)
    for component in analysis["matches"]:
        for r, c in component:
            output[r][c] = selected
    return output


def _rival_first_match_only(grid: list[list[int]]) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid scene")
    output = full_grid(analysis["height"], analysis["width"], 0)
    if analysis["matches"]:
        for r, c in analysis["matches"][0]:
            output[r][c] = analysis["majority_color"]
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "recolor_all_green": _rival_recolor_all_green,
    "same_cell_count": _rival_same_cell_count,
    "largest_marker_color": _rival_largest_marker_color,
    "first_match_only": _rival_first_match_only,
}
CANONICAL_SHORTCUTS = {
    "recolor_all_green": _rival_recolor_all_green,
    "same_cell_count": _rival_same_cell_count,
    "largest_marker_color": _rival_largest_marker_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _valid_analysis(grid):
    analysis = _analysis(grid)
    return None if analysis["errors"] else analysis


def _witness_nonmatching_green(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis["distractors"] and _rival_recolor_all_green(grid) != rule_mirror(grid))


def _witness_same_size_nonmatch(grid) -> bool:
    analysis = _valid_analysis(grid)
    if not analysis:
        return False
    size = len(_SHAPES[analysis["template_shape"]])
    return any(len(component) == size for component in analysis["distractors"]) and (
        _rival_same_cell_count(grid) != rule_mirror(grid)
    )


def _witness_majority_not_largest(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(
        analysis
        and analysis["majority_color"] != max(analysis["marker_counts"])
        and _rival_largest_marker_color(grid) != rule_mirror(grid)
    )


def _witness_multiple_matches(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and len(analysis["matches"]) == 2 and _rival_first_match_only(grid) != rule_mirror(grid))


SEMANTIC_WITNESSES = {
    "nonmatching_green_component": _witness_nonmatching_green,
    "same_size_wrong_shape": _witness_same_size_nonmatch,
    "majority_is_not_largest_color": _witness_majority_not_largest,
    "multiple_exact_matches": _witness_multiple_matches,
}
WITNESS_RIVALS = {
    "nonmatching_green_component": ["recolor_all_green"],
    "same_size_wrong_shape": ["same_cell_count"],
    "majority_is_not_largest_color": ["largest_marker_color"],
    "multiple_exact_matches": ["first_match_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Name any declared rival that survives all demos but changes the query."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if "output" in query and rival(query["input"]) != query["output"]:
                reasons.append(f"competitor {name!r} fits all demos but changes the query")
    return reasons
