"""Generator for ARC task 135219aecdb4 (source slug 4cd1b7b2).

The input is a 4x4 Latin square over symbols 1..4 with 1..10 cells erased to
0.  One synchronous pass fills every zero whose row and column jointly leave
exactly one candidate.  The canonical rule applies that pass three times.

The ordinary lesson schedule cycles through three semantically distinct mask
profiles on consecutive sample indices: one-pass completion, a true three-pass
cascade, and a case with a cell that requires combining row and column
constraints.  Every three-demo lesson therefore exposes the full iteration
budget and the joint row/column rule instead of only showing easy isolated holes.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from typing import Iterable

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "135219aecdb4"
TASK_ID = GENERATOR_ID
RULE_HASH = "8036db043882"  # sha256[:12] of whitespace-normalized canonical rule
VERSION = "2.1.1"  # strict exact axis + explicit three-pass/joint witnesses
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Complete a 4x4 partial Latin square over symbols 1..4. Replace each 0 "
    "whose row and column jointly leave one possible symbol, synchronously, "
    "and repeat for three passes. Generated lessons include one-pass, "
    "three-pass, and joint-row/column examples."
)

INVARIANTS = [
    "input is exactly 4x4 and uses only integer colors 0..4",
    "there are 1..10 erased cells (0)",
    "non-zero cells are a valid partial Latin square",
    "three synchronous elimination passes fill every erased cell",
    "the completed grid has each row and column equal to {1,2,3,4}",
]

# Only an exact value recoverable from the returned grid is exposed as a
# caller-facing axis.  Earlier versions declared seven nuisance/internal knobs
# (including two unused booleans and a degenerate texture alias) that could not
# be inferred from the grid and silently ignored conflicting overrides.
AXES = {
    "n_erased": {
        "type": "int",
        "default": "5 easy, 6 medium, 7 hard; 5..7 when difficulty is unset",
        "valid": "1..10",
    },
}

_PROFILE_NAMES = ("one_pass", "three_pass_cascade", "joint_constraints")
SCHEDULE_PROFILES = _PROFILE_NAMES

# Two non-isotopic 4x4 Latin-square templates (Klein-four and cyclic classes).
# Row, column, and symbol permutations then cover a broad family while keeping
# mask semantics exactly transportable.
_LATIN_BASES = (
    (
        (1, 2, 3, 4),
        (3, 4, 1, 2),
        (4, 3, 2, 1),
        (2, 1, 4, 3),
    ),
    (
        (1, 4, 2, 3),
        (4, 1, 3, 2),
        (2, 3, 4, 1),
        (3, 2, 1, 4),
    ),
)

_SYMBOLS = (1, 2, 3, 4)
_ALL_CELLS = tuple(range(16))


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the deterministic three-slot teaching cadence to the gate."""
    del seed, difficulty
    return _PROFILE_NAMES[int(sample_index) % len(_PROFILE_NAMES)]


def _fill_pass(grid):
    """One synchronous row/column single-candidate fill pass."""
    out = [list(row) for row in grid]
    for row in range(4):
        for col in range(4):
            if grid[row][col] != 0:
                continue
            row_values = {
                grid[row][other_col]
                for other_col in range(4)
                if grid[row][other_col] != 0
            }
            col_values = {
                grid[other_row][col]
                for other_row in range(4)
                if grid[other_row][col] != 0
            }
            candidates = [
                value
                for value in _SYMBOLS
                if value not in row_values and value not in col_values
            ]
            if len(candidates) == 1:
                out[row][col] = candidates[0]
    return out


def _solve(grid):
    """Mirror the canonical three-pass rule exactly."""
    out = [list(row) for row in grid]
    for _ in range(3):
        out = _fill_pass(out)
    return out


def _passes_to_complete(grid) -> int | None:
    out = [list(row) for row in grid]
    for pass_index in range(1, 4):
        out = _fill_pass(out)
        if all(value != 0 for row in out for value in row):
            return pass_index
    return None


