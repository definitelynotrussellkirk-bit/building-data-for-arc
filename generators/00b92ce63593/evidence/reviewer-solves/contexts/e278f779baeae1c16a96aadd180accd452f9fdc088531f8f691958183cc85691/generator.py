"""Generator for ARC task 00b92ce63593: recolor by column headers.

The first row is a per-column legend.  Row zero clears.  In every later row,
zero remains zero and every non-zero cell becomes the value in row zero at the
same column.  A non-zero cell beneath a zero header is therefore erased.

The canonical demonstrations use only orange (7) body cells and contain no
body cells outside legend columns.  The linked curriculum separates color and
erasure evidence, then duplicates a comprehensive erasure profile so four
demonstrations refute color-only, keep-off-legend, and color-conditioned
erasure shortcuts under every cyclic start and query rotation.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "00b92ce63593"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "6f9bcb74d69f"

SUMMARY = (
    "Row 0 is a sparse per-column legend. It clears in the output. Every "
    "non-zero body cell takes the row-0 value at its own column, including 0 "
    "when no legend is present there. A linked four-example curriculum "
    "separates body-color evidence from erasure evidence and duplicates the "
    "comprehensive erasure case for rotation-safe lessons."
)

INVARIANTS = [
    "background is 0 and colors are integer ARC colors 0..9",
    "row 0 contains 2..4 non-zero cells in distinct colors",
    "every legend column has at least one non-zero body cell",
    "at least one body cell visibly changes under the rule",
    "off-legend body cells, when present, are erased",
    "every four consecutive default examples refute all declared canonical shortcuts",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = (
    "canonical_anchor",
    "color_counterexample",
    "erasure_counterexample_a",
    "erasure_counterexample_b",
)
BODY_POLICIES = ("uniform7", "uniform_other", "mixed")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

AXES = {
    "grid_h": {
        "type": "int",
        "default": "linked four-profile schedule",
        "valid": "5..10",
        "doc": "Grid height. Full range is honored in every difficulty band.",
    },
    "grid_w": {
        "type": "int",
        "default": "linked four-profile schedule",
        "valid": "5..10",
        "doc": "Grid width. Full range is honored in every difficulty band.",
    },
    "n_legend": {
        "type": "int",
        "default": "3 on anchors; 2..4 on scheduled counterexamples",
        "valid": "2..4",
        "doc": "Number of distinct non-zero header cells in row 0.",
    },
    "body_cells": {
        "type": "int",
        "default": "2 on anchors; 1..3 on scheduled counterexamples",
        "valid": "1..4",
        "doc": "Exact number of non-zero body cells in every legend column.",
    },
    "body_colors": {
        "type": "enum",
        "default": "uniform7 on anchors; mixed on counterexamples",
        "valid": ["uniform7", "uniform_other", "mixed"],
        "doc": (
            "Body values are all 7, one shared non-7 color, or a mix of 7 "
            "and a non-7 color. Generated non-7 body colors are disjoint from "
            "header colors."
        ),
    },
    "off_legend": {
        "type": "int",
        "default": "0 on anchor/color-only profiles; 2..4 on erasure profiles",
        "valid": "0..4",
        "doc": "Exact number of non-zero body cells below zero-valued headers.",
    },
}

_INT_BOUNDS = {
    "grid_h": (5, 10),
    "grid_w": (5, 10),
    "n_legend": (2, 4),
    "body_cells": (1, 4),
    "off_legend": (0, 4),
}
_HEADER_COLORS = (1, 2, 3, 4, 5, 6, 8, 9)
_ALL_NONZERO = (1, 2, 3, 4, 5, 6, 7, 8, 9)
_DIFFICULTIES = (None, "easy", "medium", "hard")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the linked profile; seed and band never disturb alternation."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _profile_defaults(sample_index: int, difficulty: str | None) -> dict[str, Any]:
    profile = schedule_profile(0, sample_index, difficulty)
    cycle = int(sample_index) // len(SCHEDULE_PROFILES)
    if profile == "canonical_anchor":
        side = 5 + cycle % 3
        return {
            "grid_h": side,
            "grid_w": side,
            "n_legend": 3,
            "body_cells": 2,
            "body_colors": "uniform7",
            "off_legend": 0,
        }

    band = "medium" if difficulty is None else difficulty
    dimensions = {
        "easy": ((5, 6), (6, 5), (6, 7), (7, 6)),
        "medium": ((7, 8), (8, 7), (8, 9), (9, 8)),
        "hard": ((9, 10), (10, 9), (10, 10), (9, 9)),
    }[band]
    profile_index = SCHEDULE_PROFILES.index(profile)
    height, width = dimensions[(cycle + profile_index - 1) % len(dimensions)]
    off_legend = 0
    if profile.startswith("erasure_counterexample"):
        off_legend = 2 + (cycle + profile_index) % 3
    return {
        "grid_h": height,
        "grid_w": width,
        "n_legend": 2 + (cycle + profile_index) % 3,
        "body_cells": 1 + (cycle + 2 * profile_index) % 3,
        "body_colors": "mixed",
        "off_legend": off_legend,
    }


def _validate_request(difficulty, overrides: dict[str, Any]) -> dict[str, Any]:
    if difficulty not in _DIFFICULTIES:
        raise ValueError(
            f"difficulty must be one of None/easy/medium/hard, got {difficulty!r}"
        )
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    active = {name: value for name, value in overrides.items() if value is not None}
    for name, (low, high) in _INT_BOUNDS.items():
        if name not in active:
            continue
        value = active[name]
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        if not low <= value <= high:
            raise ValueError(f"{name}={value} outside [{low}, {high}]")
    if "body_colors" in active:
        value = active["body_colors"]
        if not isinstance(value, str):
            raise ValueError(
                f"body_colors must be a string, not {type(value).__name__}"
            )
        if value not in BODY_POLICIES:
            raise ValueError(
                f"body_colors={value!r} is not one of {list(BODY_POLICIES)!r}"
            )
    return active


def _draw_int_axis(ctx, overrides, label: str, default: int) -> int:
    low, high = _INT_BOUNDS[label]
    if label in overrides:
        return ctx.draw_int(label, low, high)
    return ctx.draw_int(label, default, default)


def _draw_choice_axis(ctx, overrides, label: str, default: str) -> str:
    if label in overrides:
        return ctx.draw_choice(label, BODY_POLICIES)
    return ctx.draw_choice(label, (default,))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    active = _validate_request(difficulty, overrides)
    defaults = _profile_defaults(sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=active,
    )

    height = _draw_int_axis(ctx, active, "grid_h", defaults["grid_h"])
    width = _draw_int_axis(ctx, active, "grid_w", defaults["grid_w"])
    n_legend = _draw_int_axis(ctx, active, "n_legend", defaults["n_legend"])
    body_cells = _draw_int_axis(ctx, active, "body_cells", defaults["body_cells"])
    body_policy = _draw_choice_axis(
        ctx, active, "body_colors", defaults["body_colors"]
    )
    off_legend = _draw_int_axis(ctx, active, "off_legend", defaults["off_legend"])

    # The advertised Cartesian product is constructive by design:
    # h>=5 supports four cells per legend column; w>=5 and n_legend<=4
    # leave at least one free column with four available off-legend positions.
    layout_rng = ctx.draw_rng("layout")
    palette_rng = ctx.draw_rng("palette")
    color_rng = ctx.draw_rng("body_values")

    grid = full_grid(height, width, 0)
    legend_cols = sorted(layout_rng.sample(range(width), n_legend))
    legend_colors = palette_rng.sample(_HEADER_COLORS, n_legend)
    for col, color in zip(legend_cols, legend_colors):
        grid[0][col] = color

    legend_positions: list[tuple[int, int]] = []
    for col in legend_cols:
        rows = sorted(layout_rng.sample(range(1, height), body_cells))
        legend_positions.extend((row, col) for row in rows)

    legend_set = set(legend_cols)
    off_candidates = [
        (row, col)
        for row in range(1, height)
        for col in range(width)
        if col not in legend_set
    ]
    off_positions = layout_rng.sample(off_candidates, off_legend)
    positions = legend_positions + off_positions

    header_set = set(legend_colors)
    non_header_non7 = [
        color for color in _ALL_NONZERO if color != 7 and color not in header_set
    ]
    if body_policy == "uniform7":
        values = [7] * len(positions)
    elif body_policy == "uniform_other":
        color = color_rng.choice(non_header_non7)
        values = [color] * len(positions)
    else:
        # A mixed board always contains 7 and one non-7 body color.  For two or
        # more off-legend cells, both colors occur off-legend as well.  This
        # breaks shortcuts that make erasure conditional on body color.
        other = color_rng.choice(non_header_non7)
        legend_values = [other if index % 2 == 0 else 7 for index in range(len(legend_positions))]
        off_values = [7 if index % 2 == 0 else other for index in range(len(off_positions))]
        values = legend_values + off_values

    for (row, col), value in zip(positions, values):
        grid[row][col] = value
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the non-degenerate task domain without throwing on bad inputs."""
    del difficulty, meta
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not all(isinstance(row, list) for row in grid):
        return ["every row must be a list"]
    if not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    height = len(grid)
    if not 5 <= height <= 10:
        errors.append(f"grid height {height} not in [5,10]")
    if not 5 <= width <= 10:
        errors.append(f"grid width {width} not in [5,10]")
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(
                    f"cell ({row_index},{col_index}) must be an integer ARC color 0..9"
                )
                return errors

    legend_cols = [col for col, value in enumerate(grid[0]) if value != 0]
    if not 2 <= len(legend_cols) <= 4:
        errors.append(f"row 0 legend size {len(legend_cols)} not in [2,4]")
    legend_colors = [grid[0][col] for col in legend_cols]
    if len(legend_colors) != len(set(legend_colors)):
        errors.append("row 0 legend colors must be distinct")

    body_positions = [
        (row, col)
        for row in range(1, height)
        for col in range(width)
        if grid[row][col] != 0
    ]
    if not body_positions:
        errors.append("body has no non-zero cells")
    for col in legend_cols:
        if not any(grid[row][col] != 0 for row in range(1, height)):
            errors.append(f"legend column {col} has no body witness")
    off_legend = sum(col not in set(legend_cols) for _, col in body_positions)
    if off_legend > 4:
        errors.append(f"off-legend body count {off_legend} exceeds 4")
    if legend_cols and not any(
        grid[row][col] != grid[0][col]
        for row, col in body_positions
        if col in set(legend_cols)
    ):
        errors.append("no body cell visibly changes under its header")
    return errors


