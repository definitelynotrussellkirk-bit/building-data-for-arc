"""Generator for f8b9516df05e: cast rightward rays until the first gray blocker.

Each active row starts with one colored emitter followed by an empty gap and at
least one gray (8) blocker.  The selected rule paints the gap in the emitter's
color and stops at the *first* rightward blocker.  Generated teaching scenes
always include a later gray blocker so that the canonical-fitting "stop at the
last blocker" shortcut is visibly wrong.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f8b9516df05e"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "d469cd5280c8"

SUMMARY = (
    "A 0-background grid has 3..6 active rows.  In each active row, the "
    "leftmost nonzero/non-gray cell is a colored emitter and the first gray "
    "cell to its right is a blocker, with at least one empty cell between "
    "them.  Fill exactly those cells between emitter and first blocker with "
    "the emitter color.  Preserve the blocker and everything after it."
)

INVARIANTS = [
    "background is 0",
    "gray 8 is the blocker color",
    "the first nonzero cell of every active row is a non-gray emitter",
    "every active row has a visible empty gap before its first rightward blocker",
    "the selected rule preserves every cell after the first rightward blocker",
]

EMITTER_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)

# Only independently controllable, pixel-observable axes are public.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile weighted, with full 8..14 support",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile weighted, with full 9..17 support",
        "valid": "9..17",
    },
    "rays": {
        "type": "int",
        "default": "canonical-profile weighted, with full 3..6 support",
        "valid": "3..6",
    },
}

# Every advertised exact combination is constructive in every difficulty band.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, int]] = []

_CANONICAL_PROFILES = (
    (8, 10, 3),
    (9, 11, 4),
    (8, 9, 3),
    (10, 10, 3),
    (9, 10, 3),
)
_BAND_OFFSET = {None: 0, "easy": 0, "medium": 2, "hard": 4}


def _validate_request(difficulty, overrides: dict) -> None:
    if difficulty not in _BAND_OFFSET:
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis: {', '.join(unknown)}")
    bounds = {"grid_h": (8, 14), "grid_w": (9, 17), "rays": (3, 6)}
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"override {name!r} must be an integer (not bool)")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(
                f"override {name!r}={value} outside advertised range [{lo}, {hi}]"
            )


def _weighted_options(lo: int, hi: int, preferred: int) -> tuple[int, ...]:
    """Keep the complete public domain while strongly anchoring real profiles."""
    return (preferred,) * 128 + tuple(range(lo, hi + 1))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    offset = _BAND_OFFSET[difficulty]
    preferred_h, preferred_w, preferred_rays = _CANONICAL_PROFILES[
        (sample_index + offset) % len(_CANONICAL_PROFILES)
    ]
    h = ctx.draw_choice("grid_h", _weighted_options(8, 14, preferred_h))
    w = ctx.draw_choice("grid_w", _weighted_options(9, 17, preferred_w))
    rays = ctx.draw_choice("rays", _weighted_options(3, 6, preferred_rays))

    layout_rng = ctx.draw_rng("layout")
    color_rng = ctx.draw_rng("emitter-colors")
    rows = layout_rng.sample(range(h), rays)
    colors = color_rng.sample(list(EMITTER_COLORS), rays)
    grid = full_grid(h, w, 0)

    # A decisive teaching row.  The later blocker and the preserved colored
    # decoy make "fill until the last blocker" disagree with the selected rule.
    witness_row = rows[0]
    witness_color = colors[0]
    emitter_column = layout_rng.randint(0, w - 6)
    first_blocker = layout_rng.randint(emitter_column + 2, w - 4)
    second_blocker = layout_rng.randint(first_blocker + 3, w - 1)
    grid[witness_row][emitter_column] = witness_color
    grid[witness_row][first_blocker] = 8
    grid[witness_row][first_blocker + 1] = colors[1]
    grid[witness_row][second_blocker] = 8

    # Remaining rows stay close to the canonical grammar: one emitter, one
    # rightward blocker, and an empty visible ray path.
    for row, color in zip(rows[1:], colors[1:]):
        emitter_column = layout_rng.randint(0, w - 3)
        blocker_column = layout_rng.randint(emitter_column + 2, w - 1)
        grid[row][emitter_column] = color
        grid[row][blocker_column] = 8

    return grid


def _first_emitter(row: Iterable[int]):
    for column, value in enumerate(row):
        if value not in (0, 8):
            return column, value
    return None


def _rightward_blockers(row: Iterable[int], emitter_column: int) -> list[int]:
    values = list(row)
    return [
        column
        for column in range(emitter_column + 1, len(values))
        if values[column] == 8
    ]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure-Python mirror of the selected Racket first-blocker rule."""
    output = deepcopy(grid)
    for row_index, row in enumerate(grid):
        emitter = _first_emitter(row)
        if emitter is None:
            continue
        emitter_column, color = emitter
        blockers = _rightward_blockers(row, emitter_column)
        if not blockers:
            continue
        for column in range(emitter_column + 1, blockers[0]):
            output[row_index][column] = color
    return output


