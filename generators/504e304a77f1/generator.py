"""Curriculum generator for placing size-ranked objects into ranked frames.

Canonical rule
--------------
Split the non-zero cells into same-colour 4-connected components.  Hollow
rectangular outlines are frames; all other components are movable shapes.
Sort shapes by cell count, sort frames by interior area, and place each cropped
shape centred inside the frame of the same rank.  Keep the frame outlines and
erase the shapes' old locations.

The sampler deliberately contains two complementary strata:

* every fifth default draw is a 6x21 canonical-profile gallery with the same
  shared frame colour and the same 1/3/4 cell-count ladder as the task;
* the remaining draws broaden layout, pair count, colours, and include a
  bbox-area rank inversion that falsifies the tempting "rank by bbox" shortcut.

All declared axes are exact, recoverable from returned pixels, and constructively
placed; there is no retry/fallback path.
"""
from __future__ import annotations

from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "504e304a77f1"
TASK_ID = "504e304a77f1"
VERSION = "3.0.1"
RULE_HASH = "6c92d838a5dd"

SUMMARY = (
    "A zero-background grid contains 2-4 disconnected hollow rectangular "
    "frames in one shared colour and the same number of differently coloured "
    "ordinary shapes. Frame interior areas and shape cell counts are each "
    "strictly increasing. Rank shapes by cell count, rank frames by interior "
    "area, erase the old shapes, and centre each shape in its matching frame."
)

INVARIANTS = [
    "background is color 0",
    "2-4 hollow rectangular frames share one nonzero color",
    "ordinary components have distinct nonzero colors and distinct cell counts",
    "frame interior areas are distinct and every ranked shape fits its ranked frame",
    "ordinary components begin outside every frame",
]

AXES = {
    "n_pairs": {
        "type": "int",
        "default": "difficulty-aware deterministic schedule",
        "valid": "2..4",
    },
    "layout": {
        "type": "str",
        "default": "alternating gallery/scattered schedule",
        "valid": "gallery|scattered",
    },
    "frame_color": {
        "type": "color",
        "default": "keyed color draw",
        "valid": "1..9",
    },
    "bbox_rank_inversion": {
        "type": "bool",
        "default": "false in canonical core, true in broad curriculum",
        "valid": "false|true",
    },
}

# Every Cartesian combination of the four exact axes is constructively valid.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# The task's real examples cannot distinguish cell-count ranking from bbox-area
# ranking; generated broad examples must do that work.
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.99
LESSON_SCHEDULE_PERIOD = 5
SCHEDULE_PROFILES = ("core", "broad")


# ---------------------------------------------------------------------------
# Geometry and component analysis
# ---------------------------------------------------------------------------

Cell = tuple[int, int]
Shape = tuple[Cell, ...]


def _copy_grid(grid):
    return [list(row) for row in grid]


