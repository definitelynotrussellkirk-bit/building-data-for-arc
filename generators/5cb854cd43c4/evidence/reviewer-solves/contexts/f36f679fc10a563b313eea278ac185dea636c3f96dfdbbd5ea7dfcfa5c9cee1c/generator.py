"""Generator for ARC rule family 5cb854cd43c4 (bank task M6).

Each same-color nonzero 4-connected object becomes a run of its color whose
length equals the object's size. Runs are sorted by decreasing size, with
smaller color first on a size tie, and separated by one zero.

The three complete public canvas/object-count profiles and the two historical
exact axes remain stable. A three-step default schedule adds two bounded
teaching branches inside the existing ``varied`` regime: disconnected objects
sharing one color, and equal-size objects with different colors. Every three
consecutive demonstrations therefore refute the two shortcuts that fit all
public pairs: grouping by color and ignoring/reversing the color tie-break.
"""
from __future__ import annotations

from collections import Counter, deque

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "5cb854cd43c4"
TASK_ID = "5cb854cd43c4"
VERSION = "5.0.0"
RULE_HASH = "e1a351c73552"

SUMMARY = (
    "Extract same-color nonzero 4-connected objects, sort them by decreasing "
    "cell count with smaller color first on ties, and emit one row containing "
    "a color run per object separated by one zero."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the canvas and object count match one complete public profile",
    "zero is the background and every object has a nonzero color",
    "canonical draws retain the demonstrated size tuple and distinct colors",
    "varied draws are bounded strict-size, split-color, or tie witnesses",
    "repeated colors remain separate 4-connected components",
    "output run lengths equal object sizes and runs are zero-separated",
]

