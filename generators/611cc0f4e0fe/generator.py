"""Semantic generator for ``611cc0f4e0fe`` — bridge 45-degree pairs.

The selected Racket authority groups nonzero cells by color and, for every
color with at least two cells, uses the first and last row-major cells as
candidate endpoints.  It fills the inclusive segment only when those
endpoints form an exact 45-degree diagonal.

The public contract is intentionally small: one observable ``scene_profile``
axis cycles through a canonical profile and three counterexample profiles.
That curriculum teaches the exact 45-degree precondition, shows that both
pairs may share a slope, and shows that the rule is not limited to exactly two
foreground colors.
"""
from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
from itertools import combinations
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "611cc0f4e0fe"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "51d7c63afd4f"

SUMMARY = (
    "Matching-colored endpoints are joined only when their row and column "
    "offsets have equal nonzero magnitude.  Four scheduled scene profiles "
    "cover the canonical one-pair-per-slope pattern, two pairs with the same "
    "slope, a repeated-color non-45-degree decoy, and three valid pairs."
)

INVARIANTS = [
    "background is color 0",
    "every generated nonzero color appears exactly twice",
    "every generated scene contains at least one separated 45-degree pair",
    "non-45-degree decoy endpoints remain unchanged",
    "all generated diagonal segments have at least one interior cell",
    "generated three-pair and same-slope scenes use disjoint diagonal paths",
]

COUNTER_HYPOTHESES = [
    "connect every repeated-color pair with a generic straight-line algorithm",
    "act only when there is exactly one positive- and one negative-slope pair",
    "act only when the input has exactly two foreground colors",
    "connect only the first matching-color diagonal pair",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

SCENE_PROFILES = (
    "canonical_opposite_slopes",
    "same_slope_pairs",
    "off_slope_decoy",
    "three_pairs",
)
SCHEDULE_PROFILES = SCENE_PROFILES
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four-profile deterministic semantic curriculum",
        "valid": "|".join(SCENE_PROFILES),
    }
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

Point = tuple[int, int]
Pair = tuple[Point, Point]

