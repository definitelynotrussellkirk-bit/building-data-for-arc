"""Generate dense 9-bars split by a central stripe of nuisance-color cells.

Every object is a filled 2:1 rectangle.  Its sparse non-9 stripe selects one
of the two central cells in each short-axis lane.  The canonical rule clears
the scene and moves every 9 one cell outward from its object's long-axis
split.  Complete public 1/3/4/7-object layouts remain common; extrapolation
profiles vary scale and placement without changing the answer-bearing bar
morphology.
"""

from __future__ import annotations

from collections import Counter
from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "6b5d8752c5c4"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "1eb213be2892"

SUMMARY = (
    "Find every nonzero 8-connected object, split its bounding box across "
    "the longer axis, and return only its color-9 cells shifted one cell "
    "outward from that split."
)
INVARIANTS = [
    "the canvas is square, 8..22 cells on a side, with background 0",
    "every nonzero object is a completely filled 2:1 rectangle",
    "color 9 is the dense body and one shared color 1..8 is the cut stripe",
    "each short-axis lane has exactly one cut cell in the central pair",
    "all shifted 9 cells remain in bounds and distinct",
    "the complete canvas/object-count/shape relation is one scene profile",
]

PUBLIC_PROFILES = (
    "public_12",
    "public_8",
    "public_16",
    "public_19",
)
EXTRAPOLATION_PROFILES = (
    "single_bar",
    "paired_bars",
    "edge_bars",
    "mixed_bars",
)
SCENE_PROFILES = PUBLIC_PROFILES + EXTRAPOLATION_PROFILES

_PUBLIC_PROFILE_INDEX = {
    profile: index for index, profile in enumerate(PUBLIC_PROFILES)
}
_PUBLIC_LAYOUTS = {
    "public_12": {
        "canvas": 12,
        "boxes": (
            (2, 4, 3, 6),
            (7, 1, 3, 6),
            (7, 9, 4, 2),
        ),
        "cut_masks": (
            ((0, 2), (1, 3), (2, 2)),
            ((0, 3), (1, 2), (2, 3)),
            ((1, 1), (2, 0)),
        ),
        "edge_count": 0,
    },
    "public_8": {
        "canvas": 8,
        "boxes": ((1, 1, 6, 3),),
        "cut_masks": (((2, 0), (2, 2), (3, 1)),),
        "edge_count": 0,
    },
    "public_16": {
        "canvas": 16,
        "boxes": (
            (2, 6, 2, 4),
            (2, 12, 8, 4),
            (4, 2, 4, 2),
            (11, 2, 4, 8),
        ),
        "cut_masks": (
            ((0, 2), (1, 1)),
            ((3, 1), (3, 3), (4, 0), (4, 2)),
            ((1, 0), (2, 1)),
            ((0, 4), (1, 3), (2, 4), (3, 3)),
        ),
        "edge_count": 1,
    },
    "public_19": {
        "canvas": 19,
        "boxes": (
            (0, 3, 2, 4),
            (1, 10, 3, 6),
            (5, 2, 10, 5),
            (6, 8, 12, 6),
            (7, 17, 4, 2),
            (14, 17, 4, 2),
            (17, 2, 2, 4),
        ),
        "cut_masks": (
            ((0, 1), (1, 2)),
            ((0, 2), (1, 3), (2, 2)),
            ((4, 1), (4, 3), (5, 0), (5, 2), (5, 4)),
            ((5, 0), (5, 2), (5, 4), (6, 1), (6, 3), (6, 5)),
            ((1, 1), (2, 0)),
            ((1, 0), (2, 1)),
            ((0, 2), (1, 1)),
        ),
        "edge_count": 4,
    },
}
_EXTRAPOLATION_CANVASES = {
    "single_bar": (9, 11, 13),
    "paired_bars": (14, 15, 17),
    "edge_bars": (18, 20),
    "mixed_bars": (21, 22),
}

