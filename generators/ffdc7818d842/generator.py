"""Semantic generator for ARC task ``ffdc7818d842``.

The unique cyan cell identifies one edge.  Every row (for a horizontal edge)
or column (for a vertical edge) keeps its number of blue cells but packs them
toward that edge.  On the marker's own row/column, vacated cells between the
old blue block and the new packed block become maroon.
"""
from __future__ import annotations

from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "ffdc7818d842"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "d80e6280754a"

SUMMARY = (
    "Pack every row or column of blue(1) cells toward the edge identified by "
    "the unique cyan(8) marker. On the marker's own line, paint the vacated "
    "gap between the old and new blue blocks maroon(9)."
)

INVARIANTS = [
    "the input palette is exactly a subset of background 0, blue movers 1, and one cyan marker 8",
    "the cyan marker lies on exactly one non-corner edge and determines left/right/up/down gravity",
    "blue counts are conserved independently in every row or column parallel to gravity",
    "only the marker row or column may acquire the maroon trail color 9",
]

_DIRECTIONS = ("left", "up", "right", "down")
_DENSITIES = ("sparse", "mixed", "dense")
_CANONICAL_SHAPES = {(3, 3), (4, 8), (5, 5), (5, 6), (7, 7)}

# Each profile is recoverable from (shape, marker edge, per-line blue counts).
# Every difficulty band cycles through all four directions, so every consecutive
# four-demo lesson falsifies a fixed-direction shortcut.
_PROFILE_ROWS = (
    ("3x3_left_sparse", "easy", 3, 3, "left", "sparse"),
    ("4x8_up_mixed", "easy", 4, 8, "up", "mixed"),
    ("3x3_right_mixed", "easy", 3, 3, "right", "mixed"),
    ("4x8_down_sparse", "easy", 4, 8, "down", "sparse"),
    ("5x5_left_mixed", "medium", 5, 5, "left", "mixed"),
    ("5x6_up_dense", "medium", 5, 6, "up", "dense"),
    ("5x5_right_sparse", "medium", 5, 5, "right", "sparse"),
    ("5x6_down_mixed", "medium", 5, 6, "down", "mixed"),
    ("7x7_left_dense", "hard", 7, 7, "left", "dense"),
    ("7x7_up_mixed", "hard", 7, 7, "up", "mixed"),
    ("7x7_right_dense", "hard", 7, 7, "right", "dense"),
    ("7x7_down_dense", "hard", 7, 7, "down", "dense"),
)
SCENE_PROFILES = tuple(row[0] for row in _PROFILE_ROWS)
SCHEDULE_PROFILES = SCENE_PROFILES
_PROFILE_BY_NAME = {row[0]: row[1:] for row in _PROFILE_ROWS}
_PROFILE_BY_SIGNATURE = {
    (row[2], row[3], row[4], row[5]): row[0] for row in _PROFILE_ROWS
}
_PROFILES_BY_BAND = {
    band: tuple(row[0] for row in _PROFILE_ROWS if row[1] == band)
    for band in ("easy", "medium", "hard")
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic four-direction curriculum for the selected difficulty band",
        "valid": "3x3_left_sparse|4x8_up_mixed|3x3_right_mixed|4x8_down_sparse|5x5_left_mixed|5x6_up_dense|5x5_right_sparse|5x6_down_mixed|7x7_left_dense|7x7_up_mixed|7x7_right_dense|7x7_down_dense",
    }
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 4


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic four-direction curriculum slot."""
    del seed
    profiles = _PROFILES_BY_BAND[_band(difficulty)]
    return profiles[int(sample_index) % len(profiles)]


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 3 <= len(grid) <= 14 or not 3 <= width <= 14:
        return [f"grid dimensions must be in 3..14, found {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    blues = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]
    extras = sorted({value for row in grid for value in row if value not in (0, 1, 8)})
    if len(markers) != 1:
        errors.append(f"expected exactly one cyan(8) marker, found {len(markers)}")
    if extras:
        errors.append(f"unexpected input colors: {extras}")
    if not blues:
        errors.append("expected at least one blue(1) mover")
    if len(markers) != 1:
        return {"errors": errors, "height": height, "width": width}

    marker_r, marker_c = markers[0]
    on_top = marker_r == 0
    on_bottom = marker_r == height - 1
    on_left = marker_c == 0
    on_right = marker_c == width - 1
    edge_count = sum((on_top, on_bottom, on_left, on_right))
    if edge_count == 0:
        errors.append("cyan marker must lie on an edge")
        direction = None
    elif edge_count > 1:
        errors.append("cyan marker must avoid corners so direction is unambiguous")
        direction = None
    elif on_top:
        direction = "up"
    elif on_bottom:
        direction = "down"
    elif on_left:
        direction = "left"
    else:
        direction = "right"

    counts: list[int] = []
    if direction in ("left", "right"):
        counts = [sum(value == 1 for value in row) for row in grid]
    elif direction in ("up", "down"):
        counts = [
            sum(grid[r][c] == 1 for r in range(height)) for c in range(width)
        ]

    density = None
    if counts and all(count == 1 for count in counts):
        density = "sparse"
    elif counts and set(counts).issubset({1, 2}) and {1, 2}.issubset(set(counts)):
        density = "mixed"
    elif counts and min(counts) >= 2 and max(counts) >= 3:
        density = "dense"

    profile = _PROFILE_BY_SIGNATURE.get((height, width, direction, density))
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "marker": (marker_r, marker_c),
        "direction": direction,
        "counts": counts,
        "density": density,
        "scene_profile": profile,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical inputs and reject malformed or rule-hiding scenes."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if any(count == 0 for count in analysis["counts"]):
        axis = "row" if analysis["direction"] in ("left", "right") else "column"
        errors.append(f"every {axis} must contain at least one blue mover")
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observe_overrides(grid).get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as "
                f"{observe_overrides(grid).get(name)!r}"
            )
    return errors


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover the exact declared scene profile from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {"scene_profile": analysis["scene_profile"]}


def _line_counts(
    density: str,
    n_lines: int,
    marker_line: int,
    axis_length: int,
    rng,
) -> list[int]:
    """Draw observable per-line counts while preserving the named density."""
    if density == "sparse":
        return [1] * n_lines
    if density == "mixed":
        counts = [1 + rng.randint(0, 1) for _ in range(n_lines)]
        counts[0] = 1
        counts[-1] = 2
        # A 3x3 marker line uses one mover so its official trail is visible.
        if axis_length == 3:
            counts[marker_line] = 1
            counts[0 if marker_line != 0 else n_lines - 1] = 2
        return counts
    if density == "dense":
        counts = [2 + rng.randint(0, 1) for _ in range(n_lines)]
        counts[0] = 2
        counts[-1] = 3
        return counts
    raise ValueError(f"unknown density: {density!r}")


def _destination_positions(
    axis_length: int,
    count: int,
    direction: str,
    marker_line: bool,
) -> set[int]:
    toward_low = direction in ("left", "up")
    if toward_low:
        start = 1 if marker_line else 0
        return set(range(start, start + count))
    stop = axis_length - 1 if marker_line else axis_length
    return set(range(stop - count, stop))


def _source_positions(
    axis_length: int,
    count: int,
    direction: str,
    marker_line: bool,
    line_index: int,
    rng,
) -> list[int]:
    marker_position = 0 if direction in ("left", "up") else axis_length - 1
    available = [p for p in range(axis_length) if not marker_line or p != marker_position]
    if count > len(available):
        raise ValueError(
            f"profile requests {count} movers on an axis with only {len(available)} slots"
        )
    # Alternate coordinate parity across adjacent rows/columns.  This mirrors
    # the canonical checkerboard texture and keeps movers as distinct objects.
    primary = [p for p in available if p % 2 == line_index % 2]
    pool = primary if len(primary) >= count else available
    toward_low = direction in ("left", "up")
    ordered = list(reversed(pool)) if toward_low else list(pool)
    window = ordered[: min(len(ordered), count + 1)]
    chosen = set(rng.sample(window, count))
    destination = _destination_positions(axis_length, count, direction, marker_line)

    # Force at least one displaced mover.  On the marker line this also makes
    # the official maroon trail non-empty.
    if chosen == destination or (
        marker_line
        and (
            (toward_low and max(chosen) <= max(destination))
            or (not toward_low and min(chosen) >= min(destination))
        )
    ):
        outside = [p for p in ordered if p not in destination]
        if not outside:
            fallback = list(reversed(available)) if toward_low else list(available)
            outside = [p for p in fallback if p not in destination]
        if outside:
            replace = min(chosen) if toward_low else max(chosen)
            chosen.remove(replace)
            chosen.add(outside[0])
    return sorted(chosen)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    band = _band(difficulty)
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in _PROFILE_BY_NAME:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    scheduled = requested or schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", [scheduled])
    _profile_band, height, width, direction, density = _PROFILE_BY_NAME[profile]
    rng = ctx.draw_rng("placement")
    grid = full_grid(height, width, 0)

    if direction in ("left", "right"):
        marker_r = rng.randint(1, height - 2)
        marker_c = 0 if direction == "left" else width - 1
        grid[marker_r][marker_c] = 8
        counts = _line_counts(density, height, marker_r, width, rng)
        for row, count in enumerate(counts):
            for col in _source_positions(width, count, direction, row == marker_r, row, rng):
                grid[row][col] = 1
    else:
        marker_r = 0 if direction == "up" else height - 1
        marker_c = rng.randint(1, width - 2)
        grid[marker_r][marker_c] = 8
        counts = _line_counts(density, width, marker_c, height, rng)
        for col, count in enumerate(counts):
            for row in _source_positions(height, count, direction, col == marker_c, col, rng):
                grid[row][col] = 1
    return grid


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent mirror for tests; the synchronized Racket remains authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    height, width = analysis["height"], analysis["width"]
    marker_r, marker_c = analysis["marker"]
    direction = analysis["direction"]
    output = full_grid(height, width, 0)
    output[marker_r][marker_c] = 8

    if direction in ("left", "right"):
        for row in range(height):
            positions = [c for c in range(width) if grid[row][c] == 1]
            count = len(positions)
            if direction == "right":
                wall = marker_c if row == marker_r else width
                new_lo = wall - count
                for col in range(new_lo, wall):
                    output[row][col] = 1
                if row == marker_r and positions:
                    for col in range(min(positions), new_lo):
                        output[row][col] = 9
            else:
                wall = marker_c + 1 if row == marker_r else 0
                new_hi = wall + count
                for col in range(wall, new_hi):
                    output[row][col] = 1
                if row == marker_r and positions:
                    for col in range(new_hi, max(positions) + 1):
                        output[row][col] = 9
    else:
        for col in range(width):
            positions = [r for r in range(height) if grid[r][col] == 1]
            count = len(positions)
            if direction == "down":
                wall = marker_r if col == marker_c else height
                new_lo = wall - count
                for row in range(new_lo, wall):
                    output[row][col] = 1
                if col == marker_c and positions:
                    for row in range(min(positions), new_lo):
                        output[row][col] = 9
            else:
                wall = marker_r + 1 if col == marker_c else 0
                new_hi = wall + count
                for row in range(wall, new_hi):
                    output[row][col] = 1
                if col == marker_c and positions:
                    for row in range(new_hi, max(positions) + 1):
                        output[row][col] = 9
    return output


def strict_canonical_like(grid) -> list[str]:
    """Require canonical shape/palette plus visible motion and trail branches."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analysis(grid)
    if (analysis["height"], analysis["width"]) not in _CANONICAL_SHAPES:
        errors.append("grid shape is outside the canonical 3x3/4x8/5x5/5x6/7x7 envelope")
    output = rule_mirror(grid)
    if output == [list(row) for row in grid]:
        errors.append("scene is an identity/no-op under the canonical rule")
    if not any(value == 9 for row in output for value in row):
        errors.append("marker line does not expose the maroon trail branch")
    return errors


