"""Semantic generator for ARC task 1b7cbdffd485.

Read the nonzero colors in row-major first-appearance order.  Compare the row
and column spans of those first appearances: a row-span greater than or equal
to the column-span produces a column vector; otherwise produce a row vector.

The published inputs are complete partitions into connected, irregular color
bands.  Four linked public profiles preserve those complete input geometries
under color permutation and D4 symmetry.  General profiles broaden band
counts and explicitly exercise the equality and one-cell decision margins.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "1b7cbdffd485"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "db42b0b2c380"
SUMMARY = (
    "Order colors by row-major first appearance; emit a column when the "
    "first-cell row span is at least the column span, otherwise emit a row."
)

INVARIANTS = [
    "the canvas is fully partitioned among two through six nonzero colors",
    "every color is one 4-connected region",
    "output colors follow row-major first-appearance order",
    "row_span >= col_span chooses a column, including exact equality",
]

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_train_3",
    "public_test_1",
)
GENERAL_PROFILES = (
    "horizontal_three",
    "horizontal_four",
    "horizontal_many",
    "vertical_three",
    "vertical_four",
    "vertical_many",
    "tie_column",
    "row_margin_column",
    "col_margin_row",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted rng; four linked public profiles in thirteen",
        "valid": "|".join(SCENE_PROFILES),
    }
}


_PUBLIC_ROWS = {
    "public_train_1": (
        "2222222",
        "2222222",
        "2222222",
        "2888228",
        "8888888",
        "8888888",
        "8885588",
        "5855555",
        "5555555",
    ),
    "public_train_2": (
        "4444444222222288",
        "4444444422228888",
        "4444444422228888",
        "4444444222228888",
        "4444442222222888",
        "4444442222228888",
        "4444444222228888",
        "4444444222222888",
        "4444422222222288",
        "4444422222222288",
        "4444222222222888",
        "4444222222228888",
        "4444422222228888",
        "4444442222222888",
    ),
    "public_train_3": (
        "666666666",
        "664466666",
        "644464644",
        "444444444",
        "444444444",
        "444444444",
        "422444224",
        "222222222",
        "232222233",
        "333333333",
        "333333333",
    ),
    "public_test_1": (
        "33332222211188",
        "33322222111888",
        "33333221118888",
        "33333221111888",
        "33332222211188",
        "33333222211118",
        "33322222111188",
        "33332222111888",
        "33332222111188",
        "33322222211188",
        "33322222211888",
        "33332222111188",
        "33333222111188",
        "33333322211188",
    ),
}


def _public_literal(profile):
    """Return a fresh published input grid; outputs are never stored here."""
    return [[int(cell) for cell in row] for row in _PUBLIC_ROWS[profile]]


def _rot90(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _transform(grid, transform):
    out = [row[:] for row in grid]
    if transform >= 4:
        out = [row[::-1] for row in out]
    for _ in range(transform % 4):
        out = _rot90(out)
    return out


_TRANSFORMS = tuple(range(8))


def _encounter_signature(grid):
    mapping = {}
    next_label = 1
    normalized = []
    for row in grid:
        normalized_row = []
        for value in row:
            if value == 0:
                normalized_row.append(0)
                continue
            if value not in mapping:
                mapping[value] = next_label
                next_label += 1
            normalized_row.append(mapping[value])
        normalized.append(tuple(normalized_row))
    return len(grid), len(grid[0]), tuple(normalized)


_PUBLIC_SIGNATURES = {}
for _profile in PUBLIC_PROFILES:
    for _transform_id in _TRANSFORMS:
        _signature = _encounter_signature(
            _transform(_public_literal(_profile), _transform_id)
        )
        previous = _PUBLIC_SIGNATURES.setdefault(_signature, _profile)
        if previous != _profile:
            raise RuntimeError("public profile signatures collide")


def canonical_profile_signature(grid):
    """Identify a complete linked public geometry modulo color and D4."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return None
    try:
        return _PUBLIC_SIGNATURES.get(_encounter_signature(grid))
    except (TypeError, ValueError):
        return None


def _component_is_connected(grid, color):
    cells = {
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == color
    }
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        row, col = queue.popleft()
        for neighbor in (
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        ):
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen == cells


