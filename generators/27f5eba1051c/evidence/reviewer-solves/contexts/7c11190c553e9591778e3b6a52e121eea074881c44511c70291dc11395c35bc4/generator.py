"""Generator for 27f5eba1051c: crop the object selected by a rank marker.

The value in the top-left cell is a one-based rank.  After clearing that
marker, sort the three disconnected monochrome objects by descending area,
then by leftmost column, then by color.  Return the selected object's bounding
box crop.

Five profiles preserve the complete public canvas/rank/object morphology,
including the held-out equal-area pair and the training example in which an
object shares the rank marker's color.  A four-slot semantic schedule combines
those linked forms with dedicated column-tie, color-tie, and shortcut-stress
profiles.  The stress form deliberately uses disconnected same-color objects
and conflicting cell-count/bounding-box/position rankings so each four-demo
lesson identifies the complete rule instead of a plausible shortcut.
"""

from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "27f5eba1051c"
TASK_ID = "27f5eba1051c"
VERSION = "5.0.0"
RULE_HASH = "fb00fc6fefe5"

SUMMARY = (
    "Read the one-based rank at (0,0), clear that marker, sort three "
    "disconnected objects by area descending, left column ascending, then "
    "color ascending, and crop the selected object's bounding box."
)

EXAMPLES_NEEDED = 4
EXPECTED_OUTPUT_CODOMAIN = 5_000
OUTPUT_CODOMAIN_BY_DIFFICULTY = {
    "easy": 1_500,
    "medium": 3_000,
    "hard": 5_000,
    None: 3_000,
}

INVARIANTS = [
    "the top-left cell is a rank marker in 1..3",
    "clearing only that marker leaves exactly three separated objects",
    "each object is one 4-connected monochrome polyomino of 2..8 cells",
    "object colors may repeat across separated components",
    "objects are ordered by area descending, left column, then color",
    "equal-area examples exercise both the column and color tie-breakers",
    "the output is the selected object's inclusive bounding-box crop",
    "generation and rule execution are deterministic and input-pure",
    "every four consecutive default examples refute the declared rivals",
]

MIN_STRICT_FRAC = 1.0

SCHEDULE_PROFILES = (
    "canonical_linked",
    "column_tie",
    "color_tie",
    "semantic_stress",
)

