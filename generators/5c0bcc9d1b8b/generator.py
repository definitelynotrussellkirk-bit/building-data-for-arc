"""Input generator for ARC task 5c0bcc9d1b8b.

The task presents a gray motif inside a three-divider track: two parallel outer
walls and one perpendicular center crossbar.  The selected rule counts gray
cells, rebuilds the parallel walls one cell from the center line, preserves the
crossbar, and writes a centered gray line in the track direction.

Ordinary generation deliberately breaks the canonical correlation between grid
size and gray-cell count.  The four public sizes each support multiple counts,
and none uses the count paired with that size in the canonical demonstrations.
That makes every generated input a direct counterexample to a plausible
"memorize line length by grid size" shortcut while retaining canonical colors,
wall offsets, centering, and track directions.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5c0bcc9d1b8b"
TASK_ID = GENERATOR_ID
RULE_HASH = "326f0e0036c3"
VERSION = "5.0.0"
SUMMARY = (
    "Odd square grids use orange background (7), two symmetric black walls "
    "and one centered perpendicular black crossbar (0), plus a centered gray "
    "motif (5).  Count the gray cells; the rule rebuilds the walls at center "
    "plus/minus one and compresses the gray motif to a centered line along "
    "the track.  Emitted profiles vary size, orientation, motif, and count "
    "while breaking the canonical size-to-count shortcut."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
EXPECTED_OUTPUT_CODOMAIN = 16  # one output for each (size, track, gray-count) profile

TRACKS = ("vertical", "horizontal")
WALL_OFFSET_BY_SIZE = {9: 2, 11: 2, 13: 3, 19: 4}
CANONICAL_COUNT_BY_SIZE = {9: 5, 11: 9, 13: 13, 19: 11}
# Counts stay odd and at most the grid size so the selected rule never clips.
# Each size has at least two counts, and its public-demo count is intentionally
# absent from ordinary production to falsify the canonical size lookup.
COUNTS_BY_SIZE = {
    9: (7, 9),
    11: (7, 11),
    13: (9, 11),
    19: (13, 19),
}
SCENE_PROFILES = tuple(
    f"n{size}_{track}_c{count}"
    for size in WALL_OFFSET_BY_SIZE
    for track in TRACKS
    for count in COUNTS_BY_SIZE[size]
)
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted draw over 16 canonical-geometry profiles",
        "valid": "n9_vertical_c7|n9_vertical_c9|n9_horizontal_c7|n9_horizontal_c9|n11_vertical_c7|n11_vertical_c11|n11_horizontal_c7|n11_horizontal_c11|n13_vertical_c9|n13_vertical_c11|n13_horizontal_c9|n13_horizontal_c11|n19_vertical_c13|n19_vertical_c19|n19_horizontal_c13|n19_horizontal_c19",
    }
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

INVARIANTS = [
    "grid is an odd square of size 9, 11, 13, or 19 with colors 0, 5, and 7",
    "exactly two symmetric parallel zero walls and one centered perpendicular 0/5 crossbar define the track",
    "the centered gray motif stays strictly between the parallel walls and has an odd count no larger than the grid size",
    "the motif reaches both channel sides, has a centered odd track span, and is 8-connected",
    "the gray-cell count, not grid size or shape area, determines output line length",
]

_EASY_WEIGHT = tuple(
    profile
    for profile in SCENE_PROFILES
    if profile.startswith("n11_") and profile.endswith("_c11")
)
_MEDIUM_WEIGHT = tuple(
    profile
    for profile in SCENE_PROFILES
    if profile.startswith(("n11_", "n13_"))
)
_HARD_WEIGHT = tuple(
    profile
    for profile in SCENE_PROFILES
    if profile.startswith(("n13_", "n19_"))
)
_PROFILE_CHOICES = {
    None: SCENE_PROFILES,
    "easy": SCENE_PROFILES + _EASY_WEIGHT,
    "medium": SCENE_PROFILES + _MEDIUM_WEIGHT + _MEDIUM_WEIGHT,
    "hard": SCENE_PROFILES + _HARD_WEIGHT + _HARD_WEIGHT,
}


def _parse_profile(profile: str) -> tuple[int, str, int]:
    try:
        size_text, track, count_text = profile.split("_", 2)
        size = int(size_text[1:])
        count = int(count_text[1:])
    except (AttributeError, ValueError, IndexError) as exc:
        raise ValueError(f"invalid scene_profile {profile!r}") from exc
    if profile not in SCENE_PROFILES:
        raise ValueError(f"scene_profile {profile!r} is outside the declared domain")
    return size, track, count


def _track_span(perpendicular_span: int, count: int) -> int:
    """Smallest centered odd span whose rectangle and cross can hold count."""
    for span in range(3, count + 2, 2):
        area = perpendicular_span * span
        cross_size = perpendicular_span + span - 1
        if cross_size <= count <= area:
            return span
    raise ValueError(
        f"cannot fit {count} cells with perpendicular span {perpendicular_span}"
    )


def _grow_centered_motif(
    *,
    size: int,
    track: str,
    wall_offset: int,
    count: int,
    rng,
) -> set[tuple[int, int]]:
    """Construct an exact, connected motif with a centered bounding box.

    A centered cross first touches every side of the intended bounding box.
    Random frontier growth then supplies texture without changing its extents.
    """
    mid = size // 2
    perpendicular = list(range(mid - wall_offset + 1, mid + wall_offset))
    span = _track_span(len(perpendicular), count)
    along = list(range(mid - span // 2, mid + span // 2 + 1))

    if track == "vertical":
        rows, cols = along, perpendicular
    else:
        rows, cols = perpendicular, along

    allowed = {(row, col) for row in rows for col in cols}
    cells = {(row, mid) for row in rows} | {(mid, col) for col in cols}
    if len(cells) > count:
        raise RuntimeError("motif skeleton exceeds requested count")

    while len(cells) < count:
        frontier = sorted(
            (nr, nc)
            for row, col in cells
            for nr, nc in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            )
            if (nr, nc) in allowed and (nr, nc) not in cells
        )
        # Multiple selected cells can nominate the same frontier cell.
        frontier = sorted(set(frontier))
        if not frontier:
            raise RuntimeError("constructive motif growth exhausted its frontier")
        cells.add(rng.choice(frontier))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in _PROFILE_CHOICES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if "scene_profile" in overrides and overrides["scene_profile"] is not None:
        if type(overrides["scene_profile"]) is not str:
            raise TypeError("scene_profile override must be a string")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    choices = _PROFILE_CHOICES.get(difficulty, SCENE_PROFILES)
    profile = ctx.draw_choice("scene_profile", choices)
    size, track, count = _parse_profile(profile)
    wall_offset = WALL_OFFSET_BY_SIZE[size]
    mid = size // 2

    grid = full_grid(size, size, 7)
    if track == "vertical":
        for row in range(size):
            grid[row][mid - wall_offset] = 0
            grid[row][mid + wall_offset] = 0
        for col in range(size):
            grid[mid][col] = 0
    else:
        for col in range(size):
            grid[mid - wall_offset][col] = 0
            grid[mid + wall_offset][col] = 0
        for row in range(size):
            grid[row][mid] = 0

    motif = _grow_centered_motif(
        size=size,
        track=track,
        wall_offset=wall_offset,
        count=count,
        rng=ctx.draw_rng("motif_growth"),
    )
    for row, col in motif:
        grid[row][col] = 5

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructive scene violated its contract: {errors}")
    return grid


def _rectangular_grid_error(grid) -> str | None:
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return "expected a nonempty rectangular grid"
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return "ragged grid"
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return "cells must be integer ARC colors 0..9 (not bool)"
    return None


def _is_divider(values) -> bool:
    return all(value in (0, 5) for value in values) or (
        sum(value == 0 for value in values) > len(values) // 2
    )


def _divider_rows(grid) -> list[int]:
    return [row for row, values in enumerate(grid) if _is_divider(values)]


def _divider_cols(grid) -> list[int]:
    height = len(grid)
    width = len(grid[0])
    return [
        col
        for col in range(width)
        if _is_divider([grid[row][col] for row in range(height)])
    ]


def _eight_connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        row, col = queue.popleft()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if not (dr or dc):
                    continue
                point = (row + dr, col + dc)
                if point in cells and point not in seen:
                    seen.add(point)
                    queue.append(point)
    return seen == cells


def semantic_observables(grid) -> dict[str, Any]:
    malformed = _rectangular_grid_error(grid)
    if malformed:
        return {"errors": [malformed]}

    height, width = len(grid), len(grid[0])
    rows = _divider_rows(grid)
    cols = _divider_cols(grid)
    mid_row, mid_col = height // 2, width // 2
    track = None
    wall_offset = None
    if len(cols) == 2 and len(rows) == 1:
        track = "vertical"
        wall_offset = cols[1] - mid_col
    elif len(rows) == 2 and len(cols) == 1:
        track = "horizontal"
        wall_offset = rows[1] - mid_row

    gray_cells = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    }
    bbox = None
    if gray_cells:
        gray_rows = [row for row, _ in gray_cells]
        gray_cols = [col for _, col in gray_cells]
        bbox = (
            min(gray_rows),
            max(gray_rows),
            min(gray_cols),
            max(gray_cols),
        )
    return {
        "errors": [],
        "height": height,
        "width": width,
        "center": (mid_row, mid_col),
        "divider_rows": rows,
        "divider_cols": cols,
        "track": track,
        "wall_offset": wall_offset,
        "gray_cells": gray_cells,
        "gray_count": len(gray_cells),
        "gray_bbox": bbox,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    facts = semantic_observables(grid)
    if facts["errors"]:
        return facts["errors"]

    errors: list[str] = []
    height, width = facts["height"], facts["width"]
    if height != width:
        errors.append("grid must be square")
    if height not in WALL_OFFSET_BY_SIZE:
        errors.append(
            f"grid size {height} is outside canonical sizes {tuple(WALL_OFFSET_BY_SIZE)}"
        )
    if any(value not in (0, 5, 7) for row in grid for value in row):
        errors.append("only colors 0, 5, and 7 are allowed")
    if errors:
        return errors

    mid = height // 2
    track = facts["track"]
    if track is None:
        errors.append(
            "expected exactly two parallel divider lines and one perpendicular divider"
        )
        return errors

    expected_offset = WALL_OFFSET_BY_SIZE[height]
    if facts["wall_offset"] != expected_offset:
        errors.append(
            f"parallel wall offset must be {expected_offset}, got {facts['wall_offset']}"
        )

    if track == "vertical":
        walls = facts["divider_cols"]
        crossbars = facts["divider_rows"]
        if crossbars != [mid]:
            errors.append(f"vertical track crossbar must be center row {mid}")
        left, right = mid - expected_offset, mid + expected_offset
        if any(grid[mid][col] != 0 for col in range(width) if col <= left or col >= right):
            errors.append("vertical track crossbar must be zero outside the channel")
        if walls != [left, right]:
            errors.append("vertical track walls must be symmetric canonical columns")
        if walls and any(grid[row][col] != 0 for col in walls for row in range(height)):
            errors.append("parallel walls must remain all zero")
    else:
        walls = facts["divider_rows"]
        crossbars = facts["divider_cols"]
        if crossbars != [mid]:
            errors.append(f"horizontal track crossbar must be center column {mid}")
        top, bottom = mid - expected_offset, mid + expected_offset
        if any(grid[row][mid] != 0 for row in range(height) if row <= top or row >= bottom):
            errors.append("horizontal track crossbar must be zero outside the channel")
        if walls != [top, bottom]:
            errors.append("horizontal track walls must be symmetric canonical rows")
        if walls and any(grid[row][col] != 0 for row in walls for col in range(width)):
            errors.append("parallel walls must remain all zero")

    gray_cells = facts["gray_cells"]
    gray_count = facts["gray_count"]
    if gray_count < 5 or gray_count > height or gray_count % 2 == 0:
        errors.append(
            f"gray-cell count must be odd and within 5..{height}, got {gray_count}"
        )
    if not gray_cells:
        return errors

    if track == "vertical":
        left, right = mid - expected_offset, mid + expected_offset
        if any(not left < col < right for _, col in gray_cells):
            errors.append("gray motif must stay strictly between vertical walls")
    else:
        top, bottom = mid - expected_offset, mid + expected_offset
        if any(not top < row < bottom for row, _ in gray_cells):
            errors.append("gray motif must stay strictly between horizontal walls")

    top, bottom, left, right = facts["gray_bbox"]
    if track == "vertical":
        if (left, right) != (mid - expected_offset + 1, mid + expected_offset - 1):
            errors.append("gray motif must reach both vertical channel sides")
        if top + bottom != 2 * mid or (bottom - top + 1) % 2 == 0:
            errors.append("gray motif track span must be odd and centered")
    else:
        if (top, bottom) != (mid - expected_offset + 1, mid + expected_offset - 1):
            errors.append("gray motif must reach both horizontal channel sides")
        if left + right != 2 * mid or (right - left + 1) % 2 == 0:
            errors.append("gray motif track span must be odd and centered")

    if not _eight_connected(gray_cells):
        errors.append("gray motif must be 8-connected")
    return sorted(set(errors))


def strict_canonical_like(grid) -> list[str]:
    """Canonical-profile gate: ordinary and public inputs share this manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    reasons = self_check(grid)
    if reasons:
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(reasons))
    facts = semantic_observables(grid)
    profile = f"n{facts['height']}_{facts['track']}_c{facts['gray_count']}"
    if profile not in SCENE_PROFILES:
        raise ValueError(
            "lawful canonical grid is outside the emitted scene_profile domain: "
            + profile
        )
    return {"scene_profile": profile}


