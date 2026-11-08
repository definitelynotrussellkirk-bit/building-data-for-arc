"""Strict generator for marker-selected panel transforms.

The control cell at (0, 0) chooses the canonical first-stage transform:
2=left/right reflection, 3=clockwise rotation, and 1/4=identity.  The source
panel occupies rows 1+ and columns 1..separator-1; the separator is the unique
all-9 column below the control row.  The transformed panel fits in the blank
right region and is pasted at row 1, separator+1.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9e2802ee78bd"
VERSION = "3.0.0"
TASK_ID = GENERATOR_ID
SUMMARY = (
    "A marker at (0,0) selects identity, flip-lr, or rotate-cw for an "
    "asymmetric source panel left of a unique all-9 separator. The transformed "
    "panel fits into the initially blank right region. Every advertised scalar "
    "override is exact and recoverable from returned pixels."
)

INVARIANTS = [
    "the control cell (0,0) is one of 1,2,3,4 and selects the transform",
    "the unique separator is all 9 on rows 1+ and contains no source pixels",
    "the source panel is nonblank, uses 2..5 colors, and is asymmetric",
    "the right region is blank and large enough for the selected transform",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_separator", "blank_panel", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS
_TEXTURES = PALETTE_KINDS + DEGENERATE_TEXTURES
_POSITION_BIASES = ("left_panel",)
_MARKERS = (1, 2, 3, 4)
_DIFFICULTIES = (None, "easy", "medium", "hard")

# Prefix sets are unique for each palette size, making texture observable from
# returned pixels without hidden metadata.
_PALETTE_BANKS = {
    "default": (1, 2, 3, 4, 5),
    "warm": (2, 4, 6, 8, 1),
    "cool": (1, 5, 7, 3, 6),
    "varied": (3, 6, 8, 2, 7),
}

AXES = {
    "grid_h": {"type": "int", "default": "derived from panel_h", "valid": "4..30"},
    "grid_w": {"type": "int", "default": "fitted", "valid": "minimum fitted width..30"},
    "marker": {"type": "int", "default": "rng {1,2,3,4}", "valid": "1|2|3|4"},
    "panel_h": {"type": "int", "default": "difficulty-aware", "valid": "3..29"},
    "panel_w": {"type": "int", "default": "fitted", "valid": "2..panel_h"},
    "palette_size": {"type": "int", "default": "rng", "valid": "2..5"},
    "position_bias": {"type": "str", "default": "left_panel", "valid": "left_panel"},
    "texture": {
        "type": "str",
        "default": "rng palette kind",
        "valid": "default|warm|cool|varied|no_separator|blank_panel|full_grid",
    },
}


def _shape(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["empty grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["empty row"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["ragged grid"]
    return len(grid), width, []


def _flip_lr(panel: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in panel]


def _flip_ud(panel: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in reversed(panel)]


def _transpose(panel: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*panel, strict=True)]


def _rotate_cw(panel: list[list[int]]) -> list[list[int]]:
    return _flip_lr(_transpose(panel))


def _selected_transform(panel: list[list[int]], marker: int) -> list[list[int]]:
    if marker == 2:
        return _flip_lr(panel)
    if marker == 3:
        return _rotate_cw(panel)
    return [list(row) for row in panel]


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer (not bool)")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}, got {value}")
    return value


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(sample_index, 0, 2**31 - 1, "sample_index")
    if difficulty not in _DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(
            f"unknown override(s): {', '.join(unknown)}; valid axes: {', '.join(AXES)}"
        )
    for key in ("grid_h", "grid_w", "marker", "panel_h", "panel_w", "palette_size"):
        if key in overrides and overrides[key] is not None and type(overrides[key]) is not int:
            raise TypeError(f"{key} must be an integer (not bool)")
    if "texture" in overrides and overrides["texture"] is not None:
        if type(overrides["texture"]) is not str or overrides["texture"] not in _TEXTURES:
            raise ValueError(f"texture must be one of {_TEXTURES}")
    if "position_bias" in overrides and overrides["position_bias"] is not None:
        if type(overrides["position_bias"]) is not str or overrides["position_bias"] not in _POSITION_BIASES:
            raise ValueError("position_bias must be 'left_panel'")


def _default_panel_h(ctx, marker: int, difficulty: Any) -> int:
    if marker == 3:
        bands = {"easy": (3, 7), "medium": (7, 15), "hard": (15, 26), None: (3, 20)}
    else:
        bands = {"easy": (3, 7), "medium": (7, 17), "hard": (17, 29), None: (3, 20)}
    low, high = bands[difficulty]
    return ctx.draw_rng("panel_h_default").randint(low, high)


def _resolve_dimensions(ctx, marker: int, overrides: dict[str, Any], difficulty: Any) -> tuple[int, int, int, int]:
    raw_h = overrides.get("grid_h")
    raw_ph = overrides.get("panel_h")
    if raw_h is not None:
        _integer(raw_h, 4, 30, "grid_h")
    if raw_ph is not None:
        _integer(raw_ph, 3, 29, "panel_h")
    if raw_h is not None and raw_ph is not None and raw_h != raw_ph + 1:
        raise ValueError(
            f"inconsistent grid_h={raw_h} and panel_h={raw_ph}; grid_h must equal panel_h+1"
        )
    panel_h = raw_ph if raw_ph is not None else (raw_h - 1 if raw_h is not None else _default_panel_h(ctx, marker, difficulty))
    grid_h = panel_h + 1
    if marker == 3 and panel_h > 26:
        raise ValueError(
            f"panel_h={panel_h} cannot fit a rotated panel in a grid of width at most 30"
        )
    ctx.overrides["panel_h"] = panel_h
    ctx.overrides["grid_h"] = grid_h
    panel_h = ctx.draw_int_strict("panel_h", 3, 29)
    grid_h = ctx.draw_int_strict("grid_h", 4, 30)

    raw_w = overrides.get("grid_w")
    if raw_w is not None:
        _integer(raw_w, 6, 30, "grid_w")
    max_panel_w = min(panel_h, 14)
    if marker == 3:
        max_panel_w = min(max_panel_w, 30 - panel_h - 2)
    if raw_w is not None:
        width_bound = raw_w - panel_h - 2 if marker == 3 else (raw_w - 2) // 2
        max_panel_w = min(max_panel_w, width_bound)
    if max_panel_w < 2:
        raise ValueError("requested dimensions leave no room for a panel of width at least 2")

    raw_pw = overrides.get("panel_w")
    if raw_pw is not None:
        _integer(raw_pw, 2, panel_h, "panel_w")
        if raw_pw > max_panel_w:
            raise ValueError(
                f"panel_w={raw_pw} does not fit marker={marker}, panel_h={panel_h}, grid_w={raw_w or 30}"
            )
        panel_w = raw_pw
    else:
        panel_w = ctx.draw_rng("panel_w_default").randint(2, max_panel_w)
    ctx.overrides["panel_w"] = panel_w
    panel_w = ctx.draw_int_strict("panel_w", 2, panel_h)

    transformed_w = panel_h if marker == 3 else panel_w
    min_grid_w = panel_w + transformed_w + 2
    if raw_w is not None and raw_w < min_grid_w:
        raise ValueError(
            f"grid_w={raw_w} is inconsistent with fitted minimum {min_grid_w}"
        )
    grid_w = raw_w if raw_w is not None else ctx.draw_rng("grid_w_default").randint(min_grid_w, 30)
    ctx.overrides["grid_w"] = grid_w
    grid_w = ctx.draw_int_strict("grid_w", min_grid_w, 30)
    return grid_h, grid_w, panel_h, panel_w


def _make_panel(panel_h: int, panel_w: int, palette: tuple[int, ...], rng) -> list[list[int]]:
    cells = [(row, col) for row in range(panel_h) for col in range(panel_w)]
    for _ in range(64):
        panel = full_grid(panel_h, panel_w, 0)
        order = list(cells)
        rng.shuffle(order)
        for (row, col), color in zip(order, palette, strict=False):
            panel[row][col] = color
        for row, col in order[len(palette):]:
            if rng.random() < 0.58:
                panel[row][col] = rng.choice(palette)
        if panel != _flip_ud(panel) and panel != _flip_lr(panel):
            return panel
    raise RuntimeError("failed to draw an asymmetric panel")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=dict(overrides),
    )

    texture = ctx.draw_choice("texture", PALETTE_KINDS if overrides.get("texture") not in DEGENERATE_TEXTURES else _TEXTURES)
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx.draw_rng("degenerate"))

    position_bias = ctx.draw_choice("position_bias", _POSITION_BIASES)
    marker = ctx.draw_choice("marker", _MARKERS)
    grid_h, grid_w, panel_h, panel_w = _resolve_dimensions(ctx, marker, overrides, difficulty)
    palette_size = ctx.draw_int_strict("palette_size", 2, 5)
    palette = tuple(_PALETTE_BANKS[texture][:palette_size])
    panel = _make_panel(panel_h, panel_w, palette, ctx.draw_rng("panel"))

    grid = full_grid(grid_h, grid_w, 0)
    grid[0][0] = marker
    separator = panel_w + 1
    for row in range(panel_h):
        for col in range(panel_w):
            grid[row + 1][col + 1] = panel[row][col]
    for row in range(1, grid_h):
        grid[row][separator] = 9

    assert position_bias == "left_panel"
    errors = self_check(grid)
    if errors:
        raise AssertionError(f"generator produced invalid grid: {errors}")
    return grid


def _draw_from_degenerate(name, rng):
    del rng
    grid = full_grid(4, 9, 0)
    grid[0][0] = 2
    grid[1][1] = 3
    grid[2][1] = 3
    grid[2][2] = 4
    for row in range(1, 4):
        grid[row][3] = 9
    if name == "no_separator":
        for row in range(1, 4):
            grid[row][3] = 0
        return grid
    if name == "blank_panel":
        grid[1][1] = 0
        grid[2][1] = 0
        grid[2][2] = 0
        return grid
    if name == "full_grid":
        return full_grid(4, 9, 5)
    raise ValueError(f"unknown degenerate texture: {name}")


def _analyze(grid: Any) -> dict[str, Any]:
    height, width, errors = _shape(grid)
    if errors:
        raise ValueError(errors[0])
    if not (4 <= height <= 30 and 6 <= width <= 30):
        raise ValueError(f"dims {height}x{width} outside 4..30 x 6..30")
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                raise ValueError(f"cell {(row_index, col_index)} must be an integer color 0..9")

    marker = grid[0][0]
    if marker not in _MARKERS:
        raise ValueError(f"control marker must be one of {_MARKERS}, got {marker!r}")
    if any(value != 0 for value in grid[0][1:]):
        raise ValueError("control row must be blank outside (0,0)")

    separators = [
        col for col in range(1, width)
        if all(grid[row][col] == 9 for row in range(1, height))
    ]
    if len(separators) != 1:
        raise ValueError(f"expected exactly one all-9 separator column, found {separators}")
    separator = separators[0]
    panel_w = separator - 1
    panel_h = height - 1
    if panel_w < 2:
        raise ValueError("source panel width must be at least 2")

    panel = [list(row[1:separator]) for row in grid[1:]]
    if any(value == 9 for row in panel for value in row):
        raise ValueError("source panel may not contain color 9")
    colors = {value for row in panel for value in row if value != 0}
    if not 2 <= len(colors) <= 5:
        raise ValueError(f"source panel must use 2..5 nonzero colors, found {len(colors)}")
    if panel == _flip_ud(panel) or panel == _flip_lr(panel):
        raise ValueError("source panel must break both horizontal and vertical reflection shortcuts")

    if any(grid[row][col] != 0 for row in range(1, height) for col in range(separator + 1, width)):
        raise ValueError("right region must be blank in the input")
    transformed = _selected_transform(panel, marker)
    if separator + 1 + len(transformed[0]) > width:
        raise ValueError("selected transformed panel does not fit in the right region")

    texture_matches = [
        name for name, bank in _PALETTE_BANKS.items()
        if colors == set(bank[:len(colors)])
    ]
    if len(texture_matches) != 1:
        raise ValueError(f"source palette {sorted(colors)} does not identify one texture")
    return {
        "grid_h": height,
        "grid_w": width,
        "panel_h": panel_h,
        "panel_w": panel_w,
        "marker": marker,
        "palette_size": len(colors),
        "position_bias": "left_panel",
        "texture": texture_matches[0],
        "separator": separator,
        "panel": panel,
        "transformed": transformed,
    }


def observe_overrides(grid) -> dict[str, Any]:
    info = _analyze(grid)
    return {axis: info[axis] for axis in AXES}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty
    try:
        info = _analyze(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        if isinstance(meta.get("overrides"), dict):
            requested.update(meta["overrides"])
        requested.update({axis: meta[axis] for axis in AXES if axis in meta})
    for axis, expected in requested.items():
        if axis in info and info[axis] != expected:
            return [f"{axis} requested {expected!r}, observed {info[axis]!r}"]
    return []


def strict_canonical_like(grid):
    return self_check(grid)


def _paste(grid: list[list[int]], panel: list[list[int]], top: int, left: int) -> list[list[int]]:
    out = [list(row) for row in grid]
    for row, values in enumerate(panel):
        for col, value in enumerate(values):
            out[top + row][left + col] = value
    return out


def rule_mirror(grid):
    info = _analyze(grid)
    return _paste([list(row) for row in grid], info["transformed"], 1, info["separator"] + 1)


def _always_identity(grid):
    info = _analyze(grid)
    return _paste([list(row) for row in grid], info["panel"], 1, info["separator"] + 1)


def _always_flip_lr(grid):
    info = _analyze(grid)
    return _paste([list(row) for row in grid], _flip_lr(info["panel"]), 1, info["separator"] + 1)


def _always_rotate_cw(grid):
    info = _analyze(grid)
    rotated = _rotate_cw(info["panel"])
    if info["separator"] + 1 + len(rotated[0]) > info["grid_w"]:
        return _always_identity(grid)
    return _paste([list(row) for row in grid], rotated, 1, info["separator"] + 1)


SEMANTIC_RIVALS = {
    "always_identity": _always_identity,
    "always_flip_lr": _always_flip_lr,
    "always_rotate_cw": _always_rotate_cw,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _witness(grid, marker: int, rival: str) -> bool:
    try:
        info = _analyze(grid)
        return info["marker"] == marker and SEMANTIC_RIVALS[rival](grid) != rule_mirror(grid)
    except (TypeError, ValueError):
        return False


SEMANTIC_WITNESSES = {
    "identity_not_flip": lambda grid: _witness(grid, 1, "always_flip_lr"),
    "flip_lr_required": lambda grid: _witness(grid, 2, "always_identity"),
    "rotate_cw_required": lambda grid: _witness(grid, 3, "always_identity"),
}
WITNESS_RIVALS = {
    "identity_not_flip": ["always_flip_lr"],
    "flip_lr_required": ["always_identity"],
    "rotate_cw_required": ["always_identity"],
}
