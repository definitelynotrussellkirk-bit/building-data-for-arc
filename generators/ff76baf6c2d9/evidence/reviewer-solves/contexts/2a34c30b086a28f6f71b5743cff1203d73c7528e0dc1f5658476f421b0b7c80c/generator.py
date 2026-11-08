"""Generator for singleton-requested multicolor template copies.

Each multicolor source has one color that occurs exactly once and a second
color that repeats.  Isolated cells matching the singleton source color
request copies of that source.  Color 2 requests a horizontally mirrored
copy; every other request color preserves the source orientation.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "ff76baf6c2d9"
VERSION = "3.0.0"
TASK_ID = "ff76baf6c2d9"
RULE_HASH = "d31dc299f026"

SUMMARY = (
    "Place one or two multicolor templates, each with one uniquely occurring "
    "anchor color and a repeated carrier color. Isolated cells matching each "
    "anchor request complete copies of that template; anchor color 2 mirrors "
    "the copy horizontally, while all other anchor colors preserve it."
)

INVARIANTS = [
    "zero is the modal background on a square grid",
    "there are one or two separated 8-connected multicolor source templates",
    "each source has one unique anchor-colored cell and a repeated carrier",
    "every source has at least one isolated marker matching its anchor color",
    "each marker color identifies exactly one source template",
    "all requested copy footprints are in bounds, blank, and mutually disjoint",
    "color-2 markers mirror column offsets and other markers preserve offsets",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_size": {
        "type": "int",
        "default": "difficulty-aware 13..24 square canvas",
        "valid": "13..24",
    },
    "n_sources": {
        "type": "int",
        "default": "difficulty-aware one or two templates",
        "valid": "1..2",
    },
    "n_targets": {
        "type": "int",
        "default": "one through four total requested copies",
        "valid": "1..4",
    },
}

_KING_DELTAS = (
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
)
_PROFILE_PRIOR = 0.28
_NON_SPECIAL_COLORS = (1, 3, 4, 5, 6, 7, 8, 9)

# Sparse forms of every published input, including the held-out input.  The
# profile path applies only symmetries that preserve the distinguished
# horizontal-mirror semantics of color 2, plus translation and a bijective
# relabeling of all non-special colors.
_PROFILE_INPUT_CELLS = (
    (
        (1, 10, 2),
        (2, 2, 3),
        (2, 3, 8),
        (2, 4, 8),
        (3, 2, 8),
        (7, 6, 4),
        (7, 7, 2),
        (8, 1, 3),
        (8, 7, 4),
        (8, 8, 4),
    ),
    (
        (1, 6, 4),
        (2, 5, 4),
        (2, 6, 3),
        (2, 7, 4),
        (3, 5, 4),
        (3, 6, 4),
        (6, 2, 3),
        (9, 9, 3),
    ),
    (
        (1, 7, 4),
        (1, 8, 4),
        (1, 9, 4),
        (2, 3, 2),
        (2, 8, 2),
        (2, 9, 4),
        (3, 9, 4),
        (7, 10, 1),
        (7, 11, 1),
        (8, 9, 1),
        (8, 10, 3),
        (8, 11, 1),
        (9, 4, 3),
        (11, 8, 2),
    ),
    (
        (3, 3, 2),
        (3, 4, 1),
        (4, 3, 1),
        (4, 4, 1),
        (5, 5, 1),
        (8, 7, 2),
    ),
    (
        (1, 2, 1),
        (1, 5, 3),
        (1, 9, 2),
        (2, 1, 1),
        (2, 2, 2),
        (3, 1, 1),
        (3, 2, 1),
        (5, 8, 8),
        (5, 9, 8),
        (5, 10, 8),
        (6, 9, 3),
        (6, 10, 8),
        (7, 9, 8),
        (9, 3, 2),
        (10, 7, 3),
    ),
)

# Three-by-three source forms.  ``A`` is the unique anchor and ``C`` is the
# repeated carrier.  These include every demonstrated source morphology plus
# nearby lawful extrapolations.
_SOURCE_FORMS = (
    (
        ("A", "C", "C"),
        ("C", ".", "."),
        (".", ".", "."),
    ),
    (
        ("C", "A", "."),
        (".", "C", "C"),
        (".", ".", "."),
    ),
    (
        (".", "C", "."),
        ("C", "A", "C"),
        ("C", "C", "."),
    ),
    (
        ("A", "C", "."),
        ("C", "C", "."),
        (".", ".", "C"),
    ),
    (
        (".", "C", "C"),
        ("C", "A", "C"),
        (".", ".", "."),
    ),
    (
        ("C", "C", "C"),
        (".", "A", "C"),
        (".", "C", "."),
    ),
    (
        ("C", ".", "C"),
        ("C", "A", "."),
        (".", "C", "C"),
    ),
    (
        (".", "C", "."),
        ("C", "A", "C"),
        (".", "C", "C"),
    ),
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label, lower, upper in (
        ("grid_size", 13, 24),
        ("n_sources", 1, 2),
        ("n_targets", 1, 4),
    ):
        value = overrides.get(label)
        if value is not None and (
            type(value) is not int or not lower <= value <= upper
        ):
            raise ValueError(
                f"{label} must be an integer in [{lower}, {upper}]"
            )
    if (
        overrides.get("n_sources") is not None
        and overrides.get("n_targets") is not None
        and overrides["n_targets"] < overrides["n_sources"]
    ):
        raise ValueError(
            "n_targets must be at least n_sources so every source is requested"
        )


def _coerce_grid(grid):
    return [
        [
            int(value)
            if isinstance(value, str) and value.isdigit()
            else value
            for value in row
        ]
        for row in grid
    ]


def _is_rectangular_grid(grid):
    return (
        isinstance(grid, (list, tuple))
        and bool(grid)
        and all(
            isinstance(row, (list, tuple, str)) and bool(row)
            for row in grid
        )
        and len({len(row) for row in grid}) == 1
    )


def _components8(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            component = []
            while stack:
                current_row, current_col = stack.pop()
                component.append((current_row, current_col))
                for delta_row, delta_col in _KING_DELTAS:
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and grid[next_row][next_col] != 0
                        and (next_row, next_col) not in seen
                    ):
                        seen.add((next_row, next_col))
                        stack.append((next_row, next_col))
            components.append(tuple(sorted(component)))
    return tuple(components)


def _source_instruction(grid, source, singles):
    counts = Counter(grid[row][col] for row, col in source)
    errors = []
    if not 4 <= len(source) <= 7:
        errors.append("every source must contain four through seven cells")
    if len(counts) != 2:
        errors.append("every source must contain exactly two colors")
    unique_colors = [
        color for color, count in counts.items() if count == 1
    ]
    if len(unique_colors) != 1:
        errors.append(
            "every source must have exactly one uniquely occurring color"
        )
        return None, errors
    anchor_color = unique_colors[0]
    if sorted(counts.values()) != [1, len(source) - 1]:
        errors.append(
            "the non-anchor source color must occupy every remaining cell"
        )
    anchor = next(
        (row, col)
        for row, col in source
        if grid[row][col] == anchor_color
    )
    targets = tuple(
        single
        for single in singles
        if grid[single[0]][single[1]] == anchor_color
    )
    if not targets:
        errors.append("every source anchor color needs an isolated target")
    rows = [row for row, _col in source]
    cols = [col for _row, col in source]
    if max(rows) - min(rows) >= 3 or max(cols) - min(cols) >= 3:
        errors.append("source bounding boxes may be at most three by three")
    return {
        "cells": source,
        "anchor": anchor,
        "anchor_color": anchor_color,
        "targets": targets,
    }, errors


def _scene_analysis(grid):
    if not _is_rectangular_grid(grid):
        return None, None, ["grid must be non-empty and rectangular"]
    coerced = _coerce_grid(grid)
    height = len(coerced)
    width = len(coerced[0])
    errors = []
    if height != width or not 13 <= height <= 24:
        errors.append("grid must be square with side thirteen through twenty-four")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in coerced
        for value in row
    ):
        errors.append("cells must be integer ARC colors zero through nine")
        return coerced, None, errors

    components = _components8(coerced)
    singles = tuple(component[0] for component in components if len(component) == 1)
    sources = tuple(component for component in components if len(component) > 1)
    if not 1 <= len(sources) <= 2:
        errors.append("there must be one or two multicolor sources")
    if not 1 <= len(singles) <= 4:
        errors.append("there must be one through four isolated targets")

    instructions = []
    for source in sources:
        colors = {coerced[row][col] for row, col in source}
        if len(colors) < 2:
            errors.append("all non-singleton objects must be multicolor sources")
            continue
        instruction, source_errors = _source_instruction(
            coerced,
            source,
            singles,
        )
        errors.extend(source_errors)
        if instruction is not None:
            instructions.append(instruction)

    target_claims = Counter(
        target
        for instruction in instructions
        for target in instruction["targets"]
    )
    for target in singles:
        if target_claims[target] != 1:
            errors.append(
                "each target must identify exactly one source template"
            )

    occupied = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if coerced[row][col] != 0
    }
    projected = set()
    for instruction in instructions:
        anchor_row, anchor_col = instruction["anchor"]
        anchor_color = instruction["anchor_color"]
        for target_row, target_col in instruction["targets"]:
            for source_row, source_col in instruction["cells"]:
                delta_row = source_row - anchor_row
                delta_col = source_col - anchor_col
                if delta_row == 0 and delta_col == 0:
                    continue
                output_row = target_row + delta_row
                output_col = target_col + (
                    -delta_col if anchor_color == 2 else delta_col
                )
                if not (
                    0 <= output_row < height and 0 <= output_col < width
                ):
                    errors.append("every requested copy must fit in the grid")
                    continue
                destination = (output_row, output_col)
                if destination in occupied:
                    errors.append(
                        "requested copy cells must be blank in the input"
                    )
                if destination in projected:
                    errors.append(
                        "requested copy footprints must not overlap"
                    )
                projected.add(destination)

    counts = Counter(value for row in coerced for value in row)
    if counts[0] != max(counts.values()):
        errors.append("zero must be a modal background color")

    features = {
        "grid_size": height if height == width else None,
        "n_sources": len(sources),
        "n_targets": len(singles),
        "components": components,
        "sources": sources,
        "singles": singles,
        "instructions": tuple(instructions),
        "projected": frozenset(projected),
        "has_mirror": any(
            instruction["anchor_color"] == 2
            for instruction in instructions
        ),
        "has_preserve": any(
            instruction["anchor_color"] != 2
            for instruction in instructions
        ),
    }
    return coerced, features, errors


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    _coerced, _features, errors = _scene_analysis(grid)
    return errors


def observe_overrides(grid):
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {
        "grid_size": features["grid_size"],
        "n_sources": features["n_sources"],
        "n_targets": features["n_targets"],
    }


def _apply_rule_unchecked(grid):
    output = [row[:] for row in grid]
    components = _components8(grid)
    singles = tuple(component[0] for component in components if len(component) == 1)
    sources = tuple(component for component in components if len(component) > 1)
    for source in sources:
        colors = {
            grid[row][col] for row, col in source
        }
        for anchor_color in colors:
            anchors = tuple(
                (row, col)
                for row, col in source
                if grid[row][col] == anchor_color
            )
            if len(anchors) != 1:
                continue
            anchor_row, anchor_col = anchors[0]
            targets = tuple(
                (row, col)
                for row, col in singles
                if grid[row][col] == anchor_color
            )
            for target_row, target_col in targets:
                for source_row, source_col in source:
                    delta_row = source_row - anchor_row
                    delta_col = source_col - anchor_col
                    if delta_row == 0 and delta_col == 0:
                        continue
                    output_row = target_row + delta_row
                    output_col = target_col + (
                        -delta_col if anchor_color == 2 else delta_col
                    )
                    if (
                        0 <= output_row < len(grid)
                        and 0 <= output_col < len(grid[0])
                    ):
                        output[output_row][output_col] = grid[source_row][source_col]
    return output


def rule_mirror(grid):
    coerced, _features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("invalid template-copy lesson: " + "; ".join(errors))
    return _apply_rule_unchecked(coerced)


def _grid_from_sparse(cells):
    grid = full_grid(13, 13, 0)
    for row, col, value in cells:
        grid[row][col] = value
    return grid


def _safe_transform(grid, transform):
    if transform & 1:
        grid = list(reversed(grid))
    if transform & 2:
        grid = [list(reversed(row)) for row in grid]
    return [list(row) for row in grid]


def _translate(grid, delta_row, delta_col):
    height = len(grid)
    width = len(grid[0])
    translated = full_grid(height, width, 0)
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0:
                translated[row + delta_row][col + delta_col] = grid[row][col]
    return translated


def _normalize_whole_grid(grid):
    cells = [
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] != 0
    ]
    if not cells:
        return ()
    top = min(row for row, _col in cells)
    left = min(col for _row, col in cells)
    bottom = max(row for row, _col in cells)
    right = max(col for _row, col in cells)
    role_by_color = {}
    next_role = 1
    normalized = []
    for row in range(top, bottom + 1):
        normalized_row = []
        for col in range(left, right + 1):
            value = grid[row][col]
            if value == 0:
                normalized_row.append(("bg", 0))
            elif value == 2:
                normalized_row.append(("special", 2))
            else:
                if value not in role_by_color:
                    role_by_color[value] = next_role
                    next_role += 1
                normalized_row.append(("role", role_by_color[value]))
        normalized.append(tuple(normalized_row))
    return tuple(normalized)


_PROFILE_SIGNATURE_TO_INDEX = {}
for _profile_index, _cells in enumerate(_PROFILE_INPUT_CELLS):
    _profile_grid = _grid_from_sparse(_cells)
    for _transform in range(4):
        _signature = (
            13,
            _normalize_whole_grid(
                _safe_transform(_profile_grid, _transform)
            ),
        )
        _previous = _PROFILE_SIGNATURE_TO_INDEX.setdefault(
            _signature,
            _profile_index,
        )
        if _previous != _profile_index:
            raise AssertionError("canonical profile orbits overlap")


def canonical_profile_index(grid):
    coerced, features, errors = _scene_analysis(grid)
    if errors:
        return None
    signature = (
        features["grid_size"],
        _normalize_whole_grid(coerced),
    )
    return _PROFILE_SIGNATURE_TO_INDEX.get(signature)


def is_canonical_profile(grid):
    return canonical_profile_index(grid) is not None


def _draw_profile(profile_index, rng):
    grid = _grid_from_sparse(_PROFILE_INPUT_CELLS[profile_index])
    grid = _safe_transform(grid, rng.randrange(4))
    output = _apply_rule_unchecked(grid)
    output_cells = [
        (row, col)
        for row in range(13)
        for col in range(13)
        if output[row][col] != 0
    ]
    top = min(row for row, _col in output_cells)
    left = min(col for _row, col in output_cells)
    bottom = max(row for row, _col in output_cells)
    right = max(col for _row, col in output_cells)
    delta_row = rng.randint(-top, 12 - bottom)
    delta_col = rng.randint(-left, 12 - right)
    grid = _translate(grid, delta_row, delta_col)

    old_colors = []
    for row in grid:
        for value in row:
            if value not in (0, 2) and value not in old_colors:
                old_colors.append(value)
    replacements = rng.sample(_NON_SPECIAL_COLORS, len(old_colors))
    color_map = dict(zip(old_colors, replacements))
    return [
        [
            value if value in (0, 2) else color_map[value]
            for value in row
        ]
        for row in grid
    ]


def _transform_form(form, transform):
    cells = [
        (row, col, value)
        for row in range(3)
        for col in range(3)
        if (value := form[row][col]) != "."
    ]
    transformed = []
    for row, col, value in cells:
        if transform >= 4:
            col = 2 - col
        for _turn in range(transform % 4):
            row, col = col, 2 - row
        transformed.append((row, col, value))
    return tuple(sorted(transformed))


def _slot_origins(grid_size, rng):
    count = (grid_size + 1) // 4
    span = 4 * (count - 1) + 3
    row_offset = rng.randint(0, grid_size - span)
    col_offset = rng.randint(0, grid_size - span)
    return [
        (row_offset + 4 * row_index, col_offset + 4 * col_index)
        for row_index in range(count)
        for col_index in range(count)
    ]


def _draw_general(grid_size, n_sources, n_targets, band, rng):
    if n_targets < n_sources:
        raise ValueError(
            "n_targets must be at least n_sources so every source is requested"
        )
    slots = _slot_origins(grid_size, rng)
    needed_slots = n_sources + n_targets
    if len(slots) < needed_slots:
        raise ValueError("requested sources and copies do not fit the grid")
    chosen_slots = rng.sample(slots, needed_slots)
    source_slots = chosen_slots[:n_sources]
    target_slots = chosen_slots[n_sources:]

    target_counts = [1] * n_sources
    for _index in range(n_targets - n_sources):
        target_counts[rng.randrange(n_sources)] += 1

    mirror_probability = {
        "easy": 0.45,
        "medium": 0.55,
        "hard": 0.65,
    }[band]
    mirror_source = None
    if rng.random() < mirror_probability:
        mirror_source = rng.randrange(n_sources)

    anchor_colors = []
    available_anchors = list(_NON_SPECIAL_COLORS)
    rng.shuffle(available_anchors)
    for source_index in range(n_sources):
        if source_index == mirror_source:
            anchor_colors.append(2)
        else:
            anchor_colors.append(available_anchors.pop())
    carrier_pool = [
        color
        for color in _NON_SPECIAL_COLORS
        if color not in anchor_colors
    ]
    carrier_colors = rng.sample(carrier_pool, n_sources)

    form_indexes = rng.sample(range(len(_SOURCE_FORMS)), n_sources)
    forms = [
        _transform_form(
            _SOURCE_FORMS[form_index],
            rng.randrange(8),
        )
        for form_index in form_indexes
    ]

    grid = full_grid(grid_size, grid_size, 0)
    source_specs = []
    for source_index, ((top, left), form) in enumerate(
        zip(source_slots, forms)
    ):
        anchor_position = None
        for row, col, role in form:
            color = (
                anchor_colors[source_index]
                if role == "A"
                else carrier_colors[source_index]
            )
            grid[top + row][left + col] = color
            if role == "A":
                anchor_position = (row, col)
        if anchor_position is None:
            raise AssertionError("source form is missing its anchor")
        source_specs.append((form, anchor_position))

    target_source_indexes = [
        source_index
        for source_index, count in enumerate(target_counts)
        for _copy_index in range(count)
    ]
    rng.shuffle(target_source_indexes)
    for (top, left), source_index in zip(
        target_slots,
        target_source_indexes,
    ):
        _form, (anchor_row, anchor_col) = source_specs[source_index]
        if anchor_colors[source_index] == 2:
            anchor_col = 2 - anchor_col
        grid[top + anchor_row][left + anchor_col] = (
            anchor_colors[source_index]
        )
    return grid


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
    band = difficulty or "medium"
    has_override = any(
        overrides.get(label) is not None for label in AXES
    )

    profile_index = None
    if not has_override:
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _PROFILE_PRIOR:
            profile_index = ctx.draw_choice(
                f"canonical_form|{band}",
                tuple(range(len(_PROFILE_INPUT_CELLS))),
            )

    if profile_index is not None:
        grid = _draw_profile(
            profile_index,
            ctx.draw_rng("profile_transform"),
        )
        observed = observe_overrides(grid)
        for label in AXES:
            ctx.draw_choice(label, (observed[label],))
    else:
        grid_size = ctx.draw_int_diff("grid_size", 13, 24)
        if (
            overrides.get("n_targets") == 1
            and overrides.get("n_sources") is None
        ):
            source_options = (1,)
        else:
            source_options = {
                "easy": (1, 1, 1, 2),
                "medium": (1, 1, 2, 2),
                "hard": (1, 2, 2, 2),
            }[band]
        n_sources = ctx.draw_choice("n_sources", source_options)
        target_options = {
            "easy": tuple(
                value
                for value in (1, 1, 2, 2, 3, 4)
                if value >= n_sources
            ),
            "medium": tuple(
                value
                for value in (1, 2, 2, 3, 3, 4)
                if value >= n_sources
            ),
            "hard": tuple(
                value
                for value in (1, 2, 3, 3, 4, 4)
                if value >= n_sources
            ),
        }[band]
        n_targets = ctx.draw_choice("n_targets", target_options)
        grid = _draw_general(
            grid_size,
            n_sources,
            n_targets,
            band,
            ctx.draw_rng("scene"),
        )

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
