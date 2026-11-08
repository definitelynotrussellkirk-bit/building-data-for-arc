"""Generator for arc_puzzle_bank_21_set5_e:medium_e03 — mark enclosed zeros.

Treat every nonzero input cell as a wall, regardless of color or connected
component.  The answer is a fresh zero grid with color 8 at every zero cell
that cannot reach the input border through 4-connected zero cells.

The four-slot schedule retains the original area signatures and canonical-size
anchor, but non-anchor profiles now include L, T, and S-shaped zero regions.
Cooperative cages omit corner walls: diagonal contact with outside zeros is
not an escape path under the authoritative 4-neighbor rule. Open U decoys,
multiple holes, all palettes, and exact override observability are retained.

Profile names are compatibility identifiers for hole AREAS, not promises of
rectangular geometry. Every four consecutive ordinary draws expose both the
rectangular-hole shortcut and the incorrect 8-neighbor connectivity rule.
Every draw also has a small border-connected zero region, distinguishing true
enclosure from a shortcut that merely paints all zero components of area <=4.
"""
from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "36343a80035c"
TASK_ID = "36343a80035c"
VERSION = "3.1.1"
RULE_HASH = "933f8b2b4c4f"

SUMMARY = (
    "A zero-background grid contains colored wall components. Treat all "
    "nonzero cells together as walls, find every 4-connected zero region that "
    "does not touch the grid border, and output a fresh zero grid with exactly "
    "those enclosed cells colored 8. Wall colors and component membership do "
    "not matter; multiple components may cooperate to enclose one region."
)

INVARIANTS = [
    "background is color 0 and all other values are ARC colors 1..9",
    "at least one zero region is enclosed by the union of all nonzero walls",
    "at least one zero region remains connected to the grid border",
    "ordinary draws contain two enclosed regions, including a multi-component enclosure",
    "ordinary draws contain an open bbox decoy that must not appear in the answer",
    "every ordinary draw distinguishes 4-neighbor from 8-neighbor zero connectivity",
    "each non-anchor profile contains a nonrectangular hole",
    "every ordinary draw contains a border-connected zero region of area at most four",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.10

SCENE_PROFILES = (
    "unit_plus_tall2",
    "wide2_plus_tall3",
    "unit_plus_tall4",
    "square4_plus_tall2",
)
PALETTE_KINDS = ("canonical", "broad", "cyan_wall")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 9..14 with canonical anchors",
        "valid": "9..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 9..14 with canonical anchors",
        "valid": "9..14",
    },
    "scene_profile": {
        "type": "enum",
        "default": "four-slot hole-area schedule; non-anchor geometry is nonrectangular",
        "valid": "|".join(SCENE_PROFILES),
    },
    "palette_kind": {
        "type": "enum",
        "default": "four-slot canonical|cyan_wall|broad schedule",
        "valid": "|".join(PALETTE_KINDS),
    },
}

# Every declared exact-axis boundary combination is supported.  The explicit
# empty declaration opts the override checker into strict rejection accounting.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_PROFILE_SCHEDULE = SCENE_PROFILES
_PALETTE_SCHEDULE = ("canonical", "cyan_wall", "broad", "canonical")
_PALETTES = {
    "canonical": (3, 5, 7),
    "broad": (1, 2, 6),
    "cyan_wall": (4, 8, 9),
}
_PROFILE_HOLE_AREAS = {
    "unit_plus_tall2": (1, 2),
    "wide2_plus_tall3": (2, 3),
    "unit_plus_tall4": (1, 4),
    "square4_plus_tall2": (2, 4),
}
_PROFILE_SHAPES = {
    # frame height, frame width, cooperative-cage interior height
    "unit_plus_tall2": (3, 3, 2),
    "wide2_plus_tall3": (3, 4, 3),
    "unit_plus_tall4": (3, 3, 4),
    "square4_plus_tall2": (4, 4, 2),
}
# Compact polyominoes fit inside a 5x4 motif, including its wall boundary.
# Sampling all three nonrectangular tetrominoes varies topology-related geometry
# without rejection loops, resizing, or silent reinterpretation of exact axes.
_BENT_TRIOMINO = ((0, 0), (1, 0), (1, 1))
_BENT_TETROMINOES = (
    ((0, 0), (1, 0), (2, 0), (2, 1)),  # L
    ((0, 0), (1, 0), (2, 0), (1, 1)),  # T, rotated to fit a narrow motif
    ((0, 0), (1, 0), (1, 1), (2, 1)),  # S
)
_CANONICAL_DIMS = {
    "easy": (9, 9),
    "medium": (9, 10),
    "hard": (9, 10),
}
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

