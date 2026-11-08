"""Generator for ARC task f45f5ca7 / content hash 1e74f9aa9324.

Each row is controlled by the value in column 0.  Codes 2, 3, 4, and 8
move to columns 2, 4, 3, and 1 respectively; a zero row becomes all zero.
Everything outside column 0 is a distractor and is erased.

The repaired distribution deliberately places all four mapping codes plus a
zero row in every input.  That makes each generated lesson identify the full
lookup table instead of allowing a query-only code to be guessed.  A four-slot
schedule anchors one canonical 10x10/no-decoy input per episode while the other
slots contain exact, observable distractor textures.
"""
from __future__ import annotations

import copy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1e74f9aa9324"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "d37150574f6e"
EXAMPLES_NEEDED = 3

_MAPPING = {2: 2, 3: 4, 4: 3, 8: 1}
_CODE_ALPHABET = (0, 2, 3, 4, 8)
_REQUIRED_COL0 = frozenset(_CODE_ALPHABET)
_TEXTURE_DECOYS_PER_ROW = {
    "no_decoys": 0,
    "one_per_row": 1,
    "two_per_row": 2,
}
HELPFUL_TEXTURES = tuple(_TEXTURE_DECOYS_PER_ROW)
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
_TEXTURE_SCHEDULE = ("no_decoys", "one_per_row", "two_per_row", "one_per_row")

SUMMARY = (
    "Read each row's code v from column 0. Move 2 to column 2, 3 to "
    "column 4, 4 to column 3, and 8 to column 1; a zero row produces an "
    "all-zero output row. All other input cells are distractors and vanish. "
    "Every generated input contains all four active codes and at least one "
    "zero row, with exact 0/1/2-distractor-per-row textures."
)

INVARIANTS = [
    "height and width are each between 5 and 30",
    "column 0 contains exactly the code alphabet {0, 2, 3, 4, 8}",
    "every active code's destination cell is blank in the input",
    "each row has the same number of nonzero distractors outside column 0: 0, 1, or 2",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "episode slot 0 is 10; otherwise difficulty-banded",
        "valid": "5..30",
    },
    "grid_w": {
        "type": "int",
        "default": "episode slot 0 is 10; otherwise difficulty-banded",
        "valid": "5..30",
    },
    "texture": {
        "type": "str",
        "default": "four-slot no_decoys/one_per_row/two_per_row/one_per_row schedule",
        "valid": "no_decoys|one_per_row|two_per_row",
    },
}

MIN_STRICT_FRAC = 0.20


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty {difficulty!r}")
    unknown = sorted(
        key for key, value in overrides.items()
        if value is not None and key not in AXES
    )
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def _draw_dimension(ctx, label: str, difficulty, sample_index: int, overrides) -> int:
    """Honor the full declared override domain while keeping useful defaults."""
    if overrides.get(label) is not None:
        return ctx.draw_int(label, 5, 30)
    if int(sample_index) % (EXAMPLES_NEEDED + 1) == 0:
        return ctx.draw_int(label, 10, 10)
    if difficulty == "easy":
        bounds = (5, 12)
    elif difficulty == "hard":
        bounds = (18, 30)
    else:
        bounds = (9, 20)
    return ctx.draw_int(label, *bounds)


def _draw_texture(ctx, sample_index: int, overrides) -> str:
    if overrides.get("texture") is not None:
        return ctx.draw_choice("texture", HELPFUL_TEXTURES)
    scheduled = _TEXTURE_SCHEDULE[int(sample_index) % len(_TEXTURE_SCHEDULE)]
    return ctx.draw_choice("texture", (scheduled,))


def _column_codes(height: int, rng) -> list[int]:
    """Return one connected active run plus a terminal zero row.

    The four authoritative branches appear once before any filler rows.  The
    filler excludes code 3 so the single-cell distractor texture remains a
    small number of connected components, matching the canonical morphology.
    """
    core = [2, 3, 4, 8]
    shift = rng.randrange(len(core))
    core = core[shift:] + core[:shift]
    if rng.randrange(2):
        core.reverse()
    filler = [rng.choice((2, 4, 8)) for _ in range(height - 5)]
    return core + filler + [0]


