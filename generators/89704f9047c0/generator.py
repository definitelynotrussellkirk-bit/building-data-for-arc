"""Semantic generator for ARC task 89704f9047c0.

Four distinct nonzero markers occupy the four corners of an otherwise black
rectangle.  The authoritative rule fills each cell with the marker from its
nearest corner under Manhattan distance.  Distance ties use the canonical
corner order: top-left, top-right, bottom-left, bottom-right.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.palette import random_palette


GENERATOR_ID = "89704f9047c0"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "83dc1de09d53"
EXPECTED_OUTPUT_CODOMAIN = 10_000

SUMMARY = (
    "Fill every cell with the color of its Manhattan-nearest corner marker; "
    "break distance ties in top-left, top-right, bottom-left, bottom-right order."
)

INVARIANTS = [
    "the grid is a nonempty rectangular ARC grid with literal color 0 as background",
    "exactly the four corner cells are nonzero",
    "the four corner markers are pairwise-distinct nonzero colors",
    "the output preserves the input dimensions and uses only the four corner colors",
    "Manhattan-distance ties prefer top-left, then top-right, then bottom-left, then bottom-right",
]

# These are the four linked (height, width, palette-size) profiles demonstrated
# by the canonical train/test set.  The ordinary schedule cycles through all
# four, so every four-demo lesson contains both tie and no-tie cases, square and
# non-square geometry, and both canonical landscape scales.
SCENE_PROFILES = (
    "canonical_5x7",
    "canonical_6x6",
    "canonical_7x9",
    "canonical_8x8",
)
_PROFILE_DIMS = {
    "canonical_5x7": (5, 7),
    "canonical_6x6": (6, 6),
    "canonical_7x9": (7, 9),
    "canonical_8x8": (8, 8),
}
_DIMS_TO_PROFILE = {dims: name for name, dims in _PROFILE_DIMS.items()}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "sample_index cycle over the four canonical linked profiles",
        "valid": "|".join(SCENE_PROFILES),
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[str, ...], ...] = ()
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 4
SCHEDULE_PROFILES = SCENE_PROFILES

# Exact canonical input signatures are retained only to define and kill the
# explicit memorization rival below.  They are never used by the generator or
# authoritative rule to produce correct outputs.
_OFFICIAL_INPUT_SIGNATURES = {
    (5, 7, (2, 3, 4, 6)),
    (6, 6, (1, 7, 8, 2)),
    (7, 9, (9, 4, 3, 1)),
    (8, 8, (5, 2, 7, 8)),
}

# For any sorted four-color set, these permutations expose both numeric-order
# and positional-role interpretations in each four-step lesson window.
_PALETTE_ORDERS = (
    (0, 1, 2, 3),
    (3, 2, 1, 0),
    (1, 3, 0, 2),
    (2, 0, 3, 1),
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the exact four-step lesson schedule to the semantic gate."""
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _corner_values(grid: Any) -> tuple[int, int, int, int]:
    height, width = len(grid), len(grid[0])
    return (
        grid[0][0],
        grid[0][width - 1],
        grid[height - 1][0],
        grid[height - 1][width - 1],
    )


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    if not 2 <= height <= 30:
        errors.append(f"height must be in 2..30, found {height}")
    if not 2 <= width <= 30:
        errors.append(f"width must be in 2..30, found {width}")

    corners = _corner_values(grid)
    if any(value == 0 for value in corners):
        errors.append(f"all four corners must be nonzero markers, found {corners}")
    if len(set(corners)) != 4:
        errors.append(f"corner marker colors must be pairwise distinct, found {corners}")

    corner_cells = {
        (0, 0),
        (0, width - 1),
        (height - 1, 0),
        (height - 1, width - 1),
    }
    dirty = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if (row, col) not in corner_cells and grid[row][col] != 0
    ]
    if dirty:
        row, col, value = dirty[0]
        errors.append(
            f"only corner cells may be nonzero; found color {value} at ({row},{col})"
        )

    profile = _DIMS_TO_PROFILE.get((height, width))
    rank_order: tuple[int, ...] | None = None
    if len(set(corners)) == 4:
        ranks = {value: index for index, value in enumerate(sorted(corners))}
        rank_order = tuple(ranks[value] for value in corners)

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "corners": corners,
        "scene_profile": profile,
        "rank_order": rank_order,
        "has_distance_ties": bool(height % 2 or width % 2),
        "official_input": (height, width, corners) in _OFFICIAL_INPUT_SIGNATURES,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed marker layouts and override drift."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require the exact linked canonical profile set plus the lawful grammar."""
    errors = self_check(grid)
    if errors:
        return errors
    profile = _analysis(grid)["scene_profile"]
    if profile is None:
        height, width = len(grid), len(grid[0])
        return [f"dimensions {height}x{width} are outside the four canonical profiles"]
    return []


