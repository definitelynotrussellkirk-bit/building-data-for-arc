"""Generator for ``arc_additional_puzzles_21_set6:M42``.

The top-left cell is a global command.  Every other non-zero color occurs at
exactly two non-collinear marker cells.  Command 1 joins each row-major first
marker to the second marker horizontally then vertically; command 2 joins it
vertically then horizontally.  The command cell is not copied to the output.

The generator deliberately schedules both command branches and one-to-four
pair counts across every four consecutive examples.  That makes a materialized
lesson capable of refuting command-blind and first-pair-only shortcuts instead
of merely producing individually valid scenes.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "819daf7d9f91"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "1bb6e14a6291"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Read the command at (0,0). For every other color, connect its two "
    "non-collinear markers with one L-path. Command 1 uses horizontal then "
    "vertical; command 2 uses vertical then horizontal. Clear the command "
    "cell in the output."
)

INVARIANTS = [
    "the grid is rectangular, uses ARC colors, and is 7..14 cells per side",
    "cell (0,0) is command 1 or 2 and that command color does not recur",
    "there are 1..4 endpoint colors, each appearing exactly twice",
    "the two markers of every color differ in both row and column",
    "path overlaps are legal; later row-major first markers win at overlaps",
]

SCENE_PROFILES = (
    "cmd1_pairs1",
    "cmd2_pairs2",
    "cmd1_pairs3",
    "cmd2_pairs4",
    "cmd1_pairs2",
    "cmd2_pairs3",
    "cmd1_pairs4",
    "cmd2_pairs1",
)
GRID_PROFILES = ("small", "canonical", "large")
CANONICAL_DIMS = ((9, 10), (10, 11), (10, 12), (11, 11))
DIFFICULTIES = {None, "default", "easy", "medium", "hard"}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "scheduled across command and pair-count branches",
        "valid": "|".join(SCENE_PROFILES),
        "doc": "exact command plus exact number of endpoint-color pairs",
    },
    "grid_profile": {
        "type": "str",
        "default": "scheduled small|canonical|large",
        "valid": "|".join(GRID_PROFILES),
        "doc": "disjoint size family recoverable from the returned grid",
    },
}


def _normalize_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    """Return a copied rectangular integer grid or validation errors."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty row sequence"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return None, ["rows must be nonempty sequences"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None, ["grid must be rectangular"]
    copied = [list(row) for row in grid]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in copied
        for value in row
    ):
        return None, ["cells must be integer ARC colors 0..9"]
    return copied, []


def _ordered_pair_colors(grid: list[list[int]], command: int) -> list[int]:
    """Nonzero non-command colors in row-major first-occurrence order."""
    seen: set[int] = set()
    ordered: list[int] = []
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if (row, col) == (0, 0) or value in (0, command) or value in seen:
                continue
            seen.add(value)
            ordered.append(value)
    return ordered


def _markers(grid: list[list[int]], color: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    )


def _path_cells(
    first: tuple[int, int],
    second: tuple[int, int],
    command: int,
) -> tuple[tuple[int, int], ...]:
    """Cells painted by the canonical command-selected L path."""
    row_a, col_a = first
    row_b, col_b = second
    cells: list[tuple[int, int]] = []
    if command == 1:
        for col in range(min(col_a, col_b), max(col_a, col_b) + 1):
            cells.append((row_a, col))
        for row in range(min(row_a, row_b), max(row_a, row_b) + 1):
            cells.append((row, col_b))
    else:
        for row in range(min(row_a, row_b), max(row_a, row_b) + 1):
            cells.append((row, col_a))
        for col in range(min(col_a, col_b), max(col_a, col_b) + 1):
            cells.append((row_b, col))
    return tuple(dict.fromkeys(cells))


def _grid_profile(height: int, width: int) -> str | None:
    if (height, width) in CANONICAL_DIMS:
        return "canonical"
    if 7 <= height <= 8 and 7 <= width <= 8:
        return "small"
    if 12 <= height <= 14 and 12 <= width <= 14:
        return "large"
    return None


def _scene_profile(command: int, pair_count: int) -> str | None:
    value = f"cmd{command}_pairs{pair_count}"
    return value if value in SCENE_PROFILES else None


