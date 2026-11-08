"""Generator for e46763527c42 — overlay two fragments at red connectors.

The input has two separated, color-blind 4-connected fragments.  Each fragment
contains exactly one red (2) connector.  Rank the fragments by connector
position, translate the second fragment until its connector coincides with the
first connector, and paint the aligned union in color 6 (magenta) on a fresh canvas.

Ordinary examples deliberately make connector alignment distinguishable from
bounding-box alignment, in-place recoloring, using only one fragment, and
filling the aligned bounding box.  The public axes are intentionally small and
fully recoverable from the returned grid; size, orientation, colors, and exact
placement remain lawful hidden variation rather than dishonest metadata.
"""
from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e46763527c42"
TASK_ID = "e46763527c42"
VERSION = "4.0.0"
RULE_HASH = "3aba9759872c"

SUMMARY = (
    "Two separated 4-connected fragments each contain one red(2) connector. "
    "Sort the fragments by connector position, translate the second so its "
    "connector lands on the first, and paint the aligned union in color 6 (magenta) on a "
    "fresh same-size zero canvas. Ordinary draws use canonical canvas sizes "
    "and partial overlaps that refute one-fragment, bbox-alignment, solid-bbox, "
    "and in-place-recolor shortcuts."
)

EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "rectangular grid with values in 0..9",
    "exactly two color-blind 4-connected nonzero fragments",
    "each fragment has exactly one red(2) connector and at least one body cell",
    "connector-aligning the second fragment onto the first stays in bounds",
    "after alignment each fragment contributes at least one exclusive cell",
]

_CANVAS_PROFILES = {
    "7x11": (7, 11),
    "8x11": (8, 11),
    "9x12": (9, 12),
}
_CONNECTOR_RELATIONS = ("same_row", "below_left", "below_right")