def canonical_profile_signature(grid):
    """Return the linked canonical profile name, or None outside it."""
    if self_check(grid):
        return None
    return _analysis(grid)["scene_profile"]


def observe_overrides(grid) -> dict[str, str]:
    """Recover the exact caller-facing semantic axis from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["scene_profile"] is None:
        return {}
    return {"scene_profile": analysis["scene_profile"]}


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests; canonical Racket remains authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))

    height, width = analysis["height"], analysis["width"]
    values = analysis["corners"]
    corner_facts = (
        (0, 0, values[0], 0),
        (0, width - 1, values[1], 1),
        (height - 1, 0, values[2], 2),
        (height - 1, width - 1, values[3], 3),
    )
    return [
        [
            min(
                corner_facts,
                key=lambda fact: (
                    abs(row - fact[0]) + abs(col - fact[1]),
                    fact[3],
                ),
            )[2]
            for col in range(width)
        ]
        for row in range(height)
    ]


def _fill_by_cuts(grid, row_cut: int, col_cut: int) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    height, width = analysis["height"], analysis["width"]
    top_left, top_right, bottom_left, bottom_right = analysis["corners"]
    return [
        [
            (top_left if col < col_cut else top_right)
            if row < row_cut
            else (bottom_left if col < col_cut else bottom_right)
            for col in range(width)
        ]
        for row in range(height)
    ]


def _rival_last_corner_wins_ties(grid):
    """Nearest-corner rule with the opposite tie priority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    height, width = analysis["height"], analysis["width"]
    values = analysis["corners"]
    corner_facts = (
        (0, 0, values[0], 0),
        (0, width - 1, values[1], 1),
        (height - 1, 0, values[2], 2),
        (height - 1, width - 1, values[3], 3),
    )
    return [
        [
            min(
                corner_facts,
                key=lambda fact: (
                    abs(row - fact[0]) + abs(col - fact[1]),
                    -fact[3],
                ),
            )[2]
            for col in range(width)
        ]
        for row in range(height)
    ]


def _rival_fixed_5x7_cuts(grid):
    """Memorize the 5x7 divider positions for every grid size."""
    return _fill_by_cuts(grid, row_cut=3, col_cut=4)


def _rival_height_for_both_axes(grid):
    """Use the height-derived midpoint for both row and column splits."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    cut = (analysis["height"] + 1) // 2
    return _fill_by_cuts(grid, row_cut=cut, col_cut=cut)


def _rival_sort_corner_colors(grid):
    """Assign numerically sorted colors to TL, TR, BL, BR roles."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    height, width = analysis["height"], analysis["width"]
    values = sorted(analysis["corners"])
    proxy = full_grid(height, width, 0)
    proxy[0][0], proxy[0][width - 1], proxy[height - 1][0], proxy[height - 1][width - 1] = values
    return rule_mirror(proxy)


