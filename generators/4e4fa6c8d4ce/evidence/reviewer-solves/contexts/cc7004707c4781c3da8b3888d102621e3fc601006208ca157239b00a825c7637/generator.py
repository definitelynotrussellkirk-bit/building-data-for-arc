"""Generator for ARC task 6ecd11f4 / review id 4e4fa6c8d4ce.

The input contains two linked objects on a zero background:

* a large block mask in the uniquely most-common colour; and
* a dense square palette with one colour per cell.

The palette side length determines the output side length.  The large object is
sampled once per block, and the palette colour at a position is copied exactly
when the corresponding block is present; otherwise the output cell is zero.

Version 3 replaces stale pseudo-axes with six observable controls, pins the
selected Racket authority, keeps every default draw on an exact canonical
(h, w, colour-count) profile, and deliberately emits palette cells equal to the
shape colour.  That last witness refutes the strongest shortcut left open by
all canonical demonstrations: "apply the mask, but suppress shape-colour
palette entries."
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "4e4fa6c8d4ce"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "adb72b5aa400"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A uniquely most-common-colour block mask and a separate dense 3x3 or "
    "4x4 palette share positional coordinates.  Output copies each palette "
    "cell iff the corresponding large block is present, else 0.  Defaults "
    "cycle through all four canonical size/colour profiles and include "
    "connected and disconnected masks plus shape-colour palette witnesses."
)

INVARIANTS = [
    "the shape colour is the uniquely most-common non-background colour",
    "the palette is a dense 3x3 or 4x4 nonzero square",
    "the sampled shape mask contains both filled and empty blocks",
    "the output is the palette masked position-for-position by the shape",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

PALETTE_PROFILES = ("seven_nonshape", "eight_nonshape", "shape_filled")
MASK_PROFILES = ("connected", "disconnected")
LAYOUTS = ("below", "right")

AXES = {
    "palette_size": {
        "type": "int",
        "default": "four-slot canonical schedule",
        "valid": "3..4",
    },
    "block_size": {
        "type": "int",
        "default": "four-slot canonical schedule",
        "valid": "3..5",
    },
    "layout": {
        "type": "str",
        "default": "four-slot canonical schedule",
        "valid": "below|right",
    },
    "gap": {
        "type": "int",
        "default": "four-slot canonical schedule",
        "valid": "0..1",
    },
    "palette_profile": {
        "type": "str",
        "default": "four-slot canonical schedule",
        "valid": "seven_nonshape|eight_nonshape|shape_filled",
    },
    "mask_profile": {
        "type": "str",
        "default": "four-slot canonical schedule",
        "valid": "connected|disconnected",
    },
}

SCHEDULE_PROFILES = (
    "canonical_27x25",
    "canonical_27x21",
    "canonical_22x22",
    "canonical_21x24",
)

_CANONICAL_GRID_PROFILES = {
    "canonical_27x25": (27, 25, 9),
    "canonical_27x21": (27, 21, 9),
    "canonical_22x22": (22, 22, 10),
    "canonical_21x24": (21, 24, 10),
}

# The controls deliberately use anchor / anti-shortcut / anti-shortcut / anchor
# ordering.  Every sliding three-example window therefore includes a 4x4
# output, a disconnected mask, both placements, and a shape-colour output.
_SCHEDULE_CONTROLS: dict[str, dict[str, object]] = {
    "canonical_27x25": {
        "palette_size": 3,
        "block_size": 3,
        "layout": "below",
        "gap": 1,
        "palette_profile": "seven_nonshape",
        "mask_profile": "connected",
    },
    "canonical_27x21": {
        "palette_size": 3,
        "block_size": 5,
        "layout": "below",
        "gap": 0,
        "palette_profile": "shape_filled",
        "mask_profile": "disconnected",
    },
    "canonical_22x22": {
        "palette_size": 4,
        "block_size": 4,
        "layout": "right",
        "gap": 0,
        "palette_profile": "shape_filled",
        "mask_profile": "disconnected",
    },
    "canonical_21x24": {
        "palette_size": 4,
        "block_size": 3,
        "layout": "right",
        "gap": 1,
        "palette_profile": "eight_nonshape",
        "mask_profile": "connected",
    },
}


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Return the deterministic four-slot teaching profile.

    The profile intentionally ignores seed and difficulty: all bands own the
    same rule manifold, while keyed randomness still varies colour, mask, and
    placement within each slot.
    """
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _default_controls(seed, sample_index, difficulty) -> dict[str, object]:
    return dict(
        _SCHEDULE_CONTROLS[
            schedule_profile(seed, sample_index, difficulty=difficulty)
        ]
    )