def _analyze(grid: Any) -> dict[str, Any]:
    """Structural analysis shared by checks, observers, and semantic hooks."""
    normalized, errors = _normalize_grid(grid)
    result: dict[str, Any] = {"errors": errors, "facts": None}
    if normalized is None:
        return result

    height = len(normalized)
    width = len(normalized[0])
    if not (7 <= height <= 14 and 7 <= width <= 14):
        errors.append("grid dimensions must each be in 7..14")

    command = normalized[0][0]
    if command not in (1, 2):
        errors.append("cell (0,0) must be command 1 or 2")

    counts = Counter(value for row in normalized for value in row if value != 0)
    if command in (1, 2) and counts[command] != 1:
        errors.append("the command color must occur exactly once, at (0,0)")

    colors = _ordered_pair_colors(normalized, command)
    if not 1 <= len(colors) <= 4:
        errors.append(
            f"expected 1..4 endpoint colors, found {len(colors)}"
        )

    pair_markers: dict[int, tuple[tuple[int, int], ...]] = {}
    pair_paths: dict[int, tuple[tuple[int, int], ...]] = {}
    occupied_paths: set[tuple[int, int]] = set()
    overlap_cells: set[tuple[int, int]] = set()
    for color in colors:
        positions = _markers(normalized, color)
        pair_markers[color] = positions
        if len(positions) != 2:
            errors.append(
                f"endpoint color {color} must occur exactly twice; found "
                f"{len(positions)}"
            )
            continue
        first, second = positions
        if first[0] == second[0] or first[1] == second[1]:
            errors.append(
                f"endpoint color {color} markers must differ in row and column"
            )
            continue
        path = _path_cells(first, second, command)
        pair_paths[color] = path
        overlap_cells.update(occupied_paths.intersection(path))
        occupied_paths.update(path)

    extra_nonzero = {
        value
        for row in normalized
        for value in row
        if value not in ({0, command} | set(colors))
    }
    if extra_nonzero:
        errors.append(f"unexpected nonzero colors: {sorted(extra_nonzero)}")

    profile = _grid_profile(height, width)
    if profile is None:
        errors.append(
            "grid dimensions must belong to small, canonical, or large profile"
        )
    scene = _scene_profile(command, len(colors)) if command in (1, 2) else None
    if scene is None:
        errors.append("command/pair-count combination is outside declared profiles")

    if not errors:
        output = _rule_mirror(normalized)
        result["facts"] = {
            "height": height,
            "width": width,
            "command": command,
            "colors": tuple(colors),
            "pair_count": len(colors),
            "markers": pair_markers,
            "paths": pair_paths,
            "path_cells": frozenset(occupied_paths),
            "overlap_cells": frozenset(overlap_cells),
            "scene_profile": scene,
            "grid_profile": profile,
            "output": output,
        }
    return result


def _rule_with_command(grid: Any, command: int, *, first_pair_only: bool = False):
    """Python test mirror of the Racket oracle with a forced command."""
    normalized, errors = _normalize_grid(grid)
    if normalized is None or errors:
        raise ValueError("; ".join(errors))
    output = full_grid(len(normalized), len(normalized[0]), 0)
    colors = _ordered_pair_colors(normalized, normalized[0][0])
    if first_pair_only:
        colors = colors[:1]
    for color in colors:
        positions = _markers(normalized, color)
        if len(positions) != 2:
            continue
        for row, col in _path_cells(positions[0], positions[1], command):
            output[row][col] = color
    return output


def _rule_mirror(grid: Any):
    """Python test mirror; the canonical Racket program remains authority."""
    normalized, errors = _normalize_grid(grid)
    if normalized is None or errors:
        raise ValueError("; ".join(errors))
    command = normalized[0][0]
    if command not in (1, 2):
        raise ValueError("missing command")
    return _rule_with_command(normalized, command)


def _marker_only(grid: Any):
    normalized, errors = _normalize_grid(grid)
    if normalized is None or errors:
        raise ValueError("; ".join(errors))
    output = full_grid(len(normalized), len(normalized[0]), 0)
    command = normalized[0][0]
    for row, values in enumerate(normalized):
        for col, value in enumerate(values):
            if (row, col) != (0, 0) and value not in (0, command):
                output[row][col] = value
    return output


def _keep_command(grid: Any):
    output = _rule_mirror(grid)
    output[0][0] = grid[0][0]
    return output


