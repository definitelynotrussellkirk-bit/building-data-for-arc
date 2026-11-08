"""Generator for ``arc_additional_puzzles_21_set8:M53``.

The nonzero token at ``(0, 0)`` is a command.  Remove that token, crop the
single monochrome object, then apply the command-selected quarter turn:

``1`` identity, ``2`` clockwise, ``3`` 180 degrees, and ``4`` counterclockwise.

Four consecutive sample indexes deliberately cover all four commands.  The
five public axes are exact pixel-observable controls; every documented value is
constructive in every difficulty band.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache
from itertools import combinations
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "36adc51834d3"
VERSION = "2.0.1"
TASK_ID = "36adc51834d3"
RULE_HASH = "112ba59ebc7e"
EXAMPLES_NEEDED = 4

SUMMARY = (
    "A command at (0,0) selects identity/CW/180/CCW. Remove it, crop the "
    "single connected monochrome object, and apply the selected quarter turn."
)

INVARIANTS = [
    "the background is black 0 and (0,0) contains exactly one command in 1..4",
    "after removing the command there is one 8-connected monochrome object",
    "the command corner's remaining three cells are black",
    "the object has 3..10 cells and exposes four distinct quarter-turn views",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware full-domain draw with an 8..10 canonical prior",
        "valid": "6..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware full-domain draw with a 9..12 canonical prior",
        "valid": "6..14",
    },
    "blob_size": {
        "type": "int",
        "default": "difficulty-aware full-domain draw with a 5..6 canonical prior",
        "valid": "3..10",
    },
    "cmd": {
        "type": "int",
        "default": "1 + sample_index mod 4",
        "valid": "1..4",
    },
    "color_relation": {
        "type": "str",
        "default": "scheduled same/different relation, alternating by lesson cycle",
        "valid": "same|different",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[tuple[str, ...]] = []

_COMMANDS = (1, 2, 3, 4)
_RELATIONS = ("same", "different")
_LOCAL_CELLS = tuple((row, col) for row in range(4) for col in range(4))
_CANONICAL_PRIOR = {"easy": 0.75, "medium": 0.65, "hard": 0.55}
_CANONICAL_HEIGHTS = (8, 9, 10)
_CANONICAL_WIDTHS = (9, 10, 11, 12)
_CANONICAL_SIZES = (5, 6)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    for name in ("grid_h", "grid_w", "blob_size", "cmd"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    relation = overrides.get("color_relation")
    if relation is not None and type(relation) is not str:
        raise ValueError(
            "color_relation must be a string, "
            f"not {type(relation).__name__}"
        )


def _weighted_int(
    ctx,
    label: str,
    lo: int,
    hi: int,
    *,
    core: bool,
    canonical: Iterable[int],
    favored: Iterable[int],
) -> int:
    """Draw from the complete override domain, adding only sampling weight."""
    choices = list(range(lo, hi + 1))
    if core:
        choices.extend(list(canonical) * 14)
    choices.extend(list(favored) * 3)
    return int(ctx.draw_choice(label, choices))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic task input; the canonical Racket rule is authority."""
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty if difficulty in _CANONICAL_PRIOR else "medium"
    core = ctx.draw_rng("curriculum_profile").random() < _CANONICAL_PRIOR[band]

    favored_h = {
        "easy": range(6, 9),
        "medium": range(8, 12),
        "hard": range(11, 15),
    }[band]
    favored_w = {
        "easy": range(6, 9),
        "medium": range(8, 12),
        "hard": range(11, 15),
    }[band]
    favored_size = {
        "easy": range(3, 6),
        "medium": range(5, 8),
        "hard": range(8, 11),
    }[band]

    height = _weighted_int(
        ctx,
        "grid_h",
        6,
        14,
        core=core,
        canonical=_CANONICAL_HEIGHTS,
        favored=favored_h,
    )
    width = _weighted_int(
        ctx,
        "grid_w",
        6,
        14,
        core=core,
        canonical=_CANONICAL_WIDTHS,
        favored=favored_w,
    )
    size = _weighted_int(
        ctx,
        "blob_size",
        3,
        10,
        core=core,
        canonical=_CANONICAL_SIZES,
        favored=favored_size,
    )

    if overrides.get("cmd") is not None:
        command = ctx.draw_int("cmd", 1, 4)
    else:
        command = int(ctx.draw_choice("cmd", [1 + (int(sample_index) % 4)]))

    if overrides.get("color_relation") is not None:
        relation = str(ctx.draw_choice("color_relation", _RELATIONS))
    else:
        # The cycle parity flips the relation so every command appears with both
        # relations across two four-example lessons.
        cycle = int(sample_index) // 4
        scheduled = "same" if (int(sample_index) + cycle) % 2 == 0 else "different"
        relation = str(ctx.draw_choice("color_relation", [scheduled]))

    canonical_shape = (
        core
        and height in _CANONICAL_HEIGHTS
        and width in _CANONICAL_WIDTHS
        and size in _CANONICAL_SIZES
    )
    shape_options = _shape_catalog(size, canonical_only=canonical_shape)
    if not shape_options:
        raise RuntimeError(f"no transform-revealing connected shape for size {size}")
    shape = ctx.draw_rng("blob_shape").choice(shape_options)

    placements = _legal_placements(
        height,
        width,
        shape,
        canonical_margin=canonical_shape,
    )
    if not placements:
        # This is defensive only: every 4x4-or-smaller catalog shape has the
        # lower-right placement (2,2) on the minimum 6x6 canvas.
        raise RuntimeError(
            f"no legal placement for size-{size} shape on {height}x{width} canvas"
        )
    top, left = ctx.draw_rng("blob_position").choice(placements)

    if relation == "same":
        object_color = command
    else:
        object_color = ctx.draw_rng("blob_color").choice(
            [color for color in range(1, 10) if color != command]
        )

    grid = full_grid(height, width, 0)
    grid[0][0] = command
    for row, col in shape:
        grid[top + row][left + col] = object_color
    return grid


