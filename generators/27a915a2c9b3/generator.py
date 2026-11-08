"""Generator for 27a915a2c9b3: halo marked rectangle cells.

Each input contains two or three separate solid green rectangles whose
bounding boxes include red marker cells, plus unrelated red distractors on the
black background.  The output paints a clipped 3x3 blue halo around every red
cell inside a valid green-component bounding box.  All interior red markers
remain red; outside red distractors are not markers and are merely ordinary
cells that a nearby halo may overwrite.

Four profiles preserve the complete linked public canvas, rectangle,
inside-marker, and outside-distractor morphology.  A generalized profile
constructs the surrounding lawful family with varied layouts and densities.
"""

from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "27a915a2c9b3"
TASK_ID = "27a915a2c9b3"
VERSION = "4.0.0"
RULE_HASH = "043982b4cb5e"

SUMMARY = (
    "Place red marker cells inside two or three separate filled green "
    "rectangles, together with red background distractors. Paint a clipped "
    "3x3 blue halo around each inside marker while preserving every inside "
    "red marker; outside red cells have no marking role."
)

EXAMPLES_NEEDED = 4
EXPECTED_OUTPUT_CODOMAIN = 1_000_000
OUTPUT_CODOMAIN_BY_DIFFICULTY = {
    "easy": 200_000,
    "medium": 500_000,
    "hard": 1_000_000,
    None: 500_000,
}

INVARIANTS = [
    "inputs use exactly black 0, red 2, and green 3",
    "two or three separate green components each span a filled 2/3 rectangle",
    "every valid rectangle contains at least one red marker",
    "six to thirteen additional red cells lie outside all rectangle bboxes",
    "only red cells inside valid green-component bboxes trigger blue halos",
    "all interior red markers remain red even where their halos overlap",
    "the output shape is unchanged and the input object is never mutated",
]