def _target_column(code: int) -> int | None:
    return _MAPPING.get(code)


def _draw_decoys(grid: list[list[int]], count: int, rng) -> None:
    if count == 0:
        return
    for row in grid:
        code = row[0]
        target = _target_column(code)
        if count == 1:
            columns = (3,) if target == 4 else (4,)
        else:
            # These width-5-safe patterns overlap vertically and horizontally
            # across the four core rows, avoiding pepper-noise morphology.
            columns = {
                3: (2, 3),
                4: (2, 4),
            }.get(code, (3, 4))
        for col in columns:
            palette = [color for color in range(1, 10) if color != code]
            row[col] = rng.choice(palette)


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
    height = _draw_dimension(ctx, "grid_h", difficulty, sample_index, overrides)
    width = _draw_dimension(ctx, "grid_w", difficulty, sample_index, overrides)
    texture = _draw_texture(ctx, sample_index, overrides)

    row_rng = ctx.draw_rng("row_order")
    decoy_rng = ctx.draw_rng("decoys")
    grid = full_grid(height, width, 0)
    for row_index, code in enumerate(_column_codes(height, row_rng)):
        grid[row_index][0] = code
    _draw_decoys(grid, _TEXTURE_DECOYS_PER_ROW[texture], decoy_rng)
    return grid


def _analyze(grid) -> tuple[dict, list[str]]:
    facts: dict = {}
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return facts, ["empty grid"]
    if not isinstance(grid[0], list) or not grid[0]:
        return facts, ["empty row"]
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return facts, ["ragged grid"]
    facts.update(grid_h=height, grid_w=width)
    if not (5 <= height <= 30):
        errors.append(f"grid height {height} outside 5..30")
    if not (5 <= width <= 30):
        errors.append(f"grid width {width} outside 5..30")

    bad_cells = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
    ]
    if bad_cells:
        errors.append(f"non-ARC cell values: {bad_cells[:4]}")
        return facts, errors

    col0 = [row[0] for row in grid]
    facts["column0_codes"] = sorted(set(col0))
    invalid_codes = sorted(set(col0) - _REQUIRED_COL0)
    if invalid_codes:
        errors.append(f"column 0 has unsupported code(s) {invalid_codes}")
    missing_codes = sorted(_REQUIRED_COL0 - set(col0))
    if missing_codes:
        errors.append(f"column 0 omits required code(s) {missing_codes}")

    leakage = []
    decoy_counts = []
    for row_index, row in enumerate(grid):
        target = _target_column(row[0])
        if target is not None and target < width and row[target] != 0:
            leakage.append((row_index, row[0], target, row[target]))
        decoy_counts.append(sum(value != 0 for value in row[1:]))
    if leakage:
        errors.append(
            "destination cells must be blank before transformation; "
            f"found {leakage[:4]}"
        )

    unique_counts = sorted(set(decoy_counts))
    if len(unique_counts) != 1 or unique_counts[0] not in (0, 1, 2):
        errors.append(
            "rows must have one exact shared distractor count in {0,1,2}; "
            f"observed {unique_counts}"
        )
    else:
        count = unique_counts[0]
        facts["texture"] = next(
            name for name, value in _TEXTURE_DECOYS_PER_ROW.items() if value == count
        )
        facts["decoys_per_row"] = count
    facts["all_targets_blank"] = not leakage
    return facts, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    facts, errors = _analyze(grid)
    if errors:
        return errors
    requested = {}
    if isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if not isinstance(requested, dict):
            requested = {}
    for axis in AXES:
        value = requested.get(axis)
        if value is not None and facts.get(axis) != value:
            errors.append(f"{axis} requested {value!r}, realized {facts.get(axis)!r}")
    return errors


def observe_overrides(grid) -> dict:
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {axis: facts[axis] for axis in AXES}


