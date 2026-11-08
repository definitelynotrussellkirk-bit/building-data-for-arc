"""Generator for ARC task 6d678fbbe87e: complete local 2x2 corners.

For every 2x2 window in the *input*, if exactly three cells have one equal
non-zero colour and the fourth cell is zero, fill that zero with the shared
colour.  All qualifying windows are evaluated against the original input and
applied simultaneously.

The canonical examples contain only isolated three-cell L components.  The
scheduled generated lessons also include connected same-colour components with
multiple qualifying windows.  Those examples distinguish the local window rule
from object-bounding-box, one-fill-per-colour, isolated-object, and iterative
closure shortcuts while preserving the canonical rule exactly.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "6d678fbbe87e"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "e0165fc03ab4"

SUMMARY = (
    "Scan every 2x2 input window. If it contains exactly three equal non-zero "
    "cells and one zero corner, fill that zero with the shared colour. Apply "
    "all such completions simultaneously and preserve every other cell."
)

INVARIANTS = [
    "background is colour 0",
    "the input uses exactly three non-zero colours",
    "the input contains three or four qualifying 2x2 windows",
    "every non-zero colour participates in at least one qualifying window",
    "qualifying windows never demand different colours at the same cell",
]

# These are the only caller-facing controls.  Both are exact and recoverable
# from the returned pixels through observe_overrides().
AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-anchored 4..8",
        "valid": "4..8",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-anchored 5..10",
        "valid": "5..10",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4

# Four compact teaching scenes.  The numeric labels are placeholders remapped
# to three distinct colours on every draw.  Slot 0 is canonical-like and
# isolated. Slots 1..3 contain a five-cell connected same-colour component
# whose two local targets are not equivalent to completing its whole object.
_TEMPLATES: tuple[tuple[tuple[int, ...], ...], ...] = (
    (
        (1, 1, 0, 2, 2),
        (1, 0, 0, 0, 2),
        (0, 0, 3, 0, 0),
        (0, 3, 3, 0, 0),
    ),
    (
        (1, 1, 1, 1, 0),
        (0, 1, 0, 0, 0),
        (0, 2, 0, 3, 0),
        (2, 2, 0, 3, 3),
    ),
    (
        (1, 0, 0, 2, 2),
        (1, 1, 0, 2, 0),
        (1, 0, 0, 3, 3),
        (1, 0, 0, 0, 3),
    ),
    (
        (2, 2, 0, 3, 3),
        (2, 0, 0, 0, 3),
        (0, 1, 0, 0, 0),
        (1, 1, 1, 1, 0),
    ),
)
SCHEDULE_PROFILES = (
    "isolated_canonical_anchor",
    "connected_canonical_anchor",
    "connected_vertical",
    "connected_bottom",
)

Cell = tuple[int, int]
Target = tuple[int, int, int, Cell, int]
Grid = list[list[int]]


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic curriculum slot name."""
    del seed, difficulty
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative literal integer")
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _rectangular_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _target_windows(grid: Sequence[Sequence[int]]) -> list[Target]:
    """Return all local targets from the original input.

    A target tuple is ``(row, col, colour, missing_cell, missing_index)`` with
    corner order top-left, top-right, bottom-left, bottom-right.
    """
    height, width = len(grid), len(grid[0])
    targets: list[Target] = []
    for row in range(height - 1):
        for col in range(width - 1):
            cells = (
                (row, col),
                (row, col + 1),
                (row + 1, col),
                (row + 1, col + 1),
            )
            values = [grid[r][c] for r, c in cells]
            nonzero = [value for value in values if value != 0]
            if len(nonzero) != 3 or len(set(nonzero)) != 1 or values.count(0) != 1:
                continue
            missing_index = values.index(0)
            targets.append(
                (row, col, nonzero[0], cells[missing_index], missing_index)
            )
    return targets


