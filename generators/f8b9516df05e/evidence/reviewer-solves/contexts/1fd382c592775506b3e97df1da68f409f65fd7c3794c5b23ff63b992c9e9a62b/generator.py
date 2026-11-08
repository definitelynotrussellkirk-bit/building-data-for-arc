"""Canonical-centred sampler for casting rightward rays to gray blockers.

The unchanged Racket authority finds the first non-background/non-gray emitter
in each row, then paints the empty cells up to the first gray (8) blocker to its
right.  This module only samples inputs and declares executable lesson probes;
it does not manufacture labels.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f8b9516df05e"
TASK_ID = GENERATOR_ID
RULE_HASH = "d469cd5280c8"
VERSION = "4.0.0"
SUMMARY = (
    "Sparse 0-background grids contain 1-5 active rows.  Each active row has "
    "one colored emitter followed by a gray (8) blocker, with an empty gap. "
    "The rule fills only that gap with the emitter color.  Optional cells "
    "after the blocker are preserved.  Generated lessons always include a "
    "one-cell gap and visible background after a blocker, separating the "
    "authority from two plausible shortcuts."
)

INVARIANTS = [
    "background is color 0 and blockers are color 8",
    "each nonblank row begins with one emitter and has a gray blocker to its right",
    "the cells strictly between emitter and first right-side blocker are empty",
    "generated inputs contain a one-cell ray and trailing background after a blocker",
    "0..3 post-blocker cells may occur and must remain unchanged",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-centred, mostly 8..10", "valid": "5..14"},
    "grid_w": {"type": "int", "default": "canonical-centred, mostly 9..11", "valid": "7..16"},
    "rays": {"type": "int", "default": "mostly 3..4", "valid": "1..5"},
    "post_blocker_cells": {"type": "int", "default": "mostly 0", "valid": "0..3"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_EMITTER_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_BOUNDS = {
    "grid_h": (5, 14),
    "grid_w": (7, 16),
    "rays": (1, 5),
    "post_blocker_cells": (0, 3),
}
_DIFFICULTIES = (None, "easy", "medium", "hard")


def _axis_options(name: str, difficulty: str | None) -> list[int]:
    """Full legal domain plus duplicate weights; exact overrides stay legal."""
    lo, hi = _BOUNDS[name]
    options = list(range(lo, hi + 1))
    # Keep every band anchored to the public scale.  The small tail changes
    # nuisance complexity without removing any exact value from any band.
    if name == "grid_h":
        options += [8, 9, 10] * 12
        options += {None: [9], "easy": [8, 8], "medium": [9, 10], "hard": [10, 11]}[difficulty]
    elif name == "grid_w":
        options += [9, 10, 11] * 12
        options += {None: [10], "easy": [9, 9], "medium": [10, 11], "hard": [11, 12]}[difficulty]
    elif name == "rays":
        options += [3, 3, 3, 4, 4] * 8
        options += {None: [3], "easy": [3, 3], "medium": [3, 4], "hard": [4, 5]}[difficulty]
    elif name == "post_blocker_cells":
        options += [0] * 24
        options += {None: [0], "easy": [0, 0], "medium": [0, 1], "hard": [0, 1, 2]}[difficulty]
    return options


def _validate_request(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in _DIFFICULTIES:
        raise ValueError(f"difficulty must be one of {_DIFFICULTIES}, got {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if type(value) is not int:  # reject bool, float, str and explicit None
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = _BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


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
    h = ctx.draw_choice("grid_h", _axis_options("grid_h", difficulty))
    w = ctx.draw_choice("grid_w", _axis_options("grid_w", difficulty))
    rays = ctx.draw_choice("rays", _axis_options("rays", difficulty))
    post_count = ctx.draw_choice(
        "post_blocker_cells", _axis_options("post_blocker_cells", difficulty)
    )

    grid = full_grid(h, w, 0)
    rows = ctx.draw_rng("active_rows").sample(range(h), rays)
    colors = ctx.draw_rng("emitter_colors").sample(_EMITTER_COLORS, rays)

    # Row zero in this ordering is a constructive semantic witness.  Keeping
    # the last column empty leaves enough room for all 0..3 post-blocker cells
    # even at the minimum width of seven.
    witness_row = rows[0]
    witness_color = colors[0]
    max_emit = w - post_count - 4
    witness_emit = ctx.draw_rng("unit_gap_emitter_col").randint(0, max_emit)
    witness_blocker = witness_emit + 2
    grid[witness_row][witness_emit] = witness_color
    grid[witness_row][witness_blocker] = 8

    # Put every optional decoy after that blocker.  They are deliberately
    # adjacent only for compactness; their exact colors are nuisance factors.
    decoy_rng = ctx.draw_rng("post_blocker_colors")
    decoy_palette = [color for color in _EMITTER_COLORS if color != witness_color]
    for offset in range(post_count):
        grid[witness_row][witness_blocker + 1 + offset] = decoy_rng.choice(decoy_palette)

    for index, (row, color) in enumerate(zip(rows[1:], colors[1:]), start=1):
        # With at least two rays, force one emitter away from the left edge.
        # This exposes the distinction between leading blockers and legal rows.
        emit_lo = 1 if index == 1 else 0
        emit = ctx.draw_rng(f"emitter_col_{index}").randint(emit_lo, w - 4)
        blocker = ctx.draw_rng(f"blocker_col_{index}").randint(emit + 2, w - 2)
        grid[row][emit] = color
        grid[row][blocker] = 8

    return grid


def _grid_shape_error(grid) -> str | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return "expected a nonempty rectangular grid"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "expected a nonempty rectangular grid"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "grid must be rectangular"
    return None


def _row_facts(row) -> tuple[int, int, int] | None:
    """Return (emitter, first right blocker, color), or None for a blank row."""
    nonzero = [c for c, value in enumerate(row) if value != 0]
    if not nonzero:
        return None
    emitter = nonzero[0]
    color = row[emitter]
    if color == 8:
        raise ValueError("a nonblank row must begin with an emitter, not a blocker")
    blockers = [c for c in range(emitter + 1, len(row)) if row[c] == 8]
    if not blockers:
        raise ValueError("each emitter row needs a gray blocker to its right")
    blocker = blockers[0]
    if blocker - emitter < 2:
        raise ValueError("emitter and blocker must leave at least one empty cell")
    if any(row[c] != 0 for c in range(emitter + 1, blocker)):
        raise ValueError("ray path before the first right-side blocker must be empty")
    return emitter, blocker, color


def _facts_or_errors(grid):
    shape_error = _grid_shape_error(grid)
    if shape_error:
        return [], [shape_error]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return [], ["cells must be integer ARC colors 0..9 (bool is not a color)"]
    facts: list[tuple[int, int, int, int]] = []
    errors: list[str] = []
    for r, row in enumerate(grid):
        try:
            item = _row_facts(row)
        except ValueError as exc:
            errors.append(f"row {r}: {exc}")
            continue
        if item is not None:
            facts.append((r, *item))
    return facts, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    facts, errors = _facts_or_errors(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if not 5 <= h <= 14:
        errors.append(f"grid_h={h} outside [5,14]")
    if not 7 <= w <= 16:
        errors.append(f"grid_w={w} outside [7,16]")
    if not 1 <= len(facts) <= 5:
        errors.append(f"active ray rows={len(facts)} outside [1,5]")
    post = sum(
        value != 0
        for r, _emitter, blocker, _color in facts
        for value in grid[r][blocker + 1 :]
    )
    if not 0 <= post <= 3:
        errors.append(f"post-blocker nonzero cells={post} outside [0,3]")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed lesson: " + "; ".join(errors))
    facts, _ = _facts_or_errors(grid)
    post = sum(
        value != 0
        for r, _emitter, blocker, _color in facts
        for value in grid[r][blocker + 1 :]
    )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "rays": len(facts),
        "post_blocker_cells": post,
    }


def strict_canonical_like(grid) -> list[str]:
    """Canonical-scale structural predicate, not literal example replay."""
    errors = self_check(grid)
    if errors:
        return errors
    facts, _ = _facts_or_errors(grid)
    h, w = len(grid), len(grid[0])
    if not 8 <= h <= 10:
        errors.append("canonical grid height is 8..10")
    if not 9 <= w <= 11:
        errors.append("canonical grid width is 9..11")
    if not 3 <= len(facts) <= 4:
        errors.append("canonical inputs contain 3..4 active rows")
    colors = [color for _r, _emitter, _blocker, color in facts]
    if len(colors) != len(set(colors)):
        errors.append("canonical emitter colors are distinct")
    post = sum(
        value != 0
        for r, _emitter, blocker, _color in facts
        for value in grid[r][blocker + 1 :]
    )
    if post:
        errors.append("canonical inputs have no post-blocker nonzero cells")
    return errors


def rule_mirror(grid):
    """Direct Python mirror of the selected authority, used only for probes."""
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        try:
            facts = _row_facts(row)
        except ValueError:
            continue
        if facts is None:
            continue
        emitter, blocker, color = facts
        for c in range(emitter + 1, blocker):
            out[r][c] = color
    return out


def _skip_unit_gap(grid):
    """Rival: does nothing when the ray has only one cell to paint."""
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        try:
            facts = _row_facts(row)
        except ValueError:
            continue
        if facts is None:
            continue
        emitter, blocker, color = facts
        if blocker - emitter - 1 < 2:
            continue
        for c in range(emitter + 1, blocker):
            out[r][c] = color
    return out


def _ignore_blocker(grid):
    """Rival: keeps extending through zero cells to the row edge."""
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        try:
            facts = _row_facts(row)
        except ValueError:
            continue
        if facts is None:
            continue
        emitter, _blocker, color = facts
        for c in range(emitter + 1, len(row)):
            if out[r][c] == 0:
                out[r][c] = color
    return out


def _has_unit_gap(grid) -> bool:
    facts, errors = _facts_or_errors(grid)
    return not errors and any(blocker - emitter == 2 for _r, emitter, blocker, _c in facts)


def _has_trailing_background(grid) -> bool:
    facts, errors = _facts_or_errors(grid)
    return not errors and any(
        0 in grid[r][blocker + 1 :]
        for r, _emitter, blocker, _color in facts
    )


SEMANTIC_WITNESSES = {
    "unit_gap": _has_unit_gap,
    "trailing_background": _has_trailing_background,
}
SEMANTIC_RIVALS = {
    "skip_unit_gap": _skip_unit_gap,
    "ignore_blocker": _ignore_blocker,
}
WITNESS_RIVALS = {
    "unit_gap": ["skip_unit_gap"],
    "trailing_background": ["ignore_blocker"],
}
CANONICAL_SHORTCUTS = {"skip_unit_gap": _skip_unit_gap}
LESSON_COMPETITORS = SEMANTIC_RIVALS