def _bbox(cells: list[Cell] | tuple[Cell, ...]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_dims(cells: list[Cell] | tuple[Cell, ...]) -> tuple[int, int]:
    r0, c0, r1, c1 = _bbox(cells)
    return r1 - r0 + 1, c1 - c0 + 1


def _normalise(cells: list[Cell] | tuple[Cell, ...]) -> Shape:
    r0, c0, _, _ = _bbox(cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _flip_shape(shape: Shape, *, flip_rows: bool, flip_cols: bool) -> Shape:
    height, width = _bbox_dims(shape)
    cells = [
        (
            height - 1 - r if flip_rows else r,
            width - 1 - c if flip_cols else c,
        )
        for r, c in shape
    ]
    return _normalise(cells)


def _frame_outline(height: int, width: int) -> Shape:
    if height < 3 or width < 3:
        raise ValueError("a hollow frame needs both dimensions >= 3")
    return tuple(
        (r, c)
        for r in range(height)
        for c in range(width)
        if r in (0, height - 1) or c in (0, width - 1)
    )


def _components(grid) -> list[dict[str, object]]:
    """Return row-major same-colour 4-connected non-background components."""
    height, width = len(grid), len(grid[0])
    unseen = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] != 0
    }
    parts: list[dict[str, object]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        colour = grid[start[0]][start[1]]
        stack = [start]
        cells: list[Cell] = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for nr, nc in ((r - 1, c), (r, c - 1), (r, c + 1), (r + 1, c)):
                point = (nr, nc)
                if point in unseen and grid[nr][nc] == colour:
                    unseen.remove(point)
                    stack.append(point)
        cells.sort()
        parts.append(
            {
                "color": colour,
                "cells": cells,
                "bbox": _bbox(cells),
                "size": len(cells),
            }
        )
    parts.sort(key=lambda part: (part["bbox"][0], part["bbox"][1]))
    return parts


def _is_frame(cells: list[Cell] | tuple[Cell, ...]) -> bool:
    r0, c0, r1, c1 = _bbox(cells)
    if r1 - r0 < 2 or c1 - c0 < 2:
        return False
    expected = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    return set(cells) == expected


def _interior_area(part: dict[str, object]) -> int:
    r0, c0, r1, c1 = part["bbox"]
    return (r1 - r0 - 1) * (c1 - c0 - 1)


def _bbox_area(part: dict[str, object]) -> int:
    r0, c0, r1, c1 = part["bbox"]
    return (r1 - r0 + 1) * (c1 - c0 + 1)


def _bbox_sort_tie(part: dict[str, object]) -> tuple[int, int]:
    # Matches the selected Racket rule's bbox< comparator: column, then row.
    r0, c0, _, _ = part["bbox"]
    return c0, r0


def _overlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    ar0, ac0, ar1, ac1 = a
    br0, bc0, br1, bc1 = b
    return not (ar1 < br0 or br1 < ar0 or ac1 < bc0 or bc1 < ac0)


def _analyse(grid) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    parts = _components(grid)
    frames = [part for part in parts if _is_frame(part["cells"])]
    movers = [part for part in parts if not _is_frame(part["cells"])]
    return frames, movers


# ---------------------------------------------------------------------------
# Reference transforms and semantic rival
# ---------------------------------------------------------------------------


def _paint_component(grid, part: dict[str, object]) -> None:
    colour = part["color"]
    for r, c in part["cells"]:
        grid[r][c] = colour


def _crop_cells(part: dict[str, object]) -> Shape:
    r0, c0, _, _ = part["bbox"]
    return tuple(sorted((r - r0, c - c0) for r, c in part["cells"]))


def _solve_ranked(grid, key: Callable[[dict[str, object]], int]):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid frame-ranking instance: " + "; ".join(errors))
    frames, movers = _analyse(grid)
    frames = sorted(frames, key=lambda part: (_interior_area(part), *_bbox_sort_tie(part)))
    movers = sorted(movers, key=lambda part: (key(part), *_bbox_sort_tie(part)))

    out = full_grid(len(grid), len(grid[0]), 0)
    for frame in frames:
        _paint_component(out, frame)

    for frame, mover in zip(frames, movers):
        shape = _crop_cells(mover)
        shape_h, shape_w = _bbox_dims(shape)
        r0, c0, r1, c1 = frame["bbox"]
        interior_h = r1 - r0 - 1
        interior_w = c1 - c0 - 1
        top = r0 + 1 + (interior_h - shape_h) // 2
        left = c0 + 1 + (interior_w - shape_w) // 2
        colour = mover["color"]
        for dr, dc in shape:
            out[top + dr][left + dc] = colour
    return out


def _solve_by_size(grid):
    """Python mirror of the selected cell-count-ranking rule."""
    return _solve_ranked(grid, lambda part: part["size"])


def _bbox_area_rival(grid):
    """Plausible shortcut: rank ordinary components by bounding-box area."""
    return _solve_ranked(grid, _bbox_area)


# ---------------------------------------------------------------------------
# Constructive sample families
# ---------------------------------------------------------------------------

# Canonical-like ladder: cell counts 1,3,4,6 and bbox areas 1,4,6,9.
_STANDARD_SHAPES: tuple[Shape, ...] = (
    ((0, 0),),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 1), (2, 2)),
)

# Cell counts 5,6,8,9 but bbox areas 9,6,8,10.  Thus the first two swap
# under bbox-area ranking while every shape still fits its cell-count-ranked
# frame.
_INVERSION_SHAPES: tuple[Shape, ...] = (
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    tuple((r, c) for r in range(2) for c in range(3)),
    tuple((r, c) for r in range(2) for c in range(4)),
    tuple((r, c) for r in range(2) for c in range(5) if (r, c) != (0, 3)),
)

