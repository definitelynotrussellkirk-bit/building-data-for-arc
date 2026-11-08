"""Generator for 4f09f8bfa35a — command-driven rotations of a selected crop.

The canonical authority reads command codes from row 0 (2=identity, 3=clockwise,
4=180 degrees, 5=counter-clockwise).  It zeros that row, finds binary nonzero
4-connected components in the body, selects the largest with top/left tie breaks,
crops the *original body* to that component's bounding box, rotates that crop for
each command, and packs the copies left-to-right with one blank column between.

Version 3 replaces the former one-object sampler with source-bound teaching cases.
Every ordinary example contains a smaller earlier component, an equal-area later
component, disconnected cargo inside the selected bounding box, a multicolor
selected crop, and all four commands in a non-sorted order.  These cases refute
selection, crop, command, packing, and monochrome shortcuts in every pair.  Exact
controls use a separate constructive layout and are recoverable from returned
pixels.
"""
from __future__ import annotations

from collections.abc import Sequence
from copy import deepcopy
from itertools import permutations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4f09f8bfa35a"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "8710221699c5"

SUMMARY = (
    "Read row-0 rotation commands, select the largest body component with "
    "top/left tie breaks, crop the original body through its bounding box, "
    "rotate that crop for each command, and pack the copies with one-column gaps."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "row 0 contains one to five codes from {2,3,4,5}, in left-to-right command order",
    "the body contains at least one nonzero 4-connected component of size >=2",
    "largest-component ties are lawful and resolve by smaller bbox top then left",
    "the selected crop preserves every original body pixel inside its bounding box",
    "the packed output is at most 30x30",
]

