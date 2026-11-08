"""Generator for ``arc_additional_puzzles_21_set3:E17``.

The rule is local and horizontal: every background cell flanked immediately by
gray cells (``5, 0, 5``) becomes green.  The input distribution teaches the
canonical distinct-row and shared-row cases, boundary placements, and unchanged
gray distractors without ever hiding the transformation on a normal draw.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "3180c5a8cff7"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "35f54e2db692"

SUMMARY = (
    "Generate 2..4 horizontal 5-0-5 sandwiches. Profiles cover distinct "
    "rows, multiple sandwiches in one row, both horizontal boundaries, and "
    "gray distractors that must remain unchanged."
)

INVARIANTS = [
    "the input palette is exactly background 0 and gray 5",
    "the input contains exactly 2..4 zero cells flanked horizontally by 5s",
    "applying the rule changes every such middle zero to green 3 and nothing else",
    "normal draws always contain at least two visible rule applications",
]

HELPFUL_TEXTURES = (
    "scattered_rows",
    "shared_row",
    "edge_anchored",
    "distractors",
)
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 5..12",
        "valid": "5..12",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 6..14",
        "valid": "6..14",
    },
    "num_triplets": {
        "type": "int",
        "default": "difficulty-aware rng 2..4",
        "valid": "2..4",
    },
    "texture": {
        "type": "str",
        "default": "rng over four structural lesson profiles",
        "valid": "|".join(HELPFUL_TEXTURES),
    },
}

_VALID_HEIGHT = (5, 12)
_VALID_WIDTH = (6, 14)
_VALID_TRIPLETS = (2, 4)
_BAND_BOUNDS = {
    "easy": {"grid_h": (5, 7), "grid_w": (6, 9), "num_triplets": (2, 2)},
    "medium": {"grid_h": (6, 9), "grid_w": (8, 11), "num_triplets": (2, 3)},
    "hard": {"grid_h": (8, 10), "grid_w": (10, 12), "num_triplets": (3, 4)},
}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> str:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "grid_w", "num_triplets"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    texture = overrides.get("texture")
    if texture is not None and texture not in HELPFUL_TEXTURES:
        raise ValueError(f"unknown texture: {texture!r}")
    return difficulty or "medium"


def _coerce_grid(grid: Any) -> list[list[Any]]:
    if not isinstance(grid, (list, tuple)):
        return []
    result = []
    for row in grid:
        if isinstance(row, str):
            result.append([int(value) if value.isdigit() else value for value in row])
        elif isinstance(row, (list, tuple)):
            result.append(list(row))
        else:
            return []
    return result


def _triplet_centres(grid: list[list[int]]) -> tuple[tuple[int, int], ...]:
    if not grid or not grid[0]:
        return ()
    width = len(grid[0])
    return tuple(
        (row, col)
        for row, values in enumerate(grid)
        for col in range(1, width - 1)
        if values[col] == 0
        and values[col - 1] == 5
        and values[col + 1] == 5
    )


def _analysis(grid: Any) -> dict[str, Any]:
    values = _coerce_grid(grid)
    errors: list[str] = []
    if not values or not values[0]:
        return {"errors": ["grid must be a non-empty rectangle"]}
    width = len(values[0])
    if any(not row or len(row) != width for row in values):
        return {"errors": ["grid must be rectangular"]}

    height = len(values)
    if not _VALID_HEIGHT[0] <= height <= _VALID_HEIGHT[1]:
        errors.append("grid height must be in 5..12")
    if not _VALID_WIDTH[0] <= width <= _VALID_WIDTH[1]:
        errors.append("grid width must be in 6..14")
    if any(
        type(value) is not int or value not in (0, 5)
        for row in values
        for value in row
    ):
        errors.append("input cells must be literal integers from palette {0, 5}")

    centres = _triplet_centres(values) if not errors else ()
    if not _VALID_TRIPLETS[0] <= len(centres) <= _VALID_TRIPLETS[1]:
        errors.append("input must contain exactly 2..4 horizontal 5-0-5 sandwiches")

    by_row = Counter(row for row, _ in centres)
    participating_fives = {
        (row, col + delta)
        for row, col in centres
        for delta in (-1, 1)
    }
    all_fives = {
        (row, col)
        for row, line in enumerate(values)
        for col, value in enumerate(line)
        if value == 5
    }
    distractor_fives = all_fives - participating_fives
    distractor_adjacent_pairs = {
        tuple(sorted(((row, col), (row + dr, col + dc))))
        for row, col in distractor_fives
        for dr, dc in ((0, 1), (1, 0))
        if (row + dr, col + dc) in distractor_fives
    }
    return {
        "errors": errors,
        "grid": values,
        "height": height,
        "width": width,
        "centres": centres,
        "triplet_count": len(centres),
        "triplet_rows": by_row,
        "shared_row": any(count >= 2 for count in by_row.values()),
        "left_edge": any(col == 1 for _, col in centres),
        "right_edge": any(col == width - 2 for _, col in centres),
        "distractor_fives": distractor_fives,
        "distractor_adjacent_pairs": distractor_adjacent_pairs,
    }


def _requested_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    requested = meta.get("overrides")
    if isinstance(requested, dict):
        return dict(requested)
    return {name: meta[name] for name in AXES if name in meta}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the structural lesson, plus exact requested semantics when known."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    requested = _requested_overrides(meta)
    count = requested.get("num_triplets")
    if count is not None and analysis["triplet_count"] != count:
        errors.append(
            f"num_triplets requested {count}, observed {analysis['triplet_count']}"
        )

    texture = requested.get("texture")
    if texture == "scattered_rows" and (
        len(analysis["triplet_rows"]) != analysis["triplet_count"]
    ):
        errors.append("scattered_rows requires every sandwich in a distinct row")
    elif texture == "shared_row" and not analysis["shared_row"]:
        errors.append("shared_row requires at least two sandwiches in one row")
    elif texture == "edge_anchored" and not (
        analysis["left_edge"] and analysis["right_edge"]
    ):
        errors.append("edge_anchored requires sandwiches at both horizontal edges")
    elif texture == "distractors" and (
        len(analysis["distractor_fives"]) < 3
        or not analysis["distractor_adjacent_pairs"]
    ):
        errors.append(
            "distractors requires at least three non-rule gray cells, including an adjacent pair"
        )
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Expose the exact semantic count recoverable from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe invalid grid: " + "; ".join(analysis["errors"]))
    return {"num_triplets": analysis["triplet_count"]}


def rule_mirror(grid) -> list[list[int]]:
    """Exact Python test mirror; the Racket program remains output authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    output = [row[:] for row in analysis["grid"]]
    for row, col in analysis["centres"]:
        output[row][col] = 3
    return output


