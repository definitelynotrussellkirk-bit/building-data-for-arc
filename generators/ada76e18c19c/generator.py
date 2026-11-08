"""Generator for ada76e18c19c — fill exact same-color row pairs.

The selected rule is deliberately count-sensitive: in each row, fill the span
between the endpoints only when that row contains exactly two nonzero cells and
both cells have the same color.  Rows with mismatched endpoints, three copies
of one color, or a third-color blocker are unchanged.

Default dimensions cycle the five official input profiles.  A separate
three-step teaching schedule rotates one lawful counterexample row through
those profiles so every three-demo lesson refutes the most plausible shortcuts
without changing the official height/width/palette signature.
"""
from __future__ import annotations

from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ada76e18c19c"
TASK_ID = "ada76e18c19c"
VERSION = "3.0.0"
RULE_HASH = "714e73d2362f"

SUMMARY = (
    "On a black grid, inspect each row independently.  If and only if the row "
    "contains exactly two nonzero cells and those two cells have the same "
    "color, fill every cell between them, inclusive, with that color.  Leave "
    "mismatched pairs, rows with extra nonzero cells, and all other rows "
    "unchanged."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the grid uses ARC colors 0..9 on a black background",
    "exactly three rows contain a qualifying same-color endpoint pair",
    "qualifying endpoint colors are three distinct nonzero colors",
    "each qualifying endpoint gap is at least three columns",
    "at most one lawful negative-witness row is added by the teaching schedule",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "sample_index cycles official heights 7,8,6,9,8",
        "valid": "6..9",
    },
    "grid_w": {
        "type": "int",
        "default": "sample_index cycles official widths 10,9,11,12,10",
        "valid": "9..12",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_CANONICAL_DIMENSIONS = (
    (7, 10),
    (8, 9),
    (6, 11),
    (9, 12),
    (8, 10),
)
_CANONICAL_PROFILES = frozenset((h, w, 4) for h, w in _CANONICAL_DIMENSIONS)

SCHEDULE_PROFILES = (
    "mismatched_pair",
    "extra_same_color",
    "blocked_pair",
)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the replayable three-step semantic teaching profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must have at least one column"]
    width = len(grid[0])
    errors: list[str] = []
    for index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {index} is not rectangular width {width}")
            continue
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int):
                errors.append("grid values must be integer ARC colors 0..9")
                return errors
            if not 0 <= value <= 9:
                errors.append("grid values must be integer ARC colors 0..9")
                return errors
    return errors


def _row_kind(row: list[int] | tuple[int, ...]) -> tuple[str, int | None]:
    """Classify a row in the narrow authoritative teaching grammar."""
    cells = [(column, value) for column, value in enumerate(row) if value != 0]
    if not cells:
        return "blank", None

    first_column = cells[0][0]
    last_column = cells[-1][0]
    if last_column - first_column < 3:
        return "invalid_short_span", None

    values = [value for _, value in cells]
    if len(cells) == 2:
        if values[0] == values[1]:
            return "qualifying", values[0]
        return "mismatched_pair", None

    if len(cells) == 3:
        if len(set(values)) == 1:
            return "extra_same_color", values[0]
        if values[0] == values[-1] and values[1] != values[0]:
            return "blocked_pair", values[0]

    return "invalid_nonzero_pattern", None


