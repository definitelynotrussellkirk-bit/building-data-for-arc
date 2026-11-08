"""Constructive curriculum for ``Transfer the hole pattern to the solid twin``.

The selected Racket rule finds a hollow monochromatic object, computes every
4-connected zero region enclosed by that object's bounding box, and carves the
same local cells out of one same-size solid object.  This sampler keeps the
canonical two-object grammar while making each ordinary draw a direct witness
against the two strongest canonical-fitting shortcuts:

* carve the solid's entire interior; and
* transfer only the largest enclosed region; and
* apply the transfer only when the solid target is the rightmost object.

A connected interior divider creates at least two holes while leaving some
interior cells colored.  Object roles alternate across samples, and three
demonstrations ensure that every one-query rotation includes both orientations.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bc932ac8117a"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "bcafd3a4dd95"

SUMMARY = (
    "A hollow framed object and a different-colored solid square have equal "
    "bounding-box size. Transfer every enclosed zero region of the hollow in "
    "local coordinates by carving those cells from the solid; preserve all "
    "other cells. Ordinary draws contain a connected divider that creates "
    "multiple holes and therefore refutes whole-interior and largest-hole-only "
    "shortcuts. Three-example lessons also refute a rightmost-target positional shortcut."
)

INVARIANTS = [
    "exactly two monochromatic 4-connected nonzero objects on background 0",
    "one complete framed square with at least two enclosed zero regions",
    "one same-size completely solid square in a different color",
    "the object boxes are horizontally separated by at least one zero column",
    "ordinary draws leave colored interior divider cells that must not be carved",
]

# Three demonstrations are required because a four-pair alternating episode
# retains both object orientations under every one-query holdout rotation.
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

PALETTE_KINDS = ("default", "warm", "cool", "varied")
HOLLOW_SIDES = ("left", "right")
HOLE_DIAGONALS = ("main", "anti")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "5..16; strongly favors canonical heights 5 and 6",
        "valid": "5..16",
    },
    "grid_w": {
        "type": "int",
        "default": "11..22; correlated canonical anchors 5x11, 5x12, 6x14",
        "valid": "11..22",
    },
    "box_size": {
        "type": "int",
        "default": "4|5",
        "valid": "4..5",
    },
    "palette_kind": {
        "type": "enum",
        "default": "uniform exact palette family",
        "valid": "default|warm|cool|varied",
    },
    "hollow_side": {
        "type": "enum",
        "default": "left|right",
        "valid": "left|right",
    },
    "hole_diagonal": {
        "type": "enum",
        "default": "main|anti divider orientation",
        "valid": "main|anti",
    },
}

# Every advertised cross-product is constructive, including 5x11 with size 5.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_PALETTES = {
    "default": (2, 3),
    "warm": (4, 6),
    "cool": (1, 8),
    "varied": (5, 9),
}
_PAIR_TO_PALETTE = {frozenset(pair): name for name, pair in _PALETTES.items()}
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

Grid = list[list[int]]
Cell = tuple[int, int]
Region = set[Cell]
Record = dict[str, Any]


def _copy_grid(grid: Iterable[Iterable[int]]) -> Grid:
    return [list(row) for row in grid]


def _pattern_cells(size: int, diagonal: str) -> set[Cell]:
    """Connected-to-frame divider cells in local bbox coordinates."""
    if size == 4:
        # Each diagonal cell touches the surrounding frame; the frame connects
        # them into one 4-connected object while the two remaining zeros are
        # distinct enclosed regions.
        base = {(1, 1), (2, 2)}
    elif size == 5:
        # A 4-connected staircase from the top frame to the bottom frame.
        base = {(1, 1), (2, 1), (2, 2), (3, 2)}
    else:
        raise ValueError(f"unsupported box_size: {size}")
    if diagonal == "anti":
        return {(row, size - 1 - col) for row, col in base}
    if diagonal != "main":
        raise ValueError(f"unsupported hole_diagonal: {diagonal!r}")
    return base


def _draw_frame(grid: Grid, top: int, left: int, size: int, color: int) -> None:
    bottom, right = top + size - 1, left + size - 1
    for col in range(left, right + 1):
        grid[top][col] = color
        grid[bottom][col] = color
    for row in range(top, bottom + 1):
        grid[row][left] = color
        grid[row][right] = color


def _fill_square(grid: Grid, top: int, left: int, size: int, color: int) -> None:
    for row in range(top, top + size):
        for col in range(left, left + size):
            grid[row][col] = color


def _draw_weighted_height(ctx, difficulty: Any) -> int:
    choices = list(range(5, 17)) + [5] * 64 + [6] * 32
    if difficulty == "easy":
        choices += list(range(5, 9)) * 4
    elif difficulty == "hard":
        choices += list(range(12, 17)) * 4
    elif difficulty == "medium":
        choices += list(range(8, 13)) * 3
    return ctx.draw_choice("grid_h", choices)


def _draw_weighted_width(ctx, height: int, difficulty: Any) -> int:
    choices = list(range(11, 23))
    if height == 5:
        choices += [11] * 56 + [12] * 56
    elif height == 6:
        choices += [14] * 96
    else:
        # Retain broad support even when the height is not a canonical anchor.
        choices += [11, 12, 14] * 4
    if difficulty == "easy":
        choices += list(range(11, 16)) * 2
    elif difficulty == "hard":
        choices += list(range(18, 23)) * 2
    return ctx.draw_choice("grid_w", choices)


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides) -> Grid:
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be an integer, not {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")

    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    for name in ("grid_h", "grid_w", "box_size"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
    for name in ("palette_kind", "hollow_side", "hole_diagonal"):
        value = overrides.get(name)
        if value is not None and type(value) is not str:
            raise TypeError(f"{name} must be a string, not {type(value).__name__}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    height = _draw_weighted_height(ctx, difficulty)
    width = _draw_weighted_width(ctx, height, difficulty)
    size = ctx.draw_choice("box_size", (4, 5))
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    if "hollow_side" in overrides:
        hollow_side = ctx.draw_choice("hollow_side", HOLLOW_SIDES)
    else:
        # Consecutive episode samples deliberately alternate object roles.  This
        # makes two-example lessons reject "always transform the first/leftmost
        # object" while preserving exact side overrides.
        hollow_side = ctx.draw_choice(
            "hollow_side", (HOLLOW_SIDES[sample_index % len(HOLLOW_SIDES)],)
        )
    diagonal = ctx.draw_choice("hole_diagonal", HOLE_DIAGONALS)

    # Both sizes fit every advertised canvas: 2*5 + one gap = 11 columns.
    max_gap = width - 2 * size
    if max_gap < 1 or height < size:
        raise RuntimeError("declared dimensions cannot fit the paired squares")
    gap = ctx.draw_rng("object_gap").randint(1, max_gap)
    span = 2 * size + gap
    start_col = ctx.draw_rng("pair_horizontal_offset").randint(0, width - span)
    left_col = start_col
    right_col = start_col + size + gap
    # Keep both twins on the same top row, matching every canonical pair.
    # Combined with deterministic side alternation, this makes raster order
    # alternate the transformed object rather than accidentally selecting the
    # solid as the topmost object in every demonstration.
    pair_top = ctx.draw_rng("pair_vertical_offset").randint(0, height - size)

    if hollow_side == "left":
        hollow_top, hollow_left = pair_top, left_col
        solid_top, solid_left = pair_top, right_col
    else:
        solid_top, solid_left = pair_top, left_col
        hollow_top, hollow_left = pair_top, right_col

    color_a, color_b = _PALETTES[palette_kind]
    if ctx.draw_rng("color_roles").randrange(2):
        color_a, color_b = color_b, color_a
    hollow_color, solid_color = color_a, color_b

    grid = full_grid(height, width, 0)
    _draw_frame(grid, hollow_top, hollow_left, size, hollow_color)
    for local_row, local_col in _pattern_cells(size, diagonal):
        grid[hollow_top + local_row][hollow_left + local_col] = hollow_color
    _fill_square(grid, solid_top, solid_left, size, solid_color)
    return grid


# ---------------------------------------------------------------------------
# Structural analysis and validation
# ---------------------------------------------------------------------------


def _shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be literal integer colors 0..9"]
    return []


def _components(grid: Grid) -> list[Record]:
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    records: list[Record] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            pending = deque([(row, col)])
            seen.add((row, col))
            cells: set[Cell] = set()
            while pending:
                current = pending.popleft()
                cells.add(current)
                cr, cc = current
                for dr, dc in _DIR4:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < height and 0 <= nc < width and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            records.append({
                "color": color,
                "cells": cells,
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
            })
    return records


def _enclosed_regions(record: Record) -> list[Region]:
    r0, c0, r1, c1 = record["bbox"]
    height, width = r1 - r0 + 1, c1 - c0 + 1
    occupied = {(r - r0, c - c0) for r, c in record["cells"]}
    seen: set[Cell] = set()
    result: list[Region] = []
    for row in range(height):
        for col in range(width):
            if (row, col) in occupied or (row, col) in seen:
                continue
            pending = deque([(row, col)])
            seen.add((row, col))
            region: Region = set()
            touches_edge = False
            while pending:
                cr, cc = pending.popleft()
                region.add((cr, cc))
                touches_edge |= cr in (0, height - 1) or cc in (0, width - 1)
                for dr, dc in _DIR4:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < height and 0 <= nc < width and
                            (nr, nc) not in occupied and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            if not touches_edge:
                result.append(region)
    return result


def _bbox_shape(record: Record) -> tuple[int, int]:
    r0, c0, r1, c1 = record["bbox"]
    return r1 - r0 + 1, c1 - c0 + 1


def _boundary_cells(height: int, width: int | None = None) -> set[Cell]:
    width = height if width is None else width
    return {(row, col) for row in range(height) for col in range(width)
            if row in (0, height - 1) or col in (0, width - 1)}


def _local_cells(record: Record) -> set[Cell]:
    r0, c0, _, _ = record["bbox"]
    return {(row - r0, col - c0) for row, col in record["cells"]}


def _scene_records(grid: Grid) -> tuple[Record, Record, list[Region]]:
    records = _components(grid)
    classified = [(record, _enclosed_regions(record)) for record in records]
    hollows = [(record, holes) for record, holes in classified if holes]
    solids = [record for record, holes in classified if not holes]
    if len(hollows) != 1 or len(solids) != 1:
        raise ValueError(
            f"expected one hollow and one solid object, found {len(hollows)} hollow and {len(solids)} solid"
        )
    hollow, holes = hollows[0]
    return hollow, solids[0], holes


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    errors = _shape_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not 5 <= height <= 16 or not 11 <= width <= 22:
        errors.append(f"grid dimensions {height}x{width} outside 5..16 x 11..22")

    colors = {value for row in grid for value in row if value != 0}
    if len(colors) != 2:
        errors.append(f"expected exactly two nonzero colors, found {len(colors)}")

    records = _components(grid)
    if len(records) != 2:
        errors.append(f"expected exactly two monochromatic components, found {len(records)}")
        return errors

    classified = [(record, _enclosed_regions(record)) for record in records]
    hollows = [(record, holes) for record, holes in classified if holes]
    solids = [record for record, holes in classified if not holes]
    if len(hollows) != 1:
        errors.append(f"expected exactly one hollow object, found {len(hollows)}")
    if len(solids) != 1:
        errors.append(f"expected exactly one solid candidate, found {len(solids)}")
    if len(hollows) != 1 or len(solids) != 1:
        return errors

    hollow, holes = hollows[0]
    solid = solids[0]
    hshape, sshape = _bbox_shape(hollow), _bbox_shape(solid)
    if hshape != sshape:
        errors.append(f"hollow bbox {hshape} does not match solid bbox {sshape}")
    # Official pairs include 4x4 and 3x4 twins.  Ordinary generated pairs use
    # 4x4 or 5x5 squares so every exact override combination stays constructive.
    if hshape not in ((3, 4), (4, 4), (5, 5)):
        errors.append(f"paired bbox must be canonical 3x4/4x4 or generated 5x5, got {hshape}")
        return errors
    box_h, box_w = hshape

    hollow_local = _local_cells(hollow)
    boundary = _boundary_cells(box_h, box_w)
    if not boundary <= hollow_local:
        errors.append("hollow object must contain the complete bbox boundary")
    interior = hollow_local - boundary
    if hshape == (3, 4):
        lawful_patterns = [set()]
    else:
        size = box_h
        lawful_patterns = [set(), _pattern_cells(size, "main"), _pattern_cells(size, "anti")]
    if interior not in lawful_patterns:
        errors.append(f"unrecognized hollow interior divider pattern: {sorted(interior)}")
    if not holes:
        errors.append("hollow object must enclose at least one zero region")
    if interior and len(holes) < 2:
        errors.append("divider pattern must create at least two enclosed regions")

    solid_local = _local_cells(solid)
    expected_solid = {(row, col) for row in range(box_h) for col in range(box_w)}
    if solid_local != expected_solid:
        errors.append("solid twin must fill its entire bounding box")

    _, hc0, _, hc1 = hollow["bbox"]
    _, sc0, _, sc1 = solid["bbox"]
    if hc1 < sc0:
        gap = sc0 - hc1 - 1
    elif sc1 < hc0:
        gap = hc0 - sc1 - 1
    else:
        gap = -1
    if gap < 1:
        errors.append("object bounding boxes must be horizontally separated by a zero column")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Lawful canonical or generated instances inside the declared sampler manifold."""
    return self_check(grid)