def _place_triplet(grid: list[list[int]], row: int, start: int) -> bool:
    """Place one disjoint sandwich only when it creates exactly one rule match."""
    width = len(grid[0])
    if not (0 <= row < len(grid) and 0 <= start <= width - 3):
        return False
    if any(grid[row][col] != 0 for col in range(start, start + 3)):
        return False
    before = len(_triplet_centres(grid))
    candidate = [values[:] for values in grid]
    candidate[row][start] = 5
    candidate[row][start + 2] = 5
    if len(_triplet_centres(candidate)) != before + 1:
        return False
    grid[row][start] = 5
    grid[row][start + 2] = 5
    return True


def _place_one_in_row(grid: list[list[int]], row: int, rng) -> None:
    starts = list(range(len(grid[0]) - 2))
    rng.shuffle(starts)
    for start in starts:
        if _place_triplet(grid, row, start):
            return
    raise AssertionError(f"could not place a sandwich in row {row}")


def _place_scattered(
    grid: list[list[int]],
    count: int,
    rng,
    *,
    excluded_rows: tuple[int, ...] = (),
) -> None:
    rows = [row for row in range(len(grid)) if row not in excluded_rows]
    rng.shuffle(rows)
    if len(rows) < count:
        raise ValueError("requested profile cannot fit the sandwich count")
    for row in rows[:count]:
        _place_one_in_row(grid, row, rng)


def _place_shared_row(grid: list[list[int]], count: int, rng) -> None:
    width = len(grid[0])
    compatible = []
    for left in range(width - 2):
        for right in range(left + 1, width - 2):
            if not set(range(left, left + 3)).isdisjoint(
                range(right, right + 3)
            ):
                continue
            probe = [[0] * width]
            probe[0][left] = 5
            probe[0][left + 2] = 5
            probe[0][right] = 5
            probe[0][right + 2] = 5
            if len(_triplet_centres(probe)) == 2:
                compatible.append((left, right))
    if not compatible:
        raise ValueError("grid width cannot fit two disjoint sandwiches in one row")
    row = rng.randrange(len(grid))
    left, right = rng.choice(compatible)
    assert _place_triplet(grid, row, left)
    assert _place_triplet(grid, row, right)
    if count > 2:
        _place_scattered(grid, count - 2, rng, excluded_rows=(row,))


def _place_edge_anchored(grid: list[list[int]], count: int, rng) -> None:
    rows = list(range(len(grid)))
    rng.shuffle(rows)
    assert _place_triplet(grid, rows[0], 0)
    assert _place_triplet(grid, rows[1], len(grid[0]) - 3)
    if count > 2:
        _place_scattered(grid, count - 2, rng, excluded_rows=tuple(rows[:2]))


def _place_distractors(grid: list[list[int]], count: int, rng) -> None:
    reserve_row = rng.randrange(len(grid))
    _place_scattered(grid, count, rng, excluded_rows=(reserve_row,))
    if rng.choice((False, True)):
        grid[reserve_row][0] = 5
        grid[reserve_row][1] = 5
        grid[reserve_row][-1] = 5
    else:
        grid[reserve_row][-1] = 5
        grid[reserve_row][-2] = 5
        grid[reserve_row][0] = 5


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    bounds = _BAND_BOUNDS[band]
    height = ctx.draw_int(
        "grid_h",
        *(_VALID_HEIGHT if overrides.get("grid_h") is not None else bounds["grid_h"]),
    )
    width = ctx.draw_int(
        "grid_w",
        *(_VALID_WIDTH if overrides.get("grid_w") is not None else bounds["grid_w"]),
    )
    count = ctx.draw_int(
        "num_triplets",
        *(
            _VALID_TRIPLETS
            if overrides.get("num_triplets") is not None
            else bounds["num_triplets"]
        ),
    )
    texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)
    grid = full_grid(height, width, 0)
    rng = ctx.draw_rng("layout")

    if texture == "scattered_rows":
        _place_scattered(grid, count, rng)
    elif texture == "shared_row":
        _place_shared_row(grid, count, rng)
    elif texture == "edge_anchored":
        _place_edge_anchored(grid, count, rng)
    elif texture == "distractors":
        _place_distractors(grid, count, rng)
    else:  # guarded by draw_choice; keep the failure explicit if the table drifts.
        raise AssertionError(f"unhandled texture: {texture!r}")

    errors = self_check(
        grid,
        meta={"overrides": {"num_triplets": count, "texture": texture}},
    )
    if errors:
        raise AssertionError("generated invalid lesson: " + "; ".join(errors))
    return [row[:] for row in grid]