def strict_canonical_like(grid, *, difficulty=None, meta=None) -> list[str]:
    """All generated and canonical boards belong to one strict lawful domain."""
    return self_check(grid, difficulty=difficulty, meta=meta)


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every advertised exact control from a generated grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot observe overrides from invalid grid: {errors}")
    height = len(grid)
    width = len(grid[0])
    legend_cols = [col for col, value in enumerate(grid[0]) if value != 0]
    legend_set = set(legend_cols)
    counts = [
        sum(grid[row][col] != 0 for row in range(1, height))
        for col in legend_cols
    ]
    if len(set(counts)) != 1:
        raise ValueError(f"legend columns do not share one body_cells value: {counts}")
    body_values = [
        grid[row][col]
        for row in range(1, height)
        for col in range(width)
        if grid[row][col] != 0
    ]
    unique = set(body_values)
    if unique == {7}:
        body_policy = "uniform7"
    elif len(unique) == 1 and 7 not in unique:
        body_policy = "uniform_other"
    elif len(unique) >= 2:
        body_policy = "mixed"
    else:  # pragma: no cover - self_check already requires body content
        raise ValueError("body color policy is not observable")
    return {
        "grid_h": height,
        "grid_w": width,
        "n_legend": len(legend_cols),
        "body_cells": counts[0],
        "body_colors": body_policy,
        "off_legend": sum(
            grid[row][col] != 0
            for row in range(1, height)
            for col in range(width)
            if col not in legend_set
        ),
    }