def _require_scene(grid: Grid) -> tuple[Record, Record, list[Region]]:
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid hole-transfer input: " + "; ".join(errors))
    return _scene_records(grid)


def observe_overrides(grid: Grid) -> dict[str, Any]:
    """Recover every exact axis from returned pixels, not draw bookkeeping."""
    hollow, solid, _ = _require_scene(grid)
    box_h, box_w = _bbox_shape(hollow)
    if box_h != box_w or box_h not in (4, 5):
        raise ValueError("canonical rectangular frames do not encode generated exact axes")
    size = box_h
    boundary = _boundary_cells(box_h, box_w)
    interior = _local_cells(hollow) - boundary
    diagonal = next(
        (name for name in HOLE_DIAGONALS if interior == _pattern_cells(size, name)),
        None,
    )
    if diagonal is None:
        raise ValueError("canonical plain frames do not encode a generated hole_diagonal")
    colors = frozenset((hollow["color"], solid["color"]))
    palette_kind = _PAIR_TO_PALETTE.get(colors)
    if palette_kind is None:
        raise ValueError(f"unrecognized generated palette: {sorted(colors)}")
    _, hollow_left, _, _ = hollow["bbox"]
    _, solid_left, _, _ = solid["bbox"]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "box_size": size,
        "palette_kind": palette_kind,
        "hollow_side": "left" if hollow_left < solid_left else "right",
        "hole_diagonal": diagonal,
    }