AXES = {
    "n_commands": {
        "type": "int",
        "default": "4 in teaching examples; 3 when another exact axis is requested",
        "valid": "1..5",
    },
    "shape_size": {
        "type": "int",
        "default": "8",
        "valid": "2..12",
    },
    "n_distractors": {
        "type": "int",
        "default": "3 in teaching examples; 2 when another exact axis is requested",
        "valid": "0..3",
    },
    "shape_color": {
        "type": "color",
        "default": "rng 2..5 in teaching examples; 6 when another exact axis is requested",
        "valid": "1..9",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_COMMANDS = (2, 3, 4, 5)
_PROFILE_BY_BAND = {
    "easy": (8, 12),
    "medium": (9, 13),
    "hard": (10, 14),
}
_CANONICAL_PROFILES = {
    (8, 12, 5),
    (9, 13, 5),
    (10, 14, 5),
    (8, 11, 4),
    (10, 15, 6),
}
_SEMANTIC_COMMAND_ORDERS = tuple(
    order for order in permutations(_COMMANDS) if order != _COMMANDS
)

Grid = list[list[int]]
Component = list[tuple[int, int]]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> str:
    if difficulty is None:
        band = "medium"
    elif difficulty in _PROFILE_BY_BAND:
        band = difficulty
    else:
        raise ValueError("difficulty must be easy, medium, hard, or None")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))

    bounds = {
        "n_commands": (1, 5),
        "shape_size": (2, 12),
        "n_distractors": (0, 3),
        "shape_color": (1, 9),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside {lo}..{hi}")
    return band


def _rectangular_arc_grid(grid: Any) -> tuple[bool, int, int, str | None]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return False, 0, 0, "expected a nonempty rectangular grid"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return False, 0, 0, "expected a nonempty rectangular grid"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return False, 0, 0, "grid must be rectangular"
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return False, 0, 0, "cells must be integer ARC colors 0..9"
    return True, len(grid), width, None


def _body_components(grid: Sequence[Sequence[int]]) -> list[Component]:
    """Binary nonzero 4-connected components after row 0 is erased."""
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[Component] = []
    for row in range(1, height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: Component = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        1 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            found.append(cells)
    return found


def _bbox(component: Component) -> tuple[int, int, int, int]:
    return (
        min(row for row, _ in component),
        min(col for _, col in component),
        max(row for row, _ in component),
        max(col for _, col in component),
    )


def _selected_component(
    grid: Sequence[Sequence[int]],
    *,
    selector: str = "canonical",
) -> Component:
    components = _body_components(grid)
    if not components:
        raise ValueError("body contains no object")
    if selector == "first":
        return min(components, key=lambda cells: (_bbox(cells)[0], _bbox(cells)[1]))
    if selector == "reverse_ties":
        return sorted(
            components,
            key=lambda cells: (-len(cells), -_bbox(cells)[0], -_bbox(cells)[1]),
        )[0]
    return sorted(
        components,
        key=lambda cells: (-len(cells), _bbox(cells)[0], _bbox(cells)[1]),
    )[0]


def _crop(
    grid: Sequence[Sequence[int]],
    component: Component,
    *,
    component_cells_only: bool = False,
) -> Grid:
    top, left, bottom, right = _bbox(component)
    selected = set(component)
    return [
        [
            int(grid[row][col])
            if (not component_cells_only or (row, col) in selected)
            else 0
            for col in range(left, right + 1)
        ]
        for row in range(top, bottom + 1)
    ]


def _rotate_cw(grid: Grid) -> Grid:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid: Grid) -> Grid:
    return [row[::-1] for row in grid[::-1]]


def _rotate_ccw(grid: Grid) -> Grid:
    return [list(row) for row in zip(*grid)][::-1]


def _apply_command(template: Grid, command: int) -> Grid:
    if command == 2:
        return deepcopy(template)
    if command == 3:
        return _rotate_cw(template)
    if command == 4:
        return _rotate_180(template)
    if command == 5:
        return _rotate_ccw(template)
    raise ValueError(f"unsupported command {command}")


def _pack(copies: Sequence[Grid], *, gap: int = 1) -> Grid:
    if not copies:
        raise ValueError("cannot pack an empty command list")
    height = max(len(piece) for piece in copies)
    width = sum(len(piece[0]) for piece in copies) + gap * (len(copies) - 1)
    out = full_grid(height, width, 0)
    left = 0
    for piece in copies:
        for row, values in enumerate(piece):
            for col, value in enumerate(values):
                if value != 0:
                    out[row][left + col] = value
        left += len(piece[0]) + gap
    return out


def _rule_mirror(
    grid: Sequence[Sequence[int]],
    *,
    selector: str = "canonical",
    command_map: Callable[[list[int]], list[int]] | None = None,
    component_cells_only: bool = False,
    gap: int = 1,
    monochrome: bool = False,
) -> Grid:
    commands = [int(value) for value in grid[0] if value in _COMMANDS]
    if command_map is not None:
        commands = command_map(commands)
    component = _selected_component(grid, selector=selector)
    template = _crop(grid, component, component_cells_only=component_cells_only)
    if monochrome:
        top, left, _, _ = _bbox(component)
        color = int(grid[top][left])
        template = [[color if value else 0 for value in row] for row in template]
    return _pack([_apply_command(template, command) for command in commands], gap=gap)


def _semantic_grid(ctx: Any, band: str, shape_color: int) -> Grid:
    height, width = _PROFILE_BY_BAND[band]
    grid = full_grid(height, width, 0)

    order = ctx.draw_rng(f"semantic_command_order_{band}").choice(_SEMANTIC_COMMAND_ORDERS)
    other_columns = sorted(
        ctx.draw_rng(f"semantic_command_columns_{band}").sample(range(1, width), 3)
    )
    columns = (0, *other_columns)
    for col, command in zip(columns, order):
        grid[0][col] = command

    # A one-cell body component continues vertically from the first command.
    # The authority erases row 0 before object selection, so this remains a
    # separate, earlier body object while matching canonical object-count scale.
    grid[1][0] = order[0]

    base_selected = (
        (0, 0), (0, 1), (1, 0), (2, 0),
        (3, 0), (3, 1), (3, 2), (3, 3),
    )
    base_cargo = (1, 2)
    transforms = (
        lambda row, col: (row, col),
        lambda row, col: (col, 3 - row),
        lambda row, col: (3 - row, 3 - col),
        lambda row, col: (3 - row, col),
    )
    transform = ctx.draw_rng(f"semantic_template_variant_{band}").choice(transforms)
    selected = tuple(transform(row, col) for row, col in base_selected)
    cargo = transform(*base_cargo)

    top, left = 3, 1
    for dr, dc in selected:
        grid[top + dr][left + dc] = shape_color

    # Disconnected, contrasting cargo is inside the selected bbox and therefore
    # survives the crop even though it is not part of the selected component.
    cargo_choices = tuple(color for color in _COMMANDS if color != shape_color)
    cargo_color = ctx.draw_rng(f"semantic_cargo_color_{band}").choice(cargo_choices)
    grid[top + cargo[0]][left + cargo[1]] = cargo_color

    # An equal-area but later component makes the canonical top/left tie break observable.
    competitor = (
        (0, 0), (0, 1), (0, 2),
        (1, 0),         (1, 2),
        (2, 0), (2, 1), (2, 2),
    )
    competitor_left = 8
    for dr, dc in competitor:
        grid[top + dr][competitor_left + dc] = 4

    return grid


def _serpentine_polyomino(size: int) -> tuple[tuple[int, int], ...]:
    cells: list[tuple[int, int]] = []
    for row in range(3):
        columns = range(4) if row % 2 == 0 else range(3, -1, -1)
        for col in columns:
            cells.append((row, col))
            if len(cells) == size:
                return tuple(cells)
    raise ValueError(f"unsupported shape size {size}")


def _exact_grid(
    ctx: Any,
    *,
    n_commands: int,
    shape_size: int,
    n_distractors: int,
    shape_color: int,
) -> Grid:
    grid = full_grid(13, 18, 0)
    command_cycle = (5, 2, 4, 3, 5)
    columns = (1, 4, 7, 10, 13)
    shift = ctx.draw_rng("exact_command_shift").randrange(4)
    codes = command_cycle[shift:4] + command_cycle[:shift] + (command_cycle[4],)
    for col, command in zip(columns[:n_commands], codes[:n_commands]):
        grid[0][col] = command

    top, left = 5, 7
    for index, (dr, dc) in enumerate(_serpentine_polyomino(shape_size)):
        grid[top + dr][left + dc] = shape_color if index == 0 else shape_color

    distractor_cells = ((2, 0), (3, 17), (11, 1))
    distractor_colors = (1 if shape_color != 1 else 2, 9 if shape_color != 9 else 8, 4 if shape_color != 4 else 6)
    for (row, col), color in zip(distractor_cells[:n_distractors], distractor_colors):
        grid[row][col] = color
    return grid


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: str | None = None,
    **overrides: Any,
) -> Grid:
    """Construct a lawful task input; every declared control is exact."""
    band = _validate_call(difficulty, overrides)
    explicit = any(value is not None for value in overrides.values())
    effective = {
        "n_commands": 3 if explicit else 4,
        "shape_size": 8,
        "n_distractors": 2 if explicit else 3,
    }
    if explicit:
        effective["shape_color"] = 6
    effective.update({name: value for name, value in overrides.items() if value is not None})
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    n_commands = ctx.draw_int_strict("n_commands", 1, 5)
    shape_size = ctx.draw_int_strict("shape_size", 2, 12)
    n_distractors = ctx.draw_int_strict("n_distractors", 0, 3)
    if explicit:
        shape_color = ctx.draw_int_strict("shape_color", 1, 9)
    else:
        shape_color = ctx.draw_int_strict("shape_color", 2, 5)

    if not explicit:
        return _semantic_grid(ctx, band, shape_color)
    return _exact_grid(
        ctx,
        n_commands=n_commands,
        shape_size=shape_size,
        n_distractors=n_distractors,
        shape_color=shape_color,
    )


