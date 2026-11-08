"""Semantic generator for ``be7f70e60fb7`` — complete straight segments.

For every nonzero color appearing exactly twice, connect its two cells when
those cells share a row or a column.  Colors with diagonal endpoints, one cell,
or three aligned cells remain unchanged.

The generator exposes one exact public axis, ``scene_profile``.  Four scheduled
profiles preserve the canonical shape/palette support while jointly teaching
both positive branches and both rule preconditions instead of relying on
misleading pseudo-axes or an unconditional singleton distractor.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "be7f70e60fb7"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "d264380c5850"

SUMMARY = (
    "Sparse zero-background grids use the same shape/palette signatures as the "
    "five canonical examples.  Every four-example lesson cycles through two "
    "aligned pairs, three aligned pairs, a diagonal repeated-color near miss, "
    "and singleton/aligned-triple cardinality near misses.  The rule connects "
    "only colors appearing exactly twice whose endpoints share a row or column; "
    "all other cells are preserved."
)

INVARIANTS = [
    "background is color 0",
    "every generated input has an exact canonical shape/palette signature",
    "at least one exactly-two color is row- or column-aligned with a visible gap",
    "ordinary lessons include both horizontal and vertical positive examples",
    "alignment_decoy contains one separated diagonal pair that remains unchanged",
    "cardinality_decoys contains one singleton and one gapped aligned triple that remain unchanged",
    "connectable segments do not cross or pass through another color's endpoint",
]

COUNTER_HYPOTHESES = [
    "fill the whole row or column rather than only the bounded segment",
    "connect every repeated color, including diagonal endpoints",
    "connect aligned colors occurring three or more times",
    "delete singleton colors as irrelevant noise",
    "connect only one of several valid pairs",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SCENE_PROFILES = (
    "canonical_two_pairs",
    "canonical_three_pairs",
    "alignment_decoy",
    "cardinality_decoys",
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

_CANONICAL_SIGNATURES = {
    (8, 8, 3),
    (8, 10, 3),
    (9, 8, 4),
    (9, 9, 4),
    (10, 10, 4),
}
_TWO_PAIR_SHAPES = ((8, 8), (8, 10))
_THREE_COLOR_SHAPES = ((9, 8), (9, 9), (10, 10))
_CANONICAL_COLORS = (2, 3, 4, 6, 7, 8, 9)


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Cycle through every semantic branch in each four-example window."""
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


def _color_cells(grid: Sequence[Sequence[int]]) -> dict[int, tuple[tuple[int, int], ...]]:
    cells: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                cells[int(value)].append((r, c))
    return {color: tuple(sorted(points)) for color, points in cells.items()}


def _orientation(points: Sequence[tuple[int, int]]) -> str | None:
    if len(points) < 2:
        return None
    rows = {r for r, _ in points}
    cols = {c for _, c in points}
    if len(rows) == 1:
        return "H"
    if len(cols) == 1:
        return "V"
    return None


def _span(points: Sequence[tuple[int, int]]) -> set[tuple[int, int]]:
    orientation = _orientation(points)
    if orientation == "H":
        row = points[0][0]
        lo, hi = min(c for _, c in points), max(c for _, c in points)
        return {(row, c) for c in range(lo, hi + 1)}
    if orientation == "V":
        col = points[0][1]
        lo, hi = min(r for r, _ in points), max(r for r, _ in points)
        return {(r, col) for r in range(lo, hi + 1)}
    return set()


def _diagonal_path(points: Sequence[tuple[int, int]]) -> set[tuple[int, int]]:
    if len(points) != 2:
        return set()
    (r1, c1), (r2, c2) = points
    dr, dc = r2 - r1, c2 - c1
    if abs(dr) != abs(dc) or abs(dr) < 2:
        return set()
    sr = 1 if dr > 0 else -1
    sc = 1 if dc > 0 else -1
    return {(r1 + i * sr, c1 + i * sc) for i in range(abs(dr) + 1)}


def _connectable_pairs(
    grid: Sequence[Sequence[int]],
) -> list[tuple[int, str, tuple[tuple[int, int], ...]]]:
    pairs = []
    for color, points in sorted(_color_cells(grid).items()):
        orientation = _orientation(points)
        if len(points) == 2 and orientation is not None and len(_span(points)) >= 3:
            pairs.append((color, orientation, points))
    return pairs


