"""Generator for 6c2353a2cdee — overlay transformed templates to a count map.

The input contains three 5x5 template panels separated by blank columns.  A
single code beneath each panel selects identity / clockwise / 180-degree /
counter-clockwise rotation.  The transformed binary supports are overlaid and
encoded as 2 for one cover, 4 for two covers, and 8 for three covers.

Canonical examples use compact, connected 5-8 cell templates occupying the
middle three rows.  The previous generator sampled scattered cells over the
entire 5x5 panel, creating a visually different task with many disconnected
components.  Ordinary draws now preserve the canonical template grammar and a
four-example code schedule while still varying shapes and colors.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6c2353a2cdee"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "9fc3fd333ca6"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Three compact connected 5x5 templates, each paired with a rotation code "
    "1-4; overlay their transformed supports and encode coverage counts as "
    "1->2, 2->4, and 3->8."
)

INVARIANTS = [
    "the input is exactly 7x17 with blank separator row 5 and columns 5 and 11",
    "each 5x5 panel contains one connected single-color template of 5-8 cells",
    "templates occupy and span rows 1..3, matching the canonical examples",
    "the code row contains exactly one distinct code in 1..4 beneath each panel",
    "ordinary outputs visibly contain single, double, and triple overlap counts",
    "every four consecutive ordinary samples omit each transform code once",
]

AXES = {
    "panel0_cells": {
        "type": "int",
        "default": "rng 5..8",
        "valid": "5..8",
        "doc": "Exact number of occupied cells in the left template.",
    },
    "panel1_cells": {
        "type": "int",
        "default": "rng 5..8",
        "valid": "5..8",
        "doc": "Exact number of occupied cells in the middle template.",
    },
    "panel2_cells": {
        "type": "int",
        "default": "rng 5..8",
        "valid": "5..8",
        "doc": "Exact number of occupied cells in the right template.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_PANEL_STARTS = (0, 6, 12)
_PANEL_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CODE_SCHEDULE = (
    (1, 2, 3),  # omit 4
    (4, 1, 2),  # omit 3
    (3, 4, 1),  # omit 2
    (2, 3, 4),  # omit 1
)


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int or not 5 <= value <= 8:
            raise ValueError(f"{name} must be an integer in 5..8")


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


def _rotate_ccw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)][::-1]


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid]


def _flip_ud(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in grid[::-1]]


def _transform(panel: list[list[int]], code: int) -> list[list[int]]:
    if code == 1:
        return [list(row) for row in panel]
    if code == 2:
        return _rotate_cw(panel)
    if code == 3:
        return _rotate_180(panel)
    if code == 4:
        return _rotate_ccw(panel)
    # The selected executable authority also defines these two branches even
    # though canonical examples and ordinary generation use codes 1..4.
    if code == 5:
        return _flip_lr(panel)
    if code == 6:
        return _flip_ud(panel)
    return [list(row) for row in panel]


def _extract_panels(grid: list[list[int]]) -> list[list[list[int]]]:
    return [
        [list(row[left : left + 5]) for row in grid[:5]]
        for left in _PANEL_STARTS
    ]


def _extract_codes(grid: list[list[int]]) -> tuple[int, int, int]:
    codes = []
    for left in _PANEL_STARTS:
        values = [value for value in grid[6][left : left + 5] if value != 0]
        if not values:
            codes.append(0)
        else:
            codes.append(values[0])
    return tuple(codes)  # type: ignore[return-value]


def _overlay_from_transformed(
    panels: list[list[list[int]]],
    codes: tuple[int, int, int],
    *,
    code_map: dict[int, int] | None = None,
    binary_only: bool = False,
) -> list[list[int]]:
    transformed = [
        _transform(panel, code_map.get(code, code) if code_map else code)
        for panel, code in zip(panels, codes)
    ]
    output = full_grid(5, 5, 0)
    for row in range(5):
        for col in range(5):
            count = sum(panel[row][col] != 0 for panel in transformed)
            if binary_only:
                output[row][col] = 2 if count else 0
            else:
                output[row][col] = {0: 0, 1: 2, 2: 4, 3: 8}[count]
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the selected Racket authority."""
    return _overlay_from_transformed(_extract_panels(grid), _extract_codes(grid))


