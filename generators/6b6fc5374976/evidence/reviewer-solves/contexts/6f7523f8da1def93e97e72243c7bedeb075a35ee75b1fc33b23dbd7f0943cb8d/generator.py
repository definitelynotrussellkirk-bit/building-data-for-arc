"""Generator for arc_additional_puzzle_bank_volume23:H158.

A blue template is rotated by the single control cell, then the Racket
oracle stamps that transformed template in maroon from the cyan anchor along
the orange-to-cyan vector.  Stamping stops at the first wall collision or
when any cell would leave the grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6b6fc5374976"
VERSION = "2.0.0"
TASK_ID = "6b6fc5374976"
RULE_HASH = "27a417d278bf"

SUMMARY = (
    "Find the blue template, rotate it clockwise according to the lone "
    "control (2=0 turns, 3=1, 4=2, 6=3), and normalize the rotated shape. "
    "The vector from orange 7 to cyan 8 is the repeat step. Starting with "
    "the rotated template's bounding-box anchor at the cyan cell, stamp it "
    "in maroon 9 repeatedly. Stop before the first placement that touches "
    "a color-5 wall or leaves the grid; all input markings disappear."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "the background is 0 and all cells are ARC colors 0..9",
    "there is exactly one blue template of four to seven connected cells",
    "the template has four distinguishable quarter-turn orientations",
    "there is exactly one control cell in {2,3,4,6}",
    "there is exactly one orange 7 and one cyan 8 defining a nonzero vector",
    "at least two lawful placements occur before an edge or color-5 wall stops stamping",
]

ROTATION_CONTROLS = (2, 3, 4, 6)
VECTOR_FAMILIES = ("cardinal", "diagonal")
STOP_MODES = ("edge", "wall")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "easy 11..13; medium 14..16; hard 17..20",
        "valid": "11..20",
    },
    "grid_w": {
        "type": "int",
        "default": "easy 13..15; medium 16..18; hard 19..22",
        "valid": "13..22",
    },
    "rotation_control": {
        "type": "int",
        "default": "sample_index schedule 2|3|4|6",
        "valid": "2|3|4|6",
    },
    "copy_count": {
        "type": "int",
        "default": "easy 2..3; medium 3..5; hard 4..6",
        "valid": "2..6",
    },
    "template_cells": {
        "type": "int",
        "default": "easy 4..5; medium 4..6; hard 5..7",
        "valid": "4..7",
    },
    "vector_family": {
        "type": "str",
        "default": "rng cardinal|diagonal",
        "valid": "cardinal|diagonal",
    },
    "stop_mode": {
        "type": "str",
        "default": "rng edge|wall",
        "valid": "edge|wall",
    },
}

# Every shape is 4-connected, fits a 3x3 box, and has four distinct normalized
# quarter-turns.  Several canonical morphologies are included alongside larger
# asymmetric shapes so the lesson cannot be solved by a fixed T-template.
_TEMPLATE_BANK = {
    4: (
        ((0, 1), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (0, 1), (1, 1), (2, 1)),
    ),
    5: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
        ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    ),
    6: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 0)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)),
    ),
    7: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0), (2, 1)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)),
    ),
}

_CARDINAL_VECTORS = (
    (1, 0), (-1, 0), (0, 1), (0, -1),
    (2, 0), (-2, 0), (0, 2), (0, -2),
)
_DIAGONAL_VECTORS = (
    (1, 1), (1, -1), (-1, 1), (-1, -1),
    (2, 1), (2, -1), (-2, 1), (-2, -1),
    (1, 2), (1, -2), (-1, 2), (-1, -2),
)


def _normalized(cells):
    cells = tuple(cells)
    top = min(row for row, _col in cells)
    left = min(col for _row, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _quarter_turn(cells):
    cells = _normalized(cells)
    height = max(row for row, _col in cells) + 1
    return _normalized((col, height - 1 - row) for row, col in cells)


def _controlled_shape(template, control):
    turns = {2: 0, 3: 1, 4: 2, 6: 3}[control]
    shape = _normalized(template)
    for _ in range(turns):
        shape = _quarter_turn(shape)
    return shape


def _shape_at(shape, anchor, step=(0, 0), multiplier=0):
    top = anchor[0] + step[0] * multiplier
    left = anchor[1] + step[1] * multiplier
    return {(top + row, left + col) for row, col in shape}


def _inside(cells, height, width):
    return all(0 <= row < height and 0 <= col < width for row, col in cells)


def _connected(cells):
    remaining = set(cells)
    if not remaining:
        return False
    stack = [remaining.pop()]
    while stack:
        row, col = stack.pop()
        for point in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if point in remaining:
                remaining.remove(point)
                stack.append(point)
    return not remaining


def _vector_family(delta):
    dr, dc = delta
    return "cardinal" if (dr == 0) != (dc == 0) else "diagonal"


def _band_ranges(difficulty):
    if difficulty == "easy":
        return (11, 13), (13, 15), (2, 3), (4, 5)
    if difficulty == "hard":
        return (17, 20), (19, 22), (4, 6), (5, 7)
    return (14, 16), (16, 18), (3, 5), (4, 6)


def _draw_dimension(ctx, label, normal_bounds, valid_bounds):
    bounds = valid_bounds if ctx.overrides.get(label) is not None else normal_bounds
    return ctx.draw_int(label, *bounds)


def _draw_scheduled_control(ctx, sample_index):
    if ctx.overrides.get("rotation_control") is None:
        ctx.overrides["rotation_control"] = ROTATION_CONTROLS[sample_index % 4]
    return ctx.draw_choice("rotation_control", ROTATION_CONTROLS)


def _candidate_layouts(height, width, shape, copy_count, family, stop_mode, rng):
    vectors = list(_CARDINAL_VECTORS if family == "cardinal" else _DIAGONAL_VECTORS)
    rng.shuffle(vectors)
    anchors = [(row, col) for row in range(height) for col in range(width)]
    rng.shuffle(anchors)
    layouts = []
    for delta in vectors:
        for anchor in anchors:
            marker7 = (anchor[0] - delta[0], anchor[1] - delta[1])
            if not _inside((marker7, anchor), height, width):
                continue
            placements = [
                _shape_at(shape, anchor, delta, index)
                for index in range(copy_count)
            ]
            if not all(_inside(cells, height, width) for cells in placements):
                continue
            next_cells = _shape_at(shape, anchor, delta, copy_count)
            next_inside = _inside(next_cells, height, width)
            if stop_mode == "edge" and next_inside:
                continue
            if stop_mode == "wall" and not next_inside:
                continue
            occupied = set().union(*placements)
            frontier = next_cells - occupied
            if stop_mode == "wall" and not frontier:
                continue
            layouts.append((delta, marker7, anchor, placements, next_cells, frontier))
            if len(layouts) >= 96:
                return layouts
    return layouts


def _place_template(grid, template, forbidden, rng):
    height, width = len(grid), len(grid[0])
    template = _normalized(template)
    shape_h = max(row for row, _col in template) + 1
    shape_w = max(col for _row, col in template) + 1
    candidates = [
        (top, left)
        for top in range(height - shape_h + 1)
        for left in range(width - shape_w + 1)
    ]
    rng.shuffle(candidates)
    for top, left in candidates:
        cells = {(top + row, left + col) for row, col in template}
        halo = {
            (row + dr, col + dc)
            for row, col in cells
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if 0 <= row + dr < height and 0 <= col + dc < width
        }
        if halo & forbidden:
            continue
        for row, col in cells:
            grid[row][col] = 1
        return cells
    return None


def _free_cells(grid, forbidden):
    return [
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == 0 and (row, col) not in forbidden
    ]


def _facts(grid):
    height, width = len(grid), len(grid[0])
    positions = {
        color: [(row, col) for row in range(height) for col in range(width) if grid[row][col] == color]
        for color in range(10)
    }
    controls = [(color, point) for color in ROTATION_CONTROLS for point in positions[color]]
    if len(controls) != 1 or len(positions[7]) != 1 or len(positions[8]) != 1:
        raise ValueError("missing or duplicated control/marker cells")
    control = controls[0][0]
    template = _normalized(positions[1])
    shape = _controlled_shape(template, control)
    marker7, marker8 = positions[7][0], positions[8][0]
    delta = (marker8[0] - marker7[0], marker8[1] - marker7[1])
    copies = 0
    stop_mode = None
    limit = height * width + 1
    while copies <= limit:
        cells = _shape_at(shape, marker8, delta, copies)
        if not _inside(cells, height, width):
            stop_mode = "edge"
            break
        if any(grid[row][col] == 5 for row, col in cells):
            stop_mode = "wall"
            break
        copies += 1
    if stop_mode is None:
        raise ValueError("repeat walk did not terminate")
    return {
        "grid_h": height,
        "grid_w": width,
        "rotation_control": control,
        "copy_count": copies,
        "template_cells": len(template),
        "vector_family": _vector_family(delta),
        "stop_mode": stop_mode,
        "delta": delta,
        "template": template,
    }


def observe_overrides(grid):
    """Return every declared axis as realized in the returned grid."""
    facts = _facts(grid)
    return {axis: facts[axis] for axis in AXES}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h_bounds, w_bounds, copy_bounds, template_bounds = _band_ranges(difficulty)
    height = _draw_dimension(ctx, "grid_h", h_bounds, (11, 20))
    width = _draw_dimension(ctx, "grid_w", w_bounds, (13, 22))
    control = _draw_scheduled_control(ctx, sample_index)
    copy_count = ctx.draw_int(
        "copy_count",
        *( (2, 6) if ctx.overrides.get("copy_count") is not None else copy_bounds ),
    )
    template_cells = ctx.draw_int(
        "template_cells",
        *( (4, 7) if ctx.overrides.get("template_cells") is not None else template_bounds ),
    )
    family = ctx.draw_choice("vector_family", VECTOR_FAMILIES)
    stop_mode = ctx.draw_choice("stop_mode", STOP_MODES)
    rng = ctx.draw_rng("layout")

    template = tuple(rng.choice(_TEMPLATE_BANK[template_cells]))
    shape = _controlled_shape(template, control)
    layouts = _candidate_layouts(
        height, width, shape, copy_count, family, stop_mode, rng
    )
    if not layouts:
        raise ValueError(
            "infeasible override combination: cannot place "
            f"{copy_count} {family} copies with stop_mode={stop_mode!r} "
            f"on {height}x{width}"
        )

    delta, marker7, marker8, placements, next_cells, frontier = rng.choice(layouts)
    grid = full_grid(height, width, 0)
    path_cells = set().union(*placements)
    placement_forbidden = path_cells | next_cells | {marker7, marker8}
    template_position = _place_template(grid, template, placement_forbidden, rng)
    if template_position is None:
        raise ValueError("could not place the source template away from the stamp path")

    semantic = path_cells | {marker7, marker8} | template_position
    free = _free_cells(grid, semantic | next_cells)
    if not free:
        raise ValueError("no free cell remains for the rotation control")
    control_point = rng.choice(free)
    grid[control_point[0]][control_point[1]] = control
    semantic.add(control_point)

    grid[marker7[0]][marker7[1]] = 7
    grid[marker8[0]][marker8[1]] = 8

    if stop_mode == "wall":
        candidates = sorted(frontier - semantic)
        if not candidates:
            raise ValueError("wall-stop layout lacks a fresh blocking frontier cell")
        wall = rng.choice(candidates)
        grid[wall[0]][wall[1]] = 5
        semantic.add(wall)

    # Canonical tasks include irrelevant wall fragments.  Keep at least one
    # distractor and increase clutter with difficulty, while never blocking a
    # valid stamp or changing the requested stopping event.
    distractor_target = {"easy": 1, "medium": 2, "hard": 3}.get(difficulty, 2)
    wall_forbidden = path_cells | next_cells | semantic
    distractor_candidates = _free_cells(grid, wall_forbidden)
    rng.shuffle(distractor_candidates)
    for row, col in distractor_candidates[:distractor_target]:
        grid[row][col] = 5

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"internal layout violated self_check: {errors}")
    realized = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "rotation_control": control,
        "copy_count": copy_count,
        "template_cells": template_cells,
        "vector_family": family,
        "stop_mode": stop_mode,
    }
    if realized != expected:
        raise ValueError(f"internal axis realization drift: expected {expected}, got {realized}")
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["empty or non-grid input"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["ragged grid"]
    errors = []
    height = len(grid)
    bad_values = sorted({
        value
        for row in grid
        for value in row
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
    }, key=repr)
    if bad_values:
        return [f"cells outside integer ARC colors 0..9: {bad_values}"]
    if not (11 <= height <= 20 and 13 <= width <= 22):
        errors.append(f"dimensions {height}x{width} outside 11..20 x 13..22")

    positions = {
        color: [(row, col) for row in range(height) for col in range(width) if grid[row][col] == color]
        for color in range(10)
    }
    if len(positions[7]) != 1 or len(positions[8]) != 1:
        errors.append(
            f"expected exactly one 7 and one 8 marker; got {len(positions[7])} and {len(positions[8])}"
        )
    controls = [(color, point) for color in ROTATION_CONTROLS for point in positions[color]]
    if len(controls) != 1:
        errors.append(f"expected exactly one rotation control in {ROTATION_CONTROLS}; got {len(controls)}")

    template_cells = positions[1]
    if not 4 <= len(template_cells) <= 7:
        errors.append(f"expected 4..7 blue template cells; got {len(template_cells)}")
    elif not _connected(template_cells):
        errors.append("blue template must be 4-connected")
    else:
        forms = set()
        current = _normalized(template_cells)
        for _ in range(4):
            forms.add(current)
            current = _quarter_turn(current)
        if len(forms) != 4:
            errors.append("blue template must have four distinct quarter-turn orientations")

    if not positions[5]:
        errors.append("expected at least one color-5 wall or distractor")

    if errors:
        return errors
    try:
        facts = _facts(grid)
    except Exception as exc:
        return [f"could not recover rule facts: {exc}"]
    if facts["delta"] == (0, 0):
        errors.append("7-to-8 vector must be nonzero")
    if facts["copy_count"] < 2:
        errors.append(f"only {facts['copy_count']} lawful placements before stopping")

    expected = {}
    if isinstance(meta, dict):
        expected.update(meta.get("overrides") or {})
        expected.update({key: value for key, value in meta.items() if key in AXES})
    if expected:
        observed = {axis: facts[axis] for axis in AXES}
        for axis, value in expected.items():
            if axis in observed and observed[axis] != value:
                errors.append(f"override {axis}={value!r} realized as {observed[axis]!r}")
    return errors


def canonical_like(grid):
    """Task-linked strict predicate used by the uniform semantic census."""
    return self_check(grid) == []