def _mask_connected(mask: list[list[bool]]) -> bool:
    cells = {
        (row, col)
        for row, values in enumerate(mask)
        for col, value in enumerate(values)
        if value
    }
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        row, col = queue.popleft()
        for delta_row, delta_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbor = row + delta_row, col + delta_col
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen == cells


def _mask_asymmetric(mask: list[list[bool]]) -> bool:
    side = len(mask)
    return any(mask[row][col] != mask[col][row]
               for row in range(side) for col in range(side))


def _mask_has_full_extent(mask: list[list[bool]]) -> bool:
    side = len(mask)
    cells = [(row, col) for row in range(side) for col in range(side)
             if mask[row][col]]
    return bool(cells) and (
        min(row for row, _ in cells) == 0
        and max(row for row, _ in cells) == side - 1
        and min(col for _, col in cells) == 0
        and max(col for _, col in cells) == side - 1
    )


def _draw_mask(side: int, profile: str, rng) -> list[list[bool]]:
    want_connected = profile == "connected"
    cell_count = side * side
    for _ in range(2000):
        density = rng.uniform(0.38, 0.68)
        mask = [
            [rng.random() < density for _ in range(side)]
            for _ in range(side)
        ]
        filled = sum(value for row in mask for value in row)
        if not (max(3, side) <= filled < cell_count):
            continue
        if not _mask_has_full_extent(mask):
            continue
        if _mask_connected(mask) != want_connected:
            continue
        if not _mask_asymmetric(mask):
            continue
        return mask

    # Deterministic fallbacks are unreachable in the normal keyed census but
    # make the requested contract total rather than probabilistic.
    if side == 3 and want_connected:
        return [[True, True, False],
                [False, True, True],
                [True, True, False]]
    if side == 3:
        return [[True, False, True],
                [False, True, False],
                [True, True, False]]
    if want_connected:
        return [[True, True, False, False],
                [False, True, True, False],
                [True, True, False, True],
                [False, True, True, True]]
    return [[True, False, True, True],
            [False, True, False, False],
            [True, True, False, True],
            [False, False, True, False]]


def _palette_values(
    side: int,
    shape_color: int,
    profile: str,
    mask: list[list[bool]],
    layout: str,
    rng,
) -> list[list[int]]:
    nonshape = [color for color in range(1, 10) if color != shape_color]
    rng.shuffle(nonshape)
    distinct_nonshape = 7 if profile in ("seven_nonshape", "shape_filled") and side == 3 else 8
    if profile == "seven_nonshape":
        distinct_nonshape = 7
    elif profile == "eight_nonshape":
        distinct_nonshape = 8
    chosen = nonshape[:distinct_nonshape]

    fixed_shape_position: tuple[int, int] | None = None
    if profile == "shape_filled":
        if layout == "below":
            fixed_shape_position = next(
                (0, col) for col in range(side) if mask[0][col]
            )
        else:
            fixed_shape_position = next(
                (row, 0) for row in range(side) if mask[row][0]
            )

    free_count = side * side - (1 if fixed_shape_position is not None else 0)
    filler = [chosen[index % len(chosen)] for index in range(free_count)]
    rng.shuffle(filler)
    # Shuffling repeated values can in principle place all copies of a required
    # colour after an accidental truncation in a future edit.  Assert the exact
    # intended support here, close to construction.
    assert set(filler) == set(chosen)

    palette = full_grid(side, side, 0)
    iterator = iter(filler)
    for row in range(side):
        for col in range(side):
            if fixed_shape_position == (row, col):
                palette[row][col] = shape_color
            else:
                palette[row][col] = next(iterator)
    return palette