def _joint_forced_cells(grid) -> tuple[tuple[int, int], ...]:
    """Zeros uniquely forced by row+column, but by neither one alone."""
    cells: list[tuple[int, int]] = []
    for row in range(4):
        for col in range(4):
            if grid[row][col] != 0:
                continue
            row_values = {
                grid[row][other_col]
                for other_col in range(4)
                if grid[row][other_col] != 0
            }
            col_values = {
                grid[other_row][col]
                for other_row in range(4)
                if grid[other_row][col] != 0
            }
            row_candidates = [value for value in _SYMBOLS if value not in row_values]
            col_candidates = [value for value in _SYMBOLS if value not in col_values]
            joint_candidates = [
                value
                for value in _SYMBOLS
                if value not in row_values and value not in col_values
            ]
            if (
                len(joint_candidates) == 1
                and len(row_candidates) > 1
                and len(col_candidates) > 1
            ):
                cells.append((row, col))
    return tuple(cells)


def _is_complete_latin(grid) -> bool:
    wanted = set(_SYMBOLS)
    return (
        len(grid) == 4
        and all(len(row) == 4 for row in grid)
        and all(set(row) == wanted for row in grid)
        and all({grid[row][col] for row in range(4)} == wanted for col in range(4))
    )


def _mask_grid(base_index: int, mask: Iterable[int]):
    grid = [list(row) for row in _LATIN_BASES[base_index]]
    for cell in mask:
        row, col = divmod(cell, 4)
        grid[row][col] = 0
    return grid


