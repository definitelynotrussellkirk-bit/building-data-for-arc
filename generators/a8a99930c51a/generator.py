"""Input generator for H5, the top-strip cyclic color map.

The authoritative Racket rule reads the distinct non-zero colors in row 0 from
left to right and recolors each matching body cell to the next color in that
cycle.  Row 0, background cells, and body colors absent from the strip stay
unchanged.

Generated lessons use compact connected body objects and deliberately break two
shortcuts that fit every labeled canonical pair: cycling colors numerically and
cycling them by first body appearance.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a8a99930c51a"
TASK_ID = GENERATOR_ID
RULE_HASH = "e5c43869717c"
VERSION = "2.0.0"

SUMMARY = (
    "Distinct colors in row 0 define a left-to-right directed cycle. Every body "
    "cell whose color occurs in the strip changes to the next strip color; the "
    "strip, background, and out-of-strip body colors remain unchanged."
)

EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "row 0 contains 3..6 distinct non-zero codes and row 1 is blank",
    "each strip color appears as one connected 3..5-cell body object",
    "0..4 optional cells of one out-of-strip color remain unchanged",
    "the strip cycle differs from numeric order and body-first order",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 7-row core every third index; otherwise weighted 7..14",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 9..11-column core every third index; otherwise weighted 9..16",
        "valid": "9..16",
    },
    "n_codes": {
        "type": "int",
        "default": "canonical core 3; otherwise weighted 3..6",
        "valid": "3..6",
    },
    "cells_per_code": {
        "type": "int",
        "default": "canonical-like 3, with broader 3..5 support",
        "valid": "3..5",
    },
    "n_distractors": {
        "type": "int",
        "default": "canonical core 0; otherwise weighted 0..4",
        "valid": "0..4",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_AXIS_BOUNDS = {
    "grid_h": (7, 14),
    "grid_w": (9, 16),
    "n_codes": (3, 6),
    "cells_per_code": (3, 5),
    "n_distractors": (0, 4),
}
_DIFFICULTIES = {None, "easy", "medium", "hard"}


def _strip_codes(grid):
    return [value for value in grid[0] if value != 0]


def _same_cycle(left, right):
    if len(left) != len(right) or not left:
        return False
    doubled = list(right) + list(right)
    n = len(left)
    return any(list(left) == doubled[start:start + n] for start in range(n))


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a non-negative integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer (not bool)")
    if difficulty not in _DIFFICULTIES or (difficulty is not None and type(difficulty) is not str):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        lo, hi = _AXIS_BOUNDS[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _draw_axis(ctx, name, options):
    lo, hi = _AXIS_BOUNDS[name]
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, tuple(options))


def _default_options(sample_index, difficulty):
    # The periodic core guarantees visible support for all three canonical
    # (height, width, palette-size) profiles in every difficulty band.  Exact
    # overrides always use the full declared domain instead of this schedule.
    if sample_index % 3 == 0:
        return {
            "grid_h": (7,),
            "grid_w": (9, 10, 11),
            "n_codes": (3,),
            "cells_per_code": (3, 3, 3, 4),
            "n_distractors": (0,),
        }
    if difficulty == "easy":
        return {
            "grid_h": (7, 7, 7, 8, 8, 9, 10),
            "grid_w": (9, 9, 10, 10, 11, 11, 12, 13),
            "n_codes": (3, 3, 3, 3, 4, 4, 5, 6),
            "cells_per_code": (3, 3, 3, 3, 4, 5),
            "n_distractors": (0, 0, 0, 0, 1, 2, 3, 4),
        }
    if difficulty == "hard":
        return {
            "grid_h": (7, 8, 9, 10, 11, 12, 13, 14),
            "grid_w": (9, 10, 11, 12, 13, 14, 15, 16),
            "n_codes": (3, 3, 4, 4, 4, 5, 5, 6),
            "cells_per_code": (3, 3, 4, 4, 4, 5),
            "n_distractors": (0, 0, 1, 1, 2, 2, 3, 4),
        }
    # None and explicit medium share the balanced production population.
    return {
        "grid_h": (7, 7, 8, 8, 9, 10, 11, 12, 13, 14),
        "grid_w": (9, 9, 10, 10, 11, 12, 13, 14, 15, 16),
        "n_codes": (3, 3, 3, 4, 4, 4, 5, 6),
        "cells_per_code": (3, 3, 3, 4, 4, 5),
        "n_distractors": (0, 0, 0, 1, 1, 2, 3, 4),
    }


def _non_cyclic_order(values, reference, rng):
    order = list(values)
    rng.shuffle(order)
    if _same_cycle(order, reference):
        order[0], order[1] = order[1], order[0]
    if _same_cycle(order, reference):
        order = list(reversed(reference))
    if _same_cycle(order, reference):  # defensive; n>=3 makes this unreachable
        raise RuntimeError("could not construct a non-cyclic permutation")
    return order


def _body_path(height, width, variant):
    rows = list(range(2, height))
    if variant % 2 == 0:
        path = [
            (r, c)
            for offset, r in enumerate(rows)
            for c in (range(width) if offset % 2 == 0 else range(width - 1, -1, -1))
        ]
    else:
        path = [
            (r, c)
            for c in range(width)
            for r in (rows if c % 2 == 0 else list(reversed(rows)))
        ]
    if variant >= 2:
        path.reverse()
    return path


def _composition(total, parts, rng):
    result = [0] * parts
    for _ in range(total):
        result[rng.randrange(parts)] += 1
    return result


def _segments(path, count, size, rng):
    required = count * size + count - 1
    if required > len(path):
        raise ValueError("requested objects do not fit the body path")
    padding = _composition(len(path) - required, count + 1, rng)
    cursor = padding[0]
    result = []
    for index in range(count):
        result.append(path[cursor:cursor + size])
        cursor += size
        if index + 1 < count:
            cursor += 1 + padding[index + 1]
    if cursor + padding[-1] != len(path):
        raise RuntimeError("internal path partition error")
    return result


def _body_first_order(grid):
    codes = set(_strip_codes(grid))
    seen = []
    for row in grid[1:]:
        for value in row:
            if value in codes and value not in seen:
                seen.append(value)
    return seen


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
    defaults = _default_options(sample_index, difficulty)
    h = _draw_axis(ctx, "grid_h", defaults["grid_h"])
    w = _draw_axis(ctx, "grid_w", defaults["grid_w"])
    n_codes = _draw_axis(ctx, "n_codes", defaults["n_codes"])
    cells_per_code = _draw_axis(ctx, "cells_per_code", defaults["cells_per_code"])
    n_distractors = _draw_axis(ctx, "n_distractors", defaults["n_distractors"])

    grid = full_grid(h, w, 0)
    palette_rng = ctx.draw_rng("palette")
    colors = palette_rng.sample(range(1, 10), n_codes)
    strip_order = _non_cyclic_order(colors, sorted(colors), ctx.draw_rng("strip_order"))
    strip_columns = sorted(ctx.draw_rng("strip_columns").sample(range(w), n_codes))
    for column, color in zip(strip_columns, strip_order):
        grid[0][column] = color

    path_rng = ctx.draw_rng("object_path")
    path = _body_path(h, w, path_rng.randrange(4))
    segments = _segments(path, n_codes, cells_per_code, ctx.draw_rng("object_spacing"))

    # Pick a body first-appearance order that is not a cyclic rotation of the
    # strip.  Segment geometry remains independent of the color assignment.
    segment_rank = sorted(
        range(n_codes),
        key=lambda index: min(r * w + c for r, c in segments[index]),
    )
    body_order = _non_cyclic_order(strip_order, strip_order, ctx.draw_rng("body_order"))
    segment_colors = [None] * n_codes
    for segment_index, color in zip(segment_rank, body_order):
        segment_colors[segment_index] = color
    for cells, color in zip(segments, segment_colors):
        for r, c in cells:
            grid[r][c] = color

    if n_distractors:
        remaining_colors = [color for color in range(1, 10) if color not in set(strip_order)]
        distractor_color = ctx.draw_rng("distractor_color").choice(remaining_colors)
        candidates = [(r, c) for r in range(2, h) for c in range(w) if grid[r][c] == 0]
        chosen = ctx.draw_rng("distractor_positions").sample(candidates, n_distractors)
        for r, c in chosen:
            grid[r][c] = distractor_color

    # These assertions protect the teaching contract at the source rather than
    # relying on probabilistic lesson filtering.
    if _same_cycle(_body_first_order(grid), strip_order):
        raise RuntimeError("body-order shortcut was not refuted")
    if _same_cycle(strip_order, sorted(strip_order)):
        raise RuntimeError("numeric-order shortcut was not refuted")
    return grid


def _connected(points):
    if not points:
        return False
    todo = deque([next(iter(points))])
    seen = set(todo)
    while todo:
        r, c = todo.popleft()
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbor in points and neighbor not in seen:
                seen.add(neighbor)
                todo.append(neighbor)
    return seen == points


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return ["every grid row must be a sequence"]
    width = len(grid[0]) if grid else 0
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be nonempty and rectangular"]
    height = len(grid)
    if not 7 <= height <= 14:
        errors.append(f"grid height must be 7..14; got {height}")
    if not 9 <= width <= 16:
        errors.append(f"grid width must be 9..16; got {width}")
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) must be an integer color 0..9")
                return errors

    codes = _strip_codes(grid)
    if not 3 <= len(codes) <= 6:
        errors.append(f"row 0 must contain 3..6 non-zero codes; got {len(codes)}")
    if len(codes) != len(set(codes)):
        errors.append("row 0 codes must be distinct")
    if height > 1 and any(grid[1]):
        errors.append("row 1 must be blank")
    if errors:
        return errors

    code_set = set(codes)
    for color in codes:
        points = {
            (r, c)
            for r in range(2, height)
            for c in range(width)
            if grid[r][c] == color
        }
        if not 2 <= len(points) <= 5:
            errors.append(f"body color {color} must occupy 2..5 cells; got {len(points)}")
        elif not _connected(points):
            errors.append(f"body color {color} must form one 4-connected object")

    unknown = [
        value
        for row in grid[2:]
        for value in row
        if value != 0 and value not in code_set
    ]
    if len(set(unknown)) > 1:
        errors.append("body may use at most one out-of-strip distractor color")
    if len(unknown) > 4:
        errors.append(f"body may contain at most 4 distractor cells; got {len(unknown)}")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid generated grid: " + "; ".join(errors))
    codes = _strip_codes(grid)
    counts = [
        sum(value == color for row in grid[2:] for value in row)
        for color in codes
    ]
    if len(set(counts)) != 1:
        raise ValueError("cells_per_code is not recoverable because code counts differ")
    code_set = set(codes)
    distractors = sum(
        value != 0 and value not in code_set
        for row in grid[2:]
        for value in row
    )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_codes": len(codes),
        "cells_per_code": counts[0],
        "n_distractors": distractors,
    }


def _solve_strip(grid):
    codes = _strip_codes(grid)
    if not codes:
        return [list(row) for row in grid]
    mapping = {value: codes[(index + 1) % len(codes)] for index, value in enumerate(codes)}
    return [
        list(row) if r == 0 else [mapping.get(value, value) for value in row]
        for r, row in enumerate(grid)
    ]


def _solve_numeric_successor(grid):
    codes = sorted(_strip_codes(grid))
    if not codes:
        return [list(row) for row in grid]
    mapping = {value: codes[(index + 1) % len(codes)] for index, value in enumerate(codes)}
    return [
        list(row) if r == 0 else [mapping.get(value, value) for value in row]
        for r, row in enumerate(grid)
    ]


def _solve_body_first_successor(grid):
    strip = _strip_codes(grid)
    code_set = set(strip)
    order = []
    for row in grid[1:]:
        for value in row:
            if value in code_set and value not in order:
                order.append(value)
    order.extend(value for value in strip if value not in order)
    if not order:
        return [list(row) for row in grid]
    mapping = {value: order[(index + 1) % len(order)] for index, value in enumerate(order)}
    return [
        list(row) if r == 0 else [mapping.get(value, value) for value in row]
        for r, row in enumerate(grid)
    ]


def _witness_numeric(grid):
    return not self_check(grid) and False or _solve_numeric_successor(grid) != _solve_strip(grid)


def _witness_body_order(grid):
    return not self_check(grid) and False or _solve_body_first_successor(grid) != _solve_strip(grid)


SEMANTIC_RIVALS = {
    "numeric_successor": _solve_numeric_successor,
    "body_first_successor": _solve_body_first_successor,
}
WITNESS_RIVALS = {
    "non_numeric_strip_cycle": ("numeric_successor",),
    "body_order_disagrees": ("body_first_successor",),
}
SEMANTIC_WITNESSES = {
    "non_numeric_strip_cycle": _witness_numeric,
    "body_order_disagrees": _witness_body_order,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    reasons = []
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                competitor(pair["input"]) == pair["output"]
                for pair in demos
            )
            changes_query = competitor(query["input"]) != query["output"]
        except Exception as exc:  # preserve a short diagnostic for malformed lessons
            reasons.append(f"{name} could not be scored: {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
