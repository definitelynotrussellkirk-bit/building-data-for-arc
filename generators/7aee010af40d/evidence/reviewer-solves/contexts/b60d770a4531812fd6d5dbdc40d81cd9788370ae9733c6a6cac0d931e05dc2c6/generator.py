"""Semantic generator for ARC task 7aee010af40d.

Select the uniquely smallest orange (7) component, crop it to its bounding
box, and recolor the selected shape cyan (8).  Non-orange components are
explicit distractors and are deliberately smaller than the answer, so a
color-blind "smallest object" shortcut is wrong on every generated scene.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7aee010af40d"
TASK_ID = "7aee010af40d"
VERSION = "3.2.0"
RULE_HASH = "8e254e2caadf"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.35

SUMMARY = (
    "On a zero background, select the uniquely smallest 4-connected orange(7) "
    "component, crop it tightly, and recolor its cells cyan(8). Non-orange "
    "components are irrelevant distractors and may be smaller than the answer."
)

INVARIANTS = [
    "background is literal color 0",
    "there are three or four separated orange(7) components",
    "one orange component is uniquely smallest",
    "there is one non-orange distractor color with one or two components",
    "at least one non-orange distractor is smaller than the selected orange component",
    "the output is the selected orange shape cropped and recolored cyan(8)",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 8..10 on three scheduled examples; otherwise difficulty-aware",
        "valid": "8..12",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 10..12 on three scheduled examples; otherwise difficulty-aware",
        "valid": "10..14",
    },
    "small_k": {
        "type": "int",
        "default": "ten-slot anti-copy schedule spanning sizes 2..6",
        "valid": "2..6",
    },
    "n_big": {
        "type": "int",
        "default": "2 on canonical-linked examples; 2 or 3 otherwise",
        "valid": "2..3",
    },
    "n_distractors": {
        "type": "int",
        "default": "1 on canonical-linked examples; 2 otherwise",
        "valid": "1..2",
    },
    "distractor_color": {
        "type": "int",
        "default": "one keyed non-orange color",
        "valid": "1..6|9",
    },
}

_CANONICAL_DIMS = ((8, 10), (8, 11), (9, 11), (9, 12), (10, 12))
_DISTRACTOR_COLORS = (1, 2, 3, 4, 5, 6, 9)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Five demonstrations are followed by one query.  A five-period target
# schedule therefore made the query's normalized answer exactly equal to the
# first demonstration's answer, regardless of the query input.  This ten-role
# schedule keeps every five consecutive examples pedagogically broad while
# making roles i and i+5 deliberately different.
_TARGET_SCHEDULE = (
    (2, "horizontal"),
    (4, "bent"),
    (3, "vertical"),
    (5, "bent"),
    (6, "bent"),
    (3, "horizontal"),
    (5, "bent"),
    (2, "vertical"),
    (4, "bent"),
    (5, "bent"),
)


def _validate_grid(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions exceed ARC 30x30"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _components(grid, color: int | None = None) -> list[dict]:
    """Return same-color 4-connected non-background components."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    result: list[dict] = []
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value == 0 or (color is not None and value != color) or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if (nr, nc) in seen or grid[nr][nc] != value:
                        continue
                    seen.add((nr, nc))
                    stack.append((nr, nc))
            result.append({"color": value, "cells": tuple(sorted(cells))})
    return result


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _dims(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    shape = tuple(shape)
    return (
        max(row for row, _ in shape) + 1,
        max(col for _, col in shape) + 1,
    )


def _target_component(grid) -> dict:
    oranges = _components(grid, 7)
    return min(
        oranges,
        key=lambda component: (
            len(component["cells"]),
            component["cells"][0][0],
            component["cells"][0][1],
        ),
    )


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror used only for semantic tests and witnesses."""
    target = _target_component(grid)
    shape = _normalize(target["cells"])
    height, width = _dims(shape)
    output = full_grid(height, width, 0)
    for row, col in shape:
        output[row][col] = 8
    return output


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-hiding scenes; accept all canonical inputs."""
    errors = _validate_grid(grid)
    if errors:
        return errors

    oranges = _components(grid, 7)
    if len(oranges) < 3:
        errors.append(f"need at least three orange components; found {len(oranges)}")
    if len(oranges) > 4:
        errors.append(f"allow at most four orange components; found {len(oranges)}")

    orange_sizes = [len(component["cells"]) for component in oranges]
    if orange_sizes and orange_sizes.count(min(orange_sizes)) != 1:
        errors.append("smallest orange component must be unique")

    other_components = [component for component in _components(grid) if component["color"] != 7]
    other_colors = {component["color"] for component in other_components}
    if not other_components:
        errors.append("need at least one non-orange distractor component")
    if len(other_colors) != 1:
        errors.append("all non-orange distractors must share exactly one color")
    if len(other_components) > 2:
        errors.append("allow at most two non-orange distractor components")

    # Generated scenes always carry a smaller color-blind decoy. Canonical
    # rows are older and include both smaller and larger decoys, so this is a
    # teaching-distribution property checked by strict_canonical_like/witnesses,
    # not a canonical-acceptance requirement in self_check.
    return errors


def _is_connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for dr, dc in _CARDINAL:
            nxt = (row + dr, col + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == cells


@lru_cache(maxsize=None)
def _shapes(size: int, max_h: int, max_w: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    """All normalized connected shapes of ``size`` fitting the small room."""
    positions = [(row, col) for row in range(max_h) for col in range(max_w)]
    unique: set[tuple[tuple[int, int], ...]] = set()
    for choice in combinations(positions, size):
        cells = set(choice)
        if _is_connected(cells):
            unique.add(_normalize(cells))
    return tuple(sorted(unique))


def _transform(shape, code: int):
    cells = list(shape)
    if code & 4:
        cells = [(row, -col) for row, col in cells]
    for _ in range(code & 3):
        cells = [(col, -row) for row, col in cells]
    return _normalize(cells)


def _scheduled_target_shape(size: int, role: int, selector: int):
    """Choose the role's output shape without repeating it five steps later."""
    kind = _TARGET_SCHEDULE[role][1]
    if kind == "horizontal" and size <= 3:
        return tuple((0, col) for col in range(size))
    if kind == "vertical" and size <= 3:
        return tuple((row, 0) for row in range(size))

    candidates = _shapes(size, 3, 3)
    if kind == "bent":
        bent = tuple(
            shape
            for shape in candidates
            if _dims(shape)[0] > 1 and _dims(shape)[1] > 1
        )
        if bent:
            candidates = bent
    # Absolute sample position participates in ``selector`` so repeated roles
    # in later ten-step cycles continue to traverse the finite vocabulary.
    return candidates[int(selector) % len(candidates)]


def _draw_int(ctx, overrides, label: str, scheduled: Iterable[int], lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return int(ctx.draw_choice(label, tuple(scheduled)))


def _draw_choice(ctx, overrides, label: str, scheduled, legal):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, tuple(legal))
    return ctx.draw_choice(label, tuple(scheduled))


def _room_layout(height: int, width: int, rng):
    """Six separated rooms; four 3x3 rooms and two 3x2 rooms."""
    middle = (width - 2) // 2
    rooms = [
        (0, 0, 3, 3),
        (0, middle, 3, 3),
        (0, width - 2, 3, 2),
        (height - 3, 0, 3, 3),
        (height - 3, middle, 3, 3),
        (height - 3, width - 2, 3, 2),
    ]
    if rng.randrange(2):
        rooms = [(height - row - room_h, col, room_h, room_w) for row, col, room_h, room_w in rooms]
    if rng.randrange(2):
        rooms = [(row, width - col - room_w, room_h, room_w) for row, col, room_h, room_w in rooms]
    return rooms


def _paint_in_room(grid, shape, room, color: int, rng) -> None:
    row0, col0, room_h, room_w = room
    shape_h, shape_w = _dims(shape)
    if shape_h > room_h or shape_w > room_w:
        raise ValueError(f"shape {shape_h}x{shape_w} does not fit room {room_h}x{room_w}")
    row0 += rng.randint(0, room_h - shape_h)
    col0 += rng.randint(0, room_w - shape_w)
    for row, col in shape:
        grid[row0 + row][col0 + col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    band = "medium" if difficulty is None else difficulty
    if band not in {"easy", "medium", "hard"}:
        raise ValueError(f"unknown difficulty {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    sample_index = int(sample_index)
    role = sample_index % len(_TARGET_SCHEDULE)
    scheduled_size, _shape_kind = _TARGET_SCHEDULE[role]
    canonical_linked = scheduled_size in (2, 3)
    rng = ctx.draw_rng("layout")

    if canonical_linked:
        canonical_h, canonical_w = _CANONICAL_DIMS[(int(seed) + role) % len(_CANONICAL_DIMS)]
        h_options = (canonical_h,)
        w_options = (canonical_w,)
        small_options = (scheduled_size,)
        big_options = (2,)
        distractor_count_options = (1,)
        color_options = (2, 3, 4, 5)
    else:
        h_options = {
            "easy": (8, 9, 10),
            "medium": (9, 10, 11),
            "hard": (10, 11, 12),
        }[band]
        w_options = {
            "easy": (10, 11, 12),
            "medium": (11, 12, 13),
            "hard": (12, 13, 14),
        }[band]
        small_options = (scheduled_size,)
        big_options = (2,) if band == "easy" else ((2, 3) if band == "medium" else (3,))
        distractor_count_options = (2,)
        color_options = _DISTRACTOR_COLORS

    height = _draw_int(ctx, overrides, "grid_h", h_options, 8, 12)
    width = _draw_int(ctx, overrides, "grid_w", w_options, 10, 14)
    small_k = _draw_int(ctx, overrides, "small_k", small_options, 2, 6)
    n_big = _draw_int(ctx, overrides, "n_big", big_options, 2, 3)
    n_distractors = _draw_int(
        ctx, overrides, "n_distractors", distractor_count_options, 1, 2
    )
    distractor_color = int(
        _draw_choice(
            ctx,
            overrides,
            "distractor_color",
            color_options,
            _DISTRACTOR_COLORS,
        )
    )

    grid = full_grid(height, width, 0)
    rooms = _room_layout(height, width, rng)
    wide_rooms = sorted((room for room in rooms if room[3] == 3), key=lambda room: (room[0], room[1]))
    narrow_rooms = [room for room in rooms if room[3] == 2]

    # Any five consecutive examples traverse all four spatial roles.  Advancing
    # by five also advances the room by one, so the query cannot copy the first
    # demonstration's target location.
    target_room = wide_rooms[sample_index % len(wide_rooms)]
    remaining_wide = [room for room in wide_rooms if room != target_room]
    rng.shuffle(remaining_wide)

    target_shape = _scheduled_target_shape(
        small_k,
        role,
        int(seed) * 1315423911 + sample_index,
    )
    _paint_in_room(grid, target_shape, target_room, 7, rng)

    for offset, room in enumerate(remaining_wide[:n_big], start=1):
        size = small_k + offset
        candidates = _shapes(size, room[2], room[3])
        if not candidates:
            raise ValueError(f"no connected {size}-cell shape fits orange room")
        _paint_in_room(grid, rng.choice(candidates), room, 7, rng)

    available = remaining_wide[n_big:] + narrow_rooms
    rng.shuffle(available)
    distractor_sizes = (small_k - 1, max(1, small_k - 2))
    for index in range(n_distractors):
        room = available[index]
        size = distractor_sizes[index]
        candidates = _shapes(size, room[2], room[3])
        if not candidates:
            raise ValueError(f"no connected {size}-cell distractor fits room")
        _paint_in_room(grid, rng.choice(candidates), room, distractor_color, rng)

    errors = self_check(grid)
    if errors:
        raise ValueError("internal generation invariant failed: " + "; ".join(errors))
    return grid


def observe_overrides(grid) -> dict[str, int]:
    oranges = _components(grid, 7)
    other = [component for component in _components(grid) if component["color"] != 7]
    colors = sorted({component["color"] for component in other})
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "small_k": min(len(component["cells"]) for component in oranges),
        "n_big": len(oranges) - 1,
        "n_distractors": len(other),
        "distractor_color": colors[0] if len(colors) == 1 else -1,
    }


def strict_canonical_like(grid) -> list[str]:
    reasons = self_check(grid)
    if reasons:
        return reasons
    height, width = len(grid), len(grid[0])
    oranges = _components(grid, 7)
    other = [component for component in _components(grid) if component["color"] != 7]
    palette = {value for row in grid for value in row}
    target_size = min(len(component["cells"]) for component in oranges)
    if (height, width) not in _CANONICAL_DIMS:
        reasons.append("dimensions are outside the five canonical profiles")
    if len(oranges) not in (3, 4):
        reasons.append("canonical profile has three or four orange components")
    if len(other) != 1:
        reasons.append("canonical profile has exactly one non-orange component")
    if target_size not in (2, 3):
        reasons.append("canonical target size is two or three cells")
    if len(palette) != 3:
        reasons.append("canonical input palette has exactly three colors")
    return reasons


def _target_shape(grid):
    return _normalize(_target_component(grid)["cells"])


def _nonorange_smaller(grid) -> bool:
    target_size = len(_target_component(grid)["cells"])
    return any(
        len(component["cells"]) < target_size
        for component in _components(grid)
        if component["color"] != 7
    )


def _target_not_first_orange(grid) -> bool:
    oranges = sorted(_components(grid, 7), key=lambda component: component["cells"][0])
    return _target_component(grid)["cells"] != oranges[0]["cells"]


def _target_not_largest_orange(grid) -> bool:
    target = _target_component(grid)
    largest = max(
        _components(grid, 7),
        key=lambda component: (len(component["cells"]), component["cells"][0]),
    )
    return target["cells"] != largest["cells"]


def _horizontal_target(grid) -> bool:
    return _dims(_target_shape(grid))[0] == 1


def _vertical_target(grid) -> bool:
    return _dims(_target_shape(grid))[1] == 1


def _bent_target(grid) -> bool:
    height, width = _dims(_target_shape(grid))
    return height > 1 and width > 1


def _large_target(grid) -> bool:
    return len(_target_component(grid)["cells"]) >= 4


def _select_component_output(grid, key) -> list[list[int]]:
    component = key(_components(grid))
    shape = _normalize(component["cells"])
    height, width = _dims(shape)
    output = full_grid(height, width, 0)
    for row, col in shape:
        output[row][col] = 8
    return output


def _smallest_nonzero_rival(grid):
    return _select_component_output(
        grid,
        lambda components: min(components, key=lambda comp: (len(comp["cells"]), comp["cells"][0])),
    )


def _largest_orange_rival(grid):
    oranges = _components(grid, 7)
    return _select_component_output(
        grid,
        lambda _components_: max(oranges, key=lambda comp: (len(comp["cells"]), comp["cells"][0])),
    )


def _first_orange_rival(grid):
    oranges = _components(grid, 7)
    return _select_component_output(
        grid,
        lambda _components_: min(oranges, key=lambda comp: comp["cells"][0]),
    )


SEMANTIC_RIVALS = {
    "smallest_nonzero": _smallest_nonzero_rival,
    "largest_orange": _largest_orange_rival,
    "first_orange": _first_orange_rival,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# Every canonical demonstration places the selected orange object first in
# row-major order, so the canonical set alone cannot falsify this shortcut.
# Generated examples deliberately move the target among separated rooms.
CANONICAL_SHORTCUTS = {
    "first_orange": _first_orange_rival,
}

# These are semantic counterexamples to executable wrong rules.  Shape and
# size coverage remain useful curriculum metrics, but they are not themselves
# evidence against a rule and therefore do not belong in SEMANTIC_WITNESSES.
SEMANTIC_WITNESSES = {
    "smaller_nonorange_decoy": _nonorange_smaller,
    "target_not_largest_orange": _target_not_largest_orange,
    "target_not_first_orange": _target_not_first_orange,
}
WITNESS_RIVALS = {
    "smaller_nonorange_decoy": ["smallest_nonzero"],
    "target_not_largest_orange": ["largest_orange"],
    "target_not_first_orange": ["first_orange"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Verify five demonstrations reject each declared executable rival."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    for index, pair in enumerate(demos[:EXAMPLES_NEEDED]):
        grid = pair.get("input")
        output = pair.get("output")
        errors = self_check(grid)
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        official = rule_mirror(grid)
        if output != official:
            reasons.append(f"demo {index} output disagrees with the orange-minimum rule")
        if not _nonorange_smaller(grid):
            reasons.append(f"demo {index} lacks a smaller non-orange decoy")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(
            competitor(pair["input"]) == pair["output"]
            for pair in demos[:EXAMPLES_NEEDED]
        ):
            reasons.append(f"named rival {name!r} fits every demonstration")

    q_grid = query.get("input")
    q_output = query.get("output")
    q_errors = self_check(q_grid)
    if q_errors:
        reasons.append(f"query malformed: {q_errors[0]}")
    elif q_output != rule_mirror(q_grid):
        reasons.append("query answer disagrees with the orange-minimum rule")
    return reasons