def _render_with_count(grid, count: int):
    malformed = _rectangular_grid_error(grid)
    if malformed:
        raise ValueError(malformed)
    height, width = len(grid), len(grid[0])
    divider_rows = _divider_rows(grid)
    divider_cols = _divider_cols(grid)
    center_row = (height - 1) // 2
    center_col = (width - 1) // 2
    vertical = len(divider_cols) >= 2
    output = full_grid(height, width, 7)

    if vertical:
        for col in (center_col - 1, center_col + 1):
            for row in range(height):
                output[row][col] = 0
        for row in divider_rows:
            for col in range(width):
                output[row][col] = 0
        half = (count - 1) // 2
        for index in range(count):
            row = center_row - half + index
            if 0 <= row < height:
                output[row][center_col] = 5
    else:
        for row in (center_row - 1, center_row + 1):
            for col in range(width):
                output[row][col] = 0
        for col in divider_cols:
            for row in range(height):
                output[row][col] = 0
        half = (count - 1) // 2
        for index in range(count):
            col = center_col - half + index
            if 0 <= col < width:
                output[center_row][col] = 5
    return output


def rule_mirror(grid):
    """Pure Python mirror for tests and rival contracts, never label authority."""
    count = sum(value == 5 for row in grid for value in row)
    return _render_with_count(grid, count)


