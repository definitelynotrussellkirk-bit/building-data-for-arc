"""Teach the exact row-and-column blue-endpoint connection rule.

Each generated input contains one clear horizontal pair, one clear vertical
pair, and one blocked pair.  The blocker is deliberately *not* colour 5 so a
lesson distinguishes the canonical-fitting shortcut "only colour 5 blocks"
from the authoritative rule "every nonzero interior cell blocks".

Only inputs are sampled here.  ``rule_mirror`` is an independent Python
reference used by tests and reviewer tooling; the canonical Racket rule remains
the label authority.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "aea1d569d78b"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "5074f7d7c8b5"
SUMMARY = (
    "On a canonical-size canvas, connect exactly two blue endpoints in every "
    "row or column only when all cells strictly between them are background. "
    "Generated lessons contain clear horizontal and vertical positives plus a "
    "non-colour-5 blocked negative witness; easy layouts are separated, medium "
    "layouts mixed, and hard layouts cross the clear pairs."
)
EXAMPLES_NEEDED = 3

CANVAS_PROFILES = {
    "canonical_8x10": (8, 10),
    "canonical_9x8": (9, 8),
    "canonical_9x9": (9, 9),
    "canonical_10x10": (10, 10),
}
BLOCKED_ORIENTATIONS = ("horizontal", "vertical")
BLOCKER_COLORS = (2, 4, 6, 7, 8, 9)
DISTRACTOR_COLORS = (2, 4, 5, 6, 7, 8, 9)

INVARIANTS = [
    "canvas is one of the four canonical dimension profiles",
    "input palette is background 0, blue 1, and two singleton distractor colours",
    "exactly six blue cells form exactly three disjoint endpoint pairs",
    "at least one clear horizontal pair and one clear vertical pair are present",
    "zero or one pair is blocked; generated examples have exactly one non-colour-5 blocker",
    "colour 3 never occurs in an input because the rule writes green",
]

AXES = {
    "canvas_profile": {
        "type": "str",
        "default": "uniform over canonical dimension profiles",
        "valid": "canonical_8x10|canonical_9x8|canonical_9x9|canonical_10x10",
    },
    "blocked_orientation": {
        "type": "str",
        "default": "uniform horizontal|vertical",
        "valid": "horizontal|vertical",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()


def _controls(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    active = {name: value for name, value in overrides.items() if value is not None}
    if "canvas_profile" in active:
        value = active["canvas_profile"]
        if type(value) is not str or value not in CANVAS_PROFILES:
            raise ValueError(
                f"canvas_profile must be one of {tuple(CANVAS_PROFILES)}"
            )
    if "blocked_orientation" in active:
        value = active["blocked_orientation"]
        if type(value) is not str or value not in BLOCKED_ORIENTATIONS:
            raise ValueError(
                f"blocked_orientation must be one of {BLOCKED_ORIENTATIONS}"
            )
    return active


def _grid_errors(grid):
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["grid must be a nonempty rectangular sequence"]
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width for row in grid
    ):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colours 0..9 (not booleans)"]
    return []


def _line_records(grid):
    """Return every row/column containing exactly two blue cells."""
    height, width = len(grid), len(grid[0])
    records = []
    for row in range(height):
        columns = [column for column in range(width) if grid[row][column] == 1]
        if len(columns) == 2:
            start, end = columns
            interior = tuple((row, column) for column in range(start + 1, end))
            records.append(
                {
                    "orientation": "horizontal",
                    "fixed": row,
                    "start": start,
                    "end": end,
                    "endpoints": ((row, start), (row, end)),
                    "interior": interior,
                    "clear": all(grid[r][c] == 0 for r, c in interior),
                }
            )
    for column in range(width):
        rows = [row for row in range(height) if grid[row][column] == 1]
        if len(rows) == 2:
            start, end = rows
            interior = tuple((row, column) for row in range(start + 1, end))
            records.append(
                {
                    "orientation": "vertical",
                    "fixed": column,
                    "start": start,
                    "end": end,
                    "endpoints": ((start, column), (end, column)),
                    "interior": interior,
                    "clear": all(grid[r][c] == 0 for r, c in interior),
                }
            )
    return records


def _analysis(grid):
    records = _line_records(grid)
    blue = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1}
    membership = Counter(cell for record in records for cell in record["endpoints"])
    blocked = [record for record in records if not record["clear"]]
    clear_horizontal = [
        record
        for record in records
        if record["clear"] and record["orientation"] == "horizontal"
    ]
    clear_vertical = [
        record
        for record in records
        if record["clear"] and record["orientation"] == "vertical"
    ]
    return {
        "records": records,
        "blue": blue,
        "membership": membership,
        "blocked": blocked,
        "clear_horizontal": clear_horizontal,
        "clear_vertical": clear_vertical,
    }


def self_check(grid, *, difficulty=None, meta=None):
    errors = _grid_errors(grid)
    if errors:
        return errors

    height, width = len(grid), len(grid[0])
    if (height, width) not in set(CANVAS_PROFILES.values()):
        errors.append("dimensions must match a canonical canvas profile")
    if any(value == 3 for row in grid for value in row):
        errors.append("colour 3 is output-only and may not occur in an input")

    colour_positions = {
        colour: [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == colour]
        for colour in {value for row in grid for value in row if value != 0}
    }
    if len(colour_positions.get(1, ())) != 6:
        errors.append("input must contain exactly six blue endpoint cells")
    distractors = {colour: cells for colour, cells in colour_positions.items() if colour != 1}
    if len(distractors) != 2 or any(len(cells) != 1 for cells in distractors.values()):
        errors.append("input must contain exactly two distinct singleton distractor colours")

    analysis = _analysis(grid)
    records = analysis["records"]
    if len(records) != 3:
        errors.append("six blue cells must induce exactly three row/column endpoint pairs")
    if any(record["end"] - record["start"] < 2 for record in records):
        errors.append("every endpoint pair must have at least one interior cell")
    if analysis["blue"] and any(
        analysis["membership"].get(cell, 0) != 1 for cell in analysis["blue"]
    ):
        errors.append("each blue endpoint must belong to exactly one pair")
    if not analysis["clear_horizontal"]:
        errors.append("at least one clear horizontal pair is required")
    if not analysis["clear_vertical"]:
        errors.append("at least one clear vertical pair is required")
    horizontal_paint = {
        cell for record in analysis["clear_horizontal"] for cell in record["interior"]
    }
    vertical_paint = {
        cell for record in analysis["clear_vertical"] for cell in record["interior"]
    }
    if horizontal_paint and not horizontal_paint - vertical_paint:
        errors.append("horizontal positives need an output cell not supplied by vertical pairs")
    if vertical_paint and not vertical_paint - horizontal_paint:
        errors.append("vertical positives need an output cell not supplied by horizontal pairs")
    if len(analysis["blocked"]) > 1:
        errors.append("at most one endpoint pair may be blocked")
    clear_paint = horizontal_paint | vertical_paint
    for record in analysis["blocked"]:
        nonzero = [grid[r][c] for r, c in record["interior"] if grid[r][c] != 0]
        if not nonzero or any(value in (1, 3) for value in nonzero):
            errors.append("a blocked pair must contain a nonblue, nongreen interior blocker")
        if not any(
            grid[r][c] == 0 and (r, c) not in clear_paint
            for r, c in record["interior"]
        ):
            errors.append("a blocked pair needs an untouched zero cell as a negative witness")
    return errors


def strict_canonical_like(grid):
    """Task-domain ownership, separate from any exact-frequency profile gate."""
    return self_check(grid)


def _segments(height, width, orientation, minimum_gap):
    if orientation == "horizontal":
        return [
            {
                "orientation": orientation,
                "endpoints": ((row, left), (row, right)),
                "interior": tuple((row, column) for column in range(left + 1, right)),
            }
            for row in range(height)
            for left, right in combinations(range(width), 2)
            if right - left >= minimum_gap
        ]
    return [
        {
            "orientation": orientation,
            "endpoints": ((top, column), (bottom, column)),
            "interior": tuple((row, column) for row in range(top + 1, bottom)),
        }
        for column in range(width)
        for top, bottom in combinations(range(height), 2)
        if bottom - top >= minimum_gap
    ]


def _crosses(horizontal, vertical):
    hrow = horizontal["endpoints"][0][0]
    hleft = horizontal["endpoints"][0][1]
    hright = horizontal["endpoints"][1][1]
    vcolumn = vertical["endpoints"][0][1]
    vtop = vertical["endpoints"][0][0]
    vbottom = vertical["endpoints"][1][0]
    return vtop < hrow < vbottom and hleft < vcolumn < hright


def _paint_scene(height, width, horizontal, vertical, blocked, blocker_colour, other_colour, rng):
    endpoints = [
        *horizontal["endpoints"],
        *vertical["endpoints"],
        *blocked["endpoints"],
    ]
    if len(set(endpoints)) != 6:
        return None

    blocker_cells = [cell for cell in blocked["interior"] if cell not in endpoints]
    if len(blocker_cells) < 2:
        return None
    blocker = rng.choice(blocker_cells)

    occupied_spans = set(endpoints)
    occupied_spans.update(horizontal["interior"])
    occupied_spans.update(vertical["interior"])
    occupied_spans.update(blocked["interior"])
    other_candidates = [
        (row, column)
        for row in range(height)
        for column in range(width)
        if (row, column) not in occupied_spans
    ]
    if not other_candidates:
        return None
    other = rng.choice(other_candidates)

    grid = full_grid(height, width, 0)
    for row, column in endpoints:
        grid[row][column] = 1
    grid[blocker[0]][blocker[1]] = blocker_colour
    grid[other[0]][other[1]] = other_colour
    return grid


def _random_scene(height, width, blocked_orientation, blocker_colour, other_colour, rng, crossing):
    horizontal_segments = _segments(height, width, "horizontal", 2)
    vertical_segments = _segments(height, width, "vertical", 2)
    blocked_segments = _segments(height, width, blocked_orientation, 3)

    for _ in range(800):
        horizontal = rng.choice(horizontal_segments)
        if crossing:
            candidates = [
                vertical
                for vertical in vertical_segments
                if _crosses(horizontal, vertical)
            ]
            if not candidates:
                continue
            vertical = rng.choice(candidates)
        else:
            vertical = rng.choice(vertical_segments)
            if _crosses(horizontal, vertical):
                continue
        blocked = rng.choice(blocked_segments)
        grid = _paint_scene(
            height,
            width,
            horizontal,
            vertical,
            blocked,
            blocker_colour,
            other_colour,
            rng,
        )
        if grid is None:
            continue
        analysis = _analysis(grid)
        if len(analysis["records"]) != 3:
            continue
        if len(analysis["clear_horizontal"]) != 1:
            continue
        if len(analysis["clear_vertical"]) != 1:
            continue
        if len(analysis["blocked"]) != 1:
            continue
        if analysis["blocked"][0]["orientation"] != blocked_orientation:
            continue
        if any(analysis["membership"].get(cell, 0) != 1 for cell in analysis["blue"]):
            continue
        if has_clear_crossing(grid) != crossing:
            continue
        if self_check(grid):
            continue
        return grid
    return None


def _fallback_scene(height, width, blocked_orientation, blocker_colour, other_colour, crossing):
    grid = full_grid(height, width, 0)
    if crossing and blocked_orientation == "horizontal":
        blue = ((2, 1), (2, width - 2), (1, 3), (height - 3, 3),
                (height - 2, 2), (height - 2, width - 3))
        blocker = (height - 2, 3)
    elif crossing and blocked_orientation == "vertical":
        blue = ((1, 2), (height - 2, 2), (3, 1), (3, width - 3),
                (2, width - 2), (height - 3, width - 2))
        blocker = (3, width - 2)
    elif blocked_orientation == "horizontal":
        blue = ((1, 1), (1, 4), (2, width - 2), (5, width - 2),
                (height - 2, 2), (height - 2, 5))
        blocker = (height - 2, 3)
    else:
        blue = ((1, 1), (4, 1), (height - 2, 2), (height - 2, 5),
                (2, width - 2), (5, width - 2))
        blocker = (3, width - 2)
    for row, column in blue:
        grid[row][column] = 1
    grid[blocker[0]][blocker[1]] = blocker_colour
    grid[height - 1][width - 1] = other_colour
    if self_check(grid):
        raise RuntimeError("internal fallback scene violated generator invariants")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    active = _controls(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=active,
    )
    profile = ctx.draw_choice("canvas_profile", tuple(CANVAS_PROFILES))
    blocked_orientation = ctx.draw_choice(
        "blocked_orientation", BLOCKED_ORIENTATIONS
    )
    height, width = CANVAS_PROFILES[profile]

    palette_rng = ctx.draw_rng("palette")
    blocker_colour = palette_rng.choice(BLOCKER_COLORS)
    other_colour = palette_rng.choice(
        [colour for colour in DISTRACTOR_COLORS if colour != blocker_colour]
    )
    layout_rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        crossing = False
    elif difficulty == "hard":
        crossing = True
    else:
        crossing = bool(ctx.draw_rng("crossing").randrange(2))
    grid = _random_scene(
        height,
        width,
        blocked_orientation,
        blocker_colour,
        other_colour,
        layout_rng,
        crossing,
    )
    if grid is None:
        grid = _fallback_scene(
            height,
            width,
            blocked_orientation,
            blocker_colour,
            other_colour,
            crossing,
        )
    return grid


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("grid is outside the generator domain: " + "; ".join(errors))
    profile = next(
        name for name, dimensions in CANVAS_PROFILES.items()
        if dimensions == (len(grid), len(grid[0]))
    )
    blocked = _analysis(grid)["blocked"]
    return {
        "canvas_profile": profile,
        "blocked_orientation": blocked[0]["orientation"] if blocked else None,
    }


def has_clear_crossing(grid):
    if _grid_errors(grid):
        return False
    analysis = _analysis(grid)
    for horizontal in analysis["clear_horizontal"]:
        h_cells = set(horizontal["interior"])
        for vertical in analysis["clear_vertical"]:
            if h_cells.intersection(vertical["interior"]):
                return True
    return False


def rule_mirror(grid):
    """Independent Python mirror of the canonical row-then-column Racket rule."""
    original = deepcopy(grid)
    output = deepcopy(grid)
    height, width = len(original), len(original[0])
    for row in range(height):
        columns = [column for column in range(width) if original[row][column] == 1]
        if len(columns) == 2:
            left, right = columns
            if all(original[row][column] == 0 for column in range(left + 1, right)):
                for column in range(left + 1, right):
                    output[row][column] = 3
    for column in range(width):
        rows = [row for row in range(height) if original[row][column] == 1]
        if len(rows) == 2:
            top, bottom = rows
            if all(original[row][column] == 0 for row in range(top + 1, bottom)):
                for row in range(top + 1, bottom):
                    output[row][column] = 3
    return output


def _paint_with_policy(grid, *, horizontal, vertical, blocked_by):
    original = deepcopy(grid)
    output = deepcopy(grid)
    height, width = len(original), len(original[0])
    if horizontal:
        for row in range(height):
            columns = [column for column in range(width) if original[row][column] == 1]
            if len(columns) != 2:
                continue
            interior = tuple(range(columns[0] + 1, columns[1]))
            if not any(blocked_by(original[row][column]) for column in interior):
                for column in interior:
                    if original[row][column] == 0:
                        output[row][column] = 3
    if vertical:
        for column in range(width):
            rows = [row for row in range(height) if original[row][column] == 1]
            if len(rows) != 2:
                continue
            interior = tuple(range(rows[0] + 1, rows[1]))
            if not any(blocked_by(original[row][column]) for row in interior):
                for row in interior:
                    if original[row][column] == 0:
                        output[row][column] = 3
    return output


def _only_color_5_blocks(grid):
    return _paint_with_policy(
        grid,
        horizontal=True,
        vertical=True,
        blocked_by=lambda value: value == 5,
    )


def _connect_through_blockers(grid):
    return _paint_with_policy(
        grid,
        horizontal=True,
        vertical=True,
        blocked_by=lambda value: False,
    )


def _horizontal_only(grid):
    return _paint_with_policy(
        grid,
        horizontal=True,
        vertical=False,
        blocked_by=lambda value: value != 0,
    )


def _vertical_only(grid):
    return _paint_with_policy(
        grid,
        horizontal=False,
        vertical=True,
        blocked_by=lambda value: value != 0,
    )


def _identity(grid):
    return deepcopy(grid)


def _non_five_blocked_pair(grid):
    if _grid_errors(grid):
        return False
    blocked = _analysis(grid)["blocked"]
    return len(blocked) == 1 and any(
        grid[row][column] not in (0, 1, 3, 5)
        for row, column in blocked[0]["interior"]
    )


SEMANTIC_WITNESSES = {"blocked_pair": _non_five_blocked_pair}
SEMANTIC_RIVALS = {"only_color_5_blocks": _only_color_5_blocks}
WITNESS_RIVALS = {"blocked_pair": ["only_color_5_blocks"]}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = {
    **SEMANTIC_RIVALS,
    "connect_through_blockers": _connect_through_blockers,
    "horizontal_only": _horizontal_only,
    "vertical_only": _vertical_only,
    "identity": _identity,
}


def lesson_identifiable(demos, query):
    """Finite declared-rival teaching check; no universal uniqueness claim."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"demonstrations do not distinguish declared rival {name}")
    return reasons