def strict_canonical_like(grid) -> list[str]:
    facts, errors = _analyze(grid)
    if errors:
        return errors
    reasons = []
    if (facts["grid_h"], facts["grid_w"]) != (10, 10):
        reasons.append("canonical inputs are 10x10")
    if facts["texture"] != "no_decoys":
        reasons.append("canonical inputs have no cells outside column 0")
    return reasons


def _has_code(code: int):
    def predicate(grid) -> bool:
        facts, errors = _analyze(grid)
        return not errors and code in facts["column0_codes"]
    return predicate


def _has_decoys(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and facts["decoys_per_row"] > 0


def _has_no_decoys(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and facts["decoys_per_row"] == 0


def _targets_start_blank(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and facts["all_targets_blank"]


SEMANTIC_WITNESSES = {
    "zero_row_branch": _has_code(0),
    "code_2_to_col_2": _has_code(2),
    "code_3_to_col_4": _has_code(3),
    "code_4_to_col_3": _has_code(4),
    "code_8_to_col_1": _has_code(8),
    "canonical_no_decoys": _has_no_decoys,
    "distractors_are_erased": _has_decoys,
    "destinations_start_blank": _targets_start_blank,
}


def rule_mirror(grid) -> list[list[int]]:
    """Independent test mirror; the canonical Racket rule remains authority."""
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    for row_index, row in enumerate(grid):
        target = _target_column(row[0])
        if target is not None and target < width:
            output[row_index][target] = row[0]
    return output


def _rival_keep_column_zero(grid):
    output = full_grid(len(grid), len(grid[0]), 0)
    for row_index, row in enumerate(grid):
        output[row_index][0] = row[0]
    return output


def _rival_fixed_column(grid, column: int):
    output = full_grid(len(grid), len(grid[0]), 0)
    for row_index, row in enumerate(grid):
        if row[0] and column < len(row):
            output[row_index][column] = row[0]
    return output


def _rival_numeric_column(grid):
    output = full_grid(len(grid), len(grid[0]), 0)
    for row_index, row in enumerate(grid):
        code = row[0]
        if code and code < len(row):
            output[row_index][code] = code
    return output


def _rival_erase_decoys_only(grid):
    return [
        [row[0]] + [0] * (len(row) - 1)
        for row in grid
    ]


_RIVALS = {
    "keep_column_zero": _rival_keep_column_zero,
    "all_codes_to_column_1": lambda grid: _rival_fixed_column(grid, 1),
    "all_codes_to_column_2": lambda grid: _rival_fixed_column(grid, 2),
    "numeric_color_column": _rival_numeric_column,
    "erase_decoys_only": _rival_erase_decoys_only,
    "identity": lambda grid: copy.deepcopy(grid),
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons that leave a named shortcut with another query answer."""
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    episodes = list(demos) + [query]
    labels = [f"demo {index}" for index in range(len(demos))] + ["query"]
    for label, episode in zip(labels, episodes):
        if not isinstance(episode, dict) or "input" not in episode:
            reasons.append(f"{label} lacks input")
            continue
        errors = self_check(episode["input"])
        if errors:
            reasons.append(f"{label} input is outside teaching grammar: {'; '.join(errors)}")
            continue
        expected = rule_mirror(episode["input"])
        if episode.get("output") is not None and episode.get("output") != expected:
            reasons.append(f"{label} output does not match the lookup rule")
    if reasons:
        return reasons

    demonstrated = {
        code
        for demo in demos
        for code in set(row[0] for row in demo["input"])
    }
    missing = sorted(_REQUIRED_COL0 - demonstrated)
    if missing:
        reasons.append(f"demonstrations omit required lookup/zero code(s) {missing}")

    if not any(
        any(value != 0 for value in row[1:])
        for demo in demos
        for row in demo["input"]
    ):
        reasons.append("demonstrations never show that non-column-0 distractors vanish")

    truth = rule_mirror(query["input"])
    for name, rival in _RIVALS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            if rival(query["input"]) != truth:
                reasons.append(
                    f"competing rule {name!r} fits every demo but changes the query answer"
                )
    return reasons
