"""Generator for arc_puzzle_bank_21_set15:S15_E3.

A connected color-2 template is normalized to its tight bounding box, reflected
left-to-right, recolored 8, and stamped on a fresh background at the single
color-1 marker.  The sampler deliberately alternates five-cell discriminator
cases with other template sizes: the public canonical pairs also admit the
plausible shortcut "rotate 180 degrees when the template has five cells", so a
training lesson must contain generated five-cell shapes that are not vertically
symmetric.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f1668de79fa1"
TASK_ID = GENERATOR_ID
RULE_HASH = "6fbd99546842"
VERSION = "2.0.0"
SUMMARY = (
    "A 0-background grid contains one connected LR-asymmetric color-2 template "
    "of 4..7 cells and one color-1 anchor. Normalize the template to its tight "
    "bbox, reflect it left-to-right, and paint that shape in color 8 on a fresh "
    "0-grid with the anchor as the bbox top-left."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "cells are literal ARC colors 0, 1, or 2",
    "exactly one connected color-2 template of 4..7 cells",
    "the normalized template is asymmetric under left-right reflection",
    "exactly one color-1 marker",
    "the complete reflected stamp fits in the grid",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 8..12", "valid": "8..15"},
    "grid_w": {"type": "int", "default": "scheduled 13..17", "valid": "13..18"},
    "template_size": {"type": "int", "default": "scheduled 4..7", "valid": "4..7"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# Three of every six profiles are explicit five-cell discriminator cases.  Thus
# every consecutive five-pair lesson has at least two such cases, so holding out
# any one pair still leaves a demonstration that refutes the declared shortcut.
_PROFILE_ROWS = (
    ("canonical_8x13_k5", 8, 13, 5),
    ("canonical_8x14_k4", 8, 14, 4),
    ("canonical_9x14_k5", 9, 14, 5),
    ("expanded_10x15_k6", 10, 15, 6),
    ("canonical_8x14_k5", 8, 14, 5),
    ("expanded_12x17_k7", 12, 17, 7),
)
SCHEDULE_PROFILES = tuple(row[0] for row in _PROFILE_ROWS)
_BAND_SHIFT = {None: 0, "easy": 0, "medium": 1, "hard": 2}

# Deterministic emergency shapes preserve requested size and both asymmetries.
_FALLBACK_SHAPES = {
    4: ((0, 0), (1, 0), (2, 0), (2, 1)),
    5: ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    6: ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (3, 2)),
    7: ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (3, 2), (3, 3)),
}


def _validate_difficulty(difficulty):
    if difficulty not in _BAND_SHIFT:
        raise ValueError("difficulty must be one of None, easy, medium, hard")


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the exact default profile selected for a production draw."""
    del seed  # schedule is intentionally indexed, not seed-aliased
    _validate_difficulty(difficulty)
    return SCHEDULE_PROFILES[(sample_index + _BAND_SHIFT[difficulty]) % len(SCHEDULE_PROFILES)]


def _scheduled_values(seed, sample_index, difficulty):
    name = schedule_profile(seed, sample_index, difficulty)
    return next(row for row in _PROFILE_ROWS if row[0] == name)


def _size(shape):
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


def _normalize(cells):
    points = tuple(cells)
    if not points:
        return []
    top = min(row for row, _ in points)
    left = min(col for _, col in points)
    return sorted((row - top, col - left) for row, col in points)


def _hmirror(shape):
    points = _normalize(shape)
    _, width = _size(points)
    return sorted((row, width - 1 - col) for row, col in points)


def _vmirror(shape):
    points = _normalize(shape)
    height, _ = _size(points)
    return sorted((height - 1 - row, col) for row, col in points)


def _rotate_180(shape):
    points = _normalize(shape)
    height, width = _size(points)
    return sorted((height - 1 - row, width - 1 - col) for row, col in points)


def _connected(shape):
    points = set(shape)
    if not points:
        return False
    seen = {next(iter(points))}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (row + drow, col + dcol)
            if nxt in points and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == points


def _two_boxes_fit(shape, height, width):
    shape_h, shape_w = _size(shape)
    return 2 * shape_h + 1 <= height or 2 * shape_w + 1 <= width


def _rand_asym(rng, count, height, width):
    """Return a connected exact-size polyomino distinguishable from both mirrors."""
    for _ in range(200):
        cells = {(0, 0)}
        while len(cells) < count:
            row, col = rng.choice(sorted(cells))
            drow, dcol = rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
            cells.add((row + drow, col + dcol))
        shape = _normalize(cells)
        if (
            len(shape) == count
            and _hmirror(shape) != shape
            and _vmirror(shape) != shape
            and _two_boxes_fit(shape, height, width)
        ):
            return shape
    shape = list(_FALLBACK_SHAPES[count])
    if not _two_boxes_fit(shape, height, width):
        raise ValueError("requested dimensions cannot place two separated template boxes")
    return shape


def _components_color(grid, color):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            component = []
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                current = stack.pop()
                component.append(current)
                r, c = current
                for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = (r + drow, c + dcol)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            components.append(component)
    return components


def _template_and_marker(grid):
    components = _components_color(grid, 2)
    if len(components) != 1:
        raise ValueError(f"expected one connected color-2 template, found {len(components)}")
    markers = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    ]
    if len(markers) != 1:
        raise ValueError(f"expected one color-1 marker, found {len(markers)}")
    return _normalize(components[0]), markers[0]


