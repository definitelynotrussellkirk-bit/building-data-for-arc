"""Semantic generator for ARC task ``c831492f416e``.

For every non-background color that occurs exactly twice, connect the two
markers when they share a row or a column. Colors are processed in ascending
numeric order, so the numerically larger color wins where completed segments
cross. Diagonal pairs and colors occurring any number other than two are
preserved but not connected.

The public contract intentionally exposes one exact, grid-observable axis.
Every five consecutive examples cover the ordinary disjoint case, the minimum
visible gap, both crossing-precedence directions, and both rule preconditions.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "c831492f416e"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "91f9e86ee830"

SUMMARY = (
    "Connect every nonzero color that appears exactly twice when its two cells "
    "share a row or column. Fill only the inclusive segment between the two "
    "endpoints. Process colors in ascending order, so the numerically larger "
    "color wins at an interior crossing. Diagonal pairs and aligned triples "
    "remain unchanged."
)

INVARIANTS = [
    "background is color 0",
    "every ordinary scene has at least one exactly-two aligned pair with a visible gap",
    "no connectable segment passes through another pair's endpoint",
    "crossing scenes contain one interior/interior crossing",
    "both numeric crossing-precedence directions occur in every five-example lesson",
    "the precondition scene contains one diagonal pair and one aligned triple",
]

EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.80

SCENE_PROFILES = (
    "canonical_disjoint",
    "short_gap",
    "cross_horizontal_high",
    "cross_vertical_high",
    "precondition_decoys",
)
SCHEDULE_PROFILES = SCENE_PROFILES
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five-profile deterministic semantic curriculum",
        "valid": "|".join(SCENE_PROFILES),
    }
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

# (height, width, palette size including background) from all canonical inputs.
_CANONICAL_SIGNATURES = {
    (6, 10, 3),
    (7, 9, 3),
    (8, 8, 3),
    (8, 10, 3),
    (9, 7, 3),
}
_CANONICAL_SHAPES = tuple(sorted((height, width) for height, width, _ in _CANONICAL_SIGNATURES))
_SHAPES_BY_BAND = {
    "easy": ((7, 9), (8, 8)),
    "medium": ((6, 10), (8, 10), (9, 7)),
    "hard": _CANONICAL_SHAPES,
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Cover all semantic profiles in every five consecutive examples."""
    del seed
    _band(difficulty)
    if isinstance(sample_index, bool) or not isinstance(sample_index, int):
        raise ValueError("sample_index must be an integer")
    return SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]


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
    if len({r for r, _ in points}) == 1:
        return "H"
    if len({c for _, c in points}) == 1:
        return "V"
    return None


def _span(points: Sequence[tuple[int, int]]) -> set[tuple[int, int]]:
    orientation = _orientation(points)
    if orientation == "H":
        row = points[0][0]
        columns = sorted(c for _, c in points)
        return {(row, c) for c in range(columns[0], columns[-1] + 1)}
    if orientation == "V":
        col = points[0][1]
        rows = sorted(r for r, _ in points)
        return {(r, col) for r in range(rows[0], rows[-1] + 1)}
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
        if len(points) == 2 and orientation is not None:
            pairs.append((color, orientation, points))
    return pairs


