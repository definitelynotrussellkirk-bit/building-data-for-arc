"""Curriculum for filling diagonal spans between matching-color endpoints.

The selected authority scans nonzero colors in row-major first-appearance
order.  A color acts only when it appears exactly twice and the two cells are
on a 45-degree diagonal; its inclusive span is then painted.  Later colors
therefore own crossings, even when a crossing overwrites an earlier color's
original endpoint.

Exact override axes: ``grid_h``, ``grid_w``, ``pair_count``, and
``scene_profile``.  Every five consecutive samples cover separated spans,
interior crossings, both endpoint-overwrite outcomes, and inert controls that
teach the "exactly two" and "diagonal" guards.
"""
from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e0650802a8fb"
TASK_ID = "e0650802a8fb"
VERSION = "3.0.0"
RULE_HASH = "040cfb38300e"  # canonical_rule_hash(TASK_ID)
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.75

SCENE_PROFILES = (
    "disjoint",
    "interior_cross",
    "endpoint_overwrite",
    "endpoint_survive",
    "controls",
)
SCHEDULE_PROFILES = SCENE_PROFILES

SUMMARY = (
    "On a 0-background grid, every color that appears exactly twice on a "
    "non-trivial 45-degree diagonal fills its inclusive span. Colors are "
    "processed in row-major first-appearance order, so the later color owns "
    "crossings. A five-sample schedule covers disjoint and crossing spans, "
    "both endpoint outcomes, plus axis-pair/singleton/triple controls."
)

INVARIANTS = [
    "all cells are integer ARC colors 0..9 and the background is 0",
    "ordinary scenes contain 2..4 qualifying same-color diagonal endpoint pairs",
    "qualifying colors are processed in row-major first-appearance order",
    "later qualifying colors overwrite earlier colors at every shared span cell",
    "the controls scene adds one inert axis pair, singleton, and triple",
    "every ordinary draw changes under the selected diagonal-fill rule",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-anchored deterministic schedule",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-anchored deterministic schedule",
        "valid": "8..14",
    },
    "pair_count": {
        "type": "int",
        "default": "difficulty-aware deterministic schedule",
        "valid": "2..4",
    },
    "scene_profile": {
        "type": "str",
        "default": "five-sample semantic schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
}

Point = tuple[int, int]
EndpointPath = tuple[Point, Point]

# The first two paths define the profile. Later paths are non-intersecting
# extras, allowing pair_count to vary without changing the profile label.
_TEMPLATE_PATHS: dict[str, tuple[EndpointPath, ...]] = {
    "disjoint": (
        ((0, 0), (4, 4)),
        ((0, 7), (3, 4)),
        ((5, 0), (7, 2)),
        ((5, 7), (7, 5)),
    ),
    "interior_cross": (
        ((1, 1), (5, 5)),
        ((1, 5), (5, 1)),
        ((5, 7), (7, 5)),
        ((0, 7), (2, 5)),
    ),
    # Path 0 owns the shared endpoint (5, 3); path 1 crosses its interior.
    "endpoint": (
        ((1, 7), (5, 3)),
        ((3, 1), (7, 5)),
        ((0, 0), (2, 2)),
        ((0, 5), (2, 3)),
    ),
}
_TEMPLATE_SIZE = 8
_D4_NAMES = (
    "identity",
    "rot90",
    "rot180",
    "rot270",
    "flip_lr",
    "flip_ud",
    "transpose",
    "anti_transpose",
)
_CANONICAL_CANVASES = ((8, 8), (9, 9), (8, 11), (9, 10))
_EXPANDED_CANVASES = {
    "easy": ((8, 9), (9, 8), (9, 11), (10, 8)),
    "medium": ((10, 10), (10, 12), (11, 10), (12, 12), (9, 13)),
    "hard": ((12, 13), (13, 12), (14, 14), (11, 14), (14, 11)),
}


