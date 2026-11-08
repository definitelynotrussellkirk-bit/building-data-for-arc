"""Generator for 19c55a8731b1: recolor a lattice from its key.

A filled color key and a rectangular lattice of identical gray 3x3 shapes
occupy disjoint regions of a 23x23 canvas.  The key has one cell per lattice
tile.  The output preserves the key and background while replacing every gray
cell in tile ``(r, c)`` with key color ``(r, c)``.

Three profiles preserve the complete public key-equality pattern, tile shape,
and lattice dimensions (including the visible held-out 5x4 extreme).  A
generalized profile samples the surrounding lawful key and tile-shape space.
"""

from __future__ import annotations

from itertools import product

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "19c55a8731b1"
TASK_ID = "19c55a8731b1"
VERSION = "4.0.0"
RULE_HASH = "3f7c11b1e8c8"

SUMMARY = (
    "Place a repeated-color key beside a matching lattice of identical gray "
    "3x3 shapes. Recolor each complete gray tile from the corresponding key "
    "cell while preserving the key and background."
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
    "the calibrated input is a 23x23 grid with black background and gray tiles",
    "the non-black/non-gray key is one filled 3..5 by 3..5 rectangle",
    "the key dimensions exactly equal the number of tile rows and columns",
    "every gray tile has one shared connected 3x3 mask and four-cell pitch",
    "key colors repeat, and every gray cell changes to its indexed key color",
    "the key, all background cells, and the input grid itself are preserved",
]

SCENE_PROFILES = (
    "key4x4_hourglass",
    "key3x5_frame",
    "key5x4_open_bottom",
    "generalized",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted complete linked form",
        "valid": "|".join(SCENE_PROFILES),
        "doc": (
            "Recovered jointly from key dimensions/equality pattern and the "
            "repeated gray 3x3 tile mask, modulo valid scene symmetries."
        ),
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

_CANVAS = 23
_LEGAL_KEY_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)