AXES = {
    "canvas_profile": {
        "type": "str",
        "default": "keyed canonical-scale profile",
        "valid": "7x11|8x11|9x12",
    },
    "connector_relation": {
        "type": "str",
        "default": "keyed relative input placement",
        "valid": "same_row|below_left|below_right",
    },
    "overlap_cells": {
        "type": "int",
        "default": "keyed partial aligned overlap",
        "valid": "1..3",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
_ALLOWED_OVERRIDES = frozenset(AXES)

Cell = tuple[int, int]
Cells = frozenset[Cell]
Grid = list[list[int]]

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_BODY_COLORS = (1, 3, 4, 5, 6, 7, 8, 9)

# Every shape is connector-relative, with the connector at (0, 0).  For each
# requested overlap, sizes 4..6 extend the same decisive morphology.  The pairs
# were chosen so that all eight D4 orientations retain the requested overlap,
# both fragments contribute, and connector alignment differs from aligning bbox
# top-left corners.
_TEMPLATE_PAIRS: dict[int, dict[int, tuple[Cells, Cells]]] = {
    1: {
        4: (
            frozenset({(0, 0), (0, 1), (1, 0), (2, 0)}),
            frozenset({(0, 0), (0, -1), (-1, 0), (-1, -1)}),
        ),
        5: (
            frozenset({(0, 0), (0, 1), (1, 0), (2, 0), (2, 1)}),
            frozenset({(0, 0), (0, -1), (-1, 0), (-1, -1), (-2, -1)}),
        ),
        6: (
            frozenset({(0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2)}),
            frozenset(
                {(0, 0), (0, -1), (-1, 0), (-1, -1), (-2, -1), (-2, 0)}
            ),
        ),
    },
    2: {
        4: (
            frozenset({(0, 0), (0, 1), (1, 0), (1, 1)}),
            frozenset({(0, 0), (0, 1), (-1, 0), (-1, -1)}),
        ),
        5: (
            frozenset({(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)}),
            frozenset({(0, 0), (0, 1), (-1, 0), (-1, -1), (-2, -1)}),
        ),
        6: (
            frozenset({(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)}),
            frozenset(
                {(0, 0), (0, 1), (-1, 0), (-1, -1), (-2, -1), (-2, 0)}
            ),
        ),
    },
    3: {
        4: (
            frozenset({(-2, -1), (-1, -1), (-1, 0), (0, 0)}),
            frozenset({(-1, -1), (-1, 0), (0, 0), (1, 0)}),
        ),
        5: (
            frozenset({(-2, -1), (-2, 0), (-1, -1), (-1, 0), (0, 0)}),
            frozenset({(-1, -1), (-1, 0), (0, -1), (0, 0), (1, 0)}),
        ),
        6: (
            frozenset(
                {(-2, -1), (-2, 0), (-2, 1), (-1, -1), (-1, 0), (0, 0)}
            ),
            frozenset(
                {(-1, -1), (-1, 0), (0, -1), (0, 0), (0, 1), (1, 0)}
            ),
        ),
    },
}


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override key(s): {unknown}")


def _transform_cell(cell: Cell, transform: int) -> Cell:
    """Apply one of eight connector-preserving D4 transforms."""
    row, col = cell
    if transform >= 4:
        col = -col
        transform -= 4
    for _ in range(transform):
        row, col = col, -row
    return row, col


def _transform(cells: Cells, transform: int) -> Cells:
    return frozenset(_transform_cell(cell, transform) for cell in cells)


def _absolute(cells: Cells, connector: Cell) -> Cells:
    return frozenset(
        (connector[0] + row, connector[1] + col) for row, col in cells
    )


def _fits(cells: Cells, connector: Cell, height: int, width: int) -> bool:
    return all(
        0 <= connector[0] + row < height
        and 0 <= connector[1] + col < width
        for row, col in cells
    )


def _has_blank_moat(first: Cells, second: Cells) -> bool:
    return all(
        max(abs(arow - brow), abs(acol - bcol)) > 1
        for arow, acol in first
        for brow, bcol in second
    )


def _relation(first: Cell, second: Cell) -> str | None:
    if second[0] == first[0] and second[1] > first[1]:
        return "same_row"
    if second[0] > first[0] and second[1] < first[1]:
        return "below_left"
    if second[0] > first[0] and second[1] > first[1]:
        return "below_right"
    return None


@lru_cache(maxsize=None)
def _placement_candidates(
    height: int,
    width: int,
    first_shape: tuple[Cell, ...],
    second_shape: tuple[Cell, ...],
    relation: str,
) -> tuple[tuple[Cell, Cell], ...]:
    """Enumerate separated input placements with an in-bounds aligned output."""
    first = frozenset(first_shape)
    second = frozenset(second_shape)
    candidates: list[tuple[Cell, Cell]] = []
    for first_row in range(height):
        for first_col in range(width):
            first_connector = (first_row, first_col)
            if not _fits(first, first_connector, height, width):
                continue
            # The output anchors both connector-relative shapes here.
            if not _fits(second, first_connector, height, width):
                continue
            first_absolute = _absolute(first, first_connector)
            for second_row in range(height):
                for second_col in range(width):
                    second_connector = (second_row, second_col)
                    if _relation(first_connector, second_connector) != relation:
                        continue
                    if not _fits(second, second_connector, height, width):
                        continue
                    second_absolute = _absolute(second, second_connector)
                    if _has_blank_moat(first_absolute, second_absolute):
                        candidates.append((first_connector, second_connector))
    return tuple(candidates)


def _shape_sizes(difficulty: Any) -> tuple[int, ...]:
    if difficulty == "easy":
        return (4,)
    if difficulty == "hard":
        return (4, 5, 6)
    return (4, 5)


def _build_valid(ctx) -> Grid:
    profile = ctx.draw_choice("canvas_profile", tuple(_CANVAS_PROFILES))
    relation = ctx.draw_choice("connector_relation", _CONNECTOR_RELATIONS)
    overlap = ctx.draw_int("overlap_cells", 1, 3)
    height, width = _CANVAS_PROFILES[profile]

    morphology_rng = ctx.draw_rng("morphology")
    size = morphology_rng.choice(_shape_sizes(ctx.difficulty))
    transform = morphology_rng.randrange(8)
    role_swap = bool(morphology_rng.randrange(2))

    first, second = _TEMPLATE_PAIRS[overlap][size]
    first = _transform(first, transform)
    second = _transform(second, transform)
    if role_swap:
        first, second = second, first

    first_tuple = tuple(sorted(first))
    second_tuple = tuple(sorted(second))
    candidates = _placement_candidates(
        height,
        width,
        first_tuple,
        second_tuple,
        relation,
    )
    if not candidates:
        raise AssertionError(
            "template library has no placement for "
            f"{profile}/{relation}/overlap={overlap}/size={size}/t={transform}"
        )
    placement_rng = ctx.draw_rng("placement")
    first_connector, second_connector = placement_rng.choice(candidates)

    color_rng = ctx.draw_rng("body_colors")
    first_color, second_color = color_rng.sample(_BODY_COLORS, 2)
    grid = full_grid(height, width, 0)
    for row, col in _absolute(first, first_connector):
        grid[row][col] = 2 if (row, col) == first_connector else first_color
    for row, col in _absolute(second, second_connector):
        grid[row][col] = 2 if (row, col) == second_connector else second_color

    expected = {
        "canvas_profile": profile,
        "connector_relation": relation,
        "overlap_cells": overlap,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise AssertionError(f"constructed axes drifted: expected {expected}, got {observed}")
    errors = strict_canonical_like(grid)
    if errors:
        raise AssertionError("constructed invalid scene: " + "; ".join(errors))
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic connector-overlay input."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    return _build_valid(ctx)


def _coerce_grid(grid: Any) -> tuple[Grid | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty row sequence"]
    rows: Grid = []
    width: int | None = None
    for row_index, raw_row in enumerate(grid):
        if not isinstance(raw_row, (list, tuple)) or not raw_row:
            return None, [f"row {row_index} must be a nonempty sequence"]
        row = list(raw_row)
        if width is None:
            width = len(row)
        elif len(row) != width:
            return None, ["grid must be rectangular"]
        if any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value <= 9
            for value in row
        ):
            return None, ["grid values must be integer colors in 0..9"]
        rows.append(row)
    return rows, []


def _components4(grid: Grid) -> list[Cells]:
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[Cells] = []
    for row in range(height):
        for col in range(width):
            start = (row, col)
            if grid[row][col] == 0 or start in seen:
                continue
            queue = [start]
            seen.add(start)
            cells: set[Cell] = set()
            while queue:
                current = queue.pop()
                cells.add(current)
                for delta_row, delta_col in _CARDINAL:
                    neighbor = (
                        current[0] + delta_row,
                        current[1] + delta_col,
                    )
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and grid[neighbor[0]][neighbor[1]] != 0
                        and neighbor not in seen
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            components.append(frozenset(cells))
    return components


def _ordered_records(grid: Grid) -> tuple[list[dict[str, Any]], list[str]]:
    components = _components4(grid)
    if len(components) != 2:
        return [], [f"expected exactly two nonzero components, found {len(components)}"]
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, cells in enumerate(components):
        connectors = sorted(cell for cell in cells if grid[cell[0]][cell[1]] == 2)
        if len(connectors) != 1:
            errors.append(
                f"component {index} must have exactly one red connector, "
                f"found {len(connectors)}"
            )
            continue
        body = cells - {connectors[0]}
        if not body:
            errors.append(f"component {index} must contain a non-connector body cell")
            continue
        records.append(
            {
                "cells": cells,
                "connector": connectors[0],
                "body": frozenset(body),
                "body_colors": frozenset(grid[row][col] for row, col in body),
            }
        )
    if errors:
        return [], errors
    records.sort(key=lambda record: record["connector"])
    return records, []


def _aligned_geometry(
    grid: Grid,
) -> tuple[list[dict[str, Any]], Cells, Cells, Cells, list[str]]:
    records, errors = _ordered_records(grid)
    if errors:
        return [], frozenset(), frozenset(), frozenset(), errors
    first, second = records
    delta_row = first["connector"][0] - second["connector"][0]
    delta_col = first["connector"][1] - second["connector"][1]
    translated_second = frozenset(
        (row + delta_row, col + delta_col) for row, col in second["cells"]
    )
    height, width = len(grid), len(grid[0])
    if any(
        not (0 <= row < height and 0 <= col < width)
        for row, col in translated_second
    ):
        errors.append("connector-aligned second fragment leaves the canvas")
    first_cells = first["cells"]
    union = frozenset(first_cells | translated_second)
    if not (first_cells - translated_second):
        errors.append("first fragment contributes no exclusive aligned cell")
    if not (translated_second - first_cells):
        errors.append("second fragment contributes no exclusive aligned cell")
    return records, first_cells, translated_second, union, errors


def _paint_color6(height: int, width: int, cells: Cells, *, clip: bool = False) -> Grid:
    output = full_grid(height, width, 0)
    for row, col in cells:
        if 0 <= row < height and 0 <= col < width:
            output[row][col] = 6
        elif not clip:
            raise ValueError(f"output cell {(row, col)} is out of bounds")
    return output


def rule_mirror(grid: Any) -> Grid:
    """Python mirror of the selected Racket connector-overlay authority."""
    coerced, errors = _coerce_grid(grid)
    if errors or coerced is None:
        raise ValueError("invalid grid: " + "; ".join(errors))
    _, _, _, union, geometry_errors = _aligned_geometry(coerced)
    if geometry_errors:
        raise ValueError("invalid connector scene: " + "; ".join(geometry_errors))
    return _paint_color6(len(coerced), len(coerced[0]), union)


_solve_grid = rule_mirror


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the broad structural input grammar consumed by the authority."""
    del difficulty, meta
    coerced, errors = _coerce_grid(grid)
    if errors or coerced is None:
        return errors
    _, _, _, _, geometry_errors = _aligned_geometry(coerced)
    return geometry_errors


def _bbox(cells: Cells) -> tuple[int, int, int, int]:
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _overlap_count(grid: Grid) -> int | None:
    _, first, second, _, errors = _aligned_geometry(grid)
    if errors:
        return None
    return len(first & second)


def observe_overrides(grid) -> dict[str, str | int | None]:
    """Recover every declared exact axis from the returned grid."""
    coerced, errors = _coerce_grid(grid)
    if errors or coerced is None:
        return {
            "canvas_profile": None,
            "connector_relation": None,
            "overlap_cells": None,
        }
    records, record_errors = _ordered_records(coerced)
    relation = None
    if not record_errors:
        relation = _relation(records[0]["connector"], records[1]["connector"])
    return {
        "canvas_profile": f"{len(coerced)}x{len(coerced[0])}",
        "connector_relation": relation,
        "overlap_cells": _overlap_count(coerced),
    }


def _fragments_have_blank_moat(records: list[dict[str, Any]]) -> bool:
    return _has_blank_moat(records[0]["cells"], records[1]["cells"])


def _bbox_alignment_output(grid: Any) -> Grid:
    coerced, errors = _coerce_grid(grid)
    if errors or coerced is None:
        raise ValueError("invalid grid: " + "; ".join(errors))
    records, record_errors = _ordered_records(coerced)
    if record_errors:
        raise ValueError("invalid connector scene: " + "; ".join(record_errors))
    first, second = records
    first_box = _bbox(first["cells"])
    second_box = _bbox(second["cells"])
    delta_row = first_box[0] - second_box[0]
    delta_col = first_box[1] - second_box[1]
    moved = frozenset(
        (row + delta_row, col + delta_col) for row, col in second["cells"]
    )
    return _paint_color6(
        len(coerced),
        len(coerced[0]),
        frozenset(first["cells"] | moved),
        clip=True,
    )


def _first_fragment_only(grid: Any) -> Grid:
    coerced, errors = _coerce_grid(grid)
    if errors or coerced is None:
        raise ValueError("invalid grid: " + "; ".join(errors))
    records, record_errors = _ordered_records(coerced)
    if record_errors:
        raise ValueError("invalid connector scene: " + "; ".join(record_errors))
    return _paint_color6(len(coerced), len(coerced[0]), records[0]["cells"])


def _aligned_second_only(grid: Any) -> Grid:
    coerced, errors = _coerce_grid(grid)
    if errors or coerced is None:
        raise ValueError("invalid grid: " + "; ".join(errors))
    _, _, second, _, geometry_errors = _aligned_geometry(coerced)
    if geometry_errors:
        raise ValueError("invalid connector scene: " + "; ".join(geometry_errors))
    return _paint_color6(len(coerced), len(coerced[0]), second)


def _solid_aligned_bbox(grid: Any) -> Grid:
    coerced, errors = _coerce_grid(grid)
    if errors or coerced is None:
        raise ValueError("invalid grid: " + "; ".join(errors))
    _, _, _, union, geometry_errors = _aligned_geometry(coerced)
    if geometry_errors:
        raise ValueError("invalid connector scene: " + "; ".join(geometry_errors))
    top, left, bottom, right = _bbox(union)
    cells = frozenset(
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
    )
    return _paint_color6(len(coerced), len(coerced[0]), cells)


def _recolor_in_place(grid: Any) -> Grid:
    coerced, errors = _coerce_grid(grid)
    if errors or coerced is None:
        raise ValueError("invalid grid: " + "; ".join(errors))
    cells = frozenset(
        (row, col)
        for row in range(len(coerced))
        for col in range(len(coerced[0]))
        if coerced[row][col] != 0
    )
    return _paint_color6(len(coerced), len(coerced[0]), cells)


SEMANTIC_RIVALS: dict[str, Callable[[Any], Grid]] = {
    "use only the first fragment": _first_fragment_only,
    "use only the aligned second fragment": _aligned_second_only,
    "align fragment bounding-box corners": _bbox_alignment_output,
    "fill the aligned union bounding box": _solid_aligned_bbox,
    "recolor both fragments in their input positions": _recolor_in_place,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _valid_scene(grid: Any) -> bool:
    return not self_check(grid)


def _both_fragments_contribute(grid: Any) -> bool:
    coerced, errors = _coerce_grid(grid)
    if errors or coerced is None:
        return False
    _, first, second, _, geometry_errors = _aligned_geometry(coerced)
    return not geometry_errors and bool(first - second) and bool(second - first)


def _not_bbox_alignment(grid: Any) -> bool:
    if not _valid_scene(grid):
        return False
    return _bbox_alignment_output(grid) != rule_mirror(grid)


def _not_in_place_recolor(grid: Any) -> bool:
    if not _valid_scene(grid):
        return False
    return _recolor_in_place(grid) != rule_mirror(grid)


def _non_solid_overlay(grid: Any) -> bool:
    if not _valid_scene(grid):
        return False
    return _solid_aligned_bbox(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "both_fragments_contribute": _both_fragments_contribute,
    "connector_alignment_differs_from_bbox_alignment": _not_bbox_alignment,
    "alignment_differs_from_in_place_recolor": _not_in_place_recolor,
    "aligned_union_is_not_a_solid_bbox": _non_solid_overlay,
}

WITNESS_RIVALS = {
    "both_fragments_contribute": [
        "use only the first fragment",
        "use only the aligned second fragment",
    ],
    "connector_alignment_differs_from_bbox_alignment": [
        "align fragment bounding-box corners"
    ],
    "alignment_differs_from_in_place_recolor": [
        "recolor both fragments in their input positions"
    ],
    "aligned_union_is_not_a_solid_bbox": [
        "fill the aligned union bounding box"
    ],
}


def strict_canonical_like(grid) -> list[str]:
    """Validate the canonical-scale curriculum manifold used by ordinary draws."""
    errors = self_check(grid)
    if errors:
        return errors
    coerced, _ = _coerce_grid(grid)
    assert coerced is not None
    strict_errors: list[str] = []
    profile = f"{len(coerced)}x{len(coerced[0])}"
    if profile not in _CANVAS_PROFILES:
        strict_errors.append(f"canvas profile {profile} is outside canonical support")

    records, record_errors = _ordered_records(coerced)
    if record_errors:
        return record_errors
    if any(not 4 <= len(record["cells"]) <= 6 for record in records):
        strict_errors.append("fragment sizes must be in 4..6")
    if any(len(record["body_colors"]) != 1 for record in records):
        strict_errors.append("each fragment body must use one uniform color")
    elif records[0]["body_colors"] == records[1]["body_colors"]:
        strict_errors.append("the two fragment body colors must be distinct")
    if len({value for row in coerced for value in row}) != 4:
        strict_errors.append("strict scenes must use exactly four colors including zero")
    if not _fragments_have_blank_moat(records):
        strict_errors.append("strict input fragments require a one-cell blank moat")

    relation = _relation(records[0]["connector"], records[1]["connector"])
    if relation not in _CONNECTOR_RELATIONS:
        strict_errors.append("connector relation is outside the declared curriculum")
    overlap = _overlap_count(coerced)
    if overlap not in (1, 2, 3):
        strict_errors.append("aligned overlap must contain 1..3 cells")
    if not _not_bbox_alignment(coerced):
        strict_errors.append("bbox-corner alignment is answer-equivalent")
    if not _not_in_place_recolor(coerced):
        strict_errors.append("in-place recoloring is answer-equivalent")
    return strict_errors


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose visible demonstrations leave a named rival viable."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:
            reasons.append(f"pair {index} is outside the connector grammar: {exc}")
            continue
        if pair["output"] != expected:
            reasons.append(f"pair {index} output disagrees with connector alignment")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(pair["input"]) == pair["output"] for pair in demos
            )
        except Exception as exc:
            reasons.append(f"rival {name!r} raised: {type(exc).__name__}: {exc}")
            continue
        if survives:
            reasons.append(f"demonstrations do not refute rival: {name}")
    return reasons


def mutation_fixtures() -> list[tuple[str, Grid]]:
    """Task-linked malformed scenes that the structural checker must reject."""
    base = generate(73, 4, difficulty="medium")
    records, errors = _ordered_records(base)
    if errors:
        raise AssertionError("fixture source unexpectedly invalid")

    missing_connector = [row[:] for row in base]
    connector = records[0]["connector"]
    replacement = next(iter(records[0]["body_colors"]))
    missing_connector[connector[0]][connector[1]] = replacement

    duplicate_connector = [row[:] for row in base]
    body_cell = sorted(records[0]["body"])[0]
    duplicate_connector[body_cell[0]][body_cell[1]] = 2

    single_component = [row[:] for row in base]
    for row, col in records[1]["cells"]:
        single_component[row][col] = 0

    third_component = [row[:] for row in base]
    occupied = frozenset(records[0]["cells"] | records[1]["cells"])
    added = False
    for row in range(len(base)):
        for col in range(len(base[0])):
            if (row, col) in occupied:
                continue
            if all(
                abs(row - other_row) + abs(col - other_col) > 1
                for other_row, other_col in occupied
            ):
                third_component[row][col] = 9
                added = True
                break
        if added:
            break
    if not added:
        raise AssertionError("could not place third-component fixture")

    clipped_overlay = full_grid(6, 9, 0)
    for row, col, color in (
        (0, 1, 2),
        (0, 2, 4),
        (1, 2, 4),
        (5, 6, 2),
        (4, 6, 3),
        (3, 6, 3),
    ):
        clipped_overlay[row][col] = color

    return [
        ("missing_connector", missing_connector),
        ("duplicate_connector", duplicate_connector),
        ("single_component", single_component),
        ("third_component", third_component),
        ("clipped_overlay", clipped_overlay),
    ]