def _normalize_cells(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _turn_cells_cw(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _normalize_cells((col, -row) for row, col in cells)


def _quarter_turn_keys(cells: Iterable[tuple[int, int]]) -> set[tuple[tuple[int, int], ...]]:
    current = _normalize_cells(cells)
    views = set()
    for _ in range(4):
        views.add(current)
        current = _turn_cells_cw(current)
    return views


def _cells_connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen: set[tuple[int, int]] = set()
    queue = deque([next(iter(cells))])
    while queue:
        cell = queue.popleft()
        if cell in seen:
            continue
        seen.add(cell)
        row, col = cell
        for row_delta in (-1, 0, 1):
            for col_delta in (-1, 0, 1):
                if row_delta == 0 and col_delta == 0:
                    continue
                neighbor = (row + row_delta, col + col_delta)
                if neighbor in cells and neighbor not in seen:
                    queue.append(neighbor)
    return seen == cells


@lru_cache(maxsize=None)
def _shape_catalog(
    size: int,
    *,
    canonical_only: bool = False,
) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Enumerate small lawful polyominoes once, then sample without rejection."""
    shapes: set[tuple[tuple[int, int], ...]] = set()
    for chosen in combinations(_LOCAL_CELLS, size):
        occupied = set(chosen)
        if not _cells_connected(occupied):
            continue
        shape = _normalize_cells(occupied)
        box_h = max(row for row, _ in shape) + 1
        box_w = max(col for _, col in shape) + 1
        if box_h < 2 or box_w < 2:
            continue
        if canonical_only and (box_h, box_w) != (3, 3):
            continue
        if len(_quarter_turn_keys(shape)) != 4:
            continue
        shapes.add(shape)
    return tuple(sorted(shapes))


def _legal_placements(
    height: int,
    width: int,
    shape: tuple[tuple[int, int], ...],
    *,
    canonical_margin: bool,
) -> tuple[tuple[int, int], ...]:
    box_h = max(row for row, _ in shape) + 1
    box_w = max(col for _, col in shape) + 1
    command_zone = {(0, 0), (0, 1), (1, 0), (1, 1)}
    placements = []
    for top in range(height - box_h + 1):
        for left in range(width - box_w + 1):
            translated = {(top + row, left + col) for row, col in shape}
            if translated & command_zone:
                continue
            if canonical_margin:
                if top < 2 or left < 2:
                    continue
                if top + box_h > height - 1 or left + box_w > width - 1:
                    continue
            placements.append((top, left))
    return tuple(placements)


def _coerce_matrix(value: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(value, (list, tuple)) or not value:
        return None, ["grid must be a nonempty sequence of rows"]
    rows: list[list[int]] = []
    for row in value:
        if isinstance(row, str):
            if not row:
                return None, ["grid rows must be nonempty"]
            if any(character not in "0123456789" for character in row):
                return None, ["string rows must contain only ARC digits 0..9"]
            rows.append([int(character) for character in row])
        elif isinstance(row, (list, tuple)):
            rows.append(list(row))
        else:
            return None, ["each grid row must be a sequence or digit string"]
    width = len(rows[0])
    if width == 0 or any(len(row) != width for row in rows):
        return None, ["grid must be rectangular and nonempty"]
    if any(
        type(cell) is not int or not 0 <= cell <= 9
        for row in rows
        for cell in row
    ):
        return None, ["all cells must be integer ARC colors 0..9"]
    return rows, []


def _turn_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _turn_180(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(grid)]


def _turn_ccw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)][::-1]


def _apply_command(grid: list[list[int]], command: int) -> list[list[int]]:
    transforms: dict[int, Callable[[list[list[int]]], list[list[int]]]] = {
        1: lambda value: [list(row) for row in value],
        2: _turn_cw,
        3: _turn_180,
        4: _turn_ccw,
    }
    if command not in transforms:
        raise ValueError(f"command must be in 1..4, got {command!r}")
    return transforms[command](grid)


def _distinct_quarter_turns(grid: list[list[int]]) -> set[tuple[tuple[int, ...], ...]]:
    views = set()
    current = [list(row) for row in grid]
    for _ in range(4):
        views.add(tuple(tuple(row) for row in current))
        current = _turn_cw(current)
    return views


def _analyze(grid: Any) -> tuple[dict[str, Any], list[str]]:
    normalized, errors = _coerce_matrix(grid)
    if normalized is None:
        return {}, errors

    height = len(normalized)
    width = len(normalized[0])
    if not 6 <= height <= 14:
        errors.append(f"height must be in 6..14, got {height}")
    if not 6 <= width <= 14:
        errors.append(f"width must be in 6..14, got {width}")

    command = normalized[0][0]
    if command not in _COMMANDS:
        errors.append(f"command at (0,0) must be in 1..4, got {command}")
    if any(normalized[row][col] != 0 for row, col in ((0, 1), (1, 0), (1, 1))):
        errors.append("the three non-command cells in the 2x2 command corner must be black")

    object_cells = {
        (row, col)
        for row, values in enumerate(normalized)
        for col, cell in enumerate(values)
        if cell != 0 and (row, col) != (0, 0)
    }
    if not object_cells:
        return {
            "grid_h": height,
            "grid_w": width,
            "cmd": command,
            "blob_size": 0,
            "color_relation": None,
        }, errors + ["expected one nonempty object after removing the command"]

    if not 3 <= len(object_cells) <= 10:
        errors.append(f"object must contain 3..10 cells, got {len(object_cells)}")
    if not _cells_connected(object_cells):
        errors.append("object cells must form exactly one 8-connected component")

    colors = {normalized[row][col] for row, col in object_cells}
    if len(colors) != 1:
        errors.append(f"object must be monochrome, got {len(colors)} colors")
    object_color = next(iter(colors)) if len(colors) == 1 else None

    top = min(row for row, _ in object_cells)
    bottom = max(row for row, _ in object_cells)
    left = min(col for _, col in object_cells)
    right = max(col for _, col in object_cells)
    # The authoritative rule removes the command cell before cropping.  The
    # object may legitimately surround the command corner so that its bounding
    # box contains (0, 0) without occupying it; never leak the command token
    # into the object crop used by semantic rivals or lesson validation.
    object_only = [list(values) for values in normalized]
    object_only[0][0] = 0
    crop = [values[left : right + 1] for values in object_only[top : bottom + 1]]
    box_h = len(crop)
    box_w = len(crop[0])
    if box_h < 2 or box_w < 2:
        errors.append(f"object bounding box must be at least 2x2, got {box_h}x{box_w}")
    view_count = len(_distinct_quarter_turns(crop))
    if view_count != 4:
        errors.append(
            f"object must expose four distinct quarter-turn views, got {view_count}"
        )

    relation = None
    if object_color is not None and command in _COMMANDS:
        relation = "same" if object_color == command else "different"

    facts = {
        "grid_h": height,
        "grid_w": width,
        "blob_size": len(object_cells),
        "cmd": command,
        "color_relation": relation,
        "object_color": object_color,
        "object_h": box_h,
        "object_w": box_w,
        "top": top,
        "bottom": bottom,
        "left": left,
        "right": right,
        "distinct_quarter_turns": view_count,
        "crop": crop,
        "normalized_grid": normalized,
    }
    return facts, errors


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover all declared exact axes from returned pixels."""
    facts, errors = _analyze(grid)
    if errors:
        return {}
    return {
        "grid_h": int(facts["grid_h"]),
        "grid_w": int(facts["grid_w"]),
        "blob_size": int(facts["blob_size"]),
        "cmd": int(facts["cmd"]),
        "color_relation": str(facts["color_relation"]),
    }


def profile_signature(grid) -> dict[str, Any]:
    facts, errors = _analyze(grid)
    public_facts = {key: value for key, value in facts.items() if key != "normalized_grid"}
    return {"valid": not errors, "errors": errors, **public_facts}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed/rule-hiding scenes and verify requested exact axes."""
    del difficulty
    facts, errors = _analyze(grid)
    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update(nested)
        requested.update({axis: meta[axis] for axis in AXES if axis in meta})
    if facts and requested and not errors:
        observed = observe_overrides(grid)
        for axis, expected in requested.items():
            if axis in AXES and expected is not None and observed.get(axis) != expected:
                errors.append(
                    f"override {axis} requested {expected!r}, "
                    f"observed {observed.get(axis)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the canonical canvas/object envelope without replaying examples."""
    facts, errors = _analyze(grid)
    if errors:
        return errors
    reasons: list[str] = []
    if facts["grid_h"] not in _CANONICAL_HEIGHTS:
        reasons.append(f"canonical height is 8..10, got {facts['grid_h']}")
    if facts["grid_w"] not in _CANONICAL_WIDTHS:
        reasons.append(f"canonical width is 9..12, got {facts['grid_w']}")
    if facts["blob_size"] not in _CANONICAL_SIZES:
        reasons.append(f"canonical object size is 5..6, got {facts['blob_size']}")
    if (facts["object_h"], facts["object_w"]) != (3, 3):
        reasons.append(
            "canonical object bounding box is 3x3, got "
            f"{facts['object_h']}x{facts['object_w']}"
        )
    return reasons


def _crop_object(grid: Any) -> list[list[int]]:
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError(errors[0])
    return [list(row) for row in facts["crop"]]


def _valid_command(grid: Any) -> int | None:
    facts, errors = _analyze(grid)
    return None if errors else int(facts["cmd"])


SEMANTIC_WITNESSES = {
    f"command_{command}": (
        lambda grid, expected=command: _valid_command(grid) == expected
    )
    for command in _COMMANDS
}


def _rival_ignore_command(grid: Any) -> list[list[int]]:
    return _crop_object(grid)


def _rival_always_cw(grid: Any) -> list[list[int]]:
    return _turn_cw(_crop_object(grid))


def _rival_marker_only(grid: Any) -> list[list[int]]:
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError(errors[0])
    return [[int(facts["cmd"])]]


SEMANTIC_RIVALS = {
    "ignore_command": _rival_ignore_command,
    "always_cw": _rival_always_cw,
}
WITNESS_RIVALS = {
    "command_1": ["always_cw"],
    "command_2": ["ignore_command"],
    "command_3": ["ignore_command"],
    "command_4": ["ignore_command"],
}
# No known wrong rule reproduces every canonical pair.  These remain explicit
# lesson competitors rather than being mislabeled as canonical ambiguities.
CANONICAL_SHORTCUTS: dict[str, Callable[[Any], list[list[int]]]] = {}
LESSON_COMPETITORS = {
    "ignore_command": _rival_ignore_command,
    "always_cw": _rival_always_cw,
    "marker_only": _rival_marker_only,
}


def _normalized_output(value: Any) -> list[list[int]] | None:
    normalized, errors = _coerce_matrix(value)
    return None if errors else normalized


def lesson_identifiable(demos, query) -> list[str]:
    """Require one valid, correctly labeled demonstration for each command."""
    if not isinstance(demos, list) or not isinstance(query, dict):
        return ["lesson must contain a demo list and one query pair"]

    reasons: list[str] = []
    seen: set[int] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        facts, errors = _analyze(pair["input"])
        if errors:
            reasons.append(f"demo {index} input invalid: {errors[0]}")
            continue
        command = int(facts["cmd"])
        seen.add(command)
        expected = _apply_command(facts["crop"], command)
        actual = _normalized_output(pair["output"])
        if actual != expected:
            reasons.append(f"demo {index} does not match command {command}")

    missing = sorted(set(_COMMANDS) - seen)
    if missing:
        reasons.append(f"demos omit command(s) {missing}")

    if "input" not in query or "output" not in query:
        reasons.append("query is not an input/output pair")
        return reasons
    query_facts, query_errors = _analyze(query["input"])
    if query_errors:
        reasons.append(f"query input invalid: {query_errors[0]}")
        return reasons
    query_command = int(query_facts["cmd"])
    if query_command not in seen:
        reasons.append(f"query command {query_command} has no demonstration")
    expected_query = _apply_command(query_facts["crop"], query_command)
    if _normalized_output(query["output"]) != expected_query:
        reasons.append("query output disagrees with the command mapping")

    for name, competitor in LESSON_COMPETITORS.items():
        refuted = False
        for pair in demos:
            if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
                continue
            try:
                rival = competitor(pair["input"])
            except (TypeError, ValueError):
                continue
            if _normalized_output(pair["output"]) != rival:
                refuted = True
                break
        if not refuted:
            reasons.append(f"demos do not refute competitor {name!r}")
    return reasons


def schedule_profile(seed, sample_index, difficulty=None) -> int:
    """Name the command residue used by the four-example schedule."""
    del seed, difficulty
    return 1 + (int(sample_index) % 4)


SCHEDULE_PROFILES = _COMMANDS


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Named structural impostors that ``self_check`` must reject."""
    missing_command = full_grid(8, 9, 0)
    for row, col in ((3, 3), (4, 3), (4, 4)):
        missing_command[row][col] = 5

    missing_object = full_grid(8, 9, 0)
    missing_object[0][0] = 2

    disconnected = full_grid(8, 9, 0)
    disconnected[0][0] = 3
    disconnected[3][3] = 6
    disconnected[3][4] = 6
    disconnected[5][5] = 6

    multicolor = full_grid(8, 9, 0)
    multicolor[0][0] = 4
    multicolor[3][3] = 6
    multicolor[4][3] = 6
    multicolor[4][4] = 7

    rotation_alias = full_grid(8, 9, 0)
    rotation_alias[0][0] = 2
    for row, col in ((3, 3), (3, 4), (4, 3), (4, 4)):
        rotation_alias[row][col] = 8

    command_intrusion = full_grid(8, 9, 0)
    command_intrusion[0][0] = 1
    for row, col in ((0, 1), (1, 1), (2, 1)):
        command_intrusion[row][col] = 5

    return [
        ("missing_command", missing_command),
        ("missing_object", missing_object),
        ("disconnected_object", disconnected),
        ("multicolor_object", multicolor),
        ("rotation_alias_square", rotation_alias),
        ("command_corner_intrusion", command_intrusion),
    ]