_CANONICAL_DIMENSIONS = {(7, 7), (8, 8), (8, 10), (9, 9), (10, 10)}
_CANONICAL_SIGNATURES = {(height, width, 3) for height, width in _CANONICAL_DIMENSIONS}
_BAND_DIMENSIONS = {
    "easy": (7, 7),
    "medium": (8, 10),
    "hard": (10, 10),
}
_CANONICAL_COLORS = (2, 3, 4, 5, 6, 7, 8)


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Cover every semantic profile in every four consecutive examples."""
    del seed
    _band(difficulty)
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return [f"cell ({r},{c}) must be an ARC integer color 0..9"]
    return []


def _color_cells(grid: Sequence[Sequence[int]]) -> dict[int, tuple[Point, ...]]:
    """Return cells in the same row-major color order used by the authority."""
    cells: dict[int, list[Point]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                cells[int(value)].append((r, c))
    return {color: tuple(points) for color, points in cells.items()}


def _pair_delta(points: Sequence[Point]) -> tuple[int, int] | None:
    if len(points) != 2:
        return None
    (r1, c1), (r2, c2) = points
    return r2 - r1, c2 - c1


def _diagonal_slope(points: Sequence[Point]) -> int | None:
    delta = _pair_delta(points)
    if delta is None:
        return None
    dr, dc = delta
    if dr == 0 or abs(dr) != abs(dc) or abs(dr) < 2:
        return None
    return 1 if dr * dc > 0 else -1


def _diagonal_path(points: Sequence[Point]) -> tuple[Point, ...]:
    slope = _diagonal_slope(points)
    if slope is None:
        return ()
    (r1, c1), (r2, c2) = points
    dr, dc = r2 - r1, c2 - c1
    sr = 1 if dr > 0 else -1
    sc = 1 if dc > 0 else -1
    return tuple((r1 + step * sr, c1 + step * sc) for step in range(abs(dr) + 1))


def _is_off_slope_pair(points: Sequence[Point]) -> bool:
    delta = _pair_delta(points)
    if delta is None:
        return False
    dr, dc = delta
    return (
        dr != 0
        and dc != 0
        and abs(dr) != abs(dc)
        and max(abs(dr), abs(dc)) >= 2
    )


def _bresenham_path(points: Sequence[Point]) -> tuple[Point, ...]:
    """Inclusive integer line used only by the explicit generic-line rival."""
    if len(points) != 2:
        return ()
    (r1, c1), (r2, c2) = points
    x1, y1 = c1, r1
    x2, y2 = c2, r2
    dx = abs(x2 - x1)
    sx = 1 if x1 < x2 else -1
    dy = -abs(y2 - y1)
    sy = 1 if y1 < y2 else -1
    error = dx + dy
    result: list[Point] = []
    while True:
        result.append((y1, x1))
        if x1 == x2 and y1 == y2:
            return tuple(result)
        doubled = 2 * error
        if doubled >= dy:
            error += dy
            x1 += sx
        if doubled <= dx:
            error += dx
            y1 += sy


def analyze_grid(grid: Sequence[Sequence[int]]) -> dict[str, Any]:
    """Return independently observable structural facts about an input grid."""
    errors = _validate_grid(grid)
    if errors:
        return {
            "valid": False,
            "errors": errors,
            "diagonal_pair_count": 0,
            "positive_slope_pair_count": 0,
            "negative_slope_pair_count": 0,
            "off_slope_pair_count": 0,
            "unsupported_color_count": 0,
            "unsafe_path_intersection_count": 0,
            "endpoint_crossing_count": 0,
            "off_slope_endpoint_on_diagonal_count": 0,
        }

    height, width = len(grid), len(grid[0])
    by_color = _color_cells(grid)
    diagonal_pairs: list[tuple[int, tuple[Point, ...], int, tuple[Point, ...]]] = []
    off_slope_pairs: list[tuple[int, tuple[Point, ...]]] = []
    unsupported: list[tuple[int, tuple[Point, ...]]] = []

    for color, points in by_color.items():
        slope = _diagonal_slope(points)
        if slope is not None:
            diagonal_pairs.append((color, points, slope, _diagonal_path(points)))
        elif _is_off_slope_pair(points):
            off_slope_pairs.append((color, points))
        else:
            unsupported.append((color, points))

    unsafe_intersections = 0
    endpoint_crossings = 0
    for left, right in combinations(diagonal_pairs, 2):
        _left_color, left_points, _left_slope, left_path = left
        _right_color, right_points, _right_slope, right_path = right
        for point in set(left_path) & set(right_path):
            left_endpoint = point in set(left_points)
            right_endpoint = point in set(right_points)
            if left_endpoint ^ right_endpoint:
                endpoint_crossings += 1
            else:
                unsafe_intersections += 1

    diagonal_union = {
        point for _color, _points, _slope, path in diagonal_pairs for point in path
    }
    off_slope_endpoint_on_diagonal = sum(
        point in diagonal_union
        for _color, points in off_slope_pairs
        for point in points
    )

    return {
        "valid": True,
        "errors": [],
        "height": height,
        "width": width,
        "palette_size": len({value for row in grid for value in row}),
        "nonzero_color_count": len(by_color),
        "diagonal_pair_count": len(diagonal_pairs),
        "positive_slope_pair_count": sum(row[2] == 1 for row in diagonal_pairs),
        "negative_slope_pair_count": sum(row[2] == -1 for row in diagonal_pairs),
        "off_slope_pair_count": len(off_slope_pairs),
        "unsupported_color_count": len(unsupported),
        "unsafe_path_intersection_count": unsafe_intersections,
        "endpoint_crossing_count": endpoint_crossings,
        "off_slope_endpoint_on_diagonal_count": off_slope_endpoint_on_diagonal,
    }


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover the exact public scene profile from the returned input alone."""
    analysis = analyze_grid(grid)
    if not analysis["valid"]:
        return {"scene_profile": None}
    if (analysis["height"], analysis["width"]) not in _CANONICAL_DIMENSIONS:
        return {"scene_profile": None}
    if analysis["unsupported_color_count"] != 0:
        return {"scene_profile": None}
    if analysis["unsafe_path_intersection_count"] != 0:
        return {"scene_profile": None}

    diagonal = analysis["diagonal_pair_count"]
    positive = analysis["positive_slope_pair_count"]
    negative = analysis["negative_slope_pair_count"]
    off_slope = analysis["off_slope_pair_count"]
    colors = analysis["nonzero_color_count"]

    profile: str | None
    if (
        colors == 2
        and diagonal == 2
        and positive == 1
        and negative == 1
        and off_slope == 0
    ):
        profile = "canonical_opposite_slopes"
    elif (
        colors == 2
        and diagonal == 2
        and {positive, negative} == {0, 2}
        and off_slope == 0
        and analysis["endpoint_crossing_count"] == 0
    ):
        profile = "same_slope_pairs"
    elif (
        colors == 2
        and diagonal == 1
        and off_slope == 1
        and analysis["off_slope_endpoint_on_diagonal_count"] == 0
    ):
        profile = "off_slope_decoy"
    elif (
        colors == 3
        and diagonal == 3
        and positive == 2
        and negative == 1
        and off_slope == 0
        and analysis["endpoint_crossing_count"] == 0
    ):
        profile = "three_pairs"
    else:
        profile = None
    return {"scene_profile": profile}


@lru_cache(maxsize=None)
def _diagonal_candidates(height: int, width: int, slope: int | None = None) -> tuple[Pair, ...]:
    result: list[Pair] = []
    for r1 in range(height):
        for r2 in range(r1 + 2, height):
            distance = r2 - r1
            for c1 in range(width):
                for direction in (-1, 1):
                    c2 = c1 + direction * distance
                    if not 0 <= c2 < width:
                        continue
                    candidate = ((r1, c1), (r2, c2))
                    candidate_slope = _diagonal_slope(candidate)
                    if slope is None or candidate_slope == slope:
                        result.append(candidate)
    return tuple(result)


@lru_cache(maxsize=None)
def _off_slope_candidates(height: int, width: int) -> tuple[Pair, ...]:
    points = [(r, c) for r in range(height) for c in range(width)]
    return tuple(
        (left, right)
        for left, right in combinations(points, 2)
        if _is_off_slope_pair((left, right))
        and len(_bresenham_path((left, right))) >= 3
    )


@lru_cache(maxsize=None)
def _canonical_opposite_templates(height: int, width: int) -> tuple[tuple[Pair, Pair], ...]:
    result: list[tuple[Pair, Pair]] = []
    for positive in _diagonal_candidates(height, width, 1):
        positive_path = set(_diagonal_path(positive))
        positive_endpoints = set(positive)
        for negative in _diagonal_candidates(height, width, -1):
            if positive_endpoints & set(negative):
                continue
            intersection = positive_path & set(_diagonal_path(negative))
            if not intersection:
                result.append((positive, negative))
                continue
            if len(intersection) != 1:
                continue
            point = next(iter(intersection))
            if (point in positive_endpoints) ^ (point in set(negative)):
                result.append((positive, negative))
    return tuple(result)


def _select_disjoint_diagonal_pairs(
    rng, height: int, width: int, slopes: Sequence[int]
) -> list[Pair]:
    groups = [list(_diagonal_candidates(height, width, slope)) for slope in slopes]
    for group in groups:
        rng.shuffle(group)

    def search(index: int, chosen: list[Pair], occupied: set[Point]) -> list[Pair] | None:
        if index == len(groups):
            return list(chosen)
        for candidate in groups[index]:
            path = set(_diagonal_path(candidate))
            if path & occupied:
                continue
            chosen.append(candidate)
            result = search(index + 1, chosen, occupied | path)
            if result is not None:
                return result
            chosen.pop()
        return None

    selected = search(0, [], set())
    if selected is None:
        raise RuntimeError(
            f"could not place disjoint diagonal slopes {tuple(slopes)} in {height}x{width}"
        )
    return selected


def _select_off_slope_scene(rng, height: int, width: int) -> tuple[Pair, Pair]:
    diagonals = list(_diagonal_candidates(height, width))
    decoys = list(_off_slope_candidates(height, width))
    rng.shuffle(diagonals)
    rng.shuffle(decoys)
    for diagonal in diagonals:
        diagonal_path = set(_diagonal_path(diagonal))
        compatible = [
            decoy
            for decoy in decoys
            if not (set(_bresenham_path(decoy)) & diagonal_path)
        ]
        if compatible:
            return diagonal, rng.choice(compatible)
    raise RuntimeError(f"could not place off-slope decoy in {height}x{width}")


def _draw_pairs(
    height: int,
    width: int,
    pairs: Sequence[Pair],
    colors: Sequence[int],
) -> list[list[int]]:
    grid = full_grid(height, width, 0)
    for color, pair in zip(colors, pairs):
        for r, c in pair:
            if grid[r][c] != 0:
                raise RuntimeError("pair endpoints unexpectedly overlap")
            grid[r][c] = color
    return grid


def _render_profile(profile: str, height: int, width: int, rng) -> list[list[int]]:
    if profile == "canonical_opposite_slopes":
        templates = _canonical_opposite_templates(height, width)
        if not templates:
            raise RuntimeError(f"no canonical templates for {height}x{width}")
        pairs = list(rng.choice(templates))
        rng.shuffle(pairs)
    elif profile == "same_slope_pairs":
        slope = rng.choice((-1, 1))
        pairs = _select_disjoint_diagonal_pairs(rng, height, width, (slope, slope))
    elif profile == "off_slope_decoy":
        pairs = list(_select_off_slope_scene(rng, height, width))
        rng.shuffle(pairs)
    elif profile == "three_pairs":
        pairs = _select_disjoint_diagonal_pairs(rng, height, width, (1, 1, -1))
        rng.shuffle(pairs)
    else:
        raise RuntimeError(f"unhandled scene_profile: {profile!r}")

    colors = rng.sample(_CANONICAL_COLORS, len(pairs))
    return _draw_pairs(height, width, pairs, colors)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    band = _band(difficulty)
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    selected = requested or schedule_profile(seed, sample_index, band)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", [selected])
    rng = ctx.draw_rng(f"layout_{profile}_{band}")
    height, width = _BAND_DIMENSIONS[band]
    grid = _render_profile(profile, height, width, rng)

    observed = observe_overrides(grid)["scene_profile"]
    if observed != profile:
        raise RuntimeError(
            f"rendered profile {profile!r} is not observable (observed {observed!r})"
        )
    errors = self_check(grid, difficulty=band)
    if errors:
        raise RuntimeError(f"rendered profile {profile!r} failed self_check: {errors}")
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject blank, malformed, ambiguous, or undeclared scene structures."""
    del difficulty, meta
    errors = _validate_grid(grid)
    if errors:
        return errors

    height, width = len(grid), len(grid[0])
    palette = {value for row in grid for value in row}
    if (height, width) not in _CANONICAL_DIMENSIONS:
        errors.append(
            f"dimensions {(height, width)} are outside canonical dimensions "
            f"{sorted(_CANONICAL_DIMENSIONS)}"
        )
    if 0 not in palette:
        errors.append("background color 0 must be present")

    by_color = _color_cells(grid)
    if not by_color:
        errors.append("need at least one matching-color diagonal pair")
    for color, points in by_color.items():
        if len(points) != 2:
            errors.append(f"color {color} appears {len(points)} times; expected exactly two")
            continue
        if _diagonal_slope(points) is not None:
            continue
        if _is_off_slope_pair(points):
            continue
        errors.append(
            f"color {color} endpoints must be a separated 45-degree pair or the "
            "declared non-axis off-slope decoy"
        )

    analysis = analyze_grid(grid)
    if analysis["diagonal_pair_count"] == 0:
        errors.append("need at least one separated 45-degree pair")
    if analysis["unsafe_path_intersection_count"]:
        errors.append("diagonal paths may intersect only at one pair's endpoint")
    profile = observe_overrides(grid)["scene_profile"]
    if profile is None:
        errors.append("input does not match any declared semantic scene profile")
    if not errors and rule_mirror(grid) == [list(row) for row in grid]:
        errors.append("rule is an identity transformation on this input")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the exact structural family shared by all canonical inputs."""
    errors = _validate_grid(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    signature = (height, width, len({value for row in grid for value in row}))
    if signature not in _CANONICAL_SIGNATURES:
        errors.append(
            f"shape/palette signature {signature} is outside canonical signatures "
            f"{sorted(_CANONICAL_SIGNATURES)}"
        )
    analysis = analyze_grid(grid)
    if analysis["nonzero_color_count"] != 2:
        errors.append("canonical inputs contain exactly two foreground colors")
    if analysis["diagonal_pair_count"] != 2:
        errors.append("canonical inputs contain exactly two separated diagonal pairs")
    if (
        analysis["positive_slope_pair_count"] != 1
        or analysis["negative_slope_pair_count"] != 1
    ):
        errors.append("canonical inputs contain one pair of each 45-degree slope")
    if analysis["off_slope_pair_count"] or analysis["unsupported_color_count"]:
        errors.append("canonical inputs contain no decoy or unsupported color group")
    if analysis["unsafe_path_intersection_count"]:
        errors.append("canonical paths do not share endpoints or cross interior-to-interior")
    return errors


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Input-pure Python mirror of the selected canonical Racket authority."""
    errors = _validate_grid(grid)
    if errors:
        raise ValueError(errors[0])
    output = [list(row) for row in grid]
    for color, points in _color_cells(grid).items():
        if len(points) < 2:
            continue
        endpoints = (points[0], points[-1])
        for r, c in _diagonal_path(endpoints):
            output[r][c] = color
    return output


def _copy_grid(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _rival_connect_every_repeated_pair_with_bresenham(grid):
    errors = _validate_grid(grid)
    if errors:
        raise ValueError(errors[0])
    output = _copy_grid(grid)
    for color, points in _color_cells(grid).items():
        if len(points) < 2:
            continue
        for r, c in _bresenham_path((points[0], points[-1])):
            output[r][c] = color
    return output


def _rival_require_one_pair_of_each_slope(grid):
    analysis = analyze_grid(grid)
    if (
        analysis.get("positive_slope_pair_count", 0) >= 1
        and analysis.get("negative_slope_pair_count", 0) >= 1
    ):
        return rule_mirror(grid)
    return _copy_grid(grid)


def _rival_transform_only_exactly_two_foreground_colors(grid):
    if len(_color_cells(grid)) == 2:
        return rule_mirror(grid)
    return _copy_grid(grid)


def _rival_connect_only_first_diagonal_pair(grid):
    errors = _validate_grid(grid)
    if errors:
        raise ValueError(errors[0])
    output = _copy_grid(grid)
    for color, points in _color_cells(grid).items():
        path = _diagonal_path((points[0], points[-1])) if len(points) >= 2 else ()
        if path:
            for r, c in path:
                output[r][c] = color
            break
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "connect_every_repeated_pair_with_bresenham": (
        _rival_connect_every_repeated_pair_with_bresenham
    ),
    "require_one_pair_of_each_slope": _rival_require_one_pair_of_each_slope,
    "transform_only_exactly_two_foreground_colors": (
        _rival_transform_only_exactly_two_foreground_colors
    ),
    "connect_only_first_diagonal_pair": _rival_connect_only_first_diagonal_pair,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "connect_every_repeated_pair_with_bresenham": (
        _rival_connect_every_repeated_pair_with_bresenham
    ),
    "require_one_pair_of_each_slope": _rival_require_one_pair_of_each_slope,
    "transform_only_exactly_two_foreground_colors": (
        _rival_transform_only_exactly_two_foreground_colors
    ),
}


def _analysis_value(grid, key: str):
    return analyze_grid(grid).get(key)


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "both_45_degree_slopes_are_active": lambda grid: (
        _analysis_value(grid, "positive_slope_pair_count") >= 1
        and _analysis_value(grid, "negative_slope_pair_count") >= 1
    ),
    "same_slope_pairs_are_active": lambda grid: (
        _analysis_value(grid, "diagonal_pair_count") == 2
        and {
            _analysis_value(grid, "positive_slope_pair_count"),
            _analysis_value(grid, "negative_slope_pair_count"),
        }
        == {0, 2}
    ),
    "off_slope_repeated_pair_stays_unchanged": lambda grid: (
        _analysis_value(grid, "off_slope_pair_count") == 1
    ),
    "three_matching_pairs_all_transform": lambda grid: (
        _analysis_value(grid, "diagonal_pair_count") == 3
    ),
    "multiple_pairs_all_transform": lambda grid: (
        _analysis_value(grid, "diagonal_pair_count") >= 2
    ),
}
BRANCH_WITNESSES = tuple(SEMANTIC_WITNESSES)
WITNESS_RIVALS = {
    "same_slope_pairs_are_active": ["require_one_pair_of_each_slope"],
    "off_slope_repeated_pair_stays_unchanged": [
        "connect_every_repeated_pair_with_bresenham"
    ],
    "three_matching_pairs_all_transform": [
        "transform_only_exactly_two_foreground_colors"
    ],
    "multiple_pairs_all_transform": ["connect_only_first_diagonal_pair"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require a complete scheduled lesson and refutation of every rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]

    reasons: list[str] = []
    profiles: set[str] = set()
    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} must contain input and output")
            continue
        grid = pair["input"]
        check = self_check(grid)
        if check:
            reasons.append(f"pair {index} is outside the lawful grammar: {check[0]}")
            continue
        if rule_mirror(grid) != pair["output"]:
            reasons.append(f"pair {index} disagrees with the selected diagonal rule")
        if index < len(demos):
            observed = observe_overrides(grid)["scene_profile"]
            if observed is not None:
                profiles.add(observed)

    if reasons:
        return reasons
    missing = sorted(set(SCENE_PROFILES) - profiles)
    if missing:
        reasons.append(f"demonstrations are missing scheduled profiles: {missing}")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"demonstrations do not falsify rival: {name}")
    return reasons