def _scheduled_canvas(profile: str) -> tuple[int, int]:
    height, width, _ = _CANONICAL_GRID_PROFILES[profile]
    return height, width


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(
            f"unknown override(s): {', '.join(unknown)}; valid axes: "
            f"{', '.join(AXES)}"
        )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    for axis, value in _default_controls(seed, sample_index, difficulty).items():
        if ctx.overrides.get(axis) is None:
            ctx.overrides[axis] = value

    side = ctx.draw_int("palette_size", 3, 4)
    block = ctx.draw_int("block_size", 3, 5)
    layout = ctx.draw_choice("layout", LAYOUTS)
    gap = ctx.draw_int("gap", 0, 1)
    palette_profile = ctx.draw_choice("palette_profile", PALETTE_PROFILES)
    mask_profile = ctx.draw_choice("mask_profile", MASK_PROFILES)

    profile = schedule_profile(seed, sample_index, difficulty=difficulty)
    height, width = _scheduled_canvas(profile)
    core = side * block
    if layout == "below":
        minimum_height = core + gap + side + 2
        minimum_width = core + 2
    else:
        minimum_height = core + 2
        minimum_width = core + gap + side + 2
    height = max(height, minimum_height)
    width = max(width, minimum_width)
    if height > 30 or width > 30:
        raise ValueError(
            f"requested controls need {height}x{width}, outside ARC's 30x30 cap"
        )

    # GenCtx draw salts intentionally omit difficulty.  Include the band in
    # the labels for within-profile randomness so easy/medium/hard are distinct
    # curricula without changing the observable six-axis contract.
    band_tag = str(difficulty if difficulty is not None else "unspecified")
    mask = _draw_mask(side, mask_profile, ctx.draw_rng(f"mask:{band_tag}"))
    shape_color = ctx.draw_rng(f"shape_color:{band_tag}").choice(list(range(1, 10)))
    palette = _palette_values(
        side,
        shape_color,
        palette_profile,
        mask,
        layout,
        ctx.draw_rng(f"palette:{band_tag}"),
    )

    placement_rng = ctx.draw_rng(f"placement:{band_tag}")
    if layout == "below":
        vertical_slack = height - (core + gap + side)
        shape_row = placement_rng.randint(1, vertical_slack - 1)
        shape_col = placement_rng.randint(1, width - core - 1)
        palette_row = shape_row + core + gap
        palette_col = shape_col + placement_rng.randint(0, core - side)
    else:
        horizontal_slack = width - (core + gap + side)
        shape_col = placement_rng.randint(1, horizontal_slack - 1)
        shape_row = placement_rng.randint(1, height - core - 1)
        palette_col = shape_col + core + gap
        palette_row = shape_row + placement_rng.randint(0, core - side)

    grid = full_grid(height, width, 0)
    for block_row in range(side):
        for block_col in range(side):
            if not mask[block_row][block_col]:
                continue
            row0 = shape_row + block_row * block
            col0 = shape_col + block_col * block
            for delta_row in range(block):
                for delta_col in range(block):
                    grid[row0 + delta_row][col0 + delta_col] = shape_color

    for row in range(side):
        for col in range(side):
            grid[palette_row + row][palette_col + col] = palette[row][col]
    return grid


def _grid_shape_errors(grid) -> tuple[int, int, list[str]]:
    if not isinstance(grid, list) or not grid:
        return 0, 0, ["empty grid"]
    if not all(isinstance(row, list) for row in grid) or not grid[0]:
        return 0, 0, ["grid rows must be nonempty lists"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return len(grid), width, ["ragged grid"]
    return len(grid), width, []


def _analyse(grid) -> dict[str, object]:
    height, width, errors = _grid_shape_errors(grid)
    if errors:
        raise ValueError(errors[0])
    if not (1 <= height <= 30 and 1 <= width <= 30):
        raise ValueError(f"grid shape {height}x{width} is outside ARC bounds")
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                raise ValueError(f"invalid ARC colour {value!r} at {(row, col)}")

    counts = Counter(value for row in grid for value in row if value != 0)
    if not counts:
        raise ValueError("missing shape and palette")
    maximum = max(counts.values())
    modes = [color for color, count in counts.items() if count == maximum]
    if len(modes) != 1:
        raise ValueError("shape colour must be uniquely most common")
    shape_color = modes[0]

    shape_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == shape_color
    ]
    palette_nonshape_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0 and value != shape_color
    ]
    if not palette_nonshape_cells:
        raise ValueError("missing non-shape palette cells")

    shape_row0 = min(row for row, _ in shape_cells)
    shape_col0 = min(col for _, col in shape_cells)
    shape_row1 = max(row for row, _ in shape_cells)
    shape_col1 = max(col for _, col in shape_cells)
    palette_row0 = min(row for row, _ in palette_nonshape_cells)
    palette_col0 = min(col for _, col in palette_nonshape_cells)
    palette_row1 = max(row for row, _ in palette_nonshape_cells)
    palette_col1 = max(col for _, col in palette_nonshape_cells)
    palette_height = palette_row1 - palette_row0 + 1
    palette_width = palette_col1 - palette_col0 + 1
    if palette_height != palette_width or palette_height not in (3, 4):
        raise ValueError(
            "palette bbox must be a square of side 3 or 4, got "
            f"{palette_height}x{palette_width}"
        )
    side = palette_height
    shape_height = shape_row1 - shape_row0 + 1
    shape_width = shape_col1 - shape_col0 + 1
    block_height = shape_height // side
    block_width = shape_width // side
    if block_height < 1 or block_width < 1:
        raise ValueError("shape bbox is too small for the palette dimensions")

    palette = [
        [grid[palette_row0 + row][palette_col0 + col] for col in range(side)]
        for row in range(side)
    ]
    if any(value == 0 for row in palette for value in row):
        raise ValueError("palette bbox must be densely nonzero")

    mask = []
    for block_row in range(side):
        values = []
        for block_col in range(side):
            sample_row = shape_row0 + block_row * block_height
            sample_col = shape_col0 + block_col * block_width
            if not (0 <= sample_row < height and 0 <= sample_col < width):
                raise ValueError("shape block sample lies outside the grid")
            values.append(grid[sample_row][sample_col] == shape_color)
        mask.append(values)

    return {
        "height": height,
        "width": width,
        "shape_color": shape_color,
        "shape_bbox": (shape_row0, shape_col0, shape_row1, shape_col1),
        "palette_bbox": (
            palette_row0,
            palette_col0,
            palette_row1,
            palette_col1,
        ),
        "palette_size": side,
        "block_height": block_height,
        "block_width": block_width,
        "palette": palette,
        "mask": mask,
    }


