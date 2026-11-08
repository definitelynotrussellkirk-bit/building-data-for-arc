"""Generator for filling diagonal spans between matching-color endpoints.

Each active color appears exactly twice.  Its two cells are endpoints of a
non-trivial 45-degree diagonal, and the Racket authority paints the inclusive
span for colors in ascending numeric order.  Consequently the larger color
wins wherever two spans overlap.  The four-sample schedule deliberately covers
separated spans, an interior crossing, a lower-colored endpoint that is
subsequently overwritten, and a higher-colored endpoint that survives.

Exact override axes: grid_h, grid_w, pair_count, scene_profile.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "42ce66faea37"
TASK_ID = "42ce66faea37"
VERSION = "3.0.0"  # teach canonical overlap/color-priority branches; exact axes
RULE_HASH = "2f834dfaa789"  # canonical_rule_hash(TASK_ID)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SCENE_PROFILES = (
    "disjoint",
    "interior_cross",
    "endpoint_owner_lower",
    "endpoint_owner_higher",
)
SCHEDULE_PROFILES = SCENE_PROFILES

SUMMARY = (
    "A 0-background 8..14 by 8..14 grid contains 2..4 colors, each appearing "
    "exactly twice as the endpoints of a non-trivial 45-degree diagonal. "
    "For every color, paint the inclusive diagonal span between its endpoints. "
    "Spans may be disjoint, cross at blank interior cells, or pass through an "
    "endpoint of another color. Colors are painted in ascending numeric order, "
    "so the larger color owns every overlap. Every four consecutive samples "
    "cover all four collision profiles."
)

INVARIANTS = [
    "background is 0 and all cells are ARC colors 0..9",
    "there are 2..4 active colors and each appears exactly twice",
    "same-color endpoints lie on a 45-degree diagonal with span at least 2",
    "ordinary draws always change under the canonical diagonal-fill rule",
    "overlap ownership follows ascending-color paint order (larger color wins)",
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
        "default": "four-sample semantic schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
}

Point = tuple[int, int]
EndpointPath = tuple[Point, Point]

# Each template is (active_square_size, four endpoint paths).  The first two
# paths carry the profile-defining relation.  Later paths are disjoint extras,
# so pair_count can vary without changing the observed profile.
_TEMPLATE_BANK: dict[str, tuple[tuple[int, tuple[EndpointPath, ...]], ...]] = {
    "disjoint": (
        (
            8,
            (
                ((0, 0), (3, 3)),
                ((0, 7), (3, 4)),
                ((5, 0), (7, 2)),
                ((5, 7), (7, 5)),
            ),
        ),
        (
            8,
            (
                ((0, 0), (4, 4)),
                ((0, 7), (3, 4)),
                ((5, 0), (7, 2)),
                ((5, 7), (7, 5)),
            ),
        ),
        (
            10,
            (
                ((0, 0), (6, 6)),
                ((0, 9), (3, 6)),
                ((7, 0), (9, 2)),
                ((7, 9), (9, 7)),
            ),
        ),
    ),
    "interior_cross": (
        (
            8,
            (
                ((1, 1), (5, 5)),
                ((1, 5), (5, 1)),
                ((5, 7), (7, 5)),
                ((0, 7), (2, 5)),
            ),
        ),
        (
            8,
            (
                ((0, 1), (6, 7)),
                ((0, 7), (6, 1)),
                ((0, 0), (2, 2)),
                ((5, 7), (7, 5)),
            ),
        ),
        (
            10,
            (
                ((1, 1), (7, 7)),
                ((1, 7), (7, 1)),
                ((0, 9), (2, 7)),
                ((7, 9), (9, 7)),
            ),
        ),
    ),
    "endpoint_owner_lower": (
        (
            8,
            (
                ((1, 7), (5, 3)),
                ((3, 1), (7, 5)),
                ((0, 0), (2, 2)),
                ((0, 5), (2, 3)),
            ),
        ),
        (
            8,
            (
                ((1, 0), (5, 4)),
                ((3, 6), (7, 2)),
                ((0, 7), (2, 5)),
                ((0, 2), (2, 4)),
            ),
        ),
        (
            10,
            (
                ((1, 9), (6, 4)),
                ((3, 1), (8, 6)),
                ((0, 0), (2, 2)),
                ((0, 7), (2, 5)),
            ),
        ),
    ),
    "endpoint_owner_higher": (),  # shares geometry with endpoint_owner_lower
}

_CANONICAL_CANVASES = ((8, 8), (9, 10), (10, 10), (8, 12), (11, 9))
_EXPANDED_CANVASES = {
    "easy": ((8, 9), (9, 9), (9, 11), (10, 8)),
    "medium": ((10, 11), (11, 10), (12, 12), (9, 13)),
    "hard": ((12, 13), (13, 12), (14, 14), (11, 14)),
}
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


def _band(difficulty: Any) -> str:
    return difficulty if difficulty in _EXPANDED_CANVASES else "medium"


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """A four-cycle; every four consecutive sample indexes contain all modes."""
    del difficulty
    return SCENE_PROFILES[(int(seed) + int(sample_index)) % len(SCENE_PROFILES)]


def _scheduled_canvas(ctx, seed: int, sample_index: int, band: str) -> tuple[int, int]:
    rng = ctx.draw_rng("canvas_schedule")
    # A pinned one-in-three anchor keeps every band on canonical shape support.
    if (int(seed) + int(sample_index)) % 3 == 0:
        return rng.choice(_CANONICAL_CANVASES)
    return rng.choice(_EXPANDED_CANVASES[band])


def _scheduled_pair_count(seed: int, sample_index: int, band: str) -> int:
    residue = (int(seed) + int(sample_index)) % 4
    if residue == 0:
        return 2  # canonical palette anchor in every band
    if band == "easy":
        return (2, 2, 3, 3)[residue]
    if band == "hard":
        return (2, 3, 4, 4)[residue]
    return (2, 3, 3, 4)[residue]


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
    return tuple((a[0] + k * sr, a[1] + k * sc) for k in range(abs(dr) + 1))


def _transform_point(point: Point, size: int, name: str) -> Point:
    r, c = point
    last = size - 1
    if name == "identity":
        return r, c
    if name == "rot90":
        return c, last - r
    if name == "rot180":
        return last - r, last - c
    if name == "rot270":
        return last - c, r
    if name == "flip_lr":
        return r, last - c
    if name == "flip_ud":
        return last - r, c
    if name == "transpose":
        return c, r
    if name == "anti_transpose":
        return last - c, last - r
    raise ValueError(f"unknown D4 transform: {name}")


def _transform_paths(
    paths: Sequence[EndpointPath], size: int, name: str, top: int, left: int
) -> tuple[EndpointPath, ...]:
    transformed: list[EndpointPath] = []
    for a, b in paths:
        aa = _transform_point(a, size, name)
        bb = _transform_point(b, size, name)
        transformed.append(
            (((aa[0] + top), (aa[1] + left)), ((bb[0] + top), (bb[1] + left)))
        )
    return tuple(transformed)


def _templates_for(profile: str, height: int, width: int):
    source_profile = "endpoint_owner_lower" if profile.startswith("endpoint_owner_") else profile
    return tuple(
        template
        for template in _TEMPLATE_BANK[source_profile]
        if template[0] <= min(height, width)
    )


def _choose_colors(ctx, pair_count: int, profile: str) -> tuple[int, ...]:
    rng = ctx.draw_rng("color_assignment")
    selected = rng.sample(list(range(1, 10)), pair_count)
    if not profile.startswith("endpoint_owner_"):
        rng.shuffle(selected)
        return tuple(selected)

    first_two = sorted(selected[:2])
    if profile == "endpoint_owner_lower":
        owner, other = first_two[0], first_two[1]
    else:
        owner, other = first_two[1], first_two[0]
    extras = selected[2:]
    rng.shuffle(extras)
    return (owner, other, *extras)


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

    # Singleton bounds/options preserve exact keyed-draw provenance while the
    # explicit validation above enforces the full declared override domain.
    height = ctx.draw_int("grid_h", requested_h, requested_h)
    width = ctx.draw_int("grid_w", requested_w, requested_w)
    pair_count = ctx.draw_int("pair_count", requested_count, requested_count)
    profile = ctx.draw_choice("scene_profile", [requested_profile])

    layout_rng = ctx.draw_rng("layout")
    template_size, template_paths = layout_rng.choice(
        _templates_for(profile, height, width)
    )
    transform = layout_rng.choice(_D4_NAMES)
    top = layout_rng.randint(0, height - template_size)
    left = layout_rng.randint(0, width - template_size)
    paths = _transform_paths(
        template_paths[:pair_count], template_size, transform, top, left
    )
    colors = _choose_colors(ctx, pair_count, profile)

    grid = full_grid(height, width, 0)
    for color, (a, b) in zip(colors, paths):
        if grid[a[0]][a[1]] != 0 or grid[b[0]][b[1]] != 0:
            raise AssertionError("template endpoints unexpectedly overlap")
        grid[a[0]][a[1]] = color
        grid[b[0]][b[1]] = color
    return grid


def _is_rectangular_grid(grid: Any) -> bool:
    return (
        isinstance(grid, (list, tuple))
        and bool(grid)
        and isinstance(grid[0], (list, tuple))
        and bool(grid[0])
        and all(isinstance(row, (list, tuple)) and len(row) == len(grid[0]) for row in grid)
    )


def _analyze(grid: Any) -> dict[str, Any]:
    analysis: dict[str, Any] = {
        "errors": [],
        "height": 0,
        "width": 0,
        "paths": {},
        "pair_count": 0,
        "scene_profile": None,
        "endpoint_crossings": [],
        "interior_crossings": [],
    }
    errors: list[str] = analysis["errors"]
    if not _is_rectangular_grid(grid):
        errors.append("grid must be nonempty and rectangular")
        return analysis

    height, width = len(grid), len(grid[0])
    analysis["height"] = height
    analysis["width"] = width
    by_color: dict[int, list[Point]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) must be an integer ARC color 0..9")
                continue
            if value != 0:
                by_color[value].append((r, c))

    analysis["pair_count"] = len(by_color)
    if not 2 <= len(by_color) <= 4:
        errors.append(f"expected 2..4 active colors, found {len(by_color)}")

    paths: dict[int, tuple[Point, ...]] = {}
    for color, endpoints in sorted(by_color.items()):
        if len(endpoints) != 2:
            errors.append(
                f"color {color} appears {len(endpoints)} times; expected two endpoints"
            )
            continue
        a, b = endpoints
        dr, dc = b[0] - a[0], b[1] - a[1]
        if abs(dr) != abs(dc) or abs(dr) < 2:
            errors.append(
                f"color {color} endpoints must be a non-trivial 45-degree span"
            )
            continue
        paths[color] = _path(a, b)
    analysis["paths"] = paths

    if errors:
        return analysis

    colors = sorted(paths)
    endpoint_crossings: list[tuple[Point, int, int]] = []
    interior_crossings: list[tuple[Point, int, int]] = []
    for index, left_color in enumerate(colors):
        left_path = paths[left_color]
        left_endpoints = {left_path[0], left_path[-1]}
        for right_color in colors[index + 1 :]:
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
                else:
                    errors.append("two colors may not share the same endpoint cell")

    analysis["endpoint_crossings"] = endpoint_crossings
    analysis["interior_crossings"] = interior_crossings
    if endpoint_crossings:
        relations = {"lower" if owner < other else "higher" for _, owner, other in endpoint_crossings}
        if len(relations) != 1:
            errors.append("endpoint crossings mix lower-owner and higher-owner relations")
        else:
            analysis["scene_profile"] = f"endpoint_owner_{next(iter(relations))}"
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
    """Accept the canonical teaching grammar and reject rule-hiding impostors."""
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
    """Strict task-linked predicate used by the semantic census."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analyze(grid)
    if not 8 <= analysis["height"] <= 14 or not 8 <= analysis["width"] <= 14:
        errors.append("canvas must lie in the canonical-anchored 8..14 range")
    spans = [len(path) - 1 for path in analysis["paths"].values()]
    if any(span > 8 for span in spans):
        errors.append("diagonal spans must be at most 8 cells in this curriculum")
    if analysis["scene_profile"] not in SCENE_PROFILES:
        errors.append("scene profile is not one of the declared semantic branches")
    return errors


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror for semantic tests only; Racket remains authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid diagonal-endpoint scene: " + "; ".join(analysis["errors"]))
    output = [list(row) for row in grid]
    for color in sorted(analysis["paths"]):
        for r, c in analysis["paths"][color]:
            output[r][c] = color
    return output