def semantic_profile(grid) -> dict[str, object]:
    """Expose row-grammar evidence for audits and future reviewers."""
    errors = _grid_errors(grid)
    if errors:
        return {"valid": False, "errors": errors}
    kinds = [_row_kind(row)[0] for row in grid]
    return {
        "valid": not any(kind.startswith("invalid_") for kind in kinds),
        "height": len(grid),
        "width": len(grid[0]),
        "palette_size": len({value for row in grid for value in row}),
        "qualifying_rows": kinds.count("qualifying"),
        "witness_rows": {
            name: kinds.count(name)
            for name in SCHEDULE_PROFILES
        },
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical inputs and reject rule-ambiguous near misses."""
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors

    h, w = len(grid), len(grid[0])
    if not 6 <= h <= 9:
        errors.append(f"height {h} outside honest generator envelope 6..9")
    if not 9 <= w <= 12:
        errors.append(f"width {w} outside honest generator envelope 9..12")

    palette = {value for row in grid for value in row}
    if 0 not in palette:
        errors.append("scene has no black background cells")
    nonzero_palette = palette - {0}
    if len(nonzero_palette) != 3:
        errors.append(
            f"expected exactly three nonzero colors, found {len(nonzero_palette)}"
        )

    qualifying_colors: list[int] = []
    witness_rows: list[str] = []
    for index, row in enumerate(grid):
        kind, color = _row_kind(row)
        if kind == "qualifying":
            assert color is not None
            qualifying_colors.append(color)
        elif kind == "blank":
            continue
        elif kind in SCHEDULE_PROFILES:
            witness_rows.append(kind)
        else:
            errors.append(f"row {index} violates row grammar: {kind}")

    if len(qualifying_colors) != 3:
        errors.append(
            f"expected exactly three qualifying rows, found {len(qualifying_colors)}"
        )
    if len(set(qualifying_colors)) != len(qualifying_colors):
        errors.append("qualifying rows must use distinct endpoint colors")
    if len(witness_rows) > 1:
        errors.append(f"expected at most one witness row, found {len(witness_rows)}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the five official height/width/palette profiles exactly."""
    errors = self_check(grid)
    if errors:
        return errors
    signature = (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )
    if signature not in _CANONICAL_PROFILES:
        return [f"profile {signature} is outside the five official input profiles"]
    return []


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror of the selected canonical Racket rule."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("rule_mirror expects a rectangular ARC grid")

    out = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        cells = [(column, value) for column, value in enumerate(row) if value != 0]
        if len(cells) != 2 or cells[0][1] != cells[1][1]:
            continue
        left, color = cells[0]
        right = cells[1][0]
        for column in range(left, right + 1):
            out[row_index][column] = color
    return out


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the returned grid."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def _copy_grid(grid):
    return [list(row) for row in grid]


def _shortcut_fill_any_pair(grid):
    """Wrong rule: any two nonzero endpoints qualify, regardless of color."""
    out = _copy_grid(grid)
    for row_index, row in enumerate(grid):
        cells = [(column, value) for column, value in enumerate(row) if value != 0]
        if len(cells) != 2:
            continue
        left, color = cells[0]
        right = cells[1][0]
        for column in range(left, right + 1):
            out[row_index][column] = color
    return out


def _shortcut_ignore_exact_count(grid):
    """Wrong rule: one repeated row color qualifies even when it occurs 3+ times."""
    out = _copy_grid(grid)
    for row_index, row in enumerate(grid):
        cells = [(column, value) for column, value in enumerate(row) if value != 0]
        values = {value for _, value in cells}
        if len(cells) < 2 or len(values) != 1:
            continue
        color = cells[0][1]
        for column in range(cells[0][0], cells[-1][0] + 1):
            out[row_index][column] = color
    return out


def _shortcut_ignore_blockers(grid):
    """Wrong rule: a color appearing exactly twice qualifies despite blockers."""
    out = _copy_grid(grid)
    for row_index, row in enumerate(grid):
        by_color: dict[int, list[int]] = {}
        for column, value in enumerate(row):
            if value != 0:
                by_color.setdefault(value, []).append(column)
        for color, columns in sorted(by_color.items()):
            if len(columns) != 2:
                continue
            for column in range(columns[0], columns[1] + 1):
                out[row_index][column] = color
    return out


def _identity(grid):
    return _copy_grid(grid)


def _has_row_kind(grid, wanted: str) -> bool:
    return not _grid_errors(grid) and any(
        _row_kind(row)[0] == wanted for row in grid
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "mismatched_pair": lambda grid: _has_row_kind(grid, "mismatched_pair"),
    "extra_same_color": lambda grid: _has_row_kind(grid, "extra_same_color"),
    "blocked_pair": lambda grid: _has_row_kind(grid, "blocked_pair"),
}
BRANCH_WITNESSES = tuple(SEMANTIC_WITNESSES)

SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "fill_any_pair": _shortcut_fill_any_pair,
    "ignore_exact_count": _shortcut_ignore_exact_count,
    "ignore_blockers": _shortcut_ignore_blockers,
    "identity": _identity,
}
WITNESS_RIVALS = {
    "mismatched_pair": ["fill_any_pair"],
    "extra_same_color": ["ignore_exact_count"],
    "blocked_pair": ["ignore_blockers"],
}