def _components(grid: Sequence[Sequence[int]]) -> list[tuple[int, set[Cell]]]:
    """Return non-zero four-connected monochrome components."""
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }
    result: list[tuple[int, set[Cell]]] = []
    while unseen:
        start = min(unseen)
        colour = grid[start[0]][start[1]]
        component = {start}
        stack = [start]
        unseen.remove(start)
        while stack:
            row, col = stack.pop()
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (row + drow, col + dcol)
                if nxt in unseen and grid[nxt[0]][nxt[1]] == colour:
                    unseen.remove(nxt)
                    component.add(nxt)
                    stack.append(nxt)
        result.append((colour, component))
    return result


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_grid_errors(grid)
    if errors:
        return {"errors": errors, "targets": []}

    height, width = len(grid), len(grid[0])
    if not 4 <= height <= 8:
        errors.append(f"height must be in 4..8, found {height}")
    if not 5 <= width <= 10:
        errors.append(f"width must be in 5..10, found {width}")

    nonzero_colours = {value for row in grid for value in row if value != 0}
    if len(nonzero_colours) != 3:
        errors.append(
            f"expected exactly three non-zero colours, found {len(nonzero_colours)}"
        )

    targets = _target_windows(grid)
    if not 3 <= len(targets) <= 4:
        errors.append(f"expected 3-4 qualifying 2x2 windows, found {len(targets)}")

    demanded: dict[Cell, int] = {}
    for _row, _col, colour, cell, _corner in targets:
        old = demanded.setdefault(cell, colour)
        if old != colour:
            errors.append(
                f"qualifying windows demand conflicting colours at {cell}: {old} and {colour}"
            )

    participating = {colour for _r, _c, colour, _cell, _corner in targets}
    missing_colours = sorted(nonzero_colours - participating)
    if missing_colours:
        errors.append(
            f"non-zero colours without a qualifying window: {missing_colours}"
        )

    if targets:
        output = [list(row) for row in grid]
        for _r, _c, colour, (target_row, target_col), _corner in targets:
            output[target_row][target_col] = colour
        if output == [list(row) for row in grid]:
            errors.append("the rule must change at least one cell")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "targets": targets,
        "colours": nonzero_colours,
        "missing_indices": {target[4] for target in targets},
        "components": _components(grid),
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, no-op, ambiguous, or off-manifold inputs."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and requested is not None and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The accepted generator grammar is the task-linked strict manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact public axis from pixels alone."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {"grid_h": analysis["height"], "grid_w": analysis["width"]}


def rule_mirror(grid) -> Grid:
    """Independent Python mirror; the pinned Racket program remains authority."""
    errors = _rectangular_grid_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    output = [list(row) for row in grid]
    for _row, _col, colour, (target_row, target_col), _corner in _target_windows(grid):
        output[target_row][target_col] = colour
    return output


def _isolated_l_components_only(grid) -> Grid:
    """Rival: only complete targets whose colour component has exactly 3 cells."""
    errors = _rectangular_grid_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    component_size: dict[Cell, int] = {}
    for _colour, component in _components(grid):
        for cell in component:
            component_size[cell] = len(component)

    output = [list(row) for row in grid]
    for row, col, colour, (target_row, target_col), missing_index in _target_windows(grid):
        cells = (
            (row, col),
            (row, col + 1),
            (row + 1, col),
            (row + 1, col + 1),
        )
        anchor = next(cell for index, cell in enumerate(cells) if index != missing_index)
        if component_size[anchor] == 3:
            output[target_row][target_col] = colour
    return output


def _component_bbox_completion(grid) -> Grid:
    """Rival: fill each monochrome component's full bounding rectangle."""
    errors = _rectangular_grid_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    output = [list(row) for row in grid]
    for colour, component in _components(grid):
        rows = [row for row, _col in component]
        cols = [col for _row, col in component]
        for row in range(min(rows), max(rows) + 1):
            for col in range(min(cols), max(cols) + 1):
                output[row][col] = colour
    return output


def _one_completion_per_color(grid) -> Grid:
    """Rival: complete at most the first row-major target of each colour."""
    errors = _rectangular_grid_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    output = [list(row) for row in grid]
    completed: set[int] = set()
    for _row, _col, colour, (target_row, target_col), _corner in _target_windows(grid):
        if colour in completed:
            continue
        completed.add(colour)
        output[target_row][target_col] = colour
    return output


def _repeat_until_stable(grid) -> Grid:
    """Rival: repeatedly rescan outputs instead of applying one simultaneous pass."""
    errors = _rectangular_grid_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    output = [list(row) for row in grid]
    for _ in range(len(output) * len(output[0]) + 1):
        updated = rule_mirror(output)
        if updated == output:
            return output
        output = updated
    raise RuntimeError("completion did not converge within the grid-area bound")


