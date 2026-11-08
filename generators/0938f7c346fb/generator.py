"""Semantic generator for ARC task 0938f7c346fb.

Five panels encode A, B, RESULT, X, and Y, separated by gray columns.
The unique cellwise operation mapping A and B to RESULT is inferred and then
applied to X and Y.
"""
from __future__ import annotations

import copy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "0938f7c346fb"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "c2d521df026a"
SUMMARY = (
    "Infer the unique color-aware binary operation demonstrated by A, B, and "
    "RESULT, then apply it cellwise to X and Y. Five equal panels are divided "
    "by solid gray separator columns."
)
EXAMPLES_NEEDED = 4

OPS = ("intersection-eq", "xor", "left-minus", "conflict-merge")
PUBLIC_PROFILES = (
    "public_xor",
    "public_conflict_merge",
    "public_intersection_eq",
)
GENERALIZED_PROFILES = tuple(f"generalized_{name.replace('-', '_')}" for name in OPS)
SCENE_PROFILES = PUBLIC_PROFILES + GENERALIZED_PROFILES
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "rng public|generalized operation lesson",
        "valid": "public_xor|public_conflict_merge|public_intersection_eq|generalized_intersection_eq|generalized_xor|generalized_left_minus|generalized_conflict_merge",
        "doc": "complete public panel profile or a uniquely inferred generalized operation",
    },
}
DIFFICULTIES = {None, "default", "easy", "medium", "hard"}
INVARIANTS = [
    "five equal panels are separated by four solid gray columns",
    "operand panels never use gray and conflict red appears only as an operation result",
    "exactly one ordered operation maps A and B to RESULT",
    "the inferred operation applied to X and Y produces a nonempty output",
    "public profiles preserve all three official joint panel layouts under D4",
]

_COLORS = (1, 2, 3, 4, 6, 7, 8)


def _apply(name, left, right):
    height = len(left)
    width = len(left[0])
    output = full_grid(height, width, 0)
    for row in range(height):
        for col in range(width):
            x = left[row][col]
            y = right[row][col]
            if name == "intersection-eq":
                output[row][col] = x if x != 0 and x == y else 0
            elif name == "xor":
                if (x != 0) != (y != 0):
                    output[row][col] = x or y
            elif name == "left-minus":
                output[row][col] = x if x != 0 and y == 0 else 0
            else:
                if x == 0:
                    output[row][col] = y
                elif y == 0 or x == y:
                    output[row][col] = x
                else:
                    output[row][col] = 9
    return output


def _occupancy(cells):
    return tuple(
        tuple(1 if value else 0 for value in row)
        for row in cells
    )


def _rotate(mask):
    return tuple(
        tuple(mask[len(mask) - 1 - row][col] for row in range(len(mask)))
        for col in range(len(mask[0]))
    )


def _reflect(mask):
    return tuple(tuple(reversed(row)) for row in mask)


def _transform(mask, turns, reflected):
    result = tuple(tuple(row) for row in mask)
    if reflected:
        result = _reflect(result)
    for _index in range(turns):
        result = _rotate(result)
    return result


def _paint(mask, color):
    return [
        [color if value else 0 for value in row]
        for row in mask
    ]


_DEMO_A = (
    (1, 1, 0, 0),
    (0, 1, 0, 0),
    (0, 0, 0, 0),
    (0, 0, 0, 0),
)
_DEMO_B = (
    (0, 1, 0, 0),
    (0, 1, 1, 0),
    (0, 0, 0, 0),
    (0, 0, 0, 0),
)
_PUBLIC_QUERIES = {
    "public_xor": (
        (
            (1, 1, 0, 0),
            (0, 1, 0, 0),
            (0, 0, 0, 0),
            (0, 0, 0, 0),
        ),
        (
            (0, 0, 1, 0),
            (0, 0, 1, 0),
            (0, 0, 0, 0),
            (0, 0, 0, 0),
        ),
    ),
    "public_conflict_merge": (
        (
            (1, 0, 0, 0),
            (1, 1, 0, 0),
            (0, 0, 0, 0),
            (0, 0, 0, 0),
        ),
        (
            (0, 1, 0, 0),
            (0, 1, 1, 0),
            (0, 0, 0, 0),
            (0, 0, 0, 0),
        ),
    ),
    "public_intersection_eq": (
        (
            (1, 1, 0, 0),
            (0, 1, 0, 0),
            (0, 0, 1, 0),
            (0, 0, 0, 0),
        ),
        (
            (0, 1, 0, 0),
            (0, 1, 1, 0),
            (0, 0, 0, 0),
            (0, 0, 0, 0),
        ),
    ),
}
_PUBLIC_OP = {
    "public_xor": "xor",
    "public_conflict_merge": "conflict-merge",
    "public_intersection_eq": "intersection-eq",
}


def _public_keys(profile):
    query_left, query_right = _PUBLIC_QUERIES[profile]
    masks = (_DEMO_A, _DEMO_B, query_left, query_right)
    return {
        tuple(_transform(mask, turns, reflected) for mask in masks)
        for turns in range(4)
        for reflected in (False, True)
    }


_PUBLIC_KEYS = {profile: _public_keys(profile) for profile in PUBLIC_PROFILES}


def _split(grid):
    width = len(grid[0])
    panel_width = (width - 4) // 5
    return [
        [
            row[index * (panel_width + 1):index * (panel_width + 1) + panel_width]
            for row in grid
        ]
        for index in range(5)
    ]


def _infer_matches(left, right, result):
    return tuple(name for name in OPS if _apply(name, left, right) == result)