def analyze_grid(grid: Sequence[Sequence[int]]) -> dict[str, Any]:
    """Return structural facts shared by observers, tests, and semantic gates."""
    errors = _validate_grid(grid)
    if errors:
        return {
            "valid": False,
            "errors": errors,
            "aligned_pair_count": 0,
            "horizontal_pair_count": 0,
            "vertical_pair_count": 0,
            "diagonal_pair_count": 0,
            "aligned_triple_count": 0,
            "singleton_count": 0,
            "crossing_count": 0,
            "endpoint_overwrite_risk": False,
            "has_bounded_segment": False,
        }

    height, width = len(grid), len(grid[0])
    by_color = _color_cells(grid)
    pairs = _connectable_pairs(grid)
    diagonal_pairs = [
        (color, points)
        for color, points in sorted(by_color.items())
        if len(points) == 2 and bool(_diagonal_path(points))
    ]
    aligned_triples = [
        (color, points)
        for color, points in sorted(by_color.items())
        if len(points) == 3
        and _orientation(points) is not None
        and len(_span(points)) > len(points)
    ]
    singletons = [
        (color, points)
        for color, points in sorted(by_color.items())
        if len(points) == 1
    ]

    intersections: list[tuple[int, int]] = []
    endpoint_risk = False
    for index, (_left_color, left_orientation, left_points) in enumerate(pairs):
        left_span = _span(left_points)
        left_endpoints = set(left_points)
        for _right_color, right_orientation, right_points in pairs[index + 1 :]:
            right_span = _span(right_points)
            right_endpoints = set(right_points)
            for point in sorted(left_span & right_span):
                if point in left_endpoints or point in right_endpoints:
                    endpoint_risk = True
                if left_orientation != right_orientation:
                    intersections.append(point)

    has_bounded_segment = any(
        (
            orientation == "H"
            and (min(c for _, c in points) > 0 or max(c for _, c in points) < width - 1)
        )
        or (
            orientation == "V"
            and (min(r for r, _ in points) > 0 or max(r for r, _ in points) < height - 1)
        )
        for _, orientation, points in pairs
    )

    return {
        "valid": True,
        "errors": [],
        "height": height,
        "width": width,
        "palette_size": len({value for row in grid for value in row}),
        "aligned_pair_count": len(pairs),
        "horizontal_pair_count": sum(orientation == "H" for _, orientation, _ in pairs),
        "vertical_pair_count": sum(orientation == "V" for _, orientation, _ in pairs),
        "diagonal_pair_count": len(diagonal_pairs),
        "aligned_triple_count": len(aligned_triples),
        "singleton_count": len(singletons),
        "crossing_count": len(intersections),
        "endpoint_overwrite_risk": endpoint_risk,
        "has_bounded_segment": has_bounded_segment,
    }


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover the exact public scene profile from the returned input alone."""
    analysis = analyze_grid(grid)
    if not analysis["valid"]:
        return {"scene_profile": None}
    signature = (analysis["height"], analysis["width"], analysis["palette_size"])
    if signature not in _CANONICAL_SIGNATURES or analysis["crossing_count"] != 0:
        return {"scene_profile": None}

    counts = (
        analysis["aligned_pair_count"],
        analysis["diagonal_pair_count"],
        analysis["aligned_triple_count"],
        analysis["singleton_count"],
    )
    if (
        counts == (2, 0, 0, 0)
        and analysis["horizontal_pair_count"] == 1
        and analysis["vertical_pair_count"] == 1
    ):
        profile = "canonical_two_pairs"
    elif (
        counts == (3, 0, 0, 0)
        and analysis["horizontal_pair_count"] >= 1
        and analysis["vertical_pair_count"] >= 1
    ):
        profile = "canonical_three_pairs"
    elif counts == (2, 1, 0, 0):
        profile = "alignment_decoy"
    elif counts == (1, 0, 1, 1):
        profile = "cardinality_decoys"
    else:
        profile = None
    return {"scene_profile": profile}


def _draw_points(grid: list[list[int]], color: int, points: Iterable[tuple[int, int]]) -> None:
    for r, c in points:
        grid[r][c] = color


def _segment_candidates(
    height: int, width: int, orientation: str
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    result = []
    if orientation == "H":
        for r in range(height):
            for c1 in range(width - 2):
                for c2 in range(c1 + 2, width):
                    if c1 == 0 and c2 == width - 1:
                        continue
                    result.append(((r, c1), (r, c2)))
    elif orientation == "V":
        for c in range(width):
            for r1 in range(height - 2):
                for r2 in range(r1 + 2, height):
                    if r1 == 0 and r2 == height - 1:
                        continue
                    result.append(((r1, c), (r2, c)))
    else:
        raise ValueError(f"unknown orientation: {orientation!r}")
    return result


def _render_nonintersecting_pairs(
    height: int,
    width: int,
    orientations: Sequence[str],
    colors: Sequence[int],
    rng,
) -> list[list[int]]:
    for _ in range(100):
        chosen: list[tuple[tuple[int, int], tuple[int, int]]] = []
        occupied_spans: set[tuple[int, int]] = set()
        for orientation in orientations:
            candidates = _segment_candidates(height, width, orientation)
            rng.shuffle(candidates)
            selected = next(
                (candidate for candidate in candidates if not (_span(candidate) & occupied_spans)),
                None,
            )
            if selected is None:
                break
            chosen.append(selected)
            occupied_spans.update(_span(selected))
        if len(chosen) == len(orientations):
            grid = full_grid(height, width, 0)
            for color, points in zip(colors, chosen):
                _draw_points(grid, color, points)
            return grid
    raise RuntimeError(
        f"could not place {len(orientations)} nonintersecting segments in {height}x{width}"
    )


def _render_canonical_pairs(rng, *, count: int) -> list[list[int]]:
    if count == 2:
        height, width = rng.choice(_TWO_PAIR_SHAPES)
        orientations = ["H", "V"]
    elif count == 3:
        height, width = rng.choice(_THREE_COLOR_SHAPES)
        orientations = ["H", "V", rng.choice(("H", "V"))]
    else:
        raise ValueError(f"unsupported pair count: {count}")
    rng.shuffle(orientations)
    colors = rng.sample(_CANONICAL_COLORS, count)
    return _render_nonintersecting_pairs(height, width, orientations, colors, rng)


def _diagonal_candidates(
    height: int, width: int
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    result = []
    for r in range(height):
        for c in range(width):
            for distance in range(2, min(height, width)):
                for dr, dc in ((distance, distance), (distance, -distance)):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < height and 0 <= cc < width:
                        result.append(((r, c), (rr, cc)))
    return result


def _triple_candidates(
    height: int, width: int
) -> list[tuple[tuple[int, int], ...]]:
    result: list[tuple[tuple[int, int], ...]] = []
    for r in range(height):
        for c1 in range(width - 3):
            for c3 in range(c1 + 3, width):
                for c2 in range(c1 + 1, c3):
                    points = ((r, c1), (r, c2), (r, c3))
                    if len(_span(points)) > len(points):
                        result.append(points)
    for c in range(width):
        for r1 in range(height - 3):
            for r3 in range(r1 + 3, height):
                for r2 in range(r1 + 1, r3):
                    points = ((r1, c), (r2, c), (r3, c))
                    if len(_span(points)) > len(points):
                        result.append(points)
    return result


def _render_alignment_decoy(rng) -> list[list[int]]:
    height, width = rng.choice(_THREE_COLOR_SHAPES)
    colors = rng.sample(_CANONICAL_COLORS, 3)
    orientations = ["H", "V"]
    rng.shuffle(orientations)
    first_candidates = _segment_candidates(height, width, orientations[0])
    second_candidates = _segment_candidates(height, width, orientations[1])
    diagonal_candidates = _diagonal_candidates(height, width)
    rng.shuffle(first_candidates)
    rng.shuffle(second_candidates)
    rng.shuffle(diagonal_candidates)

    for first in first_candidates:
        first_span = _span(first)
        for second in second_candidates:
            second_span = _span(second)
            if first_span & second_span:
                continue
            occupied = first_span | second_span
            for diagonal in diagonal_candidates:
                diagonal_path = _diagonal_path(diagonal)
                if diagonal_path & occupied:
                    continue
                grid = full_grid(height, width, 0)
                _draw_points(grid, colors[0], first)
                _draw_points(grid, colors[1], second)
                _draw_points(grid, colors[2], diagonal)
                return grid
    raise RuntimeError("failed to place alignment_decoy scene")


def _render_cardinality_decoys(rng) -> list[list[int]]:
    height, width = rng.choice(_THREE_COLOR_SHAPES)
    colors = rng.sample(_CANONICAL_COLORS, 3)
    pair_orientation = rng.choice(("H", "V"))
    pair_candidates = _segment_candidates(height, width, pair_orientation)
    triple_candidates = _triple_candidates(height, width)
    rng.shuffle(pair_candidates)
    rng.shuffle(triple_candidates)

    for pair in pair_candidates:
        pair_span = _span(pair)
        for triple in triple_candidates:
            triple_span = _span(triple)
            if pair_span & triple_span:
                continue
            occupied = pair_span | triple_span
            free = [
                (r, c)
                for r in range(height)
                for c in range(width)
                if (r, c) not in occupied
            ]
            rng.shuffle(free)
            if not free:
                continue
            grid = full_grid(height, width, 0)
            _draw_points(grid, colors[0], pair)
            _draw_points(grid, colors[1], triple)
            _draw_points(grid, colors[2], (free[0],))
            return grid
    raise RuntimeError("failed to place cardinality_decoys scene")


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
    if profile == "canonical_two_pairs":
        grid = _render_canonical_pairs(rng, count=2)
    elif profile == "canonical_three_pairs":
        grid = _render_canonical_pairs(rng, count=3)
    elif profile == "alignment_decoy":
        grid = _render_alignment_decoy(rng)
    elif profile == "cardinality_decoys":
        grid = _render_cardinality_decoys(rng)
    else:  # guarded above and by draw_choice; retained as fail-loud defense.
        raise RuntimeError(f"unhandled scene_profile: {profile!r}")

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
    """Reject off-manifold or shortcut-ambiguous inputs."""
    del difficulty, meta
    errors = _validate_grid(grid)
    if errors:
        return errors

    height, width = len(grid), len(grid[0])
    palette = {value for row in grid for value in row}
    signature = (height, width, len(palette))
    if signature not in _CANONICAL_SIGNATURES:
        errors.append(
            f"shape/palette signature {signature} is outside canonical signatures "
            f"{sorted(_CANONICAL_SIGNATURES)}"
        )
    if 0 not in palette:
        errors.append("background color 0 must be present")

    for color, points in sorted(_color_cells(grid).items()):
        orientation = _orientation(points)
        if len(points) == 1:
            continue
        if len(points) == 2 and orientation is not None:
            if len(_span(points)) < 3:
                errors.append(f"color {color} aligned pair has no visible gap")
            continue
        if len(points) == 2:
            if not _diagonal_path(points):
                errors.append(
                    f"color {color} non-aligned pair must be a separated 45-degree decoy"
                )
            continue
        if len(points) == 3 and orientation is not None:
            if len(_span(points)) <= len(points):
                errors.append(f"color {color} aligned triple has no internal gap")
            continue
        errors.append(
            f"color {color} must be a singleton, aligned pair, separated diagonal pair, "
            "or gapped aligned triple"
        )

    analysis = analyze_grid(grid)
    if analysis["aligned_pair_count"] == 0:
        errors.append("need at least one exactly-two aligned pair with a visible gap")
    if analysis["crossing_count"]:
        errors.append("connectable segments must not cross in this canonical lesson")
    if analysis["endpoint_overwrite_risk"]:
        errors.append("a connectable segment passes through another pair's endpoint")
    if observe_overrides(grid)["scene_profile"] is None:
        errors.append("input does not match any declared semantic scene profile")
    if not errors and rule_mirror(grid) == [list(row) for row in grid]:
        errors.append("rule is an identity transformation on this input")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Canonical examples and all generated scenes share this strict grammar."""
    return self_check(grid)