def _draw_scheduled_int(ctx, name, low, high, default):
    # Explicit overrides are drawn against the entire advertised domain.  The
    # default path is singleton-scheduled so lesson composition is reproducible.
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, low, high)
    return ctx.draw_choice(name, (default,))


def _separated_origins(height, width, shape, rng):
    """Choose template/stamp bbox origins with at least one blank row/column."""
    shape_h, shape_w = _size(shape)
    origins = [
        (row, col)
        for row in range(height - shape_h + 1)
        for col in range(width - shape_w + 1)
    ]
    candidates = []
    for template_origin in origins:
        tr, tc = template_origin
        for marker_origin in origins:
            mr, mc = marker_origin
            separated = (
                tr + shape_h < mr
                or mr + shape_h < tr
                or tc + shape_w < mc
                or mc + shape_w < tc
            )
            if separated:
                candidates.append((template_origin, marker_origin))
    if not candidates:
        raise ValueError("could not place separated template and reflected stamp")
    return rng.choice(candidates)


def _paint(grid, origin, shape, color):
    row0, col0 = origin
    for drow, dcol in shape:
        grid[row0 + drow][col0 + dcol] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_difficulty(difficulty)
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    bounds = {"grid_h": (8, 15), "grid_w": (13, 18), "template_size": (4, 7)}
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        low, high = bounds[name]
        if not low <= value <= high:
            raise ValueError(f"{name}={value} outside [{low}, {high}]")

    _, default_h, default_w, default_size = _scheduled_values(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_scheduled_int(ctx, "grid_h", 8, 15, default_h)
    width = _draw_scheduled_int(ctx, "grid_w", 13, 18, default_w)
    template_size = _draw_scheduled_int(ctx, "template_size", 4, 7, default_size)
    shape = _rand_asym(ctx.draw_rng("template_shape"), template_size, height, width)
    template_origin, marker = _separated_origins(
        height, width, shape, ctx.draw_rng("layout")
    )
    grid = full_grid(height, width, 0)
    _paint(grid, template_origin, shape, 2)
    grid[marker[0]][marker[1]] = 1
    return grid


def observe_overrides(grid):
    shape, _ = _template_and_marker(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "template_size": len(shape),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    errors = []
    if not 8 <= len(grid) <= 15:
        errors.append(f"grid height {len(grid)} outside 8..15")
    if not 13 <= width <= 18:
        errors.append(f"grid width {width} outside 13..18")
    if any(type(value) is not int or value not in (0, 1, 2) for row in grid for value in row):
        errors.append("cells must be literal integer colors 0, 1, or 2")
        return errors
    markers = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    ]
    if len(markers) != 1:
        errors.append(f"expected exactly one color-1 marker, found {len(markers)}")
    components = _components_color(grid, 2)
    if len(components) != 1:
        errors.append(f"expected exactly one connected color-2 template, found {len(components)}")
        return errors
    shape = _normalize(components[0])
    if not 4 <= len(shape) <= 7:
        errors.append(f"template size should be 4..7, found {len(shape)}")
    if _hmirror(shape) == shape:
        errors.append("template is LR-symmetric; reflection would be indistinguishable from identity")
    if markers:
        marker_row, marker_col = markers[0]
        for drow, dcol in _hmirror(shape):
            if not (0 <= marker_row + drow < len(grid) and 0 <= marker_col + dcol < width):
                errors.append("complete reflected stamp must fit in bounds")
                break
    return errors


def strict_canonical_like(grid):
    """This sampler's lawful manifold; canonical vertical symmetry is allowed."""
    return self_check(grid)


def _stamp_output(grid, transformed_shape):
    height, width = len(grid), len(grid[0])
    _, marker = _template_and_marker(grid)
    output = full_grid(height, width, 0)
    for drow, dcol in transformed_shape:
        row, col = marker[0] + drow, marker[1] + dcol
        if 0 <= row < height and 0 <= col < width:
            output[row][col] = 8
    return output


def rule_mirror(grid):
    """Independent Python mirror of the unchanged selected Racket authority."""
    shape, _ = _template_and_marker(grid)
    return _stamp_output(grid, _hmirror(shape))


def _rotate_five_else_flip_lr(grid):
    """RIVAL, not authority: rotate five-cell templates; mirror all others."""
    shape, _ = _template_and_marker(grid)
    transformed = _rotate_180(shape) if len(shape) == 5 else _hmirror(shape)
    return _stamp_output(grid, transformed)


def _five_cell_non_ud_symmetric(grid):
    try:
        shape, _ = _template_and_marker(grid)
    except (TypeError, ValueError, IndexError):
        return False
    return len(shape) == 5 and _vmirror(shape) != shape


_RIVAL_NAME = "rotate_five_else_flip_lr"
SEMANTIC_WITNESSES = {"five_cell_non_ud_symmetric": _five_cell_non_ud_symmetric}
SEMANTIC_RIVALS = {_RIVAL_NAME: _rotate_five_else_flip_lr}
WITNESS_RIVALS = {"five_cell_non_ud_symmetric": [_RIVAL_NAME]}
CANONICAL_SHORTCUTS = {_RIVAL_NAME: _rotate_five_else_flip_lr}
LESSON_COMPETITORS = {_RIVAL_NAME: _rotate_five_else_flip_lr}


def lesson_identifiable(demos, query):
    """Report a declared rival only when it survives demos but differs on query."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(deepcopy(pair["input"])) == pair["output"] for pair in demos):
            if rival(deepcopy(query["input"])) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query answer")
    return reasons