_PUBLIC_SPECS = {
    "key4x4_hourglass": {
        "key": (
            (1, 8, 1, 8),
            (8, 8, 1, 1),
            (1, 1, 4, 1),
            (1, 1, 4, 4),
        ),
        "mask": (
            (1, 1, 1),
            (0, 1, 0),
            (1, 1, 1),
        ),
    },
    "key3x5_frame": {
        "key": (
            (2, 1, 1, 3, 1),
            (1, 2, 2, 1, 1),
            (2, 1, 2, 3, 2),
        ),
        "mask": (
            (1, 1, 1),
            (1, 0, 1),
            (1, 1, 1),
        ),
    },
    "key5x4_open_bottom": {
        "key": (
            (2, 1, 2, 2),
            (8, 1, 4, 4),
            (3, 1, 4, 4),
            (8, 1, 3, 1),
            (8, 1, 1, 1),
        ),
        "mask": (
            (1, 1, 1),
            (1, 0, 1),
            (1, 0, 1),
        ),
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


def _normalize_labels(matrix):
    labels = {}
    output = []
    for row in matrix:
        output_row = []
        for value in row:
            if value not in labels:
                labels[value] = len(labels)
            output_row.append(labels[value])
        output.append(tuple(output_row))
    return tuple(output)


def _scene_variants(key, mask):
    variants = []
    current_key = tuple(tuple(row) for row in key)
    current_mask = tuple(tuple(row) for row in mask)
    for _ in range(4):
        for candidate_key, candidate_mask in (
            (current_key, current_mask),
            (
                _flip_horizontal(current_key),
                _flip_horizontal(current_mask),
            ),
        ):
            normalized_key = _normalize_labels(candidate_key)
            if (
                candidate_mask[0] == (1, 1, 1)
                and all(any(row) for row in candidate_mask)
                and (len(normalized_key), len(normalized_key[0])) != (5, 5)
            ):
                pair = (normalized_key, candidate_mask)
                if pair not in variants:
                    variants.append(pair)
        current_key = _rotate(current_key)
        current_mask = _rotate(current_mask)
    return tuple(variants)


_PROFILE_VARIANTS = {
    profile: _scene_variants(spec["key"], spec["mask"])
    for profile, spec in _PUBLIC_SPECS.items()
}
_EXACT_SIGNATURES = {
    pair: profile
    for profile, pairs in _PROFILE_VARIANTS.items()
    for pair in pairs
}
if len(_EXACT_SIGNATURES) != sum(
    len(pairs) for pairs in _PROFILE_VARIANTS.values()
):
    raise RuntimeError("public profile symmetry orbits overlap")


def _mask_connected(mask):
    cells = {
        (row, col)
        for row in range(3)
        for col in range(3)
        if mask[row][col]
    }
    if not cells:
        return False
    reached = {next(iter(cells))}
    stack = list(reached)
    while stack:
        row, col = stack.pop()
        for neighbor in (
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        ):
            if neighbor in cells and neighbor not in reached:
                reached.add(neighbor)
                stack.append(neighbor)
    return reached == cells


def _build_masks():
    masks = []
    for tail in product((0, 1), repeat=6):
        mask = (
            (1, 1, 1),
            tuple(tail[:3]),
            tuple(tail[3:]),
        )
        count = sum(value for row in mask for value in row)
        if (
            5 <= count <= 9
            and all(any(row) for row in mask)
            and _mask_connected(mask)
        ):
            masks.append(mask)
    return tuple(masks)


_GENERAL_MASKS = _build_masks()
if not _GENERAL_MASKS:
    raise RuntimeError("generalized tile-mask inventory is empty")


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
                return [], ["grid values must be integer ARC colors 0..9"]
            output_row.append(value)
        output.append(output_row)
    return output, errors


def _runs(values):
    values = sorted(set(values))
    if not values:
        return ()
    runs = [[values[0]]]
    for value in values[1:]:
        if value == runs[-1][-1] + 1:
            runs[-1].append(value)
        else:
            runs.append([value])
    return tuple(tuple(run) for run in runs)


def _inspect_scene(grid):
    original, errors = _coerce_arc_grid(grid)
    if errors or len(original) != _CANVAS or len(original[0]) != _CANVAS:
        return None
    if 0 not in {value for row in original for value in row}:
        return None

    key_cells = [
        (row, col, original[row][col])
        for row in range(_CANVAS)
        for col in range(_CANVAS)
        if original[row][col] not in (0, 5)
    ]
    gray = {
        (row, col)
        for row in range(_CANVAS)
        for col in range(_CANVAS)
        if original[row][col] == 5
    }
    if not key_cells or not gray:
        return None

    key_top = min(row for row, _col, _value in key_cells)
    key_bottom = max(row for row, _col, _value in key_cells)
    key_left = min(col for _row, col, _value in key_cells)
    key_right = max(col for _row, col, _value in key_cells)
    key = tuple(
        tuple(
            original[row][col]
            for col in range(key_left, key_right + 1)
        )
        for row in range(key_top, key_bottom + 1)
    )
    key_rows = len(key)
    key_cols = len(key[0])
    key_colors = {value for row in key for value in row}
    if (
        not 3 <= key_rows <= 5
        or not 3 <= key_cols <= 5
        or (key_rows, key_cols) == (5, 5)
        or len(key_cells) != key_rows * key_cols
        or any(value in (0, 5) for row in key for value in row)
        or not 2 <= len(key_colors) <= 5
        or len(key_colors) == key_rows * key_cols
    ):
        return None

    row_runs = _runs(row for row, _col in gray)
    top = min(row for row, _col in gray)
    col_runs = _runs(col for row, col in gray if row == top)
    if (
        len(row_runs) != key_rows
        or len(col_runs) != key_cols
        or any(len(run) != 3 for run in row_runs)
        or any(len(run) != 3 for run in col_runs)
    ):
        return None
    row_starts = tuple(run[0] for run in row_runs)
    col_starts = tuple(run[0] for run in col_runs)
    if (
        any(b - a != 4 for a, b in zip(row_starts, row_starts[1:]))
        or any(b - a != 4 for a, b in zip(col_starts, col_starts[1:]))
    ):
        return None

    masks = []
    covered = set()
    for tile_top in row_starts:
        for tile_left in col_starts:
            mask = tuple(
                tuple(
                    int((tile_top + row, tile_left + col) in gray)
                    for col in range(3)
                )
                for row in range(3)
            )
            masks.append(mask)
            covered.update(
                (tile_top + row, tile_left + col)
                for row in range(3)
                for col in range(3)
                if mask[row][col]
            )
    mask = masks[0]
    mask_count = sum(value for row in mask for value in row)
    if (
        len(set(masks)) != 1
        or covered != gray
        or mask[0] != (1, 1, 1)
        or any(not any(row) for row in mask)
        or not 5 <= mask_count <= 9
        or not _mask_connected(mask)
    ):
        return None

    tile_bottom = row_starts[-1] + 2
    tile_right = col_starts[-1] + 2
    separated = (
        key_bottom < row_starts[0] - 1
        or tile_bottom < key_top - 1
        or key_right < col_starts[0] - 1
        or tile_right < key_left - 1
    )
    if not separated:
        return None

    signature = (_normalize_labels(key), mask)
    profile = _EXACT_SIGNATURES.get(signature, "generalized")
    return {
        "scene_profile": profile,
        "key": key,
        "key_bbox": (key_top, key_bottom, key_left, key_right),
        "key_dims": (key_rows, key_cols),
        "key_color_count": len(key_colors),
        "tile_mask": mask,
        "tile_cell_count": mask_count,
        "tile_row_starts": row_starts,
        "tile_col_starts": col_starts,
        "gray_count": len(gray),
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
    if analysis is None:
        return None
    profile = analysis["scene_profile"]
    if profile == "generalized":
        return None
    return SCENE_PROFILES.index(profile)


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
            "expected a 23x23 black scene with one separate filled repeated-"
            "color 3..5 by 3..5 key and a same-sized four-pitch lattice of "
            "identical connected gray 3x3 shapes"
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


def _general_dimensions(difficulty):
    if difficulty == "easy":
        return ((3, 3), (3, 4), (4, 3))
    if difficulty == "hard":
        return ((3, 5), (4, 4), (4, 5), (5, 3), (5, 4))
    return (
        (3, 3),
        (3, 4),
        (3, 5),
        (4, 3),
        (4, 4),
        (4, 5),
        (5, 3),
        (5, 4),
    )


def _general_color_range(difficulty):
    if difficulty == "easy":
        return 2, 3
    if difficulty == "hard":
        return 4, 5
    return 3, 5


def _general_mask_options(difficulty):
    if difficulty == "easy":
        low, high = 5, 6
    elif difficulty == "hard":
        low, high = 7, 9
    else:
        low, high = 5, 9
    return tuple(
        mask
        for mask in _GENERAL_MASKS
        if low <= sum(value for row in mask for value in row) <= high
    )


def _choose_general_key_and_mask(difficulty, rng):
    dimensions = _general_dimensions(difficulty)
    color_low, color_high = _general_color_range(difficulty)
    masks = _general_mask_options(difficulty)
    for _ in range(128):
        key_rows, key_cols = rng.choice(dimensions)
        color_count = rng.randint(
            color_low,
            min(color_high, key_rows * key_cols - 1),
        )
        labels = list(range(color_count))
        labels.extend(
            rng.randrange(color_count)
            for _ in range(key_rows * key_cols - color_count)
        )
        rng.shuffle(labels)
        key_labels = tuple(
            tuple(labels[row * key_cols : (row + 1) * key_cols])
            for row in range(key_rows)
        )
        key_labels = _normalize_labels(key_labels)
        mask = rng.choice(masks)
        if (key_labels, mask) not in _EXACT_SIGNATURES:
            return key_labels, mask
    raise RuntimeError("could not construct a non-public generalized profile")


def _colors_for_labels(profile, key_labels, rng):
    color_count = 1 + max(value for row in key_labels for value in row)
    if profile in _PUBLIC_SPECS and rng.randrange(4) == 0:
        public_colors = []
        for row in _PUBLIC_SPECS[profile]["key"]:
            for value in row:
                if value not in public_colors:
                    public_colors.append(value)
        colors = public_colors[:]
        rng.shuffle(colors)
    else:
        colors = list(_LEGAL_KEY_COLORS)
        rng.shuffle(colors)
        colors = colors[:color_count]
    if len(colors) != color_count:
        raise RuntimeError("insufficient key colors")
    return tuple(
        tuple(colors[label] for label in row)
        for row in key_labels
    )


def _layout_side_options(key_rows, key_cols):
    tile_height = 4 * key_rows - 1
    tile_width = 4 * key_cols - 1
    sides = []
    if key_cols + 2 <= _CANVAS - tile_width:
        sides.extend(("key_left", "key_right"))
    if key_rows + 2 <= _CANVAS - tile_height:
        sides.extend(("key_top", "key_bottom"))
    return tuple(sides)


def _choose_layout(key_rows, key_cols, rng):
    tile_height = 4 * key_rows - 1
    tile_width = 4 * key_cols - 1
    sides = _layout_side_options(key_rows, key_cols)
    if not sides:
        raise RuntimeError(
            f"no 23x23 separated layout for key {key_rows}x{key_cols}"
        )
    side = rng.choice(sides)
    if side == "key_left":
        tile_left = rng.randint(key_cols + 2, _CANVAS - tile_width)
        tile_top = rng.randint(0, _CANVAS - tile_height)
        key_left = rng.randint(0, tile_left - key_cols - 1)
        key_top = rng.randint(0, _CANVAS - key_rows)
    elif side == "key_right":
        tile_left = rng.randint(
            0,
            _CANVAS - tile_width - key_cols - 2,
        )
        tile_top = rng.randint(0, _CANVAS - tile_height)
        key_left = rng.randint(
            tile_left + tile_width + 1,
            _CANVAS - key_cols,
        )
        key_top = rng.randint(0, _CANVAS - key_rows)
    elif side == "key_top":
        tile_top = rng.randint(key_rows + 2, _CANVAS - tile_height)
        tile_left = rng.randint(0, _CANVAS - tile_width)
        key_top = rng.randint(0, tile_top - key_rows - 1)
        key_left = rng.randint(0, _CANVAS - key_cols)
    else:
        tile_top = rng.randint(
            0,
            _CANVAS - tile_height - key_rows - 2,
        )
        tile_left = rng.randint(0, _CANVAS - tile_width)
        key_top = rng.randint(
            tile_top + tile_height + 1,
            _CANVAS - key_rows,
        )
        key_left = rng.randint(0, _CANVAS - key_cols)
    return {
        "side": side,
        "key_top": key_top,
        "key_left": key_left,
        "tile_top": tile_top,
        "tile_left": tile_left,
    }


def _construct_scene(profile, difficulty, context):
    rng = context.draw_rng("scene")
    if profile == "generalized":
        key_labels, mask = _choose_general_key_and_mask(difficulty, rng)
    else:
        key_labels, mask = rng.choice(_PROFILE_VARIANTS[profile])
    key = _colors_for_labels(profile, key_labels, rng)
    key_rows = len(key)
    key_cols = len(key[0])
    layout = _choose_layout(key_rows, key_cols, rng)
    grid = [[0 for _ in range(_CANVAS)] for _ in range(_CANVAS)]
    for row in range(key_rows):
        for col in range(key_cols):
            grid[layout["key_top"] + row][layout["key_left"] + col] = (
                key[row][col]
            )
    for tile_row in range(key_rows):
        for tile_col in range(key_cols):
            top = layout["tile_top"] + 4 * tile_row
            left = layout["tile_left"] + 4 * tile_col
            for row in range(3):
                for col in range(3):
                    if mask[row][col]:
                        grid[top + row][left + col] = 5
    return grid


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(
            "unknown override(s): " + ", ".join(sorted(unknown))
        )
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
    grid = _construct_scene(profile, difficulty, context)
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


def _broad_rule_parameters(grid):
    original, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    height = len(original)
    width = len(original[0])
    key_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if original[row][col] not in (0, 5)
    ]
    gray = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if original[row][col] == 5
    ]
    if not key_cells or not gray:
        raise ValueError("canonical rule requires both key and gray cells")
    key_top = min(row for row, _col in key_cells)
    key_left = min(col for _row, col in key_cells)
    gray_top = min(row for row, _col in gray)
    gray_left = min(col for _row, col in gray)
    top_col_runs = _runs(
        col for row, col in gray if row == gray_top
    )
    row_runs = _runs(row for row, _col in gray)
    if len(top_col_runs) < 2 or len(row_runs) < 2:
        raise ValueError("canonical rule requires at least two tile rows/cols")
    row_period = row_runs[1][0] - row_runs[0][0]
    col_period = top_col_runs[1][0] - top_col_runs[0][0]
    if row_period <= 0 or col_period <= 0:
        raise ValueError("tile periods must be positive")
    return (
        original,
        key_top,
        key_left,
        gray_top,
        gray_left,
        row_period,
        col_period,
    )


def rule_mirror(grid):
    """Input-pure Python mirror of the complete canonical Racket rule."""
    (
        original,
        key_top,
        key_left,
        gray_top,
        gray_left,
        row_period,
        col_period,
    ) = _broad_rule_parameters(grid)
    height = len(original)
    width = len(original[0])
    output = [row[:] for row in original]
    for row in range(height):
        for col in range(width):
            if original[row][col] != 5:
                continue
            tile_row = (row - gray_top) // row_period
            tile_col = (col - gray_left) // col_period
            source_row = key_top + tile_row
            source_col = key_left + tile_col
            if not 0 <= source_row < height or not 0 <= source_col < width:
                raise ValueError("gray tile index falls outside the key")
            output[row][col] = original[source_row][source_col]
    return output


_mirror = rule_mirror