def observe_overrides(grid: Sequence[Sequence[int]]) -> dict[str, int]:
    """Recover every advertised exact axis from returned pixels."""
    reasons = self_check(grid)
    if reasons:
        raise ValueError("; ".join(reasons))
    component = _selected_component(grid)
    top, left, _, _ = _bbox(component)
    return {
        "n_commands": sum(value in _COMMANDS for value in grid[0]),
        "shape_size": len(component),
        "n_distractors": len(_body_components(grid)) - 1,
        "shape_color": int(grid[top][left]),
    }


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    del difficulty, meta
    okay, height, width, message = _rectangular_arc_grid(grid)
    if not okay:
        return [str(message)]
    errors: list[str] = []
    if height > 30 or width > 30:
        errors.append(f"input dimensions {height}x{width} exceed 30x30")
    if height < 3:
        errors.append("input needs a command row and at least two body rows")
    elif any(value != 0 for value in grid[1]):
        bridge_cells = [(col, value) for col, value in enumerate(grid[1]) if value != 0]
        if not (
            len(bridge_cells) == 1
            and bridge_cells[0][1] in _COMMANDS
            and grid[0][bridge_cells[0][0]] == bridge_cells[0][1]
        ):
            errors.append(
                "row 1 must be blank or contain one same-color vertical continuation beneath a command"
            )
    illegal_row0 = [value for value in grid[0] if value not in (0, *_COMMANDS)]
    if illegal_row0:
        errors.append(f"row 0 contains non-command colors: {sorted(set(illegal_row0))}")
    commands = [value for value in grid[0] if value in _COMMANDS]
    if not 1 <= len(commands) <= 5:
        errors.append(f"expected 1..5 command codes in row 0, found {len(commands)}")
    components = _body_components(grid)
    if not components:
        errors.append("missing nonzero body component")
        return errors
    selected = sorted(
        components,
        key=lambda cells: (-len(cells), _bbox(cells)[0], _bbox(cells)[1]),
    )[0]
    if len(selected) < 2:
        errors.append("selected component must contain at least two cells")
    if commands:
        top, left, bottom, right = _bbox(selected)
        crop_h = bottom - top + 1
        crop_w = right - left + 1
        heights = [crop_h if command in (2, 4) else crop_w for command in commands]
        widths = [crop_w if command in (2, 4) else crop_h for command in commands]
        out_h = max(heights)
        out_w = sum(widths) + len(commands) - 1
        if out_h > 30 or out_w > 30:
            errors.append(f"packed output dimensions {out_h}x{out_w} exceed 30x30")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    colors = len({value for row in grid for value in row})
    profile = (len(grid), len(grid[0]), colors)
    if profile not in _CANONICAL_PROFILES:
        return [f"input profile {profile} is outside the five canonical profiles"]
    return []