def _rival_no_trail(grid):
    return [[0 if value == 9 else value for value in row] for row in rule_mirror(grid)]


def _rival_opposite_edge(grid):
    """Pack blue counts toward the edge opposite the cyan marker, with no trail."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    height, width = analysis["height"], analysis["width"]
    marker_r, marker_c = analysis["marker"]
    direction = analysis["direction"]
    output = full_grid(height, width, 0)
    output[marker_r][marker_c] = 8
    if direction in ("left", "right"):
        pack_low = direction == "right"
        for row in range(height):
            count = sum(value == 1 for value in grid[row])
            cells = range(0, count) if pack_low else range(width - count, width)
            for col in cells:
                if (row, col) != (marker_r, marker_c):
                    output[row][col] = 1
    else:
        pack_low = direction == "down"
        for col in range(width):
            count = sum(grid[row][col] == 1 for row in range(height))
            cells = range(0, count) if pack_low else range(height - count, height)
            for row in cells:
                if (row, col) != (marker_r, marker_c):
                    output[row][col] = 1
    return output


def _rival_marker_line_only(grid):
    """Apply the official motion only to the marker line; leave other lines fixed."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    official = rule_mirror(grid)
    output = [list(row) for row in grid]
    marker_r, marker_c = analysis["marker"]
    if analysis["direction"] in ("left", "right"):
        output[marker_r] = list(official[marker_r])
    else:
        for row in range(analysis["height"]):
            output[row][marker_c] = official[row][marker_c]
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "omit_maroon_trail": _rival_no_trail,
    "pack_toward_opposite_edge": _rival_opposite_edge,
    "move_marker_line_only": _rival_marker_line_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _direction_witness(name: str):
    def witness(grid) -> bool:
        analysis = _analysis(grid)
        return not analysis["errors"] and analysis["direction"] == name
    return witness