_STANDARD_INTERIORS = ((1, 1), (2, 2), (3, 3), (4, 4))
_INVERSION_INTERIORS = ((3, 3), (3, 4), (4, 4), (4, 5))


def _put_shape(grid, top: int, left: int, shape: Shape, colour: int) -> None:
    height, width = len(grid), len(grid[0])
    for dr, dc in shape:
        r, c = top + dr, left + dc
        if not (0 <= r < height and 0 <= c < width):
            raise RuntimeError("constructive placement escaped the canvas")
        if grid[r][c] != 0:
            raise RuntimeError("constructive placement collided")
        grid[r][c] = colour


def _place_core(
    shapes: list[Shape],
    object_colours: tuple[int, ...],
    frame_colour: int,
):
    """Return the 6x21 canonical-profile stratum (always exactly three pairs)."""
    grid = full_grid(6, 21, 0)

    # Same dimensions and gallery rhythm as the canonical examples.
    frame_lefts = (7, 11, 16)
    for (inner_h, inner_w), left in zip(_STANDARD_INTERIORS[:3], frame_lefts):
        _put_shape(
            grid,
            0,
            left,
            _frame_outline(inner_h + 2, inner_w + 2),
            frame_colour,
        )

    # Three separated source slots in the left six columns.
    source_positions = ((0, 0), (1, 3), (3, 1))
    for shape, colour, (top, left) in zip(shapes, object_colours, source_positions):
        _put_shape(grid, top, left, shape, colour)
    return grid


def _place_gallery(
    shapes: list[Shape],
    interiors: list[tuple[int, int]],
    object_colours: tuple[int, ...],
    frame_colour: int,
    rng,
):
    """Frames in a top gallery and source shapes in a separate bottom gallery."""
    grid = full_grid(12, 30, 0)
    count = len(shapes)

    frame_order = list(range(count))
    object_order = list(range(count))
    rng.shuffle(frame_order)
    rng.shuffle(object_order)

    frame_widths = [interiors[index][1] + 2 for index in frame_order]
    total_frame_width = sum(frame_widths) + count - 1
    left = (30 - total_frame_width) // 2
    for index, width in zip(frame_order, frame_widths):
        inner_h, inner_w = interiors[index]
        _put_shape(
            grid,
            1,
            left,
            _frame_outline(inner_h + 2, inner_w + 2),
            frame_colour,
        )
        left += width + 1

    object_widths = [_bbox_dims(shapes[index])[1] for index in object_order]
    total_object_width = sum(object_widths) + 2 * (count - 1)
    left = (30 - total_object_width) // 2
    for index, width in zip(object_order, object_widths):
        _put_shape(grid, 8, left, shapes[index], object_colours[index])
        left += width + 2
    return grid


def _place_scattered(
    shapes: list[Shape],
    interiors: list[tuple[int, int]],
    object_colours: tuple[int, ...],
    frame_colour: int,
    rng,
):
    """Interleave frames and shapes across a 2x2 tile field.

    Both semantic categories span both axes, so no single horizontal or
    vertical cut separates all frames from all source shapes.
    """
    grid = full_grid(16, 28, 0)
    count = len(shapes)
    tile_origins = ((0, 0), (0, 14), (8, 0), (8, 14))
    selected = {2: (0, 3), 3: (0, 1, 2), 4: (0, 1, 2, 3)}[count]

    frame_order = list(range(count))
    object_order = list(range(count))
    rng.shuffle(frame_order)
    rng.shuffle(object_order)

    for slot, frame_index, object_index in zip(selected, frame_order, object_order):
        base_r, base_c = tile_origins[slot]
        inner_h, inner_w = interiors[frame_index]
        _put_shape(
            grid,
            base_r + 1,
            base_c + 1,
            _frame_outline(inner_h + 2, inner_w + 2),
            frame_colour,
        )
        _put_shape(
            grid,
            base_r + 2,
            base_c + 9,
            shapes[object_index],
            object_colours[object_index],
        )
    return grid