# --- task-local rival programs -------------------------------------------------

def _first_component(grid: Grid) -> Grid:
    return _rule_mirror(grid, selector="first")


def _reverse_largest_tie(grid: Grid) -> Grid:
    return _rule_mirror(grid, selector="reverse_ties")


def _component_cells_only(grid: Grid) -> Grid:
    return _rule_mirror(grid, component_cells_only=True)


def _identity_commands(grid: Grid) -> Grid:
    return _rule_mirror(grid, command_map=lambda commands: [2] * len(commands))


def _reverse_command_order(grid: Grid) -> Grid:
    return _rule_mirror(grid, command_map=lambda commands: list(reversed(commands)))


def _sorted_command_order(grid: Grid) -> Grid:
    return _rule_mirror(grid, command_map=lambda commands: sorted(commands))


def _swap_quarter_turns(grid: Grid) -> Grid:
    return _rule_mirror(
        grid,
        command_map=lambda commands: [5 if command == 3 else 3 if command == 5 else command for command in commands],
    )


def _pack_without_gaps(grid: Grid) -> Grid:
    return _rule_mirror(grid, gap=0)


def _monochrome_template(grid: Grid) -> Grid:
    return _rule_mirror(grid, monochrome=True)


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "first_component": _first_component,
    "reverse_largest_tie": _reverse_largest_tie,
    "component_cells_only": _component_cells_only,
    "identity_commands": _identity_commands,
    "reverse_command_order": _reverse_command_order,
    "sorted_command_order": _sorted_command_order,
    "swap_quarter_turns": _swap_quarter_turns,
    "pack_without_gaps": _pack_without_gaps,
    "monochrome_template": _monochrome_template,
}

# These two tempting rules fit all five canonical pairs, so generated lessons
# must deliberately break them rather than relying only on canonical support.
CANONICAL_SHORTCUTS = {
    "first_component": _first_component,
    "component_cells_only": _component_cells_only,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _refutes(name: str, grid: Grid) -> bool:
    try:
        return SEMANTIC_RIVALS[name](grid) != _rule_mirror(grid)
    except Exception:
        return False


SEMANTIC_WITNESSES = {
    name: (lambda grid, rival_name=name: _refutes(rival_name, grid))
    for name in SEMANTIC_RIVALS
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Report any declared rival fitting every demo but disagreeing on query."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["lesson has no demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
            differs = rival(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"rival {name} raised {type(exc).__name__}: {exc}")
            continue
        if fits and differs:
            reasons.append(f"declared rival {name} fits every demonstration but changes the query")
    return reasons