def _analysis(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["empty grid"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["empty grid"]}
    height = len(grid)
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["ragged grid"]}
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("cells must be integer ARC colors 0..9")
                break
        if errors:
            break

    order = []
    first_cells = []
    if not errors:
        for row in range(height):
            for col in range(width):
                value = grid[row][col]
                if value != 0 and value not in order:
                    order.append(value)
                    first_cells.append((value, row, col))
    if any(0 in row for row in grid):
        errors.append("published morphology fully partitions the canvas; zero is forbidden")
    if not 2 <= len(order) <= 6:
        errors.append(f"expected 2..6 nonzero colors, got {len(order)}")

    color_extents = {}
    if not errors:
        for color in order:
            cells = [
                (row, col)
                for row in range(height)
                for col in range(width)
                if grid[row][col] == color
            ]
            rows = [cell[0] for cell in cells]
            cols = [cell[1] for cell in cells]
            color_extents[color] = (
                min(rows), max(rows), min(cols), max(cols), len(cells)
            )
            if len(cells) < 4:
                errors.append(f"color {color} has only {len(cells)} cells")
            if not _component_is_connected(grid, color):
                errors.append(f"color {color} is not one 4-connected region")

    row_span = 0
    col_span = 0
    output_orientation = None
    if first_cells:
        first_rows = [item[1] for item in first_cells]
        first_cols = [item[2] for item in first_cells]
        row_span = max(first_rows) - min(first_rows)
        col_span = max(first_cols) - min(first_cols)
        output_orientation = "column" if row_span >= col_span else "row"

    profile = canonical_profile_signature(grid) if not errors else None
    if not errors and profile is None:
        if len(order) == 2:
            if row_span == col_span:
                profile = "tie_column"
            elif row_span == col_span + 1:
                profile = "row_margin_column"
            elif col_span == row_span + 1:
                profile = "col_margin_row"
            else:
                errors.append("two-color first-cell spans miss the declared boundary profiles")
        else:
            spans_width = all(
                extent[2] == 0 and extent[3] == width - 1
                for extent in color_extents.values()
            )
            spans_height = all(
                extent[0] == 0 and extent[1] == height - 1
                for extent in color_extents.values()
            )
            suffix = {3: "three", 4: "four"}.get(len(order), "many")
            if spans_width and not spans_height and output_orientation == "column":
                profile = f"horizontal_{suffix}"
            elif spans_height and not spans_width and output_orientation == "row":
                profile = f"vertical_{suffix}"
            else:
                errors.append("grid is not an observable fuzzy horizontal/vertical profile")

    if profile not in SCENE_PROFILES and not errors:
        errors.append("unrecognized scene profile")
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "order": order,
        "first_cells": first_cells,
        "row_span": row_span,
        "col_span": col_span,
        "output_orientation": output_orientation,
        "color_extents": color_extents,
        "scene_profile": profile,
    }