def _paint_span(output: list[list[int]], points: Sequence[tuple[int, int]], color: int) -> None:
    for r, c in _span(points):
        output[r][c] = color


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Input-pure Python mirror of the selected canonical Racket authority."""
    errors = _validate_grid(grid)
    if errors:
        raise ValueError(errors[0])
    output = [list(row) for row in grid]
    for color, points in sorted(_color_cells(grid).items()):
        if len(points) == 2 and _orientation(points) is not None:
            _paint_span(output, points, color)
    return output


def _rival_fill_entire_axis(grid):
    output = [list(row) for row in grid]
    height, width = len(output), len(output[0])
    for color, orientation, points in _connectable_pairs(grid):
        cells = (
            {(points[0][0], c) for c in range(width)}
            if orientation == "H"
            else {(r, points[0][1]) for r in range(height)}
        )
        for r, c in cells:
            output[r][c] = color
    return output


def _rival_connect_diagonal_pairs(grid):
    output = rule_mirror(grid)
    for color, points in sorted(_color_cells(grid).items()):
        for r, c in _diagonal_path(points):
            output[r][c] = color
    return output


def _rival_connect_aligned_count_ge_2(grid):
    output = [list(row) for row in grid]
    for color, points in sorted(_color_cells(grid).items()):
        if len(points) >= 2 and _orientation(points) is not None:
            _paint_span(output, points, color)
    return output


def _rival_erase_singletons(grid):
    output = rule_mirror(grid)
    for _color, points in _color_cells(grid).items():
        if len(points) == 1:
            r, c = points[0]
            output[r][c] = 0
    return output


def _rival_lowest_pair_only(grid):
    output = [list(row) for row in grid]
    pairs = _connectable_pairs(grid)
    if pairs:
        color, _orientation_name, points = min(pairs, key=lambda row: row[0])
        _paint_span(output, points, color)
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "fill_entire_row_or_column": _rival_fill_entire_axis,
    "connect_diagonal_pairs": _rival_connect_diagonal_pairs,
    "connect_any_aligned_color_with_at_least_two_cells": _rival_connect_aligned_count_ge_2,
    "erase_singletons_as_noise": _rival_erase_singletons,
    "connect_only_lowest_valued_pair": _rival_lowest_pair_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "connect_diagonal_pairs": _rival_connect_diagonal_pairs,
    "connect_any_aligned_color_with_at_least_two_cells": _rival_connect_aligned_count_ge_2,
    "erase_singletons_as_noise": _rival_erase_singletons,
}


def _analysis_value(grid, key: str):
    return analyze_grid(grid).get(key)


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "bounded_segments_not_full_axes": lambda grid: bool(
        _analysis_value(grid, "has_bounded_segment")
    ),
    "multiple_pairs_all_transform": lambda grid: (
        _analysis_value(grid, "aligned_pair_count") >= 2
    ),
    "both_orientations_are_active": lambda grid: (
        _analysis_value(grid, "horizontal_pair_count") >= 1
        and _analysis_value(grid, "vertical_pair_count") >= 1
    ),
    "diagonal_pair_stays_unchanged": lambda grid: (
        _analysis_value(grid, "diagonal_pair_count") >= 1
    ),
    "aligned_triple_stays_unchanged": lambda grid: (
        _analysis_value(grid, "aligned_triple_count") >= 1
    ),
    "singleton_stays_unchanged": lambda grid: (
        _analysis_value(grid, "singleton_count") >= 1
    ),
}
BRANCH_WITNESSES = tuple(SEMANTIC_WITNESSES)
WITNESS_RIVALS = {
    "bounded_segments_not_full_axes": ["fill_entire_row_or_column"],
    "multiple_pairs_all_transform": ["connect_only_lowest_valued_pair"],
    "diagonal_pair_stays_unchanged": ["connect_diagonal_pairs"],
    "aligned_triple_stays_unchanged": [
        "connect_any_aligned_color_with_at_least_two_cells"
    ],
    "singleton_stays_unchanged": ["erase_singletons_as_noise"],
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
            reasons.append(f"pair {index} disagrees with the selected segment rule")
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