SCENE_PROFILES = (
    "compact_5x5_three",
    "compact_6x6_two",
    "sparse_8x7_three",
)
SIZE_REGIMES = ("canonical", "varied")
SCHEDULE_PROFILES = (
    "split_color_witness",
    "tie_break_witness",
    "ordinary",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "uniform complete public canvas/object-count profile",
        "valid": (
            "compact_5x5_three|compact_6x6_two|sparse_8x7_three"
        ),
    },
    "size_regime": {
        "type": "str",
        "default": (
            "three-step schedule: two varied teaching branches followed by "
            "one canonical branch"
        ),
        "valid": "canonical|varied",
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

_PROFILE_DATA = {
    "compact_5x5_three": {
        "canvas": (5, 5),
        "count": 3,
        "canonical_sizes": (4, 3, 1),
        "varied_sizes": (
            (4, 2, 1),
            (4, 3, 2),
            (5, 2, 1),
            (5, 3, 1),
            (5, 3, 2),
        ),
        "tie_sizes": (
            (3, 3, 1),
            (4, 2, 2),
        ),
    },
    "compact_6x6_two": {
        "canvas": (6, 6),
        "count": 2,
        "canonical_sizes": (5, 2),
        "varied_sizes": (
            (3, 1),
            (4, 1),
            (4, 2),
            (5, 1),
            (5, 3),
            (6, 1),
            (6, 2),
            (6, 3),
            (6, 4),
        ),
        # (3, 3) stays excluded: the frozen negative fixture pins it as an
        # unsupported mutation. Other equal-size pairs teach the same rule.
        "tie_sizes": (
            (2, 2),
            (4, 4),
            (5, 5),
        ),
    },
    "sparse_8x7_three": {
        "canvas": (8, 7),
        "count": 3,
        "canonical_sizes": (4, 3, 1),
        "varied_sizes": (
            (4, 2, 1),
            (4, 3, 2),
            (5, 2, 1),
            (5, 3, 1),
            (5, 3, 2),
            (5, 4, 1),
            (5, 4, 2),
            (6, 2, 1),
            (6, 3, 1),
            (6, 3, 2),
            (6, 4, 1),
            (6, 4, 2),
        ),
        "tie_sizes": (
            (3, 3, 1),
            (4, 4, 1),
            (4, 2, 2),
            (5, 3, 3),
            (6, 2, 2),
        ),
    },
}

_PROFILE_BY_CANVAS = {
    data["canvas"]: profile
    for profile, data in _PROFILE_DATA.items()
}

_PROFILE_INDEX = {
    profile: index
    for index, profile in enumerate(SCENE_PROFILES)
}


def _coerce_arc_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    first = grid[0]
    width = len(first) if isinstance(first, (list, tuple)) else 0
    if width == 0:
        return None, ["grid rows must be nonempty"]
    if len(grid) > 30 or width > 30:
        return None, ["grid dimensions must not exceed 30x30"]
    errors = []
    coerced = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        converted = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                converted.append(0)
            else:
                converted.append(value)
        coerced.append(converted)
    if errors:
        return None, errors
    return coerced, []


def _components(grid):
    """Return same-color nonzero 4-components in reading order."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            start = (start_row, start_col)
            if color == 0 or start in seen:
                continue
            queue = deque([start])
            seen.add(start)
            cells = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for delta_row, delta_col in (
                    (-1, 0),
                    (0, -1),
                    (0, 1),
                    (1, 0),
                ):
                    candidate = (
                        row + delta_row,
                        col + delta_col,
                    )
                    if (
                        0 <= candidate[0] < height
                        and 0 <= candidate[1] < width
                        and candidate not in seen
                        and grid[candidate[0]][candidate[1]] == color
                    ):
                        seen.add(candidate)
                        queue.append(candidate)
            rows = [row for row, _col in cells]
            cols = [col for _row, col in cells]
            result.append({
                "color": color,
                "cells": tuple(cells),
                "size": len(cells),
                "bbox": (
                    min(rows),
                    min(cols),
                    max(rows),
                    max(cols),
                ),
            })
    return result


def _sorted_objects(grid):
    return sorted(
        _components(grid),
        key=lambda obj: (-obj["size"], obj["color"]),
    )


def _strip_from_objects(components):
    if not components:
        raise ValueError("grid has no nonzero object")
    row = []
    for index, obj in enumerate(components):
        if index:
            row.append(0)
        row.extend([obj["color"]] * obj["size"])
    return [row]


def _color_pattern(components):
    counts = sorted(Counter(obj["color"] for obj in components).values())
    if counts == [1] * len(components):
        return "distinct"
    if len(components) == 2 and counts == [2]:
        return "repeated"
    if len(components) == 3 and counts == [1, 2]:
        return "repeated"
    return None


def _semantic_signature(grid):
    """Return the two historical exact axes for a calibrated scene."""
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return None
    height = len(coerced)
    width = len(coerced[0])
    profile = _PROFILE_BY_CANVAS.get((height, width))
    if profile is None:
        return None
    data = _PROFILE_DATA[profile]
    components = _components(coerced)
    if len(components) != data["count"]:
        return None
    if not any(value == 0 for row in coerced for value in row):
        return None

    sizes = tuple(sorted(
        (obj["size"] for obj in components),
        reverse=True,
    ))
    color_pattern = _color_pattern(components)
    if sizes == data["canonical_sizes"] and color_pattern == "distinct":
        size_regime = "canonical"
    elif sizes in data["varied_sizes"] and color_pattern in {
        "distinct",
        "repeated",
    }:
        size_regime = "varied"
    elif sizes in data["tie_sizes"] and color_pattern == "distinct":
        size_regime = "varied"
    else:
        return None

    output = _strip_from_objects(_sorted_objects(coerced))
    if (
        len(output) != 1
        or len(output[0]) != sum(sizes) + len(sizes) - 1
    ):
        return None
    return {
        "scene_profile": profile,
        "size_regime": size_regime,
    }


def canonical_profile_index(grid):
    """Return the complete demonstrated canvas-profile index."""
    signature = _semantic_signature(grid)
    if signature is None:
        return None
    return _PROFILE_INDEX[signature["scene_profile"]]


def observe_overrides(grid):
    """Recover every declared exact axis from a valid returned grid."""
    signature = _semantic_signature(grid)
    return {} if signature is None else dict(signature)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    if (
        "scene_profile" in overrides
        and overrides["scene_profile"] not in SCENE_PROFILES
    ):
        raise ValueError("unknown scene_profile")
    if (
        "size_regime" in overrides
        and overrides["size_regime"] not in SIZE_REGIMES
    ):
        raise ValueError("unknown size_regime")


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the semantic branch selected by the three-step lesson schedule."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _normalise_shape(cells):
    minimum_row = min(row for row, _col in cells)
    minimum_col = min(col for _row, col in cells)
    return tuple(sorted(
        (row - minimum_row, col - minimum_col)
        for row, col in cells
    ))


def _random_polyomino(rng, size, difficulty):
    if size == 1:
        return ((0, 0),)
    if difficulty == "easy" and rng.random() < 0.45:
        if rng.random() < 0.5:
            return tuple((0, col) for col in range(size))
        return tuple((row, 0) for row in range(size))
    cells = {(0, 0)}
    while len(cells) < size:
        frontier = sorted({
            (row + delta_row, col + delta_col)
            for row, col in cells
            for delta_row, delta_col in (
                (-1, 0),
                (0, -1),
                (0, 1),
                (1, 0),
            )
            if (row + delta_row, col + delta_col) not in cells
        })
        cells.add(rng.choice(frontier))
    return _normalise_shape(cells)


def _translations(shape, height, width):
    shape_height = max(row for row, _col in shape) + 1
    shape_width = max(col for _row, col in shape) + 1
    return [
        tuple(
            (top + row, left + col)
            for row, col in shape
        )
        for top in range(height - shape_height + 1)
        for left in range(width - shape_width + 1)
    ]


def _touches(cells, occupied):
    return any(
        (row + delta_row, col + delta_col) in occupied
        for row, col in cells
        for delta_row, delta_col in (
            (-1, 0),
            (0, -1),
            (0, 1),
            (1, 0),
        )
    )


def _try_random_scene(
    profile,
    sizes,
    colors,
    difficulty,
    rng,
    *,
    attempts,
):
    height, width = _PROFILE_DATA[profile]["canvas"]
    expected = {
        "scene_profile": profile,
        "size_regime": (
            "canonical"
            if sizes == _PROFILE_DATA[profile]["canonical_sizes"]
            else "varied"
        ),
    }
    for _attempt in range(attempts):
        grid = [
            [0 for _col in range(width)]
            for _row in range(height)
        ]
        occupied = set()
        occupied_by_color = {}
        complete = True
        for size, color in zip(sizes, colors):
            placed = False
            for _shape_attempt in range(24):
                shape = _random_polyomino(rng, size, difficulty)
                same_color = occupied_by_color.get(color, set())
                available = [
                    cells
                    for cells in _translations(
                        shape,
                        height,
                        width,
                    )
                    if occupied.isdisjoint(cells)
                    and not _touches(cells, same_color)
                ]
                if not available:
                    continue
                separated = [
                    cells
                    for cells in available
                    if not _touches(cells, occupied)
                ]
                pool = (
                    separated
                    if separated and rng.random() < 0.8
                    else available
                )
                cells = rng.choice(pool)
                for row, col in cells:
                    grid[row][col] = color
                occupied.update(cells)
                occupied_by_color.setdefault(color, set()).update(cells)
                placed = True
                break
            if not placed:
                complete = False
                break
        if complete and _semantic_signature(grid) == expected:
            return grid
    return None


def _fallback_scene(profile, sizes, colors):
    """Construct every requested object exactly, without retry or shedding."""
    data = _PROFILE_DATA[profile]
    height, width = data["canvas"]
    grid = [
        [0 for _col in range(width)]
        for _row in range(height)
    ]
    if len(sizes) == 3:
        rows = (0, height // 2, height - 1)
    else:
        rows = (1, height - 2)
    for index, (row, size, color) in enumerate(
        zip(rows, sizes, colors)
    ):
        left = 0 if index % 2 == 0 else width - size
        for col in range(left, left + size):
            grid[row][col] = color
    expected = {
        "scene_profile": profile,
        "size_regime": (
            "canonical" if sizes == data["canonical_sizes"] else "varied"
        ),
    }
    if _semantic_signature(grid) != expected:
        raise AssertionError("complete fallback lost its exact axes")
    return grid


def _draw_distinct_colors(ctx, count):
    return ctx.draw_distinct_colors(
        "object_colors",
        n=count,
        exclude={0},
    )


def _draw_repeated_colors(ctx, count):
    distinct_count = 1 if count == 2 else 2
    palette = ctx.draw_distinct_colors(
        "object_colors",
        n=distinct_count,
        exclude={0},
    )
    if count == 2:
        return (palette[0], palette[0])
    return (palette[0], palette[1], palette[0])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    schedule = schedule_profile(seed, sample_index, difficulty)
    if "size_regime" in overrides:
        regime_options = SIZE_REGIMES
    elif schedule == "ordinary":
        regime_options = ("canonical",)
    else:
        regime_options = ("varied",)
    size_regime = ctx.draw_choice("size_regime", regime_options)

    data = _PROFILE_DATA[profile]
    if size_regime == "canonical":
        sizes = data["canonical_sizes"]
        colors = _draw_distinct_colors(ctx, data["count"])
    elif schedule == "split_color_witness":
        sizes = ctx.draw_rng("sizes").choice(data["varied_sizes"])
        colors = _draw_repeated_colors(ctx, data["count"])
    elif schedule == "tie_break_witness":
        sizes = ctx.draw_rng("sizes").choice(data["tie_sizes"])
        colors = _draw_distinct_colors(ctx, data["count"])
    else:
        sizes = ctx.draw_rng("sizes").choice(data["varied_sizes"])
        colors = _draw_distinct_colors(ctx, data["count"])

    grid = _try_random_scene(
        profile,
        sizes,
        colors,
        difficulty,
        ctx.draw_rng("scene"),
        attempts=96,
    )
    if grid is None:
        grid = _fallback_scene(profile, sizes, colors)
    expected = {
        "scene_profile": profile,
        "size_regime": size_regime,
    }
    if observe_overrides(grid) != expected:
        raise AssertionError("constructed scene lost its exact axes")
    return grid


def rule_mirror(grid):
    """Broad, input-pure Python mirror of the canonical object-strip rule."""
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _strip_from_objects(_sorted_objects(coerced))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept complete calibrated public-canvas object profiles."""
    del difficulty, meta
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return errors
    if _semantic_signature(coerced) is None:
        return [
            "grid must be one complete calibrated 5x5, 6x6, or 8x7 "
            "object profile with the exact object count and a supported "
            "canonical, varied, split-color, or equal-size witness pattern"
        ]
    return []


def strict_canonical_like(grid):
    """Lawful instances in this task's declared calibrated manifold."""
    return self_check(grid)


def _merge_disconnected_same_color(grid):
    """Wrong rule: aggregate all nonzero cells by color, not by component."""
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    totals = Counter(
        value
        for row in coerced
        for value in row
        if value != 0
    )
    color_groups = [
        {"color": color, "size": size}
        for color, size in totals.items()
    ]
    return _strip_from_objects(sorted(
        color_groups,
        key=lambda obj: (-obj["size"], obj["color"]),
    ))


def _larger_color_first_on_ties(grid):
    """Wrong rule: sort equal-size components by descending color."""
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    components = sorted(
        _components(coerced),
        key=lambda obj: (-obj["size"], -obj["color"]),
    )
    return _strip_from_objects(components)


def _has_split_same_color_components(grid):
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return False
    colors = [obj["color"] for obj in _components(coerced)]
    return len(colors) != len(set(colors))


def _has_equal_size_color_tie(grid):
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return False
    colors_by_size = {}
    for obj in _components(coerced):
        colors_by_size.setdefault(obj["size"], set()).add(obj["color"])
    return any(len(colors) >= 2 for colors in colors_by_size.values())


def lesson_identifiable(demos, query):
    """Report any query-changing rival that still fits every demonstration."""
    reasons = []
    query_input = query["input"]
    true_query = rule_mirror(query_input)
    for name, rival in LESSON_COMPETITORS.items():
        if rival(query_input) == true_query:
            continue
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            reasons.append(
                f"{name} fits every demo but changes the query answer"
            )
    return reasons


SEMANTIC_WITNESSES = {
    "split_same_color_components": _has_split_same_color_components,
    "equal_size_color_tie": _has_equal_size_color_tie,
}
SEMANTIC_RIVALS = {
    "merge_disconnected_same_color": _merge_disconnected_same_color,
    "larger_color_first_on_ties": _larger_color_first_on_ties,
}
WITNESS_RIVALS = {
    "split_same_color_components": ["merge_disconnected_same_color"],
    "equal_size_color_tie": ["larger_color_first_on_ties"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