def observe_overrides(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {"scene_profile": info["scene_profile"]}


def rule_mirror(grid):
    """Independent Python transcription of the canonical Racket rule."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("rule requires a nonempty rectangular grid")
    order = []
    first_cells = []
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            value = grid[row][col]
            if value > 0 and value not in order:
                order.append(value)
                first_cells.append((row, col))
    if not order:
        raise ValueError("rule requires at least one nonzero color")
    row_span = max(row for row, _ in first_cells) - min(row for row, _ in first_cells)
    col_span = max(col for _, col in first_cells) - min(col for _, col in first_cells)
    if row_span >= col_span:
        return [[color] for color in order]
    return [order[:]]


def _palette(rng, count):
    colors = list(range(1, 10))
    rng.shuffle(colors)
    return colors[:count]


def _recolor(grid, rng):
    source_colors = []
    for row in grid:
        for value in row:
            if value and value not in source_colors:
                source_colors.append(value)
    target_colors = _palette(rng, len(source_colors))
    mapping = dict(zip(source_colors, target_colors))
    return [[mapping.get(value, value) for value in row] for row in grid]


def _difficulty_dimensions(rng, difficulty, count):
    if difficulty == "easy":
        height = rng.randint(max(7, 2 * count + 1), max(10, 2 * count + 4))
        width = rng.randint(6, 9)
    elif difficulty == "hard":
        height = rng.randint(max(18, 2 * count + 5), max(24, 2 * count + 11))
        width = rng.randint(11, 17)
    else:
        height = rng.randint(max(11, 2 * count + 3), max(16, 2 * count + 8))
        width = rng.randint(8, 13)
    if height <= width + 2:
        height = width + 3
    return height, width


def _composition(rng, total, count, minimum):
    parts = [minimum] * count
    for _ in range(total - minimum * count):
        parts[rng.randrange(count)] += 1
    return parts


def _horizontal_partition(rng, height, width, colors):
    """Build connected fuzzy bands, each spanning the complete canvas width."""
    count = len(colors)
    thicknesses = _composition(rng, height, count, 2)
    base_boundaries = []
    cursor = 0
    for thickness in thicknesses[:-1]:
        cursor += thickness
        base_boundaries.append(cursor)

    boundaries_by_col = []
    previous = base_boundaries[:]
    for col in range(width):
        current = []
        for index, base in enumerate(base_boundaries):
            if col == 0:
                proposal = base
            else:
                proposal = previous[index] + rng.choice((-1, 0, 0, 1))
            lower = 2 if index == 0 else current[index - 1] + 2
            upper = height - 2 * (count - index - 1)
            proposal = max(lower, min(upper, proposal))
            current.append(proposal)
        boundaries_by_col.append(current)
        previous = current

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for col, boundaries in enumerate(boundaries_by_col):
        for row in range(height):
            band = sum(row >= boundary for boundary in boundaries)
            grid[row][col] = colors[band]
    return grid


def _fuzzy_profile(rng, difficulty, profile):
    orientation, suffix = profile.split("_", 1)
    count = {"three": 3, "four": 4}.get(suffix, rng.choice((5, 6)))
    for _ in range(100):
        height, width = _difficulty_dimensions(rng, difficulty, count)
        grid = _horizontal_partition(rng, height, width, _palette(rng, count))
        if orientation == "vertical":
            grid = [list(row) for row in zip(*grid)]
        info = _analysis(grid)
        if not info["errors"] and info["scene_profile"] == profile:
            return grid
    raise RuntimeError(f"failed to synthesize {profile}")


def _boundary_profile(rng, difficulty, profile):
    if difficulty == "easy":
        size = rng.randint(7, 10)
    elif difficulty == "hard":
        size = rng.randint(17, 24)
    else:
        size = rng.randint(11, 16)
    first, second = _palette(rng, 2)
    pivot = rng.randint(2, size - 4)
    if profile == "tie_column":
        start_row, start_col = pivot, pivot
    elif profile == "row_margin_column":
        start_row, start_col = pivot + 1, pivot
    else:
        start_row, start_col = pivot, pivot + 1
    grid = [[first for _ in range(size)] for _ in range(size)]
    for row in range(start_row, size):
        for col in range(start_col, size):
            grid[row][col] = second
    return grid


def _generate_public(rng, profile):
    grid = _recolor(_public_literal(profile), rng)
    return _transform(grid, rng.choice(_TRANSFORMS))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")

    context = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    # One copy of each profile gives the linked public curriculum a 4/13 prior.
    profile = context.draw_choice("scene_profile", list(SCENE_PROFILES))
    rng = context.draw_rng("scene")
    if profile in PUBLIC_PROFILES:
        grid = _generate_public(rng, profile)
    elif profile.startswith(("horizontal_", "vertical_")):
        grid = _fuzzy_profile(rng, difficulty, profile)
    else:
        grid = _boundary_profile(rng, difficulty, profile)

    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise RuntimeError(f"profile construction mismatch: {profile} -> {observed}")
    return [row[:] for row in grid]


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed grids and nearest semantic/profile impostors."""
    info = _analysis(grid)
    errors = list(info["errors"])
    overrides = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if overrides:
        unknown = set(overrides) - {"scene_profile"}
        if unknown:
            errors.append(f"unknown override(s): {sorted(unknown)}")
        requested = overrides.get("scene_profile")
        if requested not in SCENE_PROFILES:
            errors.append(f"unknown scene_profile: {requested!r}")
        elif not errors and info["scene_profile"] != requested:
            errors.append(
                f"requested scene_profile {requested}, observed {info['scene_profile']}"
            )
    if not errors:
        output = rule_mirror(grid)
        expected_shape = (
            (len(info["order"]), 1)
            if info["row_span"] >= info["col_span"]
            else (1, len(info["order"]))
        )
        if (len(output), len(output[0])) != expected_shape:
            errors.append("rule mirror emitted the wrong orientation")
        flattened = [value for row in output for value in row]
        if flattened != info["order"]:
            errors.append("rule mirror emitted the wrong color order")
    return errors