# ---------------------------------------------------------------------------
# Rule mirror, plausible rivals, and lesson contract
# ---------------------------------------------------------------------------


def _true_output(grid: Grid) -> Grid:
    hollow, solid, holes = _require_scene(grid)
    sr0, sc0, _, _ = solid["bbox"]
    output = _copy_grid(grid)
    for region in holes:
        for row, col in region:
            output[sr0 + row][sc0 + col] = 0
    return output


def _carve_full_interior(grid: Grid) -> Grid:
    """Canonical-fitting rival: ignore the template and hollow the whole twin."""
    _, solid, _ = _require_scene(grid)
    r0, c0, r1, c1 = solid["bbox"]
    output = _copy_grid(grid)
    for row in range(r0 + 1, r1):
        for col in range(c0 + 1, c1):
            output[row][col] = 0
    return output


def _largest_hole_only(grid: Grid) -> Grid:
    """Canonical-fitting rival: transfer only one largest enclosed region."""
    _, solid, holes = _require_scene(grid)
    sr0, sc0, _, _ = solid["bbox"]
    output = _copy_grid(grid)
    largest = max(holes, key=lambda region: (len(region), tuple(sorted(region))))
    for row, col in largest:
        output[sr0 + row][sc0 + col] = 0
    return output


def _rightmost_target_only(grid: Grid) -> Grid:
    """Canonical-fitting rival: transfer only when the solid is rightmost."""
    hollow, solid, _ = _require_scene(grid)
    if solid["bbox"][1] > hollow["bbox"][1]:
        return _true_output(grid)
    return _copy_grid(grid)