SEMANTIC_RIVALS: dict[str, Callable[[Any], Grid]] = {
    "isolated_l_components_only": _isolated_l_components_only,
    "component_bbox_completion": _component_bbox_completion,
    "one_completion_per_color": _one_completion_per_color,
    "repeat_until_stable": _repeat_until_stable,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _connected_multiwindow_component(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    expected = rule_mirror(grid)
    return all(rival(grid) != expected for rival in SEMANTIC_RIVALS.values())


def _missing_corner(index: int):
    def witness(grid) -> bool:
        analysis = _analysis(grid)
        return not analysis["errors"] and index in analysis["missing_indices"]

    return witness


SEMANTIC_WITNESSES = {
    "connected_multiwindow_component": _connected_multiwindow_component,
    "missing_top_left": _missing_corner(0),
    "missing_top_right": _missing_corner(1),
    "missing_bottom_left": _missing_corner(2),
    "missing_bottom_right": _missing_corner(3),
}
WITNESS_RIVALS = {
    "connected_multiwindow_component": sorted(SEMANTIC_RIVALS),
}
BRANCH_WITNESSES = {
    "missing_top_left",
    "missing_top_right",
    "missing_bottom_left",
    "missing_bottom_right",
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named canonical-fitting shortcut survives demos."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict):
        return ["query must be an input/output pair"]

    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        grammar_errors = self_check(pair["input"])
        if grammar_errors:
            reasons.append(f"pair {index} input is outside the teaching grammar")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"pair {index} output disagrees with the local 2x2 rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            if competitor(query["input"]) != query["output"]:
                reasons.append(f"demonstrations do not refute rival: {name}")
    return reasons


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative literal integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be a literal integer")


def _draw_size(
    ctx,
    sample_index: int,
    difficulty: str | None,
    overrides: dict[str, Any],
) -> tuple[int, int]:
    explicit_h = overrides.get("grid_h") is not None
    explicit_w = overrides.get("grid_w") is not None
    residue = sample_index % LESSON_SCHEDULE_PERIOD

    # Anchor slots intentionally retain the two canonical profiles in every
    # band. Broad slots make difficulty observable with disjoint default size
    # supports; explicit overrides always retain the full advertised domain.
    broad_bounds = {
        "easy": ((4, 5), (5, 6)),
        "medium": ((6, 7), (7, 8)),
        "hard": ((8, 8), (9, 10)),
        None: ((4, 8), (5, 10)),
    }
    height_bounds, width_bounds = broad_bounds[difficulty]

    if explicit_h:
        height = ctx.draw_int_strict("grid_h", 4, 8)
    elif residue in (0, 1):
        height = ctx.draw_int_strict("grid_h", 4, 4)
    else:
        height = ctx.draw_int_strict("grid_h", *height_bounds)

    if explicit_w:
        width = ctx.draw_int_strict("grid_w", 5, 10)
    elif residue == 0:
        width = ctx.draw_int_strict("grid_w", 5, 5)
    elif residue == 1:
        width = ctx.draw_int_strict("grid_w", 6, 6)
    else:
        width = ctx.draw_int_strict("grid_w", *width_bounds)
    return height, width


def _transform_template(template: Sequence[Sequence[int]], *, flip_v: bool, flip_h: bool) -> Grid:
    rows = [list(row) for row in template]
    if flip_v:
        rows.reverse()
    if flip_h:
        rows = [list(reversed(row)) for row in rows]
    return rows


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; Racket owns the output labels."""
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height, width = _draw_size(ctx, sample_index, difficulty, overrides)
    rng = ctx.draw_rng("layout")

    template = _transform_template(
        _TEMPLATES[sample_index % LESSON_SCHEDULE_PERIOD],
        flip_v=bool(rng.randrange(2)),
        flip_h=bool(rng.randrange(2)),
    )
    palette = rng.sample(range(1, 10), 3)
    colour_map = {index + 1: colour for index, colour in enumerate(palette)}
    row_offset = rng.randint(0, height - len(template))
    col_offset = rng.randint(0, width - len(template[0]))

    grid = full_grid(height, width, 0)
    for row, values in enumerate(template):
        for col, value in enumerate(values):
            if value:
                grid[row_offset + row][col_offset + col] = colour_map[value]

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": overrides},
    )
    if errors:
        raise ValueError("constructed invalid instance: " + "; ".join(errors))
    return [row[:] for row in grid]
