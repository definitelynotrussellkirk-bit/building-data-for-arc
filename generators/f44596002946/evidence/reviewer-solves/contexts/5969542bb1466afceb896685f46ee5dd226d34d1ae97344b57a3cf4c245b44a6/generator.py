"""Semantic generator for ARC task ``f44596002946``.

For each non-background color that occurs exactly twice, connect its two
markers when they share a row or a column.  Colors are processed in ascending
numeric order, so the larger color wins where two completed segments cross.
Diagonal pairs and colors occurring any number other than two stay unchanged.

The public contract intentionally exposes one exact, observable axis.  Four
scheduled scene profiles form a branch-complete lesson: ordinary multiple
pairs, each possible crossing winner, and negative examples for the two rule
preconditions (alignment and exactly-two cardinality).
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "f44596002946"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "61e6c49f5645"

SUMMARY = (
    "For every nonzero color appearing exactly twice, connect the two cells "
    "when they share a row or column. Process colors in ascending order, so "
    "the numerically larger color wins at a segment crossing. Diagonal pairs "
    "and colors appearing three or more times remain unchanged."
)

INVARIANTS = [
    "background is color 0",
    "every generated grid matches a canonical shape/palette signature",
    "at least one exactly-two color forms a horizontal or vertical pair with a visible gap",
    "no endpoint lies on another connectable segment",
    "crossing lessons contain one interior/interior crossing",
    "both crossing precedence directions occur in every four-example lesson",
    "the negative-precondition lesson contains one diagonal pair and one aligned triple",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SCENE_PROFILES = (
    "canonical_mixed",
    "cross_horizontal_high",
    "cross_vertical_high",
    "precondition_decoys",
)
SCHEDULE_PROFILES = SCENE_PROFILES
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four-profile deterministic curriculum",
        "valid": "|".join(SCENE_PROFILES),
    }
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_CANONICAL_SIGNATURES = {(7, 11, 4), (8, 10, 4), (9, 9, 3)}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Cycle through all four semantic branches in every consecutive window."""
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
        lo, hi = sorted(c for _, c in points)[0], sorted(c for _, c in points)[-1]
        return {(row, c) for c in range(lo, hi + 1)}
    if orientation == "V":
        col = points[0][1]
        lo, hi = sorted(r for r, _ in points)[0], sorted(r for r, _ in points)[-1]
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


def _connectable_pairs(grid: Sequence[Sequence[int]]) -> list[tuple[int, str, tuple[tuple[int, int], ...]]]:
    result = []
    for color, points in sorted(_color_cells(grid).items()):
        orientation = _orientation(points)
        if len(points) == 2 and orientation is not None and len(_span(points)) >= 3:
            result.append((color, orientation, points))
    return result