def _rival_canonical_size_to_count(grid):
    """Canonical-fitting shortcut: memorize gray-line length by grid size."""
    malformed = _rectangular_grid_error(grid)
    if malformed:
        raise ValueError(malformed)
    count = CANONICAL_COUNT_BY_SIZE.get(len(grid))
    if count is None:
        count = sum(value == 5 for row in grid for value in row)
    return _render_with_count(grid, count)


def _grids_equal(left, right) -> bool:
    try:
        return [list(row) for row in left] == [list(row) for row in right]
    except TypeError:
        return False


def _gray_count_not_size_lookup(grid) -> bool:
    return not _grids_equal(rule_mirror(grid), _rival_canonical_size_to_count(grid))


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "gray_count_not_size_lookup": _gray_count_not_size_lookup,
}
SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "canonical_size_to_count": _rival_canonical_size_to_count,
}
WITNESS_RIVALS = {
    "gray_count_not_size_lookup": ["canonical_size_to_count"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose demos leave a declared rival query-ambiguous."""
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        try:
            intended = rule_mirror(pair["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demo {index} outside rule grammar: {exc}")
            continue
        if not _grids_equal(intended, pair.get("output")):
            reasons.append(f"demo {index} output disagrees with pinned rule")

    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query outside rule grammar: {exc}")
        return reasons
    if "output" in query and not _grids_equal(query_answer, query["output"]):
        reasons.append("query output disagrees with pinned rule")

    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(
                _grids_equal(rival(pair["input"]), pair.get("output"))
                for pair in demos
            )
            if survives and not _grids_equal(rival(query["input"]), query_answer):
                reasons.append(
                    f"competitor {name!r} fits every demo but changes the query answer"
                )
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"competitor {name!r} raised: {exc}")
    return reasons
