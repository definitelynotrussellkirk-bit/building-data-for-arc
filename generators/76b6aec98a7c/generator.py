"""Constructive inputs for the rotation-code mosaic task.

The executable Racket rule remains the sole label authority.  A hollow color-1
square contains a one-color source motif.  A separate dense rectangle whose
values are 2..5 expands to a mosaic: value ``v`` selects ``v - 2`` clockwise
quarter turns of the complete frame interior.

The default four-sample teaching schedule crosses source color and placement;
every generated code rectangle contains all four codes and every default motif
has four distinct rotations.  Exact controls are either honored literally or
rejected before sampling.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "76b6aec98a7c"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "266efcdf916c"
SUMMARY = (
    "A hollow color-1 frame contains a colored source motif. A separate full "
    "2..5 code rectangle is replaced cell-by-cell by the source interior "
    "rotated code-2 clockwise quarter turns."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

LAYOUTS = ("frame_left", "frame_right", "frame_above", "frame_below")
SOURCE_COLORS = (6, 7, 8, 9)
CANONICAL_DIMENSIONS = ((10, 16), (11, 17), (11, 18))
SCHEDULE_PROFILES = (
    "left_color6", "right_color7", "above_color8", "below_color9",
)

INVARIANTS = [
    "exactly one hollow square color-1 frame with a 2x2..4x4 interior",
    "the entire frame interior contains one connected nonzero source color",
    "the separate 2x2..3x3 code rectangle is dense and contains 2,3,4,5",
    "source and code boxes are disjoint and every other cell is background",
    "the output dimensions are code_h*motif_size by code_w*motif_size",
]

AXES = {
    "grid_h": {"type": "int", "default": "one-third canonical anchor; otherwise difficulty-biased 10..20", "valid": "10..20"},
    "grid_w": {"type": "int", "default": "one-third canonical anchor; otherwise difficulty-biased 10..22", "valid": "10..22"},
    "motif_size": {"type": "int", "default": "2,3,4 schedule", "valid": "2..4"},
    "code_h": {"type": "int", "default": "2,3 schedule", "valid": "2..3"},
    "code_w": {"type": "int", "default": "2,2,3,3 schedule", "valid": "2..3"},
    "source_color": {"type": "int", "default": "6,7,8,9 schedule", "valid": "6..9"},
    "layout": {"type": "enum", "default": "four-way schedule", "valid": "|".join(LAYOUTS)},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the default profile; explicit controls may replace any axis."""
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_controls(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    bounds = {
        "grid_h": (10, 20), "grid_w": (10, 22), "motif_size": (2, 4),
        "code_h": (2, 3), "code_w": (2, 3), "source_color": (6, 9),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if name in bounds:
            if type(value) is not int:
                raise ValueError(f"{name} must be an integer (not bool)")
            lo, hi = bounds[name]
            if not lo <= value <= hi:
                raise ValueError(f"{name} outside [{lo}, {hi}]")
        elif name == "layout":
            if type(value) is not str or value not in LAYOUTS:
                raise ValueError(f"invalid layout: {value!r}")


def _bbox(cells: Iterable[tuple[int, int]]):
    cells = tuple(cells)
    if not cells:
        raise ValueError("missing required cells")
    rows, cols = zip(*cells)
    return min(rows), min(cols), max(rows) + 1, max(cols) + 1


def _crop(grid, box):
    r0, c0, r1, c1 = box
    return [list(row[c0:c1]) for row in grid[r0:r1]]


def _rotate(pattern, turns=1):
    result = [list(row) for row in pattern]
    for _ in range(turns % 4):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def _rotation_orbit(pattern):
    return {
        tuple(tuple(row) for row in _rotate(pattern, turns))
        for turns in range(4)
    }


def _connected(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = {min(cells)}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if point in cells and point not in seen:
                seen.add(point)
                stack.append(point)
    return seen == cells


@lru_cache(maxsize=4)
def _motif_library(size):
    """Finite connected, full-bbox, four-rotation motifs; no rejection loop."""
    shapes = []
    for mask in range(1, 1 << (size * size)):
        cells = {
            (r, c) for r in range(size) for c in range(size)
            if mask & (1 << (r * size + c))
        }
        if len(cells) == size * size or _bbox(cells) != (0, 0, size, size):
            continue
        if not _connected(cells):
            continue
        pattern = [[int((r, c) in cells) for c in range(size)] for r in range(size)]
        if len(_rotation_orbit(pattern)) != 4:
            continue
        shapes.append(tuple(sorted(cells)))
    if not shapes:
        raise ValueError(f"no asymmetric connected motifs for size {size}")
    return tuple(shapes)


def _axis_choice(ctx, name, domain, scheduled):
    """Expose the complete exact-control domain while retaining a schedule."""
    options = tuple(domain) if ctx.overrides.get(name) is not None else (scheduled,)
    return ctx.draw_choice(name, options)


def _grid_choice(ctx, name, lo, hi, difficulty):
    domain = tuple(range(lo, hi + 1))
    if difficulty == "easy":
        bias = tuple(range(lo, min(hi, lo + 4) + 1)) * 5
    elif difficulty == "hard":
        bias = tuple(range(max(lo, hi - 5), hi + 1)) * 5
    else:
        middle = (lo + hi) // 2
        bias = tuple(range(max(lo, middle - 3), min(hi, middle + 3) + 1)) * 4
    return ctx.draw_choice(name, domain + bias)


def _place(rng, h, w, side, code_h, code_w, layout):
    """Place boxes with a one-cell gap and overlapping orthogonal projections."""
    if layout in ("frame_left", "frame_right"):
        total = side + 1 + code_w
        base_c = rng.randint(0, w - total)
        shared_r = rng.randint(0, h - max(side, code_h))
        if layout == "frame_left":
            frame = (shared_r, base_c)
            code = (shared_r, base_c + side + 1)
        else:
            code = (shared_r, base_c)
            frame = (shared_r, base_c + code_w + 1)
    else:
        total = side + 1 + code_h
        base_r = rng.randint(0, h - total)
        shared_c = rng.randint(0, w - max(side, code_w))
        if layout == "frame_above":
            frame = (base_r, shared_c)
            code = (base_r + side + 1, shared_c)
        else:
            code = (base_r, shared_c)
            frame = (base_r + code_h + 1, shared_c)
    return frame, code


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_controls(overrides)
    ctx = gen_ctx(
        seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
        difficulty=difficulty, overrides=overrides,
    )

    canonical_anchor = (
        overrides.get("grid_h") is None
        and overrides.get("grid_w") is None
        and sample_index % 3 == 0
    )
    if canonical_anchor:
        anchor_h, anchor_w = CANONICAL_DIMENSIONS[(sample_index // 3) % len(CANONICAL_DIMENSIONS)]
        grid_h = ctx.draw_choice("grid_h", (anchor_h,))
        grid_w = ctx.draw_choice("grid_w", (anchor_w,))
    else:
        grid_h = _grid_choice(ctx, "grid_h", 10, 20, difficulty)
        grid_w = _grid_choice(ctx, "grid_w", 10, 22, difficulty)
    motif_size = _axis_choice(ctx, "motif_size", (2, 3, 4), 2 + sample_index % 3)
    code_h = _axis_choice(ctx, "code_h", (2, 3), 2 + sample_index % 2)
    code_w = _axis_choice(ctx, "code_w", (2, 3), 2 + (sample_index // 2) % 2)
    source_color = _axis_choice(ctx, "source_color", SOURCE_COLORS, 6 + sample_index % 4)
    layout = _axis_choice(ctx, "layout", LAYOUTS, LAYOUTS[sample_index % 4])

    side = motif_size + 2
    if layout in ("frame_left", "frame_right") and side + 1 + code_w > grid_w:
        raise ValueError("grid_w is too small for the requested horizontal layout")
    if layout in ("frame_above", "frame_below") and side + 1 + code_h > grid_h:
        raise ValueError("grid_h is too small for the requested vertical layout")
    if max(side, code_h) > grid_h or max(side, code_w) > grid_w:
        raise ValueError("grid dimensions are too small for the requested boxes")

    motif_cells = ctx.draw_rng("motif").choice(_motif_library(motif_size))
    motif_turns = ctx.draw_rng("motif_orientation").randrange(4)
    motif_pattern = [[int((r, c) in motif_cells) for c in range(motif_size)]
                     for r in range(motif_size)]
    motif_pattern = _rotate(motif_pattern, motif_turns)

    values = [2, 3, 4, 5]
    values.extend(ctx.draw_rng("code_fill").choice((2, 3, 4, 5))
                  for _ in range(code_h * code_w - 4))
    ctx.draw_rng("code_order").shuffle(values)

    frame_origin, code_origin = _place(
        ctx.draw_rng("placement"), grid_h, grid_w, side, code_h, code_w, layout,
    )
    grid = full_grid(grid_h, grid_w, 0)
    fr, fc = frame_origin
    draw_frame(grid, fr, fc, fr + side - 1, fc + side - 1, 1)
    for r, row in enumerate(motif_pattern):
        for c, value in enumerate(row):
            if value:
                grid[fr + 1 + r][fc + 1 + c] = source_color
    cr, cc = code_origin
    for offset, value in enumerate(values):
        grid[cr + offset // code_w][cc + offset % code_w] = value
    return grid


def _parse(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty rectangular list")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    h, w = len(grid), width
    if not (1 <= h <= 30 and 1 <= w <= 30):
        raise ValueError("input dimensions must be in 1..30")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer ARC colors 0..9")

    ones = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1}
    frame_box = _bbox(ones)
    r0, c0, r1, c1 = frame_box
    if r1 - r0 != c1 - c0 or not 4 <= r1 - r0 <= 6:
        raise ValueError("color-1 frame must be square with a 2x2..4x4 interior")
    perimeter = {
        (r, c) for r in range(r0, r1) for c in range(c0, c1)
        if r in (r0, r1 - 1) or c in (c0, c1 - 1)
    }
    if ones != perimeter:
        raise ValueError("color-1 cells must form exactly one hollow rectangular frame")

    motif = _crop(grid, (r0 + 1, c0 + 1, r1 - 1, c1 - 1))
    source_values = {value for row in motif for value in row if value != 0}
    if len(source_values) != 1:
        raise ValueError("frame interior must contain exactly one nonzero source color")
    source_color = next(iter(source_values))
    if source_color not in SOURCE_COLORS:
        raise ValueError("source color must be one of 6,7,8,9")
    source_cells = {(r, c) for r, row in enumerate(motif) for c, value in enumerate(row)
                    if value == source_color}
    if not _connected(source_cells):
        raise ValueError("source motif must be 4-connected")
    size = len(motif)
    if _bbox(source_cells) != (0, 0, size, size):
        raise ValueError("source motif must span the complete frame interior")
    if len(_rotation_orbit(motif)) == 1:
        raise ValueError("source motif must expose at least one rotation distinction")

    frame_rect = {(r, c) for r in range(r0, r1) for c in range(c0, c1)}
    code_cells = {
        (r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
        if value in (2, 3, 4, 5) and (r, c) not in frame_rect
    }
    code_box = _bbox(code_cells)
    code = _crop(grid, code_box)
    code_h, code_w = len(code), len(code[0])
    if code_h not in (2, 3) or code_w not in (2, 3):
        raise ValueError("code rectangle dimensions must each be 2 or 3")
    if any(value not in (2, 3, 4, 5) for row in code for value in row):
        raise ValueError("code rectangle must be completely filled with values 2..5")
    if {value for row in code for value in row} != {2, 3, 4, 5}:
        raise ValueError("code rectangle must contain all four rotation codes")

    cr0, cc0, cr1, cc1 = code_box
    code_rect = {(r, c) for r in range(cr0, cr1) for c in range(cc0, cc1)}
    allowed = frame_rect | code_rect
    rogue = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
             if value != 0 and (r, c) not in allowed]
    if rogue:
        raise ValueError("nonzero cells may occur only in the frame or code rectangle")
    if any((r, c) in frame_rect for r, c in code_rect):
        raise ValueError("frame and code rectangles must be disjoint")

    # The authority only requires disjoint rectangles.  Canonical examples may
    # be diagonally separated, so classify by the first valid cardinal relation
    # rather than imposing the generator's stronger orthogonal-overlap style.
    if c1 <= cc0:
        layout = "frame_left"
    elif cc1 <= c0:
        layout = "frame_right"
    elif r1 <= cr0:
        layout = "frame_above"
    elif cr1 <= r0:
        layout = "frame_below"
    else:
        raise ValueError("frame and code rectangles must be disjoint")

    if code_h * size > 30 or code_w * size > 30:
        raise ValueError("output mosaic exceeds 30x30")
    return {
        "grid_h": h, "grid_w": w, "motif_size": size,
        "code_h": code_h, "code_w": code_w, "source_color": source_color,
        "layout": layout, "frame_box": frame_box, "code_box": code_box,
        "motif": motif, "code": code,
    }


def self_check(grid, *, difficulty=None, meta=None):
    try:
        observed = _parse(grid)
    except ValueError as exc:
        return [str(exc)]
    requested = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    mismatches = [
        f"override {name}={value!r} observed as {observed.get(name)!r}"
        for name, value in requested.items()
        if value is not None and observed.get(name) != value
    ]
    return mismatches


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    parts = _parse(grid)
    return {name: parts[name] for name in AXES}


def _tile(grid, turn_fn, *, forced_color=None):
    parts = _parse(grid)
    motif = parts["motif"]
    code = parts["code"]
    size = parts["motif_size"]
    out = full_grid(len(code) * size, len(code[0]) * size, 0)
    for r, row in enumerate(code):
        for c, value in enumerate(row):
            tile = _rotate(motif, turn_fn(value) % 4)
            for dr, line in enumerate(tile):
                for dc, color in enumerate(line):
                    if color:
                        out[r * size + dr][c * size + dc] = (
                            forced_color if forced_color is not None else color
                        )
    return out


def rule_mirror(grid):
    """Independent Python oracle for tests/evidence; never used for labels."""
    return _tile(grid, lambda value: value - 2)


def _fixed_color_six(grid):
    return _tile(grid, lambda value: value - 2, forced_color=6)


def _ignore_rotations(grid):
    return _tile(grid, lambda value: 0)


def _reverse_rotations(grid):
    return _tile(grid, lambda value: 2 - value)


def _shifted_codes(grid):
    return _tile(grid, lambda value: value - 1)


CANONICAL_SHORTCUTS = {"fixed_color_six": _fixed_color_six}
SEMANTIC_RIVALS = {
    **CANONICAL_SHORTCUTS,
    "ignore_rotations": _ignore_rotations,
    "reverse_rotations": _reverse_rotations,
    "shifted_codes": _shifted_codes,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _non_six_witness(grid):
    return _fixed_color_six(grid) != rule_mirror(grid)


def _rotation_witness(grid):
    expected = rule_mirror(grid)
    return (_ignore_rotations(grid) != expected and
            _reverse_rotations(grid) != expected and
            _shifted_codes(grid) != expected)


SEMANTIC_WITNESSES = {
    "non_six_source": _non_six_witness,
    "all_rotation_codes": _rotation_witness,
}
WITNESS_RIVALS = {
    "non_six_source": ["fixed_color_six"],
    "all_rotation_codes": ["ignore_rotations", "reverse_rotations", "shifted_codes"],
}


def lesson_identifiable(demos, query):
    """Return surviving harmful rivals after checking labeled demonstrations."""
    errors = []
    for index, pair in enumerate(list(demos) + [query]):
        if rule_mirror(pair["input"]) != pair["output"]:
            errors.append(f"pair {index} label disagrees with the review oracle")
    if errors:
        return errors
    for name, rival in LESSON_COMPETITORS.items():
        fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
        harms_query = rival(query["input"]) != query["output"]
        if fits_demos and harms_query:
            errors.append(f"semantic rival survives demonstrations: {name}")
    return errors