def _drop_single_pair(grid: Any):
    normalized, errors = _normalize_grid(grid)
    if normalized is None or errors:
        raise ValueError("; ".join(errors))
    command = normalized[0][0]
    colors = _ordered_pair_colors(normalized, command)
    if len(colors) == 1:
        return full_grid(len(normalized), len(normalized[0]), 0)
    return _rule_mirror(normalized)


def _only_first_two_pairs(grid: Any):
    normalized, errors = _normalize_grid(grid)
    if normalized is None or errors:
        raise ValueError("; ".join(errors))
    command = normalized[0][0]
    output = full_grid(len(normalized), len(normalized[0]), 0)
    for color in _ordered_pair_colors(normalized, command)[:2]:
        positions = _markers(normalized, color)
        if len(positions) == 2:
            for row, col in _path_cells(positions[0], positions[1], command):
                output[row][col] = color
    return output


def _reverse_pair_priority(grid: Any):
    """Plausible rival that paints valid paths in reverse color order."""
    normalized, errors = _normalize_grid(grid)
    if normalized is None or errors:
        raise ValueError("; ".join(errors))
    command = normalized[0][0]
    output = full_grid(len(normalized), len(normalized[0]), 0)
    for color in reversed(_ordered_pair_colors(normalized, command)):
        positions = _markers(normalized, color)
        if len(positions) == 2:
            for row, col in _path_cells(positions[0], positions[1], command):
                output[row][col] = color
    return output


def _wrong_for_horizontal_direction(grid: Any, *, first_is_left: bool):
    normalized, errors = _normalize_grid(grid)
    if normalized is None or errors:
        raise ValueError("; ".join(errors))
    command = normalized[0][0]
    output = full_grid(len(normalized), len(normalized[0]), 0)
    for color in _ordered_pair_colors(normalized, command):
        positions = _markers(normalized, color)
        if len(positions) != 2:
            continue
        relation_matches = (positions[0][1] < positions[1][1]) == first_is_left
        pair_command = 3 - command if relation_matches else command
        for row, col in _path_cells(positions[0], positions[1], pair_command):
            output[row][col] = color
    return output


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-hiding scenes, including all degenerates."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Task-linked semantic manifold predicate used by the strict census."""
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {
        "scene_profile": facts["scene_profile"],
        "grid_profile": facts["grid_profile"],
    }


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    facts = analysis["facts"]
    return (
        facts["height"],
        facts["width"],
        facts["pair_count"],
        facts["command"],
    )


def _witness_command(command: int) -> Callable[[Any], bool]:
    return lambda grid: (
        not _analyze(grid)["errors"]
        and _analyze(grid)["facts"]["command"] == command
    )


def _witness_pair_count(predicate: Callable[[int], bool]) -> Callable[[Any], bool]:
    return lambda grid: (
        not _analyze(grid)["errors"]
        and predicate(_analyze(grid)["facts"]["pair_count"])
    )


def _first_marker_right_of_second(grid: Any) -> bool:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return False
    return any(
        positions[0][1] > positions[1][1]
        for positions in analysis["facts"]["markers"].values()
    )


def _first_marker_left_of_second(grid: Any) -> bool:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return False
    return any(
        positions[0][1] < positions[1][1]
        for positions in analysis["facts"]["markers"].values()
    )


def _long_leg(grid: Any) -> bool:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return False
    return any(
        abs(positions[0][0] - positions[1][0]) >= 2
        or abs(positions[0][1] - positions[1][1]) >= 2
        for positions in analysis["facts"]["markers"].values()
    )


def _has_path_overlap(grid: Any) -> bool:
    analysis = _analyze(grid)
    return bool(not analysis["errors"] and analysis["facts"]["overlap_cells"])


SEMANTIC_WITNESSES = {
    "command_1_horizontal_then_vertical": _witness_command(1),
    "command_2_vertical_then_horizontal": _witness_command(2),
    "single_pair": _witness_pair_count(lambda count: count == 1),
    "multiple_pairs": _witness_pair_count(lambda count: count >= 2),
    "three_or_four_pairs": _witness_pair_count(lambda count: count >= 3),
    "first_marker_left_of_second": _first_marker_left_of_second,
    "first_marker_right_of_second": _first_marker_right_of_second,
    "nontrivial_path_leg": _long_leg,
    "overlapping_paths_priority": _has_path_overlap,
}

