"""Generator for arc_additional_puzzle_bank_volume11:H74.

Rule: read two nonzero controls from the top row, rotate the first blue
object, boolean-combine it with the first red object, and render the minimal
cyan result.  The ordinary sampler deliberately covers all 4x4 control pairs
and keeps color-valued controls 1/2 connected to the intended source object.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "974fee515740"
VERSION = "4.0.0"
TASK_ID = GENERATOR_ID
SUMMARY = (
    "The first two nonzero cells of the top row encode a boolean operation "
    "(3 union, 4 intersection, 6 xor, 7 red-minus-blue) and a clockwise "
    "quarter-turn count (1 identity, 2/3/4 = 90/180/270 degrees). The first "
    "red object and first blue object are normalized, blue is rotated, the "
    "masks are combined, and the minimal result is rendered in cyan."
)

INVARIANTS = [
    "the first two nonzero top-row values are valid operation and rotation codes",
    "the selected red and blue components are nontrivial source objects",
    "the selected boolean result is nonempty in ordinary samples",
    "the rendered result is the minimal cyan crop of the combined mask",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("missing_op_code", "missing_rotation_code", "no_overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h": {"type": "int", "default": "difficulty schedule", "valid": "8..24"},
    "grid_w": {"type": "int", "default": "difficulty schedule", "valid": "10..24"},
    "palette_kind": {"type": "str", "default": "keyed helpful choice",
                     "valid": "|".join(PALETTE_KINDS)},
    "texture": {"type": "str", "default": "alias for palette_kind",
                "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
    "operation_code": {"type": "int", "default": "16-sample schedule", "valid": "3|4|6|7"},
    "rotation_code": {"type": "int", "default": "16-sample schedule", "valid": "1|2|3|4"},
    "n_shapes": {"type": "int", "default": "2", "valid": "2"},
    "palette_size": {"type": "int", "default": "4", "valid": "4"},
    "position_bias": {"type": "str", "default": "control_top_left",
                      "valid": "control_top_left"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4"},
    "density": {"type": "str", "default": "sparse", "valid": "sparse"},
}

_OPS = (3, 4, 6, 7)
_ROTS = (1, 2, 3, 4)
_SHAPES = (
    ((0, 0), (0, 1), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (1, 1), (2, 0), (2, 1), (3, 1)),
    ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 2), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (1, 1), (1, 2), (2, 0), (3, 0)),
    ((0, 0), (0, 1), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
)
_DECOR = {
    "default": (5,),
    "warm": (8,),
    "cool": (9,),
    "varied": (5, 8, 9),
}


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of rows")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid colors must be exact integers in 0..9")
    return len(grid), width


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _first_component(grid: list[list[int]], color: int) -> tuple[tuple[int, int], ...]:
    height, width = len(grid), len(grid[0])
    start = next(((r, c) for r in range(height) for c in range(width)
                  if grid[r][c] == color), None)
    if start is None:
        raise ValueError(f"no color-{color} source object")
    found = {start}
    pending = [start]
    while pending:
        row, col = pending.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            other = row + dr, col + dc
            if (0 <= other[0] < height and 0 <= other[1] < width
                    and grid[other[0]][other[1]] == color and other not in found):
                found.add(other)
                pending.append(other)
    return tuple(sorted(found))


def _rotate_cw(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _normalize((col, -row) for row, col in cells)


def _rotate_by(cells: Iterable[tuple[int, int]], code: int) -> tuple[tuple[int, int], ...]:
    result = _normalize(cells)
    for _ in range(code - 1):
        result = _rotate_cw(result)
    return result


def _combine(red: Iterable[tuple[int, int]], blue: Iterable[tuple[int, int]], op: int,
             *, reverse_subtraction: bool = False) -> tuple[tuple[int, int], ...]:
    red_set, blue_set = set(red), set(blue)
    if op == 3:
        result = red_set | blue_set
    elif op == 4:
        result = red_set & blue_set
    elif op == 6:
        result = red_set ^ blue_set
    elif reverse_subtraction:
        result = blue_set - red_set
    else:
        result = red_set - blue_set
    return tuple(sorted(result))


def _render(cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    norm = _normalize(cells)
    if not norm:
        return [[0]]
    height = 1 + max(row for row, _ in norm)
    width = 1 + max(col for _, col in norm)
    occupied = set(norm)
    return [[8 if (row, col) in occupied else 0 for col in range(width)]
            for row in range(height)]


def analyze(grid: Any) -> dict[str, Any]:
    """Return the exact canonical interpretation plus useful intermediates."""
    height, width = _validate_grid(grid)
    top_nonzero = [(col, value) for col, value in enumerate(grid[0]) if value != 0]
    op_raw = top_nonzero[0][1] if top_nonzero else 6
    rot_raw = top_nonzero[1][1] if len(top_nonzero) > 1 else 1
    op = op_raw if op_raw in _OPS else 6
    rot = rot_raw if rot_raw in _ROTS else 1
    red_cells = _first_component(grid, 2)
    blue_cells = _first_component(grid, 1)
    red = _normalize(red_cells)
    blue = _normalize(blue_cells)
    rotated_blue = _rotate_by(blue, rot)
    result = _combine(red, rotated_blue, op)
    return {
        "height": height,
        "width": width,
        "top_nonzero": [[col, value] for col, value in top_nonzero],
        "op_raw": op_raw,
        "rotation_raw": rot_raw,
        "op_code": op,
        "rotation_code": rot,
        "red_cells": [list(cell) for cell in red_cells],
        "blue_cells": [list(cell) for cell in blue_cells],
        "red_mask": [list(cell) for cell in red],
        "blue_mask": [list(cell) for cell in blue],
        "rotated_blue_mask": [list(cell) for cell in rotated_blue],
        "result_mask": [list(cell) for cell in result],
        "output": _render(result),
    }


def apply_rule(grid: Any) -> list[list[int]]:
    return deepcopy(analyze(grid)["output"])


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    try:
        facts = analyze(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    if facts["op_raw"] not in _OPS:
        errors.append(f"first nonzero top-row control must be one of {_OPS}; got {facts['op_raw']}")
    if facts["rotation_raw"] not in _ROTS:
        errors.append(f"second nonzero top-row control must be one of {_ROTS}; got {facts['rotation_raw']}")
    if len(facts["red_cells"]) < 3:
        errors.append("selected red object is a singleton or undersized control fragment")
    if len(facts["blue_cells"]) < 3:
        errors.append("selected blue object is a singleton or undersized control fragment")
    if not facts["result_mask"]:
        errors.append("selected operation has an empty result")
    if len(facts["top_nonzero"]) >= 2 and facts["rotation_raw"] in (1, 2):
        control = tuple(facts["top_nonzero"][1])
        control_cell = (0, control[0])
        source = facts["blue_cells"] if facts["rotation_raw"] == 1 else facts["red_cells"]
        if list(control_cell) not in source:
            errors.append("rotation control color is disconnected from its selected source object")
    return errors


def _strict_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise TypeError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _fixed(overrides: dict[str, Any], name: str, expected: Any) -> None:
    if name in overrides and overrides[name] is not None and overrides[name] != expected:
        raise ValueError(f"{name} must equal {expected!r}")


def _shape_dims(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(shape)
    return 1 + max(r for r, _ in cells), 1 + max(c for _, c in cells)


def _paint_shape(grid: list[list[int]], top: int, left: int,
                 shape: Iterable[tuple[int, int]], color: int) -> None:
    paint_at(grid, top, left, list(shape), color)


def _decorate(grid: list[list[int]], palette_kind: str, rng) -> None:
    colors = _DECOR[palette_kind]
    height, width = len(grid), len(grid[0])
    candidates = [
        (height - 1, width - 1), (height - 1, width // 2),
        (height // 2, width // 2), (height - 2, 0),
        (2, width // 2), (height // 2, width - 2),
    ]
    rng.shuffle(candidates)
    painted = 0
    for row, col in candidates:
        if grid[row][col] == 0:
            grid[row][col] = colors[painted % len(colors)]
            painted += 1
        if painted >= max(2, len(colors) * 2):
            break


def _ordinary_grid(ctx, *, height: int, width: int, op: int, rot: int,
                   palette_kind: str) -> list[list[int]]:
    rng = ctx.draw_rng("layout")
    for attempt in range(256):
        red = tuple(rng.choice(_SHAPES))
        blue = tuple(rng.choice(_SHAPES))
        if red == blue:
            continue
        if not _combine(red, _rotate_by(blue, rot), op):
            continue
        grid = full_grid(height, width, 0)
        grid[0][0] = op
        grid[0][2] = rot
        red_h, red_w = _shape_dims(red)
        blue_h, blue_w = _shape_dims(blue)
        if rot == 1:
            # The color-1 rotation control is itself a cell of the intended blue object.
            _paint_shape(grid, 0, 2, blue, 1)
            red_top = max(4, height - red_h - 2)
            _paint_shape(grid, red_top, 1, red, 2)
        elif rot == 2:
            # The color-2 rotation control is itself a cell of the intended red object.
            _paint_shape(grid, 0, 2, red, 2)
            blue_top = max(4, height - blue_h - 2)
            _paint_shape(grid, blue_top, max(1, width - blue_w - 2), blue, 1)
        else:
            _paint_shape(grid, 3, 1, red, 2)
            _paint_shape(grid, 4, max(6, width - blue_w - 2), blue, 1)
        _decorate(grid, palette_kind, rng)
        if not self_check(grid):
            return grid
    raise RuntimeError("could not construct a lawful semantic sample after 256 attempts")


def _draw_from_degenerate(name: str) -> list[list[int]]:
    height, width = 12, 14
    grid = full_grid(height, width, 0)
    red = ((0, 0), (0, 1), (1, 0), (2, 0))
    blue = ((0, 0), (0, 1), (1, 1), (2, 1))
    if name == "missing_op_code":
        grid[0][2] = 2
        _paint_shape(grid, 0, 2, red, 2)
        _paint_shape(grid, 5, 8, blue, 1)
        return grid
    if name == "missing_rotation_code":
        grid[0][0] = 4
        _paint_shape(grid, 4, 1, red, 2)
        _paint_shape(grid, 5, 8, blue, 1)
        return grid
    if name == "no_overlap":
        # After normalization at rotation code 1, red={(0,0)} and blue lacks (0,0).
        grid[0][0] = 4
        grid[0][2] = 1
        grid[3][1] = 2
        for row, col in ((0, 2), (1, 1), (1, 2)):
            grid[row][col] = 1
        return grid
    raise ValueError(f"unknown degenerate texture {name!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int or type(seed) is bool or seed < 0:
        raise TypeError("seed must be a nonnegative exact integer")
    if type(sample_index) is not int or type(sample_index) is bool or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative exact integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")
    _fixed(overrides, "n_shapes", 2)
    _fixed(overrides, "palette_size", 4)
    _fixed(overrides, "position_bias", "control_top_left")
    _fixed(overrides, "n_distinct_colors", 4)
    _fixed(overrides, "density", "sparse")

    texture = overrides.get("texture")
    if texture is not None and (type(texture) is not str
                                or texture not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES):
        raise ValueError(f"texture must be one of {HELPFUL_TEXTURES + DEGENERATE_TEXTURES}")
    palette_override = overrides.get("palette_kind")
    if palette_override is not None and (type(palette_override) is not str
                                         or palette_override not in PALETTE_KINDS):
        raise ValueError(f"palette_kind must be one of {PALETTE_KINDS}")
    if texture in HELPFUL_TEXTURES and palette_override is not None and texture != palette_override:
        raise ValueError("helpful texture and palette_kind overrides must agree")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture)

    merged = dict(overrides)
    if texture in HELPFUL_TEXTURES:
        merged["palette_kind"] = texture
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=merged)
    if difficulty == "easy":
        default_h, default_w = 10, 12
        h_bounds, w_bounds = (8, 12), (10, 15)
    elif difficulty == "hard":
        default_h, default_w = 16, 20
        h_bounds, w_bounds = (12, 24), (15, 24)
    else:
        default_h, default_w = 13, 17
        h_bounds, w_bounds = (8, 24), (10, 24)
    if "grid_h" in overrides and overrides["grid_h"] is not None:
        _strict_int(overrides["grid_h"], "grid_h", *h_bounds)
        height = ctx.draw_int_strict("grid_h", *h_bounds)
    else:
        height = default_h
    if "grid_w" in overrides and overrides["grid_w"] is not None:
        _strict_int(overrides["grid_w"], "grid_w", *w_bounds)
        width = ctx.draw_int_strict("grid_w", *w_bounds)
    else:
        width = default_w
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)

    scheduled_op = _OPS[sample_index % 4]
    scheduled_rot = _ROTS[(sample_index // 4) % 4]
    op_override = overrides.get("operation_code")
    rot_override = overrides.get("rotation_code")
    if op_override is not None:
        if type(op_override) is not int or type(op_override) is bool or op_override not in _OPS:
            raise ValueError(f"operation_code must be one of {_OPS}")
        op = op_override
    else:
        op = scheduled_op
    if rot_override is not None:
        if type(rot_override) is not int or type(rot_override) is bool or rot_override not in _ROTS:
            raise ValueError(f"rotation_code must be one of {_ROTS}")
        rot = rot_override
    else:
        rot = scheduled_rot
    return _ordinary_grid(ctx, height=height, width=width, op=op, rot=rot,
                          palette_kind=palette_kind)
