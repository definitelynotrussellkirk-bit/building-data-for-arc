"""Generator for E92 / ``c47d6176a161`` — legend-match matrix.

The top header gives one key per interior column and the left header gives one
key per interior row.  The Racket oracle preserves both headers and writes a
key into an interior cell exactly when that row key equals that column key;
all other interior cells stay background.

The generator deliberately varies header repetition, shared-key count, corner
content, dimensions, and colors while keeping those roles recoverable from the
returned grid.  Every ordinary scene contains both equal and unequal pairings,
an off-diagonal equality, and a diagonal inequality, so identity, whole-row,
whole-column, and positional-diagonal shortcuts are visibly wrong.
"""
from __future__ import annotations

from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c47d6176a161"
TASK_ID = GENERATOR_ID
VERSION = "2.0.1"  # honest axes, semantic contract, and distinct difficulty bands
RULE_HASH = "c96f5e370ca5"
SUMMARY = (
    "Preserve row 0 and column 0. For every interior (r,c), copy the left "
    "row key iff it equals the top column key; otherwise write background 0."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

GRID_SHAPES = (
    "4x4",
    "4x5",
    "4x6",
    "5x4",
    "5x5",
    "5x6",
    "6x4",
    "6x5",
    "6x6",
)
SCENE_PROFILES = (
    "unique_headers",
    "repeat_top",
    "repeat_left",
    "repeat_both",
)
CORNER_MODES = ("background", "shared_key")

AXES = {
    "grid_shape": {
        "type": "str",
        "default": "rng canonical-scale shape",
        "valid": "|".join(GRID_SHAPES),
    },
    "scene_profile": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
    "shared_colors": {
        "type": "int",
        "default": "rng 1..2",
        "valid": "1..2",
    },
    "corner_mode": {
        "type": "str",
        "default": "rng",
        "valid": "|".join(CORNER_MODES),
    },
}

# Every Cartesian combination of the four exact axes is supported.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

INVARIANTS = [
    "rectangular 4..6 by 4..6 grid with ARC colors 0..9",
    "every non-corner top/left header cell is non-background",
    "all interior input cells are background 0",
    "top and left headers share exactly one or two colors",
    "both equality and inequality comparisons are visible",
    "an off-diagonal equality and a diagonal inequality are visible",
]


def _scheduled_choice(ctx, label: str, options: tuple[str, ...], index: int) -> str:
    """Consume an override, otherwise record the deterministic schedule value."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (options[index % len(options)],))


def _difficulty_offset(difficulty) -> int:
    return {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 0)


def schedule_profile(seed, sample_index, difficulty=None):
    """Profile declaration consumed by the semantic gate's schedule census."""
    del seed
    index = int(sample_index) + _difficulty_offset(difficulty)
    return SCENE_PROFILES[index % len(SCENE_PROFILES)]


SCHEDULE_PROFILES = SCENE_PROFILES


def _header_values(
    colors: list[int],
    slots: int,
    *,
    repeated: bool,
    rng,
    fixed_prefix: tuple[int, ...] = (),
) -> list[int]:
    """Place every role color, preserve a prefix, and realize repetition exactly."""
    if repeated:
        if len(colors) != 2 or slots < 3:
            raise ValueError("repeated headers require two colors and at least three slots")
        values = list(fixed_prefix)
        for color in colors:
            if color not in values:
                values.append(color)
        while len(values) < slots:
            values.append(rng.choice(colors))
    else:
        if len(colors) != slots:
            raise ValueError("unique header color count must equal its slot count")
        values = list(fixed_prefix)
        values.extend(color for color in colors if color not in values)

    tail = values[len(fixed_prefix):]
    rng.shuffle(tail)
    return list(fixed_prefix) + tail


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    grid_shape = ctx.draw_choice("grid_shape", GRID_SHAPES)
    scene_profile = _scheduled_choice(
        ctx,
        "scene_profile",
        SCENE_PROFILES,
        int(sample_index) + _difficulty_offset(difficulty),
    )
    shared_count = ctx.draw_int("shared_colors", 1, 2)
    corner_mode = ctx.draw_choice("corner_mode", CORNER_MODES)

    h, w = (int(part) for part in grid_shape.split("x", 1))
    top_repeated = scene_profile in {"repeat_top", "repeat_both"}
    left_repeated = scene_profile in {"repeat_left", "repeat_both"}
    top_distinct = 2 if top_repeated else w - 1
    left_distinct = 2 if left_repeated else h - 1
    union_size = top_distinct + left_distinct - shared_count
    if union_size > 9:
        raise ValueError("requested header roles require more than nine nonzero ARC colors")

    rng = ctx.draw_rng("layout")
    role_colors = rng.sample(list(range(1, 10)), union_size)
    shared = role_colors[:shared_count]
    top_only = role_colors[shared_count:top_distinct]
    left_only = role_colors[top_distinct:]
    top_colors = shared + top_only
    left_colors = shared + left_only

    # Fix shared[0] at top c=1 and left r=2.  This makes an off-diagonal
    # equality unavoidable.  Put a different left key at r=1 so (1,1) is a
    # diagonal inequality; the remaining positions may shuffle freely.
    left_alt = next(color for color in left_colors if color != shared[0])
    top_values = _header_values(
        top_colors,
        w - 1,
        repeated=top_repeated,
        rng=rng,
        fixed_prefix=(shared[0],),
    )
    left_values = _header_values(
        left_colors,
        h - 1,
        repeated=left_repeated,
        rng=rng,
        fixed_prefix=(left_alt, shared[0]),
    )

    grid = full_grid(h, w, 0)
    grid[0][0] = 0 if corner_mode == "background" else shared[0]
    grid[0][1:] = top_values
    for r, color in enumerate(left_values, start=1):
        grid[r][0] = color
    return grid


def _basic_analysis(grid) -> tuple[list[str], dict[str, object]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"], {}
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular"], {}
    if not (4 <= h <= 6 and 4 <= w <= 6):
        errors.append(f"grid dimensions {h}x{w} must each be in 4..6")
    flat = [value for row in grid for value in row]
    if any(not isinstance(value, int) or not (0 <= value <= 9) for value in flat):
        errors.append("grid contains a non-integer or out-of-range ARC color")
        return errors, {}
    if any(value != 0 for row in grid[1:] for value in row[1:]):
        errors.append("interior input cells must all be background 0")

    top_values = list(grid[0][1:])
    left_values = [grid[r][0] for r in range(1, h)]
    if any(value == 0 for value in top_values):
        errors.append("every non-corner top header cell must be non-background")
    if any(value == 0 for value in left_values):
        errors.append("every non-corner left header cell must be non-background")
    top_set, left_set = set(top_values), set(left_values)
    shared = top_set & left_set
    if not shared:
        errors.append("top and left headers must share at least one key color")
    if grid[0][0] != 0 and grid[0][0] not in shared:
        errors.append("non-background corner must be a key shared by both headers")

    matches = [
        (r, c)
        for r in range(1, h)
        for c in range(1, w)
        if grid[r][0] == grid[0][c]
    ]
    mismatches = [
        (r, c)
        for r in range(1, h)
        for c in range(1, w)
        if grid[r][0] != grid[0][c]
    ]
    if not matches:
        errors.append("scene must contain at least one equality comparison")
    if not mismatches:
        errors.append("scene must contain at least one inequality comparison")
    if not any(r != c for r, c in matches):
        errors.append("scene must contain an off-diagonal equality")
    if not any(r == c for r, c in mismatches):
        errors.append("scene must contain a diagonal inequality")

    top_repeated = len(top_set) < len(top_values)
    left_repeated = len(left_set) < len(left_values)
    scene_profile = {
        (False, False): "unique_headers",
        (True, False): "repeat_top",
        (False, True): "repeat_left",
        (True, True): "repeat_both",
    }[(top_repeated, left_repeated)]
    facts: dict[str, object] = {
        "grid_shape": f"{h}x{w}",
        "scene_profile": scene_profile,
        "shared_colors": len(shared),
        "corner_mode": "background" if grid[0][0] == 0 else "shared_key",
        "matches": matches,
        "mismatches": mismatches,
        "top_values": top_values,
        "left_values": left_values,
    }
    return errors, facts


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _basic_analysis(grid)[0]


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid) -> dict[str, object]:
    errors, facts = _basic_analysis(grid)
    if errors:
        return {}
    return {axis: facts[axis] for axis in AXES}


def _solve(grid):
    """Python parity mirror used only for semantic witnesses and rivals."""
    out = [row[:] for row in grid]
    for r in range(1, len(grid)):
        for c in range(1, len(grid[0])):
            out[r][c] = grid[r][0] if grid[r][0] == grid[0][c] else 0
    return out


def _identity(grid):
    return [row[:] for row in grid]


def _row_membership(grid):
    out = [row[:] for row in grid]
    top = set(grid[0][1:])
    for r in range(1, len(grid)):
        value = grid[r][0] if grid[r][0] in top else 0
        for c in range(1, len(grid[0])):
            out[r][c] = value
    return out


def _column_membership(grid):
    out = [row[:] for row in grid]
    left = {grid[r][0] for r in range(1, len(grid))}
    for r in range(1, len(grid)):
        for c in range(1, len(grid[0])):
            out[r][c] = grid[0][c] if grid[0][c] in left else 0
    return out


def _diagonal_only(grid):
    out = [row[:] for row in grid]
    for r in range(1, len(grid)):
        for c in range(1, len(grid[0])):
            out[r][c] = grid[r][0] if r == c else 0
    return out


def _copy_left_rows(grid):
    out = [row[:] for row in grid]
    for r in range(1, len(grid)):
        for c in range(1, len(grid[0])):
            out[r][c] = grid[r][0]
    return out


def _copy_top_columns(grid):
    out = [row[:] for row in grid]
    for r in range(1, len(grid)):
        for c in range(1, len(grid[0])):
            out[r][c] = grid[0][c]
    return out


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _identity,
    "row_membership_fill": _row_membership,
    "column_membership_fill": _column_membership,
    "diagonal_only": _diagonal_only,
    "copy_left_rows": _copy_left_rows,
    "copy_top_columns": _copy_top_columns,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _has_match_and_mismatch(grid) -> bool:
    errors, facts = _basic_analysis(grid)
    return not errors and bool(facts["matches"]) and bool(facts["mismatches"])


def _shared_row_has_nonmatching_column(grid) -> bool:
    top = set(grid[0][1:])
    return any(
        grid[r][0] in top
        and any(grid[r][0] != grid[0][c] for c in range(1, len(grid[0])))
        for r in range(1, len(grid))
    )


def _shared_column_has_nonmatching_row(grid) -> bool:
    left = {grid[r][0] for r in range(1, len(grid))}
    return any(
        grid[0][c] in left
        and any(grid[r][0] != grid[0][c] for r in range(1, len(grid)))
        for c in range(1, len(grid[0]))
    )


def _off_diagonal_match(grid) -> bool:
    return any(
        r != c and grid[r][0] == grid[0][c]
        for r in range(1, len(grid))
        for c in range(1, len(grid[0]))
    )


def _repeated_top(grid) -> bool:
    values = grid[0][1:]
    return len(set(values)) < len(values)


def _repeated_left(grid) -> bool:
    values = [grid[r][0] for r in range(1, len(grid))]
    return len(set(values)) < len(values)


SEMANTIC_WITNESSES = {
    "match_and_mismatch": _has_match_and_mismatch,
    "shared_row_with_nonmatching_column": _shared_row_has_nonmatching_column,
    "shared_column_with_nonmatching_row": _shared_column_has_nonmatching_row,
    "off_diagonal_match": _off_diagonal_match,
}
WITNESS_RIVALS = {
    "match_and_mismatch": ["identity"],
    "shared_row_with_nonmatching_column": ["row_membership_fill", "copy_left_rows"],
    "shared_column_with_nonmatching_row": ["column_membership_fill", "copy_top_columns"],
    "off_diagonal_match": ["diagonal_only"],
}


def lesson_identifiable(demos, query):
    """Reject a lesson when a named plausible rival survives demos but flips query."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(
                    f"{name} fits every demonstration but disagrees on the query"
                )
    return reasons