def _rival_lower_color_wins(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    output = [list(row) for row in grid]
    for color in sorted(analysis["paths"], reverse=True):
        for r, c in analysis["paths"][color]:
            output[r][c] = color
    return output


def _rival_preserve_original_endpoints(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    output = [list(row) for row in grid]
    original_nonzero = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    for color in sorted(analysis["paths"]):
        for r, c in analysis["paths"][color]:
            if (r, c) not in original_nonzero or grid[r][c] == color:
                output[r][c] = color
    return output


def _rival_midpoint_only(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    output = [list(row) for row in grid]
    for color in sorted(analysis["paths"]):
        path = analysis["paths"][color]
        midpoint = path[len(path) // 2]
        output[midpoint[0]][midpoint[1]] = color
    return output


def _rival_positive_slope_only(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    output = [list(row) for row in grid]
    for color in sorted(analysis["paths"]):
        path = analysis["paths"][color]
        if (path[-1][0] - path[0][0]) * (path[-1][1] - path[0][1]) <= 0:
            continue
        for r, c in path:
            output[r][c] = color
    return output


def _rival_other_path_wins_endpoint_cross(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    output = rule_mirror(grid)
    for (r, c), _owner, other in analysis["endpoint_crossings"]:
        output[r][c] = other
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "lower_color_wins_overlap": _rival_lower_color_wins,
    "preserve_original_endpoints": _rival_preserve_original_endpoints,
    "fill_only_midpoints": _rival_midpoint_only,
    "fill_positive_slope_only": _rival_positive_slope_only,
    "other_path_always_wins_endpoint_cross": _rival_other_path_wins_endpoint_cross,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _has_both_slopes(grid) -> bool:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return False
    slopes = {
        1 if (path[-1][0] - path[0][0]) * (path[-1][1] - path[0][1]) > 0 else -1
        for path in analysis["paths"].values()
    }
    return slopes == {-1, 1}


def _has_long_span(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and any(
        len(path) - 1 >= 3 for path in analysis["paths"].values()
    )


def _profile_is(name: str) -> Callable[[Any], bool]:
    return lambda grid: _analyze(grid)["scene_profile"] == name and not _analyze(grid)["errors"]


SEMANTIC_WITNESSES = {
    "both_diagonal_orientations": _has_both_slopes,
    "long_span_requires_full_fill": _has_long_span,
    "interior_cross_uses_color_priority": _profile_is("interior_cross"),
    "lower_endpoint_is_overwritten": _profile_is("endpoint_owner_lower"),
    "higher_endpoint_survives": _profile_is("endpoint_owner_higher"),
}
WITNESS_RIVALS = {
    "both_diagonal_orientations": ["fill_positive_slope_only"],
    "long_span_requires_full_fill": ["fill_only_midpoints"],
    "interior_cross_uses_color_priority": ["lower_color_wins_overlap"],
    "lower_endpoint_is_overwritten": [
        "preserve_original_endpoints",
        "lower_color_wins_overlap",
    ],
    "higher_endpoint_survives": ["other_path_always_wins_endpoint_cross"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any episode whose demonstrations leave a named rival alive."""
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
            reasons.append(f"demo {index} disagrees with the diagonal-fill rule")
    try:
        query_expected = rule_mirror(query["input"])
    except Exception as exc:
        reasons.append(f"query is outside the diagonal grammar: {exc}")
    else:
        if query_expected != query["output"]:
            reasons.append("query disagrees with the diagonal-fill rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"demos do not falsify rival: {name}")
    return reasons