_PROFILE_OPTIONS = {
    "easy": (
        ("public_12",) * 3
        + ("public_8",) * 4
        + ("public_16",) * 2
        + ("public_19",)
        + ("single_bar",) * 12
        + ("paired_bars",) * 9
        + ("edge_bars",) * 4
        + ("mixed_bars",) * 5
    ),
    "medium": (
        ("public_12",) * 3
        + ("public_8",) * 2
        + ("public_16",) * 3
        + ("public_19",) * 2
        + ("single_bar",) * 7
        + ("paired_bars",) * 9
        + ("edge_bars",) * 7
        + ("mixed_bars",) * 7
    ),
    "hard": (
        ("public_12",) * 2
        + ("public_8",)
        + ("public_16",) * 3
        + ("public_19",) * 4
        + ("single_bar",) * 4
        + ("paired_bars",) * 6
        + ("edge_bars",) * 9
        + ("mixed_bars",) * 11
    ),
    "all": SCENE_PROFILES,
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted complete scene profile",
        "valid": "|".join(SCENE_PROFILES),
    },
    "cut_color": {
        "type": "color",
        "default": "weighted toward canonical 6; otherwise nuisance 1..8",
        "valid": "1..8",
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

Grid = list[list[int]]
Box = tuple[int, int, int, int]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic member of the calibrated bar grammar."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty if difficulty is not None else "all"
    profile = ctx.draw_choice("scene_profile", _PROFILE_OPTIONS[band])
    cut_color = ctx.draw_choice(
        "cut_color",
        (6, 6, 6, 6, 6, 6, 1, 2, 3, 4, 5, 7, 8),
    )
    rng = ctx.draw_rng("layout")

    if profile in PUBLIC_PROFILES:
        spec = _PUBLIC_LAYOUTS[profile]
        canvas = spec["canvas"]
        boxes = list(spec["boxes"])
        # Preserve a complete answer-bearing public bitmap often enough to
        # teach the actual cell relation, while retaining lawful mask
        # variations in the remaining public-layout draws.
        use_canonical_masks = rng.random() < 0.60
        cut_masks = (
            list(spec["cut_masks"])
            if use_canonical_masks
            else [None] * len(boxes)
        )
    else:
        canvas, boxes = _build_extrapolation_layout(
            profile,
            difficulty,
            rng,
        )
        cut_masks = [None] * len(boxes)

    grid = full_grid(canvas, canvas, 0)
    for (row, col, height, width), cut_mask in zip(
        boxes,
        cut_masks,
    ):
        _draw_bar(
            grid,
            row,
            col,
            height,
            width,
            cut_color,
            rng,
            cut_mask=cut_mask,
        )

    # A nonidentity transform prevents literal replay when the otherwise
    # canonical public palette is sampled.  Every transform preserves the
    # linked component grammar and the outward-shift rule.
    transforms = (1, 3) if (
        profile in PUBLIC_PROFILES and cut_color == 6
    ) else tuple(range(8))
    transform = rng.choice(transforms)
    grid = _transform_grid(grid, transform)

    analysis = _analyze(grid)
    if (
        analysis["scene_profile"] != profile
        or analysis["cut_color"] != cut_color
    ):
        raise AssertionError("constructed grid lost an exact axis")
    return grid


def solve_python(grid: Grid) -> Grid:
    """Independent Python mirror of the broad canonical Racket rule."""
    height, width = _validate_rectangular_grid(grid)
    output = full_grid(height, width, 0)
    for cells in _components8(grid):
        first_row = min(row for row, _col in cells)
        last_row = max(row for row, _col in cells)
        first_col = min(col for _row, col in cells)
        last_col = max(col for _row, col in cells)
        object_height = last_row - first_row + 1
        object_width = last_col - first_col + 1
        split_horizontal = object_height > object_width
        cut = (
            object_height // 2
            if split_horizontal
            else object_width // 2
        )
        for row, col in cells:
            if grid[row][col] != 9:
                continue
            if split_horizontal:
                row_delta = -1 if row - first_row < cut else 1
                col_delta = 0
            else:
                row_delta = 0
                col_delta = -1 if col - first_col < cut else 1
            next_row = row + row_delta
            next_col = col + col_delta
            if 0 <= next_row < height and 0 <= next_col < width:
                output[next_row][next_col] = 9
    return output


def self_check(grid, *, difficulty=None, meta=None):
    """Recognize the complete returned-grid training grammar."""
    try:
        _analyze(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def observe_overrides(grid):
    """Recover both exact declared axes from returned cells."""
    try:
        analysis = _analyze(grid)
    except (TypeError, ValueError):
        return {}
    return {
        "scene_profile": analysis["scene_profile"],
        "cut_color": analysis["cut_color"],
    }


def canonical_profile_index(grid):
    """Return the complete D4/color-normalized public profile index."""
    try:
        _analyze(grid)
    except (TypeError, ValueError):
        return None
    profile = _canonical_answer_profile(grid)
    return _PUBLIC_PROFILE_INDEX.get(profile)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    if (
        "scene_profile" in overrides
        and overrides["scene_profile"] not in SCENE_PROFILES
    ):
        raise ValueError("unknown scene_profile")
    if "cut_color" in overrides:
        color = overrides["cut_color"]
        if (
            not isinstance(color, int)
            or isinstance(color, bool)
            or not 1 <= color <= 8
        ):
            raise ValueError("cut_color must be an integer 1..8")


def _build_extrapolation_layout(profile, difficulty, rng):
    canvas = rng.choice(_EXTRAPOLATION_CANVASES[profile])
    if profile == "single_bar":
        count = 1
        placement_mode = "interior"
        size_options = {
            "easy": (2, 3),
            "medium": (2, 3, 4),
            "hard": (3, 4, 5),
        }.get(difficulty, (2, 3, 4, 5))
    elif profile == "paired_bars":
        count = 2
        placement_mode = "interior"
        size_options = (2, 3) if canvas == 14 else (2, 3, 4)
    elif profile == "edge_bars":
        count = 3
        placement_mode = "edge"
        size_options = (2, 3) if canvas == 18 else (2, 3, 4)
    elif profile == "mixed_bars":
        count = rng.randint(4, 6)
        placement_mode = "safe"
        size_options = (2, 3, 4) if count == 4 else (2, 3)
    else:
        raise ValueError(f"unknown scene profile: {profile!r}")

    feasible_sizes = tuple(
        size
        for size in size_options
        if 2 * size <= canvas - 2
    )
    shapes = []
    for _index in range(count):
        short_side = rng.choice(feasible_sizes)
        if rng.random() < 0.5:
            shapes.append((short_side, 2 * short_side))
        else:
            shapes.append((2 * short_side, short_side))
    boxes = _place_exact_bars(
        canvas,
        shapes,
        placement_mode,
        rng,
    )
    return canvas, boxes


def _place_exact_bars(canvas, shapes, placement_mode, rng):
    # Largest-first search makes the exact requested count constructive; it
    # either returns every bar or fails loudly instead of shedding objects.
    ordered_shapes = sorted(
        shapes,
        key=lambda shape: shape[0] * shape[1],
        reverse=True,
    )
    candidate_lists = []
    for height, width in ordered_shapes:
        candidates = _candidate_boxes(
            canvas,
            height,
            width,
            placement_mode,
        )
        rng.shuffle(candidates)
        candidate_lists.append(candidates)

    def search(index, forbidden_cells, used_targets, selected):
        if index == len(candidate_lists):
            return list(selected)
        for box in candidate_lists[index]:
            cells = _box_cells(box)
            halo = _box_halo(canvas, box)
            targets = _box_shift_targets(box)
            if cells & forbidden_cells or targets & used_targets:
                continue
            selected.append(box)
            result = search(
                index + 1,
                forbidden_cells | halo,
                used_targets | targets,
                selected,
            )
            if result is not None:
                return result
            selected.pop()
        return None

    result = search(0, set(), set(), [])
    if result is None:
        raise RuntimeError(
            f"unable to place all {len(shapes)} bars on {canvas}x{canvas}"
        )
    return result


def _candidate_boxes(canvas, height, width, mode):
    if mode == "interior":
        rows = range(1, canvas - height)
        cols = range(1, canvas - width)
    elif mode == "edge":
        if width > height:
            rows = (0, canvas - height)
            cols = range(1, canvas - width)
        else:
            rows = range(1, canvas - height)
            cols = (0, canvas - width)
    elif mode == "safe":
        if width > height:
            rows = range(0, canvas - height + 1)
            cols = range(1, canvas - width)
        else:
            rows = range(1, canvas - height)
            cols = range(0, canvas - width + 1)
    else:
        raise ValueError(f"unknown placement mode: {mode!r}")
    return [
        (row, col, height, width)
        for row in rows
        for col in cols
    ]


def _box_halo(canvas, box):
    row, col, height, width = box
    return {
        (current_row, current_col)
        for current_row in range(
            max(0, row - 1),
            min(canvas, row + height + 1),
        )
        for current_col in range(
            max(0, col - 1),
            min(canvas, col + width + 1),
        )
    }


def _box_cells(box):
    row, col, height, width = box
    return {
        (current_row, current_col)
        for current_row in range(row, row + height)
        for current_col in range(col, col + width)
    }


def _box_shift_targets(box):
    """Return every possible destination before choosing cut cells."""
    row, col, height, width = box
    targets = set()
    if width > height:
        cut = width // 2
        for current_row in range(row, row + height):
            for current_col in range(col, col + width):
                delta = -1 if current_col - col < cut else 1
                targets.add((current_row, current_col + delta))
    else:
        cut = height // 2
        for current_row in range(row, row + height):
            delta = -1 if current_row - row < cut else 1
            for current_col in range(col, col + width):
                targets.add((current_row + delta, current_col))
    return targets


def _draw_bar(
    grid,
    row,
    col,
    height,
    width,
    cut_color,
    rng,
    *,
    cut_mask=None,
):
    if max(height, width) != 2 * min(height, width):
        raise ValueError("bar must have a 2:1 aspect ratio")
    for current_row in range(row, row + height):
        for current_col in range(col, col + width):
            grid[current_row][current_col] = 9
    if cut_mask is not None:
        for relative_row, relative_col in cut_mask:
            grid[row + relative_row][col + relative_col] = cut_color
        return
    short_side = min(height, width)
    if width > height:
        for lane in range(height):
            cut_col = col + short_side - 1 + rng.randrange(2)
            grid[row + lane][cut_col] = cut_color
    else:
        for lane in range(width):
            cut_row = row + short_side - 1 + rng.randrange(2)
            grid[cut_row][col + lane] = cut_color


def _transform_grid(grid, transform):
    result = [list(row) for row in grid]
    rotations = transform
    if transform >= 4:
        result = [list(reversed(row)) for row in result]
        rotations -= 4
    for _index in range(rotations):
        result = [
            list(row)
            for row in zip(*reversed(result))
        ]
    return result


def _canonical_answer_profile(grid):
    """Match a complete public input modulo D4 and cut-color relabeling."""
    try:
        height, width = _validate_rectangular_grid(grid)
    except (TypeError, ValueError):
        return None
    if height != width:
        return None
    palette = {value for row in grid for value in row}
    cut_colors = palette - {0, 9}
    if len(cut_colors) != 1:
        return None
    cut_color = next(iter(cut_colors))
    normalized = tuple(
        tuple(6 if value == cut_color else value for value in row)
        for row in grid
    )
    for profile, variants in _canonical_answer_orbits():
        if normalized in variants:
            return profile
    return None


@lru_cache(maxsize=1)
def _canonical_answer_orbits():
    result = []
    for profile in PUBLIC_PROFILES:
        spec = _PUBLIC_LAYOUTS[profile]
        height = spec["canvas"]
        template = full_grid(height, height, 0)
        for box, cut_mask in zip(
            spec["boxes"],
            spec["cut_masks"],
        ):
            row, col, object_height, object_width = box
            for current_row in range(row, row + object_height):
                for current_col in range(col, col + object_width):
                    template[current_row][current_col] = 9
            for relative_row, relative_col in cut_mask:
                template[row + relative_row][col + relative_col] = 6
        variants = {
            tuple(
                tuple(row) for row in _transform_grid(template, transform)
            )
            for transform in range(8)
        }
        result.append((profile, variants))
    return tuple(result)


def _validate_rectangular_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty rectangular sequence")
    first = grid[0]
    if not isinstance(first, (list, tuple)) or not first:
        raise ValueError("grid rows must be nonempty sequences")
    width = len(first)
    if len(grid) > 30 or width > 30:
        raise ValueError("grid dimensions must not exceed 30x30")
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            raise ValueError(f"row {row_index} must have width {width}")
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                raise ValueError("all cells must be integer ARC colors 0..9")
    return len(grid), width


def _components8(grid):
    height, width = _validate_rectangular_grid(grid)
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for row_delta in (-1, 0, 1):
                    for col_delta in (-1, 0, 1):
                        if row_delta == 0 and col_delta == 0:
                            continue
                        next_row = current_row + row_delta
                        next_col = current_col + col_delta
                        next_cell = (next_row, next_col)
                        if (
                            0 <= next_row < height
                            and 0 <= next_col < width
                            and grid[next_row][next_col] != 0
                            and next_cell not in seen
                        ):
                            seen.add(next_cell)
                            stack.append(next_cell)
            result.append(sorted(cells))
    return result


def _component_record(grid, cells):
    height = len(grid)
    width = len(grid[0])
    first_row = min(row for row, _col in cells)
    last_row = max(row for row, _col in cells)
    first_col = min(col for _row, col in cells)
    last_col = max(col for _row, col in cells)
    object_height = last_row - first_row + 1
    object_width = last_col - first_col + 1
    if len(cells) != object_height * object_width:
        raise ValueError("component is not a filled rectangle")
    short_side = min(object_height, object_width)
    long_side = max(object_height, object_width)
    if not 2 <= short_side <= 6 or long_side != 2 * short_side:
        raise ValueError("component is not a supported 2:1 bar")

    values = Counter(grid[row][col] for row, col in cells)
    other_colors = set(values) - {9}
    if 9 not in values or len(other_colors) != 1:
        raise ValueError("component must contain 9 and one cut color")
    cut_color = next(iter(other_colors))
    if not 1 <= cut_color <= 8:
        raise ValueError("cut color must be 1..8")
    cut_cells = [
        (row - first_row, col - first_col)
        for row, col in cells
        if grid[row][col] == cut_color
    ]
    if len(cut_cells) != short_side:
        raise ValueError("cut-cell count must equal the short side")

    center_indexes = {short_side - 1, short_side}
    if object_width > object_height:
        if (
            {row for row, _col in cut_cells}
            != set(range(object_height))
            or any(
                col not in center_indexes
                for _row, col in cut_cells
            )
        ):
            raise ValueError("wide-bar cut topology is invalid")
    else:
        if (
            {col for _row, col in cut_cells}
            != set(range(object_width))
            or any(
                row not in center_indexes
                for row, _col in cut_cells
            )
        ):
            raise ValueError("tall-bar cut topology is invalid")

    touches = {
        side
        for side, condition in (
            ("top", first_row == 0),
            ("bottom", last_row == height - 1),
            ("left", first_col == 0),
            ("right", last_col == width - 1),
        )
        if condition
    }
    if len(touches) > 1:
        raise ValueError("bars may not touch a canvas corner")
    if object_width > object_height and touches & {"left", "right"}:
        raise ValueError("wide bar touches its movement boundary")
    if object_height > object_width and touches & {"top", "bottom"}:
        raise ValueError("tall bar touches its movement boundary")
    return {
        "shape": (object_height, object_width),
        "cut_color": cut_color,
        "touches": touches,
    }


def _shape_signature(records):
    return tuple(sorted(record["shape"] for record in records))


def _swapped_signature(signature):
    return tuple(sorted((width, height) for height, width in signature))


def _classify_profile(canvas, records):
    signature = _shape_signature(records)
    edge_count = sum(bool(record["touches"]) for record in records)
    for profile, spec in _PUBLIC_LAYOUTS.items():
        expected = tuple(
            sorted(
                (height, width)
                for _row, _col, height, width in spec["boxes"]
            )
        )
        if (
            canvas == spec["canvas"]
            and edge_count == spec["edge_count"]
            and signature in (expected, _swapped_signature(expected))
        ):
            return profile

    if (
        canvas in _EXTRAPOLATION_CANVASES["single_bar"]
        and len(records) == 1
        and edge_count == 0
    ):
        return "single_bar"
    if (
        canvas in _EXTRAPOLATION_CANVASES["paired_bars"]
        and len(records) == 2
        and edge_count <= 1
    ):
        return "paired_bars"
    if (
        canvas in _EXTRAPOLATION_CANVASES["edge_bars"]
        and len(records) == 3
        and edge_count == 3
    ):
        return "edge_bars"
    if (
        canvas in _EXTRAPOLATION_CANVASES["mixed_bars"]
        and 4 <= len(records) <= 6
    ):
        return "mixed_bars"
    raise ValueError(
        "canvas, component shapes, and edge contacts do not match a profile"
    )


def _analyze(grid):
    height, width = _validate_rectangular_grid(grid)
    if height != width or not 8 <= height <= 22:
        raise ValueError("canvas must be square with side 8..22")
    palette = {value for row in grid for value in row}
    if 0 not in palette or 9 not in palette:
        raise ValueError("grid must contain background 0 and active color 9")
    cut_colors = palette - {0, 9}
    if len(cut_colors) != 1:
        raise ValueError("grid must use exactly one cut color")
    cut_color = next(iter(cut_colors))
    if not 1 <= cut_color <= 8:
        raise ValueError("cut color must be 1..8")

    components = _components8(grid)
    if not components:
        raise ValueError("grid must contain at least one bar")
    records = [
        _component_record(grid, cells)
        for cells in components
    ]
    if any(record["cut_color"] != cut_color for record in records):
        raise ValueError("every bar must use the shared cut color")
    profile = _classify_profile(height, records)
    output = solve_python(grid)
    input_nines = sum(value == 9 for row in grid for value in row)
    output_nines = sum(value == 9 for row in output for value in row)
    if output_nines != input_nines:
        raise ValueError("shifted 9 cells clipped or collided")
    if output == grid:
        raise ValueError("rule must change the grid")
    return {
        "scene_profile": profile,
        "canonical_answer_profile": _canonical_answer_profile(grid),
        "cut_color": cut_color,
        "component_count": len(records),
        "edge_count": sum(
            bool(record["touches"]) for record in records
        ),
        "shapes": [record["shape"] for record in records],
        "input_nines": input_nines,
        "output_nines": output_nines,
    }