def _ignore_code_row(grid: list[list[int]]) -> list[list[int]]:
    return _overlay_from_transformed(
        _extract_panels(grid), _extract_codes(grid), code_map={1: 1, 2: 1, 3: 1, 4: 1}
    )


def _swap_quarter_turns(grid: list[list[int]]) -> list[list[int]]:
    """Plausible rival: read code 2 as CCW and code 4 as CW."""
    return _overlay_from_transformed(
        _extract_panels(grid),
        _extract_codes(grid),
        code_map={1: 1, 2: 4, 3: 3, 4: 2},
    )


def _union_only(grid: list[list[int]]) -> list[list[int]]:
    """Plausible rival: transform correctly but discard overlap multiplicity."""
    return _overlay_from_transformed(
        _extract_panels(grid), _extract_codes(grid), binary_only=True
    )


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "ignore_code_row": _ignore_code_row,
    "swap_clockwise_counterclockwise": _swap_quarter_turns,
    "union_without_overlap_counts": _union_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# None of the retained rivals fits every canonical demonstration, so there is
# no canonical-only shortcut to declare here.
CANONICAL_SHORTCUTS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {}


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {min(cells)}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for dr, dc in _CARDINAL:
            nxt = (row + dr, col + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == cells


def _shape_grid(cells: set[tuple[int, int]]) -> list[list[int]]:
    grid = full_grid(5, 5, 0)
    for row, col in cells:
        grid[row][col] = 1
    return grid


def _shape_signature(cells: set[tuple[int, int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in _shape_grid(cells))


def _rotation_signatures(cells: set[tuple[int, int]]) -> set[tuple[tuple[int, ...], ...]]:
    grid = _shape_grid(cells)
    variants = (grid, _rotate_cw(grid), _rotate_180(grid), _rotate_ccw(grid))
    return {tuple(tuple(row) for row in variant) for variant in variants}


def _grow_shape(rng, size: int, *, wide: bool) -> set[tuple[int, int]]:
    """Grow a connected asymmetric template spanning canonical rows 1..3."""
    for _ in range(2000):
        if wide:
            cols = (0, 1, 2, 3) if rng.randrange(2) == 0 else (1, 2, 3, 4)
        else:
            cols = (1, 2, 3)
        allowed = {(row, col) for row in (1, 2, 3) for col in cols}
        start = (2, rng.choice(cols))
        cells = {start}
        while len(cells) < size:
            frontier = sorted(
                {
                    (row + dr, col + dc)
                    for row, col in cells
                    for dr, dc in _CARDINAL
                    if (row + dr, col + dc) in allowed
                    and (row + dr, col + dc) not in cells
                }
            )
            if not frontier:
                break
            cells.add(rng.choice(frontier))
        if len(cells) != size:
            continue
        if {row for row, _ in cells} != {1, 2, 3}:
            continue
        width = max(col for _, col in cells) - min(col for _, col in cells) + 1
        if not 2 <= width <= 4:
            continue
        if not _connected(cells):
            continue
        # Every code must be visually meaningful; reject rotationally symmetric
        # templates that would make one or more code branches unobservable.
        if len(_rotation_signatures(cells)) != 4:
            continue
        return cells
    raise ValueError(f"could not grow canonical-like template of size {size}")


def _grid_errors(grid: Any) -> list[str]:
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
        return ["grid cells must be integer ARC colors 0..9"]
    return []


def _panel_facts(grid: list[list[int]], panel_index: int) -> dict[str, Any]:
    left = _PANEL_STARTS[panel_index]
    values = [
        grid[row][left + col]
        for row in range(5)
        for col in range(5)
        if grid[row][left + col] != 0
    ]
    cells = {
        (row, col)
        for row in range(5)
        for col in range(5)
        if grid[row][left + col] != 0
    }
    return {
        "cells": cells,
        "size": len(cells),
        "colors": set(values),
        "connected": _connected(cells),
        "rows": {row for row, _ in cells},
        "width": (
            max(col for _, col in cells) - min(col for _, col in cells) + 1
            if cells
            else 0
        ),
    }


def observe_overrides(grid) -> dict[str, int]:
    """Recover each exact override axis from a returned grid."""
    errors = _grid_errors(grid)
    if errors or len(grid) != 7 or len(grid[0]) != 17:
        return {}
    return {
        f"panel{panel_index}_cells": _panel_facts(grid, panel_index)["size"]
        for panel_index in range(3)
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical task grammar, not merely the outer dimensions."""
    errors = _grid_errors(grid)
    if errors:
        return errors
    source = [list(row) for row in grid]
    if len(source) != 7 or len(source[0]) != 17:
        return [f"expected 7x17 grid; got {len(source)}x{len(source[0])}"]

    if any(source[5]):
        errors.append("separator row 5 must be blank")
    for separator in (5, 11):
        if any(source[row][separator] != 0 for row in range(7)):
            errors.append(f"separator column {separator} must be blank")

    panel_colors: list[int] = []
    panel_facts = []
    for panel_index in range(3):
        facts = _panel_facts(source, panel_index)
        panel_facts.append(facts)
        if not 5 <= facts["size"] <= 8:
            errors.append(
                f"panel {panel_index} must contain 5-8 cells, found {facts['size']}"
            )
        if len(facts["colors"]) != 1:
            errors.append(
                f"panel {panel_index} must use exactly one non-background color"
            )
        else:
            panel_colors.append(next(iter(facts["colors"])))
        if not facts["connected"]:
            errors.append(f"panel {panel_index} template must be 4-connected")
        if facts["rows"] != {1, 2, 3}:
            errors.append(f"panel {panel_index} template must span rows 1..3")
        if not 2 <= facts["width"] <= 4:
            errors.append(f"panel {panel_index} template width must be 2..4")
    if len(panel_colors) == 3 and len(set(panel_colors)) != 3:
        errors.append("the three panel colors must be distinct")

    codes: list[int] = []
    for panel_index, left in enumerate(_PANEL_STARTS):
        block = source[6][left : left + 5]
        nonzero = [value for value in block if value != 0]
        if len(nonzero) != 1:
            errors.append(
                f"panel {panel_index} code block must contain exactly one code"
            )
            continue
        code = nonzero[0]
        codes.append(code)
        if code not in (1, 2, 3, 4):
            errors.append(f"panel {panel_index} code must be in 1..4, found {code}")
    if len(codes) == 3 and len(set(codes)) != 3:
        errors.append("the three transform codes must be distinct")

    if isinstance(meta, dict) and not errors:
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            for panel_index, axis in enumerate(AXES):
                if axis in requested and requested[axis] is not None:
                    observed = panel_facts[panel_index]["size"]
                    if requested[axis] != observed:
                        errors.append(
                            f"override {axis}={requested[axis]!r} realized as {observed!r}"
                        )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked strict grammar covering canonical inputs and ordinary draws."""
    return self_check(grid)


def semantic_observables(grid) -> dict[str, Any]:
    errors = self_check(grid)
    if errors:
        return {"errors": errors}
    output = rule_mirror(grid)
    palette = {value for row in output for value in row}
    codes = _extract_codes(grid)
    return {
        "errors": [],
        "codes": codes,
        "panel_sizes": tuple(_panel_facts(grid, i)["size"] for i in range(3)),
        "output_palette": palette,
        "has_all_counts": {2, 4, 8} <= palette,
        "ignore_code_differs": _ignore_code_row(grid) != output,
        "quarter_turn_swap_differs": _swap_quarter_turns(grid) != output,
    }


def _code_present(code: int):
    return lambda grid: not self_check(grid) and code in _extract_codes(grid)


def _all_count_colors(grid) -> bool:
    return bool(semantic_observables(grid).get("has_all_counts"))


def _codes_matter(grid) -> bool:
    return bool(semantic_observables(grid).get("ignore_code_differs"))


def _turn_direction_matters(grid) -> bool:
    return bool(semantic_observables(grid).get("quarter_turn_swap_differs"))


SEMANTIC_WITNESSES = {
    "code_1_identity_branch": _code_present(1),
    "code_2_clockwise_branch": _code_present(2),
    "code_3_half_turn_branch": _code_present(3),
    "code_4_counterclockwise_branch": _code_present(4),
    "single_double_triple_overlap": _all_count_colors,
    "code_row_changes_result": _codes_matter,
    "quarter_turn_direction_changes_result": _turn_direction_matters,
}
BRANCH_WITNESSES = {
    "code_1_identity_branch",
    "code_2_clockwise_branch",
    "code_3_half_turn_branch",
    "code_4_counterclockwise_branch",
}
WITNESS_RIVALS = {
    "single_double_triple_overlap": ["union_without_overlap_counts"],
    "code_row_changes_result": ["ignore_code_row"],
    "quarter_turn_direction_changes_result": ["swap_clockwise_counterclockwise"],
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Return the code omitted by this example; all four occur per window."""
    del seed, difficulty
    return ({1, 2, 3, 4} - set(_CODE_SCHEDULE[int(sample_index) % 4])).pop()


SCHEDULE_PROFILES = (1, 2, 3, 4)


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    validated = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        malformed = self_check(pair["input"])
        if malformed:
            reasons.append(f"demo {index} malformed: {malformed[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with selected authority")
            continue
        validated.append(pair)

    malformed_query = self_check(query["input"])
    if malformed_query:
        reasons.append(f"query malformed: {malformed_query[0]}")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with selected authority")

    if reasons or len(validated) != len(demos):
        return reasons
    seen_codes = {
        code for pair in validated for code in _extract_codes(pair["input"])
    }
    missing_codes = sorted({1, 2, 3, 4} - seen_codes)
    if missing_codes:
        reasons.append(f"demonstrations do not cover transform code(s): {missing_codes}")
    if not all(_all_count_colors(pair["input"]) for pair in validated):
        reasons.append("not every demonstration exposes single, double, and triple overlap")
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in validated):
            reasons.append(f"named rival survives all demonstrations: {name}")
    return reasons


def _draw_panel_size(ctx, label: str, difficulty) -> int:
    """Use difficulty-specific defaults while preserving the full override domain."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, 5, 8)
    if difficulty == "easy":
        return ctx.draw_int(label, 5, 6)
    if difficulty == "hard":
        return ctx.draw_int(label, 7, 8)
    return ctx.draw_int(label, 5, 8)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    sizes = tuple(
        _draw_panel_size(ctx, f"panel{i}_cells", difficulty) for i in range(3)
    )
    rng = ctx.draw_rng("layout")
    colors = tuple(rng.sample(_PANEL_COLORS, 3))
    codes = _CODE_SCHEDULE[int(sample_index) % len(_CODE_SCHEDULE)]

    # Canonical training pair 2 contains one 3x4 template; reproduce that rare
    # support without letting every panel sprawl across the full 5x5 frame.
    wide_panel = 0 if int(sample_index) % 4 == 2 else None

    for _attempt in range(3000):
        shapes = [
            _grow_shape(rng, size, wide=(panel_index == wide_panel))
            for panel_index, size in enumerate(sizes)
        ]
        if len({_shape_signature(shape) for shape in shapes}) != 3:
            continue

        grid = full_grid(7, 17, 0)
        for panel_index, (left, color, shape) in enumerate(
            zip(_PANEL_STARTS, colors, shapes)
        ):
            del panel_index
            for row, col in shape:
                grid[row][left + col] = color
        for left, code in zip(_PANEL_STARTS, codes):
            grid[6][left + 2] = code

        if self_check(grid):
            continue
        output = rule_mirror(grid)
        palette = {value for row in output for value in row}
        if not {2, 4, 8} <= palette:
            continue
        if any(rival(grid) == output for rival in LESSON_COMPETITORS.values()):
            continue
        return grid
    raise ValueError("could not realize a decisive canonical-like template lesson")