def _mask_profile_matches(base_index: int, mask: tuple[int, ...], profile: str) -> bool:
    grid = _mask_grid(base_index, mask)
    solved = _solve(grid)
    if not _is_complete_latin(solved):
        return False
    missing_symbols = {solved[cell // 4][cell % 4] for cell in mask}
    passes = _passes_to_complete(grid)
    if profile == "any":
        return True
    if profile == "one_pass":
        return len(missing_symbols) >= 3 and passes == 1
    if profile in ("cascade", "three_pass_cascade"):
        # A two-pass example only refutes the single-pass shortcut.  Requiring
        # all three passes makes the canonical iteration budget identifiable.
        return passes == 3
    if profile == "joint_constraints":
        return len(missing_symbols) >= 3 and bool(_joint_forced_cells(grid))
    raise ValueError(f"unknown internal profile {profile!r}")


@lru_cache(maxsize=None)
def _candidate_masks(base_index: int, n_erased: int, profile: str):
    """All exact-size masks satisfying one teaching profile on one base."""
    return tuple(
        mask
        for mask in combinations(_ALL_CELLS, n_erased)
        if _mask_profile_matches(base_index, mask, profile)
    )


def _transport_mask(mask, row_order, col_order):
    """Move a base-coordinate mask through row/column permutations."""
    inverse_rows = {old: new for new, old in enumerate(row_order)}
    inverse_cols = {old: new for new, old in enumerate(col_order)}
    return tuple(
        4 * inverse_rows[cell // 4] + inverse_cols[cell % 4]
        for cell in mask
    )


def _draw_n_erased(ctx, difficulty, overrides) -> int:
    if "n_erased" in overrides and overrides["n_erased"] is not None:
        return ctx.draw_int("n_erased", 1, 10)
    scheduled = {
        "easy": 5,
        "medium": 6,
        "hard": 7,
    }.get(difficulty, 5 + (int(ctx.sample_index) % 3))
    # A single-option keyed draw records exact provenance without narrowing the
    # legal override range to the current difficulty band.
    return int(ctx.draw_choice("n_erased", (scheduled,)))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    explicit_n_erased = overrides.get("n_erased")
    if explicit_n_erased is not None and type(explicit_n_erased) is not int:
        raise ValueError("n_erased must be an exact integer")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng("layout")
    n_erased = _draw_n_erased(ctx, difficulty, overrides)
    requested_profile = schedule_profile(seed, sample_index, difficulty)

    # Choose only among Latin classes that can realize the requested teaching
    # witness.  In particular, the cyclic class supplies the rare five- and
    # six-hole three-pass chains; choosing the class first used to fall back to
    # an arbitrary two-pass mask half of the time.  Explicit count overrides
    # remain exact: when a slot is impossible at that count, fall back to any
    # lawful mask rather than rejecting the caller's observable request.
    candidates = [
        (base_index, masks)
        for base_index in range(len(_LATIN_BASES))
        if (masks := _candidate_masks(base_index, n_erased, requested_profile))
    ]
    if not candidates:
        candidates = [
            (base_index, masks)
            for base_index in range(len(_LATIN_BASES))
            if (masks := _candidate_masks(base_index, n_erased, "any"))
        ]
    if not candidates:  # Defensive: every count 1..10 has valid masks.
        raise ValueError(f"no three-pass-solvable mask for n_erased={n_erased}")
    base_index, masks = candidates[rng.randrange(len(candidates))]

    row_order = list(range(4))
    col_order = list(range(4))
    symbols = list(_SYMBOLS)
    rng.shuffle(row_order)
    rng.shuffle(col_order)
    rng.shuffle(symbols)
    symbol_map = {old: new for old, new in zip(_SYMBOLS, symbols)}

    base_mask = masks[rng.randrange(len(masks))]
    transported_mask = set(_transport_mask(base_mask, row_order, col_order))

    base = _LATIN_BASES[base_index]
    grid = []
    for row in range(4):
        output_row = []
        for col in range(4):
            cell = 4 * row + col
            value = symbol_map[base[row_order[row]][col_order[col]]]
            output_row.append(0 if cell in transported_mask else value)
        grid.append(output_row)
    return grid


def _analyze(grid) -> dict[str, object]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or len(grid) != 4:
        return {"errors": ["grid must be a 4x4 list of rows"]}
    if any(not isinstance(row, (list, tuple)) or len(row) != 4 for row in grid):
        return {"errors": ["grid must be rectangular 4x4"]}
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 4
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer colors 0..4")

    zero_count = sum(value == 0 for row in grid for value in row)
    if not 1 <= zero_count <= 10:
        errors.append(f"erased-cell count {zero_count} outside 1..10")

    for row_index, row in enumerate(grid):
        values = [value for value in row if value != 0]
        if len(values) != len(set(values)):
            errors.append(f"row {row_index} repeats a non-zero symbol")
    for col in range(4):
        values = [grid[row][col] for row in range(4) if grid[row][col] != 0]
        if len(values) != len(set(values)):
            errors.append(f"column {col} repeats a non-zero symbol")

    solved = _solve(grid) if not errors else None
    if solved is not None and not _is_complete_latin(solved):
        errors.append("three synchronous passes do not complete a Latin square")

    zero_cells = tuple(
        (row, col)
        for row in range(4)
        for col in range(4)
        if grid[row][col] == 0
    )
    passes = _passes_to_complete(grid) if solved is not None else None
    missing_symbols = (
        {solved[row][col] for row, col in zero_cells}
        if solved is not None and _is_complete_latin(solved)
        else set()
    )
    return {
        "errors": errors,
        "n_erased": zero_count,
        "zero_cells": zero_cells,
        "solved": solved,
        "passes_to_complete": passes,
        "joint_forced_cells": _joint_forced_cells(grid) if not errors else (),
        "missing_symbols": missing_symbols,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed, ambiguous, partial, and rule-hiding inputs."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid):
    """The exact canonical 4x4/palette/Latin-completion grammar."""
    return self_check(grid)


def observe_overrides(grid):
    """Recover every declared exact axis from the returned grid."""
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return {"n_erased": facts["n_erased"]}


def semantic_observables(grid):
    facts = _analyze(grid)
    if facts["errors"]:
        return {"errors": list(facts["errors"])}
    return {
        "n_erased": facts["n_erased"],
        "passes_to_complete": facts["passes_to_complete"],
        "joint_forced_count": len(facts["joint_forced_cells"]),
        "missing_symbol_count": len(facts["missing_symbols"]),
        "completed_square": tuple(tuple(row) for row in facts["solved"]),
    }


def rule_mirror(grid):
    """Test-only Python mirror; canonical Racket remains output authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _solve(grid)


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_single_pass(grid):
    return _fill_pass(grid)


def _rival_two_pass(grid):
    return _fill_pass(_fill_pass(grid))


def _rival_fill_one(grid):
    return [[1 if value == 0 else value for value in row] for row in grid]


def _row_only_pass(grid):
    out = [list(row) for row in grid]
    for row in range(4):
        row_values = {value for value in grid[row] if value != 0}
        candidates = [value for value in _SYMBOLS if value not in row_values]
        if len(candidates) != 1:
            continue
        for col in range(4):
            if grid[row][col] == 0:
                out[row][col] = candidates[0]
    return out


def _col_only_pass(grid):
    out = [list(row) for row in grid]
    for col in range(4):
        col_values = {
            grid[row][col] for row in range(4) if grid[row][col] != 0
        }
        candidates = [value for value in _SYMBOLS if value not in col_values]
        if len(candidates) != 1:
            continue
        for row in range(4):
            if grid[row][col] == 0:
                out[row][col] = candidates[0]
    return out


def _iterate(fn, grid):
    out = [list(row) for row in grid]
    for _ in range(3):
        out = fn(out)
    return out


def _rival_row_only(grid):
    return _iterate(_row_only_pass, grid)


def _rival_col_only(grid):
    return _iterate(_col_only_pass, grid)


SEMANTIC_RIVALS = {
    "identity": _rival_identity,
    "single_pass_only": _rival_single_pass,
    "two_pass_only": _rival_two_pass,
    "fill_every_zero_with_one": _rival_fill_one,
    "row_constraints_only": _rival_row_only,
    "column_constraints_only": _rival_col_only,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS


def _witness(predicate):
    def wrapped(grid):
        facts = semantic_observables(grid)
        return not facts.get("errors") and bool(predicate(facts))

    return wrapped


SEMANTIC_WITNESSES = {
    "one_pass_completion": _witness(
        lambda facts: facts["passes_to_complete"] == 1
    ),
    "three_pass_cascade": _witness(
        lambda facts: facts["passes_to_complete"] == 3
    ),
    "joint_row_column_elimination": _witness(
        lambda facts: facts["joint_forced_count"] >= 1
    ),
    "multiple_missing_symbols": _witness(
        lambda facts: facts["missing_symbol_count"] >= 3
    ),
}

WITNESS_RIVALS = {
    "one_pass_completion": ["identity"],
    "three_pass_cascade": ["single_pass_only", "two_pass_only"],
    "joint_row_column_elimination": [
        "row_constraints_only",
        "column_constraints_only",
    ],
    "multiple_missing_symbols": ["fill_every_zero_with_one"],
}


def lesson_identifiable(demos, query):
    """Require each three-demo lesson to falsify the principal shortcuts."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    demo_facts: list[dict[str, object]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the three-pass rule")
            continue
        demo_facts.append(semantic_observables(pair["input"]))

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query malformed: {query_errors[0]}")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with the three-pass rule")

    if len(demo_facts) != len(demos):
        return reasons

    if not any(facts["passes_to_complete"] == 3 for facts in demo_facts):
        reasons.append("demos do not refute a two-pass-only solver")
    if not any(facts["joint_forced_count"] >= 1 for facts in demo_facts):
        reasons.append("demos do not require combining row and column constraints")
    if not any(facts["missing_symbol_count"] >= 3 for facts in demo_facts):
        reasons.append("demos do not refute filling every zero with one fixed symbol")

    completed = {facts["completed_square"] for facts in demo_facts}
    if len(completed) < 2:
        reasons.append("completed Latin square does not vary across demonstrations")
    zero_counts = {facts["n_erased"] for facts in demo_facts}
    if len(zero_counts) != 1:
        reasons.append(
            "demonstrations vary erased-cell count; a count-indexed answer shortcut remains plausible"
        )

    # Name any rival that still fits all demonstrations.  The query comparison
    # itself is intentionally irrelevant here: identifiability is determined by
    # the demonstrations before the official query answer is known.
    for name, rival in LESSON_COMPETITORS.items():
        survived = True
        for pair in demos:
            try:
                predicted = rival(pair["input"])
            except Exception:
                survived = False
                break
            if predicted != pair["output"]:
                survived = False
                break
        if survived:
            reasons.append(f"named rival {name!r} survives every demonstration")

    return reasons