def _validate_overrides(overrides: dict[str, object]) -> dict[str, object]:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    supplied = {name: value for name, value in overrides.items() if value is not None}
    if "n_pairs" in supplied:
        value = supplied["n_pairs"]
        if type(value) is not int:
            raise TypeError("n_pairs must be an integer, not bool or another type")
        if not 2 <= value <= 4:
            raise ValueError("n_pairs must be in 2..4")
    if "layout" in supplied:
        value = supplied["layout"]
        if type(value) is not str:
            raise TypeError("layout must be a string")
        if value not in ("gallery", "scattered"):
            raise ValueError("layout must be 'gallery' or 'scattered'")
    if "frame_color" in supplied:
        value = supplied["frame_color"]
        if type(value) is not int:
            raise TypeError("frame_color must be an integer color, not bool")
        if not 1 <= value <= 9:
            raise ValueError("frame_color must be in 1..9")
    if "bbox_rank_inversion" in supplied:
        value = supplied["bbox_rank_inversion"]
        if type(value) is not bool:
            raise TypeError("bbox_rank_inversion must be bool")
    return supplied


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return "core" if sample_index % LESSON_SCHEDULE_PERIOD == 0 else "broad"


def _scheduled_pair_count(sample_index: int, difficulty) -> int:
    residue = sample_index % 4
    if difficulty == "easy":
        return (2, 2, 3, 2)[residue]
    if difficulty == "hard":
        return (3, 4, 4, 4)[residue]
    return (2, 3, 4, 3)[residue]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    supplied = _validate_overrides(overrides)

    # An explicit caller request always enters the broad constructive family.
    # Default residue 0 is reserved for the canonical-profile anchor.
    core = schedule_profile(seed, sample_index, difficulty) == "core" and not supplied
    effective = dict(supplied)
    if core:
        effective.update(
            {
                "n_pairs": 3,
                "layout": "gallery",
                "frame_color": 5,
                "bbox_rank_inversion": False,
            }
        )
    else:
        effective.setdefault("n_pairs", _scheduled_pair_count(sample_index, difficulty))
        effective.setdefault("layout", "gallery" if sample_index % 2 == 0 else "scattered")
        effective.setdefault("bbox_rank_inversion", True)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    count = ctx.draw_int_strict("n_pairs", 2, 4)
    layout = ctx.draw_choice("layout", ("gallery", "scattered"))
    frame_colour = ctx.draw_color("frame_color", exclude={0})
    inversion = ctx.draw_choice("bbox_rank_inversion", (False, True))

    object_colours = ctx.draw_distinct_colors(
        "object_colors", n=count, exclude={0, frame_colour}
    )
    source_shapes = _INVERSION_SHAPES if inversion else _STANDARD_SHAPES
    source_interiors = _INVERSION_INTERIORS if inversion else _STANDARD_INTERIORS
    orientation_rng = ctx.draw_rng("shape_orientations")
    shapes = [
        _flip_shape(
            source_shapes[index],
            flip_rows=bool(orientation_rng.getrandbits(1)),
            flip_cols=bool(orientation_rng.getrandbits(1)),
        )
        for index in range(count)
    ]
    interiors = list(source_interiors[:count])

    if core:
        grid = _place_core(shapes, object_colours, frame_colour)
    elif layout == "gallery":
        grid = _place_gallery(
            shapes,
            interiors,
            object_colours,
            frame_colour,
            ctx.draw_rng("gallery_order"),
        )
    else:
        grid = _place_scattered(
            shapes,
            interiors,
            object_colours,
            frame_colour,
            ctx.draw_rng("scattered_order"),
        )

    expected = {
        "n_pairs": count,
        "layout": layout,
        "frame_color": frame_colour,
        "bbox_rank_inversion": inversion,
    }
    errors = self_check(grid)
    if errors:
        raise RuntimeError("constructive generator violated its invariant: " + "; ".join(errors))
    observed = observe_overrides(grid)
    if observed != expected:
        raise RuntimeError(f"constructed axes differ from requested axes: {observed!r} != {expected!r}")
    return grid


# ---------------------------------------------------------------------------
# Validation and exact-axis observation
# ---------------------------------------------------------------------------


