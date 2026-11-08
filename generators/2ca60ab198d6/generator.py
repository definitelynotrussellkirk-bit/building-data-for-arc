"""Source-bound generator for the left-guide row-selection crop task.

The selected Racket authority keeps exactly the rows whose column-0 selector is
orange (7), preserves their order, and removes the selector column.  Generated
four-example windows deliberately refute three shortcuts that fit every public
canonical pair: treating every nonzero selector as active, taking alternating
rows, and assuming there are always exactly three selected rows.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "2ca60ab198d6"
VERSION = "3.1.0"
RULE_HASH = "a6ff93ed49cd"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "Column 0 is a row guide: keep rows whose guide cell is orange (7), "
    "discard every other row, and remove the guide column. Inputs have 2..4 "
    "selected rows, at least two rejected rows, observable sparse/medium/dense "
    "payloads, and 2..8 payload colors. A four-profile schedule supplies an "
    "exact canonical-scale alternating example plus counterexamples to nonzero-"
    "guide, alternating-row, fixed-three-row, and any-7-in-row shortcuts."
)

INVARIANTS = [
    "height 6..10 and width 7..11; all cells are integer colors 0..9",
    "column 0 is the guide and contains 2..4 orange (7) keep selectors",
    "at least two rows have a non-7 reject selector",
    "every payload row is nonempty and the payload uses 2..8 nonzero colors",
    "the output is selected payload rows in source order, with column 0 removed",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "profile- and band-aware; canonical profile every four draws",
        "valid": "6..10",
    },
    "grid_w": {
        "type": "int",
        "default": "profile- and band-aware; canonical profile every four draws",
        "valid": "7..11",
    },
    "n_keep": {
        "type": "int",
        "default": "scheduled 3|2|4|4",
        "valid": "2..4",
    },
    "selector_style": {
        "type": "str",
        "default": "scheduled zero_only|mixed|mixed|nonzero_only",
        "valid": "zero_only|nonzero_only|mixed",
    },
    "payload_density": {
        "type": "str",
        "default": "scheduled medium|sparse|dense|medium",
        "valid": "sparse|medium|dense",
    },
    "n_payload_colors": {
        "type": "int",
        "default": "scheduled 7|2|7|8",
        "valid": "2..8",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

SCHEDULE_PROFILES = (
    "canonical_alternating",
    "nonzero_selector",
    "four_selected",
    "irregular_selection",
)

_CANONICAL_PROFILES = ((6, 8), (7, 7), (7, 9))
_DENSITY_TARGET = {"sparse": 0.22, "medium": 0.50, "dense": 0.76}
_NON_SEVEN_COLORS = (1, 2, 3, 4, 5, 6, 8, 9)


def schedule_profile(seed, sample_index, difficulty=None):
    """Any four consecutive sample indexes cover all teaching profiles."""
    del difficulty
    return SCHEDULE_PROFILES[(2 * int(seed) + int(sample_index)) % len(SCHEDULE_PROFILES)]


def rule_mirror(grid):
    """Independent Python mirror of the selected row-filter/crop authority."""
    return [row[1:] for row in grid if row[0] == 7]


def _shape_error(grid):
    if not isinstance(grid, list) or not grid:
        return "grid must be a nonempty list of rows"
    if not all(isinstance(row, list) and row for row in grid):
        return "every row must be a nonempty list"
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return "grid must be rectangular"
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return "grid values must be integer colors 0..9 (not bool)"
    return None


def _payload_colors(grid):
    return {value for row in grid for value in row[1:] if value != 0}


def self_check(grid, *, difficulty=None, meta=None):
    """Check the documented input domain without trusting metadata."""
    del difficulty, meta
    shape_error = _shape_error(grid)
    if shape_error:
        return [shape_error]

    errors = []
    height, width = len(grid), len(grid[0])
    if not 6 <= height <= 10:
        errors.append(f"height must be 6..10, got {height}")
    if not 7 <= width <= 11:
        errors.append(f"width must be 7..11, got {width}")

    keep_count = sum(row[0] == 7 for row in grid)
    drop_count = height - keep_count
    if not 2 <= keep_count <= 4:
        errors.append(f"expected 2..4 orange selectors, got {keep_count}")
    if drop_count < 2:
        errors.append(f"expected at least two rejected rows, got {drop_count}")

    empty_rows = [index for index, row in enumerate(grid) if not any(row[1:])]
    if empty_rows:
        errors.append(f"payload must be nonempty in every row; empty rows={empty_rows[:4]}")

    colors = _payload_colors(grid)
    if not 2 <= len(colors) <= 8:
        errors.append(f"payload must use 2..8 nonzero colors, got {len(colors)}")

    if keep_count and rule_mirror(grid) == grid:
        errors.append("row selection must reduce the guide-bearing input")
    return errors


def strict_canonical_like(grid):
    """Recognize the exact public scale/palette family, not merely lawful inputs."""
    errors = list(self_check(grid))
    if errors:
        return errors
    profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
    if profile not in {(6, 8, 8), (7, 7, 8), (7, 9, 8)}:
        errors.append(f"profile {profile} is outside the three canonical profiles")
    if any(row[0] not in (0, 7) for row in grid):
        errors.append("canonical guide cells are only black (0) or orange (7)")
    return errors


def _draw_exact_int(ctx, name, default, low, high):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int(name, low, high)
    return ctx.draw_int(name, default, default)


def _draw_exact_choice(ctx, name, default, options):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (default,))


def _default_dimensions(ctx, profile, difficulty):
    rng = ctx.draw_rng("default_dimensions")
    if profile in {"canonical_alternating", "four_selected"}:
        return rng.choice(_CANONICAL_PROFILES)
    band = difficulty or "medium"
    ranges = {
        "easy": ((6, 7), (7, 9)),
        "medium": ((7, 9), (8, 10)),
        "hard": ((8, 10), (9, 11)),
    }
    (h_lo, h_hi), (w_lo, w_hi) = ranges[band]
    return rng.randint(h_lo, h_hi), rng.randint(w_lo, w_hi)


def _keep_rows(profile, height, count, rng):
    if profile == "canonical_alternating" and count == 3 and height in (6, 7):
        start = 0 if height == 6 else 1
        return set(range(start, height, 2))

    if profile == "irregular_selection":
        if count == 2:
            return {0, height - 1}
        if count == 3:
            return {0, 1, height - 1}
        return {0, 1, height - 2, height - 1}

    if profile == "four_selected" and count == 4:
        # Two adjacent keepers plus separated keepers make the row schedule
        # visibly unlike the public every-other-row pattern.
        middle = max(2, height // 2)
        rows = {0, 1, middle, height - 1}
        if len(rows) == 4:
            return rows

    return set(rng.sample(range(height), count))


def _selector_values(style, drop_rows, palette, rng):
    nonzero = [color for color in palette if color != 7]
    if style == "zero_only":
        return {row: 0 for row in drop_rows}
    if style == "nonzero_only":
        return {row: nonzero[index % len(nonzero)] for index, row in enumerate(drop_rows)}

    # mixed: the documented domain guarantees at least two rejected rows.
    shuffled = list(drop_rows)
    rng.shuffle(shuffled)
    values = {shuffled[0]: 0, shuffled[1]: nonzero[0]}
    for index, row in enumerate(shuffled[2:], 1):
        values[row] = 0 if index % 2 == 0 else nonzero[index % len(nonzero)]
    return values


def _fill_count(total, height, n_colors, density):
    target = round(total * _DENSITY_TARGET[density])
    count = max(height, n_colors + 1, target)
    if density == "sparse":
        count = min(count, (total - 1) // 3)
    elif density == "medium":
        count = max(count, total // 3 + 1)
        count = min(count, (2 * total - 1) // 3)
    else:
        count = max(count, (2 * total + 2) // 3)
    return min(count, total - 1)


def _populate_payload(grid, keep_rows, palette, density, rng):
    height, width = len(grid), len(grid[0])
    all_positions = [(row, col) for row in range(height) for col in range(1, width)]
    total = len(all_positions)
    count = _fill_count(total, height, len(palette), density)

    # Reserve one payload cell per row, then fill a keyed random sample. This
    # makes the row-filter task visible rather than allowing blank guide rows.
    selected = {(row, rng.randrange(1, width)) for row in range(height)}
    remaining = [position for position in all_positions if position not in selected]
    selected.update(rng.sample(remaining, count - len(selected)))
    selected = sorted(selected)

    drop_rows = sorted(set(range(height)) - set(keep_rows))
    keeper_seven = next(position for position in selected if position[0] in keep_rows)
    dropped_seven = next(position for position in selected if position[0] in drop_rows)
    assignments = {keeper_seven: 7, dropped_seven: 7}

    free = [position for position in selected if position not in assignments]
    rng.shuffle(free)
    for color, position in zip((color for color in palette if color != 7), free):
        assignments[position] = color
    for position in selected:
        assignments.setdefault(position, rng.choice(palette))

    for (row, col), color in assignments.items():
        grid[row][col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; labels remain Racket-authoritative."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override axis/axes: " + ", ".join(unknown))
    for name in ("grid_h", "grid_w", "n_keep", "n_payload_colors"):
        if overrides.get(name) is not None and type(overrides[name]) is not int:
            raise TypeError(f"{name} must be an integer, not {type(overrides[name]).__name__}")
    for name in ("selector_style", "payload_density"):
        if overrides.get(name) is not None and type(overrides[name]) is not str:
            raise TypeError(f"{name} must be a string, not {type(overrides[name]).__name__}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_w = _default_dimensions(ctx, profile, difficulty)
    profile_defaults = {
        "canonical_alternating": (3, "zero_only", "medium", 7),
        "nonzero_selector": (2, "mixed", "sparse", 2),
        "four_selected": (4, "mixed", "dense", 7),
        "irregular_selection": (4, "nonzero_only", "medium", 8),
    }
    default_keep, default_selector, default_density, default_colors = profile_defaults[profile]

    height = _draw_exact_int(ctx, "grid_h", default_h, 6, 10)
    width = _draw_exact_int(ctx, "grid_w", default_w, 7, 11)
    n_keep = _draw_exact_int(ctx, "n_keep", default_keep, 2, 4)
    selector_style = _draw_exact_choice(
        ctx, "selector_style", default_selector, ("zero_only", "nonzero_only", "mixed")
    )
    density = _draw_exact_choice(
        ctx, "payload_density", default_density, ("sparse", "medium", "dense")
    )
    n_colors = _draw_exact_int(ctx, "n_payload_colors", default_colors, 2, 8)

    layout_rng = ctx.draw_rng("layout")
    keep_rows = _keep_rows(profile, height, n_keep, layout_rng)
    if len(keep_rows) != n_keep:
        raise AssertionError("internal keep-row construction lost cardinality")

    color_rng = ctx.draw_rng("payload_palette")
    palette = [7] + color_rng.sample(_NON_SEVEN_COLORS, n_colors - 1)
    grid = full_grid(height, width, 0)

    drop_rows = sorted(set(range(height)) - keep_rows)
    selector_values = _selector_values(
        selector_style, drop_rows, palette, ctx.draw_rng("selector_values")
    )
    for row in range(height):
        grid[row][0] = 7 if row in keep_rows else selector_values[row]

    _populate_payload(
        grid,
        keep_rows,
        palette,
        density,
        ctx.draw_rng("payload_cells"),
    )
    return grid


def observe_overrides(grid):
    """Recover every exact advertised axis from a generated grid."""
    shape_error = _shape_error(grid)
    if shape_error:
        raise ValueError(shape_error)
    height, width = len(grid), len(grid[0])
    keep_count = sum(row[0] == 7 for row in grid)
    drop_values = [row[0] for row in grid if row[0] != 7]
    if drop_values and all(value == 0 for value in drop_values):
        selector_style = "zero_only"
    elif drop_values and all(value != 0 for value in drop_values):
        selector_style = "nonzero_only"
    else:
        selector_style = "mixed"

    payload_total = height * (width - 1)
    payload_filled = sum(value != 0 for row in grid for value in row[1:])
    ratio = payload_filled / payload_total
    if ratio < 1 / 3:
        density = "sparse"
    elif ratio < 2 / 3:
        density = "medium"
    else:
        density = "dense"

    return {
        "grid_h": height,
        "grid_w": width,
        "n_keep": keep_count,
        "selector_style": selector_style,
        "payload_density": density,
        "n_payload_colors": len(_payload_colors(grid)),
    }


# ---- Explicit rival rules and semantic witnesses -------------------------


def _rival_nonzero_selector(grid):
    return [row[1:] for row in grid if row[0] != 0]


def _rival_alternate_from_first_keep(grid):
    first = next((index for index, row in enumerate(grid) if row[0] == 7), 0)
    return [grid[index][1:] for index in range(first, len(grid), 2)]


def _rival_first_three_selected(grid):
    return [row[1:] for row in grid if row[0] == 7][:3]


def _rival_any_seven_in_row(grid):
    return [row[1:] for row in grid if 7 in row]


def _witness_nonzero_drop_selector(grid):
    return any(row[0] not in (0, 7) for row in grid)


def _witness_nonalternating_keepers(grid):
    return _rival_alternate_from_first_keep(grid) != rule_mirror(grid)


def _witness_more_than_three_keepers(grid):
    return sum(row[0] == 7 for row in grid) > 3


def _witness_payload_seven_decoy(grid):
    return any(row[0] != 7 and 7 in row[1:] for row in grid)


SEMANTIC_RIVALS = {
    "nonzero_selector": _rival_nonzero_selector,
    "alternate_from_first_keep": _rival_alternate_from_first_keep,
    "first_three_selected": _rival_first_three_selected,
    "any_seven_in_row": _rival_any_seven_in_row,
}

CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "nonzero_selector",
        "alternate_from_first_keep",
        "first_three_selected",
    )
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES = {
    "nonzero_drop_selector": _witness_nonzero_drop_selector,
    "nonalternating_keepers": _witness_nonalternating_keepers,
    "more_than_three_keepers": _witness_more_than_three_keepers,
    "payload_seven_decoy": _witness_payload_seven_decoy,
}

WITNESS_RIVALS = {
    "nonzero_drop_selector": ["nonzero_selector"],
    "nonalternating_keepers": ["alternate_from_first_keep"],
    "more_than_three_keepers": ["first_three_selected"],
    "payload_seven_decoy": ["any_seven_in_row"],
}


def lesson_identifiable(demos, query):
    """Reject a lesson when any declared rival survives every demonstration."""
    reasons = []
    query_output = query.get("output")
    if query_output is None:
        query_output = rule_mirror(query["input"])
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
            if fits:
                suffix = (
                    "and also matches the query"
                    if rival(query["input"]) == query_output
                    else "but predicts a different query answer"
                )
                reasons.append(f"competitor {name!r} fits every demonstration {suffix}")
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
    return reasons
