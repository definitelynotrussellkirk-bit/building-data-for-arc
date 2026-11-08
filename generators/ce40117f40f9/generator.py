"""Generator for arc_puzzle_bank_thirteenth21:M85 — move blob to 9-marker.

Rule: the input contains one maroon (9) marker and one monochrome,
4-connected non-{0, 9} blob.  Crop the blob to its tight bounding box and
paste that crop onto a fresh zero canvas with the crop's top-left corner at
the marker.

The generator deliberately varies the marker's diagonal direction relative
to the source blob.  This prevents a lesson from teaching the accidental
shortcut "the marker is always southeast of the object".
"""
from __future__ import annotations

from collections import deque
from math import ceil, sqrt
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ce40117f40f9"
VERSION = "2.1.0"
TASK_ID = "ce40117f40f9"
SUMMARY = (
    "A 6-30 by 6-30 zero-background grid contains exactly one monochrome, "
    "4-connected blob of 2-6 cells and exactly one color-9 marker. Crop the "
    "blob to its tight bounding box, clear the canvas, and paste the crop "
    "with its top-left corner at the marker. Marker direction varies across "
    "all four diagonal quadrants."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one color-9 marker cell",
    "exactly one monochrome 4-connected non-{0, 9} blob (2-6 cells)",
    "the marker lies outside the source blob bounding box",
    "the blob crop fits in-bounds when its top-left is placed at the marker",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "no_blob", "marker_on_blob")
HELPFUL_TEXTURES = PALETTE_KINDS
POSITION_BIASES = (
    "marker_southeast",
    "marker_northwest",
    "marker_northeast",
    "marker_southwest",
)
# Retain the historical explicit override as a compatibility alias, but never
# schedule it by default.
_POSITION_ALIASES = {
    "blob_upper_left_marker_lower_right": "marker_southeast",
}

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware rng", "valid": "6..30"},
    "grid_w": {"type": "int", "default": "difficulty-aware rng", "valid": "6..30"},
    "palette_kind": {
        "type": "str",
        "default": "rng helpful",
        "valid": "|".join(PALETTE_KINDS),
    },
    "blob_size": {"type": "int", "default": "difficulty-aware rng 2..6", "valid": "2..6"},
    "palette_size": {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias": {
        "type": "str",
        "default": "cycles over all four diagonal marker directions",
        "valid": "|".join(POSITION_BIASES + tuple(_POSITION_ALIASES)),
    },
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density": {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture": {
        "type": "str",
        "default": "optional alias for palette_kind",
        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES),
    },
}


def _four_connected(points: set[tuple[int, int]]) -> bool:
    if not points:
        return False
    seen = {next(iter(points))}
    queue = deque(seen)
    while queue:
        row, column = queue.popleft()
        for neighbor in (
            (row - 1, column),
            (row + 1, column),
            (row, column - 1),
            (row, column + 1),
        ):
            if neighbor in points and neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen == points


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return structural-domain errors for a candidate generator input."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty grid"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return ["grid rows must be sequences"]
    if not grid[0]:
        return ["empty grid"]

    height, width = len(grid), len(grid[0])
    if any(len(row) != width for row in grid):
        return ["ragged grid"]

    errors: list[str] = []
    if not (6 <= height <= 30 and 6 <= width <= 30):
        errors.append(f"grid dimensions must each be in 6..30; found {height}x{width}")

    bad_cells = [
        (row, column, value)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if type(value) is not int or not (0 <= value <= 9)
    ]
    if bad_cells:
        errors.append("every cell must be a literal integer in 0..9 (not bool)")
        return errors

    markers = [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == 9
    ]
    if len(markers) != 1:
        errors.append(f"expected exactly 1 color-9 marker; found {len(markers)}")

    blob_cells = [
        (row, column, value)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value not in (0, 9)
    ]
    if not (2 <= len(blob_cells) <= 6):
        errors.append(f"expected 2..6 non-marker blob cells; found {len(blob_cells)}")
        return errors

    colors = {value for _, _, value in blob_cells}
    if len(colors) != 1:
        errors.append(f"expected a monochrome blob; found colors {sorted(colors)}")

    points = {(row, column) for row, column, _ in blob_cells}
    if not _four_connected(points):
        errors.append("non-marker cells must form one 4-connected blob")

    if len(markers) == 1:
        marker_row, marker_column = markers[0]
        rows = [row for row, _, _ in blob_cells]
        columns = [column for _, column, _ in blob_cells]
        top, bottom = min(rows), max(rows)
        left, right = min(columns), max(columns)
        blob_height = bottom - top + 1
        blob_width = right - left + 1
        if top <= marker_row <= bottom and left <= marker_column <= right:
            errors.append("marker must lie outside the source blob bounding box")
        if marker_row + blob_height > height or marker_column + blob_width > width:
            errors.append("blob crop would leave the grid when pasted at the marker")

    return errors


