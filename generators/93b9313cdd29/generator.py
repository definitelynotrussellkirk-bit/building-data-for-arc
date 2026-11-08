"""Semantic generator for ARC task 93b9313cdd29.

The first row is a left-to-right transform program.  Only colors 1..4 are
instructions; zeros and colors 5..9 in that row are inert spacing/decoys.
The nonzero body below the blank separator row is cropped tightly, then every
instruction is applied in order:

    1 -> rotate 90 degrees clockwise
    2 -> rotate 180 degrees
    3 -> flip left/right
    4 -> transpose

The public family reproduces every complete canonical input profile while
varying only nuisance placement, canvas, and body-color names.  The
generalized family varies scripts, spacing, decoys, shape topology, and color
layout without changing the rule.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "93b9313cdd29"
VERSION = "4.0.0"
TASK_ID = "93b9313cdd29"
RULE_HASH = "9ad483dbe321"
SUMMARY = (
    "Read transform tokens 1..4 from the top row, crop the nonzero body below "
    "the blank separator, and apply the transforms in left-to-right order."
)
EXAMPLES_NEEDED = 4
AXES = {
    "scene_family": {
        "type": "str",
        "default": "rng public|generalized (2:3)",
        "valid": "public|generalized",
        "doc": (
            "public preserves one complete canonical script/body profile; "
            "generalized varies script composition, header layout, topology, "
            "and body colors"
        ),
    },
}
INVARIANTS = [
    "row 0 contains one to five transform tokens from {1,2,3,4}",
    "row 1 is a blank separator and the body uses only colors 5..9",
    "the body is cropped to its nonzero bounding box before transformation",
    "the token sequence is applied left-to-right; generalized scenes change the body",
]

DIFFICULTIES = {None, "default", "easy", "medium", "hard"}
TOKENS = (1, 2, 3, 4)
BODY_COLORS = (5, 6, 7, 8, 9)

# Color-role-normalized crops from all three canonical train inputs and the
# canonical test input.  These are complete linked profiles, not marginal
# feature fragments.  Body role ids are remapped to fresh colors 5..9.
PUBLIC_PROFILES = (
    (
        "public_train_1",
        (1, 3),
        (
            (1, 0, 0),
            (1, 1, 1),
        ),
    ),
    (
        "public_train_2",
        (4, 2, 1),
        (
            (1, 1, 0, 0),
            (0, 1, 0, 2),
            (0, 1, 0, 2),
        ),
    ),
    (
        "public_train_3",
        (3, 3, 2),
        (
            (1, 1, 0),
            (0, 1, 0),
            (0, 1, 1),
        ),
    ),
    (
        "public_test_1",
        (1, 4, 3),
        (
            (1, 0),
            (1, 1),
            (0, 1),
        ),
    ),
)

SCRIPT_POOLS = {
    "easy": (
        (1,),
        (2,),
        (3,),
        (4,),
    ),
    "medium": (
        (1, 1),
        (1, 2),
        (2, 1),
        (1, 3),
        (3, 1),
        (1, 4),
        (4, 1),
        (2, 3),
        (3, 2),
        (2, 4),
        (4, 2),
        (3, 4),
        (4, 3),
    ),
    "hard": (
        (4, 2, 1),
        (3, 3, 2),
        (1, 4, 3),
        (1, 3, 4),
        (4, 1, 3),
        (3, 1, 4),
        (2, 4, 1),
        (1, 2, 3),
        (4, 3, 1),
        (1, 1, 3),
        (3, 4, 2, 1),
        (1, 4, 3, 2),
        (2, 1, 4, 3),
        (3, 3, 1, 4),
        (1, 2, 1, 3),
        (4, 2, 4, 1),
        (1, 3, 2, 4, 1),
    ),
}


def _copy_grid(grid):
    return [list(row) for row in grid]


def _crop_nonzero(grid):
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        return None
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    return [
        list(values[left : right + 1])
        for values in grid[top : bottom + 1]
    ]


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _apply_script(grid, tokens):
    result = _copy_grid(grid)
    for token in tokens:
        if token == 1:
            result = _rotate_cw(result)
        elif token == 2:
            result = _rotate_180(result)
        elif token == 3:
            result = _flip_lr(result)
        elif token == 4:
            result = _transpose(result)
    return result


def _canonicalize_body_colors(body):
    mapping = {}
    next_role = 1
    normalized = []
    for row in body:
        normalized_row = []
        for value in row:
            if value == 0:
                normalized_row.append(0)
                continue
            if value not in mapping:
                mapping[value] = next_role
                next_role += 1
            normalized_row.append(mapping[value])
        normalized.append(tuple(normalized_row))
    return tuple(normalized)


def _linked_profile(tokens, body):
    normalized = _canonicalize_body_colors(body)
    for name, profile_tokens, profile_body in PUBLIC_PROFILES:
        if tuple(tokens) == profile_tokens and normalized == profile_body:
            return name
    return None


def _analyze(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {
            "errors": ["grid must be a nonempty rectangular matrix"],
            "facts": None,
        }
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return {"errors": ["grid rows must be lists or tuples"], "facts": None}
    widths = {len(row) for row in grid}
    if len(widths) != 1 or 0 in widths:
        return {
            "errors": ["grid must be rectangular and nonempty"],
            "facts": None,
        }

    height = len(grid)
    width = next(iter(widths))
    if not (5 <= height <= 30 and 5 <= width <= 30):
        errors.append("grid dimensions must each be in 5..30")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cell values must be integer ARC colors 0..9")
        return {"errors": errors, "facts": None}
    if height < 3:
        errors.append("grid needs a header, separator, and body region")
        return {"errors": errors, "facts": None}

    tokens = tuple(value for value in grid[0] if value in TOKENS)
    if not (1 <= len(tokens) <= 5):
        errors.append("row 0 must encode one to five transform tokens")
    header_decoys = tuple(
        value for value in grid[0] if value != 0 and value not in TOKENS
    )
    if any(value not in BODY_COLORS for value in header_decoys):
        errors.append("header decoys may use only colors 5..9")
    if len(header_decoys) > 2:
        errors.append("row 0 may contain at most two non-token decoys")
    if any(value != 0 for value in grid[1]):
        errors.append("row 1 must be a blank separator")

    body_region = [list(row) for row in grid[1:]]
    body = _crop_nonzero(body_region)
    if body is None:
        errors.append("body contains no nonzero object")
        return {"errors": errors, "facts": None}

    body_values = [value for row in body for value in row if value != 0]
    if any(value not in BODY_COLORS for value in body_values):
        errors.append("body must reserve colors 1..4 for script tokens")
    body_height = len(body)
    body_width = len(body[0])
    occupied = len(body_values)
    if not (2 <= body_height <= 10 and 2 <= body_width <= 10):
        errors.append("cropped body must be 2..10 by 2..10")
    if not (4 <= occupied <= 24):
        errors.append("body must contain 4..24 nonzero cells")
    if occupied == body_height * body_width:
        errors.append("body must contain internal background, not a solid rectangle")

    linked_profile = _linked_profile(tokens, body)
    output = _apply_script(body, tokens) if tokens else None
    if output == body and linked_profile is None:
        errors.append("transform script must visibly change the cropped body")

    facts = {
        "height": height,
        "width": width,
        "tokens": tokens,
        "header_decoys": header_decoys,
        "body": body,
        "body_height": body_height,
        "body_width": body_width,
        "occupied": occupied,
        "body_colors": tuple(sorted(set(body_values))),
        "output": output,
        "linked_profile": linked_profile,
        "scene_family": "public" if linked_profile else "generalized",
    }
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analyze(grid)["errors"])


def rule_mirror(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _copy_grid(analysis["facts"]["output"])


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    return analysis["facts"]["linked_profile"]


def is_canonical_profile(grid):
    return canonical_profile_signature(grid) is not None


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {"scene_family": analysis["facts"]["scene_family"]}


def _normalize_cells(cells):
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _grow_polyomino(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        row, col = rng.choice(tuple(cells))
        delta_row, delta_col = rng.choice(
            ((-1, 0), (1, 0), (0, -1), (0, 1))
        )
        cells.add((row + delta_row, col + delta_col))
    return _normalize_cells(cells)


def _cell_dims(cells):
    return (
        max(row for row, _ in cells) + 1,
        max(col for _, col in cells) + 1,
    )


def _disconnected_cells(rng, total_size):
    first_size = rng.randint(3, total_size - 3)
    second_size = total_size - first_size
    first = _grow_polyomino(rng, first_size)
    second = _grow_polyomino(rng, second_size)
    first_height, first_width = _cell_dims(first)
    second_height, second_width = _cell_dims(second)
    if rng.random() < 0.5:
        row_offset = rng.randint(0, max(first_height, second_height) - 1)
        col_offset = first_width + rng.randint(1, 2)
    else:
        row_offset = first_height + rng.randint(1, 2)
        col_offset = rng.randint(0, max(first_width, second_width) - 1)
    moved = {
        (row + row_offset, col + col_offset) for row, col in second
    }
    return _normalize_cells(set(first) | moved)


def _color_body(cells, rng, color_count):
    palette = rng.sample(BODY_COLORS, color_count)
    height, width = _cell_dims(cells)
    body = full_grid(height, width, 0)
    ordered = list(cells)
    rng.shuffle(ordered)
    for index, (row, col) in enumerate(ordered):
        if index < color_count:
            color = palette[index]
        else:
            # Structured variation avoids a color-per-cell confound while
            # still making whole-grid transforms observable.
            color = palette[(row + 2 * col + rng.randrange(color_count)) % color_count]
        body[row][col] = color
    return body


def _body_for_band(rng, band):
    size_ranges = {
        "easy": (4, 7),
        "medium": (6, 13),
        "hard": (9, 20),
    }
    color_ranges = {
        "easy": (1, 2),
        "medium": (1, 3),
        "hard": (2, 5),
    }
    low, high = size_ranges[band]
    for _ in range(300):
        size = rng.randint(low, high)
        disconnected = (
            band == "hard" and size >= 9 and rng.random() < 0.35
        )
        cells = (
            _disconnected_cells(rng, size)
            if disconnected
            else _grow_polyomino(rng, size)
        )
        height, width = _cell_dims(cells)
        if not (2 <= height <= 8 and 2 <= width <= 8):
            continue
        if len(cells) == height * width:
            continue
        color_low, color_high = color_ranges[band]
        color_count = rng.randint(color_low, min(color_high, len(cells)))
        body = _color_body(cells, rng, color_count)
        return body
    raise RuntimeError("could not construct a non-solid generalized body")


def _canvas_shape(rng, band, body, header_items):
    body_height = len(body)
    body_width = len(body[0])
    ranges = {
        "easy": ((5, 7), (5, 9)),
        "medium": ((6, 9), (6, 11)),
        "hard": ((9, 12), (9, 14)),
    }
    (min_height, max_height), (min_width, max_width) = ranges[band]
    min_height = max(min_height, body_height + 2)
    min_width = max(min_width, body_width, header_items)
    max_height = max(max_height, min_height)
    max_width = max(max_width, min_width)
    return (
        rng.randint(min_height, max_height),
        rng.randint(min_width, max_width),
    )


def _paint_scene(body, tokens, rng, band, *, public):
    decoy_count = 0
    if not public:
        probabilities = {
            "easy": (0, 0, 0, 1),
            "medium": (0, 0, 1, 1, 2),
            "hard": (0, 1, 1, 2, 2),
        }
        decoy_count = rng.choice(probabilities[band])
    header_items = len(tokens) + decoy_count
    height, width = _canvas_shape(rng, band, body, header_items)
    grid = full_grid(height, width, 0)

    if public or band == "easy":
        start = rng.randint(0, width - len(tokens))
        token_positions = list(range(start, start + len(tokens)))
    else:
        token_positions = sorted(rng.sample(range(width), len(tokens)))
    for position, token in zip(token_positions, tokens):
        grid[0][position] = token

    free_positions = [
        col for col in range(width) if grid[0][col] == 0
    ]
    for position, color in zip(
        rng.sample(free_positions, decoy_count),
        rng.sample(BODY_COLORS, decoy_count),
    ):
        grid[0][position] = color

    body_height = len(body)
    body_width = len(body[0])
    top = rng.randint(2, height - body_height)
    left = rng.randint(0, width - body_width)
    for row, values in enumerate(body):
        for col, value in enumerate(values):
            grid[top + row][left + col] = value
    return grid


def _build_public(rng, band):
    name, tokens, role_body = rng.choice(PUBLIC_PROFILES)
    role_count = max(value for row in role_body for value in row)
    palette = rng.sample(BODY_COLORS, role_count)
    body = [
        [0 if value == 0 else palette[value - 1] for value in row]
        for row in role_body
    ]
    grid = _paint_scene(body, tokens, rng, band, public=True)
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["facts"]["linked_profile"] != name:
        raise RuntimeError("public profile construction drift")
    return grid


def _build_generalized(rng, band):
    for _ in range(400):
        tokens = rng.choice(SCRIPT_POOLS[band])
        body = _body_for_band(rng, band)
        if _apply_script(body, tokens) == body:
            continue
        if _linked_profile(tokens, body) is not None:
            continue
        grid = _paint_scene(body, tokens, rng, band, public=False)
        analysis = _analyze(grid)
        if (
            not analysis["errors"]
            and analysis["facts"]["scene_family"] == "generalized"
        ):
            return grid
    raise RuntimeError("could not realize a generalized transform-script scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    family = ctx.draw_choice(
        "scene_family",
        (
            "public",
            "public",
            "public",
            "public",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
        ),
    )
    band = "medium" if difficulty in (None, "default") else difficulty
    rng = ctx.draw_rng("scene")
    grid = (
        _build_public(rng, band)
        if family == "public"
        else _build_generalized(rng, band)
    )
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["facts"]["scene_family"] != family:
        detail = analysis["errors"] or [
            "wanted " + family + ", observed " + analysis["facts"]["scene_family"]
        ]
        raise RuntimeError("internal construction error: " + "; ".join(detail))
    return grid
