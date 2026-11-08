"""Generator for ad3b40cf: copy the rare color across a symmetry guide.

The demonstrated input grammar is unusually consistent: a square field with
background 8, one centered full guide in color 1, and exactly two structured
object colors on the same side of that guide.  The less frequent object color
is copied (not moved) to the reflected side; the more frequent decoy is left
alone.

Four scene profiles preserve every linked public dimension, guide kind,
palette role, count, and 4-connected component morphology.  Their components
are relocated and reoriented constructively.  A fifth profile composes related
polyomino families on odd square canvases for lawful generalization.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "0591985abf42"
TASK_ID = "0591985abf42"
VERSION = "4.0.0"
RULE_HASH = "d24cc4c70378"

SUMMARY = (
    "Draw a square color-8 field with one centered full color-1 row, "
    "column, or diagonal. Place two structured object colors wholly on one "
    "side: a uniquely least-frequent rare color and a larger decoy. Copy "
    "every rare cell across the guide while preserving its source and all "
    "decoy cells. Four profiles preserve the complete public linked forms; "
    "one profile builds diverse related polyomino scenes."
)

EXAMPLES_NEEDED = 4
EXPECTED_OUTPUT_CODOMAIN = 1_000_000
OUTPUT_CODOMAIN_BY_DIFFICULTY = {
    "easy": 200_000,
    "medium": 500_000,
    "hard": 1_000_000,
    None: 1_000_000,
}

INVARIANTS = [
    "the input is a 9..19 square with strict-mode background color 8",
    "there is exactly one centered full guide, always color 1",
    "exactly two other colors form one to three non-singleton components",
    "all non-guide objects lie strictly on the same side of the guide",
    "the rare color has 4..12 cells and strictly fewer cells than the decoy",
    "every rare reflection is in bounds, distinct, and currently background",
    "the output keeps every source and changes exactly the reflected rare cells",
]

SCENE_PROFILES = (
    "col_9_r4_d5",
    "anti_16_r7_d14",
    "row_15_r7_d12",
    "main_17_r12_d17",
    "generalized",
)
LINE_KINDS = ("row", "col", "anti", "main")
_GENERALIZED_GUIDE_OPTIONS = (
    "row",
    "row",
    "row",
    "row",
    "col",
    "col",
    "col",
    "col",
    "anti",
    "main",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted complete linked form",
        "valid": "|".join(SCENE_PROFILES),
        "doc": (
            "Recovered from dimension, guide kind/position, role colors, "
            "role counts, and D4-normalized component morphologies."
        ),
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()


# Normalized 4-connected component shapes.  Orientation is a nuisance; the
# semantic profile compares each shape through its full D4 orbit.
_DOMINO2 = ((0, 0), (0, 1))
_L3 = ((0, 0), (0, 1), (1, 0))
_I3 = ((0, 0), (0, 1), (0, 2))
_SQUARE4 = ((0, 0), (0, 1), (1, 0), (1, 1))
_T4 = ((0, 0), (0, 1), (0, 2), (1, 1))
_L4 = ((0, 0), (1, 0), (1, 1), (1, 2))
_Z4 = ((0, 0), (0, 1), (1, 1), (1, 2))
_L5 = ((0, 0), (1, 0), (2, 0), (3, 0), (3, 1))
_T5 = ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1))
_RECT6 = (
    (0, 0),
    (0, 1),
    (1, 0),
    (1, 1),
    (2, 0),
    (2, 1),
)
_L6 = ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (3, 2))
_STEM7 = (
    (0, 0),
    (1, 0),
    (2, 0),
    (3, 0),
    (3, 1),
    (4, 0),
    (4, 1),
)
_SQUARE9 = tuple(
    (row, col)
    for row in range(3)
    for col in range(3)
)


_PROFILE_SPECS = {
    "col_9_r4_d5": {
        "size": 9,
        "kind": "col",
        "param": 4,
        "source_sign": 1,
        "rare_color": 5,
        "decoy_color": 2,
        "rare_shapes": (_SQUARE4,),
        "decoy_shapes": (_L5,),
    },
    "anti_16_r7_d14": {
        "size": 16,
        "kind": "anti",
        "param": 15,
        "source_sign": -1,
        "rare_color": 6,
        "decoy_color": 7,
        "rare_shapes": (_L3, _SQUARE4),
        "decoy_shapes": (_RECT6, _T4, _L4),
    },
    "row_15_r7_d12": {
        "size": 15,
        "kind": "row",
        "param": 7,
        "source_sign": -1,
        "rare_color": 2,
        "decoy_color": 6,
        "rare_shapes": (_SQUARE4, _L3),
        "decoy_shapes": (_SQUARE9, _L3),
    },
    "main_17_r12_d17": {
        "size": 17,
        "kind": "main",
        "param": 0,
        "source_sign": 1,
        "rare_color": 7,
        "decoy_color": 4,
        "rare_shapes": (_L3, _STEM7, _DOMINO2),
        "decoy_shapes": (_T5, _L6, _RECT6),
    },
}


# Absolute published cells are stored compactly so the literal calibration
# branch remains independent of data files while still being exactly testable.
_PUBLIC_CELLS = {
    "col_9_r4_d5": {
        "rare": (
            (1, 6),
            (1, 7),
            (2, 6),
            (2, 7),
        ),
        "decoy": (
            (4, 6),
            (5, 6),
            (6, 6),
            (7, 6),
            (7, 7),
        ),
    },
    "anti_16_r7_d14": {
        "rare": (
            (2, 5),
            (3, 5),
            (3, 6),
            (9, 1),
            (9, 2),
            (10, 1),
            (10, 2),
        ),
        "decoy": (
            (1, 1),
            (1, 2),
            (1, 8),
            (1, 9),
            (1, 10),
            (2, 1),
            (2, 2),
            (2, 9),
            (3, 1),
            (3, 2),
            (6, 5),
            (7, 3),
            (7, 4),
            (7, 5),
        ),
    },
    "row_15_r7_d12": {
        "rare": (
            (1, 2),
            (1, 3),
            (2, 2),
            (2, 3),
            (4, 6),
            (4, 7),
            (5, 7),
        ),
        "decoy": (
            (2, 10),
            (2, 11),
            (2, 12),
            (3, 10),
            (3, 11),
            (3, 12),
            (4, 1),
            (4, 10),
            (4, 11),
            (4, 12),
            (5, 1),
            (5, 2),
        ),
    },
    "main_17_r12_d17": {
        "rare": (
            (9, 1),
            (9, 2),
            (10, 1),
            (11, 4),
            (12, 4),
            (13, 4),
            (14, 4),
            (14, 5),
            (15, 4),
            (15, 5),
            (15, 11),
            (15, 12),
        ),
        "decoy": (
            (5, 1),
            (5, 2),
            (5, 3),
            (6, 2),
            (7, 2),
            (12, 7),
            (12, 8),
            (12, 9),
            (13, 1),
            (13, 2),
            (13, 9),
            (14, 1),
            (14, 2),
            (14, 9),
            (15, 1),
            (15, 2),
            (15, 9),
        ),
    },
}


_GENERALIZED_COMPONENTS = {
    "square_vs_t_domino": {
        "rare_shapes": (_SQUARE4,),
        "decoy_shapes": (_T4, _DOMINO2),
    },
    "l_domino_vs_rectangle": {
        "rare_shapes": (_L3, _DOMINO2),
        "decoy_shapes": (_RECT6,),
    },
    "t_l_vs_l_square": {
        "rare_shapes": (_T4, _L3),
        "decoy_shapes": (_L5, _SQUARE4),
    },
    "rectangle_domino_vs_square": {
        "rare_shapes": (_RECT6, _DOMINO2),
        "decoy_shapes": (_SQUARE9,),
    },
    "l_t_vs_rectangle_stem": {
        "rare_shapes": (_L5, _T4),
        "decoy_shapes": (_RECT6, _STEM7),
    },
    "stem_square_vs_square_l": {
        "rare_shapes": (_STEM7, _SQUARE4),
        "decoy_shapes": (_SQUARE9, _L5),
    },
    "line_z_vs_t_rectangle": {
        "rare_shapes": (_I3, _Z4),
        "decoy_shapes": (_T5, _RECT6),
    },
}


def _blank(size, color=8):
    return [
        [color for _col in range(size)]
        for _row in range(size)
    ]


def _guide_cells(size, kind, param):
    if kind == "row":
        return tuple((param, col) for col in range(size))
    if kind == "col":
        return tuple((row, param) for row in range(size))
    if kind == "anti":
        return tuple((row, param - row) for row in range(size))
    return tuple((col + param, col) for col in range(size))


def _render_scene(
    size,
    kind,
    param,
    rare_color,
    decoy_color,
    rare_cells,
    decoy_cells,
):
    grid = _blank(size)
    for row, col in _guide_cells(size, kind, param):
        grid[row][col] = 1
    for row, col in rare_cells:
        grid[row][col] = rare_color
    for row, col in decoy_cells:
        grid[row][col] = decoy_color
    return grid


_PUBLIC_GRIDS = {
    profile: tuple(
        tuple(row)
        for row in _render_scene(
            spec["size"],
            spec["kind"],
            spec["param"],
            spec["rare_color"],
            spec["decoy_color"],
            _PUBLIC_CELLS[profile]["rare"],
            _PUBLIC_CELLS[profile]["decoy"],
        )
    )
    for profile, spec in _PROFILE_SPECS.items()
}
_PUBLIC_GRID_TO_PROFILE = {
    grid: profile
    for profile, grid in _PUBLIC_GRIDS.items()
}


def _normalize_shape(cells):
    minimum_row = min(row for row, _col in cells)
    minimum_col = min(col for _row, col in cells)
    return tuple(sorted(
        (
            row - minimum_row,
            col - minimum_col,
        )
        for row, col in cells
    ))


def _shape_orientations(shape):
    variants = set()
    source = tuple(shape)
    for reflected in (False, True):
        current = tuple(
            (row, -col if reflected else col)
            for row, col in source
        )
        for _rotation in range(4):
            variants.add(_normalize_shape(current))
            current = tuple(
                (col, -row)
                for row, col in current
            )
    return tuple(sorted(variants))


def _canonical_shape(cells):
    return min(_shape_orientations(_normalize_shape(cells)))


def _component_signature(shapes):
    return tuple(sorted(
        _canonical_shape(shape)
        for shape in shapes
    ))


def _spec_signature(spec):
    return (
        spec["size"],
        spec["kind"],
        spec["param"],
        spec["rare_color"],
        spec["decoy_color"],
        sum(len(shape) for shape in spec["rare_shapes"]),
        sum(len(shape) for shape in spec["decoy_shapes"]),
        _component_signature(spec["rare_shapes"]),
        _component_signature(spec["decoy_shapes"]),
    )


_EXACT_SIGNATURES = {
    _spec_signature(spec): profile
    for profile, spec in _PROFILE_SPECS.items()
}


def _coerce_arc_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    first = grid[0]
    width = len(first) if isinstance(first, (list, tuple)) else 0
    if width == 0:
        return None, ["grid rows must be nonempty"]
    if len(grid) > 30 or width > 30:
        return None, ["grid dimensions must not exceed 30x30"]
    converted = []
    errors = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        converted_row = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                converted_row.append(0)
            else:
                converted_row.append(value)
        converted.append(converted_row)
    if errors:
        return None, errors
    return converted, []


def _components4(grid, color):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            queue = [(row, col)]
            seen.add((row, col))
            cells = []
            for current_row, current_col in queue:
                cells.append((current_row, current_col))
                for delta_row, delta_col in (
                    (-1, 0),
                    (1, 0),
                    (0, -1),
                    (0, 1),
                ):
                    candidate = (
                        current_row + delta_row,
                        current_col + delta_col,
                    )
                    if (
                        0 <= candidate[0] < height
                        and 0 <= candidate[1] < width
                        and candidate not in seen
                        and grid[candidate[0]][candidate[1]] == color
                    ):
                        seen.add(candidate)
                        queue.append(candidate)
            components.append(tuple(cells))
    return tuple(components)


def _full_square_guides(grid):
    size = len(grid)
    guides = []
    for row in range(size):
        values = {grid[row][col] for col in range(size)}
        if len(values) == 1 and next(iter(values)) != 8:
            guides.append(("row", row, next(iter(values))))
    for col in range(size):
        values = {grid[row][col] for row in range(size)}
        if len(values) == 1 and next(iter(values)) != 8:
            guides.append(("col", col, next(iter(values))))
    anti_values = {
        grid[index][size - 1 - index]
        for index in range(size)
    }
    if len(anti_values) == 1 and next(iter(anti_values)) != 8:
        guides.append(("anti", size - 1, next(iter(anti_values))))
    main_values = {
        grid[index][index]
        for index in range(size)
    }
    if len(main_values) == 1 and next(iter(main_values)) != 8:
        guides.append(("main", 0, next(iter(main_values))))
    return tuple(guides)


def _mirror_destination(kind, param, row, col):
    if kind == "row":
        return 2 * param - row, col
    if kind == "col":
        return row, 2 * param - col
    if kind == "anti":
        return param - col, param - row
    return col + param, row - param


def _side_value(kind, param, row, col):
    if kind == "row":
        return row - param
    if kind == "col":
        return col - param
    if kind == "anti":
        return row + col - param
    return row - col - param


def _analysis_signature(
    size,
    kind,
    param,
    rare_color,
    decoy_color,
    rare_components,
    decoy_components,
):
    return (
        size,
        kind,
        param,
        rare_color,
        decoy_color,
        sum(len(component) for component in rare_components),
        sum(len(component) for component in decoy_components),
        _component_signature(rare_components),
        _component_signature(decoy_components),
    )


def _analyze_scene(grid):
    original, errors = _coerce_arc_grid(grid)
    if errors:
        return None
    size = len(original)
    if len(original[0]) != size or not 9 <= size <= 19:
        return None
    counts = Counter(
        value
        for row in original
        for value in row
    )
    if len(counts) != 4 or max(counts, key=counts.get) != 8:
        return None
    guides = _full_square_guides(original)
    if len(guides) != 1:
        return None
    kind, param, line_color = guides[0]
    if line_color != 1:
        return None
    if kind in ("row", "col") and 2 * param != size - 1:
        return None
    object_colors = [
        color
        for color in counts
        if color not in (8, 1)
    ]
    if len(object_colors) != 2:
        return None
    object_colors.sort(key=lambda color: counts[color])
    rare_color, decoy_color = object_colors
    if not (
        4 <= counts[rare_color] <= 12
        and counts[rare_color] < counts[decoy_color] <= 20
    ):
        return None
    rare_components = _components4(original, rare_color)
    decoy_components = _components4(original, decoy_color)
    if (
        not 1 <= len(rare_components) <= 3
        or not 1 <= len(decoy_components) <= 3
        or any(
            len(component) < 2
            for component in rare_components + decoy_components
        )
    ):
        return None
    object_cells = tuple(
        (row, col)
        for row in range(size)
        for col in range(size)
        if original[row][col] in (rare_color, decoy_color)
    )
    side_values = tuple(
        _side_value(kind, param, row, col)
        for row, col in object_cells
    )
    if (
        any(value == 0 for value in side_values)
        or len({value < 0 for value in side_values}) != 1
    ):
        return None
    rare_cells = tuple(
        cell
        for component in rare_components
        for cell in component
    )
    reflected_cells = []
    for row, col in rare_cells:
        target_row, target_col = _mirror_destination(
            kind,
            param,
            row,
            col,
        )
        if (
            not 0 <= target_row < size
            or not 0 <= target_col < size
            or original[target_row][target_col] != 8
        ):
            return None
        reflected_cells.append((target_row, target_col))
    if len(set(reflected_cells)) != len(rare_cells):
        return None
    signature = _analysis_signature(
        size,
        kind,
        param,
        rare_color,
        decoy_color,
        rare_components,
        decoy_components,
    )
    profile = _EXACT_SIGNATURES.get(
        signature,
        "generalized",
    )
    frozen = tuple(tuple(row) for row in original)
    return {
        "scene_profile": profile,
        "size": size,
        "kind": kind,
        "param": param,
        "rare_color": rare_color,
        "decoy_color": decoy_color,
        "rare_count": counts[rare_color],
        "decoy_count": counts[decoy_color],
        "rare_components": rare_components,
        "decoy_components": decoy_components,
        "source_sign": -1 if side_values[0] < 0 else 1,
        "reflected_cells": tuple(reflected_cells),
        "exact_public": frozen in _PUBLIC_GRID_TO_PROFILE,
    }


def observe_overrides(grid):
    """Recover every declared semantic axis from the returned grid."""
    analysis = _analyze_scene(grid)
    if analysis is None:
        return {}
    return {
        "scene_profile": analysis["scene_profile"],
    }


def canonical_profile_index(grid):
    """Return the linked public-profile index, or ``None``."""
    analysis = _analyze_scene(grid)
    if analysis is None:
        return None
    profile = analysis["scene_profile"]
    if profile not in _PROFILE_SPECS:
        return None
    return SCENE_PROFILES.index(profile)


def exact_public_profile_index(grid):
    """Return the literal published-input index, or ``None``."""
    original, errors = _coerce_arc_grid(grid)
    if errors:
        return None
    profile = _PUBLIC_GRID_TO_PROFILE.get(
        tuple(tuple(row) for row in original)
    )
    if profile is None:
        return None
    return SCENE_PROFILES.index(profile)


def self_check(grid, *, difficulty=None, meta=None):
    """Strict recognizer for the calibrated symmetry-guide grammar."""
    _original, errors = _coerce_arc_grid(grid)
    if errors:
        return errors
    if difficulty not in (None, "easy", "medium", "hard"):
        return [
            "difficulty must be easy, medium, hard, or None"
        ]
    analysis = _analyze_scene(grid)
    if analysis is None:
        return [
            "expected a 9..19 square color-8 field with one centered "
            "color-1 guide and two structured, strictly count-ordered "
            "object colors on one side with blank rare reflections"
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
    if difficulty == "easy":
        generalized_weight = 5
    elif difficulty == "hard":
        generalized_weight = 8
    else:
        generalized_weight = 6
    # The public training median is axial (one row, one column, one
    # diagonal).  Duplicate the two axial linked profiles so the generated
    # component-count distribution does not become diagonal-dominated.
    exact_options = (
        "col_9_r4_d5",
        "anti_16_r7_d14",
        "row_15_r7_d12",
        "row_15_r7_d12",
        "main_17_r12_d17",
    )
    return exact_options + ("generalized",) * generalized_weight


def _generalized_sizes(difficulty):
    if difficulty == "easy":
        return (11, 13, 15)
    if difficulty == "medium":
        return (13, 15, 17)
    if difficulty == "hard":
        return (15, 17, 19)
    return (11, 13, 15, 17, 19)


def _placement_candidates(size, kind, param, source_sign, shape):
    candidates = set()
    for orientation in _shape_orientations(shape):
        shape_height = 1 + max(row for row, _col in orientation)
        shape_width = 1 + max(col for _row, col in orientation)
        for top in range(size - shape_height + 1):
            for left in range(size - shape_width + 1):
                cells = tuple(
                    (top + row, left + col)
                    for row, col in orientation
                )
                if all(
                    source_sign
                    * _side_value(kind, param, row, col)
                    > 0
                    for row, col in cells
                ):
                    candidates.add(tuple(sorted(cells)))
    return list(sorted(candidates))


def _has_cardinal_contact(cells, occupied):
    return any(
        neighbor in occupied
        for row, col in cells
        for neighbor in (
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        )
    )


def _place_components(
    size,
    kind,
    param,
    source_sign,
    rare_shapes,
    decoy_shapes,
    rng,
):
    entries = [
        ("rare", index, shape)
        for index, shape in enumerate(rare_shapes)
    ] + [
        ("decoy", index, shape)
        for index, shape in enumerate(decoy_shapes)
    ]
    entries.sort(
        key=lambda entry: (
            -len(entry[2]),
            entry[0],
            entry[1],
        )
    )
    candidates = []
    for role, index, shape in entries:
        options = _placement_candidates(
            size,
            kind,
            param,
            source_sign,
            shape,
        )
        rng.shuffle(options)
        candidates.append((role, index, options))
    chosen = {}
    occupied = set()
    nodes = 0

    def search(entry_index):
        nonlocal nodes
        if entry_index == len(candidates):
            return True
        role, shape_index, options = candidates[entry_index]
        for cells in options:
            nodes += 1
            if nodes > 250_000:
                return False
            cell_set = set(cells)
            if cell_set & occupied:
                continue
            if _has_cardinal_contact(cells, occupied):
                continue
            chosen[(role, shape_index)] = cells
            occupied.update(cell_set)
            if search(entry_index + 1):
                return True
            occupied.difference_update(cell_set)
            del chosen[(role, shape_index)]
        return False

    if not search(0):
        raise RuntimeError(
            "component layout has no bounded non-touching placement"
        )
    rare_cells = tuple(
        cell
        for index in range(len(rare_shapes))
        for cell in chosen[("rare", index)]
    )
    decoy_cells = tuple(
        cell
        for index in range(len(decoy_shapes))
        for cell in chosen[("decoy", index)]
    )
    return rare_cells, decoy_cells


def _construct_spec_scene(
    spec,
    layout_rng,
    *,
    allow_side_flip=False,
):
    source_sign = spec["source_sign"]
    if allow_side_flip and layout_rng.randrange(2):
        source_sign *= -1
    rare_cells, decoy_cells = _place_components(
        spec["size"],
        spec["kind"],
        spec["param"],
        source_sign,
        spec["rare_shapes"],
        spec["decoy_shapes"],
        layout_rng,
    )
    return _render_scene(
        spec["size"],
        spec["kind"],
        spec["param"],
        spec["rare_color"],
        spec["decoy_color"],
        rare_cells,
        decoy_cells,
    )


def _construct_generalized_scene(context):
    size = context.draw_choice(
        "grid_size",
        _generalized_sizes(context.difficulty),
    )
    # Training demonstrates one row, one column, and one diagonal guide.
    # Weighting the two axial kinds twice keeps color-component complexity
    # calibrated while retaining both diagonal variants in every band.
    kind = context.draw_choice(
        "guide_kind",
        _GENERALIZED_GUIDE_OPTIONS,
    )
    source_sign = context.draw_choice(
        "source_side",
        (-1, 1),
    )
    family_names = tuple(_GENERALIZED_COMPONENTS)
    if size == 11:
        family_names = family_names[:4]
    family_name = context.draw_choice(
        "component_family",
        family_names,
    )
    component_spec = _GENERALIZED_COMPONENTS[family_name]
    rare_color, decoy_color = context.draw_distinct_colors(
        "object_colors",
        n=2,
        exclude=(1, 8),
    )
    if kind in ("row", "col"):
        param = (size - 1) // 2
    elif kind == "anti":
        param = size - 1
    else:
        param = 0
    spec = {
        "size": size,
        "kind": kind,
        "param": param,
        "source_sign": source_sign,
        "rare_color": rare_color,
        "decoy_color": decoy_color,
        "rare_shapes": component_spec["rare_shapes"],
        "decoy_shapes": component_spec["decoy_shapes"],
    }
    return _construct_spec_scene(
        spec,
        context.draw_rng("layout"),
    )


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(
            "unknown override(s): " + ", ".join(unknown)
        )
    profile = overrides.get("scene_profile")
    if profile is not None and profile not in SCENE_PROFILES:
        raise ValueError("unknown scene_profile")


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
    literal_rng = context.draw_rng("literal_public")
    if (
        profile in _PROFILE_SPECS
        and literal_rng.randrange(40) == 0
    ):
        grid = [
            list(row)
            for row in _PUBLIC_GRIDS[profile]
        ]
    elif profile == "generalized":
        grid = _construct_generalized_scene(context)
    else:
        grid = _construct_spec_scene(
            _PROFILE_SPECS[profile],
            context.draw_rng("layout"),
            allow_side_flip=True,
        )
    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": overrides},
    )
    if errors:
        raise RuntimeError(
            "constructed an invalid calibrated scene: "
            + "; ".join(errors)
        )
    if rule_mirror(grid) == grid:
        raise RuntimeError("constructed an identity rule example")
    return grid


def _mode_reading_order(grid):
    counts = {}
    for row in grid:
        for value in row:
            counts[value] = counts.get(value, 0) + 1
    return max(counts, key=counts.get)


def _priority_guide(grid, background):
    height = len(grid)
    width = len(grid[0])
    for row in range(height):
        value = grid[row][0]
        if (
            value != background
            and all(grid[row][col] == value for col in range(width))
        ):
            return "row", row, value
    for col in range(width):
        value = grid[0][col]
        if (
            value != background
            and all(grid[row][col] == value for row in range(height))
        ):
            return "col", col, value
    minimum_length = min(height, width)
    for param in range(height + width - 1):
        cells = tuple(
            (row, param - row)
            for row in range(height)
            if 0 <= param - row < width
        )
        if len(cells) < minimum_length:
            continue
        value = grid[cells[0][0]][cells[0][1]]
        if (
            value != background
            and all(grid[row][col] == value for row, col in cells)
        ):
            return "anti", param, value
    for param in range(-height, width):
        cells = tuple(
            (col + param, col)
            for col in range(width)
            if 0 <= col + param < height
        )
        if len(cells) < minimum_length:
            continue
        value = grid[cells[0][0]][cells[0][1]]
        if (
            value != background
            and all(grid[row][col] == value for row, col in cells)
        ):
            return "main", param, value
    return None


def rule_mirror(grid):
    """Input-pure Python mirror of the complete canonical Racket rule."""
    original, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [row[:] for row in original]
    height = len(original)
    width = len(original[0])
    background = _mode_reading_order(original)
    guide = _priority_guide(original, background)
    if guide is None:
        return output
    kind, param, line_color = guide
    values = [
        original[row][col]
        for row in range(height)
        for col in range(width)
        if original[row][col] not in (background, line_color)
    ]
    if not values:
        return output
    counts = Counter(values)
    reading_order_colors = tuple(dict.fromkeys(values))
    reflect_color = min(
        reading_order_colors,
        key=lambda color: counts[color],
    )
    for row in range(height):
        for col in range(width):
            if original[row][col] != reflect_color:
                continue
            target_row, target_col = _mirror_destination(
                kind,
                param,
                row,
                col,
            )
            if 0 <= target_row < height and 0 <= target_col < width:
                output[target_row][target_col] = reflect_color
    return output