def analyze_grid(grid: Sequence[Sequence[int]]) -> dict[str, Any]:
    """Return structural facts used by observers, tests, and witnesses."""
    errors = _validate_grid(grid)
    if errors:
        return {
            "valid": False,
            "errors": errors,
            "aligned_pair_count": 0,
            "diagonal_pair_count": 0,
            "aligned_triple_count": 0,
            "crossing_count": 0,
            "crossing_winner_orientation": None,
            "endpoint_overwrite_risk": False,
            "has_bounded_segment": False,
        }

    height, width = len(grid), len(grid[0])
    by_color = _color_cells(grid)
    pairs = _connectable_pairs(grid)
    diagonal_pairs = [
        (color, points)
        for color, points in sorted(by_color.items())
        if len(points) == 2 and _orientation(points) is None
    ]
    aligned_triples = [
        (color, points)
        for color, points in sorted(by_color.items())
        if len(points) == 3 and _orientation(points) is not None
    ]

    intersections: list[tuple[tuple[int, int], int, str, int, str]] = []
    endpoint_risk = False
    for index, (left_color, left_orientation, left_points) in enumerate(pairs):
        left_span = _span(left_points)
        left_endpoints = set(left_points)
        for right_color, right_orientation, right_points in pairs[index + 1 :]:
            right_span = _span(right_points)
            right_endpoints = set(right_points)
            for point in sorted(left_span & right_span):
                if point in left_endpoints or point in right_endpoints:
                    endpoint_risk = True
                if left_orientation != right_orientation:
                    intersections.append(
                        (point, left_color, left_orientation, right_color, right_orientation)
                    )

    crossing_winner = None
    if len(intersections) == 1:
        _, left_color, left_orientation, right_color, right_orientation = intersections[0]
        crossing_winner = left_orientation if left_color > right_color else right_orientation

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
        "crossing_count": len(intersections),
        "crossing_winner_orientation": crossing_winner,
        "endpoint_overwrite_risk": endpoint_risk,
        "has_bounded_segment": has_bounded_segment,
    }


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover the exact public profile from only the returned input grid."""
    analysis = analyze_grid(grid)
    if not analysis["valid"]:
        return {"scene_profile": None}
    signature = (analysis["height"], analysis["width"], analysis["palette_size"])
    if (
        signature == (8, 10, 4)
        and analysis["aligned_pair_count"] == 3
        and analysis["horizontal_pair_count"] >= 1
        and analysis["vertical_pair_count"] >= 1
        and analysis["diagonal_pair_count"] == 0
        and analysis["aligned_triple_count"] == 0
        and analysis["crossing_count"] == 0
    ):
        profile = "canonical_mixed"
    elif (
        signature == (9, 9, 3)
        and analysis["aligned_pair_count"] == 2
        and analysis["horizontal_pair_count"] == 1
        and analysis["vertical_pair_count"] == 1
        and analysis["crossing_count"] == 1
        and analysis["crossing_winner_orientation"] == "H"
    ):
        profile = "cross_horizontal_high"
    elif (
        signature == (9, 9, 3)
        and analysis["aligned_pair_count"] == 2
        and analysis["horizontal_pair_count"] == 1
        and analysis["vertical_pair_count"] == 1
        and analysis["crossing_count"] == 1
        and analysis["crossing_winner_orientation"] == "V"
    ):
        profile = "cross_vertical_high"
    elif (
        signature == (7, 11, 4)
        and analysis["aligned_pair_count"] == 1
        and analysis["diagonal_pair_count"] == 1
        and analysis["aligned_triple_count"] == 1
        and analysis["crossing_count"] == 0
    ):
        profile = "precondition_decoys"
    else:
        profile = None
    return {"scene_profile": profile}


def _draw_points(grid: list[list[int]], color: int, points: Iterable[tuple[int, int]]) -> None:
    for r, c in points:
        grid[r][c] = color


def _segment_candidates(height: int, width: int, orientation: str) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    result = []
    if orientation == "H":
        for r in range(height):
            for c1 in range(width - 2):
                for c2 in range(c1 + 2, width):
                    if c1 == 0 and c2 == width - 1:
                        continue
                    result.append(((r, c1), (r, c2)))
    else:
        for c in range(width):
            for r1 in range(height - 2):
                for r2 in range(r1 + 2, height):
                    if r1 == 0 and r2 == height - 1:
                        continue
                    result.append(((r1, c), (r2, c)))
    return result


def _render_canonical_mixed(rng) -> list[list[int]]:
    height, width = 8, 10
    orientations = ["H", "H", "V"] if rng.randrange(2) == 0 else ["H", "V", "V"]
    rng.shuffle(orientations)
    colors = rng.sample(range(1, 10), 3)

    for _ in range(100):
        chosen: list[tuple[tuple[int, int], tuple[int, int]]] = []
        occupied_spans: set[tuple[int, int]] = set()
        success = True
        for orientation in orientations:
            candidates = _segment_candidates(height, width, orientation)
            rng.shuffle(candidates)
            selected = None
            for candidate in candidates:
                cells = _span(candidate)
                if cells & occupied_spans:
                    continue
                selected = candidate
                break
            if selected is None:
                success = False
                break
            chosen.append(selected)
            occupied_spans.update(_span(selected))
        if success:
            grid = full_grid(height, width, 0)
            for color, points in zip(colors, chosen):
                _draw_points(grid, color, points)
            return grid
    raise RuntimeError("failed to place canonical_mixed scene")


def _render_crossing(rng, *, winner: str) -> list[list[int]]:
    height = width = 9
    cross_r = rng.randint(2, 6)
    cross_c = rng.randint(2, 6)

    while True:
        left = rng.randint(0, cross_c - 1)
        right = rng.randint(cross_c + 1, width - 1)
        if not (left == 0 and right == width - 1):
            break
    while True:
        top = rng.randint(0, cross_r - 1)
        bottom = rng.randint(cross_r + 1, height - 1)
        if not (top == 0 and bottom == height - 1):
            break

    low, high = sorted(rng.sample(range(1, 10), 2))
    horizontal_color, vertical_color = (
        (high, low) if winner == "H" else (low, high)
    )
    grid = full_grid(height, width, 0)
    _draw_points(grid, horizontal_color, ((cross_r, left), (cross_r, right)))
    _draw_points(grid, vertical_color, ((top, cross_c), (bottom, cross_c)))
    return grid


def _diagonal_candidates(height: int, width: int) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    result = []
    for r in range(height):
        for c in range(width):
            for distance in range(2, min(height, width)):
                for dr, dc in ((distance, distance), (distance, -distance)):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < height and 0 <= cc < width:
                        result.append(((r, c), (rr, cc)))
    return result


def _triple_candidates(height: int, width: int) -> list[tuple[tuple[int, int], ...]]:
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


def _render_precondition_decoys(rng) -> list[list[int]]:
    height, width = 7, 11
    colors = rng.sample(range(1, 10), 3)

    orientations = ["H", "V"]
    rng.shuffle(orientations)
    pair_candidates = _segment_candidates(height, width, orientations[0])
    rng.shuffle(pair_candidates)
    diagonal_candidates = _diagonal_candidates(height, width)
    rng.shuffle(diagonal_candidates)
    triple_candidates = _triple_candidates(height, width)
    rng.shuffle(triple_candidates)

    for pair in pair_candidates:
        pair_footprint = _span(pair)
        for diagonal in diagonal_candidates:
            diagonal_footprint = _diagonal_path(diagonal)
            if diagonal_footprint & pair_footprint:
                continue
            for triple in triple_candidates:
                triple_footprint = _span(triple)
                if triple_footprint & (pair_footprint | diagonal_footprint):
                    continue
                grid = full_grid(height, width, 0)
                _draw_points(grid, colors[0], pair)
                _draw_points(grid, colors[1], diagonal)
                _draw_points(grid, colors[2], triple)
                return grid
    raise RuntimeError("failed to place precondition_decoys scene")


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
    rng = ctx.draw_rng(f"scene_{band}")
    if profile == "canonical_mixed":
        grid = _render_canonical_mixed(rng)
    elif profile == "cross_horizontal_high":
        grid = _render_crossing(rng, winner="H")
    elif profile == "cross_vertical_high":
        grid = _render_crossing(rng, winner="V")
    elif profile == "precondition_decoys":
        grid = _render_precondition_decoys(rng)
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
    """Reject malformed, identity, ambiguous, or off-manifold inputs."""
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

    aligned_pairs = 0
    for color, points in sorted(_color_cells(grid).items()):
        orientation = _orientation(points)
        if len(points) == 2 and orientation is not None:
            if len(_span(points)) < 3:
                errors.append(f"color {color} aligned pair has no visible gap")
            else:
                aligned_pairs += 1
        elif len(points) == 2:
            if not _diagonal_path(points):
                errors.append(
                    f"color {color} non-aligned pair must be a separated 45-degree decoy"
                )
        elif len(points) == 3 and orientation is not None:
            if len(_span(points)) == len(points):
                errors.append(f"color {color} aligned triple has no internal gap")
        else:
            errors.append(
                f"color {color} must be an aligned pair, separated diagonal pair, "
                "or aligned triple"
            )

    analysis = analyze_grid(grid)
    if aligned_pairs == 0:
        errors.append("need at least one exactly-two aligned pair with a visible gap")
    if analysis["endpoint_overwrite_risk"]:
        errors.append("a connectable segment passes through another pair's endpoint")
    if not errors and rule_mirror(grid) == [list(row) for row in grid]:
        errors.append("rule is an identity transformation on this input")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Generated and canonical inputs share this exact structural envelope."""
    return self_check(grid)