def _partial_hole_pattern(grid: Grid) -> bool:
    try:
        hollow, _, holes = _require_scene(grid)
    except (TypeError, ValueError):
        return False
    box_h, box_w = _bbox_shape(hollow)
    hole_cells = set().union(*holes)
    return len(hole_cells) < (box_h - 2) * (box_w - 2)


def _multiple_holes(grid: Grid) -> bool:
    try:
        _, _, holes = _require_scene(grid)
    except (TypeError, ValueError):
        return False
    return len(holes) >= 2


def _solid_on_left(grid: Grid) -> bool:
    try:
        hollow, solid, _ = _require_scene(grid)
    except (TypeError, ValueError):
        return False
    return solid["bbox"][1] < hollow["bbox"][1]


SEMANTIC_WITNESSES = {
    "partial_hole_pattern": _partial_hole_pattern,
    "multiple_holes": _multiple_holes,
    "solid_on_left": _solid_on_left,
}
SEMANTIC_RIVALS = {
    "carve_full_interior": _carve_full_interior,
    "largest_hole_only": _largest_hole_only,
    "rightmost_target_only": _rightmost_target_only,
}
WITNESS_RIVALS = {
    "partial_hole_pattern": ["carve_full_interior"],
    "multiple_holes": ["largest_hole_only"],
    "solid_on_left": ["rightmost_target_only"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# Opt into the semantic gate's independent authority/mirror parity check.
rule_mirror = _true_output


def lesson_identifiable(demos: list[dict[str, Grid]], query: dict[str, Grid]) -> list[str]:
    """Report declared rivals that survive demos but disagree on the query."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"needs at least {EXAMPLES_NEEDED} demonstration"]
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demo but disagrees with query")
    return reasons
