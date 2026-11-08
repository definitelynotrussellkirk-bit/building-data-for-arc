"""Semantic generator for ARC task 78da31e156b0.

Every nonzero input cell is an isolated colored seed.  The Racket authority
copies that color to a five-cell diagonal-X stencil: the seed center plus the
four diagonal neighbors one step away, clipped at the canvas border.

The v2 generator described the center as erased even though every canonical
pair and the selected Racket rule preserve it.  It also declared eight mostly
unconsumed axes.  Version 3 replaces those claims with one exact observable
scene-profile axis and a four-phase lesson schedule whose every consecutive
four draws include an interior multi-seed scene, a clipped boundary scene, a
same-color scene, and a single-seed boundary scene.
"""
from __future__ import annotations

from itertools import combinations
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "78da31e156b0"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "12c615886fb4"

SUMMARY = (
    "On a fresh same-size color-0 canvas, replace every isolated nonzero seed "
    "at (r,c) by a same-color diagonal X containing the center and the four "
    "one-step diagonal neighbors (r±1,c±1); clip only the arms that fall "
    "outside the grid. Every seed is processed independently."
)

INVARIANTS = [
    "background is literal color 0",
    "all nonzero cells are isolated singleton seeds",
    "seed X-footprints are disjoint, so no color overwrite ambiguity is hidden",
    "the output preserves every seed center and adds only its four diagonal arms",
    "diagonal arms clip at borders and corners",
    "the returned grid belongs to one exact observable scene profile",
]

# (height, width, seed_count, distinct_foreground_colors,
#  boundary_seed_count, corner_seed_count)
#
# The first, fifth, ninth positions are interior/multi-color (A); the second,
# sixth, tenth are boundary/multi-color (B); the third, seventh, eleventh are
# same-color multi-seed (C); the fourth, eighth, twelfth are boundary singletons
# (D). Thus every four consecutive sample indexes contain A/B/C/D, including
# across the cyclic boundary. Five profiles match the public canonical
# (height, width, palette-size) signatures exactly.
SCENE_SPECS = {
    "canonical_7x7_two_interior": (7, 7, 2, 2, 0, 0),
    "canonical_8x9_three_corner": (8, 9, 3, 3, 1, 1),
    "same_color_9x12_three": (9, 12, 3, 1, 0, 0),
    "corner_single_5x6": (5, 6, 1, 1, 1, 1),
    "canonical_6x10_two_interior": (6, 10, 2, 2, 0, 0),
    "canonical_8x8_three_edge": (8, 8, 3, 3, 1, 0),
    "same_color_11x15_four": (11, 15, 4, 1, 0, 0),
    "edge_single_10x7": (10, 7, 1, 1, 1, 0),
    "canonical_9x9_three_interior": (9, 9, 3, 3, 0, 0),
    "large_13x16_six_edges": (13, 16, 6, 4, 2, 0),
    "same_color_14x10_five": (14, 10, 5, 1, 0, 0),
    "edge_single_12x12": (12, 12, 1, 1, 1, 0),
}
SCENE_PROFILES = tuple(SCENE_SPECS)
SCHEDULE_PROFILES = SCENE_PROFILES
CANONICAL_PROFILES = frozenset(
    {
        "canonical_7x7_two_interior",
        "canonical_8x9_three_corner",
        "canonical_6x10_two_interior",
        "canonical_8x8_three_edge",
        "canonical_9x9_three_interior",
    }
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic twelve-profile sample-index cycle",
        "valid": "canonical_7x7_two_interior|canonical_8x9_three_corner|same_color_9x12_three|corner_single_5x6|canonical_6x10_two_interior|canonical_8x8_three_edge|same_color_11x15_four|edge_single_10x7|canonical_9x9_three_interior|large_13x16_six_edges|same_color_14x10_five|edge_single_12x12",
    }
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

_CENTER_AND_DIAGONALS = ((0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1))
_DIAGONALS_ONLY = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_CENTER_ONLY = ((0, 0),)
_CARDINAL_PLUS = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))
_FULL_SQUARE = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1))


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _seed_cells(grid) -> list[tuple[int, int, int]]:
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]


def _is_boundary(row: int, col: int, height: int, width: int) -> bool:
    return row in (0, height - 1) or col in (0, width - 1)


def _is_corner(row: int, col: int, height: int, width: int) -> bool:
    return row in (0, height - 1) and col in (0, width - 1)


def _signature(grid) -> tuple[int, int, int, int, int, int]:
    height, width = len(grid), len(grid[0])
    seeds = _seed_cells(grid)
    colors = {color for _, _, color in seeds}
    boundary = sum(_is_boundary(row, col, height, width) for row, col, _ in seeds)
    corners = sum(_is_corner(row, col, height, width) for row, col, _ in seeds)
    return height, width, len(seeds), len(colors), boundary, corners


_SIGNATURE_TO_PROFILE = {spec: profile for profile, spec in SCENE_SPECS.items()}
if len(_SIGNATURE_TO_PROFILE) != len(SCENE_SPECS):
    raise AssertionError("scene profile signatures must be unique")