def observe_overrides(grid) -> dict[str, int]:
    """Recover all public exact axes from the returned pixels."""
    active = 0
    for row in grid:
        emitter = _first_emitter(row)
        if emitter is None:
            continue
        if _rightward_blockers(row, emitter[0]):
            active += 1
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "rays": active}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the lawful task grammar, including all canonical inputs."""
    del difficulty, meta
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["grid must be a nonempty rectangular sequence"]
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width for row in grid
    ):
        return ["grid must be rectangular"]
    height = len(grid)
    errors: list[str] = []
    if not 8 <= height <= 14 or not 9 <= width <= 17:
        errors.append(f"grid dimensions {height}x{width} outside 8..14 by 9..17")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
        return errors

    active = 0
    for row_index, row in enumerate(grid):
        nonzero = [column for column, value in enumerate(row) if value != 0]
        if not nonzero:
            continue
        first = nonzero[0]
        if row[first] == 8:
            errors.append(f"row {row_index}: first nonzero cell must be an emitter")
            continue
        active += 1
        blockers = _rightward_blockers(row, first)
        if not blockers:
            errors.append(f"row {row_index}: emitter has no rightward gray blocker")
            continue
        blocker = blockers[0]
        if blocker - first < 2:
            errors.append(f"row {row_index}: emitter and blocker need a visible gap")
            continue
        if any(row[column] != 0 for column in range(first + 1, blocker)):
            errors.append(f"row {row_index}: cells before first blocker must be empty")

    if not 3 <= active <= 6:
        errors.append(f"expected 3..6 active ray rows, found {active}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Lawful first-blocker scenes in the declared generator manifold."""
    return self_check(grid)


def _last_blocker_rival(grid: list[list[int]]) -> list[list[int]]:
    """Plausible shortcut: continue through gaps until the last gray blocker."""
    output = deepcopy(grid)
    for row_index, row in enumerate(grid):
        emitter = _first_emitter(row)
        if emitter is None:
            continue
        emitter_column, color = emitter
        blockers = _rightward_blockers(row, emitter_column)
        if not blockers:
            continue
        for column in range(emitter_column + 1, blockers[-1]):
            if output[row_index][column] == 0:
                output[row_index][column] = color
    return output


def _has_multiple_right_blockers(grid) -> bool:
    if self_check(grid):
        return False
    for row in grid:
        emitter = _first_emitter(row)
        if emitter is not None and len(_rightward_blockers(row, emitter[0])) >= 2:
            if _last_blocker_rival(grid) != rule_mirror(grid):
                return True
    return False


def lesson_identifiable(demos, query) -> list[str]:
    """Require lawful labels and a demonstration that refutes every rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    errors: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demo {index} must contain input and output grids")
            continue
        structural = strict_canonical_like(pair["input"])
        if structural:
            errors.append(f"demo {index} is not lawful: {structural[0]}")
        elif rule_mirror(pair["input"]) != pair["output"]:
            errors.append(f"demo {index} output disagrees with the selected rule")

    query_errors = strict_canonical_like(query["input"])
    if query_errors:
        errors.append(f"query is not lawful: {query_errors[0]}")
    elif rule_mirror(query["input"]) != query["output"]:
        errors.append("query output disagrees with the selected rule")
    if errors:
        return errors

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            errors.append(f"competitor {name!r} still fits every demonstration")
    return errors


EXAMPLES_NEEDED = 3
SEMANTIC_WITNESSES = {"first_blocker_stop": _has_multiple_right_blockers}
SEMANTIC_RIVALS = {"last_blocker_stop": _last_blocker_rival}
WITNESS_RIVALS = {"first_blocker_stop": ["last_blocker_stop"]}
CANONICAL_SHORTCUTS = {"last_blocker_stop": _last_blocker_rival}
LESSON_COMPETITORS = {"last_blocker_stop": _last_blocker_rival}