SEMANTIC_RIVALS = {
    "always_horizontal_then_vertical": lambda grid: _rule_with_command(grid, 1),
    "always_vertical_then_horizontal": lambda grid: _rule_with_command(grid, 2),
    "first_pair_only": lambda grid: _rule_with_command(
        grid, grid[0][0], first_pair_only=True
    ),
    "drop_single_pair": _drop_single_pair,
    "only_first_two_pairs": _only_first_two_pairs,
    "wrong_when_first_marker_left": lambda grid: _wrong_for_horizontal_direction(
        grid, first_is_left=True
    ),
    "wrong_when_first_marker_right": lambda grid: _wrong_for_horizontal_direction(
        grid, first_is_left=False
    ),
    "marker_only": _marker_only,
    "keep_command_cell": _keep_command,
    "reverse_pair_priority": _reverse_pair_priority,
}

WITNESS_RIVALS = {
    "command_1_horizontal_then_vertical": ["always_vertical_then_horizontal"],
    "command_2_vertical_then_horizontal": ["always_horizontal_then_vertical"],
    "single_pair": ["drop_single_pair"],
    "multiple_pairs": ["first_pair_only"],
    "three_or_four_pairs": ["only_first_two_pairs"],
    "first_marker_left_of_second": ["wrong_when_first_marker_left"],
    "first_marker_right_of_second": ["wrong_when_first_marker_right"],
    "nontrivial_path_leg": ["marker_only", "keep_command_cell"],
    "overlapping_paths_priority": ["reverse_pair_priority"],
}

LESSON_COMPETITORS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "always_horizontal_then_vertical",
        "always_vertical_then_horizontal",
        "first_pair_only",
        "wrong_when_first_marker_left",
        "wrong_when_first_marker_right",
        "marker_only",
        "keep_command_cell",
        "reverse_pair_priority",
    )
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
SCHEDULE_PROFILES = SCENE_PROFILES


def lesson_identifiable(demos, query) -> list[str]:
    """Require the demonstrations to refute every named plausible rival."""
    del query
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        survived = True
        for demo in demos:
            try:
                predicted = rival(demo["input"])
            except Exception:
                survived = False
                break
            if predicted != demo["output"]:
                survived = False
                break
        if survived:
            reasons.append(f"named rival {name!r} fits every demonstration")
    return reasons


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]


def _scheduled_grid_profile(sample_index: int) -> str:
    return ("canonical", "small", "canonical", "large")[sample_index % 4]


def _parse_scene_profile(profile: str) -> tuple[int, int]:
    command_text, pair_text = profile.split("_")
    return int(command_text[-1]), int(pair_text.removeprefix("pairs"))


def _draw_dimensions(ctx, profile: str, difficulty: str) -> tuple[int, int]:
    rng = ctx.draw_rng("dimensions")
    if profile == "canonical":
        return rng.choice(CANONICAL_DIMS)
    if profile == "small":
        ranges = {
            "easy": (7, 7),
            "medium": (7, 8),
            "hard": (8, 8),
        }
    else:
        ranges = {
            "easy": (12, 12),
            "medium": (12, 13),
            "hard": (13, 14),
        }
    lo, hi = ranges[difficulty]
    return rng.randint(lo, hi), rng.randint(lo, hi)


def _partition(start: int, stop: int, parts: int) -> list[tuple[int, int]]:
    """Half-open intervals covering ``range(start, stop)`` nearly evenly."""
    size = stop - start
    base, extra = divmod(size, parts)
    intervals = []
    cursor = start
    for index in range(parts):
        width = base + (1 if index < extra else 0)
        intervals.append((cursor, cursor + width))
        cursor += width
    return intervals


