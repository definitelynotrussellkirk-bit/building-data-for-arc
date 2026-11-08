"""Generator for masked submatrix extraction followed by a command rotation.

The command in the upper-left corner is interpreted exactly as the canonical
Racket authority: 1 = identity, 2 = clockwise, 3 = 180 degrees, and
4 = counter-clockwise.  Color-8 cells on the left and top headers select rows
and columns from a dense payload; their ordered Cartesian intersection is then
transformed by that command.

The sampler stays close to the tiny canonical boards while deliberately using
four selectors and gapped selector lists.  Those cases refute the strongest
public-data shortcut ("read at most the first three selectors") and a bounding-
span interpretation without changing the task's visual language.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "66a121e0d7e4"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "c03aadcd616e"
EXAMPLES_NEEDED = 7
LESSON_SCHEDULE_PERIOD = 8
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A command value at (0,0) controls an ordered extraction selected by color-8 "
    "markers: 8s in column 0 select payload rows and 8s in row 0 select payload "
    "columns.  Extract their Cartesian-intersection submatrix, then apply command "
    "1=identity, 2=rotate clockwise, 3=rotate 180, or 4=rotate counter-clockwise. "
    "The entire interior is a dense multicolor payload, not a sparse set of only "
    "the answer cells."
)

INVARIANTS = [
    "the command at (0,0) is one of 1,2,3,4 with the canonical rotation mapping",
    "only 0 and selector color 8 occur in the two headers outside the command",
    "1..4 selected payload rows and 1..4 selected payload columns preserve source order",
    "the whole interior is a dense ordinary payload and includes many distractor cells",
]

SCENE_PROFILES = {
    "c5x5": (5, 5),
    "c5x6": (5, 6),
    "c6x5": (6, 5),
    "m6x7": (6, 7),
    "m7x6": (7, 6),
    "h7x8": (7, 8),
    "h8x9": (8, 9),
    "h9x10": (9, 10),
}
_PROFILE_BY_SHAPE = {shape: name for name, shape in SCENE_PROFILES.items()}
_PROFILE_NAMES = tuple(SCENE_PROFILES)
_COMMANDS = (1, 2, 3, 4)
_SELECTOR_COUNTS = (1, 2, 3, 4)
_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "eight-step difficulty-aware schedule with exact canonical-size anchors",
        "valid": "c5x5|c5x6|c6x5|m6x7|m7x6|h7x8|h8x9|h9x10",
        "doc": "Exact observable board shape/profile.",
    },
    "cmd": {
        "type": "int",
        "default": "eight-step schedule covering all four canonical commands twice",
        "valid": "1..4",
        "doc": "Exact command at the upper-left corner.",
    },
    "n_rows": {
        "type": "int",
        "default": "eight-step teaching schedule over 1..4",
        "valid": "1..4",
        "doc": "Exact number of row selectors in column 0.",
    },
    "n_cols": {
        "type": "int",
        "default": "eight-step teaching schedule over 1..4",
        "valid": "1..4",
        "doc": "Exact number of column selectors in row 0.",
    },
}

# Every profile has at least four payload rows and four payload columns, so the
# complete advertised cross-product is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

_PROFILE_SCHEDULES = {
    None: ("c5x5", "m6x7", "c5x6", "m7x6", "c6x5", "h7x8", "h8x9", "h9x10"),
    "easy": ("c5x5", "c5x6", "c6x5", "c5x5", "c5x6", "c6x5", "c5x5", "c5x6"),
    "medium": ("c5x5", "m6x7", "c5x6", "m7x6", "c6x5", "h7x8", "m6x7", "c5x5"),
    "hard": ("c5x5", "h7x8", "c5x6", "h8x9", "c6x5", "h9x10", "h8x9", "h7x8"),
}
_COMMAND_SCHEDULE = (1, 2, 3, 4, 2, 3, 4, 1)
_SELECTOR_SCHEDULE = (
    (4, 2),
    (2, 4),
    (4, 3),
    (3, 4),
    (4, 4),
    (1, 4),
    (4, 1),
    (2, 4),
)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the hashable teaching profile used by an ordinary default draw."""
    del seed
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    slot = sample_index % LESSON_SCHEDULE_PERIOD
    profile = _PROFILE_SCHEDULES[difficulty][slot]
    command = _COMMAND_SCHEDULE[slot]
    n_rows, n_cols = _SELECTOR_SCHEDULE[slot]
    return f"{profile}|cmd{command}|rows{n_rows}|cols{n_cols}"


