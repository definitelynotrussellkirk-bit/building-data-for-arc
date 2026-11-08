"""Generator for bank task ce088a50599a:M158 / e1be962ccf97.

Gray walls divide the grid into chambers.  The unique chamber containing the
most red seeds has each of its background cells filled with cyan.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "e1be962ccf97"
VERSION = "4.0.0"
TASK_ID = "e1be962ccf97"
RULE_HASH = "c005ef0ac3d3"

SUMMARY = (
    "Place one full gray row, one full gray column, or their intersection as "
    "walls. Scatter red seeds in the resulting two or four chambers with one "
    "strict count winner. Fill only that chamber's black cells with cyan."
)

INVARIANTS = [
    "input colors are 0, 2, and 5",
    "one full gray row, one full gray column, or both form every wall cell",
    "the walls create exactly two or four rectangular chambers",
    "exactly one chamber has the largest red-seed count",
    "the winning chamber contains 3..7 red seeds",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 9..22",
        "valid": "9..22",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 9..22",
        "valid": "9..22",
    },
    "layout_kind": {
        "type": "str",
        "default": "rng horizontal|vertical|cross",
        "valid": "horizontal|vertical|cross",
    },
    "winner_count": {
        "type": "int",
        "default": "difficulty-aware rng 3..7",
        "valid": "3..7",
    },
}

_VALID_H = (9, 22)
_VALID_W = (9, 22)
_VALID_WINNER_COUNT = (3, 7)
_LAYOUT_KINDS = ("horizontal", "vertical", "cross")
_PROFILE_PRIOR = 0.08
_CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Height, width, divider row, divider column, then red counts in
# top-left/top-right/bottom-left/bottom-right reading order.
_PROFILE_SPECS = (
    (11, 11, 7, 4, (3, 2, 4, 2)),
    (11, 11, 7, 7, (0, 2, 3, 4)),
    (11, 11, 6, 6, (0, 3, 2, 2)),
    (11, 11, 7, 7, (2, 4, 3, 2)),
    (11, 11, 5, 6, (3, 4, 1, 2)),
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in ("grid_h", "grid_w", "winner_count"):
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} must be an integer")
    layout_kind = overrides.get("layout_kind")
    if layout_kind is not None and type(layout_kind) is not str:
        raise ValueError("layout_kind must be a string")


def _coerce_grid(grid):
    return [
        [
            int(value)
            if isinstance(value, str) and value.isdigit()
            else value
            for value in row
        ]
        for row in grid
    ]


def _components_without_walls(grid):
    h = len(grid)
    w = len(grid[0]) if grid else 0
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 5
    }
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in _CARDINALS:
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        components.append(tuple(sorted(cells)))
    return tuple(sorted(components, key=lambda cells: cells[0]))


def _layout_kind(divider_rows, divider_cols):
    if len(divider_rows) == 1 and len(divider_cols) == 1:
        return "cross"
    if len(divider_rows) == 1 and not divider_cols:
        return "horizontal"
    if not divider_rows and len(divider_cols) == 1:
        return "vertical"
    return "invalid"


def _analyze_scene(grid):
    grid = _coerce_grid(grid)
    h = len(grid)
    w = len(grid[0]) if grid else 0
    rectangular = bool(grid) and all(len(row) == w for row in grid)
    if not rectangular:
        return {
            "grid": grid,
            "h": h,
            "w": w,
            "divider_rows": (),
            "divider_cols": (),
            "layout_kind": "invalid",
            "components": (),
            "red_counts": (),
            "winner_indices": (),
        }
    divider_rows = tuple(
        r
        for r in range(h)
        if all(grid[r][c] == 5 for c in range(w))
    )
    divider_cols = tuple(
        c
        for c in range(w)
        if all(grid[r][c] == 5 for r in range(h))
    )
    components = _components_without_walls(grid)
    red_counts = tuple(
        sum(grid[r][c] == 2 for r, c in cells)
        for cells in components
    )
    max_count = max(red_counts, default=-1)
    winner_indices = tuple(
        index
        for index, count in enumerate(red_counts)
        if count == max_count
    )
    return {
        "grid": grid,
        "h": h,
        "w": w,
        "divider_rows": divider_rows,
        "divider_cols": divider_cols,
        "layout_kind": _layout_kind(divider_rows, divider_cols),
        "components": components,
        "red_counts": red_counts,
        "winner_indices": winner_indices,
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not all(isinstance(row, (list, str)) and row for row in grid):
        return ["grid rows must be non-empty lists or digit strings"]
    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return ["grid must be rectangular"]

    errors = []
    h = len(coerced)
    w = width
    if not (_VALID_H[0] <= h <= _VALID_H[1]):
        errors.append("grid height must be in 9..22")
    if not (_VALID_W[0] <= w <= _VALID_W[1]):
        errors.append("grid width must be in 9..22")
    if any(
        type(value) is not int or value not in (0, 2, 5)
        for row in coerced
        for value in row
    ):
        errors.append("input values must be integer colors 0, 2, or 5")

    scene = _analyze_scene(coerced)
    if scene["layout_kind"] == "invalid":
        errors.append(
            "walls must be one full row, one full column, or one of each"
        )
    expected_walls = {
        (r, c)
        for r in scene["divider_rows"]
        for c in range(w)
    } | {
        (r, c)
        for c in scene["divider_cols"]
        for r in range(h)
    }
    actual_walls = {
        (r, c)
        for r, row in enumerate(coerced)
        for c, value in enumerate(row)
        if value == 5
    }
    if actual_walls != expected_walls:
        errors.append("every gray cell must belong to a complete divider")
    if any(
        divider < 3 or divider > length - 4
        for dividers, length in (
            (scene["divider_rows"], h),
            (scene["divider_cols"], w),
        )
        for divider in dividers
    ):
        errors.append("every divider must leave at least three cells per side")

    expected_components = 4 if scene["layout_kind"] == "cross" else 2
    if len(scene["components"]) != expected_components:
        errors.append(
            f"wall layout must create exactly {expected_components} chambers"
        )
    if len(scene["winner_indices"]) != 1:
        errors.append("exactly one chamber must have the most red seeds")
    elif not (
        _VALID_WINNER_COUNT[0]
        <= scene["red_counts"][scene["winner_indices"][0]]
        <= _VALID_WINNER_COUNT[1]
    ):
        errors.append("winning chamber must contain 3..7 red seeds")
    return errors


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    winner_index = scene["winner_indices"][0]
    return {
        "grid_h": scene["h"],
        "grid_w": scene["w"],
        "layout_kind": scene["layout_kind"],
        "winner_count": scene["red_counts"][winner_index],
    }


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    output = [row[:] for row in scene["grid"]]
    winner = scene["components"][scene["winner_indices"][0]]
    for r, c in winner:
        if output[r][c] == 0:
            output[r][c] = 8
    return output


def canonical_profile_signature(grid):
    if self_check(grid):
        return None
    scene = _analyze_scene(grid)
    return (
        scene["h"],
        scene["w"],
        scene["divider_rows"],
        scene["divider_cols"],
        scene["red_counts"],
    )


def _profile_signature(profile):
    h, w, divider_row, divider_col, red_counts = profile
    return (
        h,
        w,
        (divider_row,),
        (divider_col,),
        tuple(red_counts),
    )


_CANONICAL_PROFILE_SIGNATURES = frozenset(
    _profile_signature(profile) for profile in _PROFILE_SPECS
)


def is_canonical_profile(grid):
    return canonical_profile_signature(grid) in _CANONICAL_PROFILE_SIGNATURES


def _chambers(h, w, divider_rows, divider_cols):
    row_edges = (-1, *divider_rows, h)
    col_edges = (-1, *divider_cols, w)
    return tuple(
        tuple(
            (r, c)
            for r in range(row_edges[row_index] + 1, row_edges[row_index + 1])
            for c in range(
                col_edges[col_index] + 1,
                col_edges[col_index + 1],
            )
        )
        for row_index in range(len(row_edges) - 1)
        for col_index in range(len(col_edges) - 1)
    )


def _paint_scene(h, w, divider_rows, divider_cols, red_counts, rng):
    grid = full_grid(h, w, 0)
    for r in divider_rows:
        for c in range(w):
            grid[r][c] = 5
    for c in divider_cols:
        for r in range(h):
            grid[r][c] = 5
    chambers = _chambers(h, w, divider_rows, divider_cols)
    if len(chambers) != len(red_counts):
        raise ValueError("red count vector does not match the wall layout")
    for cells, count in zip(chambers, red_counts):
        if type(count) is not int or count < 0 or count > len(cells):
            raise ValueError("red count does not fit its chamber")
        for r, c in rng.sample(cells, count):
            grid[r][c] = 2
    return grid


def _draw_profile(profile, rng):
    h, w, divider_row, divider_col, red_counts = profile
    return _paint_scene(
        h,
        w,
        (divider_row,),
        (divider_col,),
        red_counts,
        rng,
    )


def _draw_general(h, w, layout_kind, winner_count, rng):
    divider_rows = (
        (rng.randint(3, h - 4),)
        if layout_kind in ("horizontal", "cross")
        else ()
    )
    divider_cols = (
        (rng.randint(3, w - 4),)
        if layout_kind in ("vertical", "cross")
        else ()
    )
    chamber_count = 4 if layout_kind == "cross" else 2
    winner_index = rng.randrange(chamber_count)
    red_counts = [
        rng.randint(0, winner_count - 1)
        for _ in range(chamber_count)
    ]
    red_counts[winner_index] = winner_count
    return _paint_scene(
        h,
        w,
        divider_rows,
        divider_cols,
        tuple(red_counts),
        rng,
    )


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
    band = difficulty or "medium"
    has_override = any(overrides.get(label) is not None for label in AXES)
    profile = None
    if not has_override:
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _PROFILE_PRIOR:
            profile_index = ctx.draw_choice(
                f"canonical_form|{band}",
                tuple(range(len(_PROFILE_SPECS))),
            )
            profile = _PROFILE_SPECS[profile_index]

    if profile is not None:
        h, w, _divider_row, _divider_col, red_counts = profile
        ctx.draw_int("grid_h", h, h)
        ctx.draw_int("grid_w", w, w)
        ctx.draw_choice("layout_kind", ("cross",))
        ctx.draw_int("winner_count", max(red_counts), max(red_counts))
        grid = _draw_profile(profile, ctx.draw_rng("layout"))
    else:
        if overrides.get("grid_h") is not None:
            h = ctx.draw_int("grid_h", *_VALID_H)
        else:
            h = ctx.draw_int(
                "grid_h",
                *{
                    "easy": (9, 13),
                    "medium": (10, 17),
                    "hard": (14, 22),
                }[band],
            )
        if overrides.get("grid_w") is not None:
            w = ctx.draw_int("grid_w", *_VALID_W)
        else:
            w = ctx.draw_int(
                "grid_w",
                *{
                    "easy": (9, 13),
                    "medium": (10, 17),
                    "hard": (14, 22),
                }[band],
            )
        layout_kind = ctx.draw_choice("layout_kind", _LAYOUT_KINDS)
        if overrides.get("winner_count") is not None:
            winner_count = ctx.draw_int(
                "winner_count",
                *_VALID_WINNER_COUNT,
            )
        else:
            winner_count = ctx.draw_int(
                "winner_count",
                *{
                    "easy": (3, 4),
                    "medium": (3, 6),
                    "hard": (4, 7),
                }[band],
            )
        grid = _draw_general(
            h,
            w,
            layout_kind,
            winner_count,
            ctx.draw_rng("layout"),
        )

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