def _rival_canonical_palette_memorizer(grid):
    """Fit only the four official inputs; otherwise echo the TL color globally."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    if analysis["official_input"]:
        return rule_mirror(grid)
    return full_grid(analysis["height"], analysis["width"], analysis["corners"][0])


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "last_corner_wins_ties": _rival_last_corner_wins_ties,
    "fixed_5x7_cuts": _rival_fixed_5x7_cuts,
    "height_for_both_axes": _rival_height_for_both_axes,
    "sort_corner_colors": _rival_sort_corner_colors,
    "canonical_palette_memorizer": _rival_canonical_palette_memorizer,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "canonical_palette_memorizer": _rival_canonical_palette_memorizer,
}


def _valid_analysis(grid):
    analysis = _analysis(grid)
    return analysis if not analysis["errors"] else None


def _witness_tie_case(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis["has_distance_ties"])


def _witness_even_no_tie_case(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and not analysis["has_distance_ties"])


def _witness_landscape_geometry(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis["width"] > analysis["height"])


def _witness_non_numeric_corner_order(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis["rank_order"] != (0, 1, 2, 3))


def _witness_novel_palette_profile(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and not analysis["official_input"])


SEMANTIC_WITNESSES = {
    "odd_dimension_distance_ties": _witness_tie_case,
    "even_dimensions_without_ties": _witness_even_no_tie_case,
    "landscape_width_controls_column_boundary": _witness_landscape_geometry,
    "corner_position_not_numeric_color_order": _witness_non_numeric_corner_order,
    "novel_palette_refutes_canonical_memorization": _witness_novel_palette_profile,
}

WITNESS_RIVALS = {
    "odd_dimension_distance_ties": ["last_corner_wins_ties"],
    "even_dimensions_without_ties": ["fixed_5x7_cuts"],
    "landscape_width_controls_column_boundary": ["height_for_both_axes"],
    "corner_position_not_numeric_color_order": ["sort_corner_colors"],
    "novel_palette_refutes_canonical_memorization": ["canonical_palette_memorizer"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every four-demo lesson to refute the named shortcut family."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    if self_check(query["input"]):
        reasons.append("query input is outside the lawful corner-marker grammar")

    profiles: set[str] = set()
    analyses: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        analysis = _analysis(demo["input"])
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside the lawful corner-marker grammar")
            continue
        if analysis["scene_profile"] is None:
            reasons.append(f"demo {index} is outside the linked canonical profile set")
        else:
            profiles.add(analysis["scene_profile"])
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output is not the nearest-corner rule")
        analyses.append(analysis)

    if profiles != set(SCENE_PROFILES):
        reasons.append(
            "demonstrations do not cover all four linked profiles "
            f"(saw {sorted(profiles)})"
        )
    if analyses and not any(analysis["has_distance_ties"] for analysis in analyses):
        reasons.append("demonstrations never expose the canonical tie priority")
    if analyses and not any(not analysis["has_distance_ties"] for analysis in analyses):
        reasons.append("demonstrations never expose a no-tie geometry")
    if analyses and not any(analysis["width"] > analysis["height"] for analysis in analyses):
        reasons.append("demonstrations never show width controlling the column boundary")
    if analyses and not any(analysis["rank_order"] != (0, 1, 2, 3) for analysis in analyses):
        reasons.append("demonstrations never refute numeric color sorting")
    if analyses and not all(not analysis["official_input"] for analysis in analyses):
        reasons.append("a demonstration reuses an exact official input instead of refuting memorization")

    if analyses and len(analyses) == len(demos):
        for name, competitor in LESSON_COMPETITORS.items():
            if all(competitor(demo["input"]) == demo["output"] for demo in demos):
                reasons.append(f"named competitor survives all demonstrations: {name}")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input; the canonical Racket rule owns output."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")

    scheduled_profile = schedule_profile(seed, sample_index, difficulty)
    effective_overrides = dict(overrides)
    effective_overrides.setdefault("scene_profile", scheduled_profile)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    height, width = _PROFILE_DIMS[profile]
    profile_index = SCENE_PROFILES.index(profile)

    rng = ctx.draw_rng(f"corner-palette:{difficulty or 'medium'}")
    base_colors = sorted(random_palette(rng, 4))
    palette = tuple(base_colors[index] for index in _PALETTE_ORDERS[profile_index])

    # Never emit an exact official input: the generated corpus must contain a
    # direct counterexample to canonical-instance memorization.
    if (height, width, palette) in _OFFICIAL_INPUT_SIGNATURES:
        palette = (palette[1], palette[0], palette[2], palette[3])

    grid = full_grid(height, width, 0)
    grid[0][0] = palette[0]
    grid[0][width - 1] = palette[1]
    grid[height - 1][0] = palette[2]
    grid[height - 1][width - 1] = palette[3]

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": overrides},
    )
    if errors:
        raise ValueError("constructed invalid instance: " + "; ".join(errors))
    return [row[:] for row in grid]