def observe_overrides(grid) -> dict[str, object]:
    analysis = _analyse(grid)
    side = int(analysis["palette_size"])
    block_height = int(analysis["block_height"])
    block_width = int(analysis["block_width"])
    if block_height != block_width:
        raise ValueError(
            f"generated block sizes are not square: {block_height}x{block_width}"
        )
    shape_row0, shape_col0, _, _ = analysis["shape_bbox"]
    palette_row0, palette_col0, _, _ = analysis["palette_bbox"]
    core = side * block_height
    if palette_row0 >= shape_row0 + core:
        layout = "below"
        gap = palette_row0 - (shape_row0 + core)
    elif palette_col0 >= shape_col0 + core:
        layout = "right"
        gap = palette_col0 - (shape_col0 + core)
    else:
        raise ValueError("palette is neither below nor right of the sampled core")

    palette = analysis["palette"]
    palette_colors = {value for row in palette for value in row}
    shape_color = int(analysis["shape_color"])
    if shape_color in palette_colors:
        palette_profile = "shape_filled"
    elif len(palette_colors) == 7:
        palette_profile = "seven_nonshape"
    elif len(palette_colors) == 8:
        palette_profile = "eight_nonshape"
    else:
        raise ValueError(
            f"palette has unsupported distinct-colour count {len(palette_colors)}"
        )

    mask = analysis["mask"]
    return {
        "palette_size": side,
        "block_size": block_height,
        "layout": layout,
        "gap": gap,
        "palette_profile": palette_profile,
        "mask_profile": "connected" if _mask_connected(mask) else "disconnected",
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    try:
        analysis = _analyse(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]

    errors: list[str] = []
    height = int(analysis["height"])
    width = int(analysis["width"])
    if height * width < 320:
        errors.append("canvas too small for the canonical large-field distribution")

    mask = analysis["mask"]
    if not any(value for row in mask for value in row):
        errors.append("shape mask has no filled block")
    if all(value for row in mask for value in row):
        errors.append("shape mask must include at least one empty block")
    if not _mask_has_full_extent(mask):
        errors.append("sampled shape mask must span every extreme row and column")

    palette = analysis["palette"]
    shape_color = int(analysis["shape_color"])
    palette_colors = {value for row in palette for value in row}
    nonshape_palette_colors = palette_colors - {shape_color}
    if len(nonshape_palette_colors) not in (7, 8):
        errors.append(
            "palette must contain exactly seven or eight non-shape colours, "
            f"found {len(nonshape_palette_colors)}"
        )

    requested: dict[str, object] = {}
    if isinstance(meta, dict):
        if isinstance(meta.get("overrides"), dict):
            requested.update(meta["overrides"])
        requested.update({axis: meta[axis] for axis in AXES if axis in meta})
    if requested:
        try:
            observed = observe_overrides(grid)
        except ValueError as exc:
            errors.append(f"cannot observe requested controls: {exc}")
        else:
            for axis, expected in requested.items():
                if axis in observed and observed[axis] != expected:
                    errors.append(
                        f"{axis} requested {expected!r}, observed {observed[axis]!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    profile = (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )
    if profile not in set(_CANONICAL_GRID_PROFILES.values()):
        reasons.append(
            f"grid profile {profile} is not one of the four canonical profiles"
        )
    return reasons


def rule_mirror(grid):
    """Independent Python mirror; selected Racket remains the authority."""
    analysis = _analyse(grid)
    side = int(analysis["palette_size"])
    palette = analysis["palette"]
    mask = analysis["mask"]
    return [
        [palette[row][col] if mask[row][col] else 0 for col in range(side)]
        for row in range(side)
    ]


def _rival_copy_palette(grid):
    analysis = _analyse(grid)
    return [list(row) for row in analysis["palette"]]


def _rival_largest_component_only(grid):
    analysis = _analyse(grid)
    mask = analysis["mask"]
    side = int(analysis["palette_size"])
    remaining = {
        (row, col)
        for row in range(side)
        for col in range(side)
        if mask[row][col]
    }
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        component = {start}
        queue = deque([start])
        remaining.remove(start)
        while queue:
            row, col = queue.popleft()
            for delta_row, delta_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = row + delta_row, col + delta_col
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    largest = max(components, key=lambda component: (len(component), -min(component)[0], -min(component)[1]))
    palette = analysis["palette"]
    return [
        [palette[row][col] if (row, col) in largest else 0 for col in range(side)]
        for row in range(side)
    ]


def _rival_drop_shape_color(grid):
    analysis = _analyse(grid)
    shape_color = int(analysis["shape_color"])
    return [
        [0 if value == shape_color else value for value in row]
        for row in rule_mirror(grid)
    ]


def _rival_transpose_mask(grid):
    analysis = _analyse(grid)
    side = int(analysis["palette_size"])
    palette = analysis["palette"]
    mask = analysis["mask"]
    return [
        [palette[row][col] if mask[col][row] else 0 for col in range(side)]
        for row in range(side)
    ]


def _rival_fixed_3x3(grid):
    intended = rule_mirror(grid)
    return [row[:3] for row in intended[:3]]


def _valid(grid) -> bool:
    return not self_check(grid)


def _witness_empty_mask_cell(grid) -> bool:
    if not _valid(grid):
        return False
    return any(not value for row in _analyse(grid)["mask"] for value in row)


def _witness_disconnected_mask(grid) -> bool:
    if not _valid(grid):
        return False
    return not _mask_connected(_analyse(grid)["mask"])


def _witness_shape_color_survives(grid) -> bool:
    if not _valid(grid):
        return False
    shape_color = int(_analyse(grid)["shape_color"])
    return any(value == shape_color for row in rule_mirror(grid) for value in row)


def _witness_four_by_four_output(grid) -> bool:
    return _valid(grid) and int(_analyse(grid)["palette_size"]) == 4


def _witness_asymmetric_mask(grid) -> bool:
    return _valid(grid) and _mask_asymmetric(_analyse(grid)["mask"])


SEMANTIC_WITNESSES: dict[str, Callable] = {
    "empty_mask_cell": _witness_empty_mask_cell,
    "disconnected_mask": _witness_disconnected_mask,
    "shape_color_survives": _witness_shape_color_survives,
    "four_by_four_output": _witness_four_by_four_output,
    "asymmetric_mask": _witness_asymmetric_mask,
}

SEMANTIC_RIVALS: dict[str, Callable] = {
    "copy_palette": _rival_copy_palette,
    "largest_component_only": _rival_largest_component_only,
    "drop_shape_color": _rival_drop_shape_color,
    "transpose_mask": _rival_transpose_mask,
    "fixed_3x3": _rival_fixed_3x3,
}

WITNESS_RIVALS = {
    "empty_mask_cell": ["copy_palette"],
    "disconnected_mask": ["largest_component_only"],
    "shape_color_survives": ["drop_shape_color"],
    "four_by_four_output": ["fixed_3x3"],
    "asymmetric_mask": ["transpose_mask"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # All canonical outputs omit the shape colour even though one canonical
    # input places it in the palette at a masked-out coordinate.
    "drop_shape_color": _rival_drop_shape_color,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every three-demo lesson to refute every named competitor."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")

    killed = {name: False for name in LESSON_COMPETITORS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output does not match the selected rule")
        for name, rival in LESSON_COMPETITORS.items():
            killed[name] = killed[name] or rival(demo["input"]) != expected

    for name, was_killed in killed.items():
        if not was_killed:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons
