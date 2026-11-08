"""Generator for Select from the Library and Transform into a Gallery.

The input contains three maroon-framed library patterns.  A colored key above
an entry names it.  The penultimate row selects keys and the final row gives
aligned transform codes: 5 = identity, 6 = rotate clockwise, 7 = flip left/right.
The selected transformed crops are packed left-to-right with one blank column.
"""
from __future__ import annotations

import copy
from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "3f5263211041"
TASK_ID = GENERATOR_ID
RULE_HASH = "b923514da8e3"
VERSION = "3.1.0"
SUMMARY = "Use framed library shapes, selector keys, and transform codes to build a decoded gallery strip."

INVARIANTS = [
    "exactly three separate 6x5 color-9 frames form the library",
    "one unique nonzero key immediately above each frame names its cropped pattern",
    "aligned cells in the final two rows encode selector keys and transforms",
    "transform codes are 5=identity, 6=rotate-clockwise, and 7=flip-left-right",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
_PALETTES = {
    "default": (1, 2, 3),
    "warm": (2, 4, 8),
    "cool": (1, 2, 8),
    "varied": (1, 3, 4),
}

# Every advertised axis is exact, keyed, pixel-observable, and jointly legal.
AXES = {
    "library": {"type": "int", "default": "rng 0..3", "valid": "0..3"},
    "program": {"type": "int", "default": "rng 0..6", "valid": "0..6"},
    "palette_kind": {
        "type": "str",
        "default": "rng default|warm|cool|varied",
        "valid": "|".join(PALETTE_KINDS),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_NEGATIVE_TEXTURES: tuple[str, ...] = ()

_LIBRARIES = [
    [
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1), (2, 1), (2, 2)],
        [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)],
    ],
    [
        [(0, 0), (1, 0), (2, 0), (2, 1)],
        [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
        [(0, 0), (0, 1), (1, 1), (2, 1)],
    ],
    [
        [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)],
        [(0, 0), (1, 0), (1, 1), (2, 0), (2, 1)],
        [(0, 2), (1, 0), (1, 1), (1, 2), (2, 0)],
    ],
    [
        [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 0), (2, 1), (2, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
]

# Logical shape index, then transform code.  Include both canonical program
# lengths so generated lessons cover three- and four-part galleries.
_PROGRAMS = [
    [(0, 5), (1, 6), (2, 7)],
    [(2, 6), (0, 7), (1, 5)],
    [(1, 7), (1, 6), (0, 5)],
    [(0, 6), (2, 5), (0, 7)],
    [(2, 7), (1, 5), (2, 6)],
    [(0, 5), (2, 7), (1, 6), (0, 7)],
    [(2, 6), (1, 5), (0, 7), (2, 5)],
]

_FRAME_LEFTS = (1, 8, 15)
_KEY_COLORS = (2, 3, 4, 8)
_TRANSFORMS = (5, 6, 7)
_H = 14
_W = 21


def _normalize_cells(cells):
    cells = tuple(cells)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


_SHAPE_LOOKUP = {
    _normalize_cells(cells): (library_index, shape_index)
    for library_index, library in enumerate(_LIBRARIES)
    for shape_index, cells in enumerate(library)
}
_PALETTE_LOOKUP = {frozenset(colors): name for name, colors in _PALETTES.items()}
_PROGRAM_LOOKUP = {tuple(program): index for index, program in enumerate(_PROGRAMS)}


def _paint(grid, top, left, cells, color):
    for r, c in cells:
        grid[top + r][left + c] = color


def _crop_nonzero(grid):
    occupied = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not occupied:
        return [[0]]
    r0 = min(r for r, _ in occupied)
    r1 = max(r for r, _ in occupied)
    c0 = min(c for _, c in occupied)
    c1 = max(c for _, c in occupied)
    return [list(row[c0:c1 + 1]) for row in grid[r0:r1 + 1]]


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _apply_transform(pattern, code):
    if code == 6:
        return _rotate_cw(pattern)
    if code == 7:
        return _flip_lr(pattern)
    return [list(row) for row in pattern]


def _hstack_center(pieces):
    if not pieces:
        return [[]]
    height = max(len(piece) for piece in pieces)
    width = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    output = full_grid(height, width, 0)
    left = 0
    for piece in pieces:
        top = (height - len(piece)) // 2
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                output[top + r][left + c] = value
        left += len(piece[0]) + 1
    return output


def _grid_error(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return "expected a nonempty rectangular grid"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "expected nonempty rows"
    width = len(grid[0])
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != width:
            return "ragged grid"
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            return "cells must be integer ARC colors 0..9"
    if len(grid) > 30 or width > 30:
        return f"grid too large: {len(grid)}x{width}"
    return None


def _components_of_color(grid, color):
    cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    components = []
    while cells:
        start = next(iter(cells))
        cells.remove(start)
        queue = deque([start])
        component = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in cells:
                    cells.remove(point)
                    component.add(point)
                    queue.append(point)
        components.append(component)
    return components


def _frame_record(grid, component):
    rows = [r for r, _ in component]
    cols = [c for _, c in component]
    top, bottom = min(rows), max(rows)
    left, right = min(cols), max(cols)
    height, width = bottom - top + 1, right - left + 1
    expected = {
        (r, c)
        for r in range(top, bottom + 1)
        for c in range(left, right + 1)
        if r in (top, bottom) or c in (left, right)
    }
    if height != 6 or width != 5 or component != expected:
        raise ValueError("color-9 objects must be exact separate 6x5 rectangular borders")
    if top < 1 or bottom >= len(grid) - 3:
        raise ValueError("library frames need a key row above and must stay above the two code rows")
    key_hits = [
        (top - 1, c, grid[top - 1][c])
        for c in range(left, right + 1)
        if grid[top - 1][c] not in (0, 9)
    ]
    if len(key_hits) != 1:
        raise ValueError("each frame must have exactly one nonzero non-9 key immediately above it")
    interior = [list(row[left + 1:right]) for row in grid[top + 1:bottom]]
    if not any(value != 0 for row in interior for value in row):
        raise ValueError("library patterns must be nonempty")
    pattern = _crop_nonzero(interior)
    occupied = [(r, c) for r, row in enumerate(pattern) for c, value in enumerate(row) if value]
    signature = _normalize_cells(occupied)
    shape_info = _SHAPE_LOOKUP.get(signature)
    colors = {value for row in pattern for value in row if value}
    return {
        "top": top,
        "bottom": bottom,
        "left": left,
        "right": right,
        "key_row": top - 1,
        "key_col": key_hits[0][1],
        "key": key_hits[0][2],
        "pattern": pattern,
        "signature": signature,
        "pattern_colors": colors,
        "library_index": None if shape_info is None else shape_info[0],
        "shape_index": None if shape_info is None else shape_info[1],
        "border": component,
    }


def _analysis(grid):
    """Parse the visible task grammar independently of generation bookkeeping."""
    error = _grid_error(grid)
    if error:
        return {"errors": [error], "frames": []}
    grid = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    errors = []
    components = _components_of_color(grid, 9)
    if len(components) != 3:
        return {"errors": [f"expected exactly three color-9 frame objects, found {len(components)}"], "frames": []}
    frames = []
    for component in components:
        try:
            frames.append(_frame_record(grid, component))
        except ValueError as exc:
            errors.append(str(exc))
    if errors:
        return {"errors": errors, "frames": frames}
    frames.sort(key=lambda frame: (frame["top"], frame["left"]))
    keys = [frame["key"] for frame in frames]
    if len(set(keys)) != 3:
        errors.append("frame keys must be unique")

    selector_positions = [(c, value) for c, value in enumerate(grid[-2]) if value != 0]
    transform_positions = [(c, value) for c, value in enumerate(grid[-1]) if value != 0]
    if not 3 <= len(selector_positions) <= 4:
        errors.append("program must contain three or four selector/transform pairs")
    if len(selector_positions) != len(transform_positions):
        errors.append("selector and transform rows must have equal nonzero lengths")
    if [c for c, _ in selector_positions] != [c for c, _ in transform_positions]:
        errors.append("selector keys and transform codes must be vertically aligned")
    if any(value not in set(keys) for _, value in selector_positions):
        errors.append("every selector must name one of the visible frame keys")
    if any(value not in _TRANSFORMS for _, value in transform_positions):
        errors.append("transform codes must be 5, 6, or 7")

    allowed_nonzero = set()
    for frame in frames:
        allowed_nonzero.update(frame["border"])
        allowed_nonzero.add((frame["key_row"], frame["key_col"]))
        for r in range(frame["top"] + 1, frame["bottom"]):
            for c in range(frame["left"] + 1, frame["right"]):
                if grid[r][c] != 0:
                    allowed_nonzero.add((r, c))
    allowed_nonzero.update((h - 2, c) for c, _ in selector_positions)
    allowed_nonzero.update((h - 1, c) for c, _ in transform_positions)
    unexpected = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and (r, c) not in allowed_nonzero
    ]
    if unexpected:
        errors.append(f"unexpected nonzero cells outside library and code rows: {unexpected[:4]}")

    key_to_frame = {frame["key"]: frame for frame in frames}
    selectors = [value for _, value in selector_positions]
    transforms = [value for _, value in transform_positions]
    logical_program = []
    if not errors:
        for key, code in zip(selectors, transforms):
            logical_program.append((key_to_frame[key]["shape_index"], code))

    recognized_libraries = {frame["library_index"] for frame in frames}
    shape_indices = {frame["shape_index"] for frame in frames}
    library_index = None
    if None not in recognized_libraries and len(recognized_libraries) == 1 and shape_indices == {0, 1, 2}:
        library_index = next(iter(recognized_libraries))
    pattern_palette = frozenset().union(*(frame["pattern_colors"] for frame in frames))
    palette_kind = _PALETTE_LOOKUP.get(pattern_palette)
    program_index = None
    if library_index is not None and all(index is not None for index, _ in logical_program):
        program_index = _PROGRAM_LOOKUP.get(tuple(logical_program))

    return {
        "errors": errors,
        "grid": grid,
        "frames": frames,
        "selectors": selectors,
        "transforms": transforms,
        "selector_positions": selector_positions,
        "transform_positions": transform_positions,
        "key_to_frame": key_to_frame,
        "library_index": library_index,
        "palette_kind": palette_kind,
        "program_index": program_index,
    }


def rule_mirror(grid):
    """Exact Python mirror for tests; the pinned Racket program remains authority."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("invalid task input: " + "; ".join(facts["errors"]))
    pieces = []
    for key, code in zip(facts["selectors"], facts["transforms"]):
        pattern = facts["key_to_frame"][key]["pattern"]
        pieces.append(_apply_transform(pattern, code))
    return _hstack_center(pieces)


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def strict_canonical_like(grid):
    return self_check(grid)


MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("witness_anchor", "free_variant")


def schedule_profile(seed, sample_index, difficulty=None):
    """Alternating anchors make every four-pair lesson rotation-safe."""
    return "witness_anchor" if sample_index % 2 == 0 else "free_variant"


def observe_overrides(grid):
    """Recover every advertised exact axis from the returned pixels."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(facts["errors"]))
    missing = [
        name
        for name, value in (
            ("library", facts["library_index"]),
            ("program", facts["program_index"]),
            ("palette_kind", facts["palette_kind"]),
        )
        if value is None
    ]
    if missing:
        raise ValueError(f"grid is lawful but outside observable generated manifold: {missing}")
    return {
        "library": facts["library_index"],
        "program": facts["program_index"],
        "palette_kind": facts["palette_kind"],
    }


def _shape_extent(cells):
    normalized = _normalize_cells(cells)
    return max(r for r, _ in normalized) + 1, max(c for _, c in normalized) + 1


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    library_index = ctx.draw_int_strict("library", 0, len(_LIBRARIES) - 1)
    program_index = ctx.draw_int_strict("program", 0, len(_PROGRAMS) - 1)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)

    library = _LIBRARIES[library_index]
    program = _PROGRAMS[program_index]
    frame_order = ctx.draw_rng("frame_order").sample(range(3), 3)
    if schedule_profile(seed, sample_index, difficulty) == "witness_anchor":
        # A 3-cycle relative to the canonical 2/3/4 position convention:
        # every selected key points to a different physical frame under the
        # fixed-position rival.  Every four consecutive sample indices contain
        # two such anchors, so any single query rotation leaves one in demos.
        physical_keys = (3, 4, 2)
    else:
        physical_keys = tuple(ctx.draw_rng("key_assignment").sample(_KEY_COLORS, 3))
    logical_keys = {
        logical_index: physical_keys[physical_index]
        for physical_index, logical_index in enumerate(frame_order)
    }
    logical_colors = dict(
        zip(range(3), ctx.draw_rng("color_assignment").sample(_PALETTES[palette_kind], 3))
    )

    max_top = {"easy": 2, "medium": 4, "hard": 5, None: 5}[difficulty]
    layout_rng = ctx.draw_rng("frame_layout")
    grid = full_grid(_H, _W, 0)
    for physical_index, logical_index in enumerate(frame_order):
        left = _FRAME_LEFTS[physical_index]
        top = layout_rng.randint(1, max_top)
        draw_frame(grid, top, left, top + 5, left + 4, 9)
        grid[top - 1][left + 2] = logical_keys[logical_index]
        cells = _normalize_cells(library[logical_index])
        shape_h, shape_w = _shape_extent(cells)
        shift_rng = ctx.draw_rng(f"shape_shift_{logical_index}")
        row_shift = shift_rng.randint(0, 4 - shape_h)
        col_shift = shift_rng.randint(0, 3 - shape_w)
        _paint(
            grid,
            top + 1 + row_shift,
            left + 1 + col_shift,
            cells,
            logical_colors[logical_index],
        )

    positions = sorted(ctx.draw_rng("program_positions").sample(range(1, _W - 1), len(program)))
    for col, (logical_index, code) in zip(positions, program):
        grid[-2][col] = logical_keys[logical_index]
        grid[-1][col] = code
    return grid


def _fixed_key_positions(grid):
    """Plausible wrong rule: 2/3/4 mean left/middle/right, ignoring key dots."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("invalid task input: " + "; ".join(facts["errors"]))
    left_to_right = sorted(facts["frames"], key=lambda frame: frame["left"])
    fixed = {2: 0, 3: 1, 4: 2}
    pieces = []
    for selector, code in zip(facts["selectors"], facts["transforms"]):
        frame = left_to_right[fixed.get(selector, 0)]
        pieces.append(_apply_transform(frame["pattern"], code))
    return _hstack_center(pieces)


def _permuted_key_legend(grid):
    try:
        return _fixed_key_positions(copy.deepcopy(grid)) != rule_mirror(copy.deepcopy(grid))
    except (TypeError, ValueError):
        return False


SEMANTIC_WITNESSES = {"permuted_key_legend": _permuted_key_legend}
SEMANTIC_RIVALS = {"fixed_key_positions": _fixed_key_positions}
WITNESS_RIVALS = {"permuted_key_legend": ["fixed_key_positions"]}
CANONICAL_SHORTCUTS = {"fixed_key_positions": _fixed_key_positions}
LESSON_COMPETITORS = {"fixed_key_positions": _fixed_key_positions}


def lesson_identifiable(demos, query):
    """Report any named rival fitting every demonstration but changing query."""
    reasons = []
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(copy.deepcopy(pair["input"])) == pair["output"]
                for pair in demos
            )
            if survives and competitor(copy.deepcopy(query["input"])) != query["output"]:
                reasons.append(f"competitor {name!r} fits every demo but changes the query answer")
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"competitor {name!r} could not evaluate lesson: {exc}")
    return reasons