# All three shortcuts reproduce every public train/test pair.  The generated
# witness schedule is therefore responsible for falsifying them.
CANONICAL_SHORTCUTS = {
    "fill_any_pair": _shortcut_fill_any_pair,
    "ignore_exact_count": _shortcut_ignore_exact_count,
    "ignore_blockers": _shortcut_ignore_blockers,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named rival fits all demos but changes the query."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]

    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} is missing input/output")
            continue
        structural = strict_canonical_like(pair["input"])
        if structural:
            reasons.append(f"{role} input is not lawful: {structural[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{role} output disagrees with the exact-pair row rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} matches every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures():
    """Task-linked malformed near misses that self_check must reject."""
    blank = full_grid(6, 9, 0)

    only_two_pairs = full_grid(6, 9, 0)
    only_two_pairs[0][0] = only_two_pairs[0][4] = 2
    only_two_pairs[2][1] = only_two_pairs[2][7] = 3
    only_two_pairs[4][2] = 4

    short_span = full_grid(6, 9, 0)
    short_span[0][0] = short_span[0][2] = 2
    short_span[2][0] = short_span[2][4] = 3
    short_span[4][1] = short_span[4][7] = 4

    repeated_active_color = full_grid(6, 9, 0)
    repeated_active_color[0][0] = repeated_active_color[0][4] = 2
    repeated_active_color[2][1] = repeated_active_color[2][7] = 2
    repeated_active_color[4][2] = repeated_active_color[4][8] = 3

    four_nonzeros = full_grid(6, 9, 0)
    four_nonzeros[0][0] = four_nonzeros[0][4] = 2
    four_nonzeros[2][1] = four_nonzeros[2][7] = 3
    four_nonzeros[4][0] = four_nonzeros[4][3] = 4
    four_nonzeros[5][0] = four_nonzeros[5][2] = 4
    four_nonzeros[5][4] = four_nonzeros[5][8] = 4

    ragged = [[0, 2, 0, 0, 2], [0, 0, 0, 0]]

    return [
        ("blank_grid", blank),
        ("only_two_qualifying_rows", only_two_pairs),
        ("short_endpoint_gap", short_span),
        ("repeated_active_color", repeated_active_color),
        ("four_nonzero_row", four_nonzeros),
        ("ragged_grid", ragged),
    ]


def _draw_exact_int(ctx, label: str, default: int, lo: int, hi: int) -> int:
    """Record a keyed draw while preserving deterministic scheduled defaults."""
    if ctx.overrides.get(label) is None:
        ctx.overrides[label] = default
    return ctx.draw_int(label, lo, hi)


def _random_span(rng, width: int, *, minimum_gap: int = 3) -> tuple[int, int]:
    gap = rng.randint(minimum_gap, width - 1)
    left = rng.randint(0, width - gap - 1)
    return left, left + gap


def _other_endpoint(rng, width: int, anchor: int) -> int:
    choices = [column for column in range(width) if abs(column - anchor) >= 3]
    if not choices:
        raise ValueError("internal span construction has no legal second endpoint")
    return rng.choice(choices)


def _paint_pair(grid, row: int, color: int, left: int, right: int) -> None:
    grid[row][left] = color
    grid[row][right] = color


def _teaching_scene(height: int, width: int, profile: str, rng) -> list[list[int]]:
    """Build three positive rows plus one morphology-neutral counterexample."""
    grid = full_grid(height, width, 0)
    top = rng.randint(0, height - 4)
    row_a, witness_row, row_b, row_c = range(top, top + 4)
    color_a, color_b, color_c = rng.sample(list(range(1, 10)), 3)

    left_a, right_a = _random_span(rng, width, minimum_gap=4)
    _paint_pair(grid, row_a, color_a, left_a, right_a)

    if profile == "mismatched_pair":
        other_b = _other_endpoint(rng, width, right_a)
        _paint_pair(grid, row_b, color_b, min(right_a, other_b), max(right_a, other_b))
        grid[witness_row][left_a] = color_a
        grid[witness_row][right_a] = color_b
    elif profile == "extra_same_color":
        left_b, right_b = _random_span(rng, width)
        _paint_pair(grid, row_b, color_b, left_b, right_b)
        grid[witness_row][left_a] = color_a
        grid[witness_row][left_a + 1] = color_a
        grid[witness_row][right_a] = color_a
    elif profile == "blocked_pair":
        blocker = rng.randint(left_a + 1, right_a - 1)
        other_b = _other_endpoint(rng, width, blocker)
        _paint_pair(grid, row_b, color_b, min(blocker, other_b), max(blocker, other_b))
        grid[witness_row][left_a] = color_a
        grid[witness_row][blocker] = color_b
        grid[witness_row][right_a] = color_a
    else:
        raise ValueError(f"unknown internal schedule profile {profile!r}")

    left_c, right_c = _random_span(rng, width)
    _paint_pair(grid, row_c, color_c, left_c, right_c)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override key(s): " + ", ".join(unknown))
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty {difficulty!r}")

    default_h, default_w = _CANONICAL_DIMENSIONS[
        sample_index % len(_CANONICAL_DIMENSIONS)
    ]
    profile = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=dict(overrides),
    )
    height = _draw_exact_int(ctx, "grid_h", default_h, 6, 9)
    width = _draw_exact_int(ctx, "grid_w", default_w, 9, 12)
    band = difficulty if difficulty is not None else "default"
    rng = ctx.draw_rng(f"layout:{band}:{profile}")
    grid = _teaching_scene(height, width, profile, rng)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("internal teaching scene failed: " + "; ".join(errors))
    return grid
