"""Generator for bfb4c6fb3c1a: select dihedrally congruent objects.

The blue object is the reference.  Exactly three red candidates occupy the
other three scene quadrants: two are rotations/reflections of the reference
and one is not.  The rule preserves the scene while recoloring the two
matching candidates cyan.

All five complete public input profiles are represented.  Generalized draws
retain their linked canvas/reference/decoy profile while varying object
orientation, within-quadrant position, decoration color, and a provably
equivariant whole-scene reflection or 180-degree rotation.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "bfb4c6fb3c1a"
TASK_ID = "bfb4c6fb3c1a"
VERSION = "3.0.0"
RULE_HASH = "7e507ba2c64f"

SUMMARY = (
    "Use the blue object as a reference shape. Recolor each red object cyan "
    "exactly when its normalized cells match the reference under a rotation "
    "or reflection; preserve the reference, decoy, marker, and background."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "zero is the background; blue 1 is the single reference object",
    "exactly three red 2 objects are present",
    "exactly two red objects are dihedrally congruent to the reference",
    "the remaining red object belongs to the profile's linked decoy class",
    "one isolated non-{0,1,2,8} decoration cell occupies an outer corner",
    "the reference, two matches, and decoy occupy four distinct quadrants",
    "only matching red cells change, from 2 to cyan 8",
]

SCENE_PROFILES = (
    "l3_9x10",
    "l4_10x12",
    "t4_9x11",
    "u5_10x12",
    "stair5_9x12",
)

SCENE_TRANSFORMS = (
    "identity",
    "horizontal",
    "vertical",
    "rotated_180",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted complete public shape family",
        "valid": "l3_9x10|l4_10x12|t4_9x11|u5_10x12|stair5_9x12",
        "doc": (
            "Linked canvas, reference shape class, and nonmatching decoy "
            "shape class from one complete public input profile."
        ),
    },
    "scene_transform": {
        "type": "str",
        "default": "40% identity; 20% each reflection/180-degree rotation",
        "valid": "identity|horizontal|vertical|rotated_180",
        "doc": (
            "Whole-scene transform, observable from the reference quadrant. "
            "The canonical rule commutes with every listed transform."
        ),
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

_DECORATION_COLORS = (3, 4, 5, 6, 7, 9)
_CORNERS = ("top_left", "top_right", "bottom_left", "bottom_right")

_PROFILE_DATA = {
    "l3_9x10": {
        "canvas": (9, 10),
        "reference": ((0, 0), (1, 0), (1, 1)),
        "decoy": ((0, 0), (0, 1), (0, 2), (1, 1)),
        "canonical": (
            "0000000000",
            "0100002000",
            "0110002200",
            "0000000000",
            "0000000000",
            "0220002220",
            "0200000200",
            "0000000000",
            "0000000007",
        ),
    },
    "l4_10x12": {
        "canvas": (10, 12),
        "reference": ((0, 0), (1, 0), (2, 0), (2, 1)),
        "decoy": ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
        "canonical": (
            "000000000000",
            "010000022000",
            "010000020000",
            "011000020000",
            "000000000000",
            "002200002000",
            "000200002200",
            "000200000220",
            "000000000000",
            "000000000004",
        ),
    },
    "t4_9x11": {
        "canvas": (9, 11),
        "reference": ((0, 0), (0, 1), (0, 2), (1, 1)),
        "decoy": ((0, 0), (1, 0), (1, 1)),
        "canonical": (
            "00000000000",
            "01110000200",
            "00100002200",
            "00000000200",
            "00000000000",
            "00200002000",
            "02220002200",
            "00000000000",
            "90000000000",
        ),
    },
    "u5_10x12": {
        "canvas": (10, 12),
        "reference": ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
        "decoy": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        "canonical": (
            "000000000000",
            "010100020200",
            "011100022200",
            "000000000000",
            "000000000000",
            "002220000200",
            "002020002220",
            "000000000200",
            "000000000000",
            "600000000000",
        ),
    },
    "stair5_9x12": {
        "canvas": (9, 12),
        "reference": ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
        "decoy": ((0, 0), (1, 0), (2, 0), (2, 1)),
        "canonical": (
            "000000000005",
            "010000000220",
            "011000002200",
            "001100002000",
            "000000000000",
            "000220000200",
            "002200000200",
            "002000000220",
            "000000000000",
        ),
    },
}

_PUBLIC_GRIDS = {
    profile: tuple(
        tuple(int(value) for value in row)
        for row in data["canonical"]
    )
    for profile, data in _PROFILE_DATA.items()
}

_PROFILE_INDEX = {
    profile: index
    for index, profile in enumerate(SCENE_PROFILES)
}

_EXPECTED_ROLE_QUADRANTS = {
    "identity": {
        "reference": "top_left",
        "matches": frozenset(("top_right", "bottom_left")),
        "decoy": "bottom_right",
    },
    "horizontal": {
        "reference": "top_right",
        "matches": frozenset(("top_left", "bottom_right")),
        "decoy": "bottom_left",
    },
    "vertical": {
        "reference": "bottom_left",
        "matches": frozenset(("top_left", "bottom_right")),
        "decoy": "top_right",
    },
    "rotated_180": {
        "reference": "bottom_right",
        "matches": frozenset(("top_right", "bottom_left")),
        "decoy": "top_left",
    },
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


def _normalize(cells):
    cells = tuple(cells)
    if not cells:
        return ()
    row0 = min(row for row, _col in cells)
    col0 = min(col for _row, col in cells)
    return tuple(
        sorted((row - row0, col - col0) for row, col in cells)
    )


def _rotate90(cells):
    normalized = _normalize(cells)
    height = max(row for row, _col in normalized) + 1
    return _normalize(
        (col, height - 1 - row)
        for row, col in normalized
    )


def _reflect_rows(cells):
    normalized = _normalize(cells)
    height = max(row for row, _col in normalized) + 1
    return _normalize(
        (height - 1 - row, col)
        for row, col in normalized
    )


def _dihedral_forms(cells):
    forms = set()
    current = _normalize(cells)
    for _index in range(4):
        forms.add(current)
        forms.add(_reflect_rows(current))
        current = _rotate90(current)
    return tuple(sorted(forms))


def _dihedral_key(cells):
    return min(_dihedral_forms(cells))


def _components(grid, color=None):
    height = len(grid)
    width = len(grid[0])
    if color is None:
        remaining = {
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] != 0
        }
    else:
        remaining = {
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == color
        }
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        cells = []
        while queue:
            row, col = queue.popleft()
            cells.append((row, col))
            for delta_row, delta_col in (
                (-1, 0),
                (0, -1),
                (0, 1),
                (1, 0),
            ):
                candidate = (row + delta_row, col + delta_col)
                if candidate in remaining:
                    remaining.remove(candidate)
                    queue.append(candidate)
        result.append(tuple(sorted(cells)))
    return sorted(result, key=lambda cells: cells[0])


def _quadrant(cells, height, width):
    center_row = sum(row for row, _col in cells) / len(cells)
    center_col = sum(col for _row, col in cells) / len(cells)
    vertical = "bottom" if center_row >= height / 2 else "top"
    horizontal = "right" if center_col >= width / 2 else "left"
    return f"{vertical}_{horizontal}"


def _outer_corner(row, col, height, width):
    mapping = {
        (0, 0): "top_left",
        (0, width - 1): "top_right",
        (height - 1, 0): "bottom_left",
        (height - 1, width - 1): "bottom_right",
    }
    return mapping.get((row, col))


def _analyze_scene(grid):
    """Recover the linked profile and every declared returned-grid axis."""
    original, errors = _coerce_arc_grid(grid)
    if errors:
        return None
    height = len(original)
    width = len(original[0])
    if any(8 in row for row in original):
        return None

    references = _components(original, 1)
    candidates = _components(original, 2)
    decorations = [
        (row, col, value)
        for row, values in enumerate(original)
        for col, value in enumerate(values)
        if value not in (0, 1, 2)
    ]
    if (
        len(references) != 1
        or len(candidates) != 3
        or len(decorations) != 1
        or decorations[0][2] not in _DECORATION_COLORS
        or len(_components(original)) != 5
    ):
        return None

    decoration_row, decoration_col, decoration_color = decorations[0]
    decoration_corner = _outer_corner(
        decoration_row,
        decoration_col,
        height,
        width,
    )
    if decoration_corner is None:
        return None

    reference = references[0]
    reference_key = _dihedral_key(reference)
    matches = [
        cells
        for cells in candidates
        if _dihedral_key(cells) == reference_key
    ]
    decoys = [
        cells
        for cells in candidates
        if _dihedral_key(cells) != reference_key
    ]
    if len(matches) != 2 or len(decoys) != 1:
        return None
    decoy_key = _dihedral_key(decoys[0])

    profile = next(
        (
            name
            for name, data in _PROFILE_DATA.items()
            if data["canvas"] == (height, width)
            and _dihedral_key(data["reference"]) == reference_key
            and _dihedral_key(data["decoy"]) == decoy_key
        ),
        None,
    )
    if profile is None:
        return None

    reference_quadrant = _quadrant(reference, height, width)
    transform = next(
        (
            name
            for name, roles in _EXPECTED_ROLE_QUADRANTS.items()
            if roles["reference"] == reference_quadrant
        ),
        None,
    )
    if transform is None:
        return None
    expected = _EXPECTED_ROLE_QUADRANTS[transform]
    if (
        frozenset(
            _quadrant(cells, height, width)
            for cells in matches
        )
        != expected["matches"]
        or _quadrant(decoys[0], height, width) != expected["decoy"]
    ):
        return None

    exact_public = (
        transform == "identity"
        and tuple(tuple(row) for row in original) == _PUBLIC_GRIDS[profile]
    )
    return {
        "scene_profile": profile,
        "scene_transform": transform,
        "decoration_corner": decoration_corner,
        "decoration_color": decoration_color,
        "reference": reference,
        "matches": tuple(matches),
        "decoy": decoys[0],
        "exact_public": exact_public,
    }


def observe_overrides(grid):
    """Recover all declared semantic controls only from the returned grid."""
    analysis = _analyze_scene(grid)
    if analysis is None:
        return {}
    return {
        "scene_profile": analysis["scene_profile"],
        "scene_transform": analysis["scene_transform"],
    }


def canonical_profile_index(grid):
    """Return the complete linked public-family profile index."""
    analysis = _analyze_scene(grid)
    if analysis is None:
        return None
    return _PROFILE_INDEX[analysis["scene_profile"]]


def exact_public_profile_index(grid):
    """Return the public input index only for a literal canonical input."""
    analysis = _analyze_scene(grid)
    if analysis is None or not analysis["exact_public"]:
        return None
    return _PROFILE_INDEX[analysis["scene_profile"]]


def self_check(grid, *, difficulty=None, meta=None):
    """Strictly recognize the complete calibrated scene grammar."""
    original, errors = _coerce_arc_grid(grid)
    if errors:
        return errors
    if difficulty not in (None, "easy", "medium", "hard"):
        return ["difficulty must be easy, medium, hard, or None"]
    analysis = _analyze_scene(original)
    if analysis is None:
        return [
            "grid must contain one linked public-profile reference, exactly "
            "two congruent candidates, one profile decoy, and one corner marker"
        ]
    if isinstance(meta, dict):
        requested = meta.get("overrides")
        if not isinstance(requested, dict):
            requested = meta
        for axis in AXES:
            if (
                axis in requested
                and requested[axis] is not None
                and analysis[axis] != requested[axis]
            ):
                errors.append(
                    f"{axis} requested {requested[axis]!r}, "
                    f"observed {analysis[axis]!r}"
                )
    return errors


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
    if (
        "scene_transform" in overrides
        and overrides["scene_transform"] not in SCENE_TRANSFORMS
    ):
        raise ValueError("unknown scene_transform")


def _profile_options(difficulty):
    if difficulty == "easy":
        return (
            "l3_9x10",
            "l3_9x10",
            "l3_9x10",
            "l4_10x12",
            "l4_10x12",
            "t4_9x11",
            "t4_9x11",
            "u5_10x12",
            "stair5_9x12",
        )
    if difficulty == "hard":
        return (
            "l3_9x10",
            "l4_10x12",
            "t4_9x11",
            "t4_9x11",
            "u5_10x12",
            "u5_10x12",
            "u5_10x12",
            "stair5_9x12",
            "stair5_9x12",
            "stair5_9x12",
        )
    return SCENE_PROFILES


def _place_in_slot(grid, rng, shape, slot, color):
    row1, col1, row2, col2 = slot
    shape_height = max(row for row, _col in shape) + 1
    shape_width = max(col for _row, col in shape) + 1
    max_row = row2 - shape_height + 1
    max_col = col2 - shape_width + 1
    if max_row < row1 or max_col < col1:
        raise RuntimeError("profile shape does not fit its constructive slot")
    origin_row = rng.randint(row1, max_row)
    origin_col = rng.randint(col1, max_col)
    for row, col in shape:
        grid[origin_row + row][origin_col + col] = color


def _corner_position(corner, height, width):
    return {
        "top_left": (0, 0),
        "top_right": (0, width - 1),
        "bottom_left": (height - 1, 0),
        "bottom_right": (height - 1, width - 1),
    }[corner]


def _transform_grid(grid, transform):
    if transform == "identity":
        return [row[:] for row in grid]
    if transform == "horizontal":
        return [list(reversed(row)) for row in grid]
    if transform == "vertical":
        return [row[:] for row in reversed(grid)]
    if transform == "rotated_180":
        return [
            list(reversed(row))
            for row in reversed(grid)
        ]
    raise ValueError(f"unknown scene transform: {transform}")


def _render_generalized(profile, transform, rng):
    data = _PROFILE_DATA[profile]
    height, width = data["canvas"]
    grid = [
        [0 for _col in range(width)]
        for _row in range(height)
    ]

    row_mid = height // 2
    col_mid = width // 2
    slots = {
        "top_left": (1, 1, row_mid - 1, col_mid - 1),
        "top_right": (1, col_mid + 1, row_mid - 1, width - 2),
        "bottom_left": (
            row_mid + 1,
            1,
            height - 2,
            col_mid - 1,
        ),
        "bottom_right": (
            row_mid + 1,
            col_mid + 1,
            height - 2,
            width - 2,
        ),
    }

    reference_forms = _dihedral_forms(data["reference"])
    decoy_forms = _dihedral_forms(data["decoy"])
    _place_in_slot(
        grid,
        rng,
        rng.choice(reference_forms),
        slots["top_left"],
        1,
    )
    _place_in_slot(
        grid,
        rng,
        rng.choice(reference_forms),
        slots["top_right"],
        2,
    )
    _place_in_slot(
        grid,
        rng,
        rng.choice(reference_forms),
        slots["bottom_left"],
        2,
    )
    _place_in_slot(
        grid,
        rng,
        rng.choice(decoy_forms),
        slots["bottom_right"],
        2,
    )

    decoration_corner = rng.choice(_CORNERS)
    decoration_row, decoration_col = _corner_position(
        decoration_corner,
        height,
        width,
    )
    grid[decoration_row][decoration_col] = rng.choice(_DECORATION_COLORS)
    transformed = _transform_grid(grid, transform)

    if (
        transform == "identity"
        and tuple(tuple(row) for row in transformed)
        == _PUBLIC_GRIDS[profile]
    ):
        for row_index, row in enumerate(transformed):
            for col_index, value in enumerate(row):
                if value in _DECORATION_COLORS:
                    color_index = _DECORATION_COLORS.index(value)
                    transformed[row_index][col_index] = _DECORATION_COLORS[
                        (color_index + 1) % len(_DECORATION_COLORS)
                    ]
                    return transformed
    return transformed


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice(
        "scene_profile",
        _profile_options(difficulty),
    )
    transform = ctx.draw_choice(
        "scene_transform",
        (
            "identity",
            "identity",
            "horizontal",
            "vertical",
            "rotated_180",
        ),
    )
    rng = ctx.draw_rng("layout")

    # A small literal-input rehearsal prior retains all five public scenes
    # without turning the generator into a memorization-heavy template stream.
    literal_public = transform == "identity" and rng.random() < 0.125
    if literal_public:
        grid = [list(row) for row in _PUBLIC_GRIDS[profile]]
    else:
        grid = _render_generalized(profile, transform, rng)

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
    return grid


def rule_mirror(grid):
    """Broad, input-pure Python mirror of the canonical Racket rule."""
    original, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    references = _components(original, 1)
    if not references:
        raise ValueError("the rule requires at least one blue reference object")
    reference = sorted(
        references,
        key=lambda cells: (-len(cells), cells[0]),
    )[0]
    reference_key = _dihedral_key(reference)
    output = [row[:] for row in original]
    for candidate in _components(original, 2):
        if _dihedral_key(candidate) != reference_key:
            continue
        for row, col in candidate:
            output[row][col] = 8
    return output