SCENE_PROFILES = (
    "three_rect_dense_20x20",
    "two_rect_wide_20x20",
    "two_rect_compact_10x17",
    "three_rect_heldout_16x27",
    "generalized",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted complete linked form",
        "valid": "|".join(SCENE_PROFILES),
        "doc": (
            "Recovered jointly from canvas dimensions, the multiset of "
            "rectangle/inside-marker bitmaps modulo D4, and the number of "
            "outside red distractors."
        ),
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()


_PUBLIC_SPECS = {
    "three_rect_dense_20x20": {
        "canvas": (20, 20),
        "rectangles": (
            ((1, 14, 15, 19), ((3, 2), (7, 4), (9, 0))),
            ((13, 19, 3, 12), ((3, 6), (4, 8), (5, 4), (6, 7))),
            (
                (2, 11, 2, 10),
                ((1, 5), (2, 0), (2, 7), (4, 5), (7, 1), (8, 5), (9, 0)),
            ),
        ),
        "external_count": 9,
    },
    "two_rect_wide_20x20": {
        "canvas": (20, 20),
        "rectangles": (
            ((2, 9, 3, 14), ((1, 2), (2, 7), (3, 11), (5, 1))),
            ((13, 19, 8, 16), ((0, 0), (2, 8), (3, 2), (4, 3), (6, 1))),
        ),
        "external_count": 13,
    },
    "two_rect_compact_10x17": {
        "canvas": (10, 17),
        "rectangles": (
            ((3, 7, 9, 14), ((0, 5), (2, 1), (2, 2))),
            ((2, 5, 1, 4), ((1, 3),)),
        ),
        "external_count": 6,
    },
    "three_rect_heldout_16x27": {
        "canvas": (16, 27),
        "rectangles": (
            ((12, 15, 13, 21), ((1, 5), (1, 7), (3, 0), (3, 2), (3, 3))),
            (
                (0, 9, 13, 24),
                ((0, 3), (1, 0), (2, 5), (3, 3), (4, 2), (8, 2), (8, 11)),
            ),
            (
                (2, 10, 3, 10),
                ((1, 7), (2, 4), (3, 0), (5, 3), (7, 2), (7, 3)),
            ),
        ),
        "external_count": 11,
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


def _bitmap_orbit(matrix):
    variants = []
    current = tuple(tuple(row) for row in matrix)
    for _ in range(4):
        variants.extend((current, _flip_horizontal(current)))
        current = _rotate(current)
    return tuple(dict.fromkeys(variants))


def _normal_marker_bitmap(rows, cols, markers):
    marker_set = set(markers)
    bitmap = tuple(
        tuple(int((row, col) in marker_set) for col in range(cols))
        for row in range(rows)
    )
    return min(_bitmap_orbit(bitmap))


def _spec_signature(spec):
    height, width = spec["canvas"]
    rectangle_signatures = []
    for (top, bottom, left, right), markers in spec["rectangles"]:
        rectangle_signatures.append(
            _normal_marker_bitmap(
                bottom - top + 1,
                right - left + 1,
                markers,
            )
        )
    return (
        height,
        width,
        spec["external_count"],
        tuple(sorted(rectangle_signatures)),
    )


_EXACT_SIGNATURES = {
    _spec_signature(spec): profile
    for profile, spec in _PUBLIC_SPECS.items()
}
if len(_EXACT_SIGNATURES) != len(_PUBLIC_SPECS):
    raise RuntimeError("public linked profile signatures overlap")


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


def _components4(cells):
    remaining = set(cells)
    output = []
    while remaining:
        seed = remaining.pop()
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
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        output.append(component)
    return output


def _canonical_rectangles(grid):
    height = len(grid)
    width = len(grid[0])
    three_cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 3
    }
    rectangles = []
    for component in _components4(three_cells):
        top = min(row for row, _col in component)
        bottom = max(row for row, _col in component)
        left = min(col for _row, col in component)
        right = max(col for _row, col in component)
        bbox_cells = {
            (row, col)
            for row in range(top, bottom + 1)
            for col in range(left, right + 1)
        }
        valid = all(grid[row][col] in (2, 3) for row, col in bbox_cells)
        markers = {
            (row, col)
            for row, col in bbox_cells
            if grid[row][col] == 2
        } if valid else set()
        rectangles.append(
            {
                "bbox": (top, bottom, left, right),
                "component": component,
                "bbox_cells": bbox_cells,
                "valid": valid,
                "markers": markers,
            }
        )
    return rectangles


def _analysis_signature(height, width, rectangles, external_count):
    rectangle_signatures = []
    for rectangle in rectangles:
        top, bottom, left, right = rectangle["bbox"]
        offsets = {
            (row - top, col - left)
            for row, col in rectangle["markers"]
        }
        rectangle_signatures.append(
            _normal_marker_bitmap(
                bottom - top + 1,
                right - left + 1,
                offsets,
            )
        )
    return (
        height,
        width,
        external_count,
        tuple(sorted(rectangle_signatures)),
    )


def _inspect_scene(grid):
    original, errors = _coerce_arc_grid(grid)
    if errors:
        return None
    height = len(original)
    width = len(original[0])
    if not 10 <= height <= 24 or not 17 <= width <= 30:
        return None
    if {value for row in original for value in row} != {0, 2, 3}:
        return None

    rectangles = _canonical_rectangles(original)
    if len(rectangles) not in (2, 3):
        return None
    interior = set()
    for rectangle in rectangles:
        top, bottom, left, right = rectangle["bbox"]
        rows = bottom - top + 1
        cols = right - left + 1
        if (
            not rectangle["valid"]
            or not rectangle["markers"]
            or not 4 <= rows <= 14
            or not 4 <= cols <= 12
        ):
            return None
        three_in_bbox = {
            (row, col)
            for row, col in rectangle["bbox_cells"]
            if original[row][col] == 3
        }
        if three_in_bbox != rectangle["component"]:
            return None
        interior.update(rectangle["markers"])

    all_red = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if original[row][col] == 2
    }
    external = all_red - interior
    if not 4 <= len(interior) <= 18 or not 6 <= len(external) <= 13:
        return None
    signature = _analysis_signature(
        height,
        width,
        rectangles,
        len(external),
    )
    profile = _EXACT_SIGNATURES.get(signature, "generalized")
    return {
        "scene_profile": profile,
        "shape": (height, width),
        "rectangles": tuple(rectangles),
        "rectangle_count": len(rectangles),
        "rectangle_dims": tuple(
            sorted(
                (
                    rectangle["bbox"][1] - rectangle["bbox"][0] + 1,
                    rectangle["bbox"][3] - rectangle["bbox"][2] + 1,
                )
                for rectangle in rectangles
            )
        ),
        "marker_counts": tuple(
            sorted(len(rectangle["markers"]) for rectangle in rectangles)
        ),
        "interior_markers": frozenset(interior),
        "interior_count": len(interior),
        "external_markers": frozenset(external),
        "external_count": len(external),
        "signature": signature,
    }


def observe_overrides(grid):
    """Recover every declared semantic override from the returned grid."""
    analysis = _inspect_scene(grid)
    if analysis is None:
        return {}
    return {"scene_profile": analysis["scene_profile"]}


def canonical_profile_index(grid):
    """Return a linked public-profile index, or ``None``."""
    analysis = _inspect_scene(grid)
    if analysis is None or analysis["scene_profile"] == "generalized":
        return None
    return SCENE_PROFILES.index(analysis["scene_profile"])


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
            "expected a 10..24 by 17..30 black 0/red 2/green 3 scene "
            "with two or three separate filled 2/3 rectangle bboxes, "
            "4..18 inside markers, and 6..13 outside red distractors"
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


def _profile_options(difficulty):
    generalized_weight = {
        "easy": 4,
        "medium": 5,
        "hard": 6,
        None: 5,
    }[difficulty]
    return tuple(_PUBLIC_SPECS) + ("generalized",) * generalized_weight


def _transform_absolute(row, col, height, width, flip_vertical, flip_horizontal):
    if flip_vertical:
        row = height - 1 - row
    if flip_horizontal:
        col = width - 1 - col
    return row, col


def _exact_rectangles(profile, rng):
    spec = _PUBLIC_SPECS[profile]
    height, width = spec["canvas"]
    flip_vertical = bool(rng.randrange(2))
    flip_horizontal = bool(rng.randrange(2))
    rectangles = []
    for bbox, marker_offsets in spec["rectangles"]:
        top, bottom, left, right = bbox
        corners = [
            _transform_absolute(
                row,
                col,
                height,
                width,
                flip_vertical,
                flip_horizontal,
            )
            for row in (top, bottom)
            for col in (left, right)
        ]
        transformed_top = min(row for row, _col in corners)
        transformed_bottom = max(row for row, _col in corners)
        transformed_left = min(col for _row, col in corners)
        transformed_right = max(col for _row, col in corners)
        marker_cells = {
            _transform_absolute(
                top + row,
                left + col,
                height,
                width,
                flip_vertical,
                flip_horizontal,
            )
            for row, col in marker_offsets
        }
        rectangles.append(
            {
                "bbox": (
                    transformed_top,
                    transformed_bottom,
                    transformed_left,
                    transformed_right,
                ),
                "markers": marker_cells,
            }
        )

    minimum_row = min(rectangle["bbox"][0] for rectangle in rectangles)
    maximum_row = max(rectangle["bbox"][1] for rectangle in rectangles)
    minimum_col = min(rectangle["bbox"][2] for rectangle in rectangles)
    maximum_col = max(rectangle["bbox"][3] for rectangle in rectangles)
    row_shift = rng.randint(-minimum_row, height - 1 - maximum_row)
    col_shift = rng.randint(-minimum_col, width - 1 - maximum_col)
    shifted = []
    for rectangle in rectangles:
        top, bottom, left, right = rectangle["bbox"]
        shifted.append(
            {
                "bbox": (
                    top + row_shift,
                    bottom + row_shift,
                    left + col_shift,
                    right + col_shift,
                ),
                "markers": {
                    (row + row_shift, col + col_shift)
                    for row, col in rectangle["markers"]
                },
            }
        )
    return height, width, shifted, spec["external_count"]


def _general_canvas_options(difficulty):
    if difficulty == "easy":
        return ((10, 17), (12, 18), (14, 20), (16, 20))
    if difficulty == "hard":
        return ((18, 24), (20, 27), (22, 28), (24, 30), (20, 20))
    return ((14, 20), (16, 22), (18, 24), (20, 20), (16, 27))


def _partition_slots(height, width, rectangle_count, rng):
    layouts = []
    if rectangle_count == 2:
        split_col = width // 2
        layouts.append(
            (
                (0, 0, height, split_col),
                (0, split_col + 1, height, width - split_col - 1),
            )
        )
        split_row = height // 2
        layouts.append(
            (
                (0, 0, split_row, width),
                (split_row + 1, 0, height - split_row - 1, width),
            )
        )
    else:
        usable_width = width - 2
        first_width = usable_width // 3
        second_width = usable_width // 3
        third_width = usable_width - first_width - second_width
        layouts.append(
            (
                (0, 0, height, first_width),
                (0, first_width + 1, height, second_width),
                (
                    0,
                    first_width + second_width + 2,
                    height,
                    third_width,
                ),
            )
        )
        if height >= 14:
            usable_height = height - 2
            first_height = usable_height // 3
            second_height = usable_height // 3
            third_height = usable_height - first_height - second_height
            layouts.append(
                (
                    (0, 0, first_height, width),
                    (first_height + 1, 0, second_height, width),
                    (
                        first_height + second_height + 2,
                        0,
                        third_height,
                        width,
                    ),
                )
            )
        split_row = height // 2
        split_col = width // 2
        layouts.append(
            (
                (0, 0, split_row, split_col),
                (0, split_col + 1, split_row, width - split_col - 1),
                (
                    split_row + 1,
                    0,
                    height - split_row - 1,
                    width,
                ),
            )
        )
    legal = [
        slots
        for slots in layouts
        if all(slot_height >= 4 and slot_width >= 4
               for _top, _left, slot_height, slot_width in slots)
    ]
    if not legal:
        raise RuntimeError("no legal separated rectangle-slot layout")
    return rng.choice(legal)


def _connected(cells):
    if not cells:
        return False
    return len(_components4(cells)) == 1


def _sample_marker_offsets(rows, cols, count, rng):
    cells = [(row, col) for row in range(rows) for col in range(cols)]
    for _ in range(512):
        markers = set(rng.sample(cells, count))
        remaining = set(cells) - markers
        if not _connected(remaining):
            continue
        if (
            not any(row == 0 for row, _col in remaining)
            or not any(row == rows - 1 for row, _col in remaining)
            or not any(col == 0 for _row, col in remaining)
            or not any(col == cols - 1 for _row, col in remaining)
        ):
            continue
        return markers
    raise RuntimeError(
        f"could not sample {count} safe markers in a {rows}x{cols} rectangle"
    )


def _general_rectangles(height, width, difficulty, rng):
    if difficulty == "easy":
        rectangle_count = rng.choice((2, 2, 3))
        marker_bounds = (1, 3)
    elif difficulty == "hard":
        rectangle_count = 3
        marker_bounds = (3, 6)
    else:
        rectangle_count = rng.choice((2, 3))
        marker_bounds = (2, 5)
    slots = _partition_slots(height, width, rectangle_count, rng)
    rectangles = []
    for slot_top, slot_left, slot_height, slot_width in slots:
        maximum_rows = min(slot_height, 14)
        maximum_cols = min(slot_width, 12)
        minimum_rows = max(4, (maximum_rows + 1) // 2)
        minimum_cols = max(4, (maximum_cols + 1) // 2)
        rows = rng.randint(minimum_rows, maximum_rows)
        cols = rng.randint(minimum_cols, maximum_cols)
        top = rng.randint(slot_top, slot_top + slot_height - rows)
        left = rng.randint(slot_left, slot_left + slot_width - cols)
        marker_count = rng.randint(
            marker_bounds[0],
            min(marker_bounds[1], rows * cols - 4),
        )
        offsets = _sample_marker_offsets(rows, cols, marker_count, rng)
        rectangles.append(
            {
                "bbox": (top, top + rows - 1, left, left + cols - 1),
                "markers": {
                    (top + row, left + col)
                    for row, col in offsets
                },
            }
        )
    total_markers = sum(len(rectangle["markers"]) for rectangle in rectangles)
    while total_markers < 4:
        rectangle = rectangles[total_markers % len(rectangles)]
        top, bottom, left, right = rectangle["bbox"]
        rows = bottom - top + 1
        cols = right - left + 1
        count = len(rectangle["markers"]) + 1
        offsets = _sample_marker_offsets(rows, cols, count, rng)
        rectangle["markers"] = {
            (top + row, left + col)
            for row, col in offsets
        }
        total_markers = sum(
            len(candidate["markers"]) for candidate in rectangles
        )
    return rectangles


def _external_range(difficulty):
    if difficulty == "easy":
        return 6, 8
    if difficulty == "hard":
        return 10, 13
    return 8, 11


def _render_scene(
    height,
    width,
    rectangles,
    external_count,
    rng,
):
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for rectangle in rectangles:
        top, bottom, left, right = rectangle["bbox"]
        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                grid[row][col] = 3
        for row, col in rectangle["markers"]:
            grid[row][col] = 2

    interior = {
        marker
        for rectangle in rectangles
        for marker in rectangle["markers"]
    }
    candidates = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 0
    ]
    if len(candidates) < external_count:
        raise RuntimeError("insufficient background for outside distractors")
    selected = []
    near_candidates = [
        (row, col)
        for row, col in candidates
        if any(
            abs(row - marker_row) <= 1
            and abs(col - marker_col) <= 1
            for marker_row, marker_col in interior
        )
    ]
    if near_candidates and rng.randrange(4) == 0:
        selected.append(rng.choice(near_candidates))
    remaining = [cell for cell in candidates if cell not in set(selected)]
    rng.shuffle(remaining)
    selected.extend(remaining[: external_count - len(selected)])
    for row, col in selected:
        grid[row][col] = 2
    return grid


def _construct_exact(profile, context):
    rng = context.draw_rng("scene")
    height, width, rectangles, external_count = _exact_rectangles(profile, rng)
    return _render_scene(
        height,
        width,
        rectangles,
        external_count,
        rng,
    )


def _construct_generalized(difficulty, context):
    rng = context.draw_rng("scene")
    for _ in range(64):
        height, width = rng.choice(_general_canvas_options(difficulty))
        rectangles = _general_rectangles(
            height,
            width,
            difficulty,
            rng,
        )
        external_low, external_high = _external_range(difficulty)
        external_count = rng.randint(external_low, external_high)
        grid = _render_scene(
            height,
            width,
            rectangles,
            external_count,
            rng,
        )
        analysis = _inspect_scene(grid)
        if (
            analysis is not None
            and analysis["scene_profile"] == "generalized"
        ):
            return grid
    raise RuntimeError("could not construct a non-public generalized scene")


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
    profile = context.draw_choice(
        "scene_profile",
        _profile_options(difficulty),
    )
    if profile == "generalized":
        grid = _construct_generalized(difficulty, context)
    else:
        grid = _construct_exact(profile, context)
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
    height = len(original)
    width = len(original[0])
    interior = set()
    for rectangle in _canonical_rectangles(original):
        if rectangle["valid"]:
            interior.update(rectangle["markers"])
    output = [row[:] for row in original]
    for marker_row, marker_col in interior:
        for row in range(max(0, marker_row - 1), min(height, marker_row + 2)):
            for col in range(max(0, marker_col - 1), min(width, marker_col + 2)):
                if (row, col) not in interior:
                    output[row][col] = 1
    return output


_mirror = rule_mirror