def analyze_grid(grid: Sequence[Sequence[int]]) -> dict[str, Any]:
    """Return structural facts shared by observers, checks, and audit tools."""
    errors = _validate_grid(grid)
    if errors:
        return {
            "valid": False,
            "errors": errors,
            "aligned_pair_count": 0,
            "horizontal_pair_count": 0,
            "vertical_pair_count": 0,
            "short_pair_count": 0,
            "diagonal_pair_count": 0,
            "aligned_triple_count": 0,
            "crossing_count": 0,
            "crossing_point": None,
            "crossing_winner_orientation": None,
            "crossing_high_color": None,
            "crossing_low_color": None,
            "endpoint_overwrite_risk": False,
            "has_bounded_segment": False,
            "decoy_colors": (),
            "invalid_color_specs": (),
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

    allowed_colors = {
        color for color, _, _ in pairs
    } | {
        color for color, _ in diagonal_pairs
    } | {
        color for color, _ in aligned_triples
    }
    invalid_specs = tuple(
        (color, len(points), _orientation(points))
        for color, points in sorted(by_color.items())
        if color not in allowed_colors
    )

    intersections: list[tuple[tuple[int, int], int, str, int, str]] = []
    endpoint_risk = False
    for index, (left_color, left_orientation, left_points) in enumerate(pairs):
        left_span = _span(left_points)
        left_endpoints = set(left_points)
        for right_color, right_orientation, right_points in pairs[index + 1 :]:
            right_span = _span(right_points)
            right_endpoints = set(right_points)
            if (left_span - left_endpoints) & right_endpoints:
                endpoint_risk = True
            if (right_span - right_endpoints) & left_endpoints:
                endpoint_risk = True
            if left_orientation != right_orientation:
                for point in sorted(left_span & right_span):
                    intersections.append(
                        (point, left_color, left_orientation, right_color, right_orientation)
                    )

    crossing_point = None
    crossing_winner = None
    crossing_high = None
    crossing_low = None
    if len(intersections) == 1:
        point, left_color, left_orientation, right_color, right_orientation = intersections[0]
        crossing_point = point
        crossing_high = max(left_color, right_color)
        crossing_low = min(left_color, right_color)
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
        "short_pair_count": sum(len(_span(points)) == 3 for _, _, points in pairs),
        "diagonal_pair_count": len(diagonal_pairs),
        "aligned_triple_count": len(aligned_triples),
        "crossing_count": len(intersections),
        "crossing_point": crossing_point,
        "crossing_winner_orientation": crossing_winner,
        "crossing_high_color": crossing_high,
        "crossing_low_color": crossing_low,
        "endpoint_overwrite_risk": endpoint_risk,
        "has_bounded_segment": has_bounded_segment,
        "decoy_colors": tuple(
            sorted([color for color, _ in diagonal_pairs] + [color for color, _ in aligned_triples])
        ),
        "invalid_color_specs": invalid_specs,
    }


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover the exact public profile from only the returned input grid."""
    analysis = analyze_grid(grid)
    if not analysis["valid"]:
        return {"scene_profile": None}

    if (
        analysis["aligned_pair_count"] == 1
        and analysis["diagonal_pair_count"] == 1
        and analysis["aligned_triple_count"] == 1
        and analysis["crossing_count"] == 0
        and not analysis["invalid_color_specs"]
    ):
        profile = "precondition_decoys"
    elif (
        analysis["aligned_pair_count"] == 2
        and analysis["horizontal_pair_count"] == 1
        and analysis["vertical_pair_count"] == 1
        and analysis["diagonal_pair_count"] == 0
        and analysis["aligned_triple_count"] == 0
        and analysis["crossing_count"] == 1
        and analysis["crossing_winner_orientation"] == "H"
    ):
        profile = "cross_horizontal_high"
    elif (
        analysis["aligned_pair_count"] == 2
        and analysis["horizontal_pair_count"] == 1
        and analysis["vertical_pair_count"] == 1
        and analysis["diagonal_pair_count"] == 0
        and analysis["aligned_triple_count"] == 0
        and analysis["crossing_count"] == 1
        and analysis["crossing_winner_orientation"] == "V"
    ):
        profile = "cross_vertical_high"
    elif (
        analysis["aligned_pair_count"] == 2
        and analysis["horizontal_pair_count"] == 1
        and analysis["vertical_pair_count"] == 1
        and analysis["diagonal_pair_count"] == 0
        and analysis["aligned_triple_count"] == 0
        and analysis["crossing_count"] == 0
        and analysis["short_pair_count"] >= 1
    ):
        profile = "short_gap"
    elif (
        analysis["aligned_pair_count"] == 2
        and analysis["horizontal_pair_count"] == 1
        and analysis["vertical_pair_count"] == 1
        and analysis["diagonal_pair_count"] == 0
        and analysis["aligned_triple_count"] == 0
        and analysis["crossing_count"] == 0
        and analysis["short_pair_count"] == 0
    ):
        profile = "canonical_disjoint"
    else:
        profile = None
    return {"scene_profile": profile}


def _draw_points(grid: list[list[int]], color: int, points: Iterable[tuple[int, int]]) -> None:
    for r, c in points:
        grid[r][c] = color


def _segment_candidates(
    height: int,
    width: int,
    orientation: str,
    *,
    distances: set[int] | None = None,
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    result = []
    if orientation == "H":
        for row in range(height):
            for left in range(width - 2):
                for right in range(left + 2, width):
                    distance = right - left
                    if distances is not None and distance not in distances:
                        continue
                    if left == 0 and right == width - 1:
                        continue
                    result.append(((row, left), (row, right)))
    elif orientation == "V":
        for col in range(width):
            for top in range(height - 2):
                for bottom in range(top + 2, height):
                    distance = bottom - top
                    if distances is not None and distance not in distances:
                        continue
                    if top == 0 and bottom == height - 1:
                        continue
                    result.append(((top, col), (bottom, col)))
    else:
        raise ValueError(f"unknown orientation: {orientation!r}")
    return result


def _render_disjoint(rng, *, height: int, width: int, short_gap: bool) -> list[list[int]]:
    short_orientation = rng.choice(("H", "V")) if short_gap else None
    candidate_sets: dict[str, list[tuple[tuple[int, int], tuple[int, int]]]] = {}
    for orientation in ("H", "V"):
        if orientation == short_orientation:
            distances = {2}
        else:
            axis_length = width if orientation == "H" else height
            distances = set(range(3, axis_length))
        candidates = _segment_candidates(
            height, width, orientation, distances=distances
        )
        rng.shuffle(candidates)
        candidate_sets[orientation] = candidates

    for horizontal in candidate_sets["H"]:
        h_span = _span(horizontal)
        for vertical in candidate_sets["V"]:
            if h_span & _span(vertical):
                continue
            colors = rng.sample(range(1, 10), 2)
            grid = full_grid(height, width, 0)
            _draw_points(grid, colors[0], horizontal)
            _draw_points(grid, colors[1], vertical)
            return grid
    raise RuntimeError("failed to place disjoint pair scene")


def _render_crossing(rng, *, height: int, width: int, winner: str) -> list[list[int]]:
    # Keep the crossing strictly inside both spans so no pair endpoint can be
    # overwritten by the other segment.
    cross_r = rng.randint(1, height - 2)
    cross_c = rng.randint(1, width - 2)

    horizontal_candidates = [
        pair
        for pair in _segment_candidates(height, width, "H")
        if pair[0][0] == cross_r
        and pair[0][1] < cross_c < pair[1][1]
        and pair[1][1] - pair[0][1] >= 3
    ]
    vertical_candidates = [
        pair
        for pair in _segment_candidates(height, width, "V")
        if pair[0][1] == cross_c
        and pair[0][0] < cross_r < pair[1][0]
        and pair[1][0] - pair[0][0] >= 3
    ]
    if not horizontal_candidates or not vertical_candidates:
        raise RuntimeError("failed to enumerate crossing segments")
    horizontal = rng.choice(horizontal_candidates)
    vertical = rng.choice(vertical_candidates)

    low, high = sorted(rng.sample(range(1, 10), 2))
    horizontal_color, vertical_color = (high, low) if winner == "H" else (low, high)
    grid = full_grid(height, width, 0)
    _draw_points(grid, horizontal_color, horizontal)
    _draw_points(grid, vertical_color, vertical)
    return grid


def _diagonal_candidates(
    height: int, width: int
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    result = []
    for r in range(height):
        for c in range(width):
            for distance in range(2, min(height, width)):
                for dc in (-distance, distance):
                    rr, cc = r + distance, c + dc
                    if 0 <= rr < height and 0 <= cc < width:
                        result.append(((r, c), (rr, cc)))
    return result


def _triple_candidates(
    height: int, width: int
) -> list[tuple[tuple[int, int], ...]]:
    result: list[tuple[tuple[int, int], ...]] = []
    for row in range(height):
        for left in range(width - 3):
            for right in range(left + 3, width):
                for middle in range(left + 1, right):
                    points = ((row, left), (row, middle), (row, right))
                    if len(_span(points)) > len(points):
                        result.append(points)
    for col in range(width):
        for top in range(height - 3):
            for bottom in range(top + 3, height):
                for middle in range(top + 1, bottom):
                    points = ((top, col), (middle, col), (bottom, col))
                    if len(_span(points)) > len(points):
                        result.append(points)
    return result


def _render_precondition_decoys(rng, *, height: int, width: int) -> list[list[int]]:
    pair_orientation = rng.choice(("H", "V"))
    pair_candidates = _segment_candidates(height, width, pair_orientation)
    diagonal_candidates = _diagonal_candidates(height, width)
    triple_candidates = _triple_candidates(height, width)
    rng.shuffle(pair_candidates)
    rng.shuffle(diagonal_candidates)
    rng.shuffle(triple_candidates)

    for pair in pair_candidates:
        pair_footprint = _span(pair)
        for diagonal in diagonal_candidates:
            diagonal_footprint = _diagonal_path(diagonal)
            if pair_footprint & diagonal_footprint:
                continue
            for triple in triple_candidates:
                triple_footprint = _span(triple)
                if triple_footprint & (pair_footprint | diagonal_footprint):
                    continue
                colors = rng.sample(range(1, 10), 3)
                grid = full_grid(height, width, 0)
                _draw_points(grid, colors[0], pair)
                _draw_points(grid, colors[1], diagonal)
                _draw_points(grid, colors[2], triple)
                return grid
    raise RuntimeError("failed to place precondition-decoy scene")


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
    rng = ctx.draw_rng(f"scene_layout_{band}")
    height, width = rng.choice(_SHAPES_BY_BAND[band])

    if profile == "canonical_disjoint":
        grid = _render_disjoint(
            rng, height=height, width=width, short_gap=False
        )
    elif profile == "short_gap":
        grid = _render_disjoint(
            rng, height=height, width=width, short_gap=True
        )
    elif profile == "cross_horizontal_high":
        grid = _render_crossing(
            rng, height=height, width=width, winner="H"
        )
    elif profile == "cross_vertical_high":
        grid = _render_crossing(
            rng, height=height, width=width, winner="V"
        )
    elif profile == "precondition_decoys":
        grid = _render_precondition_decoys(
            rng, height=height, width=width
        )
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
    """Reject malformed, identity, ambiguous, or off-curriculum inputs."""
    del meta
    if difficulty is not None:
        _band(difficulty)
    errors = _validate_grid(grid)
    if errors:
        return errors

    height, width = len(grid), len(grid[0])
    palette = {value for row in grid for value in row}
    if (height, width) not in _CANONICAL_SHAPES:
        errors.append(
            f"shape {(height, width)} is outside canonical shapes {_CANONICAL_SHAPES}"
        )
    if 0 not in palette:
        errors.append("background color 0 must be present")
    if len(palette) not in (3, 4):
        errors.append("palette must contain background plus two or three nonzero colors")

    for color, points in sorted(_color_cells(grid).items()):
        orientation = _orientation(points)
        if len(points) == 2 and orientation is not None:
            if len(_span(points)) < 3:
                errors.append(f"color {color} aligned pair has no visible interior gap")
        elif len(points) == 2:
            if not _diagonal_path(points):
                errors.append(
                    f"color {color} non-aligned pair must be a separated 45-degree decoy"
                )
        elif len(points) == 3 and orientation is not None:
            if len(_span(points)) == len(points):
                errors.append(f"color {color} aligned triple has no unpainted internal gap")
        else:
            errors.append(
                f"color {color} must be an aligned pair, separated diagonal pair, "
                "or aligned triple"
            )

    analysis = analyze_grid(grid)
    if analysis["aligned_pair_count"] == 0:
        errors.append("need at least one exactly-two aligned pair with a visible gap")
    if analysis["endpoint_overwrite_risk"]:
        errors.append("a connectable segment passes through another pair's endpoint")
    if analysis["crossing_count"] > 1:
        errors.append("at most one orthogonal segment crossing is allowed")
    if analysis["invalid_color_specs"]:
        errors.append(f"invalid color specifications: {analysis['invalid_color_specs']}")

    profile = observe_overrides(grid)["scene_profile"]
    if profile is None:
        errors.append("grid does not match any declared scene_profile")
    elif profile == "precondition_decoys" and len(palette) != 4:
        errors.append("precondition_decoys must use three distinct nonzero colors")
    elif profile != "precondition_decoys" and (height, width, len(palette)) not in _CANONICAL_SIGNATURES:
        errors.append(
            f"ordinary profile signature {(height, width, len(palette))} is not canonical"
        )

    if not errors and rule_mirror(grid) == [list(row) for row in grid]:
        errors.append("rule is an identity transformation on this input")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Return [] exactly for the canonical two-pair structural manifold."""
    errors = _validate_grid(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    palette_size = len({value for row in grid for value in row})
    signature = (height, width, palette_size)
    if signature not in _CANONICAL_SIGNATURES:
        errors.append(
            f"shape/palette signature {signature} is outside canonical signatures "
            f"{sorted(_CANONICAL_SIGNATURES)}"
        )

    analysis = analyze_grid(grid)
    if analysis["aligned_pair_count"] != 2:
        errors.append("canonical manifold requires exactly two aligned endpoint pairs")
    if analysis["horizontal_pair_count"] != 1 or analysis["vertical_pair_count"] != 1:
        errors.append("canonical manifold requires one horizontal and one vertical pair")
    if analysis["diagonal_pair_count"] or analysis["aligned_triple_count"]:
        errors.append("canonical manifold contains no diagonal-pair or triple decoys")
    if analysis["invalid_color_specs"]:
        errors.append(f"invalid color specifications: {analysis['invalid_color_specs']}")
    if analysis["endpoint_overwrite_risk"]:
        errors.append("a connectable segment passes through another pair's endpoint")
    if not errors and rule_mirror(grid) == [list(row) for row in grid]:
        errors.append("rule is an identity transformation on this input")
    return errors


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
            _draw_line(output, points, color)
    return output


def _rival_require_two_blank_interior_cells(grid):
    output = [list(row) for row in grid]
    for color, _, points in _connectable_pairs(grid):
        if len(_span(points)) >= 4:
            _draw_line(output, points, color)
    return output


def _rival_low_color_wins(grid):
    output = [list(row) for row in grid]
    cells = _color_cells(grid)
    for color in sorted(cells, reverse=True):
        points = cells[color]
        if len(points) == 2 and _orientation(points) is not None:
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
    "require_at_least_two_blank_interior_cells": _rival_require_two_blank_interior_cells,
    "lower_numeric_color_wins_crossings": _rival_low_color_wins,
    "horizontal_segment_always_wins_crossings": _rival_horizontal_always_wins,
    "vertical_segment_always_wins_crossings": _rival_vertical_always_wins,
    "connect_only_lowest_valued_pair": _rival_lowest_pair_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "connect_diagonal_pairs": _rival_connect_diagonal_pairs,
    "connect_any_aligned_color_with_at_least_two_cells": _rival_connect_aligned_count_ge_2,
    "require_at_least_two_blank_interior_cells": _rival_require_two_blank_interior_cells,
    "horizontal_segment_always_wins_crossings": _rival_horizontal_always_wins,
}


def _analysis_value(grid, key: str):
    return analyze_grid(grid).get(key)


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "bounded_segments_not_full_axes": lambda grid: bool(
        _analysis_value(grid, "has_bounded_segment")
    ),
    "minimum_one_cell_interior_is_connected": lambda grid: (
        observe_overrides(grid).get("scene_profile") == "short_gap"
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
    "minimum_one_cell_interior_is_connected": [
        "require_at_least_two_blank_interior_cells"
    ],
    "multiple_pairs_all_transform": ["connect_only_lowest_valued_pair"],
    "diagonal_pair_stays_unchanged": ["connect_diagonal_pairs"],
    "aligned_triple_stays_unchanged": [
        "connect_any_aligned_color_with_at_least_two_cells"
    ],
    "horizontal_higher_color_wins": [
        "lower_numeric_color_wins_crossings",
        "vertical_segment_always_wins_crossings",
    ],
    "vertical_higher_color_wins": [
        "lower_numeric_color_wins_crossings",
        "horizontal_segment_always_wins_crossings",
    ],
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
            reasons.append(f"pair {index} disagrees with the selected endpoint rule")
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