def _apply_rule(grid):
    """Small Python mirror used only by executable semantic declarations."""
    out = deepcopy(grid)
    header = list(grid[0])
    out[0] = [0] * len(header)
    for row in range(1, len(grid)):
        for col, value in enumerate(grid[row]):
            out[row][col] = 0 if value == 0 else header[col]
    return out


def _only_color7(grid):
    out = deepcopy(grid)
    header = list(grid[0])
    out[0] = [0] * len(header)
    for row in range(1, len(grid)):
        for col, value in enumerate(grid[row]):
            if value == 7:
                out[row][col] = header[col]
    return out


def _keep_off_legend(grid):
    out = deepcopy(grid)
    header = list(grid[0])
    out[0] = [0] * len(header)
    for row in range(1, len(grid)):
        for col, value in enumerate(grid[row]):
            if value != 0 and header[col] != 0:
                out[row][col] = header[col]
    return out


def _erase_off_legend_non7_only(grid):
    out = deepcopy(grid)
    header = list(grid[0])
    out[0] = [0] * len(header)
    for row in range(1, len(grid)):
        for col, value in enumerate(grid[row]):
            if value == 0:
                out[row][col] = 0
            elif header[col] != 0:
                out[row][col] = header[col]
            elif value != 7:
                out[row][col] = 0
    return out