def _place_markers_disjoint(
    grid: list[list[int]],
    colors: tuple[int, ...],
    command: int,
    *,
    rng,
    sample_index: int,
) -> None:
    """Place each pair in a disjoint rectangular zone."""
    height = len(grid)
    width = len(grid[0])
    pair_count = len(colors)
    row_parts = 1 if pair_count <= 2 else 2
    col_parts = pair_count if pair_count <= 2 else 2
    row_intervals = _partition(1, height, row_parts)
    col_intervals = _partition(0, width, col_parts)
    zones = [
        (row_interval, col_interval)
        for row_interval in row_intervals
        for col_interval in col_intervals
    ]
    rng.shuffle(zones)

    for pair_index, (color, zone) in enumerate(zip(colors, zones)):
        (row_lo, row_hi), (col_lo, col_hi) = zone
        rows = list(range(row_lo, row_hi))
        cols = list(range(col_lo, col_hi))
        if len(rows) < 2 or len(cols) < 2:
            raise ValueError(
                f"zone {zone} is too small for a non-collinear marker pair"
            )
        row_a, row_b = sorted(rng.sample(rows, 2))
        col_left, col_right = sorted(rng.sample(cols, 2))
        if (sample_index + pair_index) % 2:
            col_a, col_b = col_right, col_left
        else:
            col_a, col_b = col_left, col_right
        grid[row_a][col_a] = color
        grid[row_b][col_b] = color

        # The construction is intentionally command-aware only in validation:
        # zones are disjoint, so either of the two legal elbows stays inside
        # its own zone and cannot collide with another color's path.
        path = _path_cells((row_a, col_a), (row_b, col_b), command)
        if any(not (row_lo <= row < row_hi and col_lo <= col < col_hi)
               for row, col in path):
            raise AssertionError("constructed path escaped its placement zone")


def _place_markers_with_overlap(
    grid: list[list[int]],
    colors: tuple[int, ...],
    command: int,
    *,
    rng,
) -> None:
    """Place markers so at least two path interiors overlap, without ambiguity."""
    height = len(grid)
    width = len(grid[0])
    cells = [(row, col) for row in range(1, height) for col in range(width)]
    for _attempt in range(10_000):
        selected = rng.sample(cells, 2 * len(colors))
        pairs = [tuple(selected[2 * i:2 * i + 2]) for i in range(len(colors))]
        if any(a[0] == b[0] or a[1] == b[1] for a, b in pairs):
            continue
        paths = [_path_cells(a, b, command) for a, b in pairs]
        all_markers = set(selected)
        if any((set(path) - {a, b}) & (all_markers - {a, b})
               for path, (a, b) in zip(paths, pairs)):
            continue
        occupied: set[tuple[int, int]] = set()
        overlap: set[tuple[int, int]] = set()
        for path in paths:
            overlap.update(occupied.intersection(path))
            occupied.update(path)
        if not overlap:
            continue
        for color, (first, second) in zip(colors, pairs):
            grid[first[0]][first[1]] = color
            grid[second[0]][second[1]] = color
        if _reverse_pair_priority(grid) == _rule_mirror(grid):
            for row, col in selected:
                grid[row][col] = 0
            continue
        return
    raise ValueError("could not place a deterministic overlapping-path scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    band = "medium" if difficulty in (None, "default") else difficulty
    if band not in {"easy", "medium", "hard"}:
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    # Scheduled defaults are injected through GenCtx as exact keyed draws.  An
    # explicit caller override still wins and passes through the same domain
    # validation.  This preserves replay/provenance while guaranteeing that any
    # four consecutive lesson examples cover both commands and multi-pair data.
    ctx_overrides = dict(overrides)
    ctx_overrides.setdefault(
        "scene_profile", schedule_profile(seed, sample_index, band)
    )
    ctx_overrides.setdefault(
        "grid_profile", _scheduled_grid_profile(sample_index)
    )
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=ctx_overrides,
    )
    scene_profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    grid_profile = ctx.draw_choice("grid_profile", GRID_PROFILES)
    command, pair_count = _parse_scene_profile(scene_profile)
    height, width = _draw_dimensions(ctx, grid_profile, band)

    grid = full_grid(height, width, 0)
    grid[0][0] = command
    colors = ctx.draw_distinct_colors(
        "pair_colors", n=pair_count, exclude={0, command}
    )
    layout_rng = ctx.draw_rng("layout")
    if pair_count >= 3:
        _place_markers_with_overlap(
            grid, colors, command, rng=layout_rng
        )
    else:
        _place_markers_disjoint(
            grid,
            colors,
            command,
            rng=layout_rng,
            sample_index=sample_index,
        )
    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("generator constructed invalid scene: " + "; ".join(errors))
    return [row[:] for row in grid]
