"""Generator for ARC task 82819916 / catalog task 83ca9df09514.

A uniquely dense template row assigns a template color to every column.  Each
sparse key row reveals a destination color for every template-color group.  The
selected rule expands those sparse reveals across all columns carrying the same
template color, independently for each key row.

Version 3 replaces a broad but dishonest surface (unused axes, undeclared axes,
and invalid negative textures) with six fully constructive and observable axes.
Each ten-sample cycle starts with exact coverage of all five canonical
(height, width, palette-size) profiles, then adds five wider contrastive cases
that exercise the declared scale range.  Generated examples deliberately rebut
three shortcuts that fit every canonical pair:
reading only the first three columns, assuming exactly two template groups, and
assuming the template is always row one.
"""
from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "83ca9df09514"
TASK_ID = "83ca9df09514"
VERSION = "3.0.1"
RULE_HASH = "1dc6f00b70c9"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Find the uniquely dense template row.  In every sparse key row, pair each "
    "revealed color with the template color above it, then fill every column "
    "belonging to that template-color group.  The curriculum exactly covers "
    "all five canonical size/palette profiles and falsifies first-three-column, "
    "two-group, and fixed-row-one shortcuts."
)

INVARIANTS = [
    "background is ARC color 0",
    "the template is the unique densest row and occupies every column",
    "the template contains 2..4 repeated color groups",
    "each key row consistently reveals one destination for every template group",
    "key rows are sparse and the rule expands every group beyond its reveal cells",
]

TEMPLATE_POSITIONS = ("top", "middle", "bottom", "random")
KEY_LAYOUTS = ("prefix", "shifted", "scattered")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

AXES = {
    "grid_h": {
        "type": "int",
        "default": "five-profile canonical schedule",
        "valid": "6..16",
    },
    "grid_w": {
        "type": "int",
        "default": "five-profile canonical schedule",
        "valid": "8..18",
    },
    "n_keys": {
        "type": "int",
        "default": "2 easy, 3 medium/default, 4 hard",
        "valid": "1..4",
    },
    "n_groups": {
        "type": "int",
        "default": "3 easy/medium/default, 4 hard",
        "valid": "2..4",
    },
    "template_position": {
        "type": "enum",
        "default": "scheduled middle/bottom",
        "valid": TEMPLATE_POSITIONS,
    },
    "key_layout": {
        "type": "enum",
        "default": "scattered",
        "valid": KEY_LAYOUTS,
    },
}

# These are exactly the canonical (height, width, total palette size including
# background) profiles.  The first half of every schedule cycle covers each
# profile exactly; the second half holds height/palette anchors while widening
# the grid to prevent the declared 8..18 width axis from becoming override-only.
CANONICAL_PROFILES: tuple[tuple[int, int, int], ...] = (
    (6, 8, 5),
    (10, 8, 5),
    (10, 8, 7),
    (12, 8, 8),
    (14, 10, 7),
)
SCHEDULE_PROFILES = tuple(range(len(CANONICAL_PROFILES)))
CONTRASTIVE_WIDTHS: tuple[int, ...] = (18, 15, 12, 9, 17)
SCHEDULE_PERIOD = len(CANONICAL_PROFILES) + len(CONTRASTIVE_WIDTHS)


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> int:
    """Return the deterministic five-way canonical-profile slot."""
    del seed, difficulty
    return sample_index % len(CANONICAL_PROFILES)


def _validate_request(seed, sample_index, difficulty, overrides: dict) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    if any(value is None for value in overrides.values()):
        raise ValueError("explicit override values may not be None")

    integer_axes = {
        "grid_h": (6, 16),
        "grid_w": (8, 18),
        "n_keys": (1, 4),
        "n_groups": (2, 4),
    }
    for label, (lo, hi) in integer_axes.items():
        if label not in overrides:
            continue
        value = overrides[label]
        if type(value) is not int:
            raise TypeError(f"{label} must be an integer (not bool)")
        if not lo <= value <= hi:
            raise ValueError(f"{label}={value} outside [{lo},{hi}]")

    enum_axes = {
        "template_position": TEMPLATE_POSITIONS,
        "key_layout": KEY_LAYOUTS,
    }
    for label, options in enum_axes.items():
        if label not in overrides:
            continue
        value = overrides[label]
        if not isinstance(value, str):
            raise TypeError(f"{label} must be a string")
        if value not in options:
            raise ValueError(f"{label}={value!r} not in {options}")


