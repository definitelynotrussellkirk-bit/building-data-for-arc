"""Canonical-centred generator for casting colored seeds to the right.

The selected authority is unchanged: every cell whose color is neither 0 nor
5 casts its own color rightward through cells until the first gray (5) blocker
or the row boundary.  This module samples sparse, same-size teaching inputs and
declares executable rivals; the Racket authority still produces all labels.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "26dbe76edccd"
TASK_ID = GENERATOR_ID
RULE_HASH = "ff55fa477cae"
VERSION = "2.0.0"
SUMMARY = (
    "Sparse 0-background grids contain 2-5 colored seeds, at most one per "
    "active row. Each seed paints rightward until the first gray (5) blocker "
    "or the border. Every ordinary lesson includes a one-cell blocked ray, an "
    "open ray, and a second gray blocker after the first, so four common "
    "shortcut rules are visibly wrong."
)

INVARIANTS = [
    "background is color 0 and blockers are color 5",
    "each active row has exactly one colored seed and at least one cell to paint",
    "seed colors are distinct within an input",
    "the path from a seed to its first right-side blocker or border is empty",
    "every generated input contains both a blocked unit ray and an open-to-border ray",
    "1..3 gray cells are non-terminating distractors; the first is a second right-side blocker",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "75% canonical 6/7 rows plus exact endpoint probes",
        "valid": "5..14",
    },
    "grid_w": {
        "type": "int",
        "default": "75% canonical 8/9 columns plus exact endpoint probes",
        "valid": "7..18",
    },
    "rays": {
        "type": "int",
        "default": "canonical 2/3 rays plus endpoint probes",
        "valid": "2..5",
    },
    "extra_blockers": {
        "type": "int",
        "default": "scheduled 1/2/3 non-terminating gray distractors",
        "valid": "1..3",
    },
}

_BLOCKER = 5
_SEED_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_BOUNDS = {
    "grid_h": (5, 14),
    "grid_w": (7, 18),
    "rays": (2, 5),
    "extra_blockers": (1, 3),
}
_DIFFICULTIES = (None, "easy", "medium", "hard")
_DEFAULT_PROFILES = (
    # h, w, rays, extra blockers. Distinct seed colors make palette size rays+2.
    # Six canonical-profile anchors preserve the task's native scale; two
    # endpoint probes keep every advertised integer domain exercised.
    (6, 8, 3, 1),
    (7, 9, 3, 2),
    (7, 9, 2, 3),
    (6, 8, 3, 2),
    (7, 9, 3, 3),
    (7, 9, 2, 1),
    (5, 7, 4, 1),
    (14, 18, 5, 3),
)


def _band(difficulty: str | None) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"difficulty must be one of {_DIFFICULTIES}, got {difficulty!r}")


def _validate_request(
    seed: int, sample_index: int, difficulty: str | None, overrides: dict[str, Any]
) -> None:
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be an integer, not {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError(f"sample_index must be nonnegative, got {sample_index}")
    _band(difficulty)
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if type(value) is not int:  # reject bool, float, string, and explicit None
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = _BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _draw_axis(ctx, overrides: dict[str, Any], name: str, scheduled: int) -> int:
    lo, hi = _BOUNDS[name]
    if name in overrides:
        return ctx.draw_int_strict(name, lo, hi)
    # Record every advertised axis through GenCtx while preserving the finite
    # canonical schedule. Exact callers still get the complete declared domain.
    return ctx.draw_choice(name, [scheduled])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scheduled = _DEFAULT_PROFILES[sample_index % len(_DEFAULT_PROFILES)]
    h = _draw_axis(ctx, overrides, "grid_h", scheduled[0])
    w = _draw_axis(ctx, overrides, "grid_w", scheduled[1])
    rays = _draw_axis(ctx, overrides, "rays", scheduled[2])
    extra_blockers = _draw_axis(ctx, overrides, "extra_blockers", scheduled[3])

    grid = full_grid(h, w, 0)
    rows = ctx.draw_rng("active_rows").sample(range(h), rays)
    colors = ctx.draw_rng("seed_colors").sample(_SEED_COLORS, rays)

    # Witness 1: exactly one empty cell before the first blocker.  A second
    # blocker, separated by background and followed by background, simultaneously
    # refutes treating the final gray as the stop and ignoring blockers entirely.
    blocked_row = rows[0]
    blocked_color = colors[0]
    emitter = ctx.draw_rng("unit_gap_emitter").randint(0, w - 6)
    first = emitter + 2
    second = emitter + 4
    grid[blocked_row][emitter] = blocked_color
    grid[blocked_row][first] = _BLOCKER
    grid[blocked_row][second] = _BLOCKER

    # Witness 2: a seed with no blocker to its right must paint to the border.
    # Remaining non-terminating blockers are put to its left, so they are exact,
    # observable distractors without changing that ray's authority.
    open_row = rows[1]
    leading = extra_blockers - 1
    for c in range(leading):
        grid[open_row][c] = _BLOCKER
    emit_lo = leading
    # Easy keeps the open seed visibly left; hard permits a short border ray.
    emit_hi = w - 3 if band == "easy" else w - 2
    open_emitter = ctx.draw_rng("open_emitter").randint(emit_lo, emit_hi)
    grid[open_row][open_emitter] = colors[1]

    # Additional rows vary nuisance geometry while preserving one seed per row.
    for index, (row, color) in enumerate(zip(rows[2:], colors[2:]), start=2):
        layout_rng = ctx.draw_rng(f"ray_layout_{index}")
        blocked_probability = {"easy": 0.35, "medium": 0.55, "hard": 0.75}[band]
        if layout_rng.random() < blocked_probability:
            emit = layout_rng.randint(0, w - 3)
            blocker = layout_rng.randint(emit + 2, w - 1)
            grid[row][emit] = color
            grid[row][blocker] = _BLOCKER
        else:
            emit = layout_rng.randint(0, w - 2)
            grid[row][emit] = color

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


def _row_facts(row) -> tuple[int, int | None, int] | None:
    """Return (seed column, first right blocker, seed color), or None."""
    seeds = [c for c, value in enumerate(row) if value not in (0, _BLOCKER)]
    if not seeds:
        return None
    if len(seeds) != 1:
        raise ValueError("an active row must contain exactly one colored seed")
    emitter = seeds[0]
    if emitter >= len(row) - 1:
        raise ValueError("seed needs at least one cell to its right")
    blockers = [c for c in range(emitter + 1, len(row)) if row[c] == _BLOCKER]
    blocker = blockers[0] if blockers else None
    stop = len(row) if blocker is None else blocker
    if stop - emitter < 2:
        raise ValueError("seed and stopping point must leave at least one empty cell")
    if any(row[c] != 0 for c in range(emitter + 1, stop)):
        raise ValueError("ray path before the first blocker or border must be empty")
    return emitter, blocker, row[emitter]


def _facts_or_errors(grid):
    shape_error = _grid_shape_error(grid)
    if shape_error:
        return [], [shape_error]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return [], ["cells must be integer ARC colors 0..9 (bool is not a color)"]
    facts: list[tuple[int, int, int | None, int]] = []
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
    del difficulty, meta
    facts, errors = _facts_or_errors(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if not 5 <= h <= 14:
        errors.append(f"grid_h={h} outside [5,14]")
    if not 7 <= w <= 18:
        errors.append(f"grid_w={w} outside [7,18]")
    if not 2 <= len(facts) <= 5:
        errors.append(f"active ray rows={len(facts)} outside [2,5]")
    colors = [color for _r, _emitter, _blocker, color in facts]
    if len(colors) != len(set(colors)):
        errors.append("seed colors must be distinct within an input")
    terminating = sum(blocker is not None for _r, _emitter, blocker, _color in facts)
    blocker_count = sum(value == _BLOCKER for row in grid for value in row)
    extra = blocker_count - terminating
    if not 1 <= extra <= 3:
        errors.append(f"non-terminating gray blockers={extra} outside [1,3]")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed lesson: " + "; ".join(errors))
    facts, _ = _facts_or_errors(grid)
    terminating = sum(blocker is not None for _r, _emitter, blocker, _color in facts)
    blocker_count = sum(value == _BLOCKER for row in grid for value in row)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "rays": len(facts),
        "extra_blockers": blocker_count - terminating,
    }


def strict_canonical_like(grid) -> list[str]:
    """Structural task manifold shared by all three canonical inputs."""
    return self_check(grid)


def rule_mirror(grid):
    """Direct Python mirror of the selected authority, used only for probes."""
    out = deepcopy(grid)
    if not grid:
        return out
    width = len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, _BLOCKER):
                continue
            cc = c + 1
            while cc < width and row[cc] != _BLOCKER:
                out[r][cc] = value
                cc += 1
    return out


def _skip_unit_gap(grid):
    out = deepcopy(grid)
    facts, errors = _facts_or_errors(grid)
    if errors:
        return out
    for r, emitter, blocker, color in facts:
        stop = len(grid[r]) if blocker is None else blocker
        if stop - emitter - 1 == 1:
            continue
        for c in range(emitter + 1, stop):
            out[r][c] = color
    return out


def _ignore_blocker(grid):
    out = deepcopy(grid)
    facts, errors = _facts_or_errors(grid)
    if errors:
        return out
    for r, emitter, _blocker, color in facts:
        for c in range(emitter + 1, len(grid[r])):
            if out[r][c] == 0:
                out[r][c] = color
    return out


def _last_blocker(grid):
    out = deepcopy(grid)
    facts, errors = _facts_or_errors(grid)
    if errors:
        return out
    for r, emitter, first, color in facts:
        if first is None:
            stop = len(grid[r])
        else:
            stop = max(c for c in range(emitter + 1, len(grid[r])) if grid[r][c] == _BLOCKER)
        for c in range(emitter + 1, stop):
            if out[r][c] == 0:
                out[r][c] = color
    return out


def _require_blocker(grid):
    out = deepcopy(grid)
    facts, errors = _facts_or_errors(grid)
    if errors:
        return out
    for r, emitter, blocker, color in facts:
        if blocker is None:
            continue
        for c in range(emitter + 1, blocker):
            out[r][c] = color
    return out


def _has_unit_gap(grid) -> bool:
    facts, errors = _facts_or_errors(grid)
    return not errors and any(
        blocker is not None and blocker - emitter == 2
        for _r, emitter, blocker, _color in facts
    )


def _has_trailing_background(grid) -> bool:
    facts, errors = _facts_or_errors(grid)
    return not errors and any(
        blocker is not None and 0 in grid[r][blocker + 1 :]
        for r, _emitter, blocker, _color in facts
    )


def _has_first_vs_last_blocker(grid) -> bool:
    facts, errors = _facts_or_errors(grid)
    if errors:
        return False
    return any(
        blocker is not None
        and any(
            grid[r][later] == _BLOCKER and 0 in grid[r][blocker + 1 : later]
            for later in range(blocker + 2, len(grid[r]))
        )
        for r, _emitter, blocker, _color in facts
    )


def _has_open_ray(grid) -> bool:
    facts, errors = _facts_or_errors(grid)
    return not errors and any(blocker is None for _r, _emitter, blocker, _color in facts)


SEMANTIC_WITNESSES = {
    "unit_gap": _has_unit_gap,
    "trailing_background": _has_trailing_background,
    "first_vs_last_blocker": _has_first_vs_last_blocker,
    "open_ray": _has_open_ray,
}
SEMANTIC_RIVALS = {
    "skip_unit_gap": _skip_unit_gap,
    "ignore_blocker": _ignore_blocker,
    "last_blocker": _last_blocker,
    "require_blocker": _require_blocker,
}
WITNESS_RIVALS = {
    "unit_gap": ["skip_unit_gap"],
    "trailing_background": ["ignore_blocker"],
    "first_vs_last_blocker": ["last_blocker"],
    "open_ray": ["require_blocker"],
}
CANONICAL_SHORTCUTS = {
    "skip_unit_gap": _skip_unit_gap,
    "last_blocker": _last_blocker,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