def _classify_profile(operation, panels):
    key = tuple(_occupancy(panel) for panel in (panels[0], panels[1], panels[3], panels[4]))
    for profile in PUBLIC_PROFILES:
        if operation == _PUBLIC_OP[profile] and key in _PUBLIC_KEYS[profile]:
            return profile
    return f"generalized_{operation.replace('-', '_')}"


def _analyze(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty row sequence"], "facts": None}
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return {"errors": ["rows must be nonempty sequences"], "facts": None}
    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"], "facts": None}
    if not 4 <= height <= 6 or (width - 4) % 5 != 0:
        errors.append("grid must contain five equal width panels")
        return {"errors": errors, "facts": None}
    panel_width = (width - 4) // 5
    if not 4 <= panel_width <= 5:
        errors.append("panel width must be 4..5")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
    separators = [index * (panel_width + 1) + panel_width for index in range(4)]
    if any(grid[row][col] != 5 for row in range(height) for col in separators):
        errors.append("all four separator columns must be solid gray")
    panels = _split(grid)
    if any(value == 5 for panel in panels for row in panel for value in row):
        errors.append("gray is reserved for separator columns")
    if errors:
        return {"errors": errors, "facts": None}

    matches = _infer_matches(panels[0], panels[1], panels[2])
    if len(matches) != 1:
        errors.append(f"demo must identify exactly one operation, found {list(matches)}")
    facts = None
    if len(matches) == 1:
        operation = matches[0]
        output = _apply(operation, panels[3], panels[4])
        if not any(value != 0 for row in output for value in row):
            errors.append("query output must be nonempty")
        if not errors:
            facts = {
                "height": height,
                "panel_width": panel_width,
                "operation": operation,
                "scene_profile": _classify_profile(operation, panels),
                "panels": panels,
                "output": output,
                "conflicts": sum(value == 9 for row in output for value in row),
            }
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {"scene_profile": analysis["facts"]["scene_profile"]}


def rule_mirror(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return copy.deepcopy(analysis["facts"]["output"])


def _mask(rng, height, width, density):
    return [
        [1 if rng.random() < density else 0 for _col in range(width)]
        for _row in range(height)
    ]


def _unique_demo(rng, operation, height, width):
    same_color = operation == "intersection-eq"
    for _attempt in range(1000):
        left_mask = _mask(rng, height, width, 0.32)
        right_mask = _mask(rng, height, width, 0.32)
        left_color = rng.choice(_COLORS)
        right_color = left_color if same_color else rng.choice(
            [color for color in _COLORS if color != left_color]
        )
        left = _paint(left_mask, left_color)
        right = _paint(right_mask, right_color)
        result = _apply(operation, left, right)
        if (
            any(value for row in result for value in row)
            and _infer_matches(left, right, result) == (operation,)
        ):
            return left, right, result
    raise RuntimeError(f"could not construct unique {operation} demo")


def _query(rng, operation, height, width):
    same_color = operation == "intersection-eq"
    for _attempt in range(1000):
        left_color = rng.choice(_COLORS)
        right_color = left_color if same_color else rng.choice(
            [color for color in _COLORS if color != left_color]
        )
        left = _paint(_mask(rng, height, width, 0.3), left_color)
        right = _paint(_mask(rng, height, width, 0.3), right_color)
        output = _apply(operation, left, right)
        if any(value for row in output for value in row):
            return left, right
    raise RuntimeError(f"could not construct nonempty {operation} query")


def _assemble(panels):
    height = len(panels[0])
    panel_width = len(panels[0][0])
    grid = full_grid(height, 5 * panel_width + 4, 0)
    for index, panel in enumerate(panels):
        left = index * (panel_width + 1)
        for row in range(height):
            grid[row][left:left + panel_width] = panel[row]
        if index < 4:
            for row in range(height):
                grid[row][left + panel_width] = 5
    return grid


def _public_scene(rng, profile):
    operation = _PUBLIC_OP[profile]
    demo_same = operation in ("xor", "intersection-eq")
    demo_left_color = rng.choice(_COLORS)
    demo_right_color = demo_left_color if demo_same else rng.choice(
        [color for color in _COLORS if color != demo_left_color]
    )
    query_same = operation == "intersection-eq"
    query_left_color = rng.choice(_COLORS)
    query_right_color = query_left_color if query_same else rng.choice(
        [color for color in _COLORS if color != query_left_color]
    )
    query_left, query_right = _PUBLIC_QUERIES[profile]
    panels = [
        _paint(_DEMO_A, demo_left_color),
        _paint(_DEMO_B, demo_right_color),
        None,
        _paint(query_left, query_left_color),
        _paint(query_right, query_right_color),
    ]
    panels[2] = _apply(operation, panels[0], panels[1])
    turns = rng.randrange(4)
    reflected = bool(rng.randrange(2))
    panels = [
        [list(row) for row in _transform(panel, turns, reflected)]
        for panel in panels
    ]
    return _assemble(panels)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    rng = ctx.draw_rng("layout")
    if profile in PUBLIC_PROFILES:
        grid = _public_scene(rng, profile)
    else:
        operation = profile.removeprefix("generalized_").replace("_", "-")
        if difficulty == "hard":
            size = 5
        elif difficulty == "medium":
            size = rng.choice((4, 5))
        elif difficulty in (None, "default"):
            size = rng.choice((4, 5))
        else:
            size = 4
        left, right, result = _unique_demo(rng, operation, size, size)
        query_left, query_right = _query(rng, operation, size, size)
        grid = _assemble((left, right, result, query_left, query_right))
    errors = self_check(grid)
    if errors:
        raise RuntimeError("constructed invalid scene: " + "; ".join(errors))
    return grid