def _draw_exact_int(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    if label in ctx.overrides:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_choice(label, (scheduled,))


def _draw_exact_choice(ctx, label: str, options: tuple[str, ...], scheduled: str) -> str:
    if label in ctx.overrides:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _scheduled_defaults(
    profile: int, sample_index: int, difficulty: str | None
) -> tuple[int, int, int, int, int, str, str]:
    height, canonical_width, palette_size = CANONICAL_PROFILES[profile]
    slot = sample_index % SCHEDULE_PERIOD
    width = (
        canonical_width
        if slot < len(CANONICAL_PROFILES)
        else CONTRASTIVE_WIDTHS[slot - len(CANONICAL_PROFILES)]
    )
    band = difficulty or "medium"
    if band == "easy":
        n_keys, n_groups = 2, 3
    elif band == "hard":
        n_keys, n_groups = 4, 4
    else:
        n_keys, n_groups = 3, 3
    position = "middle" if profile % 2 == 0 else "bottom"
    return height, width, palette_size, n_keys, n_groups, position, "scattered"


def _choose_template_row(height: int, position: str, rng) -> int:
    if position == "top":
        return 1
    if position == "middle":
        return height // 2
    if position == "bottom":
        return height - 2
    reserved = {1, height // 2, height - 2}
    choices = [row for row in range(height) if row not in reserved]
    return rng.choice(choices)


def _reveal_plan(width: int, n_groups: int, layout: str, rng) -> tuple[list[int], list[int]]:
    """Return key columns and their group indices.

    Group zero is deliberately revealed twice.  Every other group is revealed
    once, giving n_groups+1 sparse cells per key row.  The template construction
    later guarantees every group has at least two full-row members.
    """
    group_indices = [0, 0, *range(1, n_groups)]
    if layout == "prefix":
        columns = list(range(n_groups + 1))
    elif layout == "shifted":
        columns = list(range(1, n_groups + 2))
    else:
        late = list(range(3, width - 1))
        rng.shuffle(late)
        needed = n_groups - 1
        if len(late) < needed:
            raise ValueError(
                f"scattered layout needs {needed} late columns in width {width}"
            )
        columns = [0, width - 1, *late[:needed]]
    return columns, group_indices


def _template_groups(width: int, n_groups: int, reveal_columns: list[int], reveal_groups: list[int], rng) -> list[int]:
    groups: list[int | None] = [None] * width
    for column, group in zip(reveal_columns, reveal_groups):
        groups[column] = group

    # Every template color must repeat.  Group zero already has two reveal
    # positions; seed one additional member for every other group.
    for group in range(n_groups):
        while groups.count(group) < 2:
            free = [column for column, value in enumerate(groups) if value is None]
            if not free:
                raise ValueError("template width cannot repeat every group")
            groups[rng.choice(free)] = group

    for column, value in enumerate(groups):
        if value is None:
            groups[column] = rng.randrange(n_groups)
    return [int(value) for value in groups]


def _draw_colors(ctx, target_palette_size: int, n_groups: int, n_keys: int) -> tuple[list[int], list[list[int]]]:
    """Choose template colors and per-row destination mappings.

    The internal target is exact for every scheduled default.  Under unusual
    override combinations it is clipped to what the requested number of groups
    and mapping slots can represent; all public overrides remain constructive.
    """
    rng = ctx.draw_rng("palette")
    colors = list(range(1, 10))
    rng.shuffle(colors)

    mapping_slots = n_groups * n_keys
    requested_foreground = target_palette_size - 1
    actual_foreground = max(
        n_groups,
        min(requested_foreground, 9, n_groups + mapping_slots),
    )
    template_colors = colors[:n_groups]
    new_colors = colors[n_groups:actual_foreground]

    # Put new colors first so every one is exercised whenever the slot count
    # permits it (the clipping above guarantees that it does).
    mapping_palette = [*new_colors, *template_colors]
    rows: list[list[int]] = []
    for row_index in range(n_keys):
        values = [
            mapping_palette[(row_index + group) % len(mapping_palette)]
            for group in range(n_groups)
        ]
        rows.append(values)

    used_new = {value for row in rows for value in row if value in new_colors}
    if len(used_new) != len(new_colors):
        # This only matters for high-palette, low-group schedules.  Deterministic
        # slot replacement preserves per-row distinctness because all colors in
        # mapping_palette are distinct and target slots are chosen row-major.
        missing = [color for color in new_colors if color not in used_new]
        for slot, color in enumerate(missing):
            row_index, group = divmod(slot, n_groups)
            rows[row_index][group] = color

    # Repair a rare row-local duplicate introduced by the coverage replacement.
    for row_index, values in enumerate(rows):
        if len(set(values)) == n_groups:
            continue
        available = [color for color in mapping_palette if color not in values]
        seen: set[int] = set()
        for group, value in enumerate(values):
            if value in seen:
                if not available:
                    raise ValueError("cannot construct distinct row mapping")
                values[group] = available.pop(0)
            seen.add(values[group])
        rows[row_index] = values
    return template_colors, rows


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the selected Racket rule is authority."""
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    profile = schedule_profile(seed, sample_index, difficulty)
    (
        default_h,
        default_w,
        target_palette_size,
        default_keys,
        default_groups,
        default_position,
        default_layout,
    ) = _scheduled_defaults(profile, sample_index, difficulty)

    height = _draw_exact_int(ctx, "grid_h", 6, 16, default_h)
    width = _draw_exact_int(ctx, "grid_w", 8, 18, default_w)
    n_keys = _draw_exact_int(ctx, "n_keys", 1, 4, default_keys)
    n_groups = _draw_exact_int(ctx, "n_groups", 2, 4, default_groups)
    position = _draw_exact_choice(
        ctx, "template_position", TEMPLATE_POSITIONS, default_position
    )
    key_layout = _draw_exact_choice(ctx, "key_layout", KEY_LAYOUTS, default_layout)

    layout_rng = ctx.draw_rng("layout")
    template_row = _choose_template_row(height, position, layout_rng)
    reveal_columns, reveal_groups = _reveal_plan(
        width, n_groups, key_layout, layout_rng
    )
    group_by_column = _template_groups(
        width, n_groups, reveal_columns, reveal_groups, layout_rng
    )
    template_colors, row_mappings = _draw_colors(
        ctx, target_palette_size, n_groups, n_keys
    )

    grid = full_grid(height, width, 0)
    for column, group in enumerate(group_by_column):
        grid[template_row][column] = template_colors[group]

    available_rows = [row for row in range(height) if row != template_row]
    key_rows = layout_rng.sample(available_rows, n_keys)
    for key_row, destinations in zip(key_rows, row_mappings):
        for column, group in zip(reveal_columns, reveal_groups):
            grid[key_row][column] = destinations[group]
    return grid


def _validate_grid_shape(grid) -> tuple[list[str], int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"], 0, 0
    height, width = len(grid), len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid rows must be non-empty and rectangular"], height, width
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        for column, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(
                    f"cell ({row_index},{column}) has invalid ARC color {value!r}"
                )
    return errors, height, width


def _find_template_row(grid: list[list[int]]) -> int:
    counts = [sum(value != 0 for value in row) for row in grid]
    return counts.index(max(counts))


def _row_mapping(
    grid: list[list[int]], template_row: int, row: int, *, first_columns: int | None = None
) -> dict[int, int]:
    template = grid[template_row]
    stop = len(template) if first_columns is None else min(first_columns, len(template))
    mapping: dict[int, int] = {}
    for column in range(stop):
        value = grid[row][column]
        if value != 0:
            mapping[template[column]] = value
    return mapping


def _solve_with_template(
    grid: list[list[int]],
    template_row: int,
    *,
    first_columns: int | None = None,
    allowed_template_colors: set[int] | None = None,
) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    template = grid[template_row]
    output = deepcopy(grid)
    for row in range(height):
        if row == template_row:
            continue
        if not any(grid[row]):
            output[row] = [0] * width
            continue
        mapping = _row_mapping(
            grid, template_row, row, first_columns=first_columns
        )
        if allowed_template_colors is not None:
            mapping = {
                color: value
                for color, value in mapping.items()
                if color in allowed_template_colors
            }
        output[row] = [mapping.get(template[column], 0) for column in range(width)]
    return output


def _apply_rule(grid: list[list[int]]) -> list[list[int]]:
    """Input-pure Python mirror of the selected Racket rule."""
    return _solve_with_template(grid, _find_template_row(grid))


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    return _apply_rule(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every public axis from a generated grid."""
    template_row = _find_template_row(grid)
    height, width = len(grid), len(grid[0])
    template_colors = [value for value in grid[template_row] if value != 0]
    n_groups = len(set(template_colors))
    key_rows = [
        row
        for row in range(height)
        if row != template_row and any(grid[row])
    ]
    key_columns = [column for column, value in enumerate(grid[key_rows[0]]) if value != 0]
    if key_columns == list(range(n_groups + 1)):
        layout = "prefix"
    elif key_columns == list(range(1, n_groups + 2)):
        layout = "shifted"
    else:
        layout = "scattered"

    if template_row == 1:
        position = "top"
    elif template_row == height // 2:
        position = "middle"
    elif template_row == height - 2:
        position = "bottom"
    else:
        position = "random"
    return {
        "grid_h": height,
        "grid_w": width,
        "n_keys": len(key_rows),
        "n_groups": n_groups,
        "template_position": position,
        "key_layout": layout,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate canonical ownership and the generated task grammar."""
    del difficulty, meta
    errors, height, width = _validate_grid_shape(grid)
    if errors:
        return errors

    if not (6 <= height <= 16 and 8 <= width <= 18):
        errors.append(f"expected dimensions 6..16 by 8..18, got {height}x{width}")

    row_counts = [sum(value != 0 for value in row) for row in grid]
    maximum = max(row_counts)
    if row_counts.count(maximum) != 1:
        errors.append("template row is not uniquely densest")
        return errors
    template_row = row_counts.index(maximum)
    if maximum != width:
        errors.append("template row must occupy every column")

    template = grid[template_row]
    template_groups = {value for value in template if value != 0}
    if not 2 <= len(template_groups) <= 4:
        errors.append(
            f"expected 2..4 template color groups, got {len(template_groups)}"
        )
    for color in template_groups:
        if template.count(color) < 2:
            errors.append(f"template color {color} is not repeated")

    key_rows = [
        row
        for row in range(height)
        if row != template_row and row_counts[row] > 0
    ]
    if not 1 <= len(key_rows) <= 4:
        errors.append(f"expected 1..4 key rows, got {len(key_rows)}")

    for row in key_rows:
        if row_counts[row] >= maximum:
            errors.append(f"key row {row} is not sparse relative to template")
            continue
        mapping: dict[int, int] = {}
        for column, value in enumerate(grid[row]):
            if value == 0:
                continue
            template_color = template[column]
            if template_color == 0:
                errors.append(
                    f"key row {row} has a reveal outside template support"
                )
                continue
            if template_color in mapping and mapping[template_color] != value:
                errors.append(
                    f"key row {row} assigns conflicting values to template color {template_color}"
                )
            mapping[template_color] = value
        missing = sorted(template_groups - set(mapping))
        if missing:
            errors.append(
                f"key row {row} does not reveal template group(s) {missing}"
            )
        if len(set(mapping.values())) != len(mapping):
            errors.append(f"key row {row} destination colors must be distinct")

    if not errors and _apply_rule(grid) == grid:
        errors.append("selected rule leaves the input unchanged")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


# ---------------------------------------------------------------------------
# Semantic rivals and witnesses
# ---------------------------------------------------------------------------

def _identity_rival(grid: list[list[int]]) -> list[list[int]]:
    return deepcopy(grid)


def _single_destination_rival(grid: list[list[int]]) -> list[list[int]]:
    template_row = _find_template_row(grid)
    template = grid[template_row]
    output = deepcopy(grid)
    for row in range(len(grid)):
        if row == template_row:
            continue
        revealed = next((value for value in grid[row] if value != 0), 0)
        output[row] = [revealed if value != 0 and revealed else 0 for value in template]
    return output


def _first_three_columns_rival(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with_template(
        grid, _find_template_row(grid), first_columns=3
    )


def _two_groups_rival(grid: list[list[int]]) -> list[list[int]]:
    template_row = _find_template_row(grid)
    allowed: list[int] = []
    for value in grid[template_row]:
        if value != 0 and value not in allowed:
            allowed.append(value)
        if len(allowed) == 2:
            break
    return _solve_with_template(
        grid, template_row, allowed_template_colors=set(allowed)
    )


def _row_one_template_rival(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with_template(grid, 1)


def _first_key_mapping_rival(grid: list[list[int]]) -> list[list[int]]:
    template_row = _find_template_row(grid)
    template = grid[template_row]
    first_key = next(
        row
        for row in range(len(grid))
        if row != template_row and any(grid[row])
    )
    mapping = _row_mapping(grid, template_row, first_key)
    output = deepcopy(grid)
    for row in range(len(grid)):
        if row == template_row:
            continue
        if not any(grid[row]):
            output[row] = [0] * len(template)
        else:
            output[row] = [mapping.get(color, 0) for color in template]
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "leave_sparse_rows_unchanged": _identity_rival,
    "one_destination_color_per_row": _single_destination_rival,
    "first_three_columns_only": _first_three_columns_rival,
    "exactly_two_template_groups": _two_groups_rival,
    "template_is_row_one": _row_one_template_rival,
    "reuse_first_key_mapping": _first_key_mapping_rival,
}

CANONICAL_SHORTCUTS = {
    "first_three_columns_only": _first_three_columns_rival,
    "exactly_two_template_groups": _two_groups_rival,
    "template_is_row_one": _row_one_template_rival,
}

LESSON_COMPETITORS = SEMANTIC_RIVALS


def _late_group_reveal(grid: list[list[int]]) -> bool:
    template_row = _find_template_row(grid)
    full_groups = set(grid[template_row]) - {0}
    for row in range(len(grid)):
        if row == template_row or not any(grid[row]):
            continue
        early = set(_row_mapping(grid, template_row, row, first_columns=3))
        if early != full_groups:
            return True
    return False


def _more_than_two_groups(grid: list[list[int]]) -> bool:
    template_row = _find_template_row(grid)
    return len(set(grid[template_row]) - {0}) > 2


def _template_not_row_one(grid: list[list[int]]) -> bool:
    return _find_template_row(grid) != 1


def _row_specific_mappings(grid: list[list[int]]) -> bool:
    template_row = _find_template_row(grid)
    mappings = []
    for row in range(len(grid)):
        if row != template_row and any(grid[row]):
            mappings.append(tuple(sorted(_row_mapping(grid, template_row, row).items())))
    return len(set(mappings)) > 1


def _group_expansion(grid: list[list[int]]) -> bool:
    return _apply_rule(grid) != grid


def _multiple_destination_groups(grid: list[list[int]]) -> bool:
    template_row = _find_template_row(grid)
    return all(
        len(set(_row_mapping(grid, template_row, row).values())) >= 2
        for row in range(len(grid))
        if row != template_row and any(grid[row])
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "late_group_reveal": _late_group_reveal,
    "more_than_two_template_groups": _more_than_two_groups,
    "template_not_row_one": _template_not_row_one,
    "row_specific_mappings": _row_specific_mappings,
    "group_expansion": _group_expansion,
    "multiple_destination_groups": _multiple_destination_groups,
}

WITNESS_RIVALS = {
    "late_group_reveal": ["first_three_columns_only"],
    "more_than_two_template_groups": ["exactly_two_template_groups"],
    "template_not_row_one": ["template_is_row_one"],
    "row_specific_mappings": ["reuse_first_key_mapping"],
    "group_expansion": ["leave_sparse_rows_unchanged"],
    "multiple_destination_groups": ["one_destination_color_per_row"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every query-changing named rival to be contradicted by a demo."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        try:
            intended = _apply_rule(pair["input"])
        except Exception as exc:  # diagnostic contract: never hide malformed lessons
            reasons.append(f"pair {index} cannot be solved: {exc!r}")
            continue
        if pair["output"] != intended:
            reasons.append(
                f"pair {index} output disagrees with template-group substitution"
            )

    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"demonstrations do not refute rival: {name}")
    return reasons