def _draw_axis_int(ctx, overrides, label: str, *, default_lo: int, default_hi: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int_strict(label, default_lo, default_hi)


def _validate_difficulty(difficulty) -> str | None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    return difficulty


def _connected_shape(rng, size: int) -> tuple[tuple[int, int], ...]:
    """Construct exactly ``size`` cells in a compact 4-connected polyomino."""
    side = max(2, min(3, ceil(sqrt(size))))
    cells = {(rng.randrange(side), rng.randrange(side))}
    while len(cells) < size:
        frontier = sorted(
            {
                neighbor
                for row, column in cells
                for neighbor in (
                    (row - 1, column),
                    (row + 1, column),
                    (row, column - 1),
                    (row, column + 1),
                )
                if 0 <= neighbor[0] < side
                and 0 <= neighbor[1] < side
                and neighbor not in cells
            }
        )
        if not frontier:
            raise AssertionError("compact shape growth exhausted unexpectedly")
        cells.add(rng.choice(frontier))

    min_row = min(row for row, _ in cells)
    min_column = min(column for _, column in cells)
    return tuple(sorted((row - min_row, column - min_column) for row, column in cells))


def _bbox_disjoint(
    first: tuple[int, int, int, int], second: tuple[int, int, int, int]
) -> bool:
    first_top, first_left, first_bottom, first_right = first
    second_top, second_left, second_bottom, second_right = second
    return (
        first_bottom < second_top
        or second_bottom < first_top
        or first_right < second_left
        or second_right < first_left
    )


def _matches_direction(
    position_bias: str,
    source: tuple[int, int, int, int],
    marker_row: int,
    marker_column: int,
) -> bool:
    top, left, bottom, right = source
    return {
        "marker_southeast": marker_row > bottom and marker_column > right,
        "marker_northwest": marker_row < top and marker_column < left,
        "marker_northeast": marker_row < top and marker_column > right,
        "marker_southwest": marker_row > bottom and marker_column < left,
    }[position_bias]


def _placement_candidates(
    height: int,
    width: int,
    blob_height: int,
    blob_width: int,
    position_bias: str,
) -> list[tuple[int, int, int, int]]:
    candidates: list[tuple[int, int, int, int]] = []
    for source_row in range(height - blob_height + 1):
        for source_column in range(width - blob_width + 1):
            source_box = (
                source_row,
                source_column,
                source_row + blob_height - 1,
                source_column + blob_width - 1,
            )
            for marker_row in range(height - blob_height + 1):
                for marker_column in range(width - blob_width + 1):
                    destination_box = (
                        marker_row,
                        marker_column,
                        marker_row + blob_height - 1,
                        marker_column + blob_width - 1,
                    )
                    if not _bbox_disjoint(source_box, destination_box):
                        continue
                    if not _matches_direction(
                        position_bias, source_box, marker_row, marker_column
                    ):
                        continue
                    candidates.append(
                        (source_row, source_column, marker_row, marker_column)
                    )
    return candidates


def _palette(palette_kind: str) -> tuple[int, ...]:
    return {
        "default": (2, 3, 4, 5, 6, 7, 8),
        "warm": (2, 4, 6, 7),
        "cool": (1, 3, 8),
        "varied": (1, 2, 3, 4, 5, 6, 7, 8),
    }[palette_kind]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")
    difficulty = _validate_difficulty(difficulty)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if difficulty == "easy":
        dim_band = (7, 9)
        blob_band = (2, 3)
    elif difficulty == "hard":
        dim_band = (12, 20)
        blob_band = (4, 6)
    else:
        dim_band = (8, 14)
        blob_band = (2, 5)

    height = _draw_axis_int(
        ctx, overrides, "grid_h", default_lo=dim_band[0], default_hi=dim_band[1], lo=6, hi=30
    )
    width = _draw_axis_int(
        ctx, overrides, "grid_w", default_lo=dim_band[0], default_hi=dim_band[1], lo=6, hi=30
    )
    blob_size = _draw_axis_int(
        ctx, overrides, "blob_size", default_lo=blob_band[0], default_hi=blob_band[1], lo=2, hi=6
    )

    # Fixed axes remain explicit so every accepted override is consumed and
    # provenance tools can see the exact contract.
    ctx.draw_int_strict("palette_size", 2, 2)
    ctx.draw_int_strict("n_distinct_colors", 2, 2)
    ctx.draw_choice("density", ("sparse",))

    texture = None
    if "texture" in overrides and overrides["texture"] is not None:
        texture = ctx.draw_choice("texture", HELPFUL_TEXTURES + DEGENERATE_TEXTURES)

    if texture in HELPFUL_TEXTURES:
        if (
            "palette_kind" in overrides
            and overrides["palette_kind"] is not None
            and overrides["palette_kind"] != texture
        ):
            raise ValueError(
                f"texture={texture!r} conflicts with palette_kind={overrides['palette_kind']!r}"
            )
        palette_kind = ctx.draw_choice("palette_kind", (texture,))
    else:
        palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)

    if "position_bias" in overrides and overrides["position_bias"] is not None:
        raw_position_bias = ctx.draw_choice(
            "position_bias", POSITION_BIASES + tuple(_POSITION_ALIASES)
        )
    else:
        raw_position_bias = ctx.draw_choice(
            "position_bias", (POSITION_BIASES[int(sample_index) % len(POSITION_BIASES)],)
        )
    position_bias = _POSITION_ALIASES.get(raw_position_bias, raw_position_bias)

    layout_rng = ctx.draw_rng("layout")
    color_rng = ctx.draw_rng("blob_color")
    blob_color = color_rng.choice(_palette(palette_kind))

    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, height, width, blob_color)

    shape = _connected_shape(layout_rng, blob_size)
    blob_height = max(row for row, _ in shape) + 1
    blob_width = max(column for _, column in shape) + 1
    candidates = _placement_candidates(
        height, width, blob_height, blob_width, position_bias
    )
    if not candidates:
        raise ValueError(
            "requested grid/blob/direction combination has no disjoint legal placement: "
            f"grid={height}x{width}, blob_bbox={blob_height}x{blob_width}, "
            f"position_bias={position_bias}"
        )

    source_row, source_column, marker_row, marker_column = layout_rng.choice(candidates)
    grid = full_grid(height, width, 0)
    for row, column in shape:
        grid[source_row + row][source_column + column] = blob_color
    grid[marker_row][marker_column] = 9

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid move-to-marker scene: " + "; ".join(errors))
    return grid


def _draw_from_degenerate(name: str, height: int, width: int, color: int):
    grid = full_grid(height, width, 0)
    if name == "no_marker":
        grid[1][1] = color
        grid[1][2] = color
        grid[2][1] = color
        return grid
    if name == "no_blob":
        grid[height - 2][width - 2] = 9
        return grid
    if name == "marker_on_blob":
        grid[1][1] = 9
        grid[1][2] = color
        grid[2][1] = color
        return grid
    raise ValueError(f"unknown degenerate texture: {name!r}")