def _band(difficulty: Any) -> str:
    return difficulty if difficulty in _EXPANDED_CANVASES else "medium"


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Five-cycle: every five consecutive indexes contain all profiles."""
    del difficulty
    return SCENE_PROFILES[(int(seed) + int(sample_index)) % len(SCENE_PROFILES)]


def _scheduled_canvas(ctx, seed: int, sample_index: int, band: str) -> tuple[int, int]:
    rng = ctx.draw_rng("canvas_schedule")
    # Keep exact official profile support in every difficulty band without
    # reducing the curriculum to memorized public dimensions.
    if (int(seed) + int(sample_index)) % 3 == 0:
        return rng.choice(_CANONICAL_CANVASES)
    return rng.choice(_EXPANDED_CANVASES[band])


def _scheduled_pair_count(seed: int, sample_index: int, band: str) -> int:
    residue = (int(seed) + int(sample_index)) % 5
    if band == "easy":
        return (2, 2, 2, 3, 3)[residue]
    if band == "hard":
        return (2, 3, 3, 4, 4)[residue]
    return (2, 2, 3, 3, 4)[residue]


def _validate_override(name: str, value: Any) -> Any:
    if name in {"grid_h", "grid_w"}:
        if isinstance(value, bool) or not isinstance(value, int) or not 8 <= value <= 14:
            raise ValueError(f"{name} override must be an integer in 8..14")
    elif name == "pair_count":
        if isinstance(value, bool) or not isinstance(value, int) or not 2 <= value <= 4:
            raise ValueError("pair_count override must be an integer in 2..4")
    elif name == "scene_profile":
        if value not in SCENE_PROFILES:
            raise ValueError(
                f"scene_profile override must be one of {SCENE_PROFILES}, got {value!r}"
            )
    return value


def _path(a: Point, b: Point) -> tuple[Point, ...]:
    dr = b[0] - a[0]
    dc = b[1] - a[1]
    if abs(dr) != abs(dc) or dr == 0:
        raise ValueError(f"not a non-axis 45-degree path: {a!r} -> {b!r}")
    sr = 1 if dr > 0 else -1
    sc = 1 if dc > 0 else -1
    return tuple((a[0] + step * sr, a[1] + step * sc) for step in range(abs(dr) + 1))


def _transform_point(point: Point, size: int, name: str) -> Point:
    row, col = point
    last = size - 1
    if name == "identity":
        return row, col
    if name == "rot90":
        return col, last - row
    if name == "rot180":
        return last - row, last - col
    if name == "rot270":
        return last - col, row
    if name == "flip_lr":
        return row, last - col
    if name == "flip_ud":
        return last - row, col
    if name == "transpose":
        return col, row
    if name == "anti_transpose":
        return last - col, last - row
    raise ValueError(f"unknown D4 transform: {name}")


def _transform_paths(
    paths: Sequence[EndpointPath], name: str, top: int, left: int
) -> tuple[EndpointPath, ...]:
    transformed: list[EndpointPath] = []
    for first, second in paths:
        a = _transform_point(first, _TEMPLATE_SIZE, name)
        b = _transform_point(second, _TEMPLATE_SIZE, name)
        transformed.append(
            ((a[0] + top, a[1] + left), (b[0] + top, b[1] + left))
        )
    return tuple(transformed)


def _first_endpoint(path: EndpointPath) -> Point:
    return min(path)


def _endpoint_outcome(paths: Sequence[EndpointPath]) -> str | None:
    """Classify the first two endpoint-template paths without color values."""
    first_path = _path(*paths[0])
    second_path = _path(*paths[1])
    shared = set(first_path) & set(second_path)
    if len(shared) != 1:
        return None
    point = next(iter(shared))
    first_endpoint = point in {first_path[0], first_path[-1]}
    second_endpoint = point in {second_path[0], second_path[-1]}
    if first_endpoint == second_endpoint:
        return None
    owner_index = 0 if first_endpoint else 1
    other_index = 1 - owner_index
    first_seen = sorted(range(2), key=lambda index: _first_endpoint(paths[index]))
    return "overwrite" if first_seen.index(owner_index) < first_seen.index(other_index) else "survive"


def _layout_paths(
    ctx, height: int, width: int, pair_count: int, profile: str
) -> tuple[tuple[EndpointPath, ...], int, int]:
    layout_rng = ctx.draw_rng("layout")
    source = "disjoint" if profile == "controls" else profile
    if source.startswith("endpoint_"):
        template_key = "endpoint"
        expected = source.removeprefix("endpoint_")
    else:
        template_key = source
        expected = None

    candidates: list[tuple[tuple[EndpointPath, ...], int, int]] = []
    for transform in _D4_NAMES:
        for top in range(height - _TEMPLATE_SIZE + 1):
            for left in range(width - _TEMPLATE_SIZE + 1):
                transformed = _transform_paths(
                    _TEMPLATE_PATHS[template_key], transform, top, left
                )[:pair_count]
                if expected is not None and _endpoint_outcome(transformed) != expected:
                    continue
                candidates.append((transformed, top, left))
    if not candidates:
        raise AssertionError(
            f"no {profile!r} layout fits {height}x{width} with {pair_count} pairs"
        )
    return layout_rng.choice(candidates)


def _target_colors(ctx, paths: Sequence[EndpointPath], profile: str) -> tuple[int, ...]:
    rng = ctx.draw_rng("color_assignment")
    selected = rng.sample(list(range(1, 10)), len(paths))
    assignment: list[int | None] = [None] * len(paths)

    # The collision scenes deliberately make row-major priority disagree with
    # simple numeric priority. Interior crossings refute ascending order;
    # endpoint scenes refute descending order and endpoint preservation.
    if profile == "interior_cross":
        early, late = sorted(range(2), key=lambda index: _first_endpoint(paths[index]))
        low, high = sorted(selected[:2])
        assignment[early], assignment[late] = high, low
    elif profile.startswith("endpoint_"):
        early, late = sorted(range(2), key=lambda index: _first_endpoint(paths[index]))
        low, high = sorted(selected[:2])
        assignment[early], assignment[late] = low, high
    else:
        first_two = selected[:2]
        rng.shuffle(first_two)
        assignment[0], assignment[1] = first_two

    extras = selected[2:]
    rng.shuffle(extras)
    for index, color in zip(range(2, len(paths)), extras):
        assignment[index] = color
    return tuple(int(color) for color in assignment)


def _axis_segment(a: Point, b: Point) -> tuple[Point, ...]:
    if a[0] == b[0]:
        lo, hi = sorted((a[1], b[1]))
        return tuple((a[0], col) for col in range(lo, hi + 1))
    if a[1] == b[1]:
        lo, hi = sorted((a[0], b[0]))
        return tuple((row, a[1]) for row in range(lo, hi + 1))
    raise ValueError("not an axis-aligned segment")


def _control_layout(
    ctx, target_paths: Sequence[EndpointPath], top: int, left: int
) -> tuple[tuple[Point, Point], Point, tuple[Point, Point, Point]]:
    """Find an inert axis pair, singleton, and adversarial triple in the 8x8 frame."""
    rng = ctx.draw_rng("control_layout")
    reserved = {
        point
        for endpoints in target_paths
        for point in _path(*endpoints)
    }
    frame = [
        (row, col)
        for row in range(top, top + _TEMPLATE_SIZE)
        for col in range(left, left + _TEMPLATE_SIZE)
    ]
    free = [point for point in frame if point not in reserved]
    free_set = set(free)

    axis_candidates: list[tuple[Point, Point]] = []
    diagonal_candidates: list[tuple[Point, Point, tuple[Point, ...]]] = []
    for a, b in combinations(free, 2):
        if (a[0] == b[0] or a[1] == b[1]):
            segment = _axis_segment(a, b)
            if len(segment) >= 3 and any(point in free_set for point in segment[1:-1]):
                axis_candidates.append((a, b))
        dr, dc = b[0] - a[0], b[1] - a[1]
        if abs(dr) == abs(dc) and abs(dr) >= 2:
            segment = _path(a, b)
            if any(point in free_set for point in segment[1:-1]):
                diagonal_candidates.append((a, b, segment))

    rng.shuffle(axis_candidates)
    rng.shuffle(diagonal_candidates)
    for axis_pair in axis_candidates:
        axis_used = set(axis_pair)
        for first, last, diagonal in diagonal_candidates:
            if axis_used & {first, last}:
                continue
            middle_candidates = [
                point
                for point in free
                if first < point < last
                and point not in diagonal
                and point not in axis_used
            ]
            if not middle_candidates:
                continue
            middle = rng.choice(middle_candidates)
            used = axis_used | {first, middle, last}
            singleton_candidates = [point for point in free if point not in used]
            if singleton_candidates:
                return axis_pair, rng.choice(singleton_candidates), (first, middle, last)
    raise AssertionError("failed to place rule-guard controls")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    for name, value in overrides.items():
        _validate_override(name, value)

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    scheduled_h, scheduled_w = _scheduled_canvas(ctx, seed, sample_index, band)
    requested_h = overrides.get("grid_h", scheduled_h)
    requested_w = overrides.get("grid_w", scheduled_w)
    requested_count = overrides.get(
        "pair_count", _scheduled_pair_count(seed, sample_index, band)
    )
    requested_profile = overrides.get(
        "scene_profile", schedule_profile(seed, sample_index, band)
    )

    # Singleton draws preserve keyed-draw provenance while validation above
    # enforces the declared full override domain.
    height = ctx.draw_int("grid_h", requested_h, requested_h)
    width = ctx.draw_int("grid_w", requested_w, requested_w)
    pair_count = ctx.draw_int("pair_count", requested_count, requested_count)
    profile = ctx.draw_choice("scene_profile", [requested_profile])

    paths, frame_top, frame_left = _layout_paths(
        ctx, height, width, pair_count, profile
    )
    colors = _target_colors(ctx, paths, profile)
    grid = full_grid(height, width, 0)
    for color, (a, b) in zip(colors, paths):
        if grid[a[0]][a[1]] != 0 or grid[b[0]][b[1]] != 0:
            raise AssertionError("template endpoints unexpectedly overlap")
        grid[a[0]][a[1]] = color
        grid[b[0]][b[1]] = color

    if profile == "controls":
        axis_pair, singleton, triple = _control_layout(
            ctx, paths, frame_top, frame_left
        )
        used_colors = set(colors)
        control_rng = ctx.draw_rng("control_colors")
        control_colors = control_rng.sample(
            [color for color in range(1, 10) if color not in used_colors], 3
        )
        for point in axis_pair:
            grid[point[0]][point[1]] = control_colors[0]
        grid[singleton[0]][singleton[1]] = control_colors[1]
        for point in triple:
            grid[point[0]][point[1]] = control_colors[2]
    return grid


def _is_rectangular_grid(grid: Any) -> bool:
    return (
        isinstance(grid, (list, tuple))
        and bool(grid)
        and isinstance(grid[0], (list, tuple))
        and bool(grid[0])
        and all(
            isinstance(row, (list, tuple)) and len(row) == len(grid[0])
            for row in grid
        )
    )


def _scan_colors(grid: Sequence[Sequence[int]]) -> tuple[list[int], dict[int, list[Point]]]:
    order: list[int] = []
    by_color: dict[int, list[Point]] = defaultdict(list)
    seen: set[int] = set()
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value == 0:
                continue
            if value not in seen:
                seen.add(value)
                order.append(value)
            by_color[value].append((row_index, col_index))
    return order, dict(by_color)


def _authority_paths(
    grid: Sequence[Sequence[int]],
) -> tuple[list[int], dict[int, tuple[Point, ...]]]:
    order, by_color = _scan_colors(grid)
    paths: dict[int, tuple[Point, ...]] = {}
    for color in order:
        cells = by_color[color]
        if len(cells) != 2:
            continue
        first, second = cells
        dr = second[0] - first[0]
        dc = second[1] - first[1]
        if abs(dr) == abs(dc) and dr != 0:
            paths[color] = _path(first, second)
    return order, paths


def _analyze(grid: Any) -> dict[str, Any]:
    analysis: dict[str, Any] = {
        "errors": [],
        "height": 0,
        "width": 0,
        "color_order": [],
        "paths": {},
        "pair_count": 0,
        "scene_profile": None,
        "endpoint_crossings": [],
        "interior_crossings": [],
        "axis_pairs": [],
        "singletons": [],
        "triples": [],
        "other_controls": [],
    }
    errors: list[str] = analysis["errors"]
    if not _is_rectangular_grid(grid):
        errors.append("grid must be nonempty and rectangular")
        return analysis

    height, width = len(grid), len(grid[0])
    analysis["height"], analysis["width"] = height, width
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(
                    f"cell ({row_index},{col_index}) must be an integer ARC color 0..9"
                )
    if errors:
        return analysis

    color_order, by_color = _scan_colors(grid)
    analysis["color_order"] = color_order
    paths: dict[int, tuple[Point, ...]] = {}
    axis_pairs: list[int] = []
    singletons: list[int] = []
    triples: list[int] = []
    other_controls: list[int] = []
    for color in color_order:
        cells = by_color[color]
        if len(cells) == 1:
            singletons.append(color)
            continue
        if len(cells) == 3:
            triples.append(color)
            continue
        if len(cells) != 2:
            other_controls.append(color)
            continue
        first, second = cells
        dr, dc = second[0] - first[0], second[1] - first[1]
        if abs(dr) == abs(dc) and abs(dr) >= 2:
            paths[color] = _path(first, second)
        elif (dr == 0 or dc == 0) and max(abs(dr), abs(dc)) >= 2:
            axis_pairs.append(color)
        else:
            other_controls.append(color)

    analysis["paths"] = paths
    analysis["pair_count"] = len(paths)
    analysis["axis_pairs"] = axis_pairs
    analysis["singletons"] = singletons
    analysis["triples"] = triples
    analysis["other_controls"] = other_controls
    if not 2 <= len(paths) <= 4:
        errors.append(f"expected 2..4 qualifying diagonal pairs, found {len(paths)}")
    if other_controls:
        errors.append(f"unsupported control color counts/geometries: {other_controls}")

    control_counts = (len(axis_pairs), len(singletons), len(triples))
    has_controls = any(control_counts)
    if has_controls and control_counts != (1, 1, 1):
        errors.append(
            "controls must be exactly one axis pair, one singleton, and one triple"
        )
    if errors:
        return analysis

    order_index = {color: index for index, color in enumerate(color_order)}
    target_colors = [color for color in color_order if color in paths]
    endpoint_crossings: list[tuple[Point, int, int]] = []
    interior_crossings: list[tuple[Point, int, int]] = []
    for left_index, left_color in enumerate(target_colors):
        left_path = paths[left_color]
        left_endpoints = {left_path[0], left_path[-1]}
        for right_color in target_colors[left_index + 1 :]:
            right_path = paths[right_color]
            right_endpoints = {right_path[0], right_path[-1]}
            for point in sorted(set(left_path) & set(right_path)):
                left_is_endpoint = point in left_endpoints
                right_is_endpoint = point in right_endpoints
                if left_is_endpoint ^ right_is_endpoint:
                    owner = left_color if left_is_endpoint else right_color
                    other = right_color if left_is_endpoint else left_color
                    endpoint_crossings.append((point, owner, other))
                elif not left_is_endpoint and not right_is_endpoint:
                    interior_crossings.append((point, left_color, right_color))

    analysis["endpoint_crossings"] = endpoint_crossings
    analysis["interior_crossings"] = interior_crossings
    if has_controls:
        if endpoint_crossings or interior_crossings:
            errors.append("controls profile requires disjoint qualifying paths")
        analysis["scene_profile"] = "controls"
    elif endpoint_crossings:
        outcomes = {
            "overwrite"
            if order_index[owner] < order_index[other]
            else "survive"
            for _point, owner, other in endpoint_crossings
        }
        analysis["scene_profile"] = (
            f"endpoint_{next(iter(outcomes))}"
            if len(outcomes) == 1
            else "endpoint_mixed"
        )
    elif interior_crossings:
        analysis["scene_profile"] = "interior_cross"
    else:
        analysis["scene_profile"] = "disjoint"
    return analysis


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the selected task grammar and reject rule-hiding impostors."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if analysis["height"] > 30 or analysis["width"] > 30:
        errors.append(f"grid too large: {analysis['height']}x{analysis['width']}")
    if rule_mirror(grid) == [list(row) for row in grid]:
        errors.append("diagonal fill must make a visible change")

    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact axis directly from the returned input grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "pair_count": analysis["pair_count"],
        "scene_profile": analysis["scene_profile"],
    }


def strict_canonical_like(grid) -> list[str]:
    """Task-linked strict predicate; controls are the deliberate 20% extension."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analyze(grid)
    if not 7 <= analysis["height"] <= 14 or not 8 <= analysis["width"] <= 14:
        errors.append("canvas must stay within the canonical-anchored 7..14 by 8..14 range")
    if analysis["scene_profile"] == "controls":
        errors.append("rule-guard controls are outside the strict canonical profile")
    if any(len(path) - 1 > 8 for path in analysis["paths"].values()):
        errors.append("qualifying diagonal spans must be at most 8 steps")
    return errors


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror; the selected Racket source remains authority."""
    if not _is_rectangular_grid(grid):
        raise ValueError("grid must be nonempty and rectangular")
    for row in grid:
        if any(
            isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
            for value in row
        ):
            raise ValueError("grid contains a non-ARC color")
    order, paths = _authority_paths(grid)
    output = [list(row) for row in grid]
    for color in order:
        for row, col in paths.get(color, ()):  # ignored colors have no path
            output[row][col] = color
    return output


def _paint_paths(
    grid: Sequence[Sequence[int]], colors: Sequence[int], paths: dict[int, tuple[Point, ...]]
) -> list[list[int]]:
    output = [list(row) for row in grid]
    for color in colors:
        for row, col in paths.get(color, ()):
            output[row][col] = color
    return output


def _rival_numeric_ascending(grid):
    _order, paths = _authority_paths(grid)
    return _paint_paths(grid, sorted(paths), paths)


def _rival_numeric_descending(grid):
    _order, paths = _authority_paths(grid)
    return _paint_paths(grid, sorted(paths, reverse=True), paths)


def _rival_preserve_original_endpoints(grid):
    order, paths = _authority_paths(grid)
    original_nonzero = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    }
    output = [list(row) for row in grid]
    for color in order:
        for row, col in paths.get(color, ()):
            if (row, col) not in original_nonzero or grid[row][col] == color:
                output[row][col] = color
    return output


def _rival_midpoint_only(grid):
    order, paths = _authority_paths(grid)
    output = [list(row) for row in grid]
    for color in order:
        path = paths.get(color)
        if path:
            row, col = path[len(path) // 2]
            output[row][col] = color
    return output


def _rival_positive_slope_only(grid):
    order, paths = _authority_paths(grid)
    output = [list(row) for row in grid]
    for color in order:
        path = paths.get(color)
        if not path:
            continue
        if (path[-1][0] - path[0][0]) * (path[-1][1] - path[0][1]) <= 0:
            continue
        for row, col in path:
            output[row][col] = color
    return output


def _rival_fill_axis_pairs(grid):
    output = rule_mirror(grid)
    order, by_color = _scan_colors(grid)
    for color in order:
        cells = by_color[color]
        if len(cells) != 2:
            continue
        first, second = cells
        if first[0] == second[0] or first[1] == second[1]:
            for row, col in _axis_segment(first, second):
                output[row][col] = color
    return output


def _rival_use_outermost_same_color_cells(grid):
    order, by_color = _scan_colors(grid)
    output = [list(row) for row in grid]
    for color in order:
        cells = by_color[color]
        if len(cells) < 2:
            continue
        first, second = cells[0], cells[-1]
        dr, dc = second[0] - first[0], second[1] - first[1]
        if abs(dr) == abs(dc) and dr != 0:
            for row, col in _path(first, second):
                output[row][col] = color
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "numeric_ascending_priority": _rival_numeric_ascending,
    "numeric_descending_priority": _rival_numeric_descending,
    "preserve_original_endpoints": _rival_preserve_original_endpoints,
    "fill_only_midpoints": _rival_midpoint_only,
    "fill_positive_slope_only": _rival_positive_slope_only,
    "fill_axis_pairs_too": _rival_fill_axis_pairs,
    "outermost_cells_even_when_repeated": _rival_use_outermost_same_color_cells,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "fill_axis_pairs_too": _rival_fill_axis_pairs,
    "outermost_cells_even_when_repeated": _rival_use_outermost_same_color_cells,
}


def _rival_differs(name: str) -> Callable[[Any], bool]:
    return lambda grid: SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "row_major_not_numeric_ascending": _rival_differs("numeric_ascending_priority"),
    "row_major_not_numeric_descending": _rival_differs("numeric_descending_priority"),
    "later_span_overwrites_original_endpoint": _rival_differs(
        "preserve_original_endpoints"
    ),
    "full_span_not_midpoint_only": _rival_differs("fill_only_midpoints"),
    "both_diagonal_slopes_matter": _rival_differs("fill_positive_slope_only"),
    "axis_pair_is_inert": _rival_differs("fill_axis_pairs_too"),
    "exactly_two_guard_matters": _rival_differs(
        "outermost_cells_even_when_repeated"
    ),
}
WITNESS_RIVALS = {
    "row_major_not_numeric_ascending": ["numeric_ascending_priority"],
    "row_major_not_numeric_descending": ["numeric_descending_priority"],
    "later_span_overwrites_original_endpoint": ["preserve_original_endpoints"],
    "full_span_not_midpoint_only": ["fill_only_midpoints"],
    "both_diagonal_slopes_matter": ["fill_positive_slope_only"],
    "axis_pair_is_inert": ["fill_axis_pairs_too"],
    "exactly_two_guard_matters": ["outermost_cells_even_when_repeated"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose demonstrations leave any declared rival alive."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:
            reasons.append(f"demo {index} is outside the diagonal grammar: {exc}")
            continue
        if expected != pair["output"]:
            reasons.append(f"demo {index} disagrees with the selected rule")
    try:
        query_expected = rule_mirror(query["input"])
    except Exception as exc:
        reasons.append(f"query is outside the diagonal grammar: {exc}")
    else:
        if query_expected != query["output"]:
            reasons.append("query disagrees with the selected rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"demos do not falsify rival: {name}")
    return reasons
