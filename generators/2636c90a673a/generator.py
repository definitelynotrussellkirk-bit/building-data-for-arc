"""Generator for arc_puzzle_bank_fifth21:M34.

The first row is a mask.  Blue (1) cells select body columns; the rule drops
that row and outputs the selected columns in their original order.  Generated
headers contain repeated non-blue distractors and a two-phase frequency-decoy
schedule so lessons distinguish "blue" from canonical-fitting nonzero, odd,
repetition, and modal-marker shortcuts.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2636c90a673a"
TASK_ID = GENERATOR_ID
RULE_HASH = "2d7db8fb7aa9"
VERSION = "2.1.0"
SUMMARY = "A row-0 blue mask selects columns; scheduled colored decoys teach blue identity."

INVARIANTS = [
    "row 0 has 2..5 blue selectors and at least two unselected columns",
    "repeated odd non-blue header distractors teach equality-to-blue, not frequency",
    "the body has canonical scale/palette support and one connected nonzero scene",
    "the output is rows 1+ restricted, in order, to columns whose header is blue(1)",
]

_BODY_STYLES = ("row_bands", "column_bands", "mixed")
_DENSITIES = ("medium", "dense")
_CANONICAL_PROFILES = (
    # input height, input width, total palette size, canonical selector count
    (5, 7, 9, 4),
    (6, 8, 10, 4),
    (6, 9, 10, 5),
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "one of the three canonical profiles",
        "valid": "5..9",
    },
    "grid_w": {
        "type": "int",
        "default": "one of the three canonical profiles",
        "valid": "7..12",
    },
    "n_keep": {
        "type": "int",
        "default": "canonical profile count",
        "valid": "2..5",
    },
    "palette_size": {
        "type": "int",
        "default": "one of the three canonical profiles",
        "valid": "4..10",
    },
    "body_style": {
        "type": "str",
        "default": "difficulty-weighted",
        "valid": "row_bands|column_bands|mixed",
    },
    "density": {
        "type": "str",
        "default": "difficulty-weighted",
        "valid": "medium|dense",
    },
}

# Every advertised joint combination is constructive: the smallest width (7)
# still leaves two non-selected columns when n_keep is maximal (5).
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

_INT_DOMAINS = {
    "grid_h": (5, 9),
    "grid_w": (7, 12),
    "n_keep": (2, 5),
    "palette_size": (4, 10),
}
_STR_DOMAINS = {
    "body_style": _BODY_STYLES,
    "density": _DENSITIES,
}


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, (lo, hi) in _INT_DOMAINS.items():
        if name not in overrides:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
    for name, domain in _STR_DOMAINS.items():
        if name not in overrides:
            continue
        value = overrides[name]
        if type(value) is not str or value not in domain:
            raise ValueError(f"{name} must be one of {domain}, got {value!r}")


def _draw_profile(ctx, difficulty):
    if difficulty == "easy":
        choices = (_CANONICAL_PROFILES[0],) * 5 + (_CANONICAL_PROFILES[1],) * 2 + (_CANONICAL_PROFILES[2],)
    elif difficulty == "hard":
        choices = (_CANONICAL_PROFILES[2],) * 5 + (_CANONICAL_PROFILES[1],) * 2 + (_CANONICAL_PROFILES[0],)
    else:
        choices = _CANONICAL_PROFILES
    return ctx.draw_rng("canonical_profile").choice(choices)


def _draw_int_axis(ctx, name, lo, hi, default):
    """Record a canonical default while preserving the entire exact override domain."""
    if name in ctx.overrides:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, (default,))


def _draw_header(ctx, width, n_keep, sample_index):
    """Draw a blue mask plus scheduled non-blue frequency decoys."""
    rng = ctx.draw_rng("header_layout")
    keep = sorted(rng.sample(range(width), n_keep))
    unselected = [c for c in range(width) if c not in keep]
    header = [0] * width
    for col in keep:
        header[col] = 1

    # Every default repeats an odd non-blue color, defeating both parity and
    # "select the repeated color" shortcuts.  Even sample indices use n_keep=2
    # and one extra color-3 decoy, so color 3 is more frequent than blue; every
    # four consecutive lesson pairs contain two such witnesses.
    if sample_index % 2 == 0 and len(unselected) > n_keep:
        decoy_count = n_keep + 1
    else:
        decoy_count = min(2, len(unselected))
    decoys = rng.sample(unselected, decoy_count)
    for col in decoys:
        header[col] = 3

    remaining = [col for col in unselected if header[col] == 0]
    if remaining:
        header[rng.choice(remaining)] = 2
    return header


def _interval_containing(rng, width, anchor, span):
    span = max(1, min(span, width))
    lo = max(0, anchor - span + 1)
    hi = min(anchor, width - span)
    start = rng.randint(lo, hi)
    return range(start, start + span)


def _body_cells(ctx, height, width, style, density):
    """Construct a single connected nonzero body with a fully occupied first row."""
    rng = ctx.draw_rng("body_geometry")
    anchor = rng.randrange(width)
    cells = {(1, col) for col in range(width)}

    if style == "row_bands":
        span = width - 1 if density == "dense" else max(3, (width + 1) // 2)
        for row in range(2, height):
            for col in _interval_containing(rng, width, anchor, span):
                cells.add((row, col))
    elif style == "column_bands":
        count = width - 1 if density == "dense" else max(3, width // 2)
        others = [col for col in range(width) if col != anchor]
        columns = {anchor, *rng.sample(others, count - 1)}
        for row in range(2, height):
            for col in columns:
                cells.add((row, col))
    else:  # mixed
        n_columns = max(2, width // 2) if density == "dense" else 2
        others = [col for col in range(width) if col != anchor]
        columns = {anchor, *rng.sample(others, n_columns - 1)}
        span = max(3, (width + 1) // 2) if density == "dense" else max(2, width // 3)
        for row in range(2, height):
            cells.update((row, col) for col in columns)
            cells.update(
                (row, col)
                for col in _interval_containing(rng, width, anchor, span)
            )

    # Keep background color 0 represented even at the smallest, densest joint
    # override.  Removing a non-anchor cell cannot disconnect the anchor spine.
    if len(cells) == (height - 1) * width:
        cells.remove((height - 1, (anchor + 1) % width))
    return cells


def _paint_body(ctx, grid, cells, palette_size):
    """Paint canonical-scale monochrome structure plus the requested palette."""
    rng = ctx.draw_rng("body_colors")

    # Canonical demonstrations contain a full-width monochrome body row.  Keep
    # that scale reachable instead of scattering every color cell-by-cell.
    stripe = sorted((row, col) for row, col in cells if row == 1)
    for row, col in stripe:
        grid[row][col] = 2

    remaining = sorted(cells - set(stripe))
    rng.shuffle(remaining)

    # Header colors already guarantee 0,1,2,3.  Introduce each larger requested
    # color once, then vary the rest without exceeding the declared palette.
    required = list(range(4, palette_size))
    for (row, col), color in zip(remaining, required):
        grid[row][col] = color

    tail = remaining[len(required):]
    body_colors = list(range(1, palette_size))
    rng.shuffle(body_colors)
    for index, (row, col) in enumerate(tail):
        grid[row][col] = body_colors[index % len(body_colors)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile_h, profile_w, profile_palette, profile_keep = _draw_profile(ctx, difficulty)
    height = _draw_int_axis(ctx, "grid_h", 5, 9, profile_h)
    width = _draw_int_axis(ctx, "grid_w", 7, 12, profile_w)
    # Two frequency-decoy examples in every four-pair window make the strongest
    # canonical-fitting marker-frequency rival fail under every query rotation.
    scheduled_keep = 2 if sample_index % 2 == 0 else profile_keep
    n_keep = _draw_int_axis(ctx, "n_keep", 2, 5, scheduled_keep)
    palette_size = _draw_int_axis(ctx, "palette_size", 4, 10, profile_palette)

    style_options = _BODY_STYLES
    if difficulty == "easy":
        style_options = ("row_bands",) * 3 + _BODY_STYLES
    elif difficulty == "hard":
        style_options = ("mixed",) * 3 + _BODY_STYLES
    body_style = ctx.draw_choice("body_style", style_options)

    density_options = _DENSITIES
    if difficulty == "easy":
        density_options = ("medium",) * 4 + ("dense",)
    elif difficulty == "hard":
        density_options = ("dense",) * 4 + ("medium",)
    density = ctx.draw_choice("density", density_options)

    grid = full_grid(height, width, 0)
    grid[0] = _draw_header(ctx, width, n_keep, sample_index)
    cells = _body_cells(ctx, height, width, body_style, density)
    _paint_body(ctx, grid, cells, palette_size)
    return grid


def _grid_structure_errors(grid):
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["ragged grid"]
    errors = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) must be an integer color 0..9")
                return errors
    return errors


def _nonzero_component_count(grid):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            row, col = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (row + dr, col + dc)
                if point in remaining:
                    remaining.remove(point)
                    stack.append(point)
    return count


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the declared task manifold, including all canonical inputs."""
    errors = _grid_structure_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not 5 <= height <= 9:
        errors.append(f"height {height} outside 5..9")
    if not 7 <= width <= 12:
        errors.append(f"width {width} outside 7..12")

    header = grid[0]
    keep = [col for col, value in enumerate(header) if value == 1]
    if not 2 <= len(keep) <= 5:
        errors.append(f"expected 2..5 blue selectors, got {len(keep)}")
    if width - len(keep) < 2:
        errors.append("mask must leave at least two unselected columns")

    palette = {value for row in grid for value in row}
    if 0 not in palette or 1 not in palette:
        errors.append("palette must include background 0 and selector blue 1")
    if not 4 <= len(palette) <= 10:
        errors.append(f"palette size {len(palette)} outside 4..10")

    body = grid[1:]
    if not any(all(value != 0 for value in row) for row in body):
        errors.append("body needs a fully occupied row connecting the header scene")
    body_nonzero_colors = {value for row in body for value in row if value != 0}
    if len(body_nonzero_colors) < 2:
        errors.append("body needs at least two nonzero colors")
    if _nonzero_component_count(grid) != 1:
        errors.append("all nonzero cells must form one 4-connected scene")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    """Recover every exact numeric axis from returned pixels."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_keep": sum(value == 1 for value in grid[0]),
        "palette_size": len({value for row in grid for value in row}),
    }


def _apply_rule(grid):
    keep = [col for col, value in enumerate(grid[0]) if value == 1]
    return [[row[col] for col in keep] for row in grid[1:]]


def _rival_nonzero_header(grid):
    keep = [col for col, value in enumerate(grid[0]) if value != 0]
    return [[row[col] for col in keep] for row in grid[1:]]


def _rival_odd_header(grid):
    keep = [col for col, value in enumerate(grid[0]) if value % 2 == 1]
    return [[row[col] for col in keep] for row in grid[1:]]


def _rival_repeated_nonzero_header(grid):
    counts = Counter(grid[0])
    keep = [
        col for col, value in enumerate(grid[0])
        if value != 0 and counts[value] > 1
    ]
    return [[row[col] for col in keep] for row in grid[1:]]


def _rival_modal_nonzero_header(grid):
    counts = Counter(value for value in grid[0] if value != 0)
    if not counts:
        return [[] for _ in grid[1:]]
    marker = min(counts, key=lambda value: (-counts[value], value))
    keep = [col for col, value in enumerate(grid[0]) if value == marker]
    return [[row[col] for col in keep] for row in grid[1:]]


def _rival_drop_header_only(grid):
    return deepcopy(grid[1:])


def _has_colored_header_distractors(grid):
    return any(value not in (0, 1) for value in grid[0])


def _has_repeated_nonblue_header(grid):
    counts = Counter(grid[0])
    return any(color not in (0, 1) and count > 1 for color, count in counts.items())


def _has_frequency_decoy(grid):
    counts = Counter(grid[0])
    blue = counts.get(1, 0)
    return any(color not in (0, 1) and count > blue for color, count in counts.items())


SEMANTIC_WITNESSES = {
    "colored_header_distractors": _has_colored_header_distractors,
    "repeated_nonblue_header": _has_repeated_nonblue_header,
    "frequency_decoy": _has_frequency_decoy,
}
SEMANTIC_RIVALS = {
    "nonzero_header": _rival_nonzero_header,
    "odd_header": _rival_odd_header,
    "repeated_nonzero_header": _rival_repeated_nonzero_header,
    "modal_nonzero_header": _rival_modal_nonzero_header,
}
WITNESS_RIVALS = {
    "colored_header_distractors": ["nonzero_header", "odd_header"],
    "repeated_nonblue_header": ["repeated_nonzero_header"],
    "frequency_decoy": ["modal_nonzero_header"],
}
CANONICAL_SHORTCUTS = {
    "nonzero_header": _rival_nonzero_header,
    "odd_header": _rival_odd_header,
    "repeated_nonzero_header": _rival_repeated_nonzero_header,
    "modal_nonzero_header": _rival_modal_nonzero_header,
}
LESSON_COMPETITORS = {
    "nonzero_header": _rival_nonzero_header,
    "odd_header": _rival_odd_header,
    "repeated_nonzero_header": _rival_repeated_nonzero_header,
    "modal_nonzero_header": _rival_modal_nonzero_header,
    "drop_header_only": _rival_drop_header_only,
}


def lesson_identifiable(demos, query):
    """Report a rival that fits all demonstrations but changes this query."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