def _non_marker_motion(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    official = rule_mirror(grid)
    marker_r, marker_c = analysis["marker"]
    if analysis["direction"] in ("left", "right"):
        return any(
            list(grid[row]) != official[row]
            for row in range(analysis["height"])
            if row != marker_r
        )
    return any(
        grid[row][col] != official[row][col]
        for col in range(analysis["width"])
        if col != marker_c
        for row in range(analysis["height"])
    )


SEMANTIC_WITNESSES = {
    "left_gravity": _direction_witness("left"),
    "up_gravity": _direction_witness("up"),
    "right_gravity": _direction_witness("right"),
    "down_gravity": _direction_witness("down"),
    "maroon_trail_nonempty": lambda grid: any(
        value == 9 for row in rule_mirror(grid) for value in row
    ),
    "non_marker_lines_move": _non_marker_motion,
}
WITNESS_RIVALS = {
    "left_gravity": ["pack_toward_opposite_edge"],
    "up_gravity": ["pack_toward_opposite_edge"],
    "right_gravity": ["pack_toward_opposite_edge"],
    "down_gravity": ["pack_toward_opposite_edge"],
    "maroon_trail_nonempty": ["omit_maroon_trail"],
    "non_marker_lines_move": ["move_marker_line_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson if a named rival survives all demonstrations."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]
    reasons: list[str] = []
    directions: set[str] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} disagrees with the edge-gravity rule")
        analysis = _analysis(pair["input"])
        if not analysis["errors"]:
            directions.add(analysis["direction"])
    if rule_mirror(query["input"]) != query["output"]:
        reasons.append("query disagrees with the edge-gravity rule")
    if directions != set(_DIRECTIONS):
        reasons.append(
            "demonstrations must cover left, up, right, and down marker edges"
        )
    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"demos do not falsify rival: {name}")
    return reasons
