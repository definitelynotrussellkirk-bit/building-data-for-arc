"""Generator for ARC task f84f23e456ac — periodically tile an origin motif.

The input contains a primitive 2-D motif in the upper-left corner and zero
background everywhere else.  The authoritative rule crops the nonzero bounding
box and tiles that exact rectangle over the full output canvas.
"""
from __future__ import annotations

from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f84f23e456ac"
TASK_ID = GENERATOR_ID
VERSION = "3.4.0"
RULE_HASH = "54458840a785"
SUMMARY = (
    "A 6..20 by 6..24 zero-background grid contains a 2..5 by 2..5 motif "
    "whose nonzero bounding box starts at the upper-left corner. Crop that "
    "motif and tile it periodically in both dimensions to fill the output."
)
INVARIANTS = [
    "cells are ARC colors 0..9 and the background is 0",
    "the nonzero bounding box begins at (0, 0) and is 2..5 by 2..5",
    "the motif contains at least one zero and one or two nonzero colors",
    "the motif has no smaller horizontal or vertical period",
    "the canvas is larger than the motif in both dimensions",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
DENSITIES = ("sparse", "dense")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "five canonical height/width/color anchors",
        "valid": "6..20",
    },
    "grid_w": {
        "type": "int",
        "default": "five canonical height/width/color anchors",
        "valid": "6..24",
    },
    "motif_h": {
        "type": "int",
        "default": "three-step difficulty schedule",
        "valid": "2..5",
    },
    "motif_w": {
        "type": "int",
        "default": "three-step schedule including width != 3",
        "valid": "2..5",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "one or two, coupled to canonical profile anchors",
        "valid": "1..2",
    },
    "density": {
        "type": "str",
        "default": "alternating sparse/dense lesson schedule",
        "valid": "sparse|dense",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# All five canonical (height, width, total-color-count) profiles.  The third
# component is represented below as the count of nonzero colors (total - 1).
_CANONICAL_ANCHORS = (
    (8, 9, 2),
    (9, 9, 1),
    (8, 10, 2),
    (10, 12, 2),
    (9, 12, 1),
)
# Thirteen of fifteen slots are exact canonical profiles.  Two explicit range
# sentinels exercise the full declared canvas domain in ordinary generation, so
# the public dimension axes are broad in fact rather than only under overrides.
_SCHEDULED_ANCHORS = (
    _CANONICAL_ANCHORS[0],
    (6, 6, 1),
    _CANONICAL_ANCHORS[1],
    _CANONICAL_ANCHORS[2],
    (20, 24, 2),
    _CANONICAL_ANCHORS[3],
    _CANONICAL_ANCHORS[4],
    _CANONICAL_ANCHORS[0],
    _CANONICAL_ANCHORS[1],
    _CANONICAL_ANCHORS[2],
    _CANONICAL_ANCHORS[3],
    _CANONICAL_ANCHORS[4],
    _CANONICAL_ANCHORS[0],
    _CANONICAL_ANCHORS[2],
    _CANONICAL_ANCHORS[4],
)
_MOTIF_SCHEDULE = {
    "easy": ((2, 3), (3, 2), (2, 4)),
    "medium": ((2, 4), (3, 3), (4, 2)),
    "hard": ((3, 5), (4, 3), (5, 2)),
}
_DENSITY_SCHEDULE = ("sparse", "dense", "sparse")
SCHEDULE_PROFILES = tuple(f"slot_{index}" for index in range(15))


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty in _MOTIF_SCHEDULE:
        return str(difficulty)
    raise ValueError(
        "difficulty must be None, 'easy', 'medium', or 'hard', "
        f"got {difficulty!r}"
    )


def _profile_index(seed: int, sample_index: int) -> int:
    """Rotate the complete profile cycle so cohorts do not share one phase."""
    return (int(sample_index) + int(seed)) % len(SCHEDULE_PROFILES)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Expose the seed-rotated 15-slot profile/motif schedule."""
    _band(difficulty)
    return SCHEDULE_PROFILES[_profile_index(seed, sample_index)]


def _draw_int_axis(ctx, overrides: dict[str, Any], name: str, default: int,
                   lo: int, hi: int) -> int:
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _draw_choice_axis(ctx, overrides: dict[str, Any], name: str, default: str,
                      options: Sequence[str]) -> str:
    if name in overrides and overrides[name] is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (default,))


def _has_vertical_period(motif: Sequence[Sequence[int]], period: int) -> bool:
    return all(
        list(motif[row]) == list(motif[row - period])
        for row in range(period, len(motif))
    )


def _has_horizontal_period(motif: Sequence[Sequence[int]], period: int) -> bool:
    height = len(motif)
    width = len(motif[0])
    return all(
        motif[row][col] == motif[row][col - period]
        for row in range(height)
        for col in range(period, width)
    )


def _is_primitive(motif: Sequence[Sequence[int]]) -> bool:
    height = len(motif)
    width = len(motif[0])
    return not any(_has_vertical_period(motif, p) for p in range(1, height)) \
        and not any(_has_horizontal_period(motif, p) for p in range(1, width))


def _density_label(nonzero_count: int, area: int) -> str:
    return "sparse" if 2 * nonzero_count <= area else "dense"


def _build_motif(
    height: int,
    width: int,
    n_colors: int,
    density: str,
    position_rng,
    color_rng,
) -> list[list[int]]:
    """Construct a varied primitive motif with exact color/density controls.

    One of the two opposite-corner pairs is always nonzero, which pins the
    nonzero bounding box to the full requested rectangle.  The remaining
    support and color placement are sampled, then rejected only when they
    accidentally create a smaller row or column period.  Sampling the support
    size within the requested density class avoids the tiny finite families
    produced by a fixed L-shaped zero guard.
    """
    area = height * width
    colors = color_rng.sample(list(range(1, 10)), n_colors)
    if density == "sparse":
        min_nonzero = max(2, n_colors)
        max_nonzero = area // 2
    else:
        min_nonzero = max(n_colors, area // 2 + 1)
        max_nonzero = area - 1
    target = position_rng.randint(min_nonzero, max_nonzero)

    all_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
    ]
    anchor_pairs = (
        ((0, width - 1), (height - 1, 0)),
        ((0, 0), (height - 1, width - 1)),
    )

    for _attempt in range(128):
        anchors = anchor_pairs[position_rng.randrange(len(anchor_pairs))]
        available = [cell for cell in all_cells if cell not in anchors]
        position_rng.shuffle(available)
        selected = [*anchors, *available[: target - len(anchors)]]
        position_rng.shuffle(selected)

        motif = [[0 for _ in range(width)] for _ in range(height)]
        assigned = list(colors)
        color_rng.shuffle(assigned)
        assigned.extend(
            colors[color_rng.randrange(len(colors))]
            for _ in range(len(selected) - len(assigned))
        )
        color_rng.shuffle(assigned)
        for (row, col), color in zip(selected, assigned):
            motif[row][col] = color

        if _is_primitive(motif):
            return motif

    raise RuntimeError(
        "internal motif construction could not find a primitive sample"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    band = _band(difficulty)
    profile_index = _profile_index(seed, sample_index)
    anchor_h, anchor_w, anchor_colors = _SCHEDULED_ANCHORS[profile_index]
    motif_index = int(sample_index) % 3
    motif_default = _MOTIF_SCHEDULE[band][motif_index]
    density_default = _DENSITY_SCHEDULE[motif_index]

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    height = _draw_int_axis(ctx, overrides, "grid_h", anchor_h, 6, 20)
    width = _draw_int_axis(ctx, overrides, "grid_w", anchor_w, 6, 24)
    motif_h = _draw_int_axis(ctx, overrides, "motif_h", motif_default[0], 2, 5)
    motif_w = _draw_int_axis(ctx, overrides, "motif_w", motif_default[1], 2, 5)
    n_colors = _draw_int_axis(
        ctx, overrides, "n_distinct_colors", anchor_colors, 1, 2
    )
    density = _draw_choice_axis(
        ctx, overrides, "density", density_default, DENSITIES
    )

    motif = _build_motif(
        motif_h,
        motif_w,
        n_colors,
        density,
        ctx.draw_rng("motif_positions"),
        ctx.draw_rng("motif_colors"),
    )
    grid = full_grid(height, width, 0)
    for row in range(motif_h):
        for col in range(motif_w):
            grid[row][col] = motif[row][col]
    return grid


def _grid_shape_errors(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return 0, 0, ["grid rows must be non-empty sequences"]
    height, width = len(grid), len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return height, width, ["grid must be rectangular"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return height, width, ["cells must be literal ARC integers 0..9"]
    return height, width, []


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    height, width, errors = _grid_shape_errors(grid)
    info: dict[str, Any] = {"grid_h": height, "grid_w": width}
    if errors:
        return info, errors
    if not 6 <= height <= 20:
        errors.append(f"grid height must be 6..20, got {height}")
    if not 6 <= width <= 24:
        errors.append(f"grid width must be 6..24, got {width}")

    nonzero = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not nonzero:
        errors.append("grid must contain a nonzero motif")
        return info, errors

    min_row = min(row for row, _ in nonzero)
    min_col = min(col for _, col in nonzero)
    max_row = max(row for row, _ in nonzero)
    max_col = max(col for _, col in nonzero)
    motif_h = max_row - min_row + 1
    motif_w = max_col - min_col + 1
    info.update({"motif_h": motif_h, "motif_w": motif_w})
    if (min_row, min_col) != (0, 0):
        errors.append(
            "nonzero bounding box must begin at the upper-left corner (0, 0)"
        )
    if not 2 <= motif_h <= 5:
        errors.append(f"motif height must be 2..5, got {motif_h}")
    if not 2 <= motif_w <= 5:
        errors.append(f"motif width must be 2..5, got {motif_w}")
    if motif_h >= height or motif_w >= width:
        errors.append("canvas must be larger than the motif in both dimensions")

    motif = [list(row[min_col : max_col + 1]) for row in grid[min_row : max_row + 1]]
    info["motif"] = motif
    if not any(value == 0 for row in motif for value in row):
        errors.append("motif must contain at least one background-zero cell")
    colors = sorted({value for row in motif for value in row if value != 0})
    info["n_distinct_colors"] = len(colors)
    info["colors"] = tuple(colors)
    if not 1 <= len(colors) <= 2:
        errors.append(
            f"motif must contain one or two nonzero colors, got {len(colors)}"
        )
    nonzero_count = sum(value != 0 for row in motif for value in row)
    density = _density_label(nonzero_count, motif_h * motif_w)
    info.update({"nonzero_count": nonzero_count, "density": density})
    if motif_h >= 2 and motif_w >= 2 and not _is_primitive(motif):
        errors.append("motif must have no smaller horizontal or vertical period")
    return info, errors


def observe_overrides(grid: Any) -> dict[str, Any]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {name: info[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _analyse(grid)[1]


def strict_canonical_like(grid: Any) -> list[str]:
    return _analyse(grid)[1]


def rule_mirror(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    motif = info["motif"]
    motif_h = info["motif_h"]
    motif_w = info["motif_w"]
    return [
        [motif[row % motif_h][col % motif_w] for col in range(info["grid_w"])]
        for row in range(info["grid_h"])
    ]


def _rival_identity(grid: Any) -> list[list[int]]:
    return [list(row) for row in grid]


def _rival_horizontal_only(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = full_grid(info["grid_h"], info["grid_w"], 0)
    motif = info["motif"]
    for row in range(info["motif_h"]):
        for col in range(info["grid_w"]):
            out[row][col] = motif[row][col % info["motif_w"]]
    return out


def _rival_vertical_only(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = full_grid(info["grid_h"], info["grid_w"], 0)
    motif = info["motif"]
    for row in range(info["grid_h"]):
        for col in range(info["motif_w"]):
            out[row][col] = motif[row % info["motif_h"]][col]
    return out


def _rival_fixed_motif_width_3(grid: Any) -> list[list[int]]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    fixed_width = 3
    motif = [list(row[:fixed_width]) for row in grid[: info["motif_h"]]]
    return [
        [motif[row % info["motif_h"]][col % fixed_width]
         for col in range(info["grid_w"])]
        for row in range(info["grid_h"])
    ]


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "identity": _rival_identity,
    "horizontal_only": _rival_horizontal_only,
    "vertical_only": _rival_vertical_only,
    "fixed_motif_width_3": _rival_fixed_motif_width_3,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "fixed_motif_width_3": _rival_fixed_motif_width_3,
}


def _rival_differs(grid: Any, name: str) -> bool:
    try:
        return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)
    except Exception:
        return False


def _witness_width_not_three(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and info["motif_w"] != 3


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "repetition_below_motif": lambda grid: _rival_differs(
        grid, "horizontal_only"
    ),
    "repetition_right_of_motif": lambda grid: _rival_differs(
        grid, "vertical_only"
    ),
    "visible_nonidentity_transform": lambda grid: _rival_differs(
        grid, "identity"
    ),
    "motif_width_not_three": _witness_width_not_three,
}
WITNESS_RIVALS = {
    "repetition_below_motif": ["horizontal_only"],
    "repetition_right_of_motif": ["vertical_only"],
    "visible_nonidentity_transform": ["identity"],
    "motif_width_not_three": ["fixed_motif_width_3"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    valid_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output does not match periodic tiling")
            continue
        valid_demos.append(pair)

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
        return reasons
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query malformed: {query_errors[0]}")
        return reasons
    true_query = rule_mirror(query["input"])
    if "output" in query and query["output"] != true_query:
        reasons.append("query output does not match periodic tiling")

    if reasons:
        return reasons
    survivors = []
    for name, competitor in LESSON_COMPETITORS.items():
        if all(
            competitor(pair["input"]) == pair["output"]
            for pair in valid_demos
        ) and competitor(query["input"]) != true_query:
            survivors.append(name)
    if survivors:
        reasons.append(
            f"plausible rival(s) survive all demonstrations: {survivors}"
        )
    return reasons