def _grid_shape_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors in 0..9"]
    return []


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    errors = _grid_shape_errors(grid)
    if errors:
        return errors

    frames, movers = _analyse(grid)
    if not 2 <= len(frames) <= 4:
        errors.append(f"expected 2-4 hollow frames, found {len(frames)}")
    if len(movers) != len(frames):
        errors.append(
            f"expected one ordinary component per frame, found {len(movers)} ordinary and {len(frames)} frames"
        )
    if not frames:
        return errors

    frame_colours = {part["color"] for part in frames}
    if len(frame_colours) != 1:
        errors.append("all frames must share one color")
    frame_colour = next(iter(frame_colours))
    if frame_colour == 0:
        errors.append("frame color must be nonzero")

    mover_colours = [part["color"] for part in movers]
    if len(mover_colours) != len(set(mover_colours)):
        errors.append("ordinary components must have distinct colors")
    if frame_colour in mover_colours:
        errors.append("ordinary component colors must differ from the frame color")

    frame_areas = [_interior_area(part) for part in frames]
    if len(frame_areas) != len(set(frame_areas)):
        errors.append("frame interior areas must be distinct")
    mover_sizes = [part["size"] for part in movers]
    if len(mover_sizes) != len(set(mover_sizes)):
        errors.append("ordinary component cell counts must be distinct")

    for mover in movers:
        if any(_overlap(mover["bbox"], frame["bbox"]) for frame in frames):
            errors.append("ordinary components must begin outside every frame")
            break

    if len(frames) == len(movers):
        ranked_frames = sorted(
            frames, key=lambda part: (_interior_area(part), *_bbox_sort_tie(part))
        )
        ranked_movers = sorted(
            movers, key=lambda part: (part["size"], *_bbox_sort_tie(part))
        )
        for rank, (frame, mover) in enumerate(zip(ranked_frames, ranked_movers), 1):
            r0, c0, r1, c1 = frame["bbox"]
            interior_h, interior_w = r1 - r0 - 1, c1 - c0 - 1
            shape_h, shape_w = _bbox_dims(mover["cells"])
            if shape_h > interior_h or shape_w > interior_w:
                errors.append(
                    f"rank-{rank} ordinary shape {shape_h}x{shape_w} does not fit frame interior {interior_h}x{interior_w}"
                )
    return errors


def _axis_separated(frames, movers) -> bool:
    frame_boxes = [part["bbox"] for part in frames]
    mover_boxes = [part["bbox"] for part in movers]
    return any(
        (
            max(box[edge_max] for box in frame_boxes)
            < min(box[edge_min] for box in mover_boxes)
        )
        or (
            max(box[edge_max] for box in mover_boxes)
            < min(box[edge_min] for box in frame_boxes)
        )
        for edge_min, edge_max in ((0, 2), (1, 3))
    )


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe axes on invalid grid: " + "; ".join(errors))
    frames, movers = _analyse(grid)
    frame_colour = frames[0]["color"]
    by_size = [
        part["color"]
        for part in sorted(movers, key=lambda part: (part["size"], *_bbox_sort_tie(part)))
    ]
    by_bbox = [
        part["color"]
        for part in sorted(movers, key=lambda part: (_bbox_area(part), *_bbox_sort_tie(part)))
    ]
    return {
        "n_pairs": len(frames),
        "layout": "gallery" if _axis_separated(frames, movers) else "scattered",
        "frame_color": frame_colour,
        "bbox_rank_inversion": by_size != by_bbox,
    }


def strict_canonical_like(grid):
    return self_check(grid)


# ---------------------------------------------------------------------------
# Task-linked semantic contract
# ---------------------------------------------------------------------------


def _has_bbox_rank_inversion(grid) -> bool:
    return observe_overrides(grid)["bbox_rank_inversion"]


SEMANTIC_WITNESSES = {"cell_count_not_bbox_area": _has_bbox_rank_inversion}
SEMANTIC_RIVALS = {"bbox_area_rank": _bbox_area_rival}
WITNESS_RIVALS = {"cell_count_not_bbox_area": ["bbox_area_rank"]}
CANONICAL_SHORTCUTS = {"bbox_area_rank": _bbox_area_rival}
LESSON_COMPETITORS = {"bbox_area_rank": _bbox_area_rival}


def lesson_identifiable(demos, query) -> list[str]:
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    for label, pair in [
        *((f"demo {index}", pair) for index, pair in enumerate(demos)),
        ("query", query),
    ]:
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{label} must contain input and output grids")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"{label} input is unlawful: {errors[0]}")
            continue
        if pair["output"] != _solve_by_size(pair["input"]):
            reasons.append(f"{label} output disagrees with cell-count ranking")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if survives and rival(query["input"]) != query["output"]:
            reasons.append(f"demos do not refute rival rule: {name}")
    return reasons