def _profile_of(grid) -> str | None:
    if _grid_errors(grid):
        return None
    return _SIGNATURE_TO_PROFILE.get(_signature(grid))


def _positions_are_separated(positions: Iterable[tuple[int, int]]) -> bool:
    """Chebyshev distance >=3 keeps both seeds and X footprints disjoint."""
    points = list(positions)
    return all(
        max(abs(row_a - row_b), abs(col_a - col_b)) >= 3
        for (row_a, col_a), (row_b, col_b) in combinations(points, 2)
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, no-op, or rule-hiding seed scenes."""
    errors = _grid_errors(grid)
    if errors:
        return errors

    height, width = len(grid), len(grid[0])
    seeds = _seed_cells(grid)
    if not seeds:
        errors.append("at least one nonzero seed is required")
        return errors

    profile = _profile_of(grid)
    if profile is None:
        errors.append(f"grid signature {_signature(grid)!r} is not a declared scene profile")

    positions = [(row, col) for row, col, _ in seeds]
    for (row_a, col_a), (row_b, col_b) in combinations(positions, 2):
        distance = max(abs(row_a - row_b), abs(col_a - col_b))
        if distance < 2:
            errors.append(
                f"nonzero cells at {(row_a, col_a)} and {(row_b, col_b)} are not isolated singletons"
            )
            break
        if distance < 3:
            errors.append(
                f"diagonal-X footprints overlap for seeds at {(row_a, col_a)} and {(row_b, col_b)}"
            )
            break

    # Every lawful seed must visibly affect at least one cell beyond its center.
    for row, col, _ in seeds:
        visible_arms = sum(
            0 <= row + delta_row < height and 0 <= col + delta_col < width
            for delta_row, delta_col in _DIAGONALS_ONLY
        )
        if visible_arms == 0:
            errors.append(f"seed at {(row, col)} has no visible diagonal arm")
            break

    requested = ((meta or {}).get("overrides") or {}).get("scene_profile")
    if requested is not None and profile != requested:
        errors.append(f"scene profile drifted from {requested!r} to {profile!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The whole declared distribution is the task's singleton-X grammar."""
    return list(self_check(grid))


def canonical_profile_signature(grid):
    profile = _profile_of(grid)
    return profile if profile in CANONICAL_PROFILES else None


def observe_overrides(grid) -> dict[str, str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    profile = _profile_of(grid)
    assert profile is not None
    return {"scene_profile": profile}


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _paint_stencil(
    grid,
    offsets,
    *,
    fixed_color: int | None = None,
    only_first: bool = False,
    ignore_boundary: bool = False,
) -> list[list[int]]:
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    seeds = sorted(_seed_cells(grid))
    if only_first:
        seeds = seeds[:1]
    for row, col, color in seeds:
        if ignore_boundary and _is_boundary(row, col, height, width):
            continue
        paint_color = color if fixed_color is None else fixed_color
        for delta_row, delta_col in offsets:
            next_row, next_col = row + delta_row, col + delta_col
            if 0 <= next_row < height and 0 <= next_col < width:
                output[next_row][next_col] = paint_color
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests; Racket remains output authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _paint_stencil(grid, _CENTER_AND_DIAGONALS)


def _identity(grid):
    return [list(row) for row in grid]


def _omit_center(grid):
    return _paint_stencil(grid, _DIAGONALS_ONLY)


def _center_only(grid):
    return _paint_stencil(grid, _CENTER_ONLY)


def _cardinal_plus(grid):
    return _paint_stencil(grid, _CARDINAL_PLUS)


def _full_square(grid):
    return _paint_stencil(grid, _FULL_SQUARE)


def _fixed_color_x(grid):
    return _paint_stencil(grid, _CENTER_AND_DIAGONALS, fixed_color=8)


def _first_seed_only(grid):
    return _paint_stencil(grid, _CENTER_AND_DIAGONALS, only_first=True)


def _ignore_boundary_seeds(grid):
    return _paint_stencil(grid, _CENTER_AND_DIAGONALS, ignore_boundary=True)


SEMANTIC_RIVALS = {
    "identity_input": _identity,
    "omit_seed_center": _omit_center,
    "paint_center_only": _center_only,
    "cardinal_plus_instead_of_diagonal_x": _cardinal_plus,
    "filled_3x3_instead_of_x": _full_square,
    "fixed_color_8_x": _fixed_color_x,
    "transform_first_seed_only": _first_seed_only,
    "ignore_boundary_seeds": _ignore_boundary_seeds,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _valid(grid) -> bool:
    return not self_check(grid)


def _has_boundary_seed(grid) -> bool:
    if not _valid(grid):
        return False
    height, width = len(grid), len(grid[0])
    return any(_is_boundary(row, col, height, width) for row, col, _ in _seed_cells(grid))


def _has_interior_seed(grid) -> bool:
    if not _valid(grid):
        return False
    height, width = len(grid), len(grid[0])
    return any(not _is_boundary(row, col, height, width) for row, col, _ in _seed_cells(grid))


def _has_multiple_seeds(grid) -> bool:
    return _valid(grid) and len(_seed_cells(grid)) >= 2


def _has_multiple_colors(grid) -> bool:
    return _valid(grid) and len({color for _, _, color in _seed_cells(grid)}) >= 2


def _has_non_eight_color(grid) -> bool:
    return _valid(grid) and any(color != 8 for _, _, color in _seed_cells(grid))


SEMANTIC_WITNESSES = {
    "center_is_preserved_and_arms_are_added": lambda grid: _valid(grid),
    "diagonal_not_cardinal_growth": _has_interior_seed,
    "boundary_clipping_branch": _has_boundary_seed,
    "every_seed_is_transformed": _has_multiple_seeds,
    "seed_color_is_copied": _has_non_eight_color,
    "multiple_seed_colors_remain_distinct": _has_multiple_colors,
}

WITNESS_RIVALS = {
    "center_is_preserved_and_arms_are_added": [
        "identity_input",
        "omit_seed_center",
        "paint_center_only",
    ],
    "diagonal_not_cardinal_growth": [
        "cardinal_plus_instead_of_diagonal_x",
        "filled_3x3_instead_of_x",
    ],
    "boundary_clipping_branch": ["ignore_boundary_seeds"],
    "every_seed_is_transformed": ["transform_first_seed_only"],
    "seed_color_is_copied": ["fixed_color_8_x"],
    "multiple_seed_colors_remain_distinct": ["fixed_color_8_x"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require the demonstrations to refute every named plausible rival."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is outside the teaching grammar: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output does not match the center-plus-diagonal-X rule")
            continue
        valid_demos.append(demo)

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is outside the teaching grammar: {query_errors[0]}")
        return reasons

    if not any(_has_boundary_seed(demo["input"]) for demo in valid_demos):
        reasons.append("demonstrations do not show the clipping behavior of a boundary seed")
    if not any(_has_interior_seed(demo["input"]) for demo in valid_demos):
        reasons.append("demonstrations do not show a full five-cell interior X")
    if not any(_has_multiple_seeds(demo["input"]) for demo in valid_demos):
        reasons.append("demonstrations do not show that every seed is transformed")
    if not any(_has_multiple_colors(demo["input"]) for demo in valid_demos):
        reasons.append("demonstrations do not show independent same-color copying")
    if len({_profile_of(demo["input"]) for demo in valid_demos}) < 4:
        reasons.append("demonstrations do not cover four distinct scene profiles")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in valid_demos):
            reasons.append(f"competing rule {name!r} survives every demonstration")
    return reasons


def _candidate_categories(height: int, width: int):
    corners = []
    boundary = []
    interior = []
    for row in range(height):
        for col in range(width):
            if _is_corner(row, col, height, width):
                corners.append((row, col))
            elif _is_boundary(row, col, height, width):
                boundary.append((row, col))
            else:
                interior.append((row, col))
    return corners, boundary, interior


def _choose_positions(rng, spec) -> list[tuple[int, int]]:
    height, width, seed_count, _, boundary_count, corner_count = spec
    edge_noncorner_count = boundary_count - corner_count
    interior_count = seed_count - boundary_count
    categories = _candidate_categories(height, width)
    quotas = (corner_count, edge_noncorner_count, interior_count)

    for _ in range(512):
        chosen: list[tuple[int, int]] = []
        success = True
        for candidates, quota in zip(categories, quotas):
            if quota == 0:
                continue
            options = list(candidates)
            rng.shuffle(options)
            added = 0
            for position in options:
                if all(
                    max(abs(position[0] - row), abs(position[1] - col)) >= 3
                    for row, col in chosen
                ):
                    chosen.append(position)
                    added += 1
                    if added == quota:
                        break
            if added != quota:
                success = False
                break
        if success and len(chosen) == seed_count and _positions_are_separated(chosen):
            rng.shuffle(chosen)
            return chosen
    raise RuntimeError(f"could not place profile signature {spec!r}")


def _choose_colors(rng, seed_count: int, distinct_count: int) -> list[int]:
    palette = rng.sample(range(1, 10), distinct_count)
    colors = list(palette)
    colors.extend(rng.choice(palette) for _ in range(seed_count - distinct_count))
    rng.shuffle(colors)
    if len(set(colors)) != distinct_count:
        raise AssertionError("foreground palette did not realize the requested color count")
    return colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the Racket rule owns outputs."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    profile_options = SCENE_PROFILES if "scene_profile" in overrides else (scheduled,)
    profile = ctx.draw_choice("scene_profile", profile_options)
    spec = SCENE_SPECS[profile]
    height, width, seed_count, distinct_count, _, _ = spec

    rng = ctx.draw_rng(f"layout:{difficulty or 'medium'}:{profile}")
    positions = _choose_positions(rng, spec)
    colors = _choose_colors(rng, seed_count, distinct_count)
    grid = full_grid(height, width, 0)
    for (row, col), color in zip(positions, colors):
        grid[row][col] = color

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": {"scene_profile": profile}},
    )
    if errors:
        raise RuntimeError(f"constructed invalid scene for {profile}: {errors}")
    return [row[:] for row in grid]