def _validate_call(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis: " + unknown[0])

    profile = overrides.get("scene_profile")
    if profile is not None and (type(profile) is not str or profile not in SCENE_PROFILES):
        raise ValueError(f"scene_profile must be one of {_PROFILE_NAMES}")
    for name in ("cmd", "n_rows", "n_cols"):
        value = overrides.get(name)
        if value is None:
            continue
        lo, hi = (1, 4)
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")


def _scheduled_choice(ctx, label: str, domain: tuple, target):
    """Realize a scheduled value while retaining GenCtx provenance and overrides."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, domain)
    options = list(domain)
    chosen_index = ctx.draw_rng(label).randrange(len(options))
    target_index = options.index(target)
    options[chosen_index], options[target_index] = options[target_index], options[chosen_index]
    return ctx.draw_choice(label, tuple(options))


@lru_cache(maxsize=64)
def _selector_layouts(axis_length: int, count: int):
    """Layouts include coordinate 1 and prefer a gap whenever one is possible."""
    positions = tuple(range(1, axis_length))
    layouts = [values for values in combinations(positions, count) if 1 in values]
    gapped = [values for values in layouts if values[-1] - values[0] + 1 > len(values)]
    return tuple(gapped or layouts)


def _coerce_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty sequence of rows")
    result = []
    for row in grid:
        if isinstance(row, str):
            if not row or any(char not in "0123456789" for char in row):
                raise ValueError("string rows must contain ARC digits only")
            result.append([int(char) for char in row])
        elif isinstance(row, (list, tuple)) and row:
            result.append(list(row))
        else:
            raise ValueError("each row must be a nonempty sequence or digit string")
    width = len(result[0])
    if any(len(row) != width for row in result):
        raise ValueError("grid must be rectangular")
    return result


def _selector_facts(grid):
    g = _coerce_grid(grid)
    rows = tuple(row for row in range(1, len(g)) if g[row][0] == 8)
    cols = tuple(col for col in range(1, len(g[0])) if g[0][col] == 8)
    return g, rows, cols


def _extract(grid, *, row_limit=None, col_limit=None, span=False):
    g, rows, cols = _selector_facts(grid)
    if row_limit is not None:
        rows = rows[:row_limit]
    if col_limit is not None:
        cols = cols[:col_limit]
    if span and rows and cols:
        rows = tuple(range(min(rows), max(rows) + 1))
        cols = tuple(range(min(cols), max(cols) + 1))
    if not rows or not cols:
        return [[0]]
    return [[g[row][col] for col in cols] for row in rows]


def _rotate_cw(matrix):
    return [list(row) for row in zip(*matrix[::-1])]


def _rotate_180(matrix):
    return [row[::-1] for row in matrix[::-1]]


def _rotate_ccw(matrix):
    return [list(row) for row in zip(*matrix)][::-1]


def _apply_command(matrix, command):
    matrix = [list(row) for row in matrix]
    if command == 1:
        return matrix
    if command == 2:
        return _rotate_cw(matrix)
    if command == 3:
        return _rotate_180(matrix)
    if command == 4:
        return _rotate_ccw(matrix)
    raise ValueError(f"unsupported command {command!r}")


def rule_mirror(grid):
    """Input-pure Python mirror for diagnostics; Racket remains label authority."""
    g = _coerce_grid(grid)
    return _apply_command(_extract(g), g[0][0])


def _fill_payload(grid, rng) -> None:
    """Fill every interior cell with dense ordinary data using colors 1..9."""
    palette = list(range(1, 10))
    rng.shuffle(palette)
    offset = rng.randrange(len(palette))
    width = len(grid[0])
    for index, (row, col) in enumerate(
        (row, col)
        for row in range(1, len(grid))
        for col in range(1, width)
    ):
        grid[row][col] = palette[(index + offset) % len(palette)]


def _ensure_selected_variety(grid, rows, cols) -> None:
    """Keep every multi-cell selected submatrix semantically informative."""
    cells = [(row, col) for row in rows for col in cols]
    if len(cells) <= 1 or len({grid[row][col] for row, col in cells}) >= 2:
        return
    row, col = cells[0]
    original = grid[row][col]
    grid[row][col] = 1 if original != 1 else 2


def _ensure_command_witness(grid, rows, cols, command) -> None:
    """Break accidental rotational symmetry for nontrivial generated answers."""
    if command == 1 or len(rows) * len(cols) <= 1:
        return
    if _apply_command([[grid[r][c] for c in cols] for r in rows], command) != [
        [grid[r][c] for c in cols] for r in rows
    ]:
        return
    row, col = rows[0], cols[0]
    original = grid[row][col]
    for candidate in range(1, 10):
        if candidate == original:
            continue
        grid[row][col] = candidate
        submatrix = [[grid[r][c] for c in cols] for r in rows]
        if _apply_command(submatrix, command) != submatrix:
            return
    grid[row][col] = original


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = sample_index % LESSON_SCHEDULE_PERIOD
    profile = _scheduled_choice(
        ctx,
        "scene_profile",
        _PROFILE_NAMES,
        _PROFILE_SCHEDULES[difficulty][slot],
    )
    command = _scheduled_choice(ctx, "cmd", _COMMANDS, _COMMAND_SCHEDULE[slot])
    target_rows, target_cols = _SELECTOR_SCHEDULE[slot]
    n_rows = _scheduled_choice(ctx, "n_rows", _SELECTOR_COUNTS, target_rows)
    n_cols = _scheduled_choice(ctx, "n_cols", _SELECTOR_COUNTS, target_cols)

    height, width = SCENE_PROFILES[profile]
    rows = ctx.draw_rng("selected_rows").choice(_selector_layouts(height, n_rows))
    cols = ctx.draw_rng("selected_cols").choice(_selector_layouts(width, n_cols))

    grid = full_grid(height, width, 0)
    _fill_payload(grid, ctx.draw_rng("payload"))
    grid[0][0] = command
    for row in rows:
        grid[row][0] = 8
    for col in cols:
        grid[0][col] = 8
    _ensure_selected_variety(grid, rows, cols)
    _ensure_command_witness(grid, rows, cols, command)
    return grid


def observe_overrides(grid) -> dict:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    g, rows, cols = _selector_facts(grid)
    return {
        "scene_profile": _PROFILE_BY_SHAPE[(len(g), len(g[0]))],
        "cmd": g[0][0],
        "n_rows": len(rows),
        "n_cols": len(cols),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task manifold while accepting every labeled canonical input."""
    del difficulty, meta
    try:
        g = _coerce_grid(grid)
    except ValueError as exc:
        return [str(exc)]

    errors = []
    height, width = len(g), len(g[0])
    if (height, width) not in _PROFILE_BY_SHAPE:
        errors.append(
            f"shape {height}x{width} is outside the supported canonical-like profiles"
        )
    if any(type(value) is not int or not 0 <= value <= 9 for row in g for value in row):
        return errors + ["all cells must be literal integer ARC colors 0..9"]

    command = g[0][0]
    if command not in _COMMANDS:
        errors.append("origin command must be one of 1,2,3,4")
    illegal_top = [col for col in range(1, width) if g[0][col] not in (0, 8)]
    illegal_left = [row for row in range(1, height) if g[row][0] not in (0, 8)]
    if illegal_top:
        errors.append("top header outside the command may contain only 0/8")
    if illegal_left:
        errors.append("left header outside the command may contain only 0/8")

    rows = [row for row in range(1, height) if g[row][0] == 8]
    cols = [col for col in range(1, width) if g[0][col] == 8]
    if not 1 <= len(rows) <= 4:
        errors.append(f"expected 1..4 selected rows, found {len(rows)}")
    if not 1 <= len(cols) <= 4:
        errors.append(f"expected 1..4 selected columns, found {len(cols)}")

    payload = [g[row][col] for row in range(1, height) for col in range(1, width)]
    density = sum(value != 0 for value in payload) / len(payload)
    if density < 0.75:
        errors.append(f"interior payload must be dense (>=0.75 nonzero), found {density:.3f}")
    if len(set(value for row in g for value in row)) < 8:
        errors.append("canonical-like inputs must use at least eight distinct ARC colors")

    if rows and cols:
        selected = [g[row][col] for row in rows for col in cols]
        if len(selected) > 1 and len(set(selected)) < 2:
            errors.append("selected submatrix must be nonuniform when it has multiple cells")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _rival_first_three_selectors(grid):
    """Wrong public-data shortcut: silently ignore every selector after three."""
    g = _coerce_grid(grid)
    return _apply_command(_extract(g, row_limit=3, col_limit=3), g[0][0])


def _rival_ignore_command(grid):
    """Wrong rule: extract the selected values but never rotate them."""
    return _extract(grid)


def _rival_selector_span(grid):
    """Wrong rule: crop the full min/max selector span instead of exact indices."""
    g = _coerce_grid(grid)
    return _apply_command(_extract(g, span=True), g[0][0])


SEMANTIC_RIVALS: dict[str, Callable] = {
    "first_three_selectors": _rival_first_three_selectors,
    "ignore_command": _rival_ignore_command,
    "selector_span": _rival_selector_span,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "first_three_selectors": SEMANTIC_RIVALS["first_three_selectors"],
}


def _witness_more_than_three(grid) -> bool:
    _, rows, cols = _selector_facts(grid)
    return (
        (len(rows) > 3 or len(cols) > 3)
        and rule_mirror(grid) != _rival_first_three_selectors(grid)
    )


def _witness_non_identity(grid) -> bool:
    g = _coerce_grid(grid)
    return g[0][0] != 1 and rule_mirror(g) != _rival_ignore_command(g)


def _witness_gapped(grid) -> bool:
    _, rows, cols = _selector_facts(grid)
    row_gap = bool(rows) and rows[-1] - rows[0] + 1 > len(rows)
    col_gap = bool(cols) and cols[-1] - cols[0] + 1 > len(cols)
    return (row_gap or col_gap) and rule_mirror(grid) != _rival_selector_span(grid)


SEMANTIC_WITNESSES: dict[str, Callable] = {
    "more_than_three_selectors": _witness_more_than_three,
    "non_identity_command": _witness_non_identity,
    "gapped_selectors": _witness_gapped,
}
WITNESS_RIVALS = {
    "more_than_three_selectors": ["first_three_selectors"],
    "non_identity_command": ["ignore_command"],
    "gapped_selectors": ["selector_span"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report bad labels or any named rival left able to change the query."""
    errors = []
    for index, demo in enumerate(demos):
        try:
            official = rule_mirror(demo["input"])
        except Exception as exc:
            errors.append(f"demo {index} input is invalid: {type(exc).__name__}: {exc}")
            continue
        if demo.get("output") != official:
            errors.append(f"demo {index} output does not match the intended rule")
    try:
        official_query = rule_mirror(query["input"])
    except Exception as exc:
        return errors + [f"query input is invalid: {type(exc).__name__}: {exc}"]
    if query.get("output") is not None and query.get("output") != official_query:
        errors.append("query output does not match the intended rule")

    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits = all(rival(demo["input"]) == demo.get("output") for demo in demos)
            changes_query = rival(query["input"]) != official_query
        except Exception as exc:
            errors.append(f"rival {name} failed: {type(exc).__name__}: {exc}")
            continue
        if fits and changes_query:
            errors.append(f"demos do not rule out rival operation {name}")
    return errors
