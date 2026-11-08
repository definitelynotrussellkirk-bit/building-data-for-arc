"""Semantic generator for ARC task 6eb3835a5555.

Gray (5) cells are walls.  Each four-connected non-wall region is a room.
If a room contains exactly one *distinct* non-background seed color, fill its
zero cells with that color.  Empty rooms and rooms with multiple distinct seed
colors remain unchanged.
"""
from __future__ import annotations

from typing import Callable

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "6eb3835a5555"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "2944822b1e33"
SUMMARY = (
    "Fill each gray-wall room when it contains exactly one distinct seed color; "
    "leave empty or multi-color rooms unchanged."
)
INVARIANTS = [
    "color 5 forms a closed outer wall and may form complete or partial interior walls",
    "background is 0 and seed colors are drawn from 1..9 except gray 5",
    "a room is a four-connected component of non-wall cells",
    "ordinary lessons contain a repeated same-color room and a conflicting-color room",
]

SCENE_PROFILES = (
    "canonical_7x9",
    "canonical_7x8",
    "canonical_7x9_t",
    "canonical_7x8_l",
    "wide_9x13",
    "tall_13x10",
)
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic six-profile curriculum",
        "valid": "|".join(SCENE_PROFILES),
    }
}
EXAMPLES_NEEDED = 3

# Each profile is (height, width, horizontal wall segments, vertical wall
# segments).  Segments are inclusive: (fixed_coordinate, start, stop).
_PROFILE_SPECS = {
    # Official 7x9 chamber geometry.
    "canonical_7x9": (
        7,
        9,
        ((0, 0, 8), (3, 0, 8), (6, 0, 8)),
        ((0, 0, 6), (3, 0, 6), (8, 0, 6)),
    ),
    # Official 7x8 T-junction geometry: the lower half is one merged room.
    "canonical_7x8": (
        7,
        8,
        ((0, 0, 7), (3, 0, 7), (6, 0, 7)),
        ((0, 0, 6), (7, 0, 6), (4, 0, 3)),
    ),
    # Same exact canonical size/palette profile with a different T orientation.
    "canonical_7x9_t": (
        7,
        9,
        ((0, 0, 8), (3, 0, 8), (6, 0, 8)),
        ((0, 0, 6), (8, 0, 6), (4, 0, 3)),
    ),
    # Same exact canonical size/palette profile with a lower L divider.
    "canonical_7x8_l": (
        7,
        8,
        ((0, 0, 7), (3, 0, 7), (6, 0, 7)),
        ((0, 0, 6), (7, 0, 6), (3, 3, 6)),
    ),
    "wide_9x13": (
        9,
        13,
        ((0, 0, 12), (4, 0, 12), (8, 0, 12)),
        ((0, 0, 8), (4, 0, 8), (8, 0, 8), (12, 0, 8)),
    ),
    "tall_13x10": (
        13,
        10,
        ((0, 0, 9), (4, 0, 9), (8, 0, 9), (12, 0, 9)),
        ((0, 0, 12), (4, 0, 12), (9, 0, 12)),
    ),
}
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SEED_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)