Grid = list[list[int]]
Cell = tuple[int, int]
Region = set[Cell]


def _copy_grid(grid: Grid) -> Grid:
    return [list(row) for row in grid]


def _valid_grid_shape(grid: Any) -> tuple[int, int] | None:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return None
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return None
    return len(grid), width


def _zero_regions(grid: Grid) -> list[Region]:
    """Return 4-connected zero regions in row-major discovery order."""
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    regions: list[Region] = []
    for r in range(height):
        for c in range(width):
            if grid[r][c] != 0 or (r, c) in seen:
                continue
            region: Region = set()
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                rr, cc = queue.popleft()
                region.add((rr, cc))
                for dr, dc in _DIR4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            regions.append(region)
    return regions


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
    """Return same-color 4-connected nonzero components."""
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    result: list[dict[str, Any]] = []
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            cells: set[Cell] = set()
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                rr, cc = queue.popleft()
                cells.add((rr, cc))
                for dr, dc in _DIR4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            result.append(
                {
                    "color": color,
                    "cells": cells,
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return result


def _true_output(grid: Grid) -> Grid:
    output = full_grid(len(grid), len(grid[0]), 0)
    for region in _hole_regions(grid):
        for r, c in region:
            output[r][c] = 8
    return output


def _paint_regions(grid: Grid, regions: Iterable[Iterable[Cell]]) -> Grid:
    output = full_grid(len(grid), len(grid[0]), 0)
    for region in regions:
        for r, c in region:
            output[r][c] = 8
    return output


def _bbox_interior_output(grid: Grid) -> Grid:
    """Rival: paint every zero strictly inside each component bbox."""
    cells: set[Cell] = set()
    for component in _same_color_components(grid):
        r0, c0, r1, c1 = component["bbox"]
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                if grid[r][c] == 0:
                    cells.add((r, c))
    return _paint_regions(grid, [cells])


def _rect_frame_output(grid: Grid) -> Grid:
    """Rival: only complete one-component rectangular frames make holes."""
    cells: set[Cell] = set()
    for component in _same_color_components(grid):
        r0, c0, r1, c1 = component["bbox"]
        perimeter = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        if component["cells"] != perimeter:
            continue
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                if grid[r][c] == 0:
                    cells.add((r, c))
    return _paint_regions(grid, [cells])


def _same_color_vertical_sandwich_output(grid: Grid) -> Grid:
    """Canonical-fitting rival: the same wall color above and below."""
    height, width = len(grid), len(grid[0])
    cells = {
        (r, c)
        for r in range(1, height - 1)
        for c in range(width)
        if (
            grid[r][c] == 0
            and grid[r - 1][c] != 0
            and grid[r - 1][c] == grid[r + 1][c]
        )
    }
    return _paint_regions(grid, [cells])


def _largest_hole_output(grid: Grid) -> Grid:
    holes = _hole_regions(grid)
    if not holes:
        return full_grid(len(grid), len(grid[0]), 0)
    return _paint_regions(grid, [max(holes, key=lambda region: (len(region), sorted(region)))])


def _one_cell_per_hole_output(grid: Grid) -> Grid:
    return _paint_regions(grid, [[min(region)] for region in _hole_regions(grid)])


def _global_bbox_output(grid: Grid) -> Grid:
    walls = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    if not walls:
        return full_grid(len(grid), len(grid[0]), 0)
    rows = [r for r, _ in walls]
    cols = [c for _, c in walls]
    r0, c0, r1, c1 = min(rows), min(cols), max(rows), max(cols)
    cells = {
        (r, c)
        for r in range(r0 + 1, r1)
        for c in range(c0 + 1, c1)
        if grid[r][c] == 0
    }
    return _paint_regions(grid, [cells])


def _copy_cyan_output(grid: Grid) -> Grid:
    cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    }
    return _paint_regions(grid, [cells])


def _is_rectangular(region: Region) -> bool:
    rows, cols = zip(*region)
    return len(region) == (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def _rectangular_holes_output(grid: Grid) -> Grid:
    """Canonical-fitting rival: discard any nonrectangular enclosed region."""
    return _paint_regions(grid, [r for r in _hole_regions(grid) if _is_rectangular(r)])


def _hole_bounding_boxes_output(grid: Grid) -> Grid:
    """Canonical-fitting rival: replace each hole with its full bounding box."""
    boxes = []
    for region in _hole_regions(grid):
        rows, cols = zip(*region)
        boxes.append({(r, c) for r in range(min(rows), max(rows) + 1)
                      for c in range(min(cols), max(cols) + 1)})
    return _paint_regions(grid, boxes)


def _eight_neighbor_holes_output(grid: Grid) -> Grid:
    """Wrong rival: allow diagonal zero-cell steps on the way to the border."""
    height, width = len(grid), len(grid[0])
    outside = {(r, c) for r in range(height) for c in range(width)
               if grid[r][c] == 0
               and (r in (0, height - 1) or c in (0, width - 1))}
    pending = list(outside)
    while pending:
        r, c = pending.pop()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                if (0 <= nr < height and 0 <= nc < width
                        and grid[nr][nc] == 0 and (nr, nc) not in outside):
                    outside.add((nr, nc))
                    pending.append((nr, nc))
    return _paint_regions(grid, [{(r, c) for r in range(height) for c in range(width)
                                 if grid[r][c] == 0 and (r, c) not in outside}])


def _identity(grid: Grid) -> Grid:
    return _copy_grid(grid)


def _small_zero_regions_output(grid: Grid) -> Grid:
    """Wrong rival: classify by size and ignore contact with the border."""
    return _paint_regions(grid, [region for region in _zero_regions(grid) if len(region) <= 4])


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "component_bbox_interiors": _bbox_interior_output,
    "rectangular_frames_only": _rect_frame_output,
    "same_color_vertical_sandwich": _same_color_vertical_sandwich_output,
    "largest_hole_only": _largest_hole_output,
    "one_cell_per_hole": _one_cell_per_hole_output,
    "global_wall_bbox": _global_bbox_output,
    "copy_input_cyan": _copy_cyan_output,
    "identity": _identity,
    "rectangular_holes_only": _rectangular_holes_output,
    "hole_bounding_boxes": _hole_bounding_boxes_output,
    "eight_neighbor_holes": _eight_neighbor_holes_output,
    "small_zero_regions": _small_zero_regions_output,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS

# This shortcut fits every official demonstration and query because every
# canonical hole is one cell tall.  The generated tall cooperative cages are
# the decisive discriminator.
CANONICAL_SHORTCUTS = {
    "same_color_vertical_sandwich": _same_color_vertical_sandwich_output,
    "rectangular_holes_only": _rectangular_holes_output,
    "hole_bounding_boxes": _hole_bounding_boxes_output,
}
# Area-1/area-2 canonical anchors cannot distinguish these two rivals; the
# non-anchor demonstrations must do so. Do not require impossible per-grid kills.
ANCHOR_COMPATIBLE_RIVALS = frozenset({"rectangular_holes_only", "hole_bounding_boxes"})
# Opt into the existing smoke gate's independent Racket/mirror parity check.
rule_mirror = _true_output


def _profile_from_grid(grid: Grid) -> str:
    signature = tuple(sorted(len(region) for region in _hole_regions(grid)))
    for profile, expected in _PROFILE_HOLE_AREAS.items():
        if signature == tuple(sorted(expected)):
            return profile
    return "unclassified"


def observe_overrides(grid: Grid) -> dict[str, Any]:
    """Recover every exact non-dimension axis from the returned grid."""
    colors = {value for row in grid for value in row if value != 0}
    palette_kind = "mixed_or_invalid"
    for name, palette in _PALETTES.items():
        if colors == set(palette):
            palette_kind = name
            break
    return {
        "scene_profile": _profile_from_grid(grid),
        "palette_kind": palette_kind,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-level wall/enclosure grammar."""
    del difficulty, meta
    shape = _valid_grid_shape(grid)
    if shape is None:
        return ["empty, non-list, or ragged grid"]
    height, width = shape
    errors: list[str] = []
    if height > 30 or width > 30:
        errors.append(f"grid exceeds ARC limit: {height}x{width}")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
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
    holes = _hole_regions(grid)
    if not holes:
        errors.append("no enclosed zero region")
    if not _outside_zero_cells(grid):
        errors.append("no border-connected zero background region")
    return errors


def strict_canonical_like(grid: Grid) -> list[str]:
    """Accept canonical pairs and narrow generated canonical-scale anchors."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    dims = (len(grid), len(grid[0]))
    if dims not in {(9, 9), (9, 10)}:
        reasons.append(f"dimensions {dims} are outside canonical 9x9/9x10 scale")
    colors = {value for row in grid for value in row if value != 0}
    if not 2 <= len(colors) <= 3:
        reasons.append(f"canonical inputs use 2-3 nonzero colors, found {len(colors)}")
    holes = _hole_regions(grid)
    if not 2 <= len(holes) <= 3:
        reasons.append(f"canonical inputs contain 2-3 hole regions, found {len(holes)}")
    if any(len(region) > 3 for region in holes):
        reasons.append("canonical hole regions have area at most 3")
    return reasons


def _component_labels(grid: Grid) -> dict[Cell, int]:
    labels: dict[Cell, int] = {}
    for index, component in enumerate(_same_color_components(grid)):
        for cell in component["cells"]:
            labels[cell] = index
    return labels


def _hole_boundary_components(grid: Grid, region: Region) -> set[int]:
    labels = _component_labels(grid)
    result: set[int] = set()
    for r, c in region:
        for dr, dc in _DIR4:
            cell = (r + dr, c + dc)
            if cell in labels:
                result.add(labels[cell])
    return result


def _witness_multiple_holes(grid: Grid) -> bool:
    return not self_check(grid) and len(_hole_regions(grid)) >= 2


def _witness_multi_cell_hole(grid: Grid) -> bool:
    return not self_check(grid) and any(len(region) >= 2 for region in _hole_regions(grid))


def _witness_composite_enclosure(grid: Grid) -> bool:
    return not self_check(grid) and any(
        len(_hole_boundary_components(grid, region)) >= 2
        for region in _hole_regions(grid)
    )


def _witness_open_bbox_decoy(grid: Grid) -> bool:
    if self_check(grid):
        return False
    outside = _outside_zero_cells(grid)
    for component in _same_color_components(grid):
        r0, c0, r1, c1 = component["bbox"]
        if any(
            (r, c) in outside
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
        ):
            return True
    return False


def _witness_cyan_wall(grid: Grid) -> bool:
    return not self_check(grid) and any(value == 8 for row in grid for value in row)


def _profile_witness(profile: str) -> Callable[[Grid], bool]:
    return lambda grid: not self_check(grid) and _profile_from_grid(grid) == profile


def _witness_nonrectangular_hole(grid: Grid) -> bool:
    return not self_check(grid) and any(not _is_rectangular(r) for r in _hole_regions(grid))


def _witness_diagonal_leak(grid: Grid) -> bool:
    return not self_check(grid) and _eight_neighbor_holes_output(grid) != _true_output(grid)


def _has_small_border_region(grid: Grid) -> bool:
    height, width = len(grid), len(grid[0])
    return any(len(region) <= 4 and _touches_border(region, height, width)
               for region in _zero_regions(grid))


def _witness_small_border_region(grid: Grid) -> bool:
    return not self_check(grid) and _has_small_border_region(grid)


SEMANTIC_WITNESSES = {
    "multiple_holes": _witness_multiple_holes,
    "multi_cell_hole": _witness_multi_cell_hole,
    "cooperative_multi_component_enclosure": _witness_composite_enclosure,
    "open_bbox_decoy": _witness_open_bbox_decoy,
    "cyan_wall_distractor": _witness_cyan_wall,
    "nonrectangular_hole": _witness_nonrectangular_hole,
    "diagonal_is_not_an_escape": _witness_diagonal_leak,
    "small_border_region_is_not_a_hole": _witness_small_border_region,
    **{f"profile_{name}": _profile_witness(name) for name in SCENE_PROFILES},
}

WITNESS_RIVALS = {
    "multiple_holes": ["largest_hole_only"],
    "multi_cell_hole": ["one_cell_per_hole", "same_color_vertical_sandwich"],
    "cooperative_multi_component_enclosure": [
        "component_bbox_interiors",
        "rectangular_frames_only",
    ],
    "open_bbox_decoy": ["component_bbox_interiors", "global_wall_bbox"],
    "cyan_wall_distractor": ["copy_input_cyan", "identity"],
    "nonrectangular_hole": ["rectangular_holes_only", "hole_bounding_boxes"],
    "diagonal_is_not_an_escape": ["eight_neighbor_holes"],
    "small_border_region_is_not_a_hole": ["small_zero_regions"],
    **{
        f"profile_{name}": ["same_color_vertical_sandwich", "component_bbox_interiors"]
        for name in SCENE_PROFILES
    },
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named rival survives demos but changes query."""
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
        outputs = {name: function(grid) for name, function in candidates.items()}
        if outputs["true"] != official:
            reasons.append(f"demo {index} output disagrees with the audit mirror")
            continue
        survivors &= {name for name, output in outputs.items() if output == official}

    query_grid = query.get("input")
    query_answer = query.get("output")
    input_errors = self_check(query_grid)
    if input_errors:
        reasons.append(f"query input is outside grammar: {input_errors}")
        return reasons
    query_outputs = {
        name: function(query_grid) for name, function in candidates.items()
    }
    if query_outputs["true"] != query_answer:
        reasons.append("query output disagrees with the audit mirror")
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
    for c in range(left, right + 1):
        grid[top][c] = color
        grid[bottom][c] = color
    for r in range(top, bottom + 1):
        grid[r][left] = color
        grid[r][right] = color


def _draw_cooperative_cage(
    grid: Grid,
    top: int,
    left: int,
    interior_height: int,
    left_color: int,
    right_color: int,
) -> None:
    """Draw a 3-wide 4-connected enclosure with deliberately absent corners."""
    bottom = top + interior_height + 1
    right = left + 2
    for r in range(top + 1, bottom):
        grid[r][left] = left_color
        grid[r][right] = right_color
    grid[top][left + 1] = left_color
    grid[bottom][left + 1] = right_color


def _draw_open_u(grid: Grid, color: int) -> None:
    """Draw a connected U with bbox-interior zeros open to the outside."""
    top, bottom, left, right = 6, 8, 0, 4
    for r in range(top, bottom + 1):
        grid[r][left] = color
        grid[r][right] = color
    for c in range(left, right + 1):
        grid[bottom][c] = color


def _draw_polyomino_hole(
    grid: Grid, top: int, left: int, cells: Iterable[Cell],
    left_color: int, right_color: int,
) -> None:
    """Surround only cardinal neighbors; unused corner cells stay outside.

    The bounded shape tables keep a full zero corridor between motifs. Wall
    colors split the boundary, so enclosure is a property of their union.
    """
    region = {(top + 1 + r, left + 1 + c) for r, c in cells}
    boundary = {(r + dr, c + dc) for r, c in region for dr, dc in _DIR4} - region
    for r, c in sorted(boundary):
        grid[r][c] = left_color if c <= left + 1 else right_color


def _base_scene(profile: str, colors: tuple[int, int, int], shape_index: int = 0) -> Grid:
    frame_h, frame_w, cage_inner_h = _PROFILE_SHAPES[profile]
    frame_color, left_color, right_color = colors
    grid = full_grid(9, 9, 0)
    if profile == "square4_plus_tall2":
        _draw_polyomino_hole(grid, 0, 0, _BENT_TETROMINOES[shape_index],
                            frame_color, frame_color)
    else:
        _draw_frame(grid, 0, 0, frame_h, frame_w, frame_color)
    if cage_inner_h == 2:
        _draw_cooperative_cage(grid, 0, 6, cage_inner_h, left_color, right_color)
    else:
        shape = _BENT_TRIOMINO if cage_inner_h == 3 else _BENT_TETROMINOES[shape_index]
        _draw_polyomino_hole(grid, 0, 5, shape, left_color, right_color)
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
    for r, row in enumerate(base):
        for c, value in enumerate(row):
            grid[top + r][left + c] = value
    return grid


def _ensure_small_border_region(grid: Grid, color: int, rng) -> None:
    """Add a border singleton only when the size-only rival lacks a witness.

    The base scene leaves a 4x4 corner empty. D4 and zero padding preserve an
    empty inward 3x3 at a physical corner. The two added walls are on the grid
    border, isolated from existing walls; they separate only the corner zero,
    which still touches the border. All enclosed cells and their output stay
    unchanged. This must run after embedding so the new region stays exterior.
    """
    if _has_small_border_region(grid):
        return
    height, width = len(grid), len(grid[0])
    corners = ((0, 0, 1, 1), (0, width - 1, 1, -1),
               (height - 1, 0, -1, 1), (height - 1, width - 1, -1, -1))
    available = [(r, c, dr, dc) for r, c, dr, dc in corners
                 if all(grid[r + dr * i][c + dc * j] == 0
                        for i in range(3) for j in range(3))]
    if not available:
        raise RuntimeError("no empty physical corner for the small-border-region witness")
    r, c, dr, dc = available[rng.randrange(len(available))]
    grid[r + dr][c] = color
    grid[r][c + dc] = color


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
        return ctx.draw_int(label, 9, 14)
    if anchor is not None:
        return ctx.draw_int(label, anchor, anchor)
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

    anchor_dims = _CANONICAL_DIMS.get(difficulty) if slot == 0 else None
    if slot == 0 and anchor_dims is None:
        anchor_dims = ((9, 9), (9, 10))[ctx.draw_rng("canonical_dims").randrange(2)]
    if difficulty == "easy":
        default_h = (9, 10)
        default_w = (9, 10)
    elif difficulty == "hard":
        default_h = (10, 14)
        default_w = (10, 14)
    else:
        default_h = (9, 12)
        default_w = (9, 12)
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
    _ensure_small_border_region(grid, colors[0], ctx.draw_rng("border_zero_decoy"))

    errors = self_check(grid)
    if errors:
        raise RuntimeError("generator constructed invalid grid: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {"scene_profile": profile, "palette_kind": palette_kind}
    if observed != expected:
        raise RuntimeError(
            f"axis realization mismatch: expected {expected}, observed {observed}"
        )
    return grid