SCENE_PROFILES = (
    "rank1_l_square_bar_9x14",
    "rank2_triangle_square_bar_9x14",
    "rank3_bridge_l_square_10x15",
    "rank2_plus_square_bar_alias_10x16",
    "rank1_triangle_tied_fours_9x15",
    "column_tie",
    "color_tie",
    "semantic_stress",
    "generalized",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four-slot cyclic semantic schedule",
        "valid": "|".join(SCENE_PROFILES),
        "doc": (
            "Recovered from the linked canvas, rank, D4-normalized object "
            "masks, equal-area relation, and rank/object color alias."
        ),
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the semantic role for a default draw.

    The role depends only on the sample index so every consecutive block of
    ``EXAMPLES_NEEDED`` examples contains all four roles, independent of seed
    and difficulty.
    """
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


_PUBLIC_SPECS = {
    "rank1_l_square_bar_9x14": {
        "canvas": (9, 14),
        "rank": 1,
        "objects": (
            ((2, 1), (3, 1), (4, 1), (4, 2), (4, 3)),
            ((2, 7), (2, 8), (3, 7), (3, 8)),
            ((6, 10), (6, 11), (6, 12)),
        ),
        "alias_index": None,
        "public_colors": (2, 4, 7),
    },
    "rank2_triangle_square_bar_9x14": {
        "canvas": (9, 14),
        "rank": 2,
        "objects": (
            ((2, 1), (3, 1), (3, 2), (4, 1), (4, 2), (4, 3)),
            ((5, 8), (5, 9), (6, 8), (6, 9)),
            ((2, 10), (2, 11), (2, 12)),
        ),
        "alias_index": None,
        "public_colors": (3, 6, 8),
    },
    "rank3_bridge_l_square_10x15": {
        "canvas": (10, 15),
        "rank": 3,
        "objects": (
            (
                (2, 1),
                (2, 3),
                (3, 1),
                (3, 3),
                (4, 1),
                (4, 2),
                (4, 3),
            ),
            ((2, 7), (3, 7), (4, 7), (4, 8), (4, 9)),
            ((6, 11), (6, 12), (7, 11), (7, 12)),
        ),
        "alias_index": None,
        "public_colors": (5, 2, 9),
    },
    "rank2_plus_square_bar_alias_10x16": {
        "canvas": (10, 16),
        "rank": 2,
        "objects": (
            ((2, 2), (3, 1), (3, 2), (3, 3), (4, 2)),
            ((2, 8), (2, 9), (3, 8), (3, 9)),
            ((6, 12), (6, 13), (6, 14)),
        ),
        "alias_index": 2,
        "public_colors": (4, 7, 2),
    },
    "rank1_triangle_tied_fours_9x15": {
        "canvas": (9, 15),
        "rank": 1,
        "objects": (
            ((2, 7), (3, 7), (3, 8), (4, 7), (4, 8), (4, 9)),
            ((2, 2), (3, 1), (3, 2), (4, 1)),
            ((6, 11), (6, 12), (7, 11), (7, 12)),
        ),
        "alias_index": None,
        "public_colors": (3, 6, 8),
    },
}


def _rotate(matrix):
    height = len(matrix)
    width = len(matrix[0])
    return tuple(
        tuple(matrix[height - 1 - row][col] for row in range(height))
        for col in range(width)
    )


def _flip_horizontal(matrix):
    return tuple(tuple(reversed(row)) for row in matrix)


def _canonical_mask(cells):
    top = min(row for row, _col in cells)
    bottom = max(row for row, _col in cells)
    left = min(col for _row, col in cells)
    right = max(col for _row, col in cells)
    matrix = tuple(
        tuple(int((row, col) in cells) for col in range(left, right + 1))
        for row in range(top, bottom + 1)
    )
    variants = []
    current = matrix
    for _ in range(4):
        variants.extend((current, _flip_horizontal(current)))
        current = _rotate(current)
    return min(variants)


def _components_same_color(grid):
    height = len(grid)
    width = len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }
    scene_objects = []
    while remaining:
        seed = min(remaining)
        color = grid[seed[0]][seed[1]]
        remaining.remove(seed)
        component = {seed}
        stack = [seed]
        while stack:
            row, col = stack.pop()
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if (
                    neighbor in remaining
                    and grid[neighbor[0]][neighbor[1]] == color
                ):
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        top = min(row for row, _col in component)
        bottom = max(row for row, _col in component)
        left = min(col for _row, col in component)
        right = max(col for _row, col in component)
        scene_objects.append(
            {
                "color": color,
                "cells": frozenset(component),
                "size": len(component),
                "bbox": (top, bottom, left, right),
                "mask": _canonical_mask(component),
            }
        )
    return scene_objects


def _coerce_arc_grid(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return [], ["grid must be a nonempty row sequence"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return [], ["every grid row must be a sequence"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return [], ["grid must be nonempty and rectangular"]
    if len(grid) > 30 or width > 30:
        errors.append("grid dimensions must not exceed 30")
    output = []
    for row in grid:
        output_row = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("grid values must be integer ARC colors 0..9")
                return [], errors
            output_row.append(value)
        output.append(output_row)
    return output, errors


def _object_order(scene_objects):
    return tuple(
        sorted(
            scene_objects,
            key=lambda obj: (
                -obj["size"],
                obj["bbox"][2],
                obj["color"],
            ),
        )
    )


def _analysis_signature(height, width, rank, scene_objects):
    object_forms = tuple(
        sorted((obj["size"], obj["mask"]) for obj in scene_objects)
    )
    alias_forms = tuple(
        sorted(
            (obj["size"], obj["mask"])
            for obj in scene_objects
            if obj["color"] == rank
        )
    )
    return height, width, rank, object_forms, alias_forms


def _spec_signature(spec):
    height, width = spec["canvas"]
    scene_objects = [
        {
            "size": len(cells),
            "mask": _canonical_mask(cells),
            "color": spec["rank"] if index == spec["alias_index"] else -1,
        }
        for index, cells in enumerate(spec["objects"])
    ]
    return _analysis_signature(
        height,
        width,
        spec["rank"],
        scene_objects,
    )


_EXACT_SIGNATURES = {
    _spec_signature(spec): profile
    for profile, spec in _PUBLIC_SPECS.items()
}
if len(_EXACT_SIGNATURES) != len(_PUBLIC_SPECS):
    raise RuntimeError("public linked profile signatures overlap")


def _separated(scene_objects):
    for index, left_obj in enumerate(scene_objects):
        left_top, left_bottom, left_col, left_right = left_obj["bbox"]
        for right_obj in scene_objects[index + 1 :]:
            right_top, right_bottom, right_col, right_right = right_obj["bbox"]
            bboxes_overlap = not (
                left_bottom < right_top
                or right_bottom < left_top
                or left_right < right_col
                or right_right < left_col
            )
            if bboxes_overlap:
                return False
            if any(
                max(abs(row - other_row), abs(col - other_col)) <= 1
                for row, col in left_obj["cells"]
                for other_row, other_col in right_obj["cells"]
            ):
                return False
    return True


def _tie_features(ordered):
    equal_area_pairs = [
        (left_obj, right_obj)
        for index, left_obj in enumerate(ordered)
        for right_obj in ordered[index + 1 :]
        if left_obj["size"] == right_obj["size"]
    ]
    return {
        "size_tie": bool(equal_area_pairs),
        "column_tie": any(
            left_obj["bbox"][2] != right_obj["bbox"][2]
            for left_obj, right_obj in equal_area_pairs
        ),
        "color_tie": any(
            left_obj["bbox"][2] == right_obj["bbox"][2]
            and left_obj["color"] != right_obj["color"]
            for left_obj, right_obj in equal_area_pairs
        ),
    }


def _inspect_scene(grid):
    original, errors = _coerce_arc_grid(grid)
    if errors:
        return None
    height = len(original)
    width = len(original[0])
    if not 8 <= height <= 18 or not 12 <= width <= 24:
        return None
    rank = original[0][0]
    if rank not in (1, 2, 3):
        return None
    clean = [row[:] for row in original]
    clean[0][0] = 0
    scene_objects = _components_same_color(clean)
    if (
        len(scene_objects) != 3
        or any(not 2 <= obj["size"] <= 8 for obj in scene_objects)
        or any(
            obj["bbox"][1] - obj["bbox"][0] + 1 > 3
            or obj["bbox"][3] - obj["bbox"][2] + 1 > 3
            for obj in scene_objects
        )
        or not _separated(scene_objects)
    ):
        return None
    ordered = _object_order(scene_objects)
    keys = tuple(
        (-obj["size"], obj["bbox"][2], obj["color"])
        for obj in ordered
    )
    if len(keys) != len(set(keys)):
        return None
    selected = ordered[rank - 1]
    top, bottom, left, right = selected["bbox"]
    output = [
        row[left : right + 1]
        for row in clean[top : bottom + 1]
    ]
    tie_features = _tie_features(ordered)
    signature = _analysis_signature(
        height,
        width,
        rank,
        scene_objects,
    )
    repeated_colors = len({obj["color"] for obj in scene_objects}) < 3
    if repeated_colors:
        profile = "semantic_stress"
    else:
        profile = _EXACT_SIGNATURES.get(signature)
    if profile is None:
        if tie_features["color_tie"]:
            profile = "color_tie"
        elif tie_features["column_tie"]:
            profile = "column_tie"
        else:
            profile = "generalized"
    return {
        "scene_profile": profile,
        "shape": (height, width),
        "rank": rank,
        "objects": tuple(scene_objects),
        "ordered_objects": ordered,
        "sizes": tuple(obj["size"] for obj in ordered),
        "colors": tuple(obj["color"] for obj in ordered),
        "repeated_colors": repeated_colors,
        "rank_alias_indexes": tuple(
            index
            for index, obj in enumerate(ordered, start=1)
            if obj["color"] == rank
        ),
        "selected_index": rank,
        "selected_object": selected,
        "output": output,
        "output_shape": (len(output), len(output[0])),
        "signature": signature,
        **tie_features,
    }


def observe_overrides(grid):
    """Recover the declared semantic override from the returned grid."""
    analysis = _inspect_scene(grid)
    if analysis is None:
        return {}
    return {"scene_profile": analysis["scene_profile"]}


def canonical_profile_index(grid):
    """Return a public linked-profile index, or ``None``."""
    analysis = _inspect_scene(grid)
    if analysis is None:
        return None
    profile = analysis["scene_profile"]
    if profile not in _PUBLIC_SPECS:
        return None
    return tuple(_PUBLIC_SPECS).index(profile)


def self_check(grid, *, difficulty=None, meta=None):
    """Strict returned-grid recognizer for the calibrated task grammar."""
    _original, errors = _coerce_arc_grid(grid)
    if errors:
        return errors
    if difficulty not in (None, "easy", "medium", "hard"):
        return ["difficulty must be easy, medium, hard, or None"]
    analysis = _inspect_scene(grid)
    if analysis is None:
        return [
            "expected an 8..18 by 12..24 scene with a rank 1..3 at "
            "(0,0), exactly three separated monochrome 2..8-cell "
            "polyominoes, and unique area/column/color sort keys"
        ]
    if isinstance(meta, dict):
        requested = meta.get("overrides")
        if not isinstance(requested, dict):
            requested = meta
        requested_profile = requested.get("scene_profile")
        if (
            requested_profile is not None
            and requested_profile != analysis["scene_profile"]
        ):
            errors.append(
                f"scene_profile requested {requested_profile!r}, "
                f"observed {analysis['scene_profile']!r}"
            )
    return errors


def _colors_for_objects(rank, count, alias_index, rng):
    if alias_index is None:
        return tuple(rng.sample([color for color in range(1, 10) if color != rank], count))
    remaining = rng.sample(
        [color for color in range(1, 10) if color != rank],
        count - 1,
    )
    colors = []
    next_remaining = iter(remaining)
    for index in range(count):
        colors.append(rank if index == alias_index else next(next_remaining))
    return tuple(colors)


def _render(height, width, rank, cells_by_object, colors):
    grid = [[0 for _ in range(width)] for _ in range(height)]
    grid[0][0] = rank
    for cells, color in zip(cells_by_object, colors):
        for row, col in cells:
            if (row, col) == (0, 0) or grid[row][col] != 0:
                raise RuntimeError("constructive object placement overlapped")
            grid[row][col] = color
    return grid


def _transform_exact_cells(spec, rng):
    height, width = spec["canvas"]
    flip_vertical = bool(rng.randrange(2))
    flip_horizontal = bool(rng.randrange(2))
    transformed = []
    for object_cells in spec["objects"]:
        cells = set()
        for row, col in object_cells:
            if flip_vertical:
                row = height - 1 - row
            if flip_horizontal:
                col = width - 1 - col
            cells.add((row, col))
        transformed.append(cells)
    all_cells = set().union(*transformed)
    minimum_row = min(row for row, _col in all_cells)
    maximum_row = max(row for row, _col in all_cells)
    minimum_col = min(col for _row, col in all_cells)
    maximum_col = max(col for _row, col in all_cells)
    shifts = [
        (row_shift, col_shift)
        for row_shift in range(-minimum_row, height - maximum_row)
        for col_shift in range(-minimum_col, width - maximum_col)
        if all(
            max(row + row_shift, col + col_shift) > 1
            for row, col in all_cells
        )
    ]
    if not shifts:
        raise RuntimeError("exact profile has no marker-safe translation")
    row_shift, col_shift = rng.choice(shifts)
    return tuple(
        frozenset(
            (row + row_shift, col + col_shift)
            for row, col in cells
        )
        for cells in transformed
    )


def _construct_exact(profile, context):
    spec = _PUBLIC_SPECS[profile]
    rng = context.draw_rng("scene")
    height, width = spec["canvas"]
    rank = spec["rank"]
    cells = _transform_exact_cells(spec, rng)
    colors = _colors_for_objects(
        rank,
        len(cells),
        spec["alias_index"],
        rng,
    )
    grid = _render(height, width, rank, cells, colors)
    literal = _render(
        height,
        width,
        rank,
        tuple(frozenset(obj) for obj in spec["objects"]),
        spec["public_colors"],
    )
    if grid == literal:
        colors = (colors[1], colors[0], *colors[2:])
        grid = _render(height, width, rank, cells, colors)
    return grid


def _connected(cells):
    if not cells:
        return False
    remaining = set(cells)
    seed = remaining.pop()
    stack = [seed]
    while stack:
        row, col = stack.pop()
        for neighbor in (
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        ):
            if neighbor in remaining:
                remaining.remove(neighbor)
                stack.append(neighbor)
    return not remaining


def _normalized(cells):
    minimum_row = min(row for row, _col in cells)
    minimum_col = min(col for _row, col in cells)
    return frozenset(
        (row - minimum_row, col - minimum_col)
        for row, col in cells
    )


def _polyomino_bank():
    bank = {}
    universe = tuple((row, col) for row in range(3) for col in range(3))
    for size in range(2, 9):
        shapes = {
            _normalized(cells)
            for cells in combinations(universe, size)
            if _connected(cells)
        }
        if not shapes:
            raise RuntimeError(f"no connected 3x3 shapes of size {size}")
        bank[size] = tuple(
            sorted(
                shapes,
                key=lambda shape: tuple(sorted(shape)),
            )
        )
    return bank


_POLYOMINOES = _polyomino_bank()


def _shape_dimensions(shape):
    return (
        max(row for row, _col in shape) + 1,
        max(col for _row, col in shape) + 1,
    )


_STRESS_LARGEST = tuple(
    shape
    for shape in _POLYOMINOES[7]
    if _shape_dimensions(shape) == (3, 3)
)
_STRESS_MIDDLE = tuple(
    shape
    for shape in _POLYOMINOES[6]
    if _shape_dimensions(shape) in ((2, 3), (3, 2))
)
_STRESS_SMALLEST = tuple(
    shape
    for shape in _POLYOMINOES[5]
    if _shape_dimensions(shape) == (3, 3)
)
if not (_STRESS_LARGEST and _STRESS_MIDDLE and _STRESS_SMALLEST):
    raise RuntimeError("semantic stress shape banks must be nonempty")


def _horizontal_slots(width):
    usable = width - 2
    base, remainder = divmod(usable, 3)
    widths = [base + int(index < remainder) for index in range(3)]
    if min(widths) < 3:
        raise RuntimeError("canvas is too narrow for three separated slots")
    slots = []
    left = 0
    for slot_width in widths:
        slots.append((left, slot_width))
        left += slot_width + 1
    return tuple(slots)


def _place_shapes_in_slots(height, width, shapes, slot_order, rng):
    slots = _horizontal_slots(width)
    placed = []
    for shape, slot_index in zip(shapes, slot_order):
        left, slot_width = slots[slot_index]
        shape_height, shape_width = _shape_dimensions(shape)
        if shape_width > slot_width:
            raise RuntimeError("shape does not fit its constructive slot")
        top = rng.randint(2, height - shape_height)
        start_col = rng.randint(left, left + slot_width - shape_width)
        placed.append(
            frozenset(
                (top + row, start_col + col)
                for row, col in shape
            )
        )
    return tuple(placed)


def _canvas_options(difficulty):
    if difficulty == "easy":
        return ((8, 12), (9, 14), (9, 15), (10, 15), (10, 16))
    if difficulty == "hard":
        return ((12, 18), (14, 20), (16, 22), (18, 24))
    return ((9, 14), (10, 15), (10, 16), (12, 18), (14, 20))


def _construct_generalized(difficulty, context):
    rng = context.draw_rng("scene")
    for _ in range(128):
        height, width = rng.choice(_canvas_options(difficulty))
        rank = rng.randint(1, 3)
        sizes = sorted(rng.sample(range(2, 9), 3), reverse=True)
        shapes = tuple(rng.choice(_POLYOMINOES[size]) for size in sizes)
        slot_order = list(range(3))
        rng.shuffle(slot_order)
        cells = _place_shapes_in_slots(
            height,
            width,
            shapes,
            slot_order,
            rng,
        )
        alias_index = rng.randrange(3) if rng.randrange(4) == 0 else None
        colors = _colors_for_objects(rank, 3, alias_index, rng)
        grid = _render(height, width, rank, cells, colors)
        analysis = _inspect_scene(grid)
        if (
            analysis is not None
            and analysis["scene_profile"] == "generalized"
        ):
            return grid
    raise RuntimeError("could not construct a non-public generalized scene")


def _construct_column_tie(difficulty, context):
    rng = context.draw_rng("scene")
    for _ in range(128):
        height, width = rng.choice(_canvas_options(difficulty))
        rank = 2
        tie_size = rng.randint(2, 6)
        big_size = rng.randint(tie_size + 1, 8)
        left_shape, right_shape = rng.sample(_POLYOMINOES[tie_size], 2)
        big_shape = rng.choice(_POLYOMINOES[big_size])
        slots = _horizontal_slots(width)

        def place(shape, slot_index, top):
            _shape_height, shape_width = _shape_dimensions(shape)
            slot_left, slot_width = slots[slot_index]
            start_col = rng.randint(
                slot_left,
                slot_left + slot_width - shape_width,
            )
            return frozenset(
                (top + row, start_col + col)
                for row, col in shape
            )

        left_height, _left_width = _shape_dimensions(left_shape)
        right_height, _right_width = _shape_dimensions(right_shape)
        big_height, _big_width = _shape_dimensions(big_shape)
        cells = (
            place(
                big_shape,
                1,
                rng.randint(2, height - big_height),
            ),
            place(left_shape, 0, height - left_height),
            place(right_shape, 2, 1),
        )
        palette = rng.sample(range(1, 10), 3)
        colors = (
            palette[0],
            max(palette[1:]),
            min(palette[1:]),
        )
        grid = _render(height, width, rank, cells, colors)
        analysis = _inspect_scene(grid)
        if (
            analysis is not None
            and analysis["scene_profile"] == "column_tie"
        ):
            return grid
    raise RuntimeError("column-tie constructor did not realize its profile")


def _construct_color_tie(difficulty, context):
    rng = context.draw_rng("scene")
    options = {
        "easy": ((12, 14), (12, 16)),
        "medium": ((12, 16), (14, 18)),
        "hard": ((14, 18), (16, 20), (18, 22)),
        None: ((12, 16), (14, 18)),
    }[difficulty]
    for _ in range(128):
        height, width = rng.choice(options)
        rank = 2
        tie_size = rng.randint(2, 6)
        big_size = rng.randint(tie_size + 1, 8)
        tied_shapes = rng.sample(_POLYOMINOES[tie_size], 2)
        tie_col = rng.randint(1, 3)
        first = frozenset(
            (1 + row, tie_col + col)
            for row, col in tied_shapes[0]
        )
        second_height, _second_width = _shape_dimensions(tied_shapes[1])
        second_top = height - second_height
        second = frozenset(
            (second_top + row, tie_col + col)
            for row, col in tied_shapes[1]
        )
        big_shape = rng.choice(_POLYOMINOES[big_size])
        big_height, big_width = _shape_dimensions(big_shape)
        big_top = rng.randint(2, height - big_height)
        big_left = width - big_width - 1
        big = frozenset(
            (big_top + row, big_left + col)
            for row, col in big_shape
        )
        cells = (big, first, second)
        palette = rng.sample(range(1, 10), 3)
        colors = (
            palette[0],
            max(palette[1:]),
            min(palette[1:]),
        )
        grid = _render(height, width, rank, cells, colors)
        analysis = _inspect_scene(grid)
        if (
            analysis is not None
            and analysis["scene_profile"] == "color_tie"
        ):
            return grid
    raise RuntimeError("color-tie constructor did not realize its profile")


def _construct_semantic_stress(difficulty, context):
    """Build a scene that simultaneously refutes common shortcut rules."""
    rng = context.draw_rng("scene")
    for _ in range(128):
        height, width = rng.choice(_canvas_options(difficulty))
        rank = 1
        shapes = (
            rng.choice(_STRESS_LARGEST),
            rng.choice(_STRESS_MIDDLE),
            rng.choice(_STRESS_SMALLEST),
        )
        # The smallest object is leftmost while the largest is rightmost.
        # Largest and smallest both have 3x3 bounding boxes but 7 versus 5
        # occupied cells, and they intentionally share the marker color.
        cells = _place_shapes_in_slots(
            height,
            width,
            shapes,
            (2, 1, 0),
            rng,
        )
        middle_color = rng.choice(tuple(range(2, 10)))
        colors = (rank, middle_color, rank)
        grid = _render(height, width, rank, cells, colors)
        analysis = _inspect_scene(grid)
        if (
            analysis is not None
            and analysis["scene_profile"] == "semantic_stress"
            and analysis["sizes"] == (7, 6, 5)
        ):
            return grid
    raise RuntimeError("semantic-stress constructor did not realize its profile")


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    profile = overrides.get("scene_profile")
    if profile is not None and profile not in SCENE_PROFILES:
        raise ValueError(
            f"scene_profile must be one of {SCENE_PROFILES}, got {profile!r}"
        )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    context = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if "scene_profile" in overrides:
        profile = context.draw_choice("scene_profile", SCENE_PROFILES)
    else:
        role = schedule_profile(seed, sample_index, difficulty)
        options = tuple(_PUBLIC_SPECS) if role == "canonical_linked" else (role,)
        profile = context.draw_choice("scene_profile", options)
    if profile in _PUBLIC_SPECS:
        grid = _construct_exact(profile, context)
    elif profile == "column_tie":
        grid = _construct_column_tie(difficulty, context)
    elif profile == "color_tie":
        grid = _construct_color_tie(difficulty, context)
    elif profile == "semantic_stress":
        grid = _construct_semantic_stress(difficulty, context)
    else:
        grid = _construct_generalized(difficulty, context)
    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": overrides},
    )
    if errors:
        raise RuntimeError(
            "constructed an invalid calibrated scene: " + "; ".join(errors)
        )
    if rule_mirror(grid) == grid:
        raise RuntimeError("constructed an identity rule example")
    return grid


def rule_mirror(grid):
    """Input-pure Python mirror of the complete canonical Racket rule."""
    original, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    rank = original[0][0]
    if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
        raise ValueError("rank marker at (0,0) must be a positive integer")
    clean = [row[:] for row in original]
    clean[0][0] = 0
    scene_objects = _object_order(_components_same_color(clean))
    if rank > len(scene_objects):
        raise ValueError(
            f"rank {rank} exceeds the {len(scene_objects)} available object(s)"
        )
    selected = scene_objects[rank - 1]
    top, bottom, left, right = selected["bbox"]
    return [
        row[left : right + 1]
        for row in clean[top : bottom + 1]
    ]


def strict_canonical_like(grid):
    """Return semantic-shape errors; ``[]`` means the scene is lawful."""
    return self_check(grid)


def _rival_ordered_crop(grid, key, *, rank_override=None):
    original, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    rank = original[0][0] if rank_override is None else rank_override
    clean = [row[:] for row in original]
    clean[0][0] = 0
    ordered = sorted(_components_same_color(clean), key=key)
    if not isinstance(rank, int) or isinstance(rank, bool) or not 1 <= rank <= len(ordered):
        raise ValueError(f"rank {rank!r} is invalid for {len(ordered)} object(s)")
    selected = ordered[rank - 1]
    top, bottom, left, right = selected["bbox"]
    return [row[left : right + 1] for row in clean[top : bottom + 1]]


def _bbox_area(obj):
    top, bottom, left, right = obj["bbox"]
    return (bottom - top + 1) * (right - left + 1)


def _rival_ascending_area(grid):
    return _rival_ordered_crop(
        grid,
        lambda obj: (obj["size"], obj["bbox"][2], obj["color"]),
    )


def _rival_bbox_area(grid):
    return _rival_ordered_crop(
        grid,
        lambda obj: (-_bbox_area(obj), obj["bbox"][2], obj["color"]),
    )


def _rival_left_to_right(grid):
    return _rival_ordered_crop(
        grid,
        lambda obj: (obj["bbox"][2], obj["bbox"][0], obj["color"]),
    )


def _rival_row_before_column_ties(grid):
    return _rival_ordered_crop(
        grid,
        lambda obj: (
            -obj["size"],
            obj["bbox"][0],
            obj["bbox"][2],
            obj["color"],
        ),
    )


def _rival_color_before_column_ties(grid):
    return _rival_ordered_crop(
        grid,
        lambda obj: (-obj["size"], obj["color"], obj["bbox"][2]),
    )


def _rival_group_same_color(grid):
    original, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    rank = original[0][0]
    clean = [row[:] for row in original]
    clean[0][0] = 0
    groups = {}
    for row, values in enumerate(clean):
        for col, color in enumerate(values):
            if color != 0:
                groups.setdefault(color, set()).add((row, col))
    color_records = []
    for color, cells in groups.items():
        top = min(row for row, _col in cells)
        bottom = max(row for row, _col in cells)
        left = min(col for _row, col in cells)
        right = max(col for _row, col in cells)
        color_records.append(
            {
                "color": color,
                "cells": frozenset(cells),
                "size": len(cells),
                "bbox": (top, bottom, left, right),
            }
        )
    ordered = _object_order(color_records)
    if not 1 <= rank <= len(ordered):
        raise ValueError(f"rank {rank} exceeds {len(ordered)} color group(s)")
    selected = ordered[rank - 1]
    top, bottom, left, right = selected["bbox"]
    return [row[left : right + 1] for row in clean[top : bottom + 1]]


def _rival_solid_bbox(grid):
    original, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    rank = original[0][0]
    clean = [row[:] for row in original]
    clean[0][0] = 0
    ordered = _object_order(_components_same_color(clean))
    if not 1 <= rank <= len(ordered):
        raise ValueError(f"rank {rank} exceeds {len(ordered)} object(s)")
    selected = ordered[rank - 1]
    top, bottom, left, right = selected["bbox"]
    return [
        [selected["color"] for _col in range(left, right + 1)]
        for _row in range(top, bottom + 1)
    ]


def _rival_always_largest(grid):
    return _rival_ordered_crop(
        grid,
        lambda obj: (-obj["size"], obj["bbox"][2], obj["color"]),
        rank_override=1,
    )


SEMANTIC_RIVALS = {
    "ascending_area": _rival_ascending_area,
    "bbox_area": _rival_bbox_area,
    "left_to_right": _rival_left_to_right,
    "row_before_column_ties": _rival_row_before_column_ties,
    "color_before_column_ties": _rival_color_before_column_ties,
    "group_same_color": _rival_group_same_color,
    "solid_bbox": _rival_solid_bbox,
    "always_largest": _rival_always_largest,
}


def _profile_refutes(grid, profile, *rival_names):
    try:
        analysis = _inspect_scene(grid)
        return (
            analysis is not None
            and analysis["scene_profile"] == profile
            and all(
                SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)
                for name in rival_names
            )
        )
    except Exception:
        return False


SEMANTIC_WITNESSES = {
    "descending_cell_count_visible": lambda grid: _profile_refutes(
        grid, "semantic_stress", "ascending_area"
    ),
    "cell_count_not_bbox_area": lambda grid: _profile_refutes(
        grid, "semantic_stress", "bbox_area"
    ),
    "size_precedes_horizontal_position": lambda grid: _profile_refutes(
        grid, "semantic_stress", "left_to_right"
    ),
    "disconnected_same_color_are_separate": lambda grid: _profile_refutes(
        grid, "semantic_stress", "group_same_color"
    ),
    "crop_preserves_internal_background": lambda grid: _profile_refutes(
        grid, "semantic_stress", "solid_bbox"
    ),
    "column_precedes_row_on_size_tie": lambda grid: _profile_refutes(
        grid, "column_tie", "row_before_column_ties"
    ),
    "column_precedes_color_on_size_tie": lambda grid: _profile_refutes(
        grid, "column_tie", "color_before_column_ties"
    ),
    "color_breaks_same_column_tie": lambda grid: _profile_refutes(
        grid, "color_tie", "row_before_column_ties"
    ),
    "rank_marker_selects_nonlargest": lambda grid: (
        _profile_refutes(grid, "column_tie", "always_largest")
        or _profile_refutes(grid, "color_tie", "always_largest")
    ),
}

WITNESS_RIVALS = {
    "descending_cell_count_visible": ["ascending_area"],
    "cell_count_not_bbox_area": ["bbox_area"],
    "size_precedes_horizontal_position": ["left_to_right"],
    "disconnected_same_color_are_separate": ["group_same_color"],
    "crop_preserves_internal_background": ["solid_bbox"],
    "column_precedes_row_on_size_tie": ["row_before_column_ties"],
    "column_precedes_color_on_size_tie": ["color_before_column_ties"],
    "color_breaks_same_column_tie": ["row_before_column_ties"],
    "rank_marker_selects_nonlargest": ["always_largest"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Require every declared rival to be eliminated by the demonstrations."""
    reasons = []
    if len(demos) != EXAMPLES_NEEDED:
        reasons.append(
            f"expected {EXAMPLES_NEEDED} demos, received {len(demos)}"
        )

    valid_demos = []
    for index, pair in enumerate(demos):
        grid = pair.get("input") if isinstance(pair, dict) else None
        output = pair.get("output") if isinstance(pair, dict) else None
        errors = self_check(grid)
        if errors:
            reasons.append(f"demo {index} malformed: {'; '.join(errors)}")
            continue
        expected = rule_mirror(grid)
        if output != expected:
            reasons.append(f"demo {index} output does not match the pinned rule")
            continue
        valid_demos.append(pair)

    query_grid = query.get("input") if isinstance(query, dict) else None
    query_output = query.get("output") if isinstance(query, dict) else None
    query_errors = self_check(query_grid)
    if query_errors:
        reasons.append(f"query malformed: {'; '.join(query_errors)}")
    elif query_output != rule_mirror(query_grid):
        reasons.append("query output does not match the pinned rule")

    if len(valid_demos) == len(demos):
        for name, competitor in LESSON_COMPETITORS.items():
            try:
                if all(
                    competitor(pair["input"]) == pair["output"]
                    for pair in valid_demos
                ):
                    reasons.append(f"competitor {name} survives every demo")
            except Exception as exc:
                reasons.append(
                    f"competitor {name} raised {type(exc).__name__}: {exc}"
                )
    return reasons


# These four wrong rules reproduce every public pair.  Generated lessons must
# therefore supply explicit counterexamples; WITNESS_RIVALS binds each shortcut
# to the semantic branch that refutes it.
CANONICAL_SHORTCUTS = {
    "bbox_area": _rival_bbox_area,
    "row_before_column_ties": _rival_row_before_column_ties,
    "color_before_column_ties": _rival_color_before_column_ties,
    "group_same_color": _rival_group_same_color,
}


_mirror = rule_mirror
