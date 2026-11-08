"""Topology curriculum for ``Fill Enclosed Holes`` (c2fb0e01a539).

The selected Racket authority is unchanged: copy the input and replace every
4-connected zero component that does not touch the grid border with color 7.
Border-connected zeros and all nonzero cells remain exactly as they were.

A four-slot schedule teaches more than hollow rectangles.  Every ordinary draw
contains two holes, an open bounding-box decoy, a mixed-color enclosure, and a
corner-gap contrast where diagonal contact is *not* an escape path.  Three slots
also contain a nonrectangular hole.  Therefore each four-demonstration lesson,
and each one-query rotation of its five materialized pairs, contains redundant
counterexamples to the canonical-fitting rectangle and 8-neighbor shortcuts.
"""
from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c2fb0e01a539"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "8efc6e86f888"

SUMMARY = (
    "Preserve the input grid and fill with color 7 every 4-connected zero "
    "region that cannot reach the outer border. Border-connected zeros stay 0; "
    "wall color, wall component identity, and hole shape do not matter."
)

INVARIANTS = [
    "every input has at least one enclosed zero region and border-connected zero background",
    "ordinary draws contain two enclosed regions, including a multi-cell hole",
    "ordinary draws contain an open component bounding-box decoy that stays zero",
    "ordinary draws contain a hole enclosed cooperatively by multiple colored components",
    "ordinary draws distinguish 4-neighbor from 8-neighbor zero connectivity",
    "the input never uses reserved fill color 7; every nonzero input cell is preserved",
    "three of four schedule profiles contain a nonrectangular hole",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

SCENE_PROFILES = (
    "unit_plus_tall2",
    "wide2_plus_bent3",
    "unit_plus_bent4",
    "bent4_plus_tall2",
)
SCHEDULE_PROFILES = SCENE_PROFILES
PALETTE_KINDS = ("canonical", "broad")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 9..14 with a 9x11 canonical anchor",
        "valid": "9..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 9..14 with a 9x11 canonical anchor",
        "valid": "9..14",
    },
    "scene_profile": {
        "type": "enum",
        "default": "four-slot deterministic topology schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
    "palette_kind": {
        "type": "enum",
        "default": "alternating canonical|broad schedule",
        "valid": "|".join(PALETTE_KINDS),
    },
}

# Every declared exact-axis combination is constructive at both boundaries and
# in every difficulty band.  The empty declaration opts into strict accounting.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_PROFILE_SCHEDULE = SCENE_PROFILES
_PALETTE_SCHEDULE = ("canonical", "broad", "canonical", "broad")
_PALETTES = {
    # Three nonzero colors keep the slot-0 9x11 draw on an exact canonical
    # (height, width, palette-size) profile.  Color 7 is reserved for output.
    "canonical": (2, 4, 6),
    "broad": (1, 8, 9),
}
_PROFILE_HOLE_AREAS = {
    "unit_plus_tall2": (1, 2),
    "wide2_plus_bent3": (2, 3),
    "unit_plus_bent4": (1, 4),
    "bent4_plus_tall2": (2, 4),
}
_PROFILE_SHAPES = {
    # first frame height, first frame width, second motif hole area
    "unit_plus_tall2": (3, 3, 2),
    "wide2_plus_bent3": (3, 4, 3),
    "unit_plus_bent4": (3, 3, 4),
    "bent4_plus_tall2": (0, 0, 2),
}
_BENT_TRIOMINO = ((0, 0), (1, 0), (1, 1))
_BENT_TETROMINOES = (
    ((0, 0), (1, 0), (2, 0), (2, 1)),  # L
    ((0, 0), (1, 0), (2, 0), (1, 1)),  # T in a narrow bbox
    ((0, 0), (1, 0), (1, 1), (2, 1)),  # S
)
_CANONICAL_DIMS = {(8, 10), (9, 9), (9, 11), (10, 11), (10, 12)}
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIR8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)

Grid = list[list[int]]
Cell = tuple[int, int]
Region = set[Cell]


def _copy_grid(grid: Grid) -> Grid:
    return [list(row) for row in grid]


def _valid_grid_shape(grid: Any) -> tuple[int, int] | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return None
    return len(grid), width