def _validate_grid(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        return ["grid dimensions must be in 1..30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _rooms(grid) -> list[tuple[tuple[int, int], ...]]:
    """Return row-major four-connected components of cells that are not gray."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    rooms: list[tuple[tuple[int, int], ...]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 5 or (row, col) in seen:
                continue
            todo = [(row, col)]
            cells: set[tuple[int, int]] = set()
            while todo:
                rr, cc = todo.pop()
                if not (0 <= rr < height and 0 <= cc < width):
                    continue
                if (rr, cc) in seen or grid[rr][cc] == 5:
                    continue
                seen.add((rr, cc))
                cells.add((rr, cc))
                todo.extend((rr + dr, cc + dc) for dr, dc in _DIRS4)
            rooms.append(tuple(sorted(cells)))
    return rooms


def _analysis(grid) -> dict:
    errors = _validate_grid(grid)
    result = {"errors": errors}
    if errors:
        return result

    height, width = len(grid), len(grid[0])
    if any(grid[0][col] != 5 or grid[-1][col] != 5 for col in range(width)) or any(
        grid[row][0] != 5 or grid[row][-1] != 5 for row in range(height)
    ):
        errors.append("color 5 must form a closed outer wall")

    rooms = _rooms(grid)
    if len(rooms) < 2:
        errors.append("at least two wall-separated rooms are required")

    room_facts = []
    output = [list(row) for row in grid]
    for cells in rooms:
        seed_cells = [(row, col, grid[row][col]) for row, col in cells if grid[row][col] not in (0, 5)]
        distinct = tuple(sorted({value for _, _, value in seed_cells}))
        zero_cells = [(row, col) for row, col in cells if grid[row][col] == 0]
        if len(distinct) == 1:
            for row, col in zero_cells:
                output[row][col] = distinct[0]
        room_facts.append(
            {
                "cells": cells,
                "seed_cells": tuple(seed_cells),
                "distinct_seed_colors": distinct,
                "zero_cells": tuple(zero_cells),
            }
        )

    if not any(len(fact["distinct_seed_colors"]) == 1 and fact["zero_cells"] for fact in room_facts):
        errors.append("at least one room must have exactly one distinct seed color and a zero to fill")

    result.update(
        {
            "height": height,
            "width": width,
            "rooms": tuple(rooms),
            "room_facts": tuple(room_facts),
            "output": output,
            "errors": errors,
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if difficulty not in (None, "easy", "medium", "hard"):
        return [f"unknown difficulty: {difficulty!r}"]
    errors = list(_analysis(grid)["errors"])
    expected = meta.get("overrides") if isinstance(meta, dict) else None
    if not errors and isinstance(expected, dict) and expected.get("scene_profile") is not None:
        try:
            observed = observe_overrides(grid)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            if observed["scene_profile"] != expected["scene_profile"]:
                errors.append(
                    f"scene_profile override expected {expected['scene_profile']!r}, "
                    f"observed {observed['scene_profile']!r}"
                )
    return errors


def rule_mirror(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [row[:] for row in analysis["output"]]


def _wall_grid(profile: str) -> list[list[int]]:
    height, width, horizontal, vertical = _PROFILE_SPECS[profile]
    grid = [[0] * width for _ in range(height)]
    for row, start, stop in horizontal:
        for col in range(start, stop + 1):
            grid[row][col] = 5
    for col, start, stop in vertical:
        for row in range(start, stop + 1):
            grid[row][col] = 5
    return grid


def _wall_signature(grid) -> tuple[int, int, tuple[tuple[int, int], ...]]:
    return (
        len(grid),
        len(grid[0]),
        tuple((row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == 5),
    )


_PROFILE_SIGNATURES = {
    _wall_signature(_wall_grid(profile)): profile for profile in SCENE_PROFILES
}


def observe_overrides(grid) -> dict[str, str]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(analysis["errors"]))
    profile = _PROFILE_SIGNATURES.get(_wall_signature(grid))
    if profile is None:
        raise ValueError("wall geometry does not realize a declared scene_profile")
    return {"scene_profile": profile}


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
    if profile not in {(7, 8, 6), (7, 9, 6)}:
        errors.append(f"not an exact canonical (height,width,palette) profile: {profile!r}")
    return errors


def canonical_profile_signature(grid):
    if strict_canonical_like(grid):
        return None
    try:
        profile = observe_overrides(grid)["scene_profile"]
    except ValueError:
        return None
    return profile if profile.startswith("canonical_") else None


def _validate_scalar(name: str, value) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer (not bool)")
    if value < 0:
        raise ValueError(f"{name} must be non-negative")
    return value


def _validate_difficulty(difficulty) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return difficulty


def _populate(profile: str, rng) -> list[list[int]]:
    grid = _wall_grid(profile)
    rooms = _rooms(grid)
    if len(rooms) < 3:
        raise AssertionError(f"profile {profile!r} has fewer than three rooms")

    room_order = list(range(len(rooms)))
    rng.shuffle(room_order)
    repeated_index, conflict_index, singleton_index = room_order[:3]

    if profile in {"wide_9x13", "tall_13x10"}:
        # Structural anchors overlap the public examples' coarse signature:
        # one wall object plus four isolated marker objects.  Two non-adjacent
        # equal-color cells still form the repeated-same-color witness, while
        # two distinct cells form the conflict witness.
        colors = rng.sample(list(_SEED_COLORS), 3)
        repeated_cells = list(rooms[repeated_index])
        separated_pairs = [
            (left, right)
            for i, left in enumerate(repeated_cells)
            for right in repeated_cells[i + 1 :]
            if abs(left[0] - right[0]) + abs(left[1] - right[1]) > 1
        ]
        for row, col in rng.choice(separated_pairs):
            grid[row][col] = colors[0]
        conflict_cells = rng.sample(list(rooms[conflict_index]), 2)
        for (row, col), color in zip(conflict_cells, colors[1:]):
            grid[row][col] = color
        return grid

    colors = rng.sample(list(_SEED_COLORS), 4)

    # Exactly one distinct color but multiple occurrences: the decisive
    # counterexample to the strongest canonical shortcut.  Keep the two cells
    # adjacent so they form one non-singleton object; together with the three
    # conflicting markers and one isolated marker this preserves the canonical
    # four-marker signature while retaining the exact six-color profile.
    repeated_cells = set(rooms[repeated_index])
    adjacent_pairs = [
        ((row, col), (row + dr, col + dc))
        for row, col in sorted(repeated_cells)
        for dr, dc in ((1, 0), (0, 1))
        if (row + dr, col + dc) in repeated_cells
    ]
    for row, col in rng.choice(adjacent_pairs):
        grid[row][col] = colors[0]

    # Three distinct colors in one room: the room must remain unchanged.
    conflict_cells = rng.sample(list(rooms[conflict_index]), 3)
    for (row, col), color in zip(conflict_cells, colors[1:]):
        grid[row][col] = color

    # Reuse one of the four colors in a separate room so the total palette is
    # exactly {0, 5, four seed colors}, matching both canonical profiles.
    row, col = rng.choice(list(rooms[singleton_index]))
    grid[row][col] = rng.choice(colors)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_scalar("seed", seed)
    _validate_scalar("sample_index", sample_index)
    band = _validate_difficulty(difficulty)
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None:
        if type(requested) is not str:
            raise TypeError("scene_profile must be a string")
        if requested not in SCENE_PROFILES:
            raise ValueError(f"unknown scene_profile: {requested!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    scheduled = SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]
    options = SCENE_PROFILES if requested is not None else (scheduled,)
    profile = ctx.draw_choice("scene_profile", options)
    grid = _populate(profile, ctx.draw_rng(f"seed_layout_{band}"))
    errors = self_check(grid, difficulty=band, meta={"overrides": overrides})
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid


def _rival_exactly_one_seed_cell(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = [list(row) for row in grid]
    for fact in analysis["room_facts"]:
        if len(fact["seed_cells"]) == 1:
            color = fact["seed_cells"][0][2]
            for row, col in fact["zero_cells"]:
                output[row][col] = color
    return output


def _rival_fill_first_seed_color(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = [list(row) for row in grid]
    for fact in analysis["room_facts"]:
        if fact["seed_cells"]:
            color = fact["seed_cells"][0][2]
            for row, col in fact["zero_cells"]:
                output[row][col] = color
    return output


def _rival_fill_last_seed_color(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = [list(row) for row in grid]
    for fact in analysis["room_facts"]:
        if fact["seed_cells"]:
            color = fact["seed_cells"][-1][2]
            for row, col in fact["zero_cells"]:
                output[row][col] = color
    return output


def _has_repeated_same_color_room(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and any(
        len(fact["seed_cells"]) >= 2
        and len(fact["distinct_seed_colors"]) == 1
        and bool(fact["zero_cells"])
        for fact in analysis["room_facts"]
    )


def _has_conflicting_seed_colors(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and any(
        len(fact["distinct_seed_colors"]) >= 2 and bool(fact["zero_cells"])
        for fact in analysis["room_facts"]
    )


SEMANTIC_RIVALS: dict[str, Callable] = {
    "exactly_one_seed_cell": _rival_exactly_one_seed_cell,
    "fill_first_seed_color": _rival_fill_first_seed_color,
    "fill_last_seed_color": _rival_fill_last_seed_color,
}
CANONICAL_SHORTCUTS = {
    "exactly_one_seed_cell": _rival_exactly_one_seed_cell,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES: dict[str, Callable] = {
    "repeated_same_color_room": _has_repeated_same_color_room,
    "conflicting_seed_colors": _has_conflicting_seed_colors,
}
WITNESS_RIVALS = {
    "repeated_same_color_room": ("exactly_one_seed_cell",),
    "conflicting_seed_colors": ("fill_first_seed_color", "fill_last_seed_color"),
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a labelled lesson when any declared rival survives its demos."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    reasons: list[str] = []
    normalized = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is missing input/output")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except (TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the task grammar: {exc}")
            continue
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the distinct-color room rule")
            continue
        normalized.append(pair)

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is missing an input grid")
    else:
        try:
            expected_query = rule_mirror(query["input"])
        except (TypeError, ValueError) as exc:
            reasons.append(f"query is outside the task grammar: {exc}")
        else:
            if query.get("output") is not None and query["output"] != expected_query:
                reasons.append("query output disagrees with the distinct-color room rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in normalized):
            reasons.append(f"declared competitor {name!r} survives every demonstration")
    return reasons