def _draw_line(output: list[list[int]], points: Sequence[tuple[int, int]], color: int) -> None:
    for r, c in _span(points):
        output[r][c] = color


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Input-pure Python mirror of the selected canonical Racket authority."""
    output = [list(row) for row in grid]
    cells = _color_cells(grid)
    for color in sorted(cells):
        points = cells[color]
        if len(points) == 2 and _orientation(points) is not None:
            _draw_line(output, points, color)
    return output


def _rival_fill_entire_axis(grid):
    output = [list(row) for row in grid]
    height, width = len(output), len(output[0])
    for color, orientation, points in _connectable_pairs(grid):
        if orientation == "H":
            cells = {(points[0][0], c) for c in range(width)}
        else:
            cells = {(r, points[0][1]) for r in range(height)}
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
            _draw_line(output, points, color)
    return output


def _paint_by_orientation_priority(grid, *, last: str):
    output = [list(row) for row in grid]
    pairs = _connectable_pairs(grid)
    first = "V" if last == "H" else "H"
    for orientation in (first, last):
        for color, pair_orientation, points in pairs:
            if pair_orientation == orientation:
                _draw_line(output, points, color)
    return output


def _rival_horizontal_always_wins(grid):
    return _paint_by_orientation_priority(grid, last="H")


def _rival_vertical_always_wins(grid):
    return _paint_by_orientation_priority(grid, last="V")


def _rival_lowest_pair_only(grid):
    output = [list(row) for row in grid]
    pairs = _connectable_pairs(grid)
    if pairs:
        color, _, points = min(pairs, key=lambda row: row[0])
        _draw_line(output, points, color)
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "fill_entire_row_or_column": _rival_fill_entire_axis,
    "connect_diagonal_pairs": _rival_connect_diagonal_pairs,
    "connect_any_aligned_color_with_at_least_two_cells": _rival_connect_aligned_count_ge_2,
    "horizontal_segment_always_wins_crossings": _rival_horizontal_always_wins,
    "vertical_segment_always_wins_crossings": _rival_vertical_always_wins,
    "connect_only_lowest_valued_pair": _rival_lowest_pair_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "connect_diagonal_pairs": _rival_connect_diagonal_pairs,
    "connect_any_aligned_color_with_at_least_two_cells": _rival_connect_aligned_count_ge_2,
    "vertical_segment_always_wins_crossings": _rival_vertical_always_wins,
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
    "diagonal_pair_stays_unchanged": lambda grid: (
        _analysis_value(grid, "diagonal_pair_count") >= 1
    ),
    "aligned_triple_stays_unchanged": lambda grid: (
        _analysis_value(grid, "aligned_triple_count") >= 1
    ),
    "horizontal_higher_color_wins": lambda grid: (
        _analysis_value(grid, "crossing_winner_orientation") == "H"
    ),
    "vertical_higher_color_wins": lambda grid: (
        _analysis_value(grid, "crossing_winner_orientation") == "V"
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
    "horizontal_higher_color_wins": ["vertical_segment_always_wins_crossings"],
    "vertical_higher_color_wins": ["horizontal_segment_always_wins_crossings"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require one complete scheduled lesson and refutation of every rival."""
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
            reasons.append(f"pair {index} disagrees with the selected connect-pairs rule")
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