def _erase_off_legend_7_only(grid):
    out = deepcopy(grid)
    header = list(grid[0])
    out[0] = [0] * len(header)
    for row in range(1, len(grid)):
        for col, value in enumerate(grid[row]):
            if value == 0:
                out[row][col] = 0
            elif header[col] != 0:
                out[row][col] = header[col]
            elif value == 7:
                out[row][col] = 0
    return out


def _has_non7_under_legend(grid) -> bool:
    header = grid[0]
    return any(
        header[col] != 0 and value not in (0, 7)
        for row in grid[1:]
        for col, value in enumerate(row)
    )


def _has_off_legend_body(grid) -> bool:
    header = grid[0]
    return any(
        header[col] == 0 and value != 0
        for row in grid[1:]
        for col, value in enumerate(row)
    )


def _has_orange_off_legend(grid) -> bool:
    header = grid[0]
    return any(
        header[col] == 0 and value == 7
        for row in grid[1:]
        for col, value in enumerate(row)
    )


def _has_non7_off_legend(grid) -> bool:
    header = grid[0]
    return any(
        header[col] == 0 and value not in (0, 7)
        for row in grid[1:]
        for col, value in enumerate(row)
    )


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "only_color7": _only_color7,
    "keep_off_legend": _keep_off_legend,
    "erase_off_legend_non7_only": _erase_off_legend_non7_only,
    "erase_off_legend_7_only": _erase_off_legend_7_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "non7_under_legend": _has_non7_under_legend,
    "off_legend_erasure": _has_off_legend_body,
    "orange_off_legend_erasure": _has_orange_off_legend,
    "non7_off_legend_erasure": _has_non7_off_legend,
}
WITNESS_RIVALS = {
    "non7_under_legend": ("only_color7",),
    "off_legend_erasure": ("keep_off_legend",),
    "orange_off_legend_erasure": ("erase_off_legend_non7_only",),
    "non7_off_legend_erasure": ("erase_off_legend_7_only",),
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report a declared rival that survives demonstrations but changes query."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        survives = all(
            rival(deepcopy(pair["input"])) == pair["output"] for pair in demos
        )
        if survives and rival(deepcopy(query["input"])) != query["output"]:
            reasons.append(
                f"declared rival {name!r} fits every demonstration but changes the query"
            )
    return reasons