def _zero_regions_with_dirs(
    grid: Grid, directions: tuple[tuple[int, int], ...]
) -> list[Region]:
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    result: list[Region] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0 or (row, col) in seen:
                continue
            region: Region = set()
            pending = deque([(row, col)])
            seen.add((row, col))
            while pending:
                current = pending.popleft()
                region.add(current)
                cr, cc = current
                for dr, dc in directions:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            result.append(region)
    return result


def _zero_regions(grid: Grid) -> list[Region]:
    return _zero_regions_with_dirs(grid, _DIR4)


def _touches_border(region: Iterable[Cell], height: int, width: int) -> bool:
    return any(r in (0, height - 1) or c in (0, width - 1) for r, c in region)


def _hole_regions(grid: Grid) -> list[Region]:
    height, width = len(grid), len(grid[0])
    return [
        region
        for region in _zero_regions(grid)
        if not _touches_border(region, height, width)
    ]


def _outside_zero_cells(grid: Grid) -> set[Cell]:
    height, width = len(grid), len(grid[0])
    outside: set[Cell] = set()
    for region in _zero_regions(grid):
        if _touches_border(region, height, width):
            outside.update(region)
    return outside


def _same_color_components(grid: Grid) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            cells: set[Cell] = set()
            pending = deque([(row, col)])
            seen.add((row, col))
            while pending:
                cr, cc = pending.popleft()
                cells.add((cr, cc))
                for dr, dc in _DIR4:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            components.append(
                {
                    "color": color,
                    "cells": cells,
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return components


def _component_labels(grid: Grid) -> dict[Cell, int]:
    labels: dict[Cell, int] = {}
    for index, component in enumerate(_same_color_components(grid)):
        for cell in component["cells"]:
            labels[cell] = index
    return labels


def _hole_boundary_components(grid: Grid, region: Region) -> set[int]:
    labels = _component_labels(grid)
    result: set[int] = set()
    for row, col in region:
        for dr, dc in _DIR4:
            adjacent = (row + dr, col + dc)
            if adjacent in labels:
                result.add(labels[adjacent])
    return result


def _paint_regions(
    grid: Grid, regions: Iterable[Iterable[Cell]], color: int = 7
) -> Grid:
    output = _copy_grid(grid)
    for region in regions:
        for row, col in region:
            output[row][col] = color
    return output


def _true_output(grid: Grid) -> Grid:
    return _paint_regions(grid, _hole_regions(grid), 7)


# ---------------------------------------------------------------------------
# Plausible wrong rules used by the semantic gate and lesson census.
# ---------------------------------------------------------------------------


def _fill_all_zeros(grid: Grid) -> Grid:
    return _paint_regions(
        grid,
        [[(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 0]],
    )


def _fill_with_boundary_color(grid: Grid) -> Grid:
    output = _copy_grid(grid)
    height, width = len(grid), len(grid[0])
    for region in _hole_regions(grid):
        colors = {
            grid[r + dr][c + dc]
            for r, c in region
            for dr, dc in _DIR4
            if 0 <= r + dr < height
            and 0 <= c + dc < width
            and grid[r + dr][c + dc] != 0
        }
        color = min(colors) if colors else 7
        for row, col in region:
            output[row][col] = color
    return output


def _largest_hole_output(grid: Grid) -> Grid:
    holes = _hole_regions(grid)
    if not holes:
        return _copy_grid(grid)
    return _paint_regions(grid, [max(holes, key=lambda region: (len(region), sorted(region)))])


def _one_cell_per_hole_output(grid: Grid) -> Grid:
    return _paint_regions(grid, [[min(region)] for region in _hole_regions(grid)])


def _component_bbox_interiors_output(grid: Grid) -> Grid:
    cells: set[Cell] = set()
    for component in _same_color_components(grid):
        row0, col0, row1, col1 = component["bbox"]
        for row in range(row0 + 1, row1):
            for col in range(col0 + 1, col1):
                if grid[row][col] == 0:
                    cells.add((row, col))
    return _paint_regions(grid, [cells])


def _rectangular_frames_only_output(grid: Grid) -> Grid:
    cells: set[Cell] = set()
    for component in _same_color_components(grid):
        row0, col0, row1, col1 = component["bbox"]
        if row1 - row0 < 2 or col1 - col0 < 2:
            continue
        perimeter = {
            (row, col)
            for row in range(row0, row1 + 1)
            for col in range(col0, col1 + 1)
            if row in (row0, row1) or col in (col0, col1)
        }
        if component["cells"] != perimeter:
            continue
        cells.update(
            (row, col)
            for row in range(row0 + 1, row1)
            for col in range(col0 + 1, col1)
            if grid[row][col] == 0
        )
    return _paint_regions(grid, [cells])


def _same_component_enclosures_output(grid: Grid) -> Grid:
    return _paint_regions(
        grid,
        [
            region
            for region in _hole_regions(grid)
            if len(_hole_boundary_components(grid, region)) == 1
        ],
    )


def _global_wall_bbox_output(grid: Grid) -> Grid:
    walls = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    if not walls:
        return _copy_grid(grid)
    rows = [r for r, _ in walls]
    cols = [c for _, c in walls]
    row0, col0, row1, col1 = min(rows), min(cols), max(rows), max(cols)
    cells = {
        (row, col)
        for row in range(row0 + 1, row1)
        for col in range(col0 + 1, col1)
        if grid[row][col] == 0
    }
    return _paint_regions(grid, [cells])


def _identity(grid: Grid) -> Grid:
    return _copy_grid(grid)


def _is_rectangular(region: Region) -> bool:
    rows, cols = zip(*region)
    return len(region) == (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def _rectangular_holes_only_output(grid: Grid) -> Grid:
    return _paint_regions(
        grid, [region for region in _hole_regions(grid) if _is_rectangular(region)]
    )


def _hole_bounding_boxes_output(grid: Grid) -> Grid:
    boxes: list[set[Cell]] = []
    for region in _hole_regions(grid):
        rows, cols = zip(*region)
        boxes.append(
            {
                (row, col)
                for row in range(min(rows), max(rows) + 1)
                for col in range(min(cols), max(cols) + 1)
            }
        )
    return _paint_regions(grid, boxes)


def _eight_neighbor_holes_output(grid: Grid) -> Grid:
    height, width = len(grid), len(grid[0])
    holes = [
        region
        for region in _zero_regions_with_dirs(grid, _DIR8)
        if not _touches_border(region, height, width)
    ]
    return _paint_regions(grid, holes)


def _fresh_hole_mask_output(grid: Grid) -> Grid:
    output = full_grid(len(grid), len(grid[0]), 0)
    for region in _hole_regions(grid):
        for row, col in region:
            output[row][col] = 7
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "fill_all_zeros": _fill_all_zeros,
    "fill_with_boundary_color": _fill_with_boundary_color,
    "largest_hole_only": _largest_hole_output,
    "one_cell_per_hole": _one_cell_per_hole_output,
    "component_bbox_interiors": _component_bbox_interiors_output,
    "rectangular_frames_only": _rectangular_frames_only_output,
    "same_component_enclosures": _same_component_enclosures_output,
    "global_wall_bbox": _global_wall_bbox_output,
    "identity": _identity,
    "rectangular_holes_only": _rectangular_holes_only_output,
    "hole_bounding_boxes": _hole_bounding_boxes_output,
    "eight_neighbor_holes": _eight_neighbor_holes_output,
    "fresh_hole_mask": _fresh_hole_mask_output,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS

# These wrong rules fit every official pair. Generated mixed-component,
# nonrectangular, and corner-gap witnesses must refute them in each lesson.
CANONICAL_SHORTCUTS = {
    "component_bbox_interiors": _component_bbox_interiors_output,
    "rectangular_frames_only": _rectangular_frames_only_output,
    "same_component_enclosures": _same_component_enclosures_output,
    "rectangular_holes_only": _rectangular_holes_only_output,
    "hole_bounding_boxes": _hole_bounding_boxes_output,
    "eight_neighbor_holes": _eight_neighbor_holes_output,
}

# Opt into the battery's independent Racket/mirror parity check.
rule_mirror = _true_output


def _profile_from_grid(grid: Grid) -> str:
    signature = tuple(sorted(len(region) for region in _hole_regions(grid)))
    for profile, expected in _PROFILE_HOLE_AREAS.items():
        if signature == tuple(sorted(expected)):
            return profile
    return "unclassified"


def observe_overrides(grid: Grid) -> dict[str, Any]:
    """Recover every exact axis from returned pixels, never RNG bookkeeping."""
    colors = {value for row in grid for value in row if value != 0}
    palette_kind = "mixed_or_invalid"
    for name, palette in _PALETTES.items():
        if colors == set(palette):
            palette_kind = name
            break
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "scene_profile": _profile_from_grid(grid),
        "palette_kind": palette_kind,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate authority-level lawful inputs without overfitting the sampler."""
    del difficulty, meta
    shape = _valid_grid_shape(grid)
    if shape is None:
        return ["expected a nonempty rectangular grid"]
    height, width = shape
    errors: list[str] = []
    if height > 30 or width > 30:
        errors.append(f"grid exceeds ARC limit: {height}x{width}")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid values must be integer ARC colors 0..9")
        return errors
    flat = [value for row in grid for value in row]
    if 0 not in flat:
        errors.append("background color 0 is absent")
    if not any(value != 0 for value in flat):
        errors.append("no nonzero wall cells")
    if not _hole_regions(grid):
        errors.append("no enclosed 4-connected zero region")
    if not _outside_zero_cells(grid):
        errors.append("no border-connected zero background region")
    return errors


def strict_canonical_like(grid: Grid) -> list[str]:
    """Accept all official inputs and the slot-0 canonical-profile anchor."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    dims = (len(grid), len(grid[0]))
    if dims not in _CANONICAL_DIMS:
        reasons.append(f"dimensions {dims} are outside the official profile set")
    colors = {value for row in grid for value in row if value != 0}
    if not 2 <= len(colors) <= 3:
        reasons.append(f"official inputs use 2-3 nonzero colors, found {len(colors)}")
    holes = _hole_regions(grid)
    if not 1 <= len(holes) <= 2:
        reasons.append(f"official inputs contain 1-2 holes, found {len(holes)}")
    if any(len(region) > 25 for region in holes):
        reasons.append("official hole areas are at most 25 cells")
    return reasons


# ---------------------------------------------------------------------------
# Executable semantic witnesses.
# ---------------------------------------------------------------------------


def _lawful(grid: Grid) -> bool:
    return not self_check(grid)


def _witness_multiple_holes(grid: Grid) -> bool:
    return _lawful(grid) and len(_hole_regions(grid)) >= 2


def _witness_multi_cell_hole(grid: Grid) -> bool:
    return _lawful(grid) and any(len(region) > 1 for region in _hole_regions(grid))


def _witness_composite_enclosure(grid: Grid) -> bool:
    return _lawful(grid) and any(
        len(_hole_boundary_components(grid, region)) >= 2
        for region in _hole_regions(grid)
    )


def _witness_open_bbox_decoy(grid: Grid) -> bool:
    return _lawful(grid) and _component_bbox_interiors_output(grid) != _true_output(grid)


def _witness_nonrectangular_hole(grid: Grid) -> bool:
    return _lawful(grid) and any(not _is_rectangular(region) for region in _hole_regions(grid))


def _witness_diagonal_leak(grid: Grid) -> bool:
    return _lawful(grid) and _eight_neighbor_holes_output(grid) != _true_output(grid)


def _witness_fixed_fill_seven(grid: Grid) -> bool:
    return _lawful(grid) and _fill_with_boundary_color(grid) != _true_output(grid)


def _witness_border_background(grid: Grid) -> bool:
    return _lawful(grid) and bool(_outside_zero_cells(grid))


SEMANTIC_WITNESSES = {
    "multiple_holes": _witness_multiple_holes,
    "multi_cell_hole": _witness_multi_cell_hole,
    "cooperative_multi_component_enclosure": _witness_composite_enclosure,
    "open_bbox_decoy": _witness_open_bbox_decoy,
    "nonrectangular_hole": _witness_nonrectangular_hole,
    "diagonal_is_not_an_escape": _witness_diagonal_leak,
    "fixed_fill_color_seven": _witness_fixed_fill_seven,
    "border_background_is_preserved": _witness_border_background,
}

WITNESS_RIVALS = {
    "multiple_holes": ["largest_hole_only"],
    "multi_cell_hole": ["one_cell_per_hole"],
    "cooperative_multi_component_enclosure": [
        "component_bbox_interiors",
        "rectangular_frames_only",
        "same_component_enclosures",
    ],
    "open_bbox_decoy": ["component_bbox_interiors", "global_wall_bbox"],
    "nonrectangular_hole": ["rectangular_holes_only", "hole_bounding_boxes"],
    "diagonal_is_not_an_escape": ["eight_neighbor_holes"],
    "fixed_fill_color_seven": ["fill_with_boundary_color"],
    "border_background_is_preserved": ["fill_all_zeros"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a declared rival fits demos but changes the query."""
    candidates: dict[str, Callable[[Grid], Grid]] = {
        "true": _true_output,
        **SEMANTIC_RIVALS,
    }
    survivors = set(candidates)
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        grid = demo.get("input")
        official = demo.get("output")
        input_errors = self_check(grid)
        if input_errors:
            reasons.append(f"demo {index} input is outside grammar: {input_errors}")
            continue
        outputs = {name: solve(grid) for name, solve in candidates.items()}
        if outputs["true"] != official:
            reasons.append(f"demo {index} output disagrees with the topology mirror")
            continue
        survivors &= {name for name, output in outputs.items() if output == official}

    query_grid = query.get("input")
    query_answer = query.get("output")
    input_errors = self_check(query_grid)
    if input_errors:
        reasons.append(f"query input is outside grammar: {input_errors}")
        return reasons
    query_outputs = {
        name: solve(query_grid) for name, solve in candidates.items()
    }
    if query_outputs["true"] != query_answer:
        reasons.append("query output disagrees with the topology mirror")
        return reasons
    for name in sorted(survivors - {"true"}):
        if query_outputs[name] != query_answer:
            reasons.append(
                f"competitor {name!r} fits every demo but changes the query answer"
            )
    return reasons


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return _PROFILE_SCHEDULE[sample_index % EXAMPLES_NEEDED]


# ---------------------------------------------------------------------------
# Constructive four-profile sampler.
# ---------------------------------------------------------------------------


def _draw_frame(
    grid: Grid,
    top: int,
    left: int,
    height: int,
    width: int,
    color: int,
) -> None:
    bottom = top + height - 1
    right = left + width - 1
    for col in range(left, right + 1):
        grid[top][col] = color
        grid[bottom][col] = color
    for row in range(top, bottom + 1):
        grid[row][left] = color
        grid[row][right] = color


def _draw_cooperative_cage(
    grid: Grid,
    top: int,
    left: int,
    interior_height: int,
    frame_color: int,
    left_color: int,
    right_color: int,
) -> None:
    """Draw one connected corner-gap wall plus two accent endpoints.

    The missing bottom-right corner is a diagonal zero escape under an
    8-neighbor interpretation but not under the selected 4-neighbor rule.  The
    remaining perimeter is a single path.  Recoloring its two endpoints gives
    a three-component cooperative enclosure without fragmenting the main wall.
    """
    bottom = top + interior_height + 1
    right = left + 2
    _draw_frame(grid, top, left, interior_height + 2, 3, frame_color)
    grid[bottom][right] = 0
    grid[bottom - 1][right] = left_color
    grid[bottom][right - 1] = right_color


def _draw_open_u(grid: Grid, color: int) -> None:
    """Draw an inverted U whose bbox interior opens through the bottom."""
    top, bottom, left, right = 6, 8, 0, 4
    for col in range(left, right + 1):
        grid[top][col] = color
    for row in range(top, bottom + 1):
        grid[row][left] = color
        grid[row][right] = color


def _draw_dense_polyomino_cavity(
    grid: Grid,
    top: int,
    left: int,
    cells: Iterable[Cell],
    frame_color: int,
    left_color: int,
    right_color: int,
) -> None:
    """Carve a nonrectangular cavity from one connected 5x4 wall block.

    A removed outer corner lies diagonally beside cavity cell (0,0), so the
    cavity is enclosed in 4-connectivity but border-connected in 8-connectivity.
    Two robust boundary cells are recolored as accent components; the remaining
    dense wall stays connected and keeps canonical-scale component mass.
    """
    for row in range(top, top + 5):
        for col in range(left, left + 4):
            grid[row][col] = frame_color
    for row, col in cells:
        grid[top + 1 + row][left + 1 + col] = 0
    grid[top][left] = 0
    grid[top][left + 1] = left_color
    grid[top + 1][left] = right_color


def _base_scene(
    profile: str, colors: tuple[int, int, int], shape_index: int = 0
) -> Grid:
    first_height, first_width, second_area = _PROFILE_SHAPES[profile]
    frame_color, left_color, right_color = colors
    grid = full_grid(9, 9, 0)

    if profile == "bent4_plus_tall2":
        _draw_dense_polyomino_cavity(
            grid,
            0,
            0,
            _BENT_TETROMINOES[shape_index],
            frame_color,
            frame_color,
            frame_color,
        )
    else:
        _draw_frame(grid, 0, 0, first_height, first_width, frame_color)
        # Join the first frame to the canonical-scale exterior backbone.
        for row in range(first_height, 6):
            grid[row][0] = frame_color

    if second_area == 2:
        _draw_cooperative_cage(
            grid, 0, 6, 2, frame_color, left_color, right_color
        )
        for row in range(4, 6):
            grid[row][6] = frame_color
    elif second_area == 3:
        _draw_dense_polyomino_cavity(
            grid, 0, 5, _BENT_TRIOMINO, frame_color, left_color, right_color
        )
    else:
        _draw_dense_polyomino_cavity(
            grid,
            0,
            5,
            _BENT_TETROMINOES[shape_index],
            frame_color,
            left_color,
            right_color,
        )

    # One exterior tree joins every main-color wall and the open decoy.  Since
    # the decoy opens downward, this backbone does not turn it into a hole.
    for col in range(9):
        grid[5][col] = frame_color
    _draw_open_u(grid, frame_color)
    return grid


def _rotate_cw(grid: Grid) -> Grid:
    return [list(row) for row in zip(*reversed(grid))]


def _flip_lr(grid: Grid) -> Grid:
    return [list(reversed(row)) for row in grid]


def _dihedral(grid: Grid, code: int) -> Grid:
    result = _copy_grid(grid)
    if code >= 4:
        result = _flip_lr(result)
        code -= 4
    for _ in range(code):
        result = _rotate_cw(result)
    return result


def _embed(base: Grid, height: int, width: int, rng) -> Grid:
    if len(base) > height or len(base[0]) > width:
        raise ValueError(f"9x9 scene does not fit requested grid {height}x{width}")
    top = rng.randint(0, height - len(base))
    left = rng.randint(0, width - len(base[0]))
    grid = full_grid(height, width, 0)
    for row, values in enumerate(base):
        for col, value in enumerate(values):
            grid[top + row][left + col] = value
    return grid


def _draw_axis_choice(ctx, label: str, options: tuple[Any, ...], default: Any) -> Any:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _draw_dimension(
    ctx,
    label: str,
    default_lo: int,
    default_hi: int,
    anchor: int | None,
) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, 9, 14)
    if anchor is not None:
        return ctx.draw_int_strict(label, anchor, anchor)
    return ctx.draw_int_diff(label, default_lo, default_hi)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = sample_index % EXAMPLES_NEEDED
    profile = _draw_axis_choice(
        ctx,
        "scene_profile",
        SCENE_PROFILES,
        _PROFILE_SCHEDULE[slot],
    )
    palette_kind = _draw_axis_choice(
        ctx,
        "palette_kind",
        PALETTE_KINDS,
        _PALETTE_SCHEDULE[slot],
    )

    # The first slot is an exact official profile in every band.  Other slots
    # retain difficulty-aware size variation; overrides always use the complete
    # declared domain rather than being clipped by a band.
    anchor_dims = (9, 11) if slot == 0 else None
    if difficulty == "easy":
        default_h, default_w = (9, 10), (9, 12)
    elif difficulty == "hard":
        default_h, default_w = (10, 14), (11, 14)
    elif difficulty == "medium":
        default_h, default_w = (9, 12), (10, 13)
    else:
        default_h, default_w = (9, 12), (9, 13)
    height = _draw_dimension(
        ctx,
        "grid_h",
        default_h[0],
        default_h[1],
        anchor_dims[0] if anchor_dims else None,
    )
    width = _draw_dimension(
        ctx,
        "grid_w",
        default_w[0],
        default_w[1],
        anchor_dims[1] if anchor_dims else None,
    )

    palette_rng = ctx.draw_rng("palette_permutation")
    colors = tuple(palette_rng.sample(list(_PALETTES[palette_kind]), 3))
    shape_index = ctx.draw_rng("hole_shape").randrange(len(_BENT_TETROMINOES))
    base = _base_scene(profile, colors, shape_index)
    layout_rng = ctx.draw_rng("layout")
    base = _dihedral(base, layout_rng.randrange(8))
    grid = _embed(base, height, width, layout_rng)

    errors = self_check(grid)
    if errors:
        raise RuntimeError("generator constructed invalid grid: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "scene_profile": profile,
        "palette_kind": palette_kind,
    }
    if observed != expected:
        raise RuntimeError(
            f"axis realization mismatch: expected {expected}, observed {observed}"
        )
    return grid
